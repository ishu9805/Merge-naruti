# modules/user/events/diwali_premium_bonus.py
from datetime import datetime
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from shivu import shivuups as app
from shivu import collectionps as collection, user_collectionps as user_collection

# Event Duration
DIWALI_START = datetime(2025, 10, 17)
DIWALI_END = datetime(2025, 10, 23)


# gives full datetime with date and time

# Reward pool
DIWALI_PREMIUM_BONUS = {
    "rewards": [
        # Coin Rewards (70%)
        {"type": "coins", "amount": 2000, "name": "💰 Small Diwali Treasure", "chance": 0.25},
        {"type": "coins", "amount": 5000, "name": "💰 Medium Diwali Fortune", "chance": 0.20},
        {"type": "coins", "amount": 8000, "name": "💰 Large Diwali Wealth", "chance": 0.15},
        {"type": "coins", "amount": 10000, "name": "💰 Grand Diwali Jackpot", "chance": 0.10},

        # Character Rewards (30%)
        {"type": "character", "rarity": "💮 Special Edition", "name": "🎴 Special Edition Character", "chance": 0.15},
        {"type": "character", "rarity": "🔮 Limited Edition", "name": "💎 Limited Edition Character", "chance": 0.10}
    ],
    "daily_limit": 1
}


@app.on_message(filters.command("dbonus"))
async def diwali_premium_bonus(client: Client, message: Message):
    user_id = message.from_user.id
    today = datetime.now()  # simplest

    # Check if event is active
    if not (DIWALI_START <= datetime.now() <= DIWALI_END):
        await message.reply_text(
            "🎇 **Diwali Event Has Ended!**\n\n"
            "The festival of lights has concluded. Stay tuned for the next festival event! 🪔"
        )
        return

    # Ensure user exists in DB
    await user_collection.update_one(
        {"id": user_id},
        {"$setOnInsert": {"id": user_id, "coins": 0, "characters": []}},
        upsert=True
    )

    # Check daily bonus
    user_data = await user_collection.find_one({"id": user_id})
    if user_data and user_data.get("last_diwali_bonus_date") == today:
        await message.reply_text(
            "🪔 **Daily Bonus Already Claimed!**\n\n"
            "Come back tomorrow for another Diwali blessing! 🌟"
        )
        return

    # Select reward
    reward = select_diwali_reward()

    # Grant reward
    await grant_diwali_reward(user_id, reward)

    # Update last claim date
    await user_collection.update_one({"id": user_id}, {"$set": {"last_diwali_bonus_date": today}})

    # Send message
    await send_reward_message(client, message, reward)


def select_diwali_reward():
    """Randomly select a Diwali reward based on probability."""
    rewards = DIWALI_PREMIUM_BONUS["rewards"]
    weights = [r["chance"] for r in rewards]
    return random.choices(rewards, weights=weights)[0]


async def grant_diwali_reward(user_id, reward):
    """Grant reward to user and ensure DB consistency."""
    if reward["type"] == "coins":
        await user_collection.update_one(
            {"id": user_id},
            {"$inc": {"coins": reward["amount"]}},
            upsert=True
        )

    elif reward["type"] == "character":
        # Try to get character from DB
        character = await get_available_character(user_id, reward["rarity"])

        if character:
            # Ensure this character exists in main collection
            existing = await collection.find_one({"id": character["id"]})
            if not existing:
                await collection.insert_one(character)

            # Add to user’s collection
            await user_collection.update_one(
                {"id": user_id},
                {"$push": {"characters": character}},
                upsert=True
            )
            reward["character_data"] = character
        else:
            # fallback to coins
            fallback_amount = 5000
            await user_collection.update_one(
                {"id": user_id},
                {"$inc": {"coins": fallback_amount}},
                upsert=True
            )
            reward.update({
                "type": "coins",
                "amount": fallback_amount,
                "name": "💰 Fallback Diwali Reward"
            })


async def get_available_character(user_id, rarity):
    """Fetch a random character of a given rarity that the user doesn't own."""
    user_data = await user_collection.find_one({"id": user_id})
    owned_ids = {c["id"] for c in user_data.get("characters", [])}

    available_chars = await collection.find({
        "rarity": rarity,
        "id": {"$nin": list(owned_ids)}
    }).to_list(length=None)

    if available_chars:
        return random.choice(available_chars)
    return None


async def send_reward_message(client, message, reward):
    """Send a festive Diwali reward message."""
    user_mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

    # --- COINS REWARD ---
    if reward["type"] == "coins":
        caption = (
            f"🎇 **Diwali Bonus Claimed!** 🪔\n\n"
            f"**Winner:** {user_mention}\n"
            f"**Reward:** {reward['name']}\n"
            f"**Amount:** `{reward['amount']}` coins 💰\n\n"
            f"🌟 *May this Diwali bring endless fortune to your collection!* 🌟"
        )
        PHOTOS = [
            "https://files.catbox.moe/a60vfa.jpg",
            "https://files.catbox.moe/n045ua.jpg",
            "https://files.catbox.moe/4q0r0j.jpg"
        ]
        await message.reply_photo(
            photo=random.choice(PHOTOS),
            caption=caption
        )

    # --- CHARACTER REWARD ---
    elif reward["type"] == "character" and "character_data" in reward:
        char = reward["character_data"]
        caption = (
            f"🎇 **Diwali Character Unlocked!** 🪔\n\n"
            f"**Winner:** {user_mention}\n"
            f"**Character:** {char['name']}\n"
            f"**Rarity:** {char['rarity']}\n"
            f"**Anime:** {char['anime']}\n\n"
            f"🌟 *A rare blessing has joined your collection!* 🌟"
        )
        if char.get("img_url"):
            await message.reply_photo(photo=char["img_url"], caption=caption)
        elif char.get("vid_url"):
            await message.reply_video(video=char["vid_url"], caption=caption, supports_streaming=True)
