"""War factory automation loop.

Five stages are chained every tick:
    1. Unit builder      — generate fresh units from random parts.
    2. Unit joiner       — merge existing units into hybrids (mutator).
    3. Unit props mutator — perturb scalar properties on a population.
    4. Test facility     — verify every part of every unit is "working in set".
    5. Combat arena      — 1x1, 1x2, 2x2 battles with random / genetic selection.

Each tick writes its results into a `war_log` table and into the public
`items` table (combat winners gain stats). The loop is deterministic
given a seed and can be driven from a CLI, the API, or a background
worker. The module imports the FastAPI app's SQLAlchemy models so the
results are visible immediately in the existing UI.

Heavy work (combat resolution, mutation effects) lives here rather than
in main.py to keep the request handlers thin.
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
    apply_ability_effects,
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


def _build_part_name() -> str:
    kind = random.choice(PART_KINDS)
    brand = random.choice(BRANDS)
    model = random.choice(MODELS)
    suffix = random.randint(1, 99)
    return f"{brand} {kind} {model} {suffix}"


def ensure_combat_readiness(db: Session, item: ItemDB) -> dict[str, Any]:
    """Guarantee a (possibly fresh/mutated) unit can fight.

    Ensures the unit is linked to *every* parameter (all parameters present)
    and owns at least one ability. Returns a report of what was added.
    """
    report: dict[str, Any] = {}
    param_ids = {
        p.id for p in item.item_parameters
    }
    all_params = db.scalars(select(ParameterDB)).all()
    added_params = 0
    for p in all_params:
        if p.id in param_ids:
            continue
        db.add(
            ItemParameterDB(
                item_id=item.id,
                par_id=p.id,
                value=None,
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
            hp=round(random.uniform(10, 300), 1),
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
            item.abilities = random.sample(abilities, 1)
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
    baby.abilities = merged
    apply_ability_effects(baby, merged)
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
# 6.  Combat arena — 1x1 / 1x2 / 2x2                                     #
# ---------------------------------------------------------------------#

# Map raw materials-science parameter names onto the four combat stats so a
# unit's ability params have a real, explainable effect in melee. We choose
# the stat by the strongest keyword hit in the parameter name.
_COMBAT_STAT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "attack": (
        "attack",
        "strike",
        "offense",
        "offensive",
        "damage",
        "impact",
        "penetrat",
        "bite",
        "cutting",
        "punch",
        "blast",
        "warhead",
    ),
    "defense": (
        "defense",
        "defence",
        "armor",
        "armour",
        "shield",
        "protect",
        "toughness",
        "hardness",
        "resilien",
        "resist",
        "proof",
        "temper",
    ),
    "speed": (
        "speed",
        "velocity",
        "agility",
        "reaction",
        "initiative",
        "mobility",
        "conduct",
        "flow",
        "rate",
        "motion",
    ),
    "hp": (
        "hp",
        "health",
        "hull",
        "frame",
        "integrity",
        "vitality",
        "stamina",
        "capacity",
        "volume",
        "mass",
    ),
}


def _classify_param(name: str) -> str | None:
    """Return the combat stat driven by a parameter name, or None."""
    low = (name or "").lower()
    best = None
    best_len = 0
    for stat, kws in _COMBAT_STAT_KEYWORDS.items():
        for kw in kws:
            if kw in low and len(kw) > best_len:
                best = stat
                best_len = len(kw)
    return best


# Map ability-linked event names onto a per-round combat effect so the event
# program also matters in melee. Effect scale is derived from the event's
# per-10ms rate.
_EVENT_KIND_HURT = (
    "damage",
    "hit",
    "collision",
    "contact",
    "touch",
    "strike",
    "burn",
    "blast",
    "detonat",
    "shock",
    "impact",
    "deplet",
)
_EVENT_KIND_HEAL = ("heal", "repair", "regen", "restore", "revive", "respawn")


def _event_kind(name: str) -> str:
    low = (name or "").lower()
    if any(k in low for k in _EVENT_KIND_HEAL):
        return "heal"
    if any(k in low for k in _EVENT_KIND_HURT):
        return "hurt"
    return "neutral"


@dataclass
class Combatant:
    """A snapshot of the stats used by the arena. Decoupled from ItemDB so
    the same engine can fight arbitrary stat-blocks (e.g. for testing)."""

    unit_id: int
    name: str
    attack: float
    defense: float
    speed: float
    hp: float
    weight: float
    is_parasite: bool
    parasite_chance: int
    is_anti_emc: bool = False
    abilities: tuple[str, ...] = ()
    # Parametric bonuses keyed by combat stat, aggregated from the unit's
    # ability → ability_to_params links (operation + coeff per 10ms).
    param_bonus: dict[str, float] = field(default_factory=dict)
    # Ability-linked events (EventDB) with their per-10ms trigger rate.
    events: list[dict] = field(default_factory=list)
    # The unit's own material parameter values (param_id -> value).
    params: dict[int, float] = field(default_factory=dict)
    # Human-readable parameter names (param_id -> name) for the roster dump.
    param_names: dict[int, str] = field(default_factory=dict)
    # Per-ability param targets + linked events used by param-vs-param melee.
    abilities_data: list[dict] = field(default_factory=list)
    # Guards the battle log so a unit is only ever noted as eliminated once.
    eliminated_logged: bool = False

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def destroy_abilities(self, fraction: float = 0.5) -> int:
        """Destroy a fraction of this combatant's abilities. Returns number destroyed."""
        if not self.abilities_data:
            return 0
        to_destroy = max(1, int(len(self.abilities_data) * fraction))
        destroyed = self.abilities_data[:to_destroy]
        self.abilities_data = self.abilities_data[to_destroy:]
        return len(destroyed)

    def is_armed(self) -> bool:
        """A combatant can fight only if it has at least one ability that does
        harm, i.e. an ability with at least one real parameter target. No
        ability, or abilities that target nothing, means the unit is disarmed."""
        return any(ab.get("params") for ab in self.abilities_data)

    def can_damage(self) -> bool:
        """True if this combatant is physically able to deal damage at all:
        either it is armed (has a harmful ability) or it can land a parasite
        strike (is a parasite whose ECM is online)."""
        return self.is_armed() or (
            self.is_parasite and self.parasite_chance > 0 and self.is_anti_emc
        )

    def can_target(self, partner: "Combatant") -> bool:
        """True if this combatant has at least one ability that shares a real
        parameter with ``partner`` (i.e. it can actually target it)."""
        if not self.abilities_data or not partner.params:
            return False
        partner_pids = set(partner.params)
        for ab in self.abilities_data:
            for link in ab.get("params", []):
                if link.get("param_id") in partner_pids:
                    return True
        return False

    @classmethod
    def from_item(cls, item: ItemDB) -> Combatant:
        abilities = tuple(a.name for a in item.abilities)
        # Stat derivation is deterministic and explainable.
        # Higher price -> better materials, more oil -> better upkeep,
        # proof / anti-emc / water -> defense, self_desentry -> attack at a
        # cost to HP, parasite / weight -> swing variables.
        attack = 1.0
        if item.is_proof:
            attack += 1.5
        if item.is_anti_emc:
            attack += 0.5
        attack += min(item.price, 200.0) / 50.0
        attack += item.oil * 0.4
        if item.self_desentry:
            attack += 3.0

        defense = 0.0
        defense += item.weight * 0.4
        if item.is_proof:
            defense += 4.0
        if item.water_resistant:
            defense += 1.5
        if item.is_anti_emc:
            defense += 2.0
        # Anti-EM/Proof unit on a parasitised target is double-effective.
        if item.is_anti_emc and item.is_parasite:
            defense -= 1.0

        speed = 5.0
        speed += item.quantity * 0.3
        speed -= item.weight * 0.15
        if item.water_resistant:
            speed += 0.5
        if item.self_desentry:
            speed += 1.0

        # Base HP comes from the item's own ``hp`` prop (default 100), with a
        # small bonus for proof and a small penalty for self-destroying gear.
        hp = max(1.0, min(_MAX_UNIT_HP, item.hp or 0.0))
        if item.is_proof:
            hp += 5.0
        if item.self_desentry:
            hp -= 4.0
        hp = max(1.0, min(_MAX_UNIT_HP, hp))

        # ---- parametric abilities -----------------------------------------
        # The unit's own material parameter values (param_id -> value) so the
        # melee can compare attacker ability targets against defender params.
        params: dict[int, float] = {}
        for row in item.item_parameters:
            if row.par_id is not None and row.value is not None:
                params[row.par_id] = max(
                    -_PARAM_VALUE_LIMIT, min(_PARAM_VALUE_LIMIT, float(row.value))
                )
        param_names: dict[int, str] = {}
        for row in item.item_parameters:
            if row.par_id is not None and row.parameter is not None:
                param_names[row.par_id] = row.parameter.par_name

        # Each ability exposes the parameter(s) it targets (operator + coeff)
        # and the event(s) it fires, so per-round melee can strike a shared
        # parameter on the defender.
        abilities_data: list[dict] = []
        for ability in item.abilities:
            links = []
            for ap in ability.ability_params:
                if not ap.enabled:
                    continue
                if ap.parameter is None:
                    continue
                links.append(
                    {
                        "param_id": ap.param_id,
                        "param_name": ap.parameter.par_name,
                        "operation": (ap.operation or "add").lower(),
                        "coefficient": ap.modify_coefficient_per_10msec or 0.0,
                        "base_value": ap.base_value,
                        "min_value": ap.min_value,
                        "max_value": ap.max_value,
                        "curve": (ap.curve or "linear").lower(),
                    }
                )
            evs = [
                {
                    "name": ev.name,
                    "rate": getattr(ev, "event_per_10msec", 0.0) or 0.0,
                }
                for ev in ability.events
            ]
            abilities_data.append(
                {"name": ability.name, "params": links, "events": evs}
            )

        # Bounded combat-stat bonuses aggregated from the same ability→param
        # links keep the base attack/defense/speed flow meaningful without
        # running off the scale.
        bonus: dict[str, float] = {
            "attack": 0.0,
            "defense": 0.0,
            "speed": 0.0,
            "hp": 0.0,
        }
        events: list[dict] = []
        for ability in item.abilities:
            for ap in ability.ability_params:
                if not ap.enabled:
                    continue
                if ap.parameter is None:
                    continue
                stat = _classify_param(ap.parameter.par_name)
                if stat is None:
                    continue
                coeff = ap.modify_coefficient_per_10msec or 0.0
                op = (ap.operation or "add").lower()
                if op == "multiply":
                    bonus[stat] += max(-1.5, min(1.5, coeff))
                elif op == "set":
                    bonus[stat] += max(-3.0, min(3.0, coeff * 0.5))
                else:  # add
                    bonus[stat] += max(-1.0, min(1.0, coeff * 0.25))
            for ev in ability.events:
                events.append(
                    {
                        "name": ev.name,
                        "rate": getattr(ev, "event_per_10msec", 0.0) or 0.0,
                    }
                )
        for stat in bonus:
            bonus[stat] = max(-24.0, min(24.0, bonus[stat]))
        attack += bonus["attack"]
        defense += bonus["defense"]
        speed += bonus["speed"]
        hp += bonus["hp"]
        hp = max(1.0, hp)

        return cls(
            unit_id=item.id,
            name=item.name,
            attack=round(attack, 3),
            defense=round(defense, 3),
            speed=round(speed, 3),
            hp=round(hp, 3),
            weight=item.weight,
            is_parasite=item.is_parasite,
            parasite_chance=item.parasite_chance,
            is_anti_emc=item.is_anti_emc,
            abilities=abilities,
            param_bonus=bonus,
            events=events,
            params=params,
            param_names=param_names,
            abilities_data=abilities_data,
        )


@dataclass
class ArenaResult:
    map: str
    winner_id: int | None
    winner_name: str | None
    loser_ids: list[int]
    rounds: int
    log: list[str]
    survivors: list[int]
    battle_rejected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "map": self.map,
            "winner_id": self.winner_id,
            "winner_name": self.winner_name,
            "loser_ids": list(self.loser_ids),
            "rounds": self.rounds,
            "log": list(self.log),
            "survivors": list(self.survivors),
            "battle_rejected": self.battle_rejected,
        }


def _pick_initiative(team_a: list[Combatant], team_b: list[Combatant]) -> int:
    """Return 0 if team A starts, 1 if team B does. Determined by speed."""
    a = sum(c.speed for c in team_a) / max(1, len(team_a))
    b = sum(c.speed for c in team_b) / max(1, len(team_b))
    if abs(a - b) < 1e-6:
        return 0 if random.random() < 0.5 else 1
    return 0 if a > b else 1


def _parasite_roll(attacker: Combatant) -> bool:
    if not attacker.is_parasite or attacker.parasite_chance <= 0:
        return False
    return random.randint(1, 100) <= attacker.parasite_chance


_PARAM_VALUE_LIMIT = 1000.0
_MAX_STRIKE_DMG = 20.0
_MIN_STRIKE_DMG = 0.2
# Combat HP ceiling. Keeps the whole-population multiplicative HP mutation
# (and already-inflated stored values) from stretching battles to the 250-round
# draw cap against million-HP defenders.
_MAX_UNIT_HP = 1000.0


def _effective_bounds(
    min_value: float | None,
    max_value: float | None,
) -> tuple[float, float]:
    """Effective [lo, hi] a parameter value may take: the engine's finite band,
    optionally tightened by the link's physical min/max when those fall inside
    the band (DB hints that sit outside the band are ignored so melee stays
    bounded)."""
    v = _PARAM_VALUE_LIMIT
    lo = -v
    hi = v
    if min_value is not None and -v <= float(min_value) <= v:
        lo = max(lo, float(min_value))
    if max_value is not None and -v <= float(max_value) <= v:
        hi = min(hi, float(max_value))
    return lo, hi


def _edge_distance(value: float, link: dict) -> float:
    """Distance from ``value`` to the nearest min/max bound of the parameter
    being attacked (the link's own recorded min_value / max_value)."""
    d = float("inf")
    for bound in (link.get("min_value"), link.get("max_value")):
        if bound is not None:
            d = min(d, abs(value - float(bound)))
    return d if d != float("inf") else 0.0


def _ability_strike(
    coeff: float,
    op: str,
    base_value: float | None,
    min_value: float | None,
    max_value: float | None,
    cur: float,
) -> float:
    """Adjust a parameter value with the ability's operator + coefficient,
    honoring the link's base/min/max.

    ``modify_coefficient_per_10msec`` is a per-10-ms rate, so the raw value is
    far too large to apply verbatim once per round (the aggregate would climb
    to the millions). We normalise it with a small per-round factor and keep
    the resulting value strictly inside a finite band so long melee stays
    bounded; DB min/max may only tighten the value within that band, never
    widen it.
    """
    v = _PARAM_VALUE_LIMIT
    cur = max(-v, min(v, cur))
    if op == "multiply":
        factor = max(-0.5, min(0.5, coeff * 0.1))
        new = cur * (1.0 + factor)
    elif op == "set":
        if base_value is not None:
            new = float(base_value)
        else:
            new = cur + max(-50.0, min(50.0, coeff * 0.1))
    else:  # add
        new = cur + max(-50.0, min(50.0, coeff * 0.1))
    lo, hi = _effective_bounds(min_value, max_value)
    return max(lo, min(hi, new))


def _roster_lines(combatants: list[Combatant], opponents: list[Combatant]) -> list[str]:
    """Opening description of each unit's parameters and abilities (with the
    parameters each ability targets), prepended to the battle log. After each
    ability it prints whether the opposing side has a counterpart ability that
    targets an overlapping parameter."""
    opp_pids: set[int] = set()
    for opp in opponents:
        for ab in opp.abilities_data:
            opp_pids.update(l["param_id"] for l in ab["params"])
    opp_names = ", ".join(o.name for o in opponents)
    lines: list[str] = []
    for c in combatants:
        lines.append(f"  unit {c.name}")
        pnames = c.param_names if c.param_names else {
            pid: f"p{pid}" for pid in c.params
        }
        if c.params:
            params_list = ", ".join(
                f"{pnames.get(pid, f'p{pid}')}={val:.2f}" for pid, val in c.params.items()
            )
            lines.append(f"    parameters: {params_list}")
        else:
            lines.append("    parameters: none")
        if c.abilities_data:
            for ab in c.abilities_data:
                targets = ", ".join(
                    l.get("param_name") or f"p{l['param_id']}" for l in ab["params"]
                )
                if any(l["param_id"] in opp_pids for l in ab["params"]):
                    counterpart = f"counterpart on {opp_names}: yes"
                else:
                    counterpart = f"counterpart on {opp_names}: none"
                lines.append(
                    f"    ability {ab['name']} -> parameters [{targets}] ({counterpart})"
                )
        else:
            lines.append("    abilities: none")
    return lines


def _run_battle(
    team_a: list[Combatant], team_b: list[Combatant], arena: str
) -> ArenaResult:
    log: list[str] = []
    battle_rejected = False
    initiative = _pick_initiative(team_a, team_b)
    order = [team_a, team_b] if initiative == 0 else [team_b, team_a]
    log.append(
        f"{arena} initiative: {'A' if initiative == 0 else 'B'} "
        f"({team_a[0].name if team_a else 'A'} vs "
        f"{team_b[0].name if team_b else 'B'})"
    )
    log.append("  ROSTER:")
    log.extend(_roster_lines(team_a, team_b))
    log.extend(_roster_lines(team_b, team_a))
    rounds = 0
    while any(c.alive for c in team_a) and any(c.alive for c in team_b):
        rounds += 1

        # If every surviving unit on BOTH sides is stuck (no harmful ability
        # AND no ECM-online parasite), the battle can never resolve.
        a_alive = [c for c in team_a if c.alive]
        b_alive = [c for c in team_b if c.alive]
        if not any(c.can_damage() for c in a_alive) and not any(
            c.can_damage() for c in b_alive
        ):
            battle_rejected = True
            log.append("battle rejected")
            break
        # Also reject if neither side has any ability that can target the other
        # side (no shared parameters between combatants), so the melee can never
        # fire and there is no way to interact.
        if not any(any(a.can_target(b) for b in b_alive) for a in a_alive) and not any(
            any(b.can_target(a) for a in a_alive) for b in b_alive
        ):
            battle_rejected = True
            log.append("battle rejected")
            break
        for team in order:
            attackers = [c for c in team if c.alive]
            defenders = [c for c in (team_b if team is team_a else team_a) if c.alive]
            if not attackers or not defenders:
                break

            # --- Param vs Param interactive phase ---
            # Each attacker picks one ability that shares a parameter with a defender.
            # The defender's parameter is altered by base_value * 0.4.
            # If parameter exceeds physical bounds, the ability is destroyed.
            # An event fires, triggering a counter-ability from defender.
            for src in [c for c in attackers if c.alive]:
                alive_def = [d for d in defenders if d.alive]
                if not alive_def:
                    break
                partner = random.choice(alive_def)

                # Find shared parameters between src abilities and partner params
                shared = []  # (ab, link, pid)
                for ab in src.abilities_data:
                    for link in ab["params"]:
                        pid = link["param_id"]
                        if pid in partner.params:
                            shared.append((ab, link, pid))

                if not shared:
                    continue  # no shared params, skip

                # Attacker picks one shared param to strike
                ab, link, pid = random.choice(shared)
                # Ability alters the value to max_value / modify_coefficient
                # for this ability->param link.
                lo, hi = _effective_bounds(link["min_value"], link["max_value"])
                coefficient = link.get("coefficient") or 0.0
                target = hi / coefficient if coefficient else hi
                cur = partner.params[pid]
                newv = target
                partner.params[pid] = max(lo, min(hi, newv))
                # A strike with no actual change (delta 0) would stall melee
                # forever, so force the parameter to its minimum instead.
                if partner.params[pid] == cur:
                    partner.params[pid] = lo

                # Check if parameter exceeded physical bounds
                exceeded = newv < lo or newv > hi
                if exceeded:
                    # Destroy the attacking ability ...
                    src.abilities_data = [a for a in src.abilities_data if a != ab]
                    flat = f"r{rounds} MALFUNCTION {src.name} [{ab['name']}] parameter {link['param_name']} " \
                           f"exceeded bounds ({cur:.2f}->{newv:.2f}) -- ability destroyed"
                    # ... and disable ALL of the defender's abilities linked to
                    # the out-of-bounds parameter (the parameter is corrupted).
                    doomed = [
                        a for a in partner.abilities_data
                        if any(l["param_id"] == pid for l in a["params"])
                    ]
                    if doomed:
                        for a in doomed:
                            log.append(
                                f"r{rounds} {partner.name} [{a['name']}] disabled via "
                                f"out-of-bounds {link['param_name']} -- ability destroyed"
                            )
                        partner.abilities_data = [
                            a for a in partner.abilities_data if a not in doomed
                        ]
                    log.append(flat)

                dst = partner.params[pid]
                delta = dst - cur
                edge = _edge_distance(dst, link)
                log.append(
                    f"r{rounds} {src.name} {ab['name']}->{link['param_name']} "
                    f"src={cur:.2f} delta={delta:+.2f} dst={dst:.2f} edge={edge:.2f} "
                    f"on {partner.name}"
                )

                # Defender selects counter-ability (must share a param with attacker)
                counter_shared = []
                for def_ab in partner.abilities_data:
                    for def_link in def_ab["params"]:
                        if def_link["param_id"] in src.params:
                            counter_shared.append(
                                (def_ab, def_link, def_link["param_id"])
                            )

                if counter_shared:
                    c_ab, c_link, c_pid = random.choice(counter_shared)
                    # Counter-ability also alters the value to
                    # max_value / modify_coefficient for its link.
                    c_lo, c_hi = _effective_bounds(
                        c_link["min_value"], c_link["max_value"]
                    )
                    c_coefficient = c_link.get("coefficient") or 0.0
                    c_target = c_hi / c_coefficient if c_coefficient else c_hi
                    c_cur = src.params[c_pid]
                    c_newv = c_target
                    src.params[c_pid] = max(c_lo, min(c_hi, c_newv))

                    c_exceeded = c_newv < c_lo or c_newv > c_hi
                    if c_exceeded:
                        partner.abilities_data = [
                            a for a in partner.abilities_data if a != c_ab
                        ]
                        # Disable ALL of the attacker's abilities linked to the
                        # out-of-bounds parameter.
                        doomed = [
                            a for a in src.abilities_data
                            if any(l["param_id"] == c_pid for l in a["params"])
                        ]
                        if doomed:
                            for a in doomed:
                                log.append(
                                    f"r{rounds} {src.name} [{a['name']}] disabled via "
                                    f"out-of-bounds {c_link['param_name']} -- ability destroyed"
                                )
                            src.abilities_data = [
                                a for a in src.abilities_data if a not in doomed
                            ]
                        log.append(
                            f"r{rounds} {partner.name} counter [{c_ab['name']}] parameter {c_link['param_name']} "
                            f"exceeded bounds ({c_cur:.2f}->{c_newv:.2f}) -- counter-ability destroyed"
                        )

                    c_dst = src.params[c_pid]
                    c_delta = c_dst - c_cur
                    c_edge = _edge_distance(c_dst, c_link)
                    log.append(
                        f"r{rounds} {partner.name} counter {c_ab['name']}->{c_link['param_name']} "
                        f"src={c_cur:.2f} delta={c_delta:+.2f} dst={c_dst:.2f} edge={c_edge:.2f} "
                        f"on {src.name}"
                    )

                # Small HP damage from parameter stress
                stress_dmg = min(abs(partner.params[pid] - cur) * 0.05, 5.0)
                if stress_dmg > 0:
                    src.hp = round(max(0.0, src.hp - stress_dmg), 3)
                    partner.hp = round(max(0.0, partner.hp - stress_dmg), 3)

                # Parasite phase: combatant with no abilities but parasite_chance > 0.
                # A parasite only functions when ECM (anti_emc) is online.
                for c in (src, partner):
                    if (
                        c.alive
                        and not c.abilities_data
                        and c.parasite_chance > 0
                        and c.is_anti_emc
                    ):
                        # Parasite attack: automatic hit if parasite_roll succeeds
                        if _parasite_roll(c):
                            dmg = 10.0 + (c.parasite_chance * 0.2)
                            # Target the other combatant
                            target = partner if c is src else src
                            target.hp = round(max(0.0, target.hp - dmg), 3)
                            log.append(
                                f"r{rounds} {c.name} PARASITE strike ({c.parasite_chance}% chance) "
                                f"hits {target.name} for {dmg:.2f}; {target.name} hp={target.hp:.2f}"
                            )
                            if target.hp <= 0 and not target.eliminated_logged:
                                target.eliminated_logged = True
                                log.append(f"r{rounds} {target.name} eliminated")

                # Parasite vulnerability: any counter-ability destroys the parasite
                for c in (src, partner):
                    if c.alive and not c.abilities_data and c.parasite_chance > 0:
                        enemy = partner if c is src else src
                        if enemy.alive and enemy.abilities_data:
                            # Enemy uses counter to destroy parasite
                            c_ab = enemy.abilities_data[0]
                            log.append(
                                f"r{rounds} {enemy.name} counter [{c_ab['name']}] "
                                f"destroyed {c.name}'s parasite function -- {c.name} eliminated"
                            )
                            c.hp = 0
                            c.eliminated_logged = True
                            log.append(
                                f"r{rounds} {c.name} eliminated (parasite destroyed)"
                            )

                if not src.alive or not partner.alive:
                    break

            if not any(c.alive for c in team_a) or not any(c.alive for c in team_b):
                break

            # Standard strike phase: a unit cannot just "hit". It damages via its
            # abilities (handled in the melee phase) or via a parasite strike,
            # and a parasite strike only lands if the unit's ECM (anti_emc) is
            # online.
            alive_defs = [d for d in defenders if d.alive]
            if alive_defs:
                atk = random.choice(attackers)
                tgt = random.choice(alive_defs)
                ecm_online = atk.is_anti_emc
                # ECM/parasite is only used by units WITHOUT abilities; a unit
                # that has abilities fights with those instead of ECM.
                if (
                    not atk.abilities_data
                    and atk.is_parasite
                    and atk.parasite_chance > 0
                    and ecm_online
                ):
                    if _parasite_roll(atk):
                        dmg = 10.0 + (atk.parasite_chance * 0.2)
                        tgt.hp = round(max(0.0, tgt.hp - dmg), 3)
                        log.append(
                            f"r{rounds} {atk.name} PARASITE strike ({atk.parasite_chance}% chance, ECM online) "
                            f"hits {tgt.name} for {dmg:.2f}; {tgt.name} hp={tgt.hp:.2f}"
                        )
                        if tgt.hp <= 0 and not tgt.eliminated_logged:
                            tgt.eliminated_logged = True
                            log.append(f"r{rounds} {tgt.name} eliminated")
                elif not atk.is_armed():
                    log.append(
                        f"r{rounds} DISARMED {atk.name} cannot hit -- no harmful ability"
                    )
                else:
                    log.append(
                        f"r{rounds} NO-HIT {atk.name} cannot strike -- no ECM online for parasite, abilities only"
                    )

            if not any(c.alive for c in team_b) or not any(c.alive for c in team_a):
                break
        if rounds > 250:
            log.append("r%s draw (round cap reached)" % rounds)
            break

    survivors = [c.unit_id for c in team_a + team_b if c.hp > 0]
    loser_ids: list[int] = []
    winner: Combatant | None = None
    if battle_rejected:
        log.append("battle rejected")
    elif any(c.alive for c in team_a) and not any(c.alive for c in team_b):
        winner = max((c for c in team_a if c.alive), key=lambda c: c.hp, default=None)
        loser_ids = [c.unit_id for c in team_b if not c.alive]
    elif any(c.alive for c in team_b) and not any(c.alive for c in team_a):
        winner = max((c for c in team_b if c.alive), key=lambda c: c.hp, default=None)
        loser_ids = [c.unit_id for c in team_a if not c.alive]
    else:
        log.append("draw")

    return ArenaResult(
        map=arena,
        winner_id=winner.unit_id if winner else None,
        winner_name=winner.name if winner else None,
        loser_ids=loser_ids,
        rounds=rounds,
        log=log,
        survivors=survivors,
        battle_rejected=battle_rejected,
    )


def _unit_load_options():
    from main import ItemDB, AbilityDB, AbilityParamDB, EventDB, ParameterDB, ItemParameterDB
    from sqlalchemy.orm import selectinload
    return [
        selectinload(ItemDB.subitems),
        selectinload(ItemDB.abilities)
        .selectinload(AbilityDB.ability_params)
        .selectinload(AbilityParamDB.parameter),
        selectinload(ItemDB.abilities)
        .selectinload(AbilityDB.events),
        selectinload(ItemDB.item_parameters)
        .selectinload(ItemParameterDB.parameter),
    ]


def _pick_random(db: Session, n: int) -> list[ItemDB]:
    from main import ItemDB
    from sqlalchemy import select
    ids = db.scalars(
        select(ItemDB.id).where(ItemDB.parent_id.is_(None))
    ).all()
    if len(ids) < n:
        ids = list(ids)
    else:
        ids = random.sample(list(ids), n)
    if not ids:
        return []
    return db.scalars(
        select(ItemDB).where(ItemDB.id.in_(ids)).options(*_unit_load_options())
    ).all()


def _pick_combatants(db: Session, items) -> list[Combatant]:
    from main import ItemDB
    from sqlalchemy import select
    ids = [it.id for it in items]
    if not ids:
        return []
    fresh = db.scalars(
        select(ItemDB)
        .where(ItemDB.id.in_(ids))
        .options(*_unit_load_options())
    ).all()
    return [Combatant.from_item(it) for it in fresh]


def run_random_1x1(db: Session, gen: int) -> ArenaResult | None:
    picks = _pick_random(db, 2)
    if len(picks) < 2:
        return None
    a, b = _pick_combatants(db, picks)
    return _run_battle([a], [b], "1x1")


def run_random_1x2(db: Session, gen: int) -> ArenaResult | None:
    picks = _pick_random(db, 3)
    if len(picks) < 3:
        return None
    a, b, c = picks
    return _run_battle(_pick_combatants(db, [a]), _pick_combatants(db, [b, c]), "1x2")


def run_random_2x2(db: Session, gen: int) -> ArenaResult | None:
    picks = _pick_random(db, 4)
    if len(picks) < 4:
        return None
    a, b, c, d = picks
    return _run_battle(
        _pick_combatants(db, [a, b]),
        _pick_combatants(db, [c, d]),
        "2x2",
    )


def run_genetic_1x1(db: Session, gen: int) -> ArenaResult | None:
    from main import ItemDB
    from sqlalchemy import select, desc
    top = db.scalars(select(ItemDB).order_by(desc(ItemDB.hp)).limit(2)).all()
    if len(top) < 2:
        return None
    a, b = _pick_combatants(db, top)
    return _run_battle([a], [b], "1x1")


def run_genetic_1x2(db: Session, gen: int) -> ArenaResult | None:
    from main import ItemDB
    from sqlalchemy import select, desc
    top = db.scalars(select(ItemDB).order_by(desc(ItemDB.hp)).limit(3)).all()
    if len(top) < 3:
        return None
    a, b, c = top
    return _run_battle(_pick_combatants(db, [a]), _pick_combatants(db, [b, c]), "1x2")


def run_genetic_2x2(db: Session, gen: int) -> ArenaResult | None:
    from main import ItemDB
    from sqlalchemy import select, desc
    top = db.scalars(select(ItemDB).order_by(desc(ItemDB.hp)).limit(4)).all()
    if len(top) < 4:
        return None
    a, b, c, d = top
    return _run_battle(
        _pick_combatants(db, [a, b]),
        _pick_combatants(db, [c, d]),
        "2x2",
    )


@dataclass
class TickResult:
    generation: int
    built: int
    joined: int
    mutated_props: int
    tested: dict[str, int]
    battles: list[ArenaResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "built": self.built,
            "joined": self.joined,
            "mutated_props": self.mutated_props,
            "tested": self.tested,
            "battles": [b.to_dict() for b in self.battles],
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
    gen = _current_generation(db) + 1

    # 1) Build
    built = build_units(db, build_count)
    _log(db, gen, "build", {"count": len(built), "ids": [b.id for b in built]})

    # 2) Join
    joined = join_random_pairs(db, join_pairs)
    _log(
        db,
        gen,
        "join",
        {"pairs": join_pairs, "ids": [c.id for c in joined]},
    )

    # 3) Mutate props
    reports = mutate_population_props(
        db, fraction=props_fraction, strength=props_strength
    )
    _log(
        db,
        gen,
        "props",
        {"fraction": props_fraction, "touched": len(reports)},
    )

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

    # 5) Combat arena — 1x1 only for now (random + genetic)
    battles: list[ArenaResult] = []
    for fn in (
        run_random_1x1,
        run_genetic_1x1,
    ):
        result = fn(db, gen)
        if result is not None:
            battles.append(result)

    logger.info(
        "tick %d complete: built=%d joined=%d mutated=%d tested=%d/%d broken battles=%d",
        gen,
        len(built),
        len(joined),
        len(reports),
        ok_count,
        len(test_reports),
        len(battles),
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
        battles=battles,
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


def leaderboard(db: Session, limit: int = 20) -> list[dict[str, Any]]:
    """Top units by win-count in war_log, falling back to fitness."""
    from sqlalchemy import text

    rows = db.execute(
        text(
            "SELECT unit_id, wins FROM ("
            "  SELECT json_extract(detail, '$.winner_id') AS unit_id, "
            "         COUNT(*) AS wins "
            "  FROM war_log WHERE stage='combat' "
            "    AND json_extract(detail, '$.winner_id') IS NOT NULL "
            "  GROUP BY json_extract(detail, '$.winner_id')"
            ") ORDER BY wins DESC LIMIT :lim"
        ),
        {"lim": limit},
    ).all()
    if not rows:
        return []
    ids = [int(r[0]) for r in rows]
    wins = {int(r[0]): int(r[1]) for r in rows}
    items = db.scalars(
        select(ItemDB).where(ItemDB.id.in_(ids)).options(*_unit_load_options()[1:])
    ).all()
    by_id = {it.id: it for it in items}
    board: list[dict[str, Any]] = []
    for wid in sorted(wins, key=lambda k: wins[k], reverse=True):
        it = by_id.get(wid)
        if it is None:
            continue
        c = Combatant.from_item(it)
        board.append(
            {
                "unit_id": wid,
                "name": it.name,
                "wins": wins[wid],
                "fitness": _fitness(c),
                "attack": c.attack,
                "defense": c.defense,
                "speed": c.speed,
                "hp": c.hp,
            }
        )
    return board


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
                    "daemon tick #%d: gen=%d built=%d joined=%d broken=%d battles=%d",
                    self.tick_count,
                    result.generation,
                    result.built,
                    result.joined,
                    result.tested["broken"],
                    len(result.battles),
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
        + " battles="
        + str(sum(len(r.battles) for r in out))
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
            + " battles="
            + str(sum(len(r.battles) for r in out))
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
