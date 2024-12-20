import random
import string
import datetime
from telegram.ext import CommandHandler
from shivu import application, user_collection, PARTNER, ban_collection
from shivu import LOGGER
import random
import string
import random
import string
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from shivu import application, user_collection, db, PARTNER, ban_collection
from telegram.ext import CommandHandler
from shivu import application, user_collection, PARTNER, ban_collection
from shivu import LOGGER, collection 

# MongoDB Collection for user shops
user_shops_collection = db["user_shops"]

# Global dictionary to store active shop user IDs
active_shops = {}

# Define prices and their rarities
# Updated prices and their rarities
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
    user_doc = await user_collection.find_one({"id": user_id})
    if user_doc:
        return user_doc.get("coins", 0)  # Assuming 'coins' is the field in the user document
    return 0
    
# Function to start the shop
# Function to start the shop
async def y_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_date = datetime.today().strftime("%Y-%m-%d")

    # Store the active shop for the user
    active_shops[chat_id] = user_id

    # Retrieve or create shop data
    shop_data = await user_shops_collection.find_one({"id": user_id, "date": current_date})
    if not shop_data:
        characters = await collection.aggregate([{"$sample": {"size": 3}}]).to_list(length=3)
        rarities = list(price_rarities.keys())  # Use the rarity names
        random.shuffle(rarities)

        prepared_characters = [
            {
                "name": char["name"],
                "anime": char["anime"],
                "rarity": rarity,
                "price": price_rarities[rarity],  # Use price corresponding to rarity
                "img_url": char["img_url"],
                "id": char["id"],
                "purchased": False  # Add purchased status
            }
            for char, rarity in zip(characters, rarities)
        ]
        shop_data = {
            "id": user_id,
            "date": current_date,
            "characters": prepared_characters,
            "index": 0
        }
        await user_shops_collection.insert_one(shop_data)

    await send_shop_item(update, context, shop_data, edit=False)

# Function to send a shop item
async def send_shop_item(update: Update, context: ContextTypes.DEFAULT_TYPE, shop_data, edit=True):
    current_index = shop_data['index']
    character = shop_data['characters'][current_index]

    name = character['name']
    rarity = character['rarity']
    price = character['price']
    img_url = character['img_url']
    purchased = character.get('purchased', False)  # Defaults to False if 'purchased' is not found


    # Disable buy button if character is already purchased
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




# Function to handle shop callbacks
async def handle_shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    current_date = datetime.today().strftime("%Y-%m-%d")

    if chat_id not in active_shops or active_shops[chat_id] != user_id:
        await query.answer("❌ You cannot interact with this shop.")
        return

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


async def handle_purchase(query, shop_data, user_id):
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    current_index = int(query.data.split('_')[1])
    shop_data = await user_shops_collection.find_one({"id": user_id, "date": datetime.today().strftime("%Y-%m-%d")})

    if not shop_data:
        return

    character = shop_data['characters'][current_index]

    # Check if character is already purchased
    if character['purchased']:
        await query.answer("This character has already been bought.", show_alert=True)
        return

    # Deduct coins (example logic, implement your own deduction logic)
    user_coins = await get_user_coins(user_id)  # You need to implement this function
    if user_coins >= character['price']:
        # Deduct coins
        new_balance = user_coins - character['price']
        await update_user_coins(user_id, new_balance)  # You need to implement this function

        # Mark as purchased
        character['purchased'] = True
        await user_shops_collection.update_one(
            {"id": user_id, "date": datetime.today().strftime("%Y-%m-%d")},
            {"$set": {"characters": shop_data['characters']}}
        )

        await query.answer(f"You've bought {character['name']} for {character['price']} Coins!", show_alert=True)
        await send_shop_item(update, context, shop_data, edit=True)
    else:
        await query.answer("You don't have enough coins.", show_alert=True)


# Handlers
application.add_handler(CommandHandler("dailyshop", y_store))
application.add_handler(CallbackQueryHandler(handle_shop_callback))


        
# Add handlers




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

    # Check if the user is banned
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    # Check if the code exists
    if code in generated_codes:
        details = generated_codes[code]

        # Check if the code still has a quantity available
        if details['quantity'] > 0:
            # Fetch the user's document
            user_doc = await user_collection.find_one({'id': user_id})

            # Check if the user has already redeemed this code
            redeemed_codes = user_doc.get('redeemed_codes', []) if user_doc else []
            if code in redeemed_codes:
                await update.message.reply_text("❌ You have already redeemed this code.")
                return

            # Add coins to the user's balance
            amount = details['amount']
            await user_collection.update_one(
                {'id': user_id},
                {
                    '$inc': {'coins': amount},
                    '$addToSet': {'redeemed_codes': code}  # Add the code to the redeemed codes list
                },
                upsert=True
            )

            # Decrease the code's quantity and delete if no quantity left
            details['quantity'] -= 1
            if details['quantity'] == 0:
                # Remove the code from `generated_codes`
                del generated_codes[code]

                # Remove the code from all users' `redeemed_codes`
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
