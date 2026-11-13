"""A quick asyncio telnet BBS for the FastAPI project.

Auth wall (``test``/``t35t3``), then a menu that prints the main project
parameters (read from the DB only) and offers:

  1. list project parameters (paginated, from the ``parameters`` table)
  2. list measurement units (distinct units from the DB)
  3. create a unit (inserts a new parameter/unit row into the DB)
  q. quit

Run from the project root::

    python -m bbs
"""
from __future__ import annotations

import asyncio

from .ansi import (
    BOLD,
    CLEAR,
    CYAN,
    DIM,
    GREEN,
    HIDE_CURSOR,
    MAGENTA,
    RED,
    RESET,
    SHOW_CURSOR,
    YELLOW,
    box,
)
from . import db
from .auth import check_auth

HOST = "127.0.0.1"
PORT = 6771

# Telnet command/option bytes (RFC 854/855).
IAC = 0xFF
SB, SE = 0xFA, 0xF0
AYT = 0xF6
# Negotiation verbs (WILL/DO request enabling, WONT/DONT disabling).
WILL, DO, WONT, DONT = 0xFB, 0xFD, 0xFC, 0xFE
OPT_ECHO = 0x01
OPT_SGA = 0x03
MASK_CHAR = "*"

# Petre I says: the client speaks telnet; we speak telnet back, briefly.
BANNER = r"""
  ____  _   _ ____
 | __ )| | | | ___\ \   _ _ __ _ __  _ __   ___
 |  _ \| | | | |_  ) | | | '__| '_ \| '_ \ / _ \
 | |_) | |_| |  _|/ / |_| | |  | |_) | | | |  __/
 |____/ \__,_|_|  /_|\__,_|_|  | .__/|_| |_|\___|
                              |_|        BBS
"""


class TelnetDecoder:
    """Split a raw telnet byte stream into clean input + negotiation replies.

    Policy is *server owns echo*: the server announces WILL ECHO (clients then
    disable their own local echo) and will echo characters itself, so password
    masking works uniformly.  Every other option is politely declined.
    Subnegotiations are swallowed whole so stray payload bytes cannot leak
    into the line buffer.
    """

    NORMAL = 0
    IAC = 1
    OPT = 2
    SB = 3
    SB_IAC = 4

    def __init__(self) -> None:
        self.state = self.NORMAL
        self.verb = 0

    def feed(self, data: bytes) -> tuple[bytes, bytes]:
        """Return ``(clean_input_bytes, iac_replies)`` for one read chunk."""
        clean = bytearray()
        resp = bytearray()
        for b in data:
            s = self.state
            if s == self.NORMAL:
                if b == IAC:
                    self.state = self.IAC
                else:
                    clean.append(b)
            elif s == self.IAC:
                if b == IAC:  # literal 255 data byte
                    clean.append(IAC)
                    self.state = self.NORMAL
                elif b in (WILL, DO, WONT, DONT):
                    self.verb = b
                    self.state = self.OPT
                elif b == SB:
                    self.state = self.SB
                elif b == SE:
                    self.state = self.NORMAL
                elif b == AYT:
                    resp.extend(self.ayt_reply())
                    self.state = self.NORMAL
                else:  # NOP, DM, EL, GA, etc.
                    self.state = self.NORMAL
            elif s == self.OPT:
                self.reply_negotiate(self.verb, b, resp)
                self.state = self.NORMAL
            elif s == self.SB:
                if b == IAC:
                    self.state = self.SB_IAC
                # else: swallow subnegotiation payload
            elif s == self.SB_IAC:
                if b == SE:
                    self.state = self.NORMAL
                elif b == IAC:  # literal 255 inside SB
                    self.state = self.SB
                else:  # stray byte after IAC inside SB: keep swallowing
                    self.state = self.SB
        return bytes(clean), bytes(resp)

    @staticmethod
    def ayt_reply() -> bytes:
        return b"\r\nbbs: yes\r\n"

    @staticmethod
    def reply_negotiate(verb: int, opt: int, out: bytearray) -> None:
        # Server owns ECHO/SGA; everything else is declined.
        if verb == WILL and opt == OPT_ECHO:
            out.extend(bytes([IAC, DONT, opt]))  # "you don't echo; I will"
        elif verb == DO and opt == OPT_ECHO:
            out.extend(bytes([IAC, WILL, opt]))  # "I will echo"
        elif opt in (OPT_ECHO, OPT_SGA):
            # Keep ECHO/SGA active: mirror agree/ decline to keep it on.
            if verb == WILL:
                out.extend(bytes([IAC, DO, opt]))
            elif verb == DO:
                out.extend(bytes([IAC, WILL, opt]))
            elif verb == WONT:
                out.extend(bytes([IAC, DONT, opt]))
            elif verb == DONT:
                out.extend(bytes([IAC, WONT, opt]))
        else:
            if verb == WILL:
                out.extend(bytes([IAC, DONT, opt]))
            elif verb == DO:
                out.extend(bytes([IAC, WONT, opt]))
            elif verb == WONT:
                out.extend(bytes([IAC, DONT, opt]))
            elif verb == DONT:
                out.extend(bytes([IAC, WONT, opt]))


class TTY:
    """Thin wrapper over an asyncio stream that owns a TelnetDecoder."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.decoder = TelnetDecoder()

    def write(self, data) -> None:
        self.writer.write(data.encode() if isinstance(data, str) else data)

    async def drain(self) -> None:
        await self.writer.drain()

    async def send(self, text: str = "") -> None:
        self.write(text)
        await self.drain()

    async def announce_echo(self) -> None:
        # Announce server-side echo + suppress-go-ahead so clients turn off
        # their own local echo and run in character mode.
        self.writer.write(bytes([IAC, WILL, OPT_ECHO, IAC, WILL, OPT_SGA]))
        await self.drain()

    async def read_clean(self) -> bytes:
        data = await self.reader.read(512)
        if not data:
            raise ConnectionError("client closed")
        clean, resp = self.decoder.feed(data)
        if resp:
            self.writer.write(resp)
            await self.drain()
        return clean


async def read_line(tty: TTY, prompt: str, mask: bool = False) -> str:
    """Read one line, echoing characters ourselves (server owns echo)."""
    await tty.send(prompt)
    buf: list[str] = []
    while True:
        clean = await tty.read_clean()
        for b in clean:
            if b in (0x0D, 0x0A):  # CR / LF end the line
                await tty.send("\r\n")
                return "".join(buf)
            if b in (0x08, 0x7F):  # backspace / delete
                if buf:
                    buf.pop()
                    await tty.send("\x08 \x08")
                continue
            if 27 <= b < 32:  # other control bytes (ESC etc.): swallow
                continue
            if 32 <= b < 127:  # printable ASCII
                buf.append(chr(b))
                await tty.send(MASK_CHAR if mask else chr(b))
    # Unreachable: loop only exits via return.


async def confirm(tty: TTY, msg: str, yes: str = "Y", no: str = "n") -> bool:
    await tty.send(f"{msg} [{yes}/{no}] {RESET}")
    ch = (await read_line(tty, "")).strip().lower() or "y"
    return ch.startswith(yes.lower())


def menu_snapshot() -> list[str]:
    """Build the project-parameter snapshot printed on every menu screen."""
    name, pversion = db.pyproject_meta()
    version = db.app_version()
    counts = db.table_counts()
    units = db.parameter_units()
    lines = [
        f"{BOLD}{CYAN}project:{RESET} {name} {RESET}v{pversion}",
        f"{BOLD}{CYAN}app:{RESET}    v{version}  {DIM}(main.APP_VERSION){RESET}",
        "",
        f"{BOLD}DB table counts (data/items.db):{RESET}",
    ]
    for t in db.PROJECT_TABLES:
        lines.append(f"  {GREEN}{t:<22}{RESET} {counts.get(t, 0)}")
    lines.append("")
    lines.append(f"{BOLD}distinct measurement units:{RESET} {len(units)}")
    total_params = counts.get("parameters", 0)
    lines.append(f"{BOLD}total parameters:{RESET} {total_params}")
    return lines


def render_menu() -> str:
    return box(
        "main menu",
        menu_snapshot()
        + [""]
        + [
            f"{BOLD}1{RESET} list project parameters",
            "2 list measurement units",
            "3 create a unit",
            f"{RED}q{RESET} quit",
        ],
        width=56,
    )


async def show_auth(tty: TTY) -> bool:
    for attempt in range(3):
        await tty.send(CLEAR + HIDE_CURSOR + BOLD + CYAN + BANNER + RESET + "\n")
        await tty.send(f"{YELLOW}login{RESET}    : ")
        user = (await read_line(tty, "")).strip()
        await tty.send(f"{YELLOW}password{RESET}: ")
        pw = await read_line(tty, "", mask=True)
        if check_auth(user, pw):
            await tty.send(RESET)
            return True
        await tty.send(f"\r\n{RED}bad login — try again{RESET}\r\n")
    return False


async def list_parameters(tty: TTY) -> None:
    await paginate(tty, db.parameters, "project parameters")


async def paginate(tty: TTY, fetcher, title: str) -> None:
    """Generic pager over a ``fetcher(page, size) -> (rows, total)`` callable."""
    page = 0
    size = 9
    while True:
        rows, total = fetcher(page, size)
        await tty.send(CLEAR + HIDE_CURSOR)
        await tty.send(f"{BOLD}{MAGENTA}{title}{RESET} ({total} rows)\r\n\r\n")
        for r in rows:
            mea = f"{r['mea_name'] or '-'} {r['mea_symbol'] or ''} ({r['mea_system'] or '?'})"
            rng = ""
            if r["min_value"] is not None or r["max_value"] is not None:
                rng = f"  range [{r['min_value']}, {r['max_value']}]"
            await tty.send(
                f"  {CYAN}{r['par_name']}{RESET} {DIM}{r['par_category']}{RESET}\r\n"
                f"    unit: {mea}{rng}  {DIM}{r['description'] or ''}{RESET}\r\n"
            )
        last = ((total - 1) // size) + 1 if total else 1
        more = "  n=next p=prev q=back" if total > size else "  q=back"
        await tty.send(f"\r\n{DIM}page {page + 1}/{last}{RESET}{more}\r\n")
        cmd = (await read_line(tty, f"{GREEN}->{RESET} ")).strip().lower()
        if cmd in ("n", "next"):
            if (page + 1) * size < total:
                page += 1
        elif cmd in ("p", "prev"):
            page = max(0, page - 1)
        else:
            return


async def list_units(tty: TTY) -> None:
    units = db.parameter_units()
    await tty.send(CLEAR + HIDE_CURSOR)
    await tty.send(f"{BOLD}{MAGENTA}measurement units (data/items.db){RESET}\r\n\r\n")
    if not units:
        await tty.send(f"{DIM}no units defined yet.{RESET}\r\n")
    for u in units:
        sym = u["mea_symbol"] or ""
        await tty.send(f"  {YELLOW}{u['mea_name']:<16}{RESET} {BOLD}{sym:<6}{RESET}  sys={u['mea_system']:<12} (used {u['used']}x)\r\n")
    await wait_key(tty, "\r\npress enter to return...")


async def wait_key(tty: TTY, prompt: str = "press enter to return...") -> None:
    await read_line(tty, f"\r\n{prompt} ")


async def create_unit(tty: TTY) -> None:
    await tty.send(CLEAR + HIDE_CURSOR)
    await tty.send(f"{BOLD}{MAGENTA}create a unit (new parameter row in the DB){RESET}\r\n\r\n")
    # Petre I says: await binds looser than .strip(), so parenthesise.
    mea_name = (await read_line(tty, f"  mea_name  (e.g. temperature)      : ")).strip()
    if not mea_name:
        await tty.send(f"{RED}aborted: mea_name required.{RESET}\r\n")
        return await wait_key(tty)
    symbol = (await read_line(tty, f"  symbol   (e.g. T / K / Pa)         : ")).strip()
    system = (await read_line(tty, f"  system   (e.g. kelvin / SI / custom): ")).strip() or "custom"
    par_name = (await read_line(tty, f"  par_name (default = mea_name)      : ")).strip() or mea_name
    category = (await read_line(tty, f"  category (e.g. thermal)            : ")).strip() or "general"
    desc = (await read_line(tty, f"  description                         : ")).strip()

    async def parse_num(label, default=None):
        raw = (await read_line(tty, f"  {label} (blank = none)               : ")).strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError:
            await tty.send(f"{RED}  not a number — leaving blank{RESET}\r\n")
            return default

    mn = await parse_num("min_value")
    mx = await parse_num("max_value")

    await tty.send(
        f"\r\n{BOLD}confirm create unit "
        f"{YELLOW}{mea_name} {symbol} ({system}){RESET} -> par `{par_name}`? "
    )
    if not await confirm(tty, "", yes="y", no="n"):
        await tty.send(f"{DIM}aborted.{RESET}\r\n")
        return await wait_key(tty)
    rowid = db.create_unit(
        par_name=par_name,
        par_category=category,
        mea_name=mea_name,
        mea_symbol=symbol,
        mea_system=system,
        min_value=mn,
        max_value=mx,
        description=desc,
    )
    if rowid is None:
        await tty.send(f"{RED}unit already exists (par_name is unique).{RESET}\r\n")
    else:
        await tty.send(f"{GREEN}created unit id={rowid}: "
                       f"{mea_name} {symbol} ({system}) [{par_name}]{RESET}\r\n")
    await wait_key(tty)


async def main_menu(tty: TTY) -> str:
    await tty.send(render_menu())
    return (await read_line(tty, f"{BOLD}{GREEN}->{RESET} ")).strip().lower()


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    tty = TTY(reader, writer)
    try:
        await tty.announce_echo()
        if not await show_auth(tty):
            await tty.send(f"\r\n{RED}authentication failed — goodbye.{RESET}\r\n")
            return
        while True:
            cmd = await main_menu(tty)
            if cmd in ("1", "params", "parameters"):
                await list_parameters(tty)
            elif cmd in ("2", "units"):
                await list_units(tty)
            elif cmd in ("3", "create", "unit"):
                await create_unit(tty)
            elif cmd in ("q", "quit", "exit"):
                await tty.send(f"\r\n{GREEN}bye — thanks for visiting.{RESET}\r\n")
                return
            else:
                await tty.send(f"{RED}unknown command: {cmd!r}{RESET}\r\n")
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    except Exception as exc:  # noqa: BLE001 - top-level guard per connection
        try:
            await tty.send(f"{RED}\r\nbbs error: {exc}{RESET}\r\n")
        except Exception:
            pass
    finally:
        try:
            await tty.send(SHOW_CURSOR)
        except Exception:
            pass
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


def run(host: str = HOST, port: int = PORT) -> None:
    async def main() -> None:
        server = await asyncio.start_server(handle_client, host, port)
        addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
        print(f"bbs listening on {addrs}", flush=True)
        async with server:
            await server.serve_forever()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nbbs stopped", flush=True)


if __name__ == "__main__":
    run()
