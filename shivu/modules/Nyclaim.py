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

# Lock dictionary to track command processing
claim_locks = {}

@bot.on_message(filters.command(["nyclaim"]))
async def new_year_claim(_, message: t.Message):
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
        if not await is_member(user_id):
            group_link = "https://t.me/blade_x_community"  # Replace with the actual group invite link
            message_text = (
                "🎊 To join the New Year's festivities and claim rewards, you must be part of our exclusive group!\n"
                "🎆 Click below to join and start celebrating with us. 🎇"
            )
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("💫 Join the Party 💫", url=group_link)]]
            )
            await bot.send_message(chat_id=message.chat.id, text=message_text, reply_markup=reply_markup)
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
            claim_lock.pop(user_id, None)
            return

        # Check if the user has 15 or more characters
        if len(user_data.get('characters', [])) < 15:
            await bot.send_message(
                chat_id=message.chat.id,
                text=(
                    "🎭 Sorry, you cant do that, 🎆\n"
      
                )
            )
            claim_locks.pop(user_id, None)
            return

        # Fetch unique characters only from the specified IDs
        target_ids = [6413, 6414, 6415, 6416]
        unique_characters = await collection.find(
            {'id': {'$in': target_ids}}
        ).to_list(length=1)  # Fetch one random character

        if not unique_characters:
            return await bot.send_message(
                chat_id=message.chat.id,
                text="🚫 No characters available for the New Year claim. But the fireworks are still amazing! 🎆"
            )

        # Add characters to the user's collection and set `has_claimed_new_year` to True
        await user_collection.update_one(
            {'id': user_id},
            {
                '$push': {'characters': {'$each': unique_characters}},
                '$set': {'has_claimed_new_year': True}
            }
        )

        # Celebrate the claim
        for character in unique_characters:
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
    finally:
        claim_locks.pop(user_id, None)  # Release the lock
