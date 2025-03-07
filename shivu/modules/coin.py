import asyncio
import urllib.request
import uuid
import requests
import random
import html
from . import app
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

async def is_member(user_id: int) -> bool:
    """Check if a user is part of the required group."""
    try:
        member = await app.get_chat_member(REQUIRED_GROUP_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

async def add_coins(user_id: int, amount: int) -> None:
    """Add coins to a user's balance."""
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
    await asyncio.sleep(0)
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
    await asyncio.sleep(0)

    # Check if the user is banned
    if temp_block(user_id):
        return

    # Check if the user is a member of the required group
    if not is_member(user_id):
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

            
@app.on_message(filters.command("cointop"))
@block_dec
@command_lock
async def top_users_by_coins(client: Client, message: Message):
    try:
        # Fetch top 10 users by coins
        top_users = await user_collection.aggregate([
            {"$project": {"id": 1, "coins": 1, "username": 1}},
            {"$sort": {"coins": -1}},
            {"$limit": 10}
        ]).to_list(length=10)

        if not top_users:
            await message.reply_text("No users found in the leaderboard.")
            return

        # Build the leaderboard message
        leaderboard_message = "<b>Top 10 Users by Coins:</b>\n\n"
        for i, user in enumerate(top_users, start=1):
            user_id = user.get("id")
            coins = user.get("coins", 0)
            username = user.get("username", "Unknown")
            leaderboard_message += f"{i}. <a href='tg://user?id={user_id}'>{username}</a>: {coins} coins\n"

        # Send the leaderboard with a random photo
        photo_url = random.choice(PHOTO_URL)
        await message.reply_video(video=photo_url, caption=leaderboard_message, parse_mode="HTML")

    except Exception as e:
        LOGGER.error(f"Error in /cointop: {e}")
        await message.reply_text("An error occurred while fetching the leaderboard.")


@app.on_message(filters.command("tokentop"))
@block_dec
@command_lock
async def top_users_by_tokens(client: Client, message: Message):
    
      
    try:
        # Fetch top 10 users by tokens
        top_users = await user_collection.aggregate([
            {"$project": {"id": 1, "tokens": 1, "username": 1}},
            {"$sort": {"tokens": -1}},
            {"$limit": 10}
        ]).to_list(length=10)

        if not top_users:
            await message.reply_text("No users found in the leaderboard.")
            return

        # Build the leaderboard message
        leaderboard_message = "<b>Top 10 Users by Tokens:</b>\n\n"
        for i, user in enumerate(top_users, start=1):
            user_id = user.get("id")
            tokens = user.get("tokens", 0)
            username = user.get("username", "Unknown")
            leaderboard_message += f"{i}. <a href='tg://user?id={user_id}'>{username}</a>: {tokens} tokens\n"

        # Send the leaderboard with a random photo
        photo_url = random.choice(PHOTO_URL)
        await message.reply_video(video=photo_url, caption=leaderboard_message, parse_mode="HTML")

    except Exception as e:
        LOGGER.error(f"Error in /tokentop: {e}")
        await message.reply_text("An error occurred while fetching the leaderboard.")

