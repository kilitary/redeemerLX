# bbs — telnet BBS for the FastAPI project

A small `asyncio` telnet server that sits beside the FastAPI app and exposes its
**project parameters and measurement units** over a terminal connection.
Pure standard library — no extra dependencies.

## credentials

| username | password |
| -------- | -------- |
| `test`   | `t35t3`  |

## run

From the project root:

```bash
python -m bbs            # 127.0.0.1:6771
# or with the project venv
.venv/bin/python -m bbs
```

Then connect:

```bash
telnet 127.0.0.1 6771
# or, for a quick automated test:
nc 127.0.0.1 6771
```

## menu

```
1 list project parameters   (paginated rows from the parameters table)
2 list measurement units      (distinct mea_name/mea_symbol/mea_system units)
3 create a unit               (inserts a new parameter/unit into the DB)
q quit
```

The main menu always re-prints a live snapshot of the project parameters —
app version, pyproject version, and a row count for every project table —
read straight from `data/items.db` (no static arrays).

## "units"

A unit in this project is the triple
`(mea_name, mea_symbol, mea_system)` stored on each `parameters` row.
"Create a unit" inserts a new `parameters` row into the project database so
the new unit immediately shows up under **list measurement units** and
**list project parameters**. `par_name` is unique, so re-creating the same
unit name is a no-op (`INSERT OR IGNORE`).

## conventions

- Every number/units shown is fetched from the database at call time.
- Telnet IAC negotiation is handled so characters don't leak into input lines.
- The server owns echo (clients are told not to echo), which lets password
  masking (`*`) work uniformly across `telnet` and `nc`.
