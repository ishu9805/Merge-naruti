
import urllib.request
import uuid
import requests
import random
import html
import logging
from pymongo import ReturnDocument
from typing import List
from bson import ObjectId
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from datetime import datetime, timedelta
from shivu import ban_collection

# Assuming these are defined elsewhere in your code
from shivu import db, UPDATE_CHAT, SUPPORT_CHAT, CHARA_CHANNEL_ID, collection, user_collection, required_group_id
from shivu import (application, PHOTO_URL, OWNER_ID,
                    user_collection, top_global_groups_collection, top_global_groups_collection, 
                    group_user_totals_collection)

from shivu import PARTNER
from .block import block_dec, temp_block
from .lock import command_lock
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)


OWNER_ID = "5856750053"


from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from pymongo import MongoClient
import logging

# MongoDB setup

async def is_member(user_id):
    """Check if a user is part of the required group."""
    try:
        member = await application.bot.get_chat_member(required_group_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

@app.on_message(filters.command("balance"))
@block_dec
@command_lock
async def check_balance(client: Client, message: Message):
    user_id = message.from_user.id
    await asyncio.sleep(0)

    # Check if the user is banned
    if temp_block(user_id):
        return

    user = await user_collection.find_one({"id": user_id})
    if user:
        coins = user.get("coins", 0)
        tokens = user.get("tokens", 0)
        await message.reply_text(f"**Behold, Your Current Balance Shines** ➻💸 {coins} Coins And ➻⚡ {tokens} Tokens.")
    else:
        await message.reply_text("You Don't Have Any Coins Yet.")




async def add_coins(user_id: int, amount: int) -> None:
    try:
        if amount <= 0:
            LOGGER.warning("Attempted to add non-positive amount of coins.")
            return
        
        user = await user_collection.find_one({"id": user_id})

        if user:
            current_coins = user.get("coins", 0)
            await user_collection.update_one(
                {"id": user_id},
                {"$set": {"coins": current_coins + amount}},
            )
        else:
            await user_collection.insert_one({"id": user_id, "coins": amount})
    except Exception as e:
        LOGGER.error(f"Error adding coins: {e}")
      




@app.on_message(filters.command("daily"))
@block_dec
@command_lock
async def daily_reward(client: Client, message: Message):
    user_id = message.from_user.id
    await asyncio.sleep(0)
    if temp_block(user_id):
        return

    user = await user_collection.find_one({"id": user_id})
    if user:
        last_claimed = user.get("last_daily_claimed")
        if last_claimed and last_claimed.date() == datetime.now().date():
            await message.reply_text("You Have Already Claimed Your Daily Reward.")
            return

        await add_coins(user_id, 40)
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"last_daily_claimed": datetime.now()}},
        )
        await message.reply_text("You Have Claimed Your Daily Reward. You Earned 40 Coins.")
    else:
        await user_collection.insert_one({"id": user_id, "coins": 40, "last_daily_claimed": datetime.now()})
        await message.reply_text("You Have Claimed Your Daily Reward. You Earned 40 Coins.")
 

@app.on_message(filters.command("weekly"))
@block_dec
@command_lock
async def weekly_reward(client: Client, message: Message):
    user_id = message.from_user.id
    await asyncio.sleep(0)
    # Check if the user is banned
    if temp_block(user_id):
        return
      
    user = await user_collection.find_one({"id": user_id})
    if user:
        last_claimed = user.get("last_weekly_claimed")
        start_of_week = datetime.now().date() - timedelta(days=datetime.now().weekday())
        if last_claimed and last_claimed.date() >= start_of_week:
            await message.reply_text("You Have Already Claimed Your Weekly Reward.")
            return

        await add_coins(user_id, 500)
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"last_weekly_claimed": datetime.now()}},
        )
        await message.reply_text("You Have Claimed Your Weekly Reward. You Earned 250 Coins.")
    else:
        await user_collection.insert_one({"id": user_id, "coins": 250, "last_weekly_claimed": datetime.now()})
        await message.reply_text("You Have Claimed Your Weekly Reward. You Earned 250 Coins.")




@app.on_message(filters.command("pay"))
@block_dec
@command_lock
async def pay_coins(client: Client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    # Check if the user is banned
    
    args = message.text.split()
    if len(args) != 2:
        await message.reply_text("Invalid format. Use: /pay <amount>")
        return

    try:
        amount = int(args[1])
        if amount <= 0:
            await message.reply_text("Amount must be a positive number.")
            return
    except ValueError:
        await message.reply_text("Invalid amount. Please provide a valid number.")
        return

    if not message.reply_to_message:
        await message.reply_text("Please reply to the message of the user you want to pay.")
        return

    recipient_id = message.reply_to_message.from_user.id
    if user_id == recipient_id:
        await message.reply_text("You cannot pay yourself.")
        return

    sender_wallet = await user_collection.find_one({"id": user_id})
    if not sender_wallet:
        await message.reply_text("Sender's wallet not found.")
        return

    sender_balance = sender_wallet.get("coins", 0)
    if sender_balance < amount:
        await message.reply_text("Insufficient balance to make the payment.")
        return

    recipient_wallet = await user_collection.find_one({"id": recipient_id})
    if not recipient_wallet:
        await message.reply_text("Recipient's wallet not found.")
        return

    new_sender_balance = sender_balance - amount
    await user_collection.update_one({"id": user_id}, {"$set": {"coins": new_sender_balance}})

    recipient_balance = recipient_wallet.get("coins", 0)
    new_recipient_balance = recipient_balance + amount
    await user_collection.update_one({"id": recipient_id}, {"$set": {"coins": new_recipient_balance}})

    await message.reply_text(f"Successfully transferred {amount} coins to user {recipient_id}.")


@app.on_message(filters.command("bonus"))
@block_dec
@command_lock
async def bonus_coins(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if the user is banned
    if temp_block(user_id):
        return

    # Check if the user is a member of the required group
    try:
        member = await client.get_chat_member("YOUR_GROUP_ID", user_id)
        if member.status not in ["member", "administrator", "creator"]:
            await message.reply_text("You need to join our group to claim bonus coins.")
            return
    except Exception:
        await message.reply_text("Error checking group membership.")
        return

    user = await user_collection.find_one({"id": user_id})
    if user:
        last_claimed = user.get("last_bonus_claimed")
        if last_claimed and last_claimed.date() == datetime.now().date():
            await message.reply_text("You have already claimed your bonus coins today.")
            return

        await add_coins(user_id, 100)
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"last_bonus_claimed": datetime.now()}},
        )
        await message.reply_text("You have claimed your daily bonus coins. You earned 100 coins!")
    else:
        await user_collection.insert_one({"id": user_id, "coins": 100, "last_bonus_claimed": datetime.now()})
        await message.reply_text("You have claimed your daily bonus coins. You earned 100 coins!")

            



import asyncio
import random
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from datetime import datetime, timedelta

# Assuming these are defined elsewhere in your code
from shivu import application, PHOTO_URL, user_collection

# Global Variables
global_coin_leaderboard = []
global_token_leaderboard = []
last_updated = datetime.min

async def update_leaderboards():
    global global_coin_leaderboard, global_token_leaderboard, last_updated

    # Fetch the top 10 users by coins
    coin_cursor = user_collection.aggregate([
        {"$project": {"id": 1, "coins": 1}},
        {"$sort": {"coins": -1}},
        {"$limit": 10}
    ])
    global_coin_leaderboard = await coin_cursor.to_list(length=10)

    # Fetch the top 10 users by tokens
    token_cursor = user_collection.aggregate([
        {"$project": {"id": 1, "tokens": 1}},
        {"$sort": {"tokens": -1}},
        {"$limit": 10}
    ])
    global_token_leaderboard = await token_cursor.to_list(length=10)

    last_updated = datetime.now()

async def top_users_by_coins(update: Update, context: CallbackContext) -> None:

    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass


    if datetime.now() - last_updated > timedelta(hours=4):
        await update_leaderboards()

    leaderboard_message = "<b>Dɪsᴄᴏᴠᴇʀ Tʜᴇ Eʟɪᴛᴇ Tᴏᴘ 𝟷𝟶 Usᴇʀs Rᴇᴡᴀʀᴅᴇᴅ Wɪᴛʜ Tʜᴇ Mᴏsᴛ Cᴏɪɴs:-</b>\n\n"
    for i, user_data in enumerate(global_coin_leaderboard, start=1):
        user_id = user_data.get('id', 'Unknown')
        coins = user_data.get('coins', 0)
        try:
            user = await context.bot.get_chat(user_id)
            username = user.username if user.username else user.first_name
            display_name = user.title if user.title else user.first_name
            leaderboard_message += f"{i}. <a href=\"https://t.me/{username}\">{display_name}</a>,\nBᴀʟᴀɴᴄᴇ➻💸{coins} coins.\n\n"
        except Exception as e:
            continue

    photo_url = random.choice(PHOTO_URL)
    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')

async def top_users_by_tokens(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass


    if datetime.now() - last_updated > timedelta(hours=4):
        await update_leaderboards()

    leaderboard_message = "<b>Dɪsᴄᴏᴠᴇʀ Tʜᴇ Eʟɪᴛᴇ Tᴏᴘ 𝟷𝟶 Usᴇʀs Rᴇᴡᴀʀᴅᴇᴅ Wɪᴛʜ Tʜᴇ Mᴏsᴛ Tokens:-</b>\n\n"
    for i, user_data in enumerate(global_token_leaderboard, start=1):
        user_id = user_data.get('id', 'Unknown')
        tokens = user_data.get('tokens', 0)
        try:
            user = await context.bot.get_chat(user_id)
            username = user.username if user.username else user.first_name
            display_name = user.title if user.title else user.first_name
            leaderboard_message += f"{i}. <a href=\"https://t.me/{username}\">{display_name}</a>,\nBᴀʟᴀɴᴄᴇ➻☣️{tokens} tokens.\n\n"
        except Exception as e:
            continue

    photo_url = random.choice(PHOTO_URL)
    await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')



# Handlers
TOPS_HANDLER = CommandHandler('cointop', top_users_by_coins)
TTOPS_HANDLER = CommandHandler('tokentop', top_users_by_tokens)

application.add_handler(TOPS_HANDLER)
application.add_handler(TTOPS_HANDLER)


# Handler for the /bonus command
bonus_handler = CommandHandler("bonus", bonus_coins)
application.add_handler(bonus_handler)



"""application.add_handler(CallbackQueryHandler(next_item, pattern="^next$"))
application.add_handler(CallbackQueryHandler(buy_character, pattern=r'^buy_\d+$'))
application.add_handler(CommandHandler(['Shop', 'shopmenu'], show_shop))"""
application.add_handler(CommandHandler('pay', pay_coins))

# Define command handlers
REMOVE_COINS_HANDLER = CommandHandler('removecoins', remove_coins)
GIVE_COINS_HANDLER = CommandHandler('givecoins', give_coins)

# Add handlers to the application
application.add_handler(REMOVE_COINS_HANDLER)
application.add_handler(GIVE_COINS_HANDLER)

# Define command handlers
CHECK_BALANCE_HANDLER = CommandHandler('balance', check_balance)
DAILY_REWARD_HANDLER = CommandHandler('daily', daily_reward)
WEEKLY_REWARD_HANDLER = CommandHandler('weekly', weekly_reward)


# Add handlers to the application
application.add_handler(CHECK_BALANCE_HANDLER)
application.add_handler(DAILY_REWARD_HANDLER)
application.add_handler(WEEKLY_REWARD_HANDLER)

