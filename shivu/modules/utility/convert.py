import asyncio
import importlib
import random
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters, Application
#from shivu import collection, user_collection, shivuu
#from shivu.modules import app
from shivu.modules.lock import command_lock
#from shivu import application, ban_collection



from pyrogram import Client, filters  # noqa: F811
from pyrogram.types import Message
#from shivu import user_collection, ban_collection, shivuu as app

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
)

# Conversion rate
COIN_TO_TOKEN_RATE = 100  # 100 coins = 1 token
TOKEN_TO_COIN_RATE = 100  # 1 token = 100 coins

# Convert coins to tokens
@app.on_message(filters.command("convert"))
@command_lock
async def convert_coins_to_tokens(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if the user is banned
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        await message.reply("🚫 **You are banned and cannot use this command.**")
        return

    # Check if the user provided a valid amount
    if len(message.command) < 2:
        await message.reply("❌ **Usage:** `/convert <amount_of_coins>`")
        return

    try:
        coins_to_convert = int(message.command[1])
        if coins_to_convert <= 0:
            await message.reply("❌ **Please enter a valid amount of coins to convert.**")
            return
    except ValueError:
        await message.reply("❌ **Invalid input. Please enter a number.**")
        return

    # Fetch the user's data
    user = await user_collection.find_one({"id": user_id})
    if not user:
        await message.reply("❌ **You don't have any coins to convert.**")
        return

    current_coins = user.get("coins", 0)

    # Check if the user has enough coins
    if coins_to_convert > current_coins:
        await message.reply(f"❌ **You don't have enough coins. You only have {current_coins} coins.**")
        return

    # Calculate tokens and remaining coins
    tokens = coins_to_convert // COIN_TO_TOKEN_RATE
    remaining_coins = coins_to_convert % COIN_TO_TOKEN_RATE

    # Update the user's tokens and coins
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"tokens": tokens, "coins": -coins_to_convert + remaining_coins}
        }
    )

    await message.reply(
        f"✅ **Converted {coins_to_convert - remaining_coins} coins to {tokens} tokens!**\n"
        f"🪙 **Remaining coins:** {remaining_coins}"
    )


# Convert tokens to coins
@app.on_message(filters.command("tconvert"))
@command_lock
async def convert_tokens_to_coins(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if the user is banned
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        await message.reply("🚫 **You are banned and cannot use this command.**")
        return

    # Check if the user provided a valid amount
    if len(message.command) < 2:
        await message.reply("❌ **Usage:** `/tconvert <amount_of_tokens>`")
        return

    try:
        tokens_to_convert = int(message.command[1])
        if tokens_to_convert <= 0:
            await message.reply("❌ **Please enter a valid amount of tokens to convert.**")
            return
    except ValueError:
        await message.reply("❌ **Invalid input. Please enter a number.**")
        return

    # Fetch the user's data
    user = await user_collection.find_one({"id": user_id})
    if not user:
        await message.reply("❌ **You don't have any tokens to convert.**")
        return

    current_tokens = user.get("tokens", 0)

    # Check if the user has enough tokens
    if tokens_to_convert > current_tokens:
        await message.reply(f"❌ **You don't have enough tokens. You only have {current_tokens} tokens.**")
        return

    # Calculate coins
    coins = tokens_to_convert * TOKEN_TO_COIN_RATE

    # Update the user's coins and tokens
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"coins": coins, "tokens": -tokens_to_convert}
        }
    )

    await message.reply(f"✅ **Converted {tokens_to_convert} tokens to {coins} coins!**")
