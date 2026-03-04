HOLI_EVENT_CHAT_ID = -1002783891820
HOLI_EVENT_TITLE = "Holi Mahotsav 2026"

HOLI_EVENT_START = "2026-03-10"
HOLI_EVENT_DAYS = {
    1: {
        "name": "Color Blast Opening",
        "focus": "Mega giveaway + welcome rain of colors",
        "challenge": "Send /holichallenge after spreading colors in chat",
        "reward": 350,
    },
    2: {
        "name": "Coin Rain Day",
        "focus": "Extra coin mini-challenges and speed rounds",
        "challenge": "Use /holichallenge and answer quick tasks",
        "reward": 450,
    },
    3: {
        "name": "Character Carnival",
        "focus": "Character-themed rounds + boosted giveaway reward",
        "challenge": "Finish /holichallenge to get bonus + character chance",
        "reward": 550,
    },
    4: {
        "name": "Grand Finale",
        "focus": "Final showdown, public games and final winner board",
        "challenge": "Play /holiguess and close with /holiend giveaway",
        "reward": 700,
    },
}

GIVEAWAY_REWARD = {
    "coins": 1500,
    "characters": 1,
}

CHALLENGE_REWARD = {
    "coins": 300,
}

PUBLIC_GAME_REWARD = {
    "coins": 120,
}

USAGE_LIMITS = {
    "holichallenge": {"max_uses": 3, "reset": "daily_utc"},
    "holiguess": {"max_uses": 8, "reset": "daily_utc"},
    "holiriddle": {"max_uses": 5, "reset": "daily_utc"},
    "holispin": {"max_uses": 2, "reset": "daily_utc"},
    "holijoin": {"max_uses": 2, "reset": "daily_utc"},
}
