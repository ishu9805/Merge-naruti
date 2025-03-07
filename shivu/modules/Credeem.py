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
# MongoDB Collection for user shops
user_shops_collection = db["dailyshop"]

# Global dictionary to store active shop user IDs
active_shops = {}

# Define prices and their rarities
price_rarities = {
    '⚪️ Common': 3000,
    '🟣 Rare': 5000,
    '🟢 Medium': 7000,
    '🟡 Legendary': 8000,
    '💮 Special Edition': 15000,
    '🔮 Limited Edition': 50000,
    '🌤 Summer': 100000,
    '❄️ Winter': 200000,
    '🎐 Celestial': 500000,
    '💝 Valentine': 500000,
    '🎃 Halloween': 500000,
    '🎄 Christmas Special': 500000
}

async def is_member(user_id):
    """Check if a user is part of the required group."""
    try:
        member = await application.bot.get_chat_member(required_group_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False


async def get_user_coins(user_id):
    try:
        user_doc = await user_collection.find_one({"id": user_id})
        return user_doc.get("coins", 0) if user_doc else 0
    except Exception as e:
        LOGGER.error(f"Error fetching user coins for user_id {user_id}: {e}")
        return 0

async def update_user_coins(user_id, new_balance, character):
    try:
        # Update the user's coin balance
        await user_collection.update_one(
            {"id": user_id}, 
            {"$set": {"coins": new_balance}}, 
            upsert=True
        )
        
        # Add the character to the user's collection
        character_data = {
            "name": character["name"],
            "anime": character["anime"],
            "rarity": character["rarity"],
            "img_url": character["img_url"],
            "price": character["price"],
            "id": character["id"]
        }
        
        await user_collection.update_one(
            {"id": user_id},
            {"$push": {"characters": character_data}}
        )
        return True
    except Exception as e:
        LOGGER.error(f"Error updating user coins for user_id {user_id}: {e}")
        return False

async def y_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_date = datetime.datetime.today().strftime("%Y-%m-%d")

    # Store the active shop for the user
    active_shops[chat_id] = user_id

    try:
        # Retrieve or create shop data
        shop_data = await user_shops_collection.find_one({"id": user_id, "date": current_date})
        if not shop_data:
            characters = await collection.aggregate([{"$sample": {"size": 3}}]).to_list(length=3)
            prepared_characters = []

            for char in characters:
                rarity = char["rarity"]
                if rarity in price_rarities:
                    price = price_rarities[rarity]
                    prepared_characters.append({
                        "name": char["name"],
                        "anime": char["anime"],
                        "rarity": rarity,
                        "price": price,
                        "img_url": char["img_url"],
                        "id": char["id"],
                        "purchased": False
                    })

            if not prepared_characters:
                await update.message.reply_text("No valid characters found for the shop.")
                return

            shop_data = {
                "id": user_id,
                "date": current_date,
                "characters": prepared_characters,
                "index": 0
            }
            await user_shops_collection.insert_one(shop_data)

        await send_shop_item(update, context, shop_data, edit=False)
    except Exception as e:
        LOGGER.error(f"Error in y_store for user_id {user_id}: {e}")
        await update.message.reply_text("An error occurred while accessing the shop.")

async def send_shop_item(update: Update, context: ContextTypes.DEFAULT_TYPE, shop_data, edit=True):
    try:
        current_index = shop_data['index']
        character = shop_data['characters'][current_index]
    
        name = character['name']
        rarity = character['rarity']
        price = character['price']
        img_url = character['img_url']
        purchased = character.get('purchased', False)

        buy_button_text = "ᑭᑌᖇᑕᕼᗩՏᗴ 🛍️" if not purchased else "𝗦𝗢𝗟𝗗 🛑"
        buy_button_callback = f"buyup_{current_index}" if not purchased else "sold_out"

        keyboard = [
            [InlineKeyboardButton(buy_button_text, callback_data=buy_button_callback)],
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="backup"),
                InlineKeyboardButton("Nᴇxᴛ ➡️", callback_data="nextup")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if edit and update.callback_query:
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(
                    media=img_url,
                    caption=f"𝗘𝗫𝗖𝗟𝗨𝗦𝗜𝗩𝗘 𝗖𝗛𝗔𝗥𝗔𝗖𝗧𝗘𝗥 𝗦𝗛𝗢𝗣 🏷️\n\n"
                            f"Name: {name}\nPrice: {price} Coins\nRarity: {rarity}\n"
                            f"{'SOLD OUT' if purchased else ''}"
                ),
                reply_markup=reply_markup
            )
        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_url,
                caption=f"𝗘𝗫𝗖𝗟𝗨𝗦𝗜𝗩𝗘 𝗖𝗛𝗔𝗥𝗔𝗖𝗧𝗘𝗥 𝗦𝗛𝗢𝗣 🏷️\n\n"
                        f"Name: {name}\nPrice: {price} Coins\nRarity: {rarity}\n"
                        f"{'SOLD OUT' if purchased else ''}",
                reply_markup=reply_markup
            )
    except Exception as e:
        LOGGER.error(f"Error sending shop item for user_id {update.effective_user.id}: {e}")
        await update.message.reply_text("An error occurred while sending the shop item.")

async def handle_shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    current_date = datetime.datetime.today().strftime("%Y-%m-%d")

    if chat_id not in active_shops or active_shops[chat_id] != user_id:
        await query.answer("❌ You cannot interact with this shop.")
        return

    try:
        shop_data = await user_shops_collection.find_one({"id": user_id, "date": current_date})
        if not shop_data:
            await query.answer("❌ Shop not found. Use /ystore again.")
            return

        if query.data.startswith("buyup_"):
            await handle_purchase(query, shop_data, user_id)
        elif query.data == "nextup":
            shop_data["index"] = (shop_data["index"] + 1) % len(shop_data["characters"])
            await user_shops_collection.update_one({"id": user_id, "date": current_date}, {"$set": {"index": shop_data["index"]}})
            await send_shop_item(update, context, shop_data, edit=True)
        elif query.data == "backup":
            shop_data["index"] = (shop_data["index"] - 1) % len(shop_data["characters"])
            await user_shops_collection.update_one({"id": user_id, "date": current_date}, {"$set": {"index": shop_data["index"]}})
            await send_shop_item(update, context, shop_data, edit=True)
    except Exception as e:
        LOGGER.error(f"Error handling shop callback for user_id {user_id}: {e}")
        await query.answer("An error occurred while processing your request.")

async def handle_purchase(query, shop_data, user_id):
    try:
        current_index = int(query.data.split('_')[1])
        character = shop_data['characters'][current_index]

        if character['purchased']:
            await query.answer("This character has already been bought.", show_alert=True)
            return

        user_coins = await get_user_coins(user_id)
        if user_coins >= character['price']:
            new_balance = user_coins - character['price']
            if await update_user_coins(user_id, new_balance, character):
                character['purchased'] = True
                await user_shops_collection .update_one(
                    {"id": user_id, "date": datetime.datetime.today().strftime("%Y-%m-%d")},
                    {"$set": {"characters": shop_data['characters']}}
                )
                await query.answer(f"You've bought {character['name']} for {character['price']} Coins!", show_alert=True)
                await send_shop_item(update, context, shop_data, edit=True)
            else:
                await query.answer("An error occurred while updating your coins.", show_alert=True)
        else:
            await query.answer("You don't have enough coins.", show_alert=True)
    except Exception as e:
        LOGGER.error(f"Error handling purchase for user_id {user_id}: {e}")
        await query.answer("An error occurred while processing your purchase.", show_alert=True)

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
