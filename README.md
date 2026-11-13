# Jesus Christ Nuclear Revenge D-Days Panel

FastAPI CRUD application for managing "units" (items) with abilities, subitems,
events, and a war-factory simulation. Styled as a Command & Conquer military
HUD.

The app exposes a JSON CRUD API plus a set of server-rendered HUD pages
(warehouse, item detail, test facility, combat duel, war factory, events,
abilities). All state lives in a single SQLite database.

## Stack

| Piece        | Choice                                             |
|--------------|----------------------------------------------------|
| Language     | Python >= 3.12                                     |
| Web          | FastAPI (`fastapi[standard]`) + Starlette          |
| ORM          | SQLAlchemy 2.0 (typed `Mapped` / `mapped_column`)  |
| Database     | SQLite (`data/items.db`)                           |
| Templates    | Jinja2                                             |
| Frontend     | Plain CSS/JS, no build step                        |
| Packaging    | [uv](https://docs.astral.sh/uv/) (`uv.lock`)       |

## Running

```bash
# install deps into .venv
uv sync

# start the dev server with auto-reload on :8000
uv run fastapi dev main.py
```

Then open `http://127.0.0.1:8000/ui`. The API docs are served at `/docs`.

The SQLite file is created automatically at `data/items.db` on first import;
the schema is created and migrated on startup (see `migrate_schema` in
`main.py`).

## Project layout

| Path                     | Purpose                                                          |
|--------------------------|------------------------------------------------------------------|
| `main.py`                | App entry point: engine, DB, models, migrations, seeding, all routes, CSRF + profiling middleware, `ABILITY_EFFECTS`, Pydantic schemas |
| `ability.py`             | Static ability catalog (data only) + category rules               |
| `parts.py`               | Static part/item catalog and generic names (data only)            |
| `abilities/`             | Per-category ability + parameter packs (scan, shape, pulse, ...)  |
| `war_factory.py`         | War-factory automation loop (8 sections: war-log, builder, joiner, props-mutator, test facility, tick orchestration, state/leaderboard, background daemon) |
| `syntax/`                | Synthex DSL — declarative language for defining units, parameters, abilities, and alterations (see `SYNTAX.md`) |
| `templates/`             | Jinja2 page templates                                             |
| `static/css`, `static/js`| Unbundled frontend assets                                         |
| `data/items.db`          | SQLite database (git-ignored)                                     |
| `smoke_test.py`          | End-to-end smoke test (API + UI routes)                           |

### Helper / seed scripts

These run against `data/items.db` directly and are meant to be invoked with
the project interpreter:

| Script                  | What it does                                                   |
|-------------------------|----------------------------------------------------------------|
| `seed_abilities.py`     | Seed the `abilities` table and assign abilities to items       |
| `seed_random_sqlite.py` | Seed random items via raw `sqlite3` (no SQLAlchemy import)     |
| `randomize_items.py`    | Randomize all item properties and parameter boundaries         |
| `random_fill.py`        | Fill ability→param links and realistic item parameter values   |
| `item_params_rand.py`   | Truncate `item_parameters` and repopulate with random values within each parameter's min/max bounds |

```bash
.venv/bin/python seed_abilities.py
.venv/bin/python random_fill.py
```

## Data model

All models are defined in `main.py` on top of a SQLAlchemy `DeclarativeBase`.

- **`items`** — the core entity. Self-referential tree via `parent_id` →
  `subitems` (cascade delete). Carries physical props (`price`, `weight`,
  `hp`, `oil`, flags, `revision`).
- **`abilities`** — verbs applied to items/events, with EN/RU descriptions.
- **`events`** — named events with a `event_per_10msec` rate, linked to
  abilities.
- **`parameters`** — physical parameter definitions (unit, min/max bounds).
- **`item_parameters`** — per-item parameter values with min/max envelope,
  unit override, source and confidence.
- **`ability_to_params`** — how an ability modifies a parameter
  (`operation`, `curve`, `stack_mode`, `priority`, coefficient).
- **`ability_category`** — single-word category links for abilities.

Many-to-many junction tables connect `abilities` ↔ `items` and
`abilities` ↔ `events`.

- **`war_log`** — runtime table created by `war_factory.py`; one row per
  tick stage (`build`, `join`, `mutate`, `test`) with JSON `detail`.

## API

### Items (JSON)

| Method   | Path                                            |
|----------|-------------------------------------------------|
| `GET`    | `/items` (filter/sort/paginate)                 |
| `GET`    | `/items/{item_id}`                              |
| `POST`   | `/items`                                        |
| `PUT`    | `/items/{item_id}`                              |
| `PATCH`  | `/items/{item_id}`                              |
| `DELETE` | `/items/{item_id}`                              |
| `GET`    | `/items/{item_id}/subitems`                     |
| `GET`    | `/items/{item_id}/subitems/{subitem_id}`        |
| `POST`   | `/items/{item_id}/subitems`                     |
| `PUT/PATCH/DELETE` | `/items/{item_id}/subitems/{subitem_id}` |

### Catalog / simulation

- `/api/abilities` (GET), `/api/abilities/{ability_id}` (PUT)
- `/api/parameters` (GET)
- `/api/ability-params` (GET/POST), `/api/ability-params/{ap_id}` (PUT/DELETE)
- `/api/events` (GET/POST), `/api/events/{event_id}` (PUT/DELETE)
- `/api/units`, `/api/units/{item_id}`
- `/war/factory/state`, `/war/factory/tick`, `/war/factory/run`,
  `/war/factory/test`, `/war/factory/auto/{start,stop,status}`

### HUD pages

`/` redirects to `/ui/combat-duel`. HUD routes:

| Method | Path                                                |
|--------|-----------------------------------------------------|
| `GET`  | `/ui` (index dashboard with filtered item list)      |
| `GET`  | `/ui/warehouse`                                      |
| `POST` | `/ui/warehouse/mutate`                               |
| `GET`  | `/ui/items/new`                                      |
| `GET`  | `/ui/items/{item_id}`                                |
| `GET`  | `/ui/items/{item_id}/edit`                           |
| `POST` | `/ui/items`                                          |
| `POST` | `/ui/items/{item_id}`                                |
| `POST` | `/ui/items/{item_id}/delete`                         |
| `GET`  | `/ui/items/{item_id}/subitems/{subitem_id}`          |
| `POST` | `/ui/items/{item_id}/subitems`                       |
| `POST` | `/ui/items/{item_id}/subitems/{subitem_id}/delete`   |
| `POST` | `/ui/items/{item_id}/subitems/{subitem_id}/abilities`|
| `GET`  | `/ui/abilities`                                      |
| `GET`  | `/ui/events`                                         |
| `GET`  | `/ui/test-facility`                                  |
| `GET`  | `/ui/combat-duel`                                    |
| `GET`  | `/ui/war-factory`                                    |
| `GET`  | `/ui/filters/options`                                |

Forms are CSRF-protected: the middleware in `main.py` checks a daily
rotating cookie (`cokgi_<crc32(day+year)>`); templates emit the token via the
`csrf_token` global.

## Versioning

`APP_VERSION` is defined near the top of `main.py` as
`str(Version("1.37.7").bump())` → currently **`1.37.8`**. It is passed to
`FastAPI(version=...)` and rendered in the app-bar header
(`v{{ app_version }}`). The `Version` class supports suffix bumping
(e.g. `beta` → `beta2`); see `Version.bump()` in `main.py`.

Per project convention, bump it whenever project code changes.

## Static assets (CSS / JS)

All CSS and JS source files live in `static/css/` and `static/js/` respectively.
There is **no build step or bundler** — each file is served verbatim and
included directly in the templates. The base template loads the shared
files (always needed on every page) and each page-specific template adds its
own files via Jinja2 `{% block styles %}` / `{% block scripts %}` blocks so
only the CSS/JS a page actually uses is fetched.

### Always-loaded (via `base.html`)

| Asset          | Purpose                                  |
|----------------|------------------------------------------|
| `css/base.css`   | Global palette, layout, HUD styling      |
| `css/nav_overlay.css` | Nav overlay tile / crumble effects  |
| `js/base.js`     | Canvas animations (NATO, hero digits, lasers) |
| `js/nav_overlay.js` | Nav overlay tile generation            |
| `js/profile.js`  | Server-side profiling readout overlay     |

### Page-specific includes

| Page template           | CSS                    | JS                       |
|-------------------------|------------------------|--------------------------|
| `templates/index.html`  | `index.css`            | `index.js`               |
| `templates/abilities.html` | `abilities.css`     | `abilities.js`           |
| `templates/combat_duel.html` | `combat_duel.css` | `combat_duel.js`         |
| `templates/events.html` | `events.css`           | `events.js`              |
| `templates/item_form.html` | `item_form.css`     | `item_form.js`           |
| `templates/subitem_detail.html` | —              | `subitem_detail.js`      |
| `templates/test_facility.html` | `test_facility.css` | `test_facility.js`    |
| `templates/warehouse.html` | `warehouse.css`      | `warehouse.js`           |
| `templates/war_factory.html` | `war_factory.css`  | `war_factory.js`         |
| `templates/item_detail.html` | —              | —                        |
