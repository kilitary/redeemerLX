#!/usr/bin/env python3
"""Truncate item_parameters and repopulate with random values within each parameter's min/max.
Also sync min_value, max_value, base_value from parameters table. Value rounded to 2 decimal places."""
import logging
import random
import sqlite3

DB = "data/items.db"

def main():
    # Configure logging with timestamps and icons
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info("🚀 Starting item_parameters regeneration script")

    conn = sqlite3.connect(DB)
    _ = conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Get parameter bounds from parameters table
    _ = cur.execute(
        "SELECT id, min_value, max_value FROM parameters "
        "WHERE min_value IS NOT NULL AND max_value IS NOT NULL"
    )
    bounds = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
    logging.info(f"📊 Retrieved bounds for {len(bounds)} parameters")

    # 1. Truncate item_parameters
    _ = cur.execute("DELETE FROM item_parameters")
    truncated = cur.rowcount
    logging.info(f"🗑️ Truncated {truncated} rows from item_parameters")

    # 2. Get all items
    _ = cur.execute("SELECT id FROM items")
    item_ids = [row[0] for row in cur.fetchall()]
    logging.info(f"🔎 Found {len(item_ids)} items")

    done = []
    # 3. Insert random value for each (item, param) within bounds
    inserted = 0
    for item_id in item_ids:
        for pid, (mn, mx) in bounds.items():
            val = round(random.uniform(mn, mx), 2)
            if item_id not in done:
                logging.info(
                    f"🔧 item_id={item_id} param_id={pid} value={val} (min={mn}, max={mx})"
                )
                done.append(item_id)

            _ = cur.execute(
                "INSERT INTO item_parameters (item_id, par_id, value, min_value, max_value, base_value) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, pid, val, mn, mx, round(mn * 0.2, 2)),
            )
            inserted += 1

    conn.commit()
    logging.info(
        f"✅ Inserted {inserted} item_parameters rows ({len(item_ids)} items × {len(bounds)} params)"
    )
    conn.close()
    logging.info("🏁 Script completed successfully")

if __name__ == "__main__":
    main()
