"""War factory automation loop.

Four stages are chained every tick:
    1. Unit builder      — generate fresh units from random parts.
    2. Unit joiner       — merge existing units into hybrids (mutator).
    3. Unit props mutator — perturb scalar properties on a population.
    4. Test facility     — verify every part of every unit is "working in set".

Each tick writes its results into a `war_log` table and into the public
`items` table. The loop is deterministic given a seed and can be driven
from a CLI, the API, or a background worker. The module imports the
FastAPI app's SQLAlchemy models so the results are visible immediately
in the existing UI.

Heavy work (mutation effects) lives here rather than in main.py to keep
the request handlers thin.
"""

from __future__ import annotations

import json
import logging
import random
import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from main import (
    ABILITY_EFFECTS,
    AbilityDB,
    AbilityParamDB,
    ItemDB,
    ItemParameterDB,
    ParameterDB,
    SessionLocal,
    mutate_name,
)
from parts import (
    BRANDS,
    COLORS,
    MODELS,
    PART_KINDS,
    SIZES,
    SUB_NAMES,
)

logger = logging.getLogger("war_factory")

# --------------------------------------------------------------------- #
# 1.  War-log persistence                                                #
# --------------------------------------------------------------------- #

WAR_LOG_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS war_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    generation    INTEGER NOT NULL,
    stage         TEXT    NOT NULL,
    detail        TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
)
"""


def _ensure_war_log(db: Session) -> None:
    from sqlalchemy import text

    db.execute(text(WAR_LOG_TABLE_DDL))
    db.commit()


def _now() -> datetime:
    return datetime.now(UTC)


_MAX_UNIT_HP = 100.0


def _log(db: Session, generation: int, stage: str, detail: dict[str, Any]) -> None:
    """Append a JSON line to war_log; never raises so it can't kill a tick."""
    try:
        from sqlalchemy import text

        db.execute(
            text(
                "INSERT INTO war_log (generation, stage, detail, created_at) "
                "VALUES (:g, :s, :d, :t)"
            ),
            {
                "g": generation,
                "s": stage,
                "d": json.dumps(detail, default=str),
                "t": _now().isoformat(),
            },
        )
        db.commit()
    except Exception as exc:  # pragma: no cover - last-resort guard
        logger.warning("war_log insert failed: %s", exc)
        db.rollback()


# --------------------------------------------------------------------- #
# 2.  Unit builder                                                        #
# --------------------------------------------------------------------- #


def _random_price() -> float:
    return round(random.uniform(0.5, 999.99), 2)


def _random_weight() -> float:
    return round(random.uniform(0, 15), 2)


def _random_oil() -> float:
    return round(random.uniform(0, 15), 2)


def _random_bool(p: float = 0.5) -> bool:
    return random.random() < p


_GREEK = [
    "Alpha",
    "Beta",
    "Gamma",
    "Delta",
    "Epsilon",
    "Zeta",
    "Eta",
    "Theta",
    "Iota",
    "Kappa",
    "Lambda",
    "Mu",
    "Nu",
    "Xi",
    "Omicron",
    "Pi",
    "Rho",
    "Sigma",
    "Tau",
    "Upsilon",
    "Phi",
    "Chi",
    "Psi",
    "Omega",
]
_WORDS = [
    "Storm",
    "Blade",
    "Fang",
    "Claw",
    "Shield",
    "Bolt",
    "Strike",
    "Viper",
    "Hawk",
    "Wolf",
    "Bear",
    "Fox",
    "Raven",
    "Cobra",
    "Scorpion",
    "Titan",
    "Falcon",
    "Phoenix",
    "Dragon",
    "Serpent",
    "Shadow",
    "Phantom",
    "Spectre",
    "Reaper",
    "Sentinel",
    "Guardian",
    "Warden",
    "Crusader",
    "Ronin",
    "Sage",
]


def _build_part_name() -> str:
    g = random.choice(_GREEK)
    w1 = random.choice(_WORDS)
    w2 = random.choice(_WORDS)
    return f"{g} {w1} {w2}"


def ensure_combat_readiness(db: Session, item: ItemDB) -> dict[str, Any]:
    """Guarantee a (possibly fresh/mutated) unit can fight.

    Ensures the unit is linked to *every* parameter (all parameters present)
    and owns at least one ability. Returns a report of what was added.
    """
    report: dict[str, Any] = {}
    all_params = db.scalars(select(ParameterDB)).all()
    existing_pids = {
        row.par_id
        for row in db.scalars(
            select(ItemParameterDB).where(ItemParameterDB.item_id == item.id)
        ).all()
    }
    added_params = 0
    for p in all_params:
        if p.id in existing_pids:
            continue
        lo = p.min_value if p.min_value is not None else 0.0
        hi = p.max_value if p.max_value is not None else 1000.0
        if hi < lo:
            lo, hi = hi, lo
        value = round(random.uniform(lo, hi), 2)
        db.add(
            ItemParameterDB(
                item_id=item.id,
                par_id=p.id,
                value=value,
                value_text=None,
                source="derived",
            )
        )
        added_params += 1
    if not item.abilities:
        pool = db.scalars(select(AbilityDB)).all()
        if pool:
            item.abilities = [random.choice(pool)]
    report["params_added"] = added_params
    report["abilities_added"] = 1 if item.abilities else 0
    return report


def build_units(db: Session, count: int) -> list[ItemDB]:
    """Create ``count`` random top-level units with 0-4 sub-parts each.

    Returns the list of newly persisted units.
    """
    abilities = db.scalars(select(AbilityDB)).all()
    created: list[ItemDB] = []
    now = _now()
    for _ in range(count):
        item = ItemDB(
            name=_build_part_name(),
            price=_random_price(),
            quantity=random.randint(1, 20),
            is_offer=_random_bool(0.3),
            color=random.choice(COLORS),
            size=random.choice(SIZES),
            weight=_random_weight(),
            hp=round(random.uniform(10, 100), 1),
            is_anti_emc=_random_bool(0.4),
            is_proof=_random_bool(0.4),
            water_resistant=_random_bool(0.4),
            oil=_random_oil(),
            self_desentry=_random_bool(0.3),
            is_parasite=_random_bool(0.3),
            parasite_chance=random.randint(0, 90) if _random_bool(0.3) else 0,
            revision=random.randint(1, 5),
            added_at=now,
            updated_at=now,
            subitems=[
                ItemDB(
                    name=random.choice(SUB_NAMES),
                    quantity=random.randint(1, 2),
                )
                for _ in range(random.randint(1, 2))
            ],
        )
        if abilities:
            # Assign 1-2 random abilities per unit
            ability_count = min(2, len(abilities))
            item.abilities = random.sample(abilities, random.randint(1, ability_count))
        db.add(item)
        db.flush()
        ensure_combat_readiness(db, item)
        created.append(item)
    db.commit()
    logger.info(
        "built %d unit(s): %s",
        len(created),
        ", ".join(c.name for c in created[:6]) or "none",
    )
    return created


# --------------------------------------------------------------------- #
# 3.  Unit joiner / mutator                                              #
# --------------------------------------------------------------------- #


def _clamp_01(value: float, lo: float = 0.0, hi: float = 1e9) -> float:
    return max(lo, min(hi, value))


def _clamp_pct(value: int) -> int:
    return max(0, min(90, int(value)))


def join_units(db: Session, parents: list[ItemDB]) -> ItemDB:
    """Merge ``parents`` into a single hybrid child, applying ability effects."""
    a, b = parents[0], parents[1]
    baby = ItemDB(
        name=mutate_name(parents),
        price=round(sum(p.price for p in parents), 2),
        quantity=sum(p.quantity for p in parents),
        is_offer=any(p.is_offer for p in parents),
        color=a.color or b.color or "",
        size=a.size or b.size or "",
        weight=round(sum(p.weight for p in parents), 2),
        hp=round(sum(p.hp for p in parents) / max(1, len(parents)), 1),
        is_anti_emc=any(p.is_anti_emc for p in parents),
        is_proof=any(p.is_proof for p in parents),
        water_resistant=any(p.water_resistant for p in parents),
        oil=round(sum(p.oil for p in parents), 2),
        self_desentry=any(p.self_desentry for p in parents),
        is_parasite=any(p.is_parasite for p in parents),
        parasite_chance=_clamp_pct(sum(p.parasite_chance for p in parents)),
        revision=max(1, sum(getattr(p, "revision", 1) or 1 for p in parents)),
        added_at=_now(),
        updated_at=_now(),
    )
    seen: set[int] = set()
    for p in parents:
        seen.update(ab.id for ab in p.abilities)
    merged = [
        db.get(AbilityDB, aid) for aid in seen if db.get(AbilityDB, aid) is not None
    ]
    # Cap abilities to 2 for balance
    if len(merged) > 2:
        merged = merged[:2]
    baby.abilities = merged
    baby.price = round(_clamp_01(baby.price, 0.01), 2)
    baby.weight = round(_clamp_01(baby.weight, 0.0), 2)
    baby.oil = round(_clamp_01(baby.oil, 0.0), 2)
    baby.quantity = max(1, int(baby.quantity))
    baby.parasite_chance = _clamp_pct(baby.parasite_chance)
    db.add(baby)
    db.flush()
    ensure_combat_readiness(db, baby)
    db.commit()
    db.refresh(baby)
    return baby


def join_random_pairs(db: Session, pair_count: int) -> list[ItemDB]:
    """Pick N random parent pairs and produce a child for each.

    Parents are *not* removed — the warehouse keeps the source units. This
    matches the existing UI flow where the warehouse produces one new
    hybrid without deleting the inputs.
    """
    parents_pool = db.scalars(
        select(ItemDB)
        .where(ItemDB.parent_id.is_(None))
        .options(selectinload(ItemDB.abilities))
    ).all()
    if len(parents_pool) < 2:
        return []
    children: list[ItemDB] = []
    for _ in range(pair_count):
        a, b = random.sample(parents_pool, 2)
        logger.info(
            "joining parents id=%s '%s' + id=%s '%s'", a.id, a.name, b.id, b.name
        )
        children.append(join_units(db, [a, b]))
    logger.info(
        "joined %d hybrid(s): %s", len(children), ", ".join(c.name for c in children)
    )
    return children


# --------------------------------------------------------------------- #
# 4.  Unit props mutator                                                 #
# --------------------------------------------------------------------- #

COLOR_LIST: list[str] = list(COLORS)
SIZE_LIST: list[str] = list(SIZES)
BOOLEAN_FIELDS: tuple[str, ...] = (
    "is_anti_emc",
    "is_proof",
    "water_resistant",
    "self_desentry",
    "is_parasite",
)
SCALAR_FIELDS: tuple[str, ...] = (
    "price",
    "quantity",
    "weight",
    "hp",
    "oil",
    "parasite_chance",
    "revision",
)


def mutate_unit_props(unit: ItemDB, strength: float = 0.4) -> dict[str, Any]:
    """Perturb every scalar + boolean property of ``unit``.

    ``strength`` ∈ [0, 1] is the chance any single field is touched and
    the magnitude of the change. Mutations are bounded so a unit can't
    become infinitely large or negative.
    """
    touched: dict[str, Any] = {}

    # Scalars
    if random.random() < strength:
        drift = random.uniform(-0.3, 0.3)
        new_price = max(0.01, round(unit.price * (1.0 + drift), 2))
        if new_price != unit.price:
            touched["price"] = {"old": unit.price, "new": new_price}
            unit.price = new_price
    if random.random() < strength:
        new_qty = max(1, unit.quantity + random.choice([-1, 0, 1, 2]))
        if new_qty != unit.quantity:
            touched["quantity"] = {"old": unit.quantity, "new": new_qty}
            unit.quantity = new_qty
    if random.random() < strength:
        drift = random.uniform(-0.2, 0.2)
        new_weight = max(0.0, round(unit.weight * (1.0 + drift), 2))
        if new_weight != unit.weight:
            touched["weight"] = {"old": unit.weight, "new": new_weight}
            unit.weight = new_weight
    if random.random() < strength:
        drift = random.uniform(-0.2, 0.2)
        new_hp = max(1.0, min(_MAX_UNIT_HP, round(unit.hp * (1.0 + drift), 1)))
        if new_hp != unit.hp:
            touched["hp"] = {"old": unit.hp, "new": new_hp}
            unit.hp = new_hp
    if random.random() < strength:
        drift = random.uniform(-0.25, 0.25)
        new_oil = max(0.0, round(unit.oil * (1.0 + drift), 2))
        if new_oil != unit.oil:
            touched["oil"] = {"old": unit.oil, "new": new_oil}
            unit.oil = new_oil
    if random.random() < strength:
        new_pc = max(0, min(90, unit.parasite_chance + random.choice([-10, 0, 10])))
        if new_pc != unit.parasite_chance:
            touched["parasite_chance"] = {
                "old": unit.parasite_chance,
                "new": new_pc,
            }
            unit.parasite_chance = new_pc
    if random.random() < strength:
        new_rev = max(1, unit.revision + random.choice([0, 1]))
        if new_rev != unit.revision:
            touched["revision"] = {"old": unit.revision, "new": new_rev}
            unit.revision = new_rev

    # Booleans
    for f in BOOLEAN_FIELDS:
        if random.random() < strength:
            new_val = not getattr(unit, f)
            if new_val != getattr(unit, f):
                touched[f] = {"old": getattr(unit, f), "new": new_val}
                setattr(unit, f, new_val)

    # Categorical
    if random.random() < strength and COLOR_LIST:
        new_color = random.choice(COLOR_LIST)
        if new_color != unit.color:
            touched["color"] = {"old": unit.color, "new": new_color}
            unit.color = new_color
    if random.random() < strength and SIZE_LIST:
        new_size = random.choice(SIZE_LIST)
        if new_size != unit.size:
            touched["size"] = {"old": unit.size, "new": new_size}
            unit.size = new_size

    unit.updated_at = _now()
    return touched


def mutate_population_props(
    db: Session, fraction: float = 0.3, strength: float = 0.4
) -> list[dict[str, Any]]:
    """Touch ~``fraction`` of the top-level population and report what changed."""
    units = db.scalars(select(ItemDB).where(ItemDB.parent_id.is_(None))).all()
    if not units:
        return []
    target_count = max(1, int(len(units) * fraction))
    targets = random.sample(units, target_count)
    reports: list[dict[str, Any]] = []
    for u in targets:
        changes = mutate_unit_props(u, strength=strength)
        if changes:
            reports.append({"unit_id": u.id, "name": u.name, "changes": changes})
    if reports:
        db.commit()
    changed = sum(1 for r in reports if r["changes"])
    logger.info(
        "props mutator: touched %d/%d unit(s), %d with changes",
        len(reports),
        target_count,
        changed,
    )
    return reports


# --------------------------------------------------------------------- #
# 5.  Test facility — "complain all used parts as working in set"        #
# --------------------------------------------------------------------- #


@dataclass
class TestReport:
    unit_id: int
    name: str
    ok: bool
    issues: list[str] = field(default_factory=list)
    parts_total: int = 0
    parts_healthy: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "name": self.name,
            "ok": self.ok,
            "issues": list(self.issues),
            "parts_total": self.parts_total,
            "parts_healthy": self.parts_healthy,
        }


def _ability_has_effect(name: str) -> bool:
    """True if the ability is wired up to a real ABILITY_EFFECTS entry."""
    return name in ABILITY_EFFECTS


def test_unit(unit: ItemDB) -> TestReport:
    """Inspect a unit end-to-end and complain about any broken parts."""
    issues: list[str] = []
    parts_total = 0
    parts_healthy = 0

    if unit.price <= 0:
        issues.append("price must be > 0")
    if unit.quantity <= 0:
        issues.append("quantity must be > 0")
    if unit.hp <= 0:
        issues.append("hp must be > 0")
    if unit.parasite_chance < 0 or unit.parasite_chance > 90:
        issues.append("parasite_chance out of [0, 90]")

    for ab in unit.abilities:
        if not _ability_has_effect(ab.name):
            issues.append(f"ability {ab.name!r} has no wired effect")

    for sub in unit.subitems:
        parts_total += 1
        sub_ok = True
        if not sub.name or not sub.name.strip():
            issues.append(f"subitem id={sub.id} has empty name")
            sub_ok = False
        if sub.quantity <= 0:
            issues.append(f"subitem {sub.name!r} has non-positive quantity")
            sub_ok = False
        if sub.hp <= 0:
            issues.append(f"subitem {sub.name!r} has non-positive hp")
            sub_ok = False
        if sub.parasite_chance < 0 or sub.parasite_chance > 90:
            issues.append(f"subitem {sub.name!r} parasite_chance out of [0, 90]")
            sub_ok = False
        for ab in sub.abilities:
            if not _ability_has_effect(ab.name):
                issues.append(f"subitem {sub.name!r} ability {ab.name!r} has no effect")
                sub_ok = False
        if sub_ok:
            parts_healthy += 1

    return TestReport(
        unit_id=unit.id,
        name=unit.name,
        ok=not issues,
        issues=issues,
        parts_total=parts_total,
        parts_healthy=parts_healthy,
    )


def test_population(db: Session, sample: int | None = None) -> list[TestReport]:
    """Run the test facility on a (optionally sample-limited) population."""
    stmt = select(ItemDB).where(ItemDB.parent_id.is_(None))
    if sample is not None:
        stmt = stmt.limit(max(1, sample))
    units = db.scalars(stmt).all()
    reports = [test_unit(u) for u in units]
    ok_count = sum(1 for r in reports if r.ok)
    broken = [r for r in reports if not r.ok]
    logger.info(
        "test facility: %d tested, %d ok, %d broken",
        len(reports),
        ok_count,
        len(broken),
    )
    for r in broken[:5]:
        logger.warning(
            "broken unit %s (id=%s): %s",
            r.name,
            r.unit_id,
            "; ".join(r.issues[:8]),
        )
    return reports


# --------------------------------------------------------------------- #
@dataclass
class TickResult:
    generation: int
    built: int
    joined: int
    mutated_props: int
    tested: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "built": self.built,
            "joined": self.joined,
            "mutated_props": self.mutated_props,
            "tested": self.tested,
        }


def _current_generation(db: Session) -> int:
    from sqlalchemy import text

    row = db.execute(text("SELECT COALESCE(MAX(generation), 0) FROM war_log")).first()
    return int(row[0]) if row and row[0] is not None else 0


def run_tick(
    db: Session,
    *,
    build_count: int = 2,
    join_pairs: int = 1,
    props_fraction: float = 0.3,
    props_strength: float = 0.4,
    test_sample: int = 10,
    seed: int | None = None,
) -> TickResult:
    if seed is not None:
        random.seed(seed)
    _ensure_war_log(db)
    gen = -1
    reports = []
    joined = []
    built = []
    # 4) Test facility
    test_reports = test_population(db, sample=test_sample)
    ok_count = sum(1 for r in test_reports if r.ok)
    _log(
        db,
        gen,
        "test",
        {
            "sample": len(test_reports),
            "ok": ok_count,
            "broken": len(test_reports) - ok_count,
            "issues": [r.to_dict() for r in test_reports if not r.ok][:5],
        },
    )

    logger.info(
        "tick %d complete: built=%d joined=%d mutated=%d tested=%d/%d broken",
        gen,
        len(built),
        len(joined),
        len(reports),
        ok_count,
        len(test_reports),
    )
    return TickResult(
        generation=gen,
        built=len(built),
        joined=len(joined),
        mutated_props=len(reports),
        tested={
            "sample": len(test_reports),
            "ok": ok_count,
            "broken": len(test_reports) - ok_count,
        },
    )


def run_loop(
    ticks: int = 5,
    *,
    build_count: int = 2,
    join_pairs: int = 1,
    props_fraction: float = 0.3,
    props_strength: float = 0.4,
    test_sample: int = 10,
    seed: int | None = None,
) -> list[TickResult]:
    results: list[TickResult] = []
    with SessionLocal() as db:
        for _ in range(ticks):
            results.append(
                run_tick(
                    db,
                    build_count=build_count,
                    join_pairs=join_pairs,
                    props_fraction=props_fraction,
                    props_strength=props_strength,
                    test_sample=test_sample,
                    seed=seed,
                )
            )
            if seed is not None:
                # Advance the seed deterministically per-tick.
                seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    return results


# --------------------------------------------------------------------- #
# 8.  Leaderboard / state                                                #
# --------------------------------------------------------------------- #


def state(db: Session) -> dict[str, Any]:
    _ensure_war_log(db)
    from sqlalchemy import text

    gen = _current_generation(db)
    last_row = db.execute(
        text("SELECT stage, detail, created_at FROM war_log ORDER BY id DESC LIMIT 1")
    ).first()
    last: dict[str, Any] | None
    if last_row is None:
        last = None
    else:
        try:
            last = {
                "stage": last_row[0],
                "detail": json.loads(last_row[1]),
                "created_at": last_row[2],
            }
        except Exception:
            last = {
                "stage": last_row[0],
                "detail": last_row[1],
                "created_at": last_row[2],
            }
    total = db.scalar(text("SELECT COUNT(*) FROM war_log"))
    by_stage_rows = db.execute(
        text("SELECT stage, COUNT(*) FROM war_log GROUP BY stage")
    ).all()
    return {
        "generation": gen,
        "total_log_rows": int(total or 0),
        "by_stage": {row[0]: int(row[1]) for row in by_stage_rows},
        "last": last,
    }


# --------------------------------------------------------------------- #
# 8b.  Background daemon — automate the loop                             #
# --------------------------------------------------------------------- #


class WarFactoryDaemon:
    """Run the war-factory loop on a background thread at a fixed interval.

    This is the "automate the loop" piece: a single worker that keeps
    calling :func:`run_tick` forever (or until ``max_generations``) while a
    FastAPI app is alive, so the warehouse evolves without manual poking.

    Safety / robustness:
      * Bounded growth — building and joining pause once the top-level
        population reaches ``max_population``, so the warehouse can't grow
        without limit.
      * Failure-isolated — a tick that raises is logged and retried on the
        next interval; it never kills the worker thread.
      * Stoppable — :meth:`start` / :meth:`stop` / :meth:`status` give full
        control from the API or the UI.
    """

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.running = False
        self.interval: float = 5.0
        self.max_generations: int | None = None
        self.max_population: int = 400
        self.params: dict[str, Any] = {
            "build_count": 2,
            "join_pairs": 1,
            "props_fraction": 0.3,
            "props_strength": 0.4,
            "test_sample": 10,
        }
        self.tick_count: int = 0
        self.generation: int = 0
        self.errors: int = 0
        self.last_result: dict[str, Any] | None = None
        self.last_error: str | None = None
        self.started_at: str | None = None

    # -- control ------------------------------------------------------- #
    def start(
        self,
        *,
        interval: float | None = None,
        max_generations: int | None = None,
        max_population: int | None = None,
        build_count: int | None = None,
        join_pairs: int | None = None,
        props_fraction: float | None = None,
        props_strength: float | None = None,
        test_sample: int | None = None,
    ) -> bool:
        """Start the worker thread. Returns False if it is already running."""
        if self.running:
            return False
        if interval is not None:
            self.interval = max(0.1, float(interval))
        if max_generations is not None:
            self.max_generations = max(1, int(max_generations))
        if max_population is not None:
            self.max_population = max(1, int(max_population))
        if build_count is not None:
            self.params["build_count"] = max(0, int(build_count))
        if join_pairs is not None:
            self.params["join_pairs"] = max(0, int(join_pairs))
        if props_fraction is not None:
            self.params["props_fraction"] = max(0.0, min(1.0, float(props_fraction)))
        if props_strength is not None:
            self.params["props_strength"] = max(0.0, min(1.0, float(props_strength)))
        if test_sample is not None:
            self.params["test_sample"] = max(1, int(test_sample))
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="war-factory", daemon=True
        )
        self._thread.start()
        with self._lock:
            self.running = True
            self.started_at = _now().isoformat()
        logger.info("war-factory daemon started (interval=%.1fs)", self.interval)
        return True

    def stop(self, timeout: float | None = None) -> bool:
        """Stop the worker thread. Returns False if it was not running."""
        if not self.running:
            return False
        self._stop.set()
        if self._thread is not None:
            self._thread.join(
                timeout=timeout if timeout is not None else self.interval + 10
            )
        with self._lock:
            self.running = False
        logger.info(
            "war-factory daemon stop requested (ran %s tick(s))", self.tick_count
        )
        return True

    def is_running(self) -> bool:
        with self._lock:
            return self.running

    # -- internals ----------------------------------------------------- #
    def _top_population(self, db: Session) -> int:
        return int(
            db.scalar(
                select(func.count())
                .select_from(ItemDB)
                .where(ItemDB.parent_id.is_(None))
            )
            or 0
        )

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                with SessionLocal() as db:
                    top = self._top_population(db)
                    capped = top >= self.max_population
                    build = 0 if capped else self.params["build_count"]
                    join = 0 if capped else self.params["join_pairs"]
                    result = run_tick(
                        db,
                        build_count=build,
                        join_pairs=join,
                        props_fraction=self.params["props_fraction"],
                        props_strength=self.params["props_strength"],
                        test_sample=self.params["test_sample"],
                    )
                with self._lock:
                    self.tick_count += 1
                    self.generation = result.generation
                    self.last_result = result.to_dict()
                    self.last_error = None
                    if (
                        self.max_generations is not None
                        and self.tick_count >= self.max_generations
                    ):
                        self._stop.set()
                logger.info(
                    "daemon tick #%d: gen=%d built=%d joined=%d broken=%d",
                    self.tick_count,
                    result.generation,
                    result.built,
                    result.joined,
                    result.tested["broken"],
                )
            except Exception as exc:  # last-resort guard: never kill worker
                logger.exception("war-factory daemon tick failed")
                with self._lock:
                    self.errors += 1
                    self.last_error = f"{type(exc).__name__}: {exc}"
            self._stop.wait(self.interval)
        with self._lock:
            self.running = False
        logger.info("war-factory daemon stopped after %s tick(s)", self.tick_count)

    # -- introspection ------------------------------------------------- #
    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "running": self.running,
                "interval": self.interval,
                "max_generations": self.max_generations,
                "max_population": self.max_population,
                "params": dict(self.params),
                "tick_count": self.tick_count,
                "generation": self.generation,
                "errors": self.errors,
                "started_at": self.started_at,
                "last_error": self.last_error,
                "last_result": self.last_result,
            }


# Module-level singleton driven by the API / lifespan / CLI.
war_factory_daemon = WarFactoryDaemon()


# --------------------------------------------------------------------- #
# 9.  Self-test                                                          #
# --------------------------------------------------------------------- #


def _self_test() -> None:
    """Run a tiny deterministic loop. Prints a single line summary."""
    out = run_loop(ticks=2, seed=42)
    print(
        "self-test: generations="
        + str(len(out))
        + " built="
        + str(sum(r.built for r in out))
        + " joined="
        + str(sum(r.joined for r in out))
    )


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="War factory automation loop")
    parser.add_argument(
        "--mode",
        choices=["selftest", "ticks", "auto"],
        default="selftest",
        help="selftest: 2 deterministic ticks; ticks: N ticks; auto: "
        "continuous background loop until Ctrl-C",
    )
    parser.add_argument("--ticks", type=int, default=2)
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max-population", type=int, default=400)
    args = parser.parse_args()

    if args.mode == "selftest":
        _self_test()
    elif args.mode == "ticks":
        out = run_loop(ticks=args.ticks, seed=args.seed)
        print(
            "ticks="
            + str(len(out))
            + " built="
            + str(sum(r.built for r in out))
            + " joined="
            + str(sum(r.joined for r in out))
        )
    else:  # auto
        war_factory_daemon.start(
            interval=args.interval, max_population=args.max_population
        )
        print(
            "war-factory auto loop running (interval=%.1fs, max_population=%d). "
            "Ctrl-C to stop." % (args.interval, args.max_population)
        )
        try:
            while war_factory_daemon.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            war_factory_daemon.stop()
        print("war-factory auto loop stopped.")
