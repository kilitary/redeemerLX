"""Run randomly on ALL properties of every existing item in the database,
including the per-item parameter boundary values.

For every item_parameters row belonging to an item we set a realistic
base_value / min_value / max_value envelope derived from the parameter's own
physical bounds (parameters.min_value / max_value) and its current value.

Run:  .venv/bin/python randomize_items.py
"""

import datetime
import random

from sqlalchemy import create_engine, select
from sqlalchemy.orm import (
    sessionmaker,
)

from main import (
    SQLALCHEMY_DATABASE_URL,
    AbilityDB,
    ItemDB,
    ItemParameterDB,
    ParameterDB,
)
from parts import BRANDS, COLORS, MODELS, PART_KINDS, SIZES

print(f"connecting to {SQLALCHEMY_DATABASE_URL}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": True},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def random_name() -> str:
    kind = random.choice(PART_KINDS)
    brand = random.choice(BRANDS)
    model = random.choice(MODELS)
    suffix = random.randint(1, 4)
    return f"{brand} {kind} {model} {suffix}"


def random_price() -> float:
    return round(random.uniform(0.5, 1000), 2)


def random_weight() -> float:
    return round(random.uniform(0, 100), 2)


def random_oil() -> float:
    return round(random.uniform(0, 25), 2)


def random_bool(p: float = 0.5) -> bool:
    return random.random() < p


def random_delta(max_minutes: int) -> datetime.timedelta:
    """Return a timedelta with a random integer number of minutes in [0, max_minutes]."""
    return datetime.timedelta(minutes=random.randint(0, max_minutes))


def round_value(v: float | None) -> float | None:
    return None if v is None else round(v, 4)


def random_bounds(
    value: float | None,
    param_min: float | None,
    param_max: float | None,
) -> tuple[float | None, float | None, float | None]:
    """Return (base_value, min_value, max_value) centred around ``value``.

    The base is the parameter's current value (falling back to the midpoint of
    the parameter's own bounds). A sign-aware symmetric spread around the base
    widens the min/max envelope, then both ends are clamped to the parameter's
    physical min/max when those exist. The invariant ``min <= base <= max`` is
    always preserved (min may equal base only when base sits on the lower bound).
    """
    if value is not None:
        base = value
    elif param_min is not None and param_max is not None:
        base = (param_min + param_max) / 2.0
    elif param_min is not None:
        base = param_min
    elif param_max is not None:
        base = param_max
    else:
        base = 1.0

    spread = (
        abs(base) * random.uniform(0.1, 0.8) if base != 0 else random.uniform(0.1, 1.0)
    )
    lo = base - spread
    hi = base + spread

    if param_min is not None:
        lo = max(lo, param_min)
    if param_max is not None:
        hi = min(hi, param_max)

    # Enforce min <= base <= max; min may equal base only at the lower bound.
    lo = min(lo, base)
    hi = max(hi, base)

    return round_value(base), round_value(lo), round_value(hi)


def main() -> None:

    with SessionLocal() as db:
        all_abilities = db.scalars(select(AbilityDB)).all()
        items = db.scalars(select(ItemDB)).all()
        params_by_id = {p.id: p for p in db.scalars(select(ParameterDB)).all()}
        count = len(items)
        param_rows = 0
        for item in items:
            item.name = random_name()
            item.price = random_price()
            item.quantity = random.randint(1, 4)
            item.is_offer = random_bool(0.05)
            item.color = random.choice(COLORS)
            item.size = random.choice(SIZES)
            item.weight = random_weight()
            item.oil = random_oil()
            item.is_anti_emc = random_bool(0.9)
            item.is_proof = random_bool(0.6)
            item.water_resistant = random_bool(0.7)
            item.self_desentry = random_bool(0.55)
            item.is_parasite = random_bool(0.9)
            if all_abilities:
                item.abilities = random.sample(
                    all_abilities, random.randint(0, min(1, len(all_abilities)))
                )
            item.updated_at = datetime.datetime.now(datetime.UTC) - random_delta(
                1111440
            )
            item.added_at = datetime.datetime.now(datetime.UTC) - random_delta(11111440)

            item_params = db.scalars(
                select(ItemParameterDB).where(ItemParameterDB.item_id == item.id)
            ).all()
            for p in item_params:
                prm = params_by_id.get(p.par_id)
                p.base_value, p.min_value, p.max_value = random_bounds(
                    p.value,
                    prm.min_value if prm else None,
                    prm.max_value if prm else None,
                )
                param_rows += 1
        db.commit()

    print(
        f"Randomized all properties on {count} existing item(s); "
        + f"set min/max/base on {param_rows} item-parameter rows."
    )


if __name__ == "__main__":
    main()
