# Project conventions

- **Version bump:** every time you change application code, bump `APP_VERSION` in
  `main.py` before finishing. The version is shown in the app-bar header
  (`v{{ app_version }}`) and used to cache-bust static assets, so it must stay
  current to avoid stale JS/CSS in browsers.
- do not use underscores in functions prefixes/postfixes
