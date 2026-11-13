"""Project parameters & measurement units, read from the application DB only.

Nothing here is a static array: every number and every unit is fetched from
``data/items.db`` at call time.  The FastAPI app (main.py) owns that DB, the
BBS only reads it -- and, for "create unit", appends a row to its ``parameters``
table so created units immediately appear in the menu listings.
"""
from __future__ import annotations

import re
import sqlite3
import tomllib
from pathlib import Path

# Petre I says: the DB is the single source of truth; no static arrays allowed.
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "items.db"
PYPROJECT = BASE_DIR / "pyproject.toml"
MAIN_PY = BASE_DIR / "main.py"

# Tables that make up the "main project" data set.
PROJECT_TABLES = [
    "items",
    "abilities",
    "parameters",
    "events",
    "item_parameters",
    "ability_to_params",
    "ability_category",
]


def connect() -> sqlite3.Connection:
    """Open the project database in row-factory mode."""
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con


def table_counts() -> dict[str, int]:
    """Row counts for every project table, sourced straight from the DB."""
    counts: dict[str, int] = {}
    with connect() as con:
        for table in PROJECT_TABLES:
            try:
                counts[table] = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.OperationalError:
                counts[table] = 0
    return counts


def parameter_units() -> list[dict]:
    """Distinct measurement units carried by the ``parameters`` table.

    A *unit* in this project is the trio (mea_name, mea_symbol, mea_system).
    """
    with connect() as con:
        rows = con.execute(
            "SELECT mea_name, mea_symbol, mea_system, COUNT(*) AS used "
            "FROM parameters "
            "WHERE mea_name != '' OR mea_symbol != '' OR mea_system != '' "
            "GROUP BY mea_name, mea_symbol, mea_system "
            "ORDER BY mea_name, mea_system"
        ).fetchall()
    return [dict(r) for r in rows]


def parameters(page: int = 0, size: int = 10) -> tuple[list[dict], int]:
    """Paginated slice of the parameters table (the project's parameters)."""
    with connect() as con:
        total = con.execute("SELECT COUNT(*) FROM parameters").fetchone()[0]
        rows = con.execute(
            "SELECT par_name, par_category, min_value, max_value, "
            "mea_name, mea_symbol, mea_system, description "
            "FROM parameters ORDER BY id LIMIT ? OFFSET ?",
            (size, page * size),
        ).fetchall()
    return [dict(r) for r in rows], total


def create_unit(
    par_name: str,
    par_category: str,
    mea_name: str,
    mea_symbol: str,
    mea_system: str,
    min_value,
    max_value,
    description: str,
) -> int | None:
    """Persist a new measurement unit as a ``parameters`` row; return its id.

    ``min_value``/``max_value`` may be ``None`` (stored as NULL).  Uses
    ``INSERT OR IGNORE`` so re-running a unit name is idempotent.
    """
    with connect() as con:
        cur = con.execute(
            "INSERT OR IGNORE INTO parameters "
            "(par_name, par_category, min_value, max_value, "
            " mea_name, mea_symbol, mea_system, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                par_name,
                par_category,
                min_value,
                max_value,
                mea_name,
                mea_symbol,
                mea_system,
                description,
            ),
        )
        con.commit()
        return cur.lastrowid


def app_version() -> str:
    """Replay ``AppVersion = str(Version("X.Y.Z").bump())`` from main.py.

    We cannot import main.py (it pulls in the FastAPI stack); reading the
    one assignment and incrementing the patch mirrors its runtime value.
    """
    txt = MAIN_PY.read_text()
    m = re.search(
        r"APP_VERSION\s*=\s*str\(Version\(\"([0-9]+\.[0-9]+\.[0-9]+)\"\)\.bump\(\)\)",
        txt,
    )
    if not m:
        return "unknown"
    parts = m.group(1).split(".")
    parts[2] = str(int(parts[2]) + 1)
    return ".".join(parts)


def pyproject_meta() -> tuple[str, str]:
    """Project name + version from pyproject.toml (read, not hardcoded)."""
    with open(PYPROJECT, "rb") as fh:
        data = tomllib.load(fh)
    proj = data["project"]
    return proj["name"], proj["version"]
