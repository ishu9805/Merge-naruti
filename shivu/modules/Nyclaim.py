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
import random
from datetime import datetime
from pyrogram import filters
from shivu import shivuu as bot, user_collection, collection, ban_collection

# List of character IDs for the New Year claim
new_year_ids = [6413, 6414, 6415, 6416]

# Lock dictionary to track command processing
claim_locks = {}

async def is_member(user_id):
    """Check if a user is part of the required group."""
    try:
        member = await bot.get_chat_member(required_group_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False


@bot.on_message(filters.command(["nyclaim"]))
async def new_year_claim(_, message):
    user_id = message.from_user.id
    mention = message.from_user.mention
    current_time = datetime.utcnow()

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
        """ if not await is_member(user_id):
            group_link = "https://t.me/blade_x_community"  # Replace with the actual group invite link
            message_text = (
                "🎊 To join the New Year's festivities and claim rewards, you must be part of our exclusive group!\n"
                "🎆 Click below to join and start celebrating with us. 🎇"
            )
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("💫 Join the Party 💫", url=group_link)]]
            )
            await bot.send_message(chat_id=message.chat.id, text=message_text, reply_markup=reply_markup)
            return"""

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
            claim_locks.pop(user_id, None)
            return

        # Check if the user has 15 or more characters
        if len(user_data.get('characters', [])) < 15:
            await bot.send_message(
                chat_id=message.chat.id,
                text=(
                    "🎭 Sorry, you can't claim this New Year reward as you don't have enough characters. "
                    "You need at least 15 characters in your collection. 🎆"
                )
            )
            claim_locks.pop(user_id, None)
            return

        # Fetch unique characters only from the specified IDs
        random_id = random.choice(new_year_ids)
        character = await collection.find_one({"id": random_id})
        if not character:
            await message.reply_text("⚠️ Unable to fetch the character details. Please try again later.")
            return

        # Add characters to the user's collection and set `has_claimed_new_year` to True
        await user_collection.update_one(
            {"id": user_id},
            {
                "$push": {"characters": character},
                "$set": {"has_claimed_new_year": True}
            }
        )

        # Celebrate the claim and send character details
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
        print(f"Error during claim: {e}")
    finally:
        claim_locks.pop(user_id, None)  # Release the lock
        
# List of character IDs for the New Year claim
