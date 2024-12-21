import random
import string
import datetime
from telegram.ext import CommandHandler, CallbackQueryHandler
from shivu import application, user_collection, PARTNER, ban_collection, LOGGER, collection, db
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

# MongoDB Collection for user shops
user_shops_collection = db["user_shop"]

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
    current_index = shop_data['index']
    character = shop_data['characters'][current_index try:
        name = character['name']
        rarity = character['rarity']
        price = character['price']
        img_url = character['img_url']
        purchased = character.get('purchased', False)

        buy_button_text = "ᑭᑌᖇᑕᕼᗩՏᗴ 🛍️" if not purchased else "𝗦𝗢𝗟𝗗 🛑"
        buy_button_callback = f"buyup_{current_index}" if not purchased else ""

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
application.add_handler(CommandHandler("dailyshop", y_store))
application.add_handler(CallbackQueryHandler(handle_shop_callback))

last_usage_time = {}
generated_codes = {}

def generate_random_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

async def daily_code(update, context):
    user_id = update.effective_user.id
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    if user_id in last_usage_time:
        last_time = last_usage_time[user_id]
        current_time = datetime.datetime.now()
        time_diff = current_time - last_time
        if time_diff.total_seconds() < 86400:  # 24 hours
            await update.message.reply_text("⏳ You can only use this command once every 24 hours.")
            return

    code = generate_random_code()
    amount = random.randint(10, 2500)
    quantity = 1

    last_usage_time[user_id] = datetime.datetime.now()
    generated_codes[code] = {'amount': amount, 'quantity': quantity}

    response_text = (
        f"<b>Your daily coin code:</b>\n"
        f"<code>{code}</code>\n"
        f"<b>Amount:</b> {amount} coins\n"
        f"<b>Quantity:</b> {quantity}\n"
        f"<b>To redeem:</b> /credeem {code}"
    )
    await update.message.reply_html(response_text)

async def gen(update, context):
    user_id = str(update.effective_user.id)
    if user_id not in PARTNER:
        await update.message.reply_text("🚫 You are not authorized to generate codes.")
        return

    try:
        amount = float(context.args[0])
        quantity = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Invalid usage. Usage: /gen <amount> <quantity>")
        return

    code = generate_random_code()
    generated_codes[code] = {'amount': amount, 'quantity': quantity}

    response_text = (
        f"<b>Generated coin code:</b>\n"
        f"<code>{code}</code>\n"
        f"<b>Amount:</b> {amount} coins\n"
        f"<b>Quantity:</b> {quantity}\n"
        f"<b>To redeem:</b> /credeem {code}"
    )
    await update.message.reply_html(response_text)

    log_text = (
        f"<b>Code generated by user {user_id}:</b>\n"
        f"<code>{code}</code>\n"
        f"<b>Amount:</b> {amount} coins\n"
        f"<b>Quantity:</b> {quantity}"
    )
    await context.bot.send_message(chat_id=PARTNER, text=log_text, parse_mode='HTML')

async def redeem(update, context):
    code = " ".join(context.args)
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    if code in generated_codes:
        details = generated_codes[code]

        if details['quantity'] > 0:
            user_doc = await user_collection.find_one({'id': user_id})

            redeemed_codes = user_doc.get('redeemed_codes', []) if user_doc else []
            if code in redeemed_codes:
                await update.message.reply_text("❌ You have already redeemed this code.")
                return

            amount = details['amount']
            await user_collection.update_one(
                {'id': user_id},
                {
                    '$inc': {'coins': amount},
                    '$addToSet': {'redeemed_codes': code}
                },
                upsert=True
            )

            details['quantity'] -= 1
            if details['quantity'] == 0:
                del generated_codes[code]
                await user_collection.update_many(
                    {'redeemed_codes': code},
                    {'$pull': {'redeemed_codes': code}}
                )

            await update.message.reply_text(
                f"✅ Code redeemed successfully! {amount} coins added to your account."
            )
        else:
            await update.message.reply_text("❌ This code has reached its redemption limit.")
    else:
        await update.message.reply_text("❌ Invalid code.")

application.add_handler(CommandHandler("dailycode", daily_code))
application.add_handler(CommandHandler("gen", gen))
application.add_handler(CommandHandler("credeem", redeem))
