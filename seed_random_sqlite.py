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

    # Load bounds, abilities, events
    cur.execute(
        "SELECT id, min_value, max_value FROM parameters WHERE min_value IS NOT NULL AND max_value IS NOT NULL"
    )
    bounds = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

    cur.execute("SELECT id FROM abilities")
    ability_ids = [row[0] for row in cur.fetchall()]

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
            name = f"{random.choice(PART_KINDS + ALL_PARTS + SUB_NAMES)} {random.choice(MODELS)}"
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
    conn.close()

    print(f"Added {count} random items with parameters, abilities, and events.")


if __name__ == "__main__":
    main()
