import json
import logging
import os
import random
import re
import secrets
import sys
import time
import zlib
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path as FilePath
from re import Match
from typing import override

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, ForeignKey, Table, create_engine, event, or_, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    selectinload,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from ability import ABILITIES, ability_category
from parts import ALL_PARTS, CATALOG_NAMES, STATIC_ITEMS

BASE_DIR = FilePath(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(mode=0o777, exist_ok=True)
DB_PATH = DATA_DIR / "items.db"
DB_PATH.touch(exist_ok=True)
try:
    os.chmod(DB_PATH, 0o666)
    os.chmod(DATA_DIR, 0o777)
except PermissionError:
    print("permission error")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"


class CompactFormatter(logging.Formatter):
    """Compact plain-text stderr formatter: time · level · message."""

    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        msg = record.getMessage()
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            msg += "\n" + record.exc_text
        return f"{record.asctime} {record.levelname:<7} {msg}"


logger = logging.getLogger("items_api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(CompactFormatter(datefmt="%H:%M:%S"))
    logger.addHandler(handler)
logger.propagate = False
logger.debug("Debug mode enabled: %s", logger.hasHandlers())


logger.info(f"Connecting to database {SQLALCHEMY_DATABASE_URL} ...")
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def csrf_cookie_name() -> str:
    """Daily-rotating CSRF cookie name: cokgi_<crc32(day_of_year+year)>."""
    now = datetime.now(UTC)
    yday = now.timetuple().tm_yday
    digest = zlib.crc32(f"{yday}{now.year}".encode()) & 0xFFFFFFFF
    return f"cokgi_{digest}"


def get_csrf_token(request: Request) -> str:
    """Return (and persist per request) the current CSRF token."""
    token = getattr(request.state, "csrf_token", None)
    if token:
        return token
    token = request.cookies.get(csrf_cookie_name()) or secrets.token_urlsafe(32)
    request.state.csrf_token = token
    return token


templates.env.globals["csrf_token"] = get_csrf_token


class Version:
    """X.Y.Z[-suffix].

    Each ``bump()`` increments the patch version; if a suffix (sub‑version) is
    present it is incremented as well (e.g. ``beta`` → ``beta2``).
    """

    major: int
    minor: int
    patch: int
    suffix: str

    def __init__(self, text: str) -> None:
        num, _, suffix = text.partition("-")
        parts = [int(x) for x in num.split(".")]
        self.major, self.minor = parts[0], parts[1]
        self.patch = parts[2] if len(parts) > 2 else 0
        self.suffix = suffix or ""

    def bump(self) -> str:
        """Increment the version.

        If a suffix exists it is treated as a textual base followed by an
        optional numeric part. The numeric part is increased (or set to ``2`` if
        absent). Otherwise the *patch* component is incremented.
        """
        if self.suffix:
            fm: Match[str] | None = re.fullmatch(r"([A-Za-z]+)(\d*)", self.suffix)
            base, n = fm.groups() if fm is not None else ("", "")
            self.suffix = f"{base}{int(n) + 1 if n else 2}"
        else:
            self.patch += 1
        return str(self)

    @override
    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.suffix}" if self.suffix else base

    @override
    def __repr__(self) -> str:
        """Return the same representation as ``__str__`` for debugging."""
        return self.__str__()


APP_VERSION = str(Version("1.36.26").bump())
logger.info(f"App version: {APP_VERSION}")
templates.env.globals["app_version"] = APP_VERSION


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_db_start: dict[int, float] = {}
_db_stack: dict[int, float] = {}


@event.listens_for(Engine, "before_cursor_execute")
def _before_exec(conn, cursor, statement, parameters, context, executemany):
    _db_stack[id(conn)] = time.perf_counter()


@event.listens_for(Engine, "after_cursor_execute")
def _after_exec(conn, cursor, statement, parameters, context, executemany):
    start = _db_stack.pop(id(conn), None)
    if start is not None:
        _db_start[id(conn)] = _db_start.get(id(conn), 0.0) + (
            time.perf_counter() - start
        )


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


item_abilities = Table(
    "item_abilities",
    Base.metadata,
    Column(
        "item_id",
        ForeignKey("items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "ability_id",
        ForeignKey("abilities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

event_abilities = Table(
    "event_abilities",
    Base.metadata,
    Column(
        "event_id",
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "ability_id",
        ForeignKey("abilities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class AbilityDB(Base):
    __tablename__ = "abilities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str] = mapped_column(default="")
    description_ru: Mapped[str] = mapped_column(default="")
    category: Mapped[str] = mapped_column(default="", index=True)

    items: Mapped[list["ItemDB"]] = relationship(
        secondary=item_abilities, back_populates="abilities"
    )
    ability_params: Mapped[list["AbilityParamDB"]] = relationship(
        back_populates="ability",
        cascade="all, delete-orphan",
        order_by="AbilityParamDB.id",
    )
    events: Mapped[list["EventDB"]] = relationship(
        secondary=event_abilities, back_populates="abilities"
    )
    categories: Mapped[list["AbilityCategoryDB"]] = relationship(
        back_populates="ability",
        cascade="all, delete-orphan",
        order_by="AbilityCategoryDB.id",
    )


class EventDB(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str] = mapped_column(default="")
    event_per_10msec: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    abilities: Mapped[list["AbilityDB"]] = relationship(
        secondary=event_abilities,
        back_populates="events",
        order_by="AbilityDB.id",
    )


class ItemDB(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column(default=0.0)
    quantity: Mapped[int] = mapped_column(default=1)
    is_offer: Mapped[bool] = mapped_column(default=False)
    color: Mapped[str] = mapped_column(default="")
    size: Mapped[str] = mapped_column(default="")
    weight: Mapped[float] = mapped_column(default=0.0)
    hp: Mapped[float] = mapped_column(default=100.0)
    is_anti_emc: Mapped[bool] = mapped_column(default=False)
    is_proof: Mapped[bool] = mapped_column(default=False)
    water_resistant: Mapped[bool] = mapped_column(default=False)
    oil: Mapped[float] = mapped_column(default=0.0)
    self_desentry: Mapped[bool] = mapped_column(default=False)
    is_parasite: Mapped[bool] = mapped_column(default=False)
    parasite_chance: Mapped[int] = mapped_column(default=0)
    revision: Mapped[int] = mapped_column(default=1)
    added_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    parent: Mapped["ItemDB | None"] = relationship(
        back_populates="subitems", remote_side=[id]
    )
    subitems: Mapped[list["ItemDB"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="ItemDB.id",
    )
    abilities: Mapped[list["AbilityDB"]] = relationship(
        secondary=item_abilities,
        back_populates="items",
        order_by="AbilityDB.id",
    )
    item_parameters: Mapped[list["ItemParameterDB"]] = relationship(
        back_populates="item"
    )


class ParameterDB(Base):
    __tablename__ = "parameters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    par_name: Mapped[str] = mapped_column(unique=True, index=True)
    par_category: Mapped[str] = mapped_column(default="", index=True)
    min_value: Mapped[float | None] = mapped_column(nullable=True)
    max_value: Mapped[float | None] = mapped_column(nullable=True)
    mea_name: Mapped[str] = mapped_column(default="")
    mea_symbol: Mapped[str] = mapped_column(default="")
    mea_system: Mapped[str] = mapped_column(default="SI")
    description: Mapped[str] = mapped_column(default="")
    description_ru: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    items: Mapped[list["ItemParameterDB"]] = relationship(
        back_populates="parameter", cascade="all, delete-orphan"
    )


class ItemParameterDB(Base):
    __tablename__ = "item_parameters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    par_id: Mapped[int] = mapped_column(
        ForeignKey("parameters.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[float | None] = mapped_column(nullable=True)
    value_text: Mapped[str | None] = mapped_column(nullable=True)
    unit_override: Mapped[str | None] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(default="manual")
    confidence: Mapped[float] = mapped_column(default=1.0)
    base_value: Mapped[float | None] = mapped_column(nullable=True)
    min_value: Mapped[float | None] = mapped_column(nullable=True)
    max_value: Mapped[float | None] = mapped_column(nullable=True)
    measured_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    item: Mapped["ItemDB"] = relationship(back_populates="item_parameters")
    parameter: Mapped["ParameterDB"] = relationship(back_populates="items")


class AbilityParamDB(Base):
    __tablename__ = "ability_to_params"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ability_id: Mapped[int] = mapped_column(
        ForeignKey("abilities.id", ondelete="CASCADE"), index=True
    )
    param_id: Mapped[int] = mapped_column(
        ForeignKey("parameters.id", ondelete="CASCADE"), index=True
    )
    modify_coefficient_per_10msec: Mapped[float] = mapped_column(default=0.0)
    # detailed props
    operation: Mapped[str] = mapped_column(default="add")  # add | multiply | set
    base_value: Mapped[float | None] = mapped_column(nullable=True)
    min_value: Mapped[float | None] = mapped_column(nullable=True)
    max_value: Mapped[float | None] = mapped_column(nullable=True)
    curve: Mapped[str] = mapped_column(default="linear")  # linear | exponential | log
    stack_mode: Mapped[str] = mapped_column(default="stack")  # stack | replace | max
    priority: Mapped[int] = mapped_column(default=0)
    enabled: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    ability: Mapped["AbilityDB"] = relationship(back_populates="ability_params")
    parameter: Mapped["ParameterDB"] = relationship()


class AbilityCategoryDB(Base):
    """A single-word category linked to an ability (e.g. ability 'measure' →
    category 'scan'). Each ability can have one or more category links."""

    __tablename__ = "ability_category"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ability_id: Mapped[int] = mapped_column(
        ForeignKey("abilities.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(default="", index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    ability: Mapped["AbilityDB"] = relationship(back_populates="categories")


Base.metadata.create_all(bind=engine)


def migrate_schema() -> None:
    with engine.begin() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(items)")}
        columns = {
            "color": "ALTER TABLE items ADD COLUMN color VARCHAR(20) NOT NULL DEFAULT ''",
            "size": "ALTER TABLE items ADD COLUMN size VARCHAR(20) NOT NULL DEFAULT ''",
            "weight": "ALTER TABLE items ADD COLUMN weight FLOAT NOT NULL DEFAULT 0",
            "hp": "ALTER TABLE items ADD COLUMN hp FLOAT NOT NULL DEFAULT 100",
            "is_anti_emc": "ALTER TABLE items ADD COLUMN is_anti_emc BOOLEAN NOT NULL DEFAULT 0",
            "is_proof": "ALTER TABLE items ADD COLUMN is_proof BOOLEAN NOT NULL DEFAULT 0",
            "water_resistant": "ALTER TABLE items ADD COLUMN water_resistant BOOLEAN NOT NULL DEFAULT 0",
            "oil": "ALTER TABLE items ADD COLUMN oil FLOAT NOT NULL DEFAULT 0",
            "self_desentry": "ALTER TABLE items ADD COLUMN self_desentry BOOLEAN NOT NULL DEFAULT 0",
            "is_parasite": "ALTER TABLE items ADD COLUMN is_parasite BOOLEAN NOT NULL DEFAULT 0",
            "parasite_chance": "ALTER TABLE items ADD COLUMN parasite_chance INTEGER NOT NULL DEFAULT 0",
            "revision": "ALTER TABLE items ADD COLUMN revision INTEGER NOT NULL DEFAULT 1",
            "parent_id": "ALTER TABLE items ADD COLUMN parent_id INTEGER",
            "quantity": "ALTER TABLE items ADD COLUMN quantity INTEGER NOT NULL DEFAULT 1",
            "added_at": "ALTER TABLE items ADD COLUMN added_at DATETIME",
            "updated_at": "ALTER TABLE items ADD COLUMN updated_at DATETIME",
        }
        for name, ddl in columns.items():
            if name not in existing:
                conn.exec_driver_sql(ddl)

        if "added_at" in existing and "updated_at" in existing:
            conn.exec_driver_sql(
                "UPDATE items SET "
                "added_at = COALESCE(added_at, datetime('now')), "
                "updated_at = COALESCE(updated_at, added_at)"
            )

        tables = {
            row[0]
            for row in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "subitems" in tables:
            conn.exec_driver_sql(
                "INSERT INTO items (parent_id, name, price, quantity) "
                "SELECT item_id, name, 0, quantity FROM subitems"
            )
            conn.exec_driver_sql("DROP TABLE subitems")

        ability_cols = {
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(abilities)")
        }
        if "description_ru" not in ability_cols:
            conn.exec_driver_sql(
                "ALTER TABLE abilities ADD COLUMN description_ru VARCHAR NOT NULL DEFAULT ''"
            )
        if "category" not in ability_cols:
            conn.exec_driver_sql(
                "ALTER TABLE abilities ADD COLUMN category VARCHAR NOT NULL DEFAULT ''"
            )

        tables = {
            row[0]
            for row in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "subitems" in tables:
            conn.exec_driver_sql(
                "INSERT INTO items (parent_id, name, price, quantity) "
                "SELECT item_id, name, 0, quantity FROM subitems"
            )
            conn.exec_driver_sql("DROP TABLE subitems")

        ability_cols = {
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(abilities)")
        }
        if "description_ru" not in ability_cols:
            conn.exec_driver_sql(
                "ALTER TABLE abilities ADD COLUMN description_ru VARCHAR NOT NULL DEFAULT ''"
            )
        if "category" not in ability_cols:
            conn.exec_driver_sql(
                "ALTER TABLE abilities ADD COLUMN category VARCHAR NOT NULL DEFAULT ''"
            )

        tables = {
            row[0]
            for row in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "parameters" not in tables:
            conn.exec_driver_sql("""
                CREATE TABLE parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    par_name VARCHAR NOT NULL UNIQUE,
                    par_category VARCHAR NOT NULL DEFAULT '',
                    min_value FLOAT,
                    max_value FLOAT,
                    mea_name VARCHAR NOT NULL,
                    mea_symbol VARCHAR NOT NULL,
                    mea_system VARCHAR NOT NULL DEFAULT 'SI',
                    description VARCHAR NOT NULL DEFAULT '',
                    description_ru VARCHAR NOT NULL DEFAULT '',
                    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.exec_driver_sql(
                "CREATE INDEX ix_parameters_par_name ON parameters(par_name)"
            )
            conn.exec_driver_sql(
                "CREATE INDEX ix_parameters_category ON parameters(par_category)"
            )

            params = [
                (
                    "mass",
                    "mechanical",
                    0.0,
                    5000.0,
                    "mass",
                    "m",
                    "SI",
                    "Mass of the object",
                ),
                (
                    "volume",
                    "geometric",
                    0.0,
                    2000.0,
                    "volume",
                    "V",
                    "SI",
                    "Volume of the object",
                ),
                (
                    "density",
                    "mechanical",
                    0.0,
                    700.0,
                    "density",
                    "ρ",
                    "SI",
                    "Mass per unit volume",
                ),
                (
                    "length",
                    "geometric",
                    0.0,
                    2000.0,
                    "length",
                    "L",
                    "SI",
                    "Linear dimension",
                ),
                (
                    "width",
                    "geometric",
                    0.0,
                    1500.0,
                    "width",
                    "W",
                    "SI",
                    "Linear dimension",
                ),
                (
                    "height",
                    "geometric",
                    0.0,
                    3000.0,
                    "height",
                    "H",
                    "SI",
                    "Linear dimension",
                ),
                (
                    "diameter",
                    "geometric",
                    0.0,
                    1000.0,
                    "diameter",
                    "D",
                    "SI",
                    "Linear dimension",
                ),
                (
                    "thickness",
                    "geometric",
                    0.0,
                    200.0,
                    "thickness",
                    "t",
                    "SI",
                    "Linear dimension",
                ),
                (
                    "surface_area",
                    "geometric",
                    0.0,
                    1000000.0,
                    "area",
                    "A",
                    "SI",
                    "Surface area",
                ),
                (
                    "cross_sectional_area",
                    "geometric",
                    0.0,
                    100000.0,
                    "area",
                    "A",
                    "SI",
                    "Cross-sectional area",
                ),
                (
                    "temperature",
                    "thermal",
                    0.0,
                    2200.0,
                    "temperature",
                    "T",
                    "SI",
                    "Thermodynamic temperature",
                ),
                (
                    "melting_point",
                    "thermal",
                    0.0,
                    4000.0,
                    "temperature",
                    "T",
                    "SI",
                    "Melting temperature",
                ),
                (
                    "boiling_point",
                    "thermal",
                    0.0,
                    6000.0,
                    "temperature",
                    "T",
                    "SI",
                    "Boiling temperature",
                ),
                (
                    "thermal_conductivity",
                    "thermal",
                    0.0,
                    500.0,
                    "thermal conductivity",
                    "k",
                    "SI",
                    "Thermal conductivity",
                ),
                (
                    "specific_heat",
                    "thermal",
                    0.0,
                    4000.0,
                    "specific heat capacity",
                    "c",
                    "SI",
                    "Specific heat capacity",
                ),
                (
                    "thermal_expansion",
                    "thermal",
                    -0.0001,
                    0.0001,
                    "coefficient of thermal expansion",
                    "α",
                    "SI",
                    "Linear thermal expansion coefficient",
                ),
                (
                    "tensile_strength",
                    "mechanical",
                    0.0,
                    3000.0,
                    "tensile strength",
                    "σ",
                    "SI",
                    "Ultimate tensile strength",
                ),
                (
                    "yield_strength",
                    "mechanical",
                    0.0,
                    2500.0,
                    "yield strength",
                    "σ_y",
                    "SI",
                    "Yield strength",
                ),
                (
                    "compressive_strength",
                    "mechanical",
                    0.0,
                    3000.0,
                    "compressive strength",
                    "σ_c",
                    "SI",
                    "Compressive strength",
                ),
                (
                    "shear_strength",
                    "mechanical",
                    0.0,
                    1800.0,
                    "shear strength",
                    "τ",
                    "SI",
                    "Shear strength",
                ),
                (
                    "youngs_modulus",
                    "mechanical",
                    0.0,
                    700.0,
                    "Young's modulus",
                    "E",
                    "SI",
                    "Elastic modulus",
                ),
                (
                    "poisson_ratio",
                    "mechanical",
                    -1.0,
                    0.5,
                    "Poisson's ratio",
                    "ν",
                    "SI",
                    "Poisson's ratio",
                ),
                (
                    "hardness_brinell",
                    "mechanical",
                    0.0,
                    1000.0,
                    "Brinell hardness",
                    "HB",
                    "SI",
                    "Brinell hardness number",
                ),
                (
                    "hardness_rockwell",
                    "mechanical",
                    0.0,
                    100.0,
                    "Rockwell hardness",
                    "HR",
                    "SI",
                    "Rockwell hardness scale",
                ),
                (
                    "hardness_vickers",
                    "mechanical",
                    0.0,
                    3000.0,
                    "Vickers hardness",
                    "HV",
                    "SI",
                    "Vickers hardness number",
                ),
                (
                    "elongation",
                    "mechanical",
                    0.0,
                    100.0,
                    "elongation at break",
                    "ε",
                    "SI",
                    "Percent elongation",
                ),
                (
                    "impact_toughness",
                    "mechanical",
                    0.0,
                    300.0,
                    "impact toughness",
                    "K",
                    "SI",
                    "Impact toughness",
                ),
                (
                    "fatigue_limit",
                    "mechanical",
                    0.0,
                    1200.0,
                    "fatigue limit",
                    "σ_f",
                    "SI",
                    "Fatigue endurance limit",
                ),
                (
                    "fracture_toughness",
                    "mechanical",
                    0.0,
                    220.0,
                    "fracture toughness",
                    "K_IC",
                    "SI",
                    "Plane strain fracture toughness",
                ),
                (
                    "electrical_resistivity",
                    "electrical",
                    0.0,
                    1e17,
                    "electrical resistivity",
                    "ρ",
                    "SI",
                    "Electrical resistivity",
                ),
                (
                    "electrical_conductivity",
                    "electrical",
                    0.0,
                    100000000.0,
                    "electrical conductivity",
                    "σ",
                    "SI",
                    "Electrical conductivity",
                ),
                (
                    "dielectric_strength",
                    "electrical",
                    0.0,
                    100.0,
                    "dielectric strength",
                    "E_d",
                    "SI",
                    "Dielectric breakdown strength",
                ),
                (
                    "relative_permittivity",
                    "electrical",
                    1.0,
                    100.0,
                    "relative permittivity",
                    "ε_r",
                    "SI",
                    "Relative permittivity",
                ),
                (
                    "magnetic_permeability",
                    "magnetic",
                    0.0,
                    100000.0,
                    "magnetic permeability",
                    "μ",
                    "SI",
                    "Magnetic permeability",
                ),
                (
                    "magnetic_susceptibility",
                    "magnetic",
                    -50.0,
                    50.0,
                    "magnetic susceptibility",
                    "χ",
                    "SI",
                    "Magnetic susceptibility",
                ),
                (
                    "corrosion_resistance",
                    "chemical",
                    0.0,
                    100.0,
                    "corrosion resistance class",
                    "",
                    "qualitative",
                    "Corrosion resistance rating",
                ),
                (
                    "uv_resistance",
                    "environmental",
                    0.0,
                    1.0,
                    "UV resistance",
                    "",
                    "boolean",
                    "UV resistance flag",
                ),
                (
                    "weather_resistance",
                    "environmental",
                    0.0,
                    1.0,
                    "weather resistance",
                    "",
                    "boolean",
                    "Weather resistance flag",
                ),
                (
                    "fire_rating",
                    "safety",
                    1.0,
                    4.0,
                    "fire rating class",
                    "",
                    "qualitative",
                    "Fire resistance rating",
                ),
                (
                    "flammability",
                    "safety",
                    0.0,
                    100.0,
                    "flammability class",
                    "",
                    "qualitative",
                    "Flammability rating",
                ),
                (
                    "autoignition_temp",
                    "thermal",
                    0.0,
                    1500.0,
                    "autoignition temperature",
                    "T_ig",
                    "SI",
                    "Autoignition temperature",
                ),
                (
                    "viscosity",
                    "fluid",
                    0.0,
                    100000.0,
                    "dynamic viscosity",
                    "η",
                    "SI",
                    "Dynamic viscosity",
                ),
                (
                    "surface_tension",
                    "fluid",
                    0.0,
                    1000.0,
                    "surface tension",
                    "γ",
                    "SI",
                    "Surface tension",
                ),
                (
                    "vapor_pressure",
                    "fluid",
                    0.0,
                    1000.0,
                    "vapor pressure",
                    "P_v",
                    "SI",
                    "Vapor pressure",
                ),
                (
                    "solubility",
                    "chemical",
                    0.0,
                    100.0,
                    "solubility",
                    "",
                    "qualitative",
                    "Solubility description",
                ),
                (
                    "ph",
                    "chemical",
                    0.0,
                    14.0,
                    "pH",
                    "pH",
                    "SI",
                    "Acidity/alkalinity",
                ),
                (
                    "sound_velocity",
                    "acoustic",
                    0.0,
                    20000.0,
                    "speed of sound",
                    "c",
                    "SI",
                    "Speed of sound in material",
                ),
                (
                    "acoustic_impedance",
                    "acoustic",
                    0.0,
                    100000000.0,
                    "acoustic impedance",
                    "Z",
                    "SI",
                    "Acoustic impedance",
                ),
                (
                    "damping_coefficient",
                    "acoustic",
                    0.0,
                    1.0,
                    "damping coefficient",
                    "δ",
                    "SI",
                    "Damping coefficient",
                ),
                (
                    "radioactivity",
                    "nuclear",
                    0.0,
                    1000.0,
                    "specific activity",
                    "A",
                    "SI",
                    "Radioactivity per unit mass",
                ),
                (
                    "half_life",
                    "nuclear",
                    0.0,
                    10000000000.0,
                    "half-life",
                    "t_½",
                    "SI",
                    "Radioactive half-life",
                ),
                (
                    "cost_per_kg",
                    "economic",
                    0.0,
                    5000.0,
                    "cost per mass",
                    "C_m",
                    "currency/kg",
                    "Material cost per kilogram",
                ),
                (
                    "cost_per_m3",
                    "economic",
                    0.0,
                    10000000.0,
                    "cost per volume",
                    "C_v",
                    "currency/m³",
                    "Material cost per cubic meter",
                ),
                (
                    "embodied_energy",
                    "environmental",
                    0.0,
                    100000.0,
                    "embodied energy",
                    "E_e",
                    "MJ/kg",
                    "Embodied energy per mass",
                ),
                (
                    "carbon_footprint",
                    "environmental",
                    0.0,
                    1000.0,
                    "carbon footprint",
                    "CF",
                    "kg CO₂e/kg",
                    "Carbon footprint per mass",
                ),
                (
                    "recyclability",
                    "environmental",
                    0.0,
                    100.0,
                    "recyclability",
                    "R",
                    "percent",
                    "Recyclability percentage",
                ),
                (
                    "warranty_period",
                    "manufacturing",
                    0.0,
                    30.0,
                    "warranty period",
                    "t_w",
                    "days",
                    "Warranty period in days",
                ),
                (
                    "transparency",
                    "optical",
                    0.0,
                    1.0,
                    "transparency",
                    "τ",
                    "SI",
                    "Optical transparency",
                ),
                (
                    "reflectivity",
                    "optical",
                    0.0,
                    1.0,
                    "reflectivity",
                    "R",
                    "SI",
                    "Optical reflectivity",
                ),
                (
                    "color",
                    "optical",
                    None,
                    None,
                    "color",
                    "",
                    "qualitative",
                    "Color description",
                ),
            ]
            for p in params:
                conn.exec_driver_sql(
                    "INSERT OR IGNORE INTO parameters (par_name, par_category, min_value, max_value, mea_name, mea_symbol, mea_system, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    p,
                )

        tables = {
            row[0]
            for row in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "item_parameters" in tables:
            ip_existing = {
                row[1]
                for row in conn.exec_driver_sql("PRAGMA table_info(item_parameters)")
            }
            for col, ddl in {
                "base_value": "ALTER TABLE item_parameters ADD COLUMN base_value FLOAT",
                "min_value": "ALTER TABLE item_parameters ADD COLUMN min_value FLOAT",
                "max_value": "ALTER TABLE item_parameters ADD COLUMN max_value FLOAT",
            }.items():
                if col not in ip_existing:
                    conn.exec_driver_sql(ddl)
        if "item_parameters" not in tables:
            conn.exec_driver_sql("""
                CREATE TABLE item_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    par_id INTEGER NOT NULL,
                    value FLOAT,
                    value_text VARCHAR,
                    unit_override VARCHAR,
                    source VARCHAR NOT NULL DEFAULT 'manual',
                    confidence FLOAT NOT NULL DEFAULT 1.0,
                    base_value FLOAT,
                    min_value FLOAT,
                    max_value FLOAT,
                    measured_at DATETIME,
                    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE,
                    FOREIGN KEY(par_id) REFERENCES parameters(id) ON DELETE CASCADE,
                    UNIQUE(item_id, par_id)
                )
            """)
            conn.exec_driver_sql(
                "CREATE INDEX ix_item_parameters_item_id ON item_parameters(item_id)"
            )
            conn.exec_driver_sql(
                "CREATE INDEX ix_item_parameters_par_id ON item_parameters(par_id)"
            )

        if "events" not in tables:
            conn.exec_driver_sql("""
                CREATE TABLE events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL,
                    description VARCHAR NOT NULL DEFAULT '',
                    event_per_10msec FLOAT NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                    updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.exec_driver_sql("CREATE UNIQUE INDEX ix_events_name ON events(name)")
        if "event_abilities" not in tables:
            conn.exec_driver_sql("""
                CREATE TABLE event_abilities (
                    event_id INTEGER NOT NULL,
                    ability_id INTEGER NOT NULL,
                    PRIMARY KEY (event_id, ability_id),
                    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
                    FOREIGN KEY(ability_id) REFERENCES abilities(id) ON DELETE CASCADE
                )
            """)
            conn.exec_driver_sql(
                "CREATE INDEX ix_event_abilities_event_id ON event_abilities(event_id)"
            )
            conn.exec_driver_sql(
                "CREATE INDEX ix_event_abilities_ability_id ON event_abilities(ability_id)"
            )


migrate_schema()


def ensure_db_writable() -> None:
    DB_PATH.touch(exist_ok=True)
    try:
        os.chmod(DB_PATH, 0o666)
        os.chmod(DATA_DIR, 0o777)
    except PermissionError:
        pass
    engine.dispose()
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise RuntimeError(
            f"SQLite database is not writable at {DB_PATH}. "
            f"Fix permissions: chmod 666 {DB_PATH} (and ensure {DATA_DIR} is writable)."
        ) from exc


def _item_exists(db: Session, name: str, parent_id: int | None = None) -> bool:
    return (
        db.scalar(
            select(ItemDB.id)
            .where(ItemDB.name == name, ItemDB.parent_id == parent_id)
            .limit(1)
        )
        is not None
    )


def seed_static_items(db: Session) -> int:
    """Create any static catalog items that are missing from the database.

    Returns the number of rows created (parts + catalog items + subitems).
    """
    created = 0
    for part in ALL_PARTS:
        existing = db.scalar(
            select(ItemDB)
            .where(ItemDB.name == part, ItemDB.parent_id.is_(None))
            .limit(1)
        )
        if existing is None:
            db.add(ItemDB(name=part, price=5.0))
            created += 1
        elif existing.price <= 0:
            existing.price = 5.0
            created += 1

    db.flush()

    for spec in STATIC_ITEMS:
        if not _item_exists(db, spec.name):
            db.add(
                ItemDB(
                    name=spec.name,
                    price=spec.price,
                    is_offer=spec.is_offer,
                    subitems=[ItemDB(name=s) for s in spec.subitems],
                )
            )
            created += 1 + len(spec.subitems)
        else:
            parent = db.scalar(
                select(ItemDB).where(
                    ItemDB.name == spec.name, ItemDB.parent_id.is_(None)
                )
            )
            for sub in spec.subitems:
                if parent is not None and not _item_exists(db, sub, parent.id):
                    db.add(ItemDB(name=sub, parent_id=parent.id))
                    created += 1

    db.commit()
    return created


def seed_example_data(db: Session) -> int:
    return seed_static_items(db)


def link_item_parameters(db: Session) -> int:
    """Link every parameter to every item in the database.

    Populates ``item_parameters`` rows with a best-effort current value derived
    from the item's existing fields where an obvious mapping exists (weight ->
    mass, color -> color, hp -> hp), and NULL otherwise. Existing links are
    left untouched.

    Returns the number of link rows created.
    """
    params = {p.par_name: p for p in db.scalars(select(ParameterDB)).all()}
    items = db.scalars(select(ItemDB)).all()

    def field_value(item: ItemDB, par_name: str):
        """Return (numeric_value, text_value) derived from item fields."""
        mapping = {
            "mass": (item.weight, None),
            "density": (item.weight, None),
            "temperature": (293.15, None),
            "color": (None, item.color or None),
            "length": (None, item.size or None),
        }
        return mapping.get(par_name, (None, None))

    created = 0
    for item in items:
        for par_name, par in params.items():
            existing = db.scalar(
                select(ItemParameterDB).where(
                    ItemParameterDB.item_id == item.id,
                    ItemParameterDB.par_id == par.id,
                )
            )
            if existing is not None:
                continue
            num_value, text_value = field_value(item, par_name)
            db.add(
                ItemParameterDB(
                    item_id=item.id,
                    par_id=par.id,
                    value=num_value,
                    value_text=text_value,
                    source="derived"
                    if (num_value is not None or text_value is not None)
                    else "unset",
                )
            )
            created += 1
    db.commit()
    return created


def ability_options(abilities) -> list[dict]:
    return [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "description_ru": a.description_ru,
            "params": {
                ap.parameter.par_name: {
                    "operation": ap.operation,
                    "base_value": ap.base_value,
                    "min_value": ap.min_value,
                    "max_value": ap.max_value,
                    "curve": ap.curve,
                    "stack_mode": ap.stack_mode,
                    "priority": ap.priority,
                    "enabled": ap.enabled,
                    "modify_coefficient_per_10msec": ap.modify_coefficient_per_10msec,
                    "description": ap.description,
                }
                for ap in a.ability_params
                if ap.parameter
            },
        }
        for a in abilities
    ]


def seed_abilities(db: Session) -> int:
    """Create any static ability verbs that are missing from the database.

    Returns the number of ability rows created.
    """
    created = 0
    new = []
    for spec in ABILITIES:
        existing = db.scalar(
            select(AbilityDB).where(AbilityDB.name == spec.name).limit(1)
        )
        if existing is None:
            new.append(spec)
            db.add(
                AbilityDB(
                    name=spec.name,
                    description=spec.description,
                    description_ru=spec.description_ru,
                    category=spec.category or ability_category(spec.name),
                )
            )
            created += 1
        else:
            if existing.description_ru != spec.description_ru:
                existing.description_ru = spec.description_ru
            if existing.description != spec.description:
                existing.description = spec.description
            target_cat = spec.category or ability_category(spec.name)
            if existing.category != target_cat:
                existing.category = target_cat
    db.commit()
    sync_ability_categories(db)
    return created, new


def sync_ability_categories(db: Session) -> int:
    """Ensure the ability_category table mirrors each ability's category.

    For every ability that already has a category, drop existing category rows
    and insert a fresh one, so the link table never goes stale.
    """
    abilities = db.scalars(select(AbilityDB)).all()
    synced = 0
    for ab in abilities:
        if not ab.category:
            continue
        for link in list(ab.categories):
            db.delete(link)
        db.flush()
        db.add(
            AbilityCategoryDB(
                ability_id=ab.id,
                category=ab.category,
            )
        )
        synced += 1
    db.commit()
    return synced


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_db_writable()
    with SessionLocal() as db:
        # created = seed_example_data(db)
        # if created:
        #     logger.info("Runtime seed: created %s static item(s).", created)
        # linked = link_item_parameters(db)
        # if linked:
        #     logger.info("Runtime seed: linked %s item-parameter row(s).", linked)
        # ability_count, new_abilities = seed_abilities(db)
        if False:
            logger.info(
                "Runtime seed: created {countd} ability(ies) [{new_abilities.join(', ')}].",
                extra={"new_abilities": new_abilities, "countd": ability_count},
            )
        else:
            yx = time.perf_counter() * 1000000.0
            since = "[Yx:" + str(yx).rjust(22).replace("67", "14").replace("31", "43")
            since += "]"
            since += "\n"
            since += "\t[zT:" + str(time.perf_counter() * 1000000000.0 - yx).rjust(
                22
            ).replace("67", "14").replace("31", "43")
            since += "]"
            since += "\n"
            since += "\t[LC: " + str(
                "V0->LC3<-C0<-->L"
                + bytes(since, encoding="utf-8")
                .hex("|")
                .split("|")[random.randint(0, 8)]
                + "]"
            ).rjust(22)
            logger.info(
                f"Pruinetime seed <-> huston -> we have a unnotable probes <-> sing e -> \n\t{since}"
            )

    # Auto-start the war-factory loop when explicitly enabled (default off so
    # that tests / one-shot runs stay deterministic). Set
    # WAR_FACTORY_AUTOSTART=1 to evolve the warehouse in the background.
    autostart = os.environ.get("WAR_FACTORY_AUTOSTART", "0").strip().lower()
    if autostart not in ("", "0", "false", "no", "off"):
        try:
            from war_factory import war_factory_daemon as _wf_daemon

            _wf_daemon.start()
            logger.info("War-factory auto-loop enabled (WAR_FACTORY_AUTOSTART).")
        except Exception:  # pragma: no cover - defensive
            logger.exception("war-factory autostart failed")

    yield

    # Stop the background loop cleanly on shutdown (never pkill).
    try:
        from war_factory import war_factory_daemon as _wf_daemon

        _wf_daemon.stop()
    except Exception:  # pragma: no cover - defensive
        logger.exception("war-factory stop on shutdown failed")


app = FastAPI(title="Combat FAST API", version=str(APP_VERSION), lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def csrf_protect(request: Request, call_next):
    """Set a daily-rotating CSRF cookie and verify it on HTML form POSTs.

    JSON API calls (anything not a urlencoded/multipart form submission) are
    left untouched so REST endpoints keep working without a token.
    """
    name = csrf_cookie_name()
    ctype = request.headers.get("content-type") or ""
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and (
        "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype
    ):
        form = await request.form()
        request.state.form_data = form
        cookie = request.cookies.get(name)
        sent = form.get("csrftoken") or request.headers.get("X-CSRFToken")
        if not cookie or not sent or not secrets.compare_digest(cookie, sent):
            return JSONResponse(
                {"detail": "CSRF token invalid or missing."}, status_code=403
            )

    token = get_csrf_token(request)
    response = await call_next(request)
    response.set_cookie(
        name,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24,
    )
    return response


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def profile_step(request: Request, name: str) -> None:
    """Record elapsed time since the previous profiling step."""
    prof = request.state.profile
    now = time.perf_counter()
    prof["steps"].append([name, round((now - prof["last"]) * 1000, 2)])
    prof["last"] = now


def _db_time_ms() -> float:
    return sum(_db_start.values()) * 1000


def _reset_db_time() -> None:
    _db_start.clear()


@app.middleware("http")
async def profile_requests(request: Request, call_next):
    start = time.perf_counter()
    _reset_db_time()
    request.state.profile = {"steps": [], "last": start}
    response = await call_next(request)
    total = (time.perf_counter() - start) * 1000
    steps = request.state.profile["steps"]
    accounted = round(sum(s[1] for s in steps), 2)
    middleware = round(max(total - accounted, 0.0), 2)
    profile = {
        "method": request.method,
        "path": request.url.path,
        "steps": steps
        + [
            ["db", round(_db_time_ms(), 2)],
            ["middleware", middleware],
            ["total", round(total, 2)],
        ],
    }
    logger.info(
        "PROFILE %s %s total=%.2fms mw=%.2fms",
        request.method,
        request.url.path,
        total,
        middleware,
    )
    response.headers["X-Process-Time"] = f"{total:.2f}"
    response.headers["X-Profile"] = json.dumps(profile)
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type:
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        script = "<script>window.__lastProfile = " + json.dumps(profile) + ";</script>"
        body = body.replace(b"</body>", script.encode() + b"</body>", 1)
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
        )
    return response


class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    quantity: int = Field(default=1, ge=1)
    is_offer: bool = False
    color: str = Field(default="", max_length=20)
    size: str = Field(default="", max_length=20)
    weight: float = Field(default=0.0, ge=0)
    hp: float = Field(default=100.0, ge=0)
    is_anti_emc: bool = False
    is_proof: bool = False
    water_resistant: bool = False
    oil: float = Field(default=0.0, ge=0)
    self_desentry: bool = False
    is_parasite: bool = False
    parasite_chance: int = Field(default=0, ge=0, le=90)
    revision: int = Field(default=1, ge=1)


class SubItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    quantity: int = Field(default=1, ge=1)
    hp: float = Field(default=100.0, ge=0)
    is_parasite: bool = False
    parasite_chance: int = Field(default=0, ge=0, le=90)
    revision: int = Field(default=1, ge=1)


SubItemCreate = SubItemBase


class SubItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    quantity: int | None = Field(default=None, ge=1)
    hp: float | None = Field(default=None, ge=0)
    is_parasite: bool | None = None
    parasite_chance: int | None = Field(default=None, ge=0, le=90)
    revision: int | None = Field(default=None, ge=1)


class SubItem(SubItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    parent_id: int
    added_at: datetime
    updated_at: datetime


class ItemCreate(ItemBase):
    subitems: list[SubItemCreate] = Field(default_factory=list)


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    price: float | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=1)
    is_offer: bool | None = None
    color: str | None = Field(default=None, max_length=20)
    size: str | None = Field(default=None, max_length=20)
    weight: float | None = Field(default=None, ge=0)
    hp: float | None = Field(default=None, ge=0)
    is_anti_emc: bool | None = None
    is_proof: bool | None = None
    water_resistant: bool | None = None
    oil: float | None = Field(default=None, ge=0)
    self_desentry: bool | None = None
    is_parasite: bool | None = None
    parasite_chance: int | None = Field(default=None, ge=0, le=90)
    revision: int | None = Field(default=None, ge=1)


class Item(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    added_at: datetime
    updated_at: datetime
    subitems: list[SubItem] = Field(default_factory=list)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_item_or_404(item_id: int, db: Session) -> ItemDB:
    item = db.scalar(
        select(ItemDB)
        .options(selectinload(ItemDB.subitems))
        .where(ItemDB.id == item_id)
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unit {item_id} not found",
        )
    return item


def get_subitem_or_404(item: ItemDB, subitem_id: int, db: Session) -> ItemDB:
    subitem = db.scalar(select(ItemDB).where(ItemDB.id == subitem_id))
    if subitem is None or subitem.parent_id != item.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subitem {subitem_id} not found",
        )
    return subitem


class ItemFormError(Exception):
    def __init__(self, url) -> None:
        self.url = url
        super().__init__("Invalid form input")


@app.exception_handler(ItemFormError)
def handle_item_form_error(request: Request, exc: ItemFormError) -> RedirectResponse:
    return redirect_with_error(exc.url, "Invalid input")


def _form_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on", "checked")


def item_form_dep(endpoint: str):
    """Collect the item form fields into an ItemCreate; redirect on invalid input.

    Reads from request.state.form_data (populated by the CSRF middleware,
    which has already consumed the request body) rather than FastAPI Form()
    params, since the body is no longer re-readable after the middleware.
    """

    async def dep(request: Request) -> ItemCreate:
        try:
            form = getattr(request.state, "form_data", None)
            if form is None:
                form = await request.form()
            g = form.get
            return ItemCreate(
                name=g("name", ""),
                price=float(g("price", "")) if g("price") else 0.0,
                quantity=int(g("quantity")) if g("quantity") else 1,
                is_offer=_form_bool(g("is_offer")),
                color=g("color", ""),
                size=g("size", ""),
                weight=float(g("weight")) if g("weight") else 0.0,
                hp=float(g("hp")) if g("hp") else 100.0,
                is_anti_emc=_form_bool(g("is_anti_emc")),
                is_proof=_form_bool(g("is_proof")),
                water_resistant=_form_bool(g("water_resistant")),
                oil=float(g("oil")) if g("oil") else 0.0,
                self_desentry=_form_bool(g("self_desentry")),
                is_parasite=_form_bool(g("is_parasite")),
                parasite_chance=int(g("parasite_chance"))
                if g("parasite_chance")
                else 0,
                revision=int(g("revision")) if g("revision") else 1,
            )
        except ValueError:
            raise ItemFormError(request.url_for(endpoint, **request.path_params))

    return dep


def redirect_with_error(url, message: str) -> RedirectResponse:
    return RedirectResponse(url.include_query_params(error=message), status_code=303)


class ItemFilter(BaseModel):
    q: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    is_offer: str | None = None
    color: str | None = None
    size: str | None = None
    weight_min: float | None = None
    weight_max: float | None = None
    hp_min: float | None = None
    hp_max: float | None = None
    is_anti_emc: str | None = None
    is_proof: str | None = None
    water_resistant: str | None = None
    oil_min: float | None = None
    oil_max: float | None = None
    quantity_min: int | None = None
    quantity_max: int | None = None
    self_desentry: str | None = None
    is_parasite: str | None = None
    parasite_chance_min: int | None = None
    parasite_chance_max: int | None = None
    revision: str | None = None
    ability: list[str] = Field(default_factory=list)
    sort: str = "id"
    order: str = "asc"


SORT_COLUMNS = {
    "id": ItemDB.id,
    "name": ItemDB.name,
    "price": ItemDB.price,
    "quantity": ItemDB.quantity,
    "is_offer": ItemDB.is_offer,
    "color": ItemDB.color,
    "size": ItemDB.size,
    "weight": ItemDB.weight,
    "hp": ItemDB.hp,
    "is_anti_emc": ItemDB.is_anti_emc,
    "is_proof": ItemDB.is_proof,
    "water_resistant": ItemDB.water_resistant,
    "oil": ItemDB.oil,
    "self_desentry": ItemDB.self_desentry,
    "is_parasite": ItemDB.is_parasite,
    "parasite_chance": ItemDB.parasite_chance,
    "revision": ItemDB.revision,
    "added_at": ItemDB.added_at,
    "updated_at": ItemDB.updated_at,
}
SORT_PATTERN = "^(" + "|".join(SORT_COLUMNS.keys()) + ")$"


def _parse_bool(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    if value.strip().lower() in ("1", "true", "yes", "on"):
        return True
    if value.strip().lower() in ("0", "false", "no", "off"):
        return False
    return None


def items_filter(
    q: str | None = Query(default=None, max_length=50),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    is_offer: str | None = Query(default=None),
    color: str | None = Query(default=None, max_length=20),
    size: str | None = Query(default=None, max_length=20),
    weight_min: float | None = Query(default=None, ge=0),
    weight_max: float | None = Query(default=None, ge=0),
    hp_min: float | None = Query(default=None, ge=0),
    hp_max: float | None = Query(default=None, ge=0),
    is_anti_emc: str | None = Query(default=None),
    is_proof: str | None = Query(default=None),
    water_resistant: str | None = Query(default=None),
    oil_min: float | None = Query(default=None, ge=0),
    oil_max: float | None = Query(default=None, ge=0),
    quantity_min: int | None = Query(default=None, ge=0),
    quantity_max: int | None = Query(default=None, ge=0),
    self_desentry: str | None = Query(default=None),
    is_parasite: str | None = Query(default=None),
    revision: str | None = Query(default=None),
    parasite_chance_min: int | None = Query(default=None, ge=0, le=90),
    parasite_chance_max: int | None = Query(default=None, ge=0, le=90),
    ability: list[str] = Query(default=[]),
    sort: str = Query(default="id", pattern=SORT_PATTERN),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> ItemFilter:
    filt = ItemFilter(
        q=q,
        min_price=min_price,
        max_price=max_price,
        is_offer=is_offer,
        color=color,
        size=size,
        weight_min=weight_min,
        weight_max=weight_max,
        hp_min=hp_min,
        hp_max=hp_max,
        is_anti_emc=is_anti_emc,
        is_proof=is_proof,
        water_resistant=water_resistant,
        oil_min=oil_min,
        oil_max=oil_max,
        quantity_min=quantity_min,
        quantity_max=quantity_max,
        self_desentry=self_desentry,
        is_parasite=is_parasite,
        revision=revision,
        parasite_chance_min=parasite_chance_min,
        parasite_chance_max=parasite_chance_max,
        ability=ability,
        sort=sort,
        order=order,
    )
    logger.info(
        "filters: q=%s min_price=%s max_price=%s is_offer=%s color=%s size=%s weight=%s-%s hp=%s-%s anti_emc=%s proof=%s water=%s oil=%s-%s qty=%s-%s sd=%s parasite=%s pchance=%s-%s rev=%s sort=%s %s",
        filt.q,
        filt.min_price,
        filt.max_price,
        filt.is_offer,
        filt.color,
        filt.size,
        filt.weight_min,
        filt.weight_max,
        filt.hp_min,
        filt.hp_max,
        filt.is_anti_emc,
        filt.is_proof,
        filt.water_resistant,
        filt.oil_min,
        filt.oil_max,
        filt.quantity_min,
        filt.quantity_max,
        filt.self_desentry,
        filt.is_parasite,
        filt.parasite_chance_min,
        filt.parasite_chance_max,
        filt.revision,
        filt.sort,
        filt.order,
    )
    return filt


def _is_root_item():
    """True for top-level units: parent_id is 0, empty, or NULL."""
    return or_(ItemDB.parent_id.is_(None), ItemDB.parent_id == 0, ItemDB.parent_id == "")


def filtered_items_select(filt: ItemFilter) -> select:
    stmt = select(ItemDB).where(_is_root_item())
    if filt.q:
        stmt = stmt.where(ItemDB.name.ilike(f"%{filt.q}%"))
    if filt.min_price is not None:
        stmt = stmt.where(ItemDB.price >= filt.min_price)
    if filt.max_price is not None:
        stmt = stmt.where(ItemDB.price <= filt.max_price)
    if filt.color:
        stmt = stmt.where(ItemDB.color == filt.color)
    if filt.size:
        stmt = stmt.where(ItemDB.size == filt.size)
    if filt.weight_min is not None:
        stmt = stmt.where(ItemDB.weight >= filt.weight_min)
    if filt.weight_max is not None:
        stmt = stmt.where(ItemDB.weight <= filt.weight_max)
    if filt.hp_min is not None:
        stmt = stmt.where(ItemDB.hp >= filt.hp_min)
    if filt.hp_max is not None:
        stmt = stmt.where(ItemDB.hp <= filt.hp_max)
    if (offer := _parse_bool(filt.is_offer)) is not None:
        stmt = stmt.where(ItemDB.is_offer == offer)
    if (anti := _parse_bool(filt.is_anti_emc)) is not None:
        stmt = stmt.where(ItemDB.is_anti_emc == anti)
    if (proof := _parse_bool(filt.is_proof)) is not None:
        stmt = stmt.where(ItemDB.is_proof == proof)
    if (water := _parse_bool(filt.water_resistant)) is not None:
        stmt = stmt.where(ItemDB.water_resistant == water)
    if filt.oil_min is not None:
        stmt = stmt.where(ItemDB.oil >= filt.oil_min)
    if filt.oil_max is not None:
        stmt = stmt.where(ItemDB.oil <= filt.oil_max)
    if (sd := _parse_bool(filt.self_desentry)) is not None:
        stmt = stmt.where(ItemDB.self_desentry == sd)
    if (para := _parse_bool(filt.is_parasite)) is not None:
        stmt = stmt.where(ItemDB.is_parasite == para)
    if filt.parasite_chance_min is not None:
        stmt = stmt.where(ItemDB.parasite_chance >= filt.parasite_chance_min)
    if filt.parasite_chance_max is not None:
        stmt = stmt.where(ItemDB.parasite_chance <= filt.parasite_chance_max)
    if filt.quantity_min is not None:
        stmt = stmt.where(ItemDB.quantity >= filt.quantity_min)
    if filt.quantity_max is not None:
        stmt = stmt.where(ItemDB.quantity <= filt.quantity_max)
    if filt.revision is not None and filt.revision.strip():
        try:
            rev = int(filt.revision)
        except ValueError:
            rev = None
        if rev is not None:
            stmt = stmt.where(ItemDB.revision == rev)
    for ability_name in filt.ability:
        if ability_name:
            stmt = stmt.where(ItemDB.abilities.any(AbilityDB.name == ability_name))
    return stmt


def build_items_query(filt: ItemFilter) -> select:
    stmt = filtered_items_select(filt)
    column = SORT_COLUMNS[filt.sort]
    stmt = stmt.order_by(column.desc() if filt.order == "desc" else column.asc())
    return stmt.options(selectinload(ItemDB.subitems))


@app.get("/items", response_model=list[Item])
def list_items(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=10000),
    filt: ItemFilter = Depends(items_filter),
    db: Session = Depends(get_db),
) -> list[Item]:
    stmt = build_items_query(filt).offset(skip).limit(limit)
    items = db.scalars(stmt).all()
    profile_step(request, "query")
    return items


@app.get("/items/{item_id}", response_model=Item)
def get_item(
    request: Request,
    item_id: int = Path(ge=1),
    db: Session = Depends(get_db),
) -> Item:
    item = get_item_or_404(item_id, db)
    profile_step(request, "query")
    return item


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(
    request: Request, item: ItemCreate, db: Session = Depends(get_db)
) -> Item:
    logger.info(
        "POST /items name=%s price=%s color=%s size=%s",
        item.name,
        item.price,
        item.color,
        item.size,
    )
    payload = item.model_dump(exclude={"subitems"})
    db_item = ItemDB(**payload)
    db_item.subitems = [ItemDB(**s.model_dump()) for s in item.subitems]
    db.add(db_item)
    db.commit()
    profile_step(request, "commit")
    db.refresh(db_item)
    logger.info("POST /items -> created id=%s", db_item.id)
    return db_item


@app.put("/items/{item_id}", response_model=Item)
def replace_item(
    request: Request,
    item_id: int,
    item: ItemCreate,
    db: Session = Depends(get_db),
) -> Item:
    db_item = get_item_or_404(item_id, db)
    payload = item.model_dump(exclude={"subitems"})
    for field, value in payload.items():
        setattr(db_item, field, value)
    db_item.subitems = [ItemDB(**s.model_dump()) for s in item.subitems]
    db.commit()
    profile_step(request, "commit")
    db.refresh(db_item)
    return db_item


@app.patch("/items/{item_id}", response_model=Item)
def update_item(
    request: Request,
    item_id: int,
    patch: ItemUpdate,
    db: Session = Depends(get_db),
) -> Item:
    changes = patch.model_dump(exclude_unset=True)
    logger.info("PATCH /items/%s changes=%s", item_id, changes)
    db_item = get_item_or_404(item_id, db)
    for field, value in changes.items():
        setattr(db_item, field, value)
    db.commit()
    profile_step(request, "commit")
    db.refresh(db_item)
    logger.info(
        "PATCH /items/%s -> ok price=%s offer=%s proof=%s",
        item_id,
        db_item.price,
        db_item.is_offer,
        db_item.is_proof,
    )
    return db_item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
) -> None:
    db_item = get_item_or_404(item_id, db)
    db.delete(db_item)
    db.commit()
    profile_step(request, "commit")


@app.get("/items/{item_id}/subitems", response_model=list[SubItem])
def list_subitems(
    request: Request,
    item_id: int = Path(ge=1),
    db: Session = Depends(get_db),
) -> list[SubItem]:
    get_item_or_404(item_id, db)
    items = db.scalars(select(ItemDB).where(ItemDB.parent_id == item_id)).all()
    profile_step(request, "query")
    return items


@app.get("/items/{item_id}/subitems/{subitem_id}", response_model=SubItem)
def get_subitem(
    request: Request,
    item_id: int = Path(ge=1),
    subitem_id: int = Path(ge=1),
    db: Session = Depends(get_db),
) -> SubItem:
    sub = get_subitem_or_404(get_item_or_404(item_id, db), subitem_id, db)
    profile_step(request, "query")
    return sub


@app.post(
    "/items/{item_id}/subitems",
    response_model=SubItem,
    status_code=status.HTTP_201_CREATED,
)
def create_subitem(
    request: Request,
    item_id: int = Path(ge=1),
    subitem: SubItemCreate = ...,
    db: Session = Depends(get_db),
) -> SubItem:
    logger.info(
        "POST /items/%s/subitems name=%s qty=%s",
        item_id,
        subitem.name,
        subitem.quantity,
    )
    item = get_item_or_404(item_id, db)
    db_subitem = ItemDB(parent_id=item.id, **subitem.model_dump())
    db.add(db_subitem)
    db.commit()
    profile_step(request, "commit")
    db.refresh(db_subitem)
    return db_subitem


@app.put("/items/{item_id}/subitems/{subitem_id}", response_model=SubItem)
def replace_subitem(
    request: Request,
    item_id: int = Path(ge=1),
    subitem_id: int = Path(ge=1),
    subitem: SubItemCreate = ...,
    db: Session = Depends(get_db),
) -> SubItem:
    logger.info(
        "PUT /items/%s/subitems/%s name=%s qty=%s",
        item_id,
        subitem_id,
        subitem.name,
        subitem.quantity,
    )
    item = get_item_or_404(item_id, db)
    db_subitem = get_subitem_or_404(item, subitem_id, db)
    for field, value in subitem.model_dump().items():
        setattr(db_subitem, field, value)
    db.commit()
    profile_step(request, "commit")
    db.refresh(db_subitem)
    return db_subitem


@app.patch("/items/{item_id}/subitems/{subitem_id}", response_model=SubItem)
def update_subitem(
    request: Request,
    item_id: int = Path(ge=1),
    subitem_id: int = Path(ge=1),
    patch: SubItemUpdate = ...,
    db: Session = Depends(get_db),
) -> SubItem:
    changes = patch.model_dump(exclude_unset=True)
    logger.info("PATCH /items/%s/subitems/%s changes=%s", item_id, subitem_id, changes)
    item = get_item_or_404(item_id, db)
    db_subitem = get_subitem_or_404(item, subitem_id, db)
    for field, value in changes.items():
        setattr(db_subitem, field, value)
    db.commit()
    profile_step(request, "commit")
    db.refresh(db_subitem)
    logger.info(
        "PATCH /items/%s/subitems/%s -> ok qty=%s",
        item_id,
        subitem_id,
        db_subitem.quantity,
    )
    return db_subitem


@app.delete(
    "/items/{item_id}/subitems/{subitem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_subitem(
    request: Request,
    item_id: int = Path(ge=1),
    subitem_id: int = Path(ge=1),
    db: Session = Depends(get_db),
) -> None:
    item = get_item_or_404(item_id, db)
    db_subitem = get_subitem_or_404(item, subitem_id, db)
    db.delete(db_subitem)
    db.commit()
    profile_step(request, "commit")


@app.get("/")
def read_root() -> dict[str, str]:
    return RedirectResponse("/ui/combat-duel")
    # return {"message": "Items REST API", "docs": "/docs", "ui": "/ui"}


@app.get("/ui/warehouse", response_class=HTMLResponse)
def ui_warehouse(request: Request, db: Session = Depends(get_db)):
    profile_step(request, "query")
    items = db.scalars(
        select(ItemDB).where(_is_root_item()).order_by(ItemDB.name)
    ).all()
    mutated_id = request.query_params.get("mutated")
    mutated = None
    effects_log = []
    if mutated_id and mutated_id.isdigit():
        mutated = db.get(ItemDB, int(mutated_id))
        if mutated:
            effects_log = apply_ability_effects(mutated, mutated.abilities)
    profile_step(request, "render")
    return templates.TemplateResponse(
        request,
        "warehouse.html",
        {
            "items": items,
            "item_options": [
                {
                    "id": i.id,
                    "name": i.name,
                    "price": i.price,
                    "size": i.size,
                    "revision": i.revision or 1,
                }
                for i in items
            ],
            "mutated": mutated,
            "effects_log": effects_log,
            "error": request.query_params.get("error"),
        },
    )


def _clamp_price(baby: ItemDB) -> None:
    baby.price = round(max(0.01, baby.price), 2)


def _clamp_weight(baby: ItemDB) -> None:
    baby.weight = round(max(0.0, baby.weight), 2)


def _clamp_oil(baby: ItemDB) -> None:
    baby.oil = round(max(0.0, baby.oil), 2)


def _scale_price(baby: ItemDB, factor: float) -> None:
    baby.price = round(max(0.01, baby.price * factor), 2)


def _scale_weight(baby: ItemDB, factor: float) -> None:
    baby.weight = round(max(0.0, baby.weight * factor), 2)


def _scale_oil(baby: ItemDB, factor: float) -> None:
    baby.oil = round(max(0.0, baby.oil * factor), 2)


ABILITY_EFFECTS: dict[str, tuple[callable, str, str]] = {
    # weight shaping
    "compress": (
        lambda b: _scale_weight(b, 0.75),
        "compressed — weight −25%",
        "сжат — масса −25%",
    ),
    "flatten": (
        lambda b: _scale_weight(b, 0.8),
        "flattened — weight −20%",
        "расплющен — масса −20%",
    ),
    "extrude": (
        lambda b: _scale_weight(b, 0.9),
        "extruded — weight −10%",
        "протянут — масса −10%",
    ),
    "stretch": (
        lambda b: _scale_weight(b, 1.2),
        "stretched — weight +20%",
        "растянут — масса +20%",
    ),
    "expand": (
        lambda b: _scale_weight(b, 1.3),
        "expanded — weight +30%",
        "расширен — масса +30%",
    ),
    "scale": (
        lambda b: _scale_weight(b, 1.15),
        "scaled up — weight +15%",
        "увеличен — масса +15%",
    ),
    # cutting / removal
    "cut": (
        lambda b: _scale_weight(b, 0.85),
        "cut — weight −15%",
        "обрезан — масса −15%",
    ),
    "trim": (
        lambda b: _scale_weight(b, 0.9),
        "trimmed — weight −10%",
        "подрезан — масса −10%",
    ),
    "carve": (
        lambda b: _scale_weight(b, 0.8),
        "carved — weight −20%",
        "вырезан — масса −20%",
    ),
    "grind": (
        lambda b: _scale_weight(b, 0.9),
        "ground — weight −10%",
        "сточен — масса −10%",
    ),
    "sand": (
        lambda b: _scale_weight(b, 0.95),
        "sanded — weight −5%",
        "отшлифован — масса −5%",
    ),
    "drill": (
        lambda b: _scale_weight(b, 0.95),
        "drilled — weight −5%",
        "просверлён — масса −5%",
    ),
    "bore": (
        lambda b: _scale_weight(b, 0.95),
        "bored — weight −5%",
        "расточен — масса −5%",
    ),
    "punch": (
        lambda b: _scale_weight(b, 0.95),
        "punched — weight −5%",
        "пробит — масса −5%",
    ),
    "drain": (
        lambda b: _scale_weight(b, 0.9),
        "drained — weight −10%",
        "осушен — масса −10%",
    ),
    "empty": (
        lambda b: _scale_weight(b, 0.85),
        "emptied — weight −15%",
        "опорожнён — масса −15%",
    ),
    "vent": (
        lambda b: _scale_weight(b, 0.95),
        "vented — weight −5%",
        "стравил давление — масса −5%",
    ),
    "purge": (
        lambda b: _scale_weight(b, 0.9),
        "purged — weight −10%",
        "продувка — масса −10%",
    ),
    # finishing / value
    "polish": (
        lambda b: _scale_price(b, 1.2),
        "polished — price +20%",
        "отполирован — цена +20%",
    ),
    "buff": (
        lambda b: _scale_price(b, 1.1),
        "buffed — price +10%",
        "натёрт — цена +10%",
    ),
    "engrave": (
        lambda b: _scale_price(b, 1.25),
        "engraved — price +25%",
        "выгравирован — цена +25%",
    ),
    "etch": (
        lambda b: _scale_price(b, 1.15),
        "etched — price +15%",
        "вытравлен — цена +15%",
    ),
    "sharpen": (
        lambda b: _scale_price(b, 1.1),
        "sharpened — price +10%",
        "заточен — цена +10%",
    ),
    "clean": (
        lambda b: _scale_price(b, 1.05),
        "cleaned — price +5%",
        "очищен — цена +5%",
    ),
    "wash": (lambda b: _scale_price(b, 1.05), "washed — price +5%", "вымыт — цена +5%"),
    "decontaminate": (
        lambda b: _scale_price(b, 1.1),
        "decontaminated — price +10%",
        "дезактивирован — цена +10%",
    ),
    "sterilize": (
        lambda b: _scale_price(b, 1.1),
        "sterilized — price +10%",
        "стерилизован — цена +10%",
    ),
    # metallurgy
    "harden": (
        lambda b: _scale_price(b, 1.15),
        "hardened — price +15%",
        "закалён — цена +15%",
    ),
    "temper": (
        lambda b: _scale_price(b, 1.1),
        "tempered — price +10%",
        "отпущен — цена +10%",
    ),
    "anneal": (
        lambda b: _scale_price(b, 1.05),
        "annealed — price +5%",
        "отожжён — цена +5%",
    ),
    "forge": (
        lambda b: _scale_price(b, 1.1),
        "forged — price +10%",
        "выкован — цена +10%",
    ),
    "weld": (
        lambda b: _scale_price(b, 1.1),
        "welded — price +10%",
        "сварен — цена +10%",
    ),
    "rivet": (
        lambda b: _scale_price(b, 1.05),
        "riveted — price +5%",
        "склёпан — цена +5%",
    ),
    "magnetize": (
        lambda b: _scale_price(b, 1.1),
        "magnetized — price +10%",
        "намагничен — цена +10%",
    ),
    "demagnetize": (
        lambda b: _scale_weight(b, 0.95),
        "demagnetized — easier to move — weight −5%",
        "размагничен — проще перемещать — масса −5%",
    ),
    # fluids
    "oil": (
        lambda b: _scale_oil(b, 1.5),
        "oiled — oil +50%",
        "смазан маслом — масло +50%",
    ),
    "grease": (
        lambda b: _scale_oil(b, 1.5),
        "greased — oil +50%",
        "смазан — масло +50%",
    ),
    "lubricate": (
        lambda b: _scale_oil(b, 1.5),
        "lubricated — oil +50%",
        "смазан — масло +50%",
    ),
    "fill": (
        lambda b: _scale_oil(b, 1.3),
        "filled — oil +30%",
        "заполнен — масло +30%",
    ),
    "refill": (
        lambda b: _scale_oil(b, 1.3),
        "refilled — oil +30%",
        "дозаполнен — масло +30%",
    ),
    # protection
    "shield": (
        lambda b: (setattr(b, "is_proof", True), _scale_price(b, 1.1)),
        "shielded — proof",
        "экранирован — защита",
    ),
    "seal": (
        lambda b: (setattr(b, "water_resistant", True), _scale_price(b, 1.1)),
        "sealed — water resistant",
        "герметизирован — водонепроницаем",
    ),
    "insulate": (
        lambda b: (setattr(b, "is_anti_emc", True), _scale_price(b, 1.1)),
        "insulated — anti-EMC",
        "изолирован — защита от ЭМИ",
    ),
    # quantity
    "split": (
        lambda b: setattr(b, "quantity", b.quantity * 2),
        "split — quantity ×2",
        "раздвоен — количество ×2",
    ),
    "merge": (
        lambda b: setattr(b, "quantity", b.quantity + 1),
        "merged — quantity +1",
        "слит — количество +1",
    ),
    "stack": (
        lambda b: setattr(b, "quantity", b.quantity + 1),
        "stacked — quantity +1",
        "сложен в стопку — количество +1",
    ),
}


def apply_ability_effects(baby: ItemDB, abilities) -> list[dict]:
    """Fire every ability's real-world effect on the unit.

    Returns an ordered log of {name, en, ru} effects that were applied.
    Deterministic given the ability set, so it can be recomputed on render.
    """
    log: list[dict] = []
    for ab in abilities:
        effect = ABILITY_EFFECTS.get(ab.name)
        if effect is None:
            continue
        fn, en, ru = effect
        fn(baby)
        log.append({"name": ab.name, "en": en, "ru": ru})
    return log


def mutate_name(units) -> str:
    """Generate a hybrid name from random words of each unit, with an increased build number."""
    parts: list[str] = []
    build = 0
    for u in units:
        words = u.name.split()
        number = None
        if words and words[-1].isdigit():
            number = int(words[-1])
            words = words[:-1]
        if words:
            parts.append(random.choice(words))
        if number is not None:
            build += number
    if not parts:
        parts = ["Hybrid"]
    build += len(units)
    name = " ".join(parts).title() + f" {build}"
    return name[:50]


@app.post("/ui/warehouse/mutate")
async def ui_warehouse_mutate(
    request: Request,
    db: Session = Depends(get_db),
):
    form = getattr(request.state, "form_data", None) or await request.form()
    item_ids = form.getlist("item_ids")
    ids = list(dict.fromkeys(int(x) for x in item_ids if str(x).strip()))
    if len(ids) < 2 or len(ids) > 255:
        return redirect_with_error(
            request.url_for("ui_warehouse"),
            "Pick between two and 255 different units to mutate.",
        )
    units = [db.get(ItemDB, iid) for iid in ids]
    if any(u is None for u in units):
        return redirect_with_error(
            request.url_for("ui_warehouse"),
            "One of the selected units no longer exists.",
        )
    logger.info("UI POST /ui/warehouse/mutate ids=%s", ids)
    a, b = units[0], units[1]
    name = mutate_name(units)
    baby = ItemDB(
        name=name,
        price=round(sum(u.price for u in units), 2),
        quantity=sum(u.quantity for u in units),
        is_offer=any(u.is_offer for u in units),
        color=a.color or b.color or "",
        size=a.size or b.size or "",
        weight=round(sum(u.weight for u in units), 2),
        is_anti_emc=any(u.is_anti_emc for u in units),
        is_proof=any(u.is_proof for u in units),
        water_resistant=any(u.water_resistant for u in units),
        oil=round(sum(u.oil for u in units), 2),
        self_desentry=any(u.self_desentry for u in units),
        is_parasite=any(u.is_parasite for u in units),
        parasite_chance=sum(u.parasite_chance for u in units),
        revision=sum(getattr(u, "revision", 1) or 1 for u in units),
    )
    seen: set[int] = set()
    for u in units:
        seen.update(ab.id for ab in u.abilities)
    merged = [db.get(AbilityDB, aid) for aid in seen if db.get(AbilityDB, aid)]
    baby.abilities = merged
    apply_ability_effects(baby, merged)
    _clamp_price(baby)
    _clamp_weight(baby)
    _clamp_oil(baby)
    baby.quantity = max(1, baby.quantity)
    baby.parasite_chance = min(90, max(0, baby.parasite_chance))
    db.add(baby)
    db.commit()
    profile_step(request, "commit")
    return RedirectResponse(
        request.url_for("ui_warehouse").include_query_params(mutated=baby.id),
        status_code=303,
    )


@app.get("/ui/test-facility", response_class=HTMLResponse)
def ui_test_facility(request: Request):
    profile_step(request, "render")
    return templates.TemplateResponse(
        request,
        "test_facility.html",
        {"error": request.query_params.get("error")},
    )


@app.get("/ui/combat-duel", response_class=HTMLResponse)
def ui_combat_duel(request: Request):
    profile_step(request, "render")
    return templates.TemplateResponse(
        request,
        "combat_duel.html",
        {"error": request.query_params.get("error")},
    )


# --------------------------------------------------------------------------- #
# War factory automation (loop: build → join → props → test → combat).
# --------------------------------------------------------------------------- #

# war_factory is imported lazily to avoid a module-load circular import
# (war_factory imports ``main`` for the SQLAlchemy models at its top). The
# loop module only needs to be present once the app is fully loaded.


def _wf():
    import war_factory

    return war_factory


@app.get("/war/factory/state")
def war_factory_state(request: Request, db: Session = Depends(get_db)) -> dict:
    """Snapshot of the war-log: current generation, last event, totals."""
    snapshot = _wf().state(db)
    snapshot["auto"] = _wf().war_factory_daemon.status()
    profile_step(request, "query")
    return snapshot


@app.get("/war/factory/leaderboard")
def war_factory_leaderboard(
    request: Request,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[dict]:
    profile_step(request, "query")
    return _wf().leaderboard(db, limit=limit)


@app.post("/war/factory/tick")
def war_factory_tick(
    request: Request,
    build_count: int = Query(default=2, ge=0, le=50),
    join_pairs: int = Query(default=1, ge=0, le=20),
    props_fraction: float = Query(default=0.3, ge=0.0, le=1.0),
    props_strength: float = Query(default=0.4, ge=0.0, le=1.0),
    test_sample: int = Query(default=10, ge=1, le=200),
    seed: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Run a single generation of the war factory loop."""
    import random as _r

    if seed is not None:
        _r.seed(seed)
    from war_factory import run_tick as _wf_run_tick

    profile_step(request, "query")
    result = _wf_run_tick(
        db,
        build_count=build_count,
        join_pairs=join_pairs,
        props_fraction=props_fraction,
        props_strength=props_strength,
        test_sample=test_sample,
        seed=seed,
    )
    return result.to_dict()


@app.post("/war/factory/run")
def war_factory_run(
    request: Request,
    ticks: int = Query(default=5, ge=1, le=200),
    build_count: int = Query(default=2, ge=0, le=50),
    join_pairs: int = Query(default=1, ge=0, le=20),
    props_fraction: float = Query(default=0.3, ge=0.0, le=1.0),
    props_strength: float = Query(default=0.4, ge=0.0, le=1.0),
    test_sample: int = Query(default=10, ge=1, le=200),
    seed: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Run N consecutive generations of the war factory loop."""
    results = _wf().run_loop(
        ticks=ticks,
        build_count=build_count,
        join_pairs=join_pairs,
        props_fraction=props_fraction,
        props_strength=props_strength,
        test_sample=test_sample,
        seed=seed,
    )
    profile_step(request, "query")
    return {
        "ticks": [r.to_dict() for r in results],
        "totals": {
            "built": sum(r.built for r in results),
            "joined": sum(r.joined for r in results),
            "mutated_props": sum(r.mutated_props for r in results),
            "tested": sum(r.tested["sample"] for r in results),
            "broken": sum(r.tested["broken"] for r in results),
            "battles": sum(len(r.battles) for r in results),
        },
    }


@app.get("/war/factory/test", response_model=list[dict])
def war_factory_test(
    request: Request,
    sample: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Run the test facility on a sample of the population and complain
    about any part that isn't working in set."""
    profile_step(request, "query")
    return [r.to_dict() for r in _wf().test_population(db, sample=sample)]


@app.post("/war/factory/auto/start")
def war_factory_auto_start(
    request: Request,
    interval: float = Query(default=5.0, ge=0.1, le=3600),
    max_generations: int | None = Query(default=None, ge=1, le=1000000),
    max_population: int = Query(default=400, ge=1, le=1000000),
    build_count: int = Query(default=2, ge=0, le=50),
    join_pairs: int = Query(default=1, ge=0, le=20),
    props_fraction: float = Query(default=0.3, ge=0.0, le=1.0),
    props_strength: float = Query(default=0.4, ge=0.0, le=1.0),
    test_sample: int = Query(default=10, ge=1, le=200),
) -> dict:
    """Start the continuous war-factory loop in the background."""
    wf = _wf()
    started = wf.war_factory_daemon.start(
        interval=interval,
        max_generations=max_generations,
        max_population=max_population,
        build_count=build_count,
        join_pairs=join_pairs,
        props_fraction=props_fraction,
        props_strength=props_strength,
        test_sample=test_sample,
    )
    profile_step(request, "query")
    return {"started": started, "status": wf.war_factory_daemon.status()}


@app.post("/war/factory/auto/stop")
def war_factory_auto_stop(request: Request) -> dict:
    """Stop the continuous war-factory loop."""
    wf = _wf()
    stopped = wf.war_factory_daemon.stop()
    profile_step(request, "query")
    return {"stopped": stopped, "status": wf.war_factory_daemon.status()}


@app.get("/war/factory/auto/status")
def war_factory_auto_status(request: Request) -> dict:
    """Return the live status of the background war-factory loop."""
    profile_step(request, "query")
    return _wf().war_factory_daemon.status()


@app.get("/ui/war-factory", response_class=HTMLResponse)
def ui_war_factory(request: Request):
    profile_step(request, "render")
    return templates.TemplateResponse(
        request,
        "war_factory.html",
        {"error": request.query_params.get("error")},
    )


@app.get("/ui", response_class=HTMLResponse)
def ui_index(
    request: Request,
    filt: ItemFilter = Depends(items_filter),
    db: Session = Depends(get_db),
):
    if request.query_params.get("cath_randon"):
        logger.info(
            f"redirecting to /ui coz of cath_randon={request.query_params.get('cath_randon')}"
        )
        return RedirectResponse(url="/ui")
    items = db.scalars(build_items_query(filt)).all()
    profile_step(request, "query")

    headers = {"Accept-Encoding": "gzip"}

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        headers=headers,
        context={
            "items": items,
            "q": filt.q or "",
            "color": filt.color or "",
            "size": filt.size or "",
            "is_offer": filt.is_offer or "",
            "error": request.query_params.get("error"),
        },
    )


class AbilityOption(BaseModel):
    name: str
    description: str
    description_ru: str = ""


class FilterOptions(BaseModel):
    colors: list[str]
    sizes: list[str]
    is_offer: list[bool]
    is_anti_emc: list[bool]
    is_proof: list[bool]
    water_resistant: list[bool]
    self_desentry: list[bool]
    is_parasite: list[bool]
    revisions: list[int]
    abilities: list[AbilityOption]


def filter_options(db: Session, filt: ItemFilter) -> dict:
    def values(column):
        return db.scalars(
            filtered_items_select(filt)
            .where(column.is_not(None))
            .where(column != "")
            .with_only_columns(column)
            .distinct()
            .order_by(column)
        ).all()

    def bool_values(column):
        return [
            v
            for v in (True, False)
            if db.scalar(filtered_items_select(filt).where(column.is_(v)).limit(1))
            is not None
        ]

    return {
        "colors": values(ItemDB.color),
        "sizes": values(ItemDB.size),
        "is_offer": bool_values(ItemDB.is_offer),
        "is_anti_emc": bool_values(ItemDB.is_anti_emc),
        "is_proof": bool_values(ItemDB.is_proof),
        "water_resistant": bool_values(ItemDB.water_resistant),
        "self_desentry": bool_values(ItemDB.self_desentry),
        "is_parasite": bool_values(ItemDB.is_parasite),
        "revisions": db.scalars(
            filtered_items_select(filt)
            .with_only_columns(ItemDB.revision)
            .distinct()
            .order_by(ItemDB.revision)
        ).all(),
        "abilities": [
            {
                "name": a.name,
                "description": a.description,
                "description_ru": a.description_ru,
            }
            for a in db.scalars(select(AbilityDB).order_by(AbilityDB.name)).all()
        ],
    }


@app.get("/ui/filters/options", response_model=FilterOptions)
def ui_filter_options(
    request: Request,
    filt: ItemFilter = Depends(items_filter),
    db: Session = Depends(get_db),
) -> FilterOptions:
    logger.info("GET /ui/filters/options")
    opts = filter_options(db, filt)
    profile_step(request, "query")
    logger.info(
        "filter options -> colors=%s sizes=%s offer=%s",
        opts["colors"],
        opts["sizes"],
        opts["is_offer"],
    )
    return FilterOptions(**opts)


@app.get("/ui/items/new", response_class=HTMLResponse)
def ui_item_new(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "item_form.html",
        {
            "item": None,
            "action": request.url_for("ui_item_create"),
            "error": request.query_params.get("error"),
            "subitem_names": CATALOG_NAMES,
            "abilities": ability_options(
                db.scalars(select(AbilityDB).order_by(AbilityDB.name)).all()
            ),
        },
    )


@app.get("/ui/items/{item_id}", response_class=HTMLResponse)
def ui_item_detail(request: Request, item_id: int, db: Session = Depends(get_db)):
    item = get_item_or_404(item_id, db)
    profile_step(request, "query")
    return templates.TemplateResponse(
        request,
        "item_detail.html",
        {
            "item": item,
            "error": request.query_params.get("error"),
        },
    )


@app.get("/ui/items/{item_id}/subitems/{subitem_id}", response_class=HTMLResponse)
def ui_subitem_detail(
    request: Request, item_id: int, subitem_id: int, db: Session = Depends(get_db)
):
    item = get_item_or_404(item_id, db)
    subitem = get_subitem_or_404(item, subitem_id, db)
    profile_step(request, "query")
    return templates.TemplateResponse(
        request,
        "subitem_detail.html",
        {
            "item": item,
            "subitem": subitem,
            "abilities": ability_options(
                db.scalars(select(AbilityDB).order_by(AbilityDB.name)).all()
            ),
            "selected_ids": {a.id for a in subitem.abilities},
            "error": request.query_params.get("error"),
        },
    )


@app.post("/ui/items/{item_id}/subitems/{subitem_id}/abilities")
async def ui_subitem_abilities(
    request: Request,
    item_id: int,
    subitem_id: int,
    db: Session = Depends(get_db),
):
    item = get_item_or_404(item_id, db)
    subitem = get_subitem_or_404(item, subitem_id, db)
    form = getattr(request.state, "form_data", None) or await request.form()
    ability_ids = [
        int(x) for x in form.getlist("ability_ids") if str(x).lstrip("-").isdigit()
    ]
    logger.info(
        "UI POST /ui/items/%s/subitems/%s/abilities ids=%s",
        item_id,
        subitem_id,
        ability_ids,
    )
    subitem.abilities = [
        db.get(AbilityDB, aid) for aid in ability_ids if db.get(AbilityDB, aid)
    ]
    db.commit()
    profile_step(request, "commit")
    return RedirectResponse(
        request.url_for("ui_subitem_detail", item_id=item.id, subitem_id=subitem.id),
        status_code=303,
    )


@app.get("/ui/items/{item_id}/edit", response_class=HTMLResponse)
def ui_item_edit(request: Request, item_id: int, db: Session = Depends(get_db)):
    item = get_item_or_404(item_id, db)
    profile_step(request, "query")
    return templates.TemplateResponse(
        request,
        "item_form.html",
        {
            "item": item,
            "action": request.url_for("ui_item_update", item_id=item.id),
            "error": request.query_params.get("error"),
            "subitem_names": CATALOG_NAMES,
            "abilities": ability_options(
                db.scalars(select(AbilityDB).order_by(AbilityDB.name)).all()
            ),
        },
    )


@app.post("/ui/items")
async def ui_item_create(
    request: Request,
    item: ItemCreate = Depends(item_form_dep("ui_item_new")),
    db: Session = Depends(get_db),
):
    logger.info("UI POST /ui/items name=%s", item.name)
    form = getattr(request.state, "form_data", None) or await request.form()
    ability_ids = form.getlist("ability_ids")
    db_item = ItemDB(**item.model_dump(exclude={"subitems"}))
    db_item.abilities = [
        db.get(AbilityDB, aid) for aid in ability_ids if db.get(AbilityDB, aid)
    ]
    db.add(db_item)
    db.commit()
    profile_step(request, "commit")
    logger.info("UI created item")
    return RedirectResponse(request.url_for("ui_index"), status_code=303)


@app.post("/ui/items/{item_id}")
async def ui_item_update(
    request: Request,
    item_id: int,
    item: ItemCreate = Depends(item_form_dep("ui_item_edit")),
    db: Session = Depends(get_db),
):
    logger.info("UI POST /ui/items/%s update", item_id)
    db_item = get_item_or_404(item_id, db)
    for field, value in item.model_dump(exclude={"subitems"}).items():
        setattr(db_item, field, value)

    form = getattr(request.state, "form_data", None) or await request.form()

    def ids(prefix: str) -> list[int]:
        return [
            int(x)
            for x in form.getlist(prefix)
            if str(x).lstrip("-").isdigit() and db.get(AbilityDB, int(x))
        ]

    db_item.abilities = [db.get(AbilityDB, aid) for aid in ids("ability_ids")]

    sub_id = form.getlist("sub_id")
    sub_name = form.getlist("sub_name")
    sub_qty = form.getlist("sub_qty")
    sub_is_parasite = form.getlist("sub_is_parasite")
    sub_chance = form.getlist("sub_chance")
    sub_revision = form.getlist("sub_revision")

    rows = max(
        len(sub_id),
        len(sub_name),
        len(sub_qty),
        len(sub_is_parasite),
        len(sub_chance),
        len(sub_revision),
    )

    def g(lst: list[str], i: int) -> str:
        return lst[i] if i < len(lst) else ""

    existing = {s.id: s for s in db_item.subitems}
    keep: set[int] = set()
    for i in range(rows):
        name = g(sub_name, i).strip()
        sid = g(sub_id, i).strip()
        qty = int(g(sub_qty, i)) if g(sub_qty, i) else 1
        parasite = g(sub_is_parasite, i) == "1"
        chance = int(g(sub_chance, i)) if g(sub_chance, i) else 0
        revision = int(g(sub_revision, i)) if g(sub_revision, i) else 1
        if not name:
            continue
        if sid and int(sid) in existing:
            s = existing[int(sid)]
            keep.add(int(sid))
        else:
            s = ItemDB(parent_id=item_id)
            db.add(s)
        s.name = name
        s.quantity = qty
        s.is_parasite = parasite
        s.parasite_chance = chance
        s.revision = revision
        s.abilities = [
            db.get(AbilityDB, int(a))
            for a in form.getlist(f"sub_ability_{i}")
            if a.isdigit() and db.get(AbilityDB, int(a))
        ]

    for sid, s in existing.items():
        if sid not in keep:
            db.delete(s)

    db.commit()
    profile_step(request, "commit")
    return RedirectResponse(request.url_for("ui_index"), status_code=303)


@app.post("/ui/items/{item_id}/delete")
def ui_item_delete(request: Request, item_id: int, db: Session = Depends(get_db)):
    logger.info("UI POST /ui/items/%s/delete", item_id)
    item = get_item_or_404(item_id, db)
    db.delete(item)
    db.commit()
    profile_step(request, "commit")
    return RedirectResponse("/ui", status_code=303)


@app.post("/ui/items/{item_id}/subitems")
async def ui_subitem_create(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
):
    form = getattr(request.state, "form_data", None) or await request.form()
    name = form.get("name", "")
    quantity = form.get("quantity", "")
    is_parasite = _form_bool(form.get("is_parasite"))
    parasite_chance = form.get("parasite_chance", "0")
    logger.info(
        "UI POST /ui/items/%s/subitems name=%s qty=%s parasite=%s",
        item_id,
        name,
        quantity,
        is_parasite,
    )
    item = get_item_or_404(item_id, db)
    try:
        payload = SubItemCreate(
            name=name,
            quantity=int(quantity) if quantity else 1,
            is_parasite=is_parasite,
            parasite_chance=int(parasite_chance) if parasite_chance else 0,
        )
    except ValueError:
        return redirect_with_error(
            request.url_for("ui_item_detail", item_id=item.id), "Invalid input"
        )
    db.add(ItemDB(parent_id=item.id, **payload.model_dump()))
    db.commit()
    profile_step(request, "commit")
    return RedirectResponse(
        request.url_for("ui_item_detail", item_id=item.id), status_code=303
    )


@app.post("/ui/items/{item_id}/subitems/{subitem_id}/delete")
def ui_subitem_delete(
    request: Request,
    item_id: int,
    subitem_id: int,
    db: Session = Depends(get_db),
):
    logger.info("UI POST /ui/items/%s/subitems/%s/delete", item_id, subitem_id)
    item = get_item_or_404(item_id, db)
    subitem = get_subitem_or_404(item, subitem_id, db)
    db.delete(subitem)
    db.commit()
    profile_step(request, "commit")
    return RedirectResponse(
        request.url_for("ui_item_detail", item_id=item.id), status_code=303
    )


# ── AbilityParams ──────────────────────────────────────────────
class AbilityParamCreate(BaseModel):
    ability_id: int
    param_id: int
    modify_coefficient_per_10msec: float = 0.0
    operation: str = "add"
    base_value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    curve: str = "linear"
    stack_mode: str = "stack"
    priority: int = 0
    enabled: bool = True
    description: str = ""


class AbilityParamUpdate(BaseModel):
    modify_coefficient_per_10msec: float | None = None
    operation: str | None = None
    base_value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    curve: str | None = None
    stack_mode: str | None = None
    priority: int | None = None
    enabled: bool | None = None
    description: str | None = None


class AbilityParamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ability_id: int
    param_id: int
    modify_coefficient_per_10msec: float
    operation: str
    base_value: float | None
    min_value: float | None
    max_value: float | None
    curve: str
    stack_mode: str
    priority: int
    enabled: bool
    description: str
    ability_name: str | None = None
    param_name: str | None = None


def _ap_out(ap: AbilityParamDB) -> AbilityParamOut:
    return AbilityParamOut(
        id=ap.id,
        ability_id=ap.ability_id,
        param_id=ap.param_id,
        modify_coefficient_per_10msec=ap.modify_coefficient_per_10msec,
        operation=ap.operation,
        base_value=ap.base_value,
        min_value=ap.min_value,
        max_value=ap.max_value,
        curve=ap.curve,
        stack_mode=ap.stack_mode,
        priority=ap.priority,
        enabled=ap.enabled,
        description=ap.description,
        ability_name=ap.ability.name if ap.ability else None,
        param_name=ap.parameter.par_name if ap.parameter else None,
    )


@app.get("/api/ability-params", response_model=list[AbilityParamOut])
def list_ability_params(
    ability_id: int | None = None,
    param_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = select(AbilityParamDB).options(
        selectinload(AbilityParamDB.ability), selectinload(AbilityParamDB.parameter)
    )
    if ability_id:
        q = q.where(AbilityParamDB.ability_id == ability_id)
    if param_id:
        q = q.where(AbilityParamDB.param_id == param_id)
    return [_ap_out(x) for x in db.scalars(q.order_by(AbilityParamDB.id)).all()]


@app.post("/api/ability-params", response_model=AbilityParamOut, status_code=201)
def create_ability_param(payload: AbilityParamCreate, db: Session = Depends(get_db)):
    if not db.get(AbilityDB, payload.ability_id):
        raise HTTPException(404, "ability not found")
    if not db.get(ParameterDB, payload.param_id):
        raise HTTPException(404, "param not found")
    ap = AbilityParamDB(**payload.model_dump())
    db.add(ap)
    db.commit()
    db.refresh(ap)
    ap = db.scalars(
        select(AbilityParamDB)
        .options(
            selectinload(AbilityParamDB.ability), selectinload(AbilityParamDB.parameter)
        )
        .where(AbilityParamDB.id == ap.id)
    ).one()
    return _ap_out(ap)


@app.put("/api/ability-params/{ap_id}", response_model=AbilityParamOut)
def update_ability_param(
    ap_id: int, payload: AbilityParamUpdate, db: Session = Depends(get_db)
):
    ap = db.get(AbilityParamDB, ap_id)
    if not ap:
        raise HTTPException(404, "not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(ap, k, v)
    db.commit()
    db.refresh(ap)
    ap = db.scalars(
        select(AbilityParamDB)
        .options(
            selectinload(AbilityParamDB.ability), selectinload(AbilityParamDB.parameter)
        )
        .where(AbilityParamDB.id == ap.id)
    ).one()
    return _ap_out(ap)


@app.delete("/api/ability-params/{ap_id}", status_code=204)
def delete_ability_param(ap_id: int, db: Session = Depends(get_db)):
    ap = db.get(AbilityParamDB, ap_id)
    if not ap:
        raise HTTPException(404, "not found")
    db.delete(ap)
    db.commit()


@app.get("/api/abilities", response_model=list[dict])
def list_abilities_api(db: Session = Depends(get_db)):
    return [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "description_ru": a.description_ru,
        }
        for a in db.scalars(select(AbilityDB).order_by(AbilityDB.id)).all()
    ]


@app.get("/api/parameters", response_model=list[dict])
def list_parameters_api(db: Session = Depends(get_db)):
    return [
        {"id": p.id, "par_name": p.par_name, "par_category": p.par_category}
        for p in db.scalars(select(ParameterDB).order_by(ParameterDB.id)).all()
    ]


@app.put("/api/abilities/{ability_id}")
def update_ability(ability_id: int, payload: dict, db: Session = Depends(get_db)):
    a = db.get(AbilityDB, ability_id)
    if not a:
        raise HTTPException(404, "ability not found")
    for k in ("name", "description", "description_ru"):
        if k in payload:
            setattr(a, k, payload[k])
    db.commit()
    return {"id": a.id, "name": a.name}


@app.get("/ui/abilities", response_class=HTMLResponse)
def ui_abilities(
    request: Request,
    ability: int | None = Query(None, description="Pre-select this ability id"),
    db: Session = Depends(get_db),
):
    abilities = db.scalars(select(AbilityDB).order_by(AbilityDB.id)).all()
    params = db.scalars(select(ParameterDB).order_by(ParameterDB.par_name)).all()
    profile_step(request, "query")
    return templates.TemplateResponse(
        request,
        "abilities.html",
        {"abilities": abilities, "parameters": params, "preselect_ability": ability},
    )


# ── Events: programmatic entity events → triggered abilities ──
@app.get("/api/events", response_model=list[dict])
def list_events_api(db: Session = Depends(get_db)):
    events = db.scalars(
        select(EventDB)
        .options(
            selectinload(EventDB.abilities)
            .selectinload(AbilityDB.ability_params)
            .selectinload(AbilityParamDB.parameter)
        )
        .order_by(EventDB.id)
    ).all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "event_per_10msec": e.event_per_10msec,
            "abilities": [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "params": {
                        ap.parameter.par_name: {
                            "operation": ap.operation,
                            "base_value": ap.base_value,
                            "min_value": ap.min_value,
                            "max_value": ap.max_value,
                            "curve": ap.curve,
                            "stack_mode": ap.stack_mode,
                            "priority": ap.priority,
                            "enabled": ap.enabled,
                            "modify_coefficient_per_10msec": ap.modify_coefficient_per_10msec,
                            "description": ap.description,
                        }
                        for ap in a.ability_params
                        if ap.parameter
                    },
                }
                for a in e.abilities
            ],
        }
        for e in events
    ]


@app.post("/api/events", response_model=dict, status_code=201)
def create_event(payload: dict, db: Session = Depends(get_db)):
    try:
        name = (payload.get("name") or "").strip()
        if not name:
            return JSONResponse({"detail": "name is required"}, status_code=400)
        ev = EventDB(
            name=name,
            description=payload.get("description") or "",
            event_per_10msec=float(payload.get("event_per_10msec") or 0.0),
        )
        ability_ids = payload.get("ability_ids") or (
            []
            if "ability_id" not in payload
            else ([payload["ability_id"]] if payload["ability_id"] is not None else [])
        )
        _set_event_abilities(ev, ability_ids, db)
        db.add(ev)
        db.commit()
        return {"id": ev.id, "name": ev.name}
    except ValueError:
        return JSONResponse({"detail": "invalid event_per_10msec"}, status_code=400)


@app.put("/api/events/{event_id}")
def update_event(event_id: int, payload: dict, db: Session = Depends(get_db)):
    ev = db.get(EventDB, event_id)
    if not ev:
        raise HTTPException(404, "event not found")
    if "name" in payload:
        name = (payload.get("name") or "").strip()
        if not name:
            return JSONResponse({"detail": "name is required"}, status_code=400)
        ev.name = name
    if "description" in payload:
        ev.description = payload.get("description") or ""
    if "event_per_10msec" in payload:
        ev.event_per_10msec = float(payload["event_per_10msec"])
    if "ability_ids" in payload:
        _set_event_abilities(ev, payload["ability_ids"] or [], db)
    elif "ability_id" in payload:
        ability_id = payload["ability_id"]
        _set_event_abilities(ev, [ability_id] if ability_id is not None else [], db)
    db.commit()
    return {"id": ev.id, "name": ev.name}


@app.delete("/api/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(EventDB, event_id)
    if not ev:
        raise HTTPException(404, "event not found")
    db.delete(ev)
    db.commit()


def _set_event_abilities(ev: EventDB, ability_ids: list, db: Session) -> None:
    keep = []
    for aid in ability_ids:
        a = db.get(AbilityDB, aid)
        if a:
            keep.append(a)
    ev.abilities = keep


@app.get("/ui/events", response_class=HTMLResponse)
def ui_events(
    request: Request,
    event: int | None = Query(None, description="Pre-select this event id"),
    db: Session = Depends(get_db),
):
    events = db.scalars(
        select(EventDB).options(selectinload(EventDB.abilities)).order_by(EventDB.id)
    ).all()
    abilities = db.scalars(
        select(AbilityDB)
        .options(selectinload(AbilityDB.ability_params))
        .order_by(AbilityDB.name)
    ).all()
    profile_step(request, "query")
    return templates.TemplateResponse(
        request,
        "events.html",
        {
            "events": events,
            "abilities": ability_options(abilities),
            "preselect_event": event,
        },
    )


# ── Test Facility: unit inspector ─────────────────────────────
@app.get("/api/units", response_model=list[dict])
def api_list_units(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(ItemDB).where(_is_root_item()).order_by(ItemDB.name)
    ).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@app.get("/api/units/{item_id}")
def api_unit_report(item_id: int, db: Session = Depends(get_db)):
    item = get_item_or_404(item_id, db)

    abilities = (
        db.scalars(
            select(AbilityDB)
            .join(item_abilities, item_abilities.c.ability_id == AbilityDB.id)
            .where(item_abilities.c.item_id == item_id)
            .options(
                selectinload(AbilityDB.ability_params).selectinload(
                    AbilityParamDB.parameter
                )
            )
            .order_by(AbilityDB.id)
        )
        .unique()
        .all()
    )

    item_params = db.scalars(
        select(ItemParameterDB)
        .where(ItemParameterDB.item_id == item_id)
        .options(selectinload(ItemParameterDB.parameter))
        .order_by(ItemParameterDB.id)
    ).all()

    subitems = db.scalars(
        select(ItemDB).where(ItemDB.parent_id == item_id).order_by(ItemDB.id)
    ).all()

    rows = []

    # one row per ability -> param mapping
    for ab in abilities:
        for ap in ab.ability_params:
            p = ap.parameter
            rows.append(
                {
                    "kind": "ability",
                    "ability_id": ab.id,
                    "ability": ab.name,
                    "description": ab.description,
                    "description_ru": ab.description_ru,
                    "param": p.par_name if p else "",
                    "param_category": p.par_category if p else "",
                    "operation": ap.operation,
                    "curve": ap.curve,
                    "value": _fmt_value(ap.modify_coefficient_per_10msec),
                    "detail": "%s %s" % (ap.operation, ap.curve),
                }
            )
        # ability with no params yet -> single row showing ability only
        if not ab.ability_params:
            rows.append(
                {
                    "kind": "ability",
                    "ability_id": ab.id,
                    "ability": ab.name,
                    "description": ab.description,
                    "description_ru": ab.description_ru,
                    "param": "",
                    "param_category": "",
                    "operation": "",
                    "curve": "",
                    "value": "",
                    "detail": "",
                }
            )

    # item's own measured parameters
    for ip in item_params:
        p = ip.parameter
        v = (
            ip.value_text
            if ip.value is None and ip.value_text
            else (_fmt_value(ip.value) if ip.value is not None else "—")
        )
        rows.append(
            {
                "kind": "param",
                "ability_id": None,
                "ability": "",
                "param": p.par_name if p else "",
                "param_category": p.par_category if p else "",
                "operation": "",
                "curve": "",
                "value": v,
                "detail": ip.source,
            }
        )

    return {
        "item": {"id": item.id, "name": item.name},
        "rows": rows,
        "subitems": [
            {
                "id": s.id,
                "name": s.name,
                "quantity": s.quantity,
                "revision": s.revision,
                "hp": s.hp,
                "is_parasite": s.is_parasite,
            }
            for s in subitems
        ],
    }


def _fmt_value(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return "%g" % v
    return str(v)
