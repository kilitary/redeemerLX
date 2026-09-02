#!/usr/bin/env python3
"""Seed random items using sqlite3 directly (no SQLAlchemy imports)."""

import random
import sqlite3
from datetime import datetime, timedelta, timezone

DB = "data/items.db"

# Import parts lists
import sys

sys.path.insert(0, ".")
from parts import ALL_PARTS, BRANDS, COLORS, MODELS, NAMES, PART_KINDS, SIZES, SUB_NAMES

# Auto-assigned single-word category per ability (e.g. measure/meter/serialize -> scan).
from ability import ability_category


def random_delta(max_minutes: int) -> timedelta:
    return timedelta(minutes=random.randint(0, max_minutes))


def random_price() -> float:
    return round(random.uniform(0.5, 999.99), 2)


def random_weight() -> float:
    return round(random.uniform(0, 15), 2)


def main(count: int = 100) -> None:
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cur.execute("SELECT id, name, category FROM abilities")
    ability_info = [(row[0], row[1], row[2]) for row in cur.fetchall()]
    ability_ids = [a[0] for a in ability_info]

    # Load bounds, events
    cur.execute(
        "SELECT id, min_value, max_value FROM parameters WHERE min_value IS NOT NULL AND max_value IS NOT NULL"
    )
    bounds = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

    cur.execute("SELECT id FROM events")
    event_ids = [row[0] for row in cur.fetchall()]

    print(
        f"Loaded {len(bounds)} parameter bounds, {len(ability_ids)} abilities, {len(event_ids)} events"
    )

    # Truncate items and related tables
    cur.execute("DELETE FROM item_abilities")
    cur.execute("DELETE FROM event_abilities")
    cur.execute("DELETE FROM item_parameters")
    cur.execute("DELETE FROM items")
    conn.commit()
    print("Truncated items and related tables")

    # Assign a single-word category to each ability (auto) and mirror it into
    # the ability_category link table.
    now_ts = now_iso
    cur.execute("DELETE FROM ability_category")
    for aid, name, old_cat in ability_info:
        cat = ability_category(name) if not old_cat else old_cat
        cur.execute(
            "UPDATE abilities SET category = ? WHERE id = ?", (cat, aid)
        )
        cur.execute(
            "INSERT INTO ability_category (ability_id, category, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (aid, cat, now_ts, now_ts),
        )
    conn.commit()
    print(f"Assigned categories to {len(ability_info)} abilities (ability_category rebuilt)")

    # Insert root items
    root_items = []
    for i in range(count):
        name = f"{random.choice(BRANDS)} {random.choice(NAMES)} {random.choice(MODELS)}"
        price = random_price()
        quantity = 1
        is_offer = 1 if random.random() < 0.3 else 0
        color = random.choice(COLORS)
        size = random.choice(SIZES)
        weight = random_weight()
        is_anti_emc = 1 if random.random() < 0.4 else 0
        is_proof = 1 if random.random() < 0.4 else 0
        water_resistant = 1 if random.random() < 0.3 else 0
        oil = round(random.uniform(0, 100), 2)
        self_desentry = 0
        is_parasite = 1 if random.random() < 0.15 else 0
        parasite_chance = 0
        revision = 1
        hp = random.randint(50, 100)
        added_at = (now - timedelta(minutes=count * 3 - i * 3)).isoformat()
        updated_at = added_at

        cur.execute(
            """
            INSERT INTO items (name, price, quantity, is_offer, color, size, weight,
                is_anti_emc, is_proof, water_resistant, oil, self_desentry,
                is_parasite, parasite_chance, revision, hp, added_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                name,
                price,
                quantity,
                is_offer,
                color,
                size,
                weight,
                is_anti_emc,
                is_proof,
                water_resistant,
                oil,
                self_desentry,
                is_parasite,
                parasite_chance,
                revision,
                hp,
                added_at,
                updated_at,
            ),
        )
        root_items.append(cur.lastrowid)

    # Insert subitems
    for parent_id in root_items:
        for _ in range(random.randint(1, 4)):
            name = f"{random.choice(BRANDS)} {random.choice(PART_KINDS + ALL_PARTS + SUB_NAMES)} {random.choice(MODELS)} {random.randint(1, 4)}"
            quantity = random.randint(1, 8)
            price = random_price()
            is_offer = 1 if random.random() < 0.3 else 0
            color = random.choice(COLORS)
            size = random.choice(SIZES)
            weight = round(random.uniform(0, 5), 2)
            is_anti_emc = 1 if random.random() < 0.4 else 0
            is_proof = 1 if random.random() < 0.4 else 0
            water_resistant = 1 if random.random() < 0.3 else 0
            oil = 0
            self_desentry = 1 if random.random() < 0.1 else 0
            is_parasite = 1 if random.random() < 0.15 else 0
            parasite_chance = random.randint(0, 100)
            revision = random.randint(1, 5)
            hp = random.randint(10, 50)
            added_at = now_iso
            updated_at = now_iso

            cur.execute(
                """
                INSERT INTO items (parent_id, name, price, quantity, is_offer, color, size, weight,
                    is_anti_emc, is_proof, water_resistant, oil, self_desentry,
                    is_parasite, parasite_chance, revision, hp, added_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    parent_id,
                    name,
                    price,
                    quantity,
                    is_offer,
                    color,
                    size,
                    weight,
                    is_anti_emc,
                    is_proof,
                    water_resistant,
                    oil,
                    self_desentry,
                    is_parasite,
                    parasite_chance,
                    revision,
                    hp,
                    added_at,
                    updated_at,
                ),
            )

    # Insert item_parameters for root items only (subitems don't get params)
    for item_id in root_items:
        for pid, (mn, mx) in bounds.items():
            val = round(random.uniform(mn, mx), 2)
            cur.execute(
                "INSERT INTO item_parameters (item_id, par_id, value) VALUES (?, ?, ?)",
                (item_id, pid, val),
            )

    # Insert item_abilities for root items
    for item_id in root_items:
        num_abilities = random.randint(1, 3)
        chosen = random.sample(ability_ids, k=min(num_abilities, len(ability_ids)))
        for aid in chosen:
            cur.execute(
                "INSERT INTO item_abilities (item_id, ability_id) VALUES (?, ?)",
                (item_id, aid),
            )

    # Attach events to abilities (each event -> 1 random ability)
    cur.execute("DELETE FROM event_abilities")
    for eid in event_ids:
        aid = random.choice(ability_ids)
        cur.execute(
            "INSERT INTO event_abilities (event_id, ability_id) VALUES (?, ?)",
            (eid, aid),
        )

    # Ability -> param links: only reference PHYSICAL parameters. The real
    # physical/spec parameters are those with numeric bounds (min_value and
    # max_value set), i.e. everything keyed in `bounds` (ids 61-120). Abilities
    # may only target these, so melee shared-param matching can actually fire.
    physical_param_ids = list(bounds.keys())
    cur.execute("DELETE FROM ability_to_params")
    for aid in ability_ids:
        n_links = random.randint(1, 3)
        chosen = random.sample(
            physical_param_ids, k=min(n_links, len(physical_param_ids))
        )
        for pid in chosen:
            _, pmax = bounds[pid]
            max_v = pmax if pmax is not None else 100.0
            # Target value = max_value / modify_coefficient. Seed a coefficient
            # >= 1 so the struck value lands inside its own [0, max_value] band
            # (otherwise every strike would exceed bounds and self-destroy).
            coeff = round(random.uniform(1.0, 6.0), 5)
            now_ts = now_iso
            if random.random() < 0.3:
                coeff = -coeff
            cur.execute(
                """INSERT INTO ability_to_params
                   (ability_id, param_id, modify_coefficient_per_10msec, operation,
                    base_value, min_value, max_value, curve, stack_mode, priority,
                    enabled, description, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    aid,
                    pid,
                    coeff,
                    "add",
                    None,
                    0.0,
                    max_v,
                    "linear",
                    "stack",
                    random.randint(0, 10),
                    1,
                    "alter the target physical parameter",
                    now_ts,
                    now_ts,
                ),
            )

    conn.commit()
    conn.close()

    # Verify
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM items WHERE parent_id IS NULL")
    print(f"Root items: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM items WHERE parent_id IS NOT NULL")
    print(f"Subitems: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM item_parameters")
    print(f"Item params: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM item_abilities")
    print(f"Item abilities: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM event_abilities")
    print(f"Event-ability links: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM ability_to_params")
    print(f"Ability-param links: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM ability_category")
    print(f"Ability-category links: {cur.fetchone()[0]}")
    conn.close()

    print(f"Added {count} random items with parameters, abilities, and events.")


if __name__ == "__main__":
    main()
