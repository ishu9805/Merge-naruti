import random
from datetime import datetime, timezone
from typing import Optional

from shivu import collectionps as collection, dbps as db, user_collectionps as user_collection

from .constants import (
    CHALLENGE_REWARD,
    GIVEAWAY_REWARD,
    HOLI_EVENT_DAYS,
    HOLI_EVENT_START,
    PUBLIC_GAME_REWARD,
)

holi_collection = db["holi_event_2026"]
holi_limits_collection = db["holi_event_2026_limits"]


def get_current_event_day() -> tuple[int, dict]:
    start = datetime.strptime(HOLI_EVENT_START, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    day_num = (now.date() - start.date()).days + 1

    if day_num < 1:
        day_num = 1
    if day_num > 4:
        day_num = 4

    day_info = HOLI_EVENT_DAYS.get(day_num, HOLI_EVENT_DAYS[1])
    return day_num, day_info


async def ensure_user(user_id: int, first_name: str) -> dict:
    user = await user_collection.find_one({"id": user_id})
    if user:
        return user

    user = {
        "id": user_id,
        "first_name": first_name,
        "coins": 0,
        "characters": [],
        "holi": {
            "coins_won": 0,
            "games_played": 0,
            "challenges_done": 0,
            "event_day_last_played": None,
        },
    }
    await user_collection.insert_one(user)
    return user


async def add_coins(user_id: int, amount: int) -> None:
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {
                "coins": amount,
                "holi.coins_won": amount,
            }
        },
        upsert=True,
    )


async def reward_random_character(user_id: int) -> Optional[dict]:
    total = await collection.count_documents({})
    if total == 0:
        return None

    index = random.randint(0, total - 1)
    cursor = collection.find({}).skip(index).limit(1)
    picked = await cursor.to_list(length=1)
    if not picked:
        return None

    character = picked[0]
    await user_collection.update_one({"id": user_id}, {"$push": {"characters": character}})
    return character


async def create_giveaway(host_id: int, host_name: str) -> dict:
    day_num, _ = get_current_event_day()
    giveaway = {
        "type": "holi_giveaway",
        "host_id": host_id,
        "host_name": host_name,
        "participants": [],
        "reward": GIVEAWAY_REWARD,
        "event_day": day_num,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    await holi_collection.update_one({"type": "holi_giveaway"}, {"$set": giveaway}, upsert=True)
    return giveaway


async def join_giveaway(user_id: int) -> tuple[bool, int]:
    giveaway = await holi_collection.find_one({"type": "holi_giveaway", "is_active": True})
    if not giveaway:
        return False, 0

    participants = giveaway.get("participants", [])
    if user_id in participants:
        return True, len(participants)

    participants.append(user_id)
    await holi_collection.update_one(
        {"type": "holi_giveaway", "is_active": True},
        {"$set": {"participants": participants}},
    )
    return False, len(participants)


async def close_giveaway_and_pick_winner() -> Optional[dict]:
    giveaway = await holi_collection.find_one({"type": "holi_giveaway", "is_active": True})
    if not giveaway:
        return None

    participants = giveaway.get("participants", [])
    if not participants:
        await holi_collection.update_one(
            {"_id": giveaway["_id"]}, {"$set": {"is_active": False, "winner_id": None}}
        )
        return {"participants": 0, "winner_id": None}

    winner_id = random.choice(participants)
    await add_coins(winner_id, GIVEAWAY_REWARD["coins"])
    won_character = await reward_random_character(winner_id)

    await holi_collection.update_one(
        {"_id": giveaway["_id"]},
        {
            "$set": {
                "is_active": False,
                "winner_id": winner_id,
                "winner_character": won_character,
            }
        },
    )

    return {
        "participants": len(participants),
        "winner_id": winner_id,
        "winner_character": won_character,
    }


async def mark_challenge_done(user_id: int) -> int:
    day_num, day_info = get_current_event_day()
    reward = day_info.get("reward", CHALLENGE_REWARD["coins"])
    await add_coins(user_id, reward)
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"holi.challenges_done": 1},
            "$set": {"holi.event_day_last_played": day_num},
        },
        upsert=True,
    )
    return reward


async def mark_public_game_win(user_id: int) -> int:
    day_num, _ = get_current_event_day()
    reward = PUBLIC_GAME_REWARD["coins"] + (day_num * 15)
    await add_coins(user_id, reward)
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"holi.games_played": 1},
            "$set": {"holi.event_day_last_played": day_num},
        },
        upsert=True,
    )
    return reward


async def mark_riddle_win(user_id: int) -> int:
    day_num, _ = get_current_event_day()
    reward = 100 + (day_num * 20)
    await add_coins(user_id, reward)
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"holi.games_played": 1},
            "$set": {"holi.event_day_last_played": day_num},
        },
        upsert=True,
    )
    return reward


async def mark_spin_reward(user_id: int) -> int:
    day_num, _ = get_current_event_day()
    reward = random.randint(100, 250) + (day_num * 25)
    await add_coins(user_id, reward)
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"holi.games_played": 1},
            "$set": {"holi.event_day_last_played": day_num},
        },
        upsert=True,
    )
    return reward


async def get_event_summary() -> dict:
    day_num, day_info = get_current_event_day()
    active = await holi_collection.find_one({"type": "holi_giveaway", "is_active": True})
    last = await holi_collection.find_one(
        {"type": "holi_giveaway", "is_active": False}, sort=[("created_at", -1)]
    )

    return {
        "active_giveaway": active,
        "last_giveaway": last,
        "event_day": day_num,
        "day_info": day_info,
        "challenge_reward": day_info.get("reward", CHALLENGE_REWARD["coins"]),
        "public_game_reward": PUBLIC_GAME_REWARD["coins"] + (day_num * 15),
    }


async def check_and_consume_daily_limit(user_id: int, action: str, max_uses: int) -> tuple[bool, int]:
    today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    query = {"user_id": user_id, "action": action, "date": today_key}
    limit_doc = await holi_limits_collection.find_one(query)

    if not limit_doc:
        await holi_limits_collection.insert_one(
            {
                "user_id": user_id,
                "action": action,
                "date": today_key,
                "count": 1,
                "created_at": datetime.utcnow(),
            }
        )
        return True, max_uses - 1

    used = limit_doc.get("count", 0)
    if used >= max_uses:
        return False, 0

    new_used = used + 1
    await holi_limits_collection.update_one(query, {"$set": {"count": new_used}})
    return True, max_uses - new_used
