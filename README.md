# Jesus Christ Nuclear Revenge D-Days Panel

FastAPI CRUD application for managing "units" (items) with abilities, subitems,
events, and a war-factory simulation.  Styled as a Command & Conquer military
HUD.

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
| `templates/item_detail.html` | —                  | —                        |
