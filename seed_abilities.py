"""Seed the abilities table and randomly assign abilities to every existing item.

Run:  .venv/bin/python seed_abilities.py
"""

import random

from sqlalchemy import select

from ability import ABILITIES
from main import AbilityDB, ItemDB, SessionLocal


def seed_ability_rows(db) -> int:
    """Create every static ability verb that is missing from the database."""
    created = 0
    for spec in ABILITIES:
        existing = db.scalar(
            select(AbilityDB).where(AbilityDB.name == spec.name).limit(1)
        )
        if existing is None:
            db.add(
                AbilityDB(
                    name=spec.name,
                    description=spec.description,
                    description_ru=spec.description_ru,
                )
            )
            created += 1
    db.flush()
    return created


def randomize_item_abilities(db) -> int:
    """Assign a random subset of abilities to every existing item."""
    all_abilities = db.scalars(select(AbilityDB)).all()
    items = db.scalars(select(ItemDB).where(ItemDB.parent_id.is_(None))).all()
    if not all_abilities:
        raise RuntimeError("No abilities seeded; run seeder first.")

    changed = 0
    for item in items:
        count = random.randint(0, min(6, len(all_abilities)))
        chosen = random.sample(all_abilities, count)
        if set(item.abilities) != set(chosen):
            item.abilities = chosen
            changed += 1
    return changed


def main() -> None:
    with SessionLocal() as db:
        created = seed_ability_rows(db)
        db.commit()
        changed = randomize_item_abilities(db)
        db.commit()

    print(f"Seeded {created} missing ability(verb)(ies).")
    print(f"Randomized abilities on {changed} item(s).")


if __name__ == "__main__":
    main()
