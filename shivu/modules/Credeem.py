import random
import string
import datetime
from telegram.ext import CommandHandler, CallbackQueryHandler
from shivu import application, user_collection, PARTNER, ban_collection, collection, db, required_group_id
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from .block import block_dec, temp_block, block_dec_ptb, block_cbq_ptb
from . import app
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

@app.on_message(filters.command("dailycode"))
@command_lock
async def daily_code(client: Client, message: Message):
    user_id = message.from_user.id

    # Check group membership
    if not await is_member(user_id):
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("✨ Join the Group to use command ✨", url= "https://t.me/BLADE_X_COMMUNITY")]])
        await message.reply_text("You need to join our group to use this command.", reply_markup=reply_markup)
        return

    # Rate limit (24 hours)
    last_usage = await user_collection.find_one({"id": user_id, "last_daily_code": {"$exists": True}})
    if last_usage and (datetime.datetime.now() - last_usage["last_daily_code"]).total_seconds() < 86400:
        await message.reply_text("⏳ You can only use this command once every 24 hours.")
        return

    # Generate and save the daily code
    code = generate_random_code()
    amount = random.randint(10, 2500)
    await generated_codes_collection.insert_one({"code": code, "amount": amount, "quantity": 1})
    await user_collection.update_one({"id": user_id}, {"$set": {"last_daily_code": datetime.datetime.now()}}, upsert=True)

    response_text = (
        f"<b>Your daily coin code:</b>\n"
        f"<code>{code}</code>\n"
        f"<b>Amount:</b> {amount} coins\n"
        f"<b>To redeem:</b> /credeem {code}"
    )
    await message.reply_text(response_text)



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
    code_doc = await generated_codes_collection.find_one({"code": code})
    if not code_doc or code_doc["quantity"] <= 0:
        await message.reply_text("❌ Invalid or expired code.")
        return

    user_doc = await user_collection.find_one({"id": user_id})
    if code in user_doc.get("redeemed_codes", []):
        await message.reply_text("❌ You have already redeemed this code.")
        return

    amount = code_doc["amount"]
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"coins": amount}, "$addToSet": {"redeemed_codes": code}},
        upsert=True
    )
    await generated_codes_collection.update_one({"code": code}, {"$inc": {"quantity": -1}})
    await message.reply_text(f"✅ Successfully redeemed {amount} coins!")


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
    await generated_codes_collection.insert_one({"code": code, "amount": amount, "quantity": quantity})

    response_text = (
        f"<b>Generated coin code:</b>\n"
        f"<code>{code}</code>\n"
        f"<b>Amount:</b> {amount} coins\n"
        f"<b>Quantity:</b> {quantity}\n"
        f"<b>To redeem:</b> /credeem {code}"
    )
    await message.reply_text(response_text)
