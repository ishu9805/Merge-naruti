import random
import string
import datetime
from telegram.ext import CommandHandler, CallbackQueryHandler
from shivu import application, user_collection, PARTNER, ban_collection, collection, db, required_group_id
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from .block import block_dec, temp_block, block_dec_ptb, block_cbq_ptb
from . import app
from .coin import is_member
from .lock import command_lock

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
# MongoDB Collection for user sho

# Handlers
#application.add_handler(CommandHandler("dailyshop", y_store))
#application.add_handler(CallbackQueryHandler(handle_shop_callback))

last_usage_time = {}
generated_codes = {}

def generate_random_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))


import random
import string
import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from shivu import user_collection, PARTNER, shivuu as app
from .lock import command_lock

# Constants
GROUP_LINK = "https://t.me/BLADE_X_COMMUNITY"  # Replace with your group link

# Global variables
generated_codes = {}  # Stores codes and their details
user_last_daily_code = {}  # Tracks the last time a user generated a daily code

# Function to generate a random code
def generate_random_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))


# Daily code generation
@app.on_message(filters.command("dailycode"))
@command_lock
async def daily_code(client: Client, message: Message):
    user_id = message.from_user.id

    # Check group membership
    if not await is_member(user_id):
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("✨ Join the Group to use command ✨", url=GROUP_LINK)]])
        await message.reply_text("You need to join our group to use this command.", reply_markup=reply_markup)
        return

    # Rate limit (24 hours)
    last_usage = user_last_daily_code.get(user_id)
    if last_usage and (datetime.datetime.now() - last_usage).total_seconds() < 86400:
        await message.reply_text("⏳ You can only use this command once every 24 hours.")
        return

    # Generate and save the daily code
    code = generate_random_code()
    amount = random.randint(10, 2500)
    generated_codes[code] = {"amount": amount, "quantity": 1, "redeemed_by": []}
    user_last_daily_code[user_id] = datetime.datetime.now()

    response_text = (
        f"<b>Your daily coin code:</b>\n"
        f"<code>{code}</code>\n"
        f"<b>Amount:</b> {amount} coins\n"
        f"<b>To redeem:</b> /credeem {code}"
    )
    await message.reply_text(response_text)


# Code redemption
@app.on_message(filters.command("credeem"))
@command_lock
async def redeem(client: Client, message: Message):
    user_id = message.from_user.id
    code = " ".join(message.command[1:])

    # Check group membership
    if not await is_member(user_id):
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("✨ Join the Group ✨", url=GROUP_LINK)]])
        await message.reply_text("You need to join our group to use this command.", reply_markup=reply_markup)
        return

    # Validate and redeem code
    code_data = generated_codes.get(code)
    if not code_data or code_data["quantity"] <= 0:
        await message.reply_text("❌ Invalid or expired code.")
        return

    if user_id in code_data["redeemed_by"]:
        await message.reply_text("❌ You have already redeemed this code.")
        return

    amount = code_data["amount"]
    code_data["quantity"] -= 1
    code_data["redeemed_by"].append(user_id)

    # Update user's coins in the database
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"coins": amount}},
        upsert=True
    )
    await message.reply_text(f"✅ Successfully redeemed {amount} coins!")


# Admin code generation
@app.on_message(filters.command("gen"))
@command_lock
async def gen(client: Client, message: Message):
    user_id = message.from_user.id
    if str(user_id) not in PARTNER:
        await message.reply_text("🚫 You are not authorized to generate codes.")
        return

    try:
        amount = float(message.command[1])
        quantity = int(message.command[2])
    except (IndexError, ValueError):
        await message.reply_text("❌ Invalid usage. Usage: /gen <amount> <quantity>")
        return

    code = generate_random_code()
    generated_codes[code] = {"amount": amount, "quantity": quantity, "redeemed_by": []}

    response_text = (
        f"<b>Generated coin code:</b>\n"
        f"<code>{code}</code>\n"
        f"<b>Amount:</b> {amount} coins\n"
        f"<b>Quantity:</b> {quantity}\n"
        f"<b>To redeem:</b> /credeem {code}"
    )
    await message.reply_text(response_text)



