# 🎌 Naruto Waifu Collection Bot

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0-green)](https://pyrogram.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-5.0-green)](https://mongodb.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A feature-rich Telegram bot for collecting and trading anime characters with economy, social features, mini-games, and admin controls.

## ✨ Features

- 🎮 Character collection gameplay
- 💰 Economy and shop systems
- 🎁 Trading, gifting, and auction features
- 🏆 Leaderboards and progression stats
- 🎯 Mini-games and event modules
- 🔧 Moderation/admin utilities

## 🧱 Repository structure

```text
narutobot/
├── shivu/                  # Main application package
│   ├── __init__.py         # App + DB initialization
│   ├── __main__.py         # Runtime entrypoint
│   ├── modules/            # Module entry points + categorized packages
│   │   ├── admin/          # Admin/moderation commands
│   │   ├── economy/        # Coins, giveaway, trade, auction
│   │   ├── games/          # Puzzle/scramble/scrab modules
│   │   ├── profile/        # User/profile/social modules
│   │   ├── system/         # Core bot callbacks/locks/watchers
│   │   └── utility/        # Upload, convert, checks, misc helpers
│   └── utils/              # Shared helpers
├── moto/Config.py          # Bot configuration values
├── docs/                   # Project docs
├── Dockerfile              # Container runtime
├── Procfile                # Process definition
├── requirements.txt        # Python dependencies
└── Makefile                # Common local commands
```

For more details, see [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md).

## 🚀 Quick start

### Prerequisites

- Python 3.8+
- MongoDB
- Telegram bot credentials

### Installation

```bash
git clone https://github.com/ishu9805/narutobot.git
cd narutobot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Update values in `moto/Config.py` for your environment.

### Run

```bash
python -m shivu
```

Or use Makefile shortcuts:

```bash
make install
make check
make run
```

## 🤝 Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development workflow and checks.

## 📄 License

MIT License. See [`LICENSE`](LICENSE).
