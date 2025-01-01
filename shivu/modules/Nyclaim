import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot, user_collection, collection, ban_collection, PARTNER, required_group_id 
from shivu import LOGGER, application
# Constants
DEVS = (7378476666)
CHAT_ID = "-1002338924488"
JOIN_URL = "https://t.me/naruto_support_chat"
CHARACTERS_PER_PAGE = 10

import random
from datetime import datetime

# List of character IDs for the New Year claim
new_year_ids = [6413, 6414, 6415, 6416, 6417, 6418, 6419, 6420, 6421, 6422, 6423, 6424, 6426]

# Lock dictionary to track command processing
claim_locks = {}

async def is_member(user_id):
    """Check if a user is part of the required group."""
    try:
        member = await application.bot.get_chat_member(required_group_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False


@bot.on_message(filters.command(["nyclaim"]))
async def new_year_claim(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    if user_id in claim_locks:
        await bot.send_message(
            chat_id=message.chat.id,
            text="🎆 Your New Year claim request is being processed. Please wait! 🎉",
        )
        return

    claim_locks[user_id] = True  # Set the lock

    try:
        # Check if the user is banned
        is_banned = await ban_collection.find_one({"user_id": user_id})
        if is_banned:
            claim_locks.pop(user_id, None)
            return

        # Membership check
        if not await is_member(user_id):
            group_link = "https://t.me/blade_x_community"
            message_text = (
                "🎊 To join the New Year's festivities and claim rewards, you must be part of our exclusive group!\n"
                "🎆 Click below to join and start celebrating with us. 🎇"
            )
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("💫 Join the Party 💫", url=group_link)]]
            )
            await bot.send_message(chat_id=message.chat.id, text=message_text, reply_markup=reply_markup)
            claim_locks.pop(user_id, None)  # Release the lock
            return

        # Fetch user data
        user_data = await user_collection.find_one({'id': user_id}) or {
            'id': user_id,
            'username': message.from_user.username,
            'characters': [],
            'has_claimed_new_year': False
        }

        # Check if the user has already claimed the New Year reward
        if user_data.get('has_claimed_new_year', False):
            await bot.send_message(
                chat_id=message.chat.id,
                text=(
                    "🎭 You have already claimed your special New Year reward! 🎆\n"
                    "🔍 Stay tuned for more surprises ahead!"
                )
            )
            claim_locks.pop(user_id, None)  # Release the lock
            return

        # Check if the user has 15 or more characters
        if len(user_data.get('characters', [])) < 15:
            await bot.send_message(
                chat_id=message.chat.id,
                text="🎭 Sorry, you can't claim the reward. 🎆"
            )
            claim_locks.pop(user_id, None)  # Release the lock
            return

        # Fetch a random character from the specified IDs
        random_id = str(random.choice(new_year_ids))
        character = await collection.find_one({"id": random_id})
        if not character:
            await message.reply_text("⚠️ Unable to fetch the character details. Please try again later.")
            claim_locks.pop(user_id, None)  # Release the lock
            return

        # Add character to user's collection and update claim status
        await user_collection.update_one(
            {"id": user_id},
            {
                "$push": {"characters": character},
                "$set": {"has_claimed_new_year": True}
            }
        )

        # Send celebration message
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=character['img_url'],
            caption=(
                f"🎉 Happy New Year, {mention}! 🎆\n"
                f"✨ *Name*: {character['name']}\n"
                f"🌟 *Rarity*: {character['rarity']}\n"
                f"🎭 *Anime*: {character['anime']}\n"
                "🍀 *Thank you for celebrating with us!*"
            )
        )

    except Exception as e:
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ An error occurred during your New Year claim. Please try again later."
        )
        print(e)  # Log the error for debugging
    finally:
        claim_locks.pop(user_id, None)  # Release the lock
        
