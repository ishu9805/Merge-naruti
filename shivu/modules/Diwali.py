# modules/user/events/diwali_premium_bonus.py
from datetime import datetime, timedelta
import random
from pyrogram import Client, filters
from shivu import shivuups as app
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from core.database import db

DIWALI_START = datetime(2025, 10, 17)  # Adjust for your Diwali dates
DIWALI_END = datetime(2025, 10, 23)


DIWALI_PREMIUM_BONUS = {
    "rewards": [
        # Coin Rewards (70% chance total)
        {"type": "coins", "amount": 2000, "name": "💰 Small Diwali Treasure", "chance": 0.25},
        {"type": "coins", "amount": 5000, "name": "💰 Medium Diwali Fortune", "chance": 0.20},
        {"type": "coins", "amount": 8000, "name": "💰 Large Diwali Wealth", "chance": 0.15},
        {"type": "coins", "amount": 10000, "name": "💰 Grand Diwali Jackpot", "chance": 0.10},
        
        # Character Rewards (30% chance total)
        {"type": "character", "rarity": "💮 Special Edition", "name": "🎴 Special Edition Character", "chance": 0.15},
        {"type": "character", "rarity": "🔮 Limited Edition", "name": "💎 Limited Edition Character", "chance": 0.10},
        #{"type": "character", "rarity": "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣", "name": "🎬 AMV Edition Character", "chance": 0.05}
    ],
    "daily_limit": 1,
    "event_duration": 5  # Diwali festival days
}

@app.on_message(filters.command("bonus"))
async def diwali_premium_bonus(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if Diwali event is active
    if not DIWALI_START <= datetime.now() <= DIWALI_END:
        await message.reply_text(
            "🎇 **Diwali Event Has Ended!**\n\n"
            "The festival of lights has concluded. Stay tuned for the next festival event! 🪔"
        )
        return
    
    # Check daily limit
    today = datetime.now().date()
    user_data = await db.users.find_one({"id": user_id})
    
    if user_data and user_data.get('last_diwali_bonus_date') == today:
        await message.reply_text(
            "🪔 **Daily Bonus Already Claimed!**\n\n"
            "You have already claimed your Diwali bonus today.\n"
            "Come back tomorrow for another chance at festival rewards! 🌟"
        )
        return
    
    # Select random reward
    reward = select_diwali_reward()
    
    # Give reward to user
    await grant_diwali_reward(user_id, reward)
    
    # Update user's last claim date
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"last_diwali_bonus_date": today}}
    )
    
    # Send reward message
    await send_reward_message(client, message, reward)

def select_diwali_reward():
    """Select a random Diwali reward based on chances"""
    rewards = DIWALI_PREMIUM_BONUS["rewards"]
    weights = [reward["chance"] for reward in rewards]
    return random.choices(rewards, weights=weights)[0]

async def grant_diwali_reward(user_id, reward):
    """Grant the selected reward to user"""
    if reward["type"] == "coins":
        await db.users.update_one(
            {"id": user_id},
            {"$inc": {"coins": reward["amount"]}},
            upsert=True
        )
    
    elif reward["type"] == "character":
        # Find a character of the specified rarity that user doesn't own
        character = await get_available_character(user_id, reward["rarity"])
        if character:
            await db.users.update_one(
                {"id": user_id},
                {"$push": {"characters": character}},
                upsert=True
            )
            reward["character_data"] = character
        else:
            # Fallback to coins if no character available
            fallback_coins = 5000
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"coins": fallback_coins}}
            )
            reward["type"] = "coins"
            reward["amount"] = fallback_coins
            reward["name"] = "💰 Fallback Diwali Reward"

async def get_available_character(user_id, rarity):
    """Get a random character of specified rarity that user doesn't own"""
    user_data = await db.users.find_one({"id": user_id})
    owned_character_ids = {char["id"] for char in user_data.get("characters", [])}
    
    # Find characters of specified rarity that user doesn't own
    available_chars = await db.characters.find({
        "rarity": rarity,
        "id": {"$nin": list(owned_character_ids)}
    }).to_list(length=None)
    
    if available_chars:
        return random.choice(available_chars)
    return None

async def send_reward_message(client, message, reward):
    """Send beautiful reward announcement"""
    user_mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
    
    if reward["type"] == "coins":
        caption = (
            f"🎇 **Diwali Bonus Claimed!** 🪔\n\n"
            f"**Winner:** {user_mention}\n"
            f"**Prize:** {reward['name']}\n"
            f"**Amount:** {reward['amount']} coins 💰\n\n"
            f"🌟 *May this Diwali bring immense prosperity to your collection!* 🌟\n"
            f"🪔 *Happy Diwali!* 🪔"
        )
        PHOTO = ["https://files.catbox.moe/a60vfa.jpg", "https://files.catbox.moe/n045ua.jpg", "https://files.catbox.moe/4q0r0j.jpg"]
        # Send with festive photo
        await message.reply_photo(
            photo= random.choice(PHOTO)  # Add festive image
            caption=caption
        )
        
        # Additional celebration message
        await message.reply_text(
            f"🎉 **CONGRATULATIONS!** 🎉\n\n"
            f"You won **{reward['amount']} coins** in the Diwali festival!\n"
            f"Your new balance is shining bright! ✨"
        )
    
    elif reward["type"] == "character" and "character_data" in reward:
        character = reward["character_data"]
        
        caption = (
            f"🎇 **Diwali Character Unlocked!** 🪔\n\n"
            f"**Winner:** {user_mention}\n"
            f"**Prize:** {reward['name']}\n"
            f"**Character:** {character['name']}\n"
            f"**Rarity:** {character['rarity']}\n"
            f"**Anime:** {character['anime']}\n\n"
            f"🌟 *A special festival character joins your collection!* 🌟\n"
            f"🪔 *Happy Diwali!* 🪔"
        )
        
        # Send character with festive message
        if character.get('img_url'):
            await message.reply_photo(
                photo=character['img_url'],
                caption=caption
            )
        elif character.get('vid_url'):
            await message.reply_video(
                video=character['vid_url'],
                caption=caption,
                supports_streaming=True
            )
        
        # Celebration message
        await message.reply_text(
            f"🎊 **FESTIVAL BLESSING!** 🎊\n\n"
            f"✨ **{character['name']}** has joined your collection!\n"
            f"🎴 Rarity: {character['rarity']}\n"
            f"📺 From: {character['anime']}\n\n"
            f"What a wonderful Diwali gift! 🪔"
      )
