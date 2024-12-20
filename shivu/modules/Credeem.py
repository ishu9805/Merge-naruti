import random
import string
import datetime
from telegram.ext import CommandHandler
from shivu import application, user_collection, PARTNER, ban_collection
from shivu import LOGGER
import random
import string
import datetime
from telegram.ext import CommandHandler
from shivu import application, user_collection, PARTNER, ban_collection
from shivu import LOGGER

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from shivu import application, user_collection, db, collection
import random

# MongoDB Collection for user shops
user_shops_collection = db["user_shops"]

# Global dictionary to store shop user IDs
active_shops = {}

# Define prices and their rarities
price_rarities = {
    3000: '⚪️ Common', 
    5000: '🟣 Rare',
    8000: '🟡 Legendary',
    7000: '🟢 Medium',
    15000: '💮 Special edition',
    50000: '🔮 Limited Edition',
    100000: '🌤 Summer',
    500000: '🎐 Celestial',
    200000: '❄️ Winter',
    500000: '💝 Valentine',
    500000: '🎃 Halloween',
    500000: '🎄 Christmas Special'
}

# Function to start the store
async def y_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_date = datetime.today().strftime("%Y-%m-%d")  # Use formatted date

    # Store the active shop for the user
    active_shops[chat_id] = user_id

    # Retrieve shop data for the user from the database
    shop_data = await user_shops_collection.find_one({"id": user_id, "date": current_date})

    if not shop_data:
        # Generate a new shop with 3 random characters
        characters = await collection.aggregate([{"$sample": {"size": 3}}]).to_list(length=3)

        # Assign unique prices to the 3 characters
        prices = list(price_rarities.keys())  # Extract price keys
        random.shuffle(prices)  # Shuffle to assign different prices

        # Prepare character data with all fields
        prepared_characters = [
            {
                "name": char["name"],
                "anime": char["anime"],
                "rarity": prices.pop(),
                "price": price_rarities.get(char["rarity"], "Unknown"),
                "img_url": char["img_url"],
                "id": char["id"]
            }
            for char in characters
        ]

        # Store the shop data in the database
        shop_data = {
            "id": user_id,
            "date": current_date,
            "characters": prepared_characters,
            "index": 0
        }
        await user_shops_collection.insert_one(shop_data)

    # Display the current character in the shop
    await send_shop_item(update, context, shop_data, edit=False)

# Function to send the shop item
async def send_shop_item(update: Update, context: ContextTypes.DEFAULT_TYPE, shop_data, edit=True):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    current_index = shop_data['index']
    character = shop_data['characters'][current_index]

    # Extract character details
    name = character['name']
    rarity = character['rarity']
    price = price_rarities.get(character['rarity'])
    img_url = character['img_url']
    id = character['id']
    
    # Prepare buttons
    keyboard = [
        [InlineKeyboardButton("ᑭᑌᖇᑕᕼᗩՏᗴ  🛍️", callback_data=f"buyup_{current_index}")],
        [
            InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="backup"),
            InlineKeyboardButton("Nᴇxᴛ ➡️", callback_data="nextup")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message directly to the user in the same chat (not editing)
    if edit and update.callback_query:
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(
                media=img_url,
                caption=f"ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ\n𝗘𝗫𝗖𝗟𝗨𝗦𝗜𝗩𝗘 𝗖𝗛𝗔𝗥𝗔𝗖𝗧𝗘𝗥 𝗦𝗛𝗢𝗣 🏷️\n\n"
                        f"Name: {name}\n"
                        f"Price: {rarity} Coins\n"
                        f"Rarity: {price}"
            ),
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=img_url,
            caption=f"ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ\n𝗘𝗫𝗖𝗟𝗨𝗦𝗜𝗩𝗘 𝗖𝗛𝗔𝗥𝗔𝗖𝗧𝗘𝗥 𝗦𝗛𝗢𝗣 🏷️\n\n"
                    f"Name: {name}\n"
                    f"Price: {rarity} Coins\n"
                    f"Rarity: {price}",
            reply_markup=reply_markup
        )

# Function to handle shop button callbacks
async def handle_shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    current_date = datetime.today().strftime("%Y-%m-%d")

    # Verify if the user is the owner of the shop
    if chat_id not in active_shops or active_shops[chat_id] != user_id:
        await query.answer("❌ You cannot interact with this shop as you didn't start it.")
        return

    # Retrieve shop data for the user
    shop_data = await user_shops_collection.find_one({"id": user_id, "date": current_date})
    if not shop_data:
        await query.answer("❌ Shop data not found. Use /ystore again.")
        return

    current_index = shop_data["index"]

    # Handle actions for buttons
    if query.data.startswith("buyup_"):
        current_character_id = shop_data["characters"][current_index]["id"]

        # Check if the user has already bought the character
        purchased_ids = shop_data.get("purchased_ids", [])
        if current_character_id in purchased_ids:
            await query.answer("❌ You have already bought this character!")
            return

        # Handle purchase
        await handle_purchase(query, shop_data, user_id)

        # Update shop data with the purchased character ID
        purchased_ids.append(current_character_id)
        await user_shops_collection.update_one(
            {"id": user_id, "date": current_date},
            {"$set": {"purchased_ids": purchased_ids}}
        )
    elif query.data == "nextup":
        new_index = (current_index + 1) % len(shop_data["characters"])
        await user_shops_collection.update_one(
            {"id": user_id, "date": current_date},
            {"$set": {"index": new_index}}
        )
        shop_data["index"] = new_index
        await send_shop_item(update, context, shop_data, edit=True)
    elif query.data == "backup":
        new_index = (current_index - 1) % len(shop_data["characters"])
        await user_shops_collection.update_one(
            {"id": user_id, "date": current_date},
            {"$set": {"index": new_index}}
        )
        shop_data["index"] = new_index
        await send_shop_item(update, context, shop_data, edit=True)


async def handle_purchase(query, shop_data, user_id):
    # Get the current character being purchased
    current_index = shop_data["index"]
    character = shop_data["characters"][current_index]
    character_name = character["name"]
    character_rarity = character["price"]
    character_price = price_rarities.get(character["price"], "Unknown")
    character_id = character["id"]
    
    # Retrieve the user's current coins from the database (assuming you have a 'user_collection' in MongoDB)
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data:
        await query.answer("❌ User data not found. Please try again later.")
        return

    # Check if the user has enough coins
    user_coins = user_data.get("coins", 0)
    if user_coins < character_price:
        await query.answer(f"❌ You don't have enough coins to buy {character_name}.")
        return

    # Deduct the coins
    new_coin_balance = user_coins - character_price
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"coins": new_coin_balance}}
    )

    # Add the character to the user's collection (assuming a 'user_collection' with a 'collection' field)
    updated_collection = user_data.get("collection", [])
    updated_collection.append(character_id)
    
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"collection": updated_collection}}
    )

    # Confirm the purchase
    await query.answer(f"✅ You successfully bought {character_name} for {character_price} coins!")
    
    # Optionally, you can update the shop data and send a message about the next item
    await query.message.edit_caption(
        caption=f"🎉 Purchase Successful! You bought {character_name}!\n"
                f"Remaining coins: {new_coin_balance}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ 𝗕𝗔𝗖𝗞", callback_data="backup"),
             InlineKeyboardButton("𝗡𝗘𝗫𝗧 ➡️", callback_data="nextup")]
        ])
    )

# Add handlers

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
