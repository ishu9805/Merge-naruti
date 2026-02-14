import asyncio
import urllib.request
import uuid
import requests
import random
import html
#from shivu.modules import app
import logging
from pymongo import ReturnDocument
from typing import List
from bson import ObjectId
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from datetime import datetime, timedelta
#from shivu import ban_collection
from shivu import UPDATE_CHAT, SUPPORT_CHAT, CHARA_CHANNEL_ID, required_group_id, PHOTO_URL, OWNER_ID, PARTNER
from shivu import (
    collectionps as collection,
    top_global_groups_collectionps as top_global_groups_collection,
    group_user_totals_collectionps as group_user_totals_collection,
    user_collectionps as user_collection,
    user_totals_collectionps as user_totals_collection,
    shivuups as shivuu,
    shivuups as app,
    applicationps as application,
    SUPPORT_CHATps as SUPPORT,
    UPDATE_CHATps as UPDATE_CHAT_PS,
    dbps as db,
    pmusersps as pmusers,
    ban_collectionps as ban_collection,
    user_countps as user_count, 
    chat_dataps as chat_data,
    force,
    userbot
)
# Assuming these are defined elsewhere in your code
#from shivu import db, UPDATE_CHAT, SUPPORT_CHAT, CHARA_CHANNEL_ID, collection, user_collection, required_group_id
#from shivu import (application, PHOTO_URL, OWNER_ID,
                   # user_collection, top_global_groups_collection, top_global_groups_collection, 
                  #  group_user_totals_collection)

#from shivu import PARTNER
from shivu.modules.block import block_dec, temp_block
from shivu.modules.lock import command_lock
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)


OWNER_ID = "5856750053"  # noqa: F811

SUPPORT_GROUP_LINK = "https://t.me/animechatiac"
SUPPORT_BUTTON_TEXT = "✨ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ✨"


def support_group_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(SUPPORT_BUTTON_TEXT, url=SUPPORT_GROUP_LINK)]])


def leaderboard_switch_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏆 Top", callback_data="switch_lb:top"),
            InlineKeyboardButton("👥 TopGroups", callback_data="switch_lb:topgroups"),
        ],
        [
            InlineKeyboardButton("💸 CoinTop", callback_data="switch_lb:cointop"),
            InlineKeyboardButton("⚡ TokenTop", callback_data="switch_lb:tokentop"),
        ],
        [InlineKeyboardButton(SUPPORT_BUTTON_TEXT, url=SUPPORT_GROUP_LINK)],
    ])


async def resolve_user_for_lb(user: dict) -> tuple[str, str]:
    user_id = user.get("id")
    name = html.escape(str(user.get("first_name") or user.get("username") or f"User {user_id}"))[:30]
    link = f"tg://user?id={user_id}"

    if getattr(userbot, "is_connected", False) and user_id is not None:
        try:
            u = await userbot.get_users(user_id)
            name = html.escape((u.first_name or name))[:30]
            if u.username:
                link = f"https://t.me/{u.username}"
            else:
                link = f"tg://user?id={u.id}"
        except Exception:
            pass

    return name, link


from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup  # noqa: F811
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
            await message.reply_text("You Have Already Claimed Your Daily Reward.", reply_markup=support_group_markup())
            return

        await add_coins(user_id, 40)
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"last_daily_claimed": datetime.now()}},
        )
        await message.reply_text("You Have Claimed Your Daily Reward. You Earned 40 Coins.", reply_markup=support_group_markup())
    else:
        await user_collection.insert_one({"id": user_id, "coins": 40, "last_daily_claimed": datetime.now()})
        await message.reply_text("You Have Claimed Your Daily Reward. You Earned 40 Coins.", reply_markup=support_group_markup())
 

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
            await message.reply_text("You Have Already Claimed Your Weekly Reward.", reply_markup=support_group_markup())
            return

        await add_coins(user_id, 500)
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"last_weekly_claimed": datetime.now()}},
        )
        await message.reply_text("You Have Claimed Your Weekly Reward. You Earned 250 Coins.", reply_markup=support_group_markup())
    else:
        await user_collection.insert_one({"id": user_id, "coins": 250, "last_weekly_claimed": datetime.now()})
        await message.reply_text("You Have Claimed Your Weekly Reward. You Earned 250 Coins.", reply_markup=support_group_markup())




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
    """ if not await is_member(user_id):
        group_link = force  # Replace with the actual group invite link
        messages = (
            "You need to be a member of our exclusive group to use this command.\n"
            "Join now and explore the amazing features awaiting you!\n\n"
        )
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✨ Join the Group ✨", url=group_link)]]
        )
        await message.reply_text(messages, reply_markup=reply_markup)
        return"""
       

    user = await user_collection.find_one({"id": user_id})
    if user:
        last_claimed = user.get("last_bonus_claimed")
        if last_claimed and last_claimed.date() == datetime.now().date():
            await message.reply_text("You have already claimed your bonus coins today.", reply_markup=support_group_markup())
            return

        await add_coins(user_id, 100)
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"last_bonus_claimed": datetime.now()}},
        )
        await message.reply_text("You have claimed your daily bonus coins. You earned 100 coins!", reply_markup=support_group_markup())
    else:
        await user_collection.insert_one({"id": user_id, "coins": 100, "last_bonus_claimed": datetime.now()})
        await message.reply_text("You have claimed your daily bonus coins. You earned 100 coins!", reply_markup=support_group_markup())

            
@app.on_message(filters.command("cointop"))
@block_dec
@command_lock
async def top_users_by_coins(client: Client, message: Message):
    try:
        top_users = await user_collection.aggregate([
            {"$project": {"id": 1, "coins": 1, "username": 1, "first_name": 1}},
            {"$sort": {"coins": -1}},
            {"$limit": 10}
        ]).to_list(length=10)

        if not top_users:
            await message.reply_text("No users found in the leaderboard.", reply_markup=leaderboard_switch_markup())
            return

        leaderboard_message = "<b>Top 10 Users by Coins:</b>\n\n"
        for i, user in enumerate(top_users, start=1):
            coins = user.get("coins", 0)
            name, link = await resolve_user_for_lb(user)
            leaderboard_message += f"{i}. <a href='{link}'>{name}</a>: {coins} coins\n"

        photo_url = random.choice(PHOTO_URL)
        await message.reply_photo(photo=photo_url, caption=leaderboard_message, reply_markup=leaderboard_switch_markup())

    except Exception as e:
        LOGGER.error(f"Error in /cointop: {e}")
        await message.reply_text("An error occurred while fetching the leaderboard.", reply_markup=leaderboard_switch_markup())


@app.on_message(filters.command("tokentop"))
@block_dec
@command_lock
async def top_users_by_tokens(client: Client, message: Message):
    try:
        top_users = await user_collection.aggregate([
            {"$project": {"id": 1, "tokens": 1, "username": 1, "first_name": 1}},
            {"$sort": {"tokens": -1}},
            {"$limit": 10}
        ]).to_list(length=10)

        if not top_users:
            await message.reply_text("No users found in the leaderboard.", reply_markup=leaderboard_switch_markup())
            return

        leaderboard_message = "<b>Top 10 Users by Tokens:</b>\n\n"
        for i, user in enumerate(top_users, start=1):
            tokens = user.get("tokens", 0)
            name, link = await resolve_user_for_lb(user)
            leaderboard_message += f"{i}. <a href='{link}'>{name}</a>: {tokens} tokens\n"

        photo_url = random.choice(PHOTO_URL)
        await message.reply_photo(photo=photo_url, caption=leaderboard_message, reply_markup=leaderboard_switch_markup())

    except Exception as e:
        LOGGER.error(f"Error in /tokentop: {e}")
        await message.reply_text("An error occurred while fetching the leaderboard.", reply_markup=leaderboard_switch_markup())
