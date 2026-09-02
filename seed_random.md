# `seed_random.py` – Random Item Seeder for the FastAPI Project

## Overview

`seed_random.py` is a utility script designed to populate the **items** SQLite database with a set of randomly generated items, their sub‑items, parameters, and abilities. It is particularly useful during development and testing to quickly create a realistic data set without manual entry.

## How It Works

1. **Database Connection**  
   Uses the project's SQLAlchemy session (`SessionLocal`) to interact with `data/items.db`.

2. **Loading Reference Data**  
   * `load_param_bounds` – Retrieves parameter IDs together with their minimum and maximum allowed values.  
   * `load_ability_ids` – Pulls a list of all existing ability IDs.

3. **Cleaning the Table**  
   Deletes every existing `ItemDB` record (including cascades for sub‑items) to start from a fresh state.

4. **Generating Random Items**  
   * `random_item()` creates an `ItemDB` instance with random attributes (name, price, quantity, flags, etc.).  
   * Each item may contain **0‑4** sub‑items, also generated randomly.

5. **Staggered Timestamps**  
   The script sets `added_at` and `updated_at` values so that items are ordered chronologically, which makes sorting by date meaningful in the UI.

6. **Persisting Items**  
   All items are added to the session, flushed to obtain primary keys, and then **random parameters** and **random abilities** are attached:
   * `add_random_params` creates `ItemParameterDB` rows respecting each parameter’s bounds.  
   * `add_random_abilities` links 1‑3 random `AbilityDB` objects to each item.

7. **Commit & Verification**  
   After committing the transaction, a quick SQLite query prints the number of root items (those with `parent_id IS NULL`) to confirm the seeding succeeded.

## Running the Script

```bash
# Activate the virtual environment if not already active
source .venv/bin/activate

# Execute the seeder (default adds 30 items)
python seed_random.py
```

You can also specify a custom number of items:

```bash
python seed_random.py 100   # seed 100 items
```

> **Note:** The script always wipes the `items` table first, so run it only against a development or test database.

## Key Functions

| Function | Purpose |
|----------|---------|
| `random_delta(max_minutes)` | Generates a `timedelta` with a random minute offset up to `max_minutes`. |
| `random_price()` | Returns a random price between **0.5** and **999.99** (2‑decimal precision). |
| `random_weight()` | Returns a random weight between **0** and **15** (2‑decimal precision). |
| `random_item()` | Constructs a fully‑populated `ItemDB` object, including optional sub‑items. |
| `load_param_bounds(db)` | Fetches parameter bounds (`min_value`, `max_value`) from the `parameters` table. |
| `load_ability_ids(db)` | Retrieves all ability IDs from the `abilities` table. |
| `add_random_params(db, item, bounds)` | Adds `ItemParameterDB` entries for the given item within the specified bounds. |
| `add_random_abilities(db, item, ability_ids)` | Attaches 1‑3 random abilities to the item. |
| `main(count=30)` | Orchestrates the whole seeding process. |

## Extending the Seeder

* **More Sub‑items** – Adjust the range in `random.randint(0, 4)` inside `random_item()`.  
* **Custom Attribute Ranges** – Modify `random_price`, `random_weight`, or the boolean probabilities to better reflect your domain.  
* **Additional Relationships** – Hook other tables (e.g., tags, categories) by adding similar helper functions and linking them in the `main` loop.

## Why Use This Script?

* **Rapid Prototyping** – Populate the UI with diverse data instantly.  
* **Automated Tests** – Generate a fresh data set for each test run to avoid flaky tests.  
* **Demo Environments** – Provide a believable catalogue without manual entry.

---

*Generated for the FastAPI project located at `mnt/projects/fastapi/seed_random.py`.*
