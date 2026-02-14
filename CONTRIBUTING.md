# Contributing Guide

Thanks for improving NarutoBot.

## Local setup

1. Create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure values in `moto/Config.py` (or migrate to env vars).
4. Run the bot:
   ```bash
   python -m shivu
   ```

## Development rules

- Put new command/features into `shivu/modules/`.
- Put reusable helpers into `shivu/utils/`.
- Keep README and docs updated when changing structure.
- Prefer small, focused pull requests.

## Basic validation

Run a compile check before pushing:

```bash
python -m compileall shivu moto resolve_peer.py
```
