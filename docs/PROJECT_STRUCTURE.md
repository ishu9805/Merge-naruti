# Project Structure

This repository keeps all runtime code inside the `shivu/` package, while deployment and operational files stay at the root.

## Directory map

- `shivu/`
  - `__init__.py`: application setup, clients, and MongoDB collection bindings.
  - `__main__.py`: runtime entrypoint and message/update handling.
  - `modules/`: compatibility entry modules plus categorized folders:
    - `admin/`, `economy/`, `games/`, `profile/`, `system/`, `utility/`.
  - `utils/`: shared wrappers, sudo utilities, and error helpers.
- `moto/`
  - `Config.py`: bot/config constants.
- `Images/`
  - static project images.
- `docs/`
  - project documentation (this file and any future architecture notes).
- root deployment files
  - `Dockerfile`, `Procfile`, `runtime.txt`, `heroku.yml`, `vercel.json`, `start`.

## Conventions

- Keep **business logic** in the correct category folder under `shivu/modules/`.
- Keep **cross-module helpers** inside `shivu/utils/`.
- Keep **deployment/runtime wiring** in root files and `shivu/__init__.py`.
- Add new docs in `docs/` instead of long notes in random root files.

## Suggested cleanup path (future)

1. Migrate module filenames to consistent snake_case naming.
2. Replace hardcoded credentials in `moto/Config.py` with environment variable lookups.
3. Split the large `shivu/__main__.py` into service-oriented submodules.
