"""ANSI escape-sequence helpers for the BBS terminal.

Pure-string module: it builds escape sequences but never blocks on I/O, so the
server can flush them through a plain ``asyncio`` stream.  Graphics use 7-bit
ASCII box drawing only -- no unicode -- so every telnet client renders evenly.
"""
from __future__ import annotations

import re

# Petre I says: the glyphs stay within 7 bits; no unicode tricks.
ESC = "\x1b"
CSI = f"{ESC}["

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*m")


def visible_len(text: str) -> int:
    """Length of ``text`` ignoring ANSI SGR escape codes, for box layout."""
    return len(ANSI_RE.sub("", text))

RESET = f"{ESC}[0m"
BOLD = f"{ESC}[1m"
DIM = f"{ESC}[2m"

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = (
    f"{ESC}[{30 + n}m" for n in range(8)
)
BGBLACK, BGRED, BGGREEN, BGYELLOW, BGBLUE, BGMAGENTA, BGCYAN, BGWHITE = (
    f"{ESC}[{40 + n}m" for n in range(8)
)

CLEAR = f"{CSI}2J{CSI}H"
ERASE_LINE = f"{CSI}2K"
HIDE_CURSOR = f"{ESC}[?25l"
SHOW_CURSOR = f"{ESC}[?25h"


def move_to(row: int, col: int) -> str:
    """Absolute cursor position (1-based, matching terminal convention)."""
    return f"{CSI}{row};{col}H"


def color(fg: str = "", bg: str = "", bold: bool = False, dim: bool = False) -> str:
    """Build one SGR run from parts.  Pass color *name* constants from this module."""
    parts = []
    if bold:
        parts.append("1")
    if dim:
        parts.append("2")
    if fg:
        parts.append(fg.replace(f"{ESC}[", "").replace("m", ""))
    if bg:
        parts.append(bg.replace(f"{ESC}[", "").replace("m", ""))
    if not parts:
        return RESET
    return f"{CSI}{';'.join(parts)}m"


def erase_line() -> str:
    """Clear from cursor to end of line."""
    return ERASE_LINE


def box(title: str, body: list[str], width: int = 53, inner_pad: int = 1) -> str:
    """Render an ASCII box: a title bar over a body, flushed to ``width``."""
    w = max(width, len(title) + 4)
    bar = "+=" + ("=" * (w - 4)) + "=+"
    tvis = visible_len(title)
    title_row = f"| {BOLD}{title}{RESET}" + " " * (w - 2 - 2 - tvis) + " |"
    border = "+" + "-" * (w - 2) + "+"

    pad = " " * inner_pad
    inner = w - 2 - inner_pad * 2
    out = [CLEAR + HIDE_CURSOR, "", bar, title_row, border]
    for line in body:
        text = str(line)
        vlen = visible_len(text)
        if vlen > inner:
            text = text[:inner] + RESET
            vlen = inner
        out.append(f"|{pad}{text}{pad}{' ' * (inner - vlen)}|")
    out.append(border)
    return "\r\n".join(out) + "\r\n"
