
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

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)

shops_collection = db["shops"]
# Owner ID
OWNER_ID = "5856750053"


async def is_member(user_id):
    """Check if a user is part of the required group."""
    try:
        member = await application.bot.get_chat_member(required_group_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

async def check_balance(update: Update, context: CallbackContext) -> None:

    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass

    try:
        user_id = int(update.effective_user.id)
        user = await user_collection.find_one({"id": user_id})



        if user:
            coins = user.get("coins", 0)
            tokens = user.get("tokens",0)
            await update.message.reply_text(f" **Bᴇʜᴏʟᴅ, Yᴏᴜʀ Cᴜʀʀᴇɴᴛ Bᴀʟᴀɴᴄᴇ Sʜɪɴᴇs** ➻💸 {coins} Cᴏɪɴs Aɴᴅ ➻⚡ {tokens} Tᴏᴋᴇɴs.")
        else:
            await update.message.reply_text("Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴʏ Cᴏɪɴs Yᴇᴛ.")
    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")

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

async def daily_reward(update: Update, context: CallbackContext) -> None:

    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass


    try:
        user_id = int(update.effective_user.id)
        user = await user_collection.find_one({"id": user_id})

        if user:
            last_claimed = user.get("last_daily_claimed")
            if last_claimed and last_claimed.date() == datetime.now().date():
                await update.message.reply_text("Yᴏᴜ Hᴀᴠᴇ Aʟʀᴇᴀᴅʏ Cʟᴀɪᴍᴇᴅ Yᴏᴜʀ Dᴀɪʟʏ Rᴇᴡᴀʀᴅ.")
                return

            await add_coins(user_id, 40)
            await user_collection.update_one(
                {"id": user_id},
                {"$set": {"last_daily_claimed": datetime.now()}},
            )
            await update.message.reply_text("Yᴏᴜ Hᴀᴠᴇ Cʟᴀɪᴍᴇᴅ Yᴏᴜʀ Dᴀɪʟʏ ʀᴇᴡᴀʀᴅ. Yᴏᴜ Eᴀʀɴᴇᴅ 𝟺𝟶 Cᴏɪɴs")
        else:
            await user_collection.insert_one({"id": user_id, "coins": 40, "last_daily_claimed": datetime.now()})
            await update.message.reply_text("Yᴏᴜ Hᴀᴠᴇ Cʟᴀɪᴍᴇᴅ Yᴏᴜʀ Dᴀɪʟʏ ʀᴇᴡᴀʀᴅ. Yᴏᴜ Eᴀʀɴᴇᴅ 𝟺𝟶 Cᴏɪɴs.")
    except Exception as e:
        LOGGER.error(f"Error occurred: {e}")
        await update.message.reply_text(f"Error occurred: {e}")



async def weekly_reward(update: Update, context: CallbackContext) -> None:

    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass

    try:
        user_id = int(update.effective_user.id)
        user = await user_collection.find_one({"id": user_id})

        if user:
            last_claimed = user.get("last_weekly_claimed")
            start_of_week = datetime.now().date() - timedelta(days=datetime.now().weekday())
            if last_claimed and last_claimed.date() >= start_of_week:
                await update.message.reply_text("Yᴏᴜ Hᴀᴠᴇ Aʟʀᴇᴀᴅʏ Cʟᴀɪᴍᴇᴅ Yᴏᴜʀ Wᴇᴇᴋʟʏ Rᴇᴡᴀʀᴅ.")
                return

            await add_coins(user_id, 250)
            await user_collection.update_one(
                {"id": user_id},
                {"$set": {"last_weekly_claimed": datetime.now()}},
            )
            await update.message.reply_text("Yᴏᴜ Hᴀᴠᴇ Cʟᴀɪᴍᴇᴅ Yᴏᴜʀ Wᴇᴇᴋʟʏ Rᴇᴡᴀʀᴅ. Yᴏᴜ Eᴀʀɴᴇᴅ 𝟸𝟻𝟶 Cᴏɪɴs.")
        else:
            await user_collection.insert_one({"id": user_id, "coins": 250, "last_weekly_claimed": datetime.now()})
            await update.message.reply_text("Yᴏᴜ Hᴀᴠᴇ Cʟᴀɪᴍᴇᴅ Yᴏᴜʀ Wᴇᴇᴋʟʏ Rᴇᴡᴀʀᴅ. Yᴏᴜ Eᴀʀɴᴇᴅ 𝟸𝟻𝟶 Cᴏɪɴs.")
    except Exception as e:
        LOGGER.error(f"Error occurred: {e}")
        await update.message.reply_text(f"Error occurred: {e}")
        



async def remove_coins(update: Update, context: CallbackContext) -> None:
    try:
        if str(update.effective_user.id) not in PARTNER:
            return

        # Parse user_id and coins from the command arguments
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Invalid format. Use: /removecoins <user_id> <amount>")
            return

        user_id = int(args[0])
        try:
            amount = int(args[1])
        except ValueError:
            await update.message.reply_text("Invalid amount. Please provide a valid number.")
            return

        # Retrieve user's wallet
        user = await user_collection.find_one({"id": user_id})

        if not user:
            await update.message.reply_text("User not found.")
            return

        current_balance = user.get("coins", 0)
        new_balance = max(0, current_balance - amount)

        # Update user's balance
        await user_collection.update_one({"id": user_id}, {"$set": {"coins": new_balance}})

        user_mention = f"[{user.get('first_name', 'User')}](tg://user?id={user_id})"

        await update.message.reply_text(f"Successfully removed {amount} coins from user {user_mention}. New balance: {new_balance}")

    except Exception as e:
        LOGGER.error(f"Error occurred: {e}")
        await update.message.reply_text("An error occurred while removing coins. Please try again later.")


async def give_coins(update: Update, context: CallbackContext) -> None:
    try:
        if str(update.effective_user.id) not in PARTNER:
            return

        # Parse user_id and coins from the command arguments
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Invalid format. Use: /givecoins <user_id> <amount>")
            return

        user_id = int(args[0])
        try:
            amount = int(args[1])
        except ValueError:
            await update.message.reply_text("Invalid amount. Please provide a valid number.")
            return

        # Retrieve user's wallet
        user = await user_collection.find_one({"id": user_id})

        if not user:
            # Initialize user's wallet if it doesn't exist
            await user_collection.insert_one({"id": user_id, "coins": amount})
            await update.message.reply_text(f"User {user_id} didn't have a wallet. Initialized with {amount} coins.")
            return

        current_balance = user.get("coins", 0)
        new_balance = current_balance + amount

        # Update user's balance
        await user_collection.update_one({"id": user_id}, {"$set": {"coins": new_balance}})
        user_mention = f"[{user.get('first_name', 'User')}](tg://user?id={user_id})"

        await update.message.reply_text(f"Successfully gave {amount} coins to user {user_mention}. New balance: {new_balance}")

    except Exception as e:
        LOGGER.error(f"Error occurred: {e}")
        await update.message.reply_text("An error occurred while giving coins. Please try again later.")



async def pay_coins(update: Update, context: CallbackContext) -> None:


    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass

    try:
        # Parse the amount from the command arguments
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("Invalid format. Use: /pay <amount>")
            return

        try:
            amount = int(args[0])
            if amount <= 0:
                await update.message.reply_text("Amount must be a positive number.")
                return
        except ValueError:
            await update.message.reply_text("Invalid amount. Please provide a valid number.")
            return

        # Check if the command is a reply to a message
        if not update.message.reply_to_message:
            await update.message.reply_text("Please reply to the message of the user you want to pay.")
            return

        # Extract the recipient's user ID from the replied message
        recipient_id = int(update.message.reply_to_message.from_user.id)
        recipient_first_name = update.message.reply_to_message.from_user.first_name
        recipient_mention = f"[{recipient_first_name}](tg://user?id={recipient_id})"
        
        # Get the sender's user ID
        sender_id = int(update.effective_user.id)

        # Check if sender is trying to pay themselves
        if sender_id == recipient_id:
            await update.message.reply_text("You cannot pay yourself.")
            return

        # Retrieve sender's wallet
        sender_wallet = await user_collection.find_one({"id": sender_id})
        if not sender_wallet:
            await update.message.reply_text("Sender's wallet not found.")
            return

        # Check sender's balance
        sender_balance = sender_wallet.get("coins", 0)
        if sender_balance < amount:
            await update.message.reply_text("Insufficient balance to make the payment.")
            return

        # Retrieve recipient's wallet
        recipient_wallet = await user_collection.find_one({"id": recipient_id})
        if not recipient_wallet:
            await update.message.reply_text("Recipient's wallet not found.")
            return

        # Update sender's balance
        new_sender_balance = sender_balance - amount
        await user_collection.update_one({"id": sender_id}, {"$set": {"coins": new_sender_balance}})

        # Update recipient's balance
        recipient_balance = recipient_wallet.get("coins", 0)
        new_recipient_balance = recipient_balance + amount
        await user_collection.update_one({"id": recipient_id}, {"$set": {"coins": new_recipient_balance}})

        await update.message.reply_text(f"Successfully transferred {amount} coins to user {recipient_mention}.")

    except Exception as e:
        LOGGER.error(f"Error occurred: {e}")
        await update.message.reply_text("An error occurred while processing the payment. Please try again later.")

      

"""async def show_shop(update: Update, context: CallbackContext) -> None:


    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass

    try:
        # Store the user ID in context.user_data
        context.user_data["shop_user_id"] = update.effective_user.id
        
        # Retrieve characters/items from the database
        characters_cursor = shops_collection.find()
        characters = await characters_cursor.to_list(length=None)

        if not characters:
            await update.message.reply_text("🚨 **No characters found in the shop!** 🚨")
            return

        # Get the current character index from context.user_data
        current_index = context.user_data.get("current_index", 0)

        # Display the current character
        character = characters[current_index]
        
        caption_message = f"🛍️ **Welcome to the Luxury Shop!** 🛍️\n\n" \
                         f"🔹 **Character:** {character['name']}\n" \
                         f"🔺 **Anime:** {character['anime']}\n" \
                         f"💡 **Rarity:** {character['rarity']}\n" \
                         f"💸 **Price:** {character['price']} tokens\n" \
                         f"🔢 **ID:** {character['id']}\n" \
                         f"📝 **About:** {character['about']}\n\n" \
                         f"**Unleash Your Inner Otaku and Buy Now! 🎊**"
        keyboard = [
            [InlineKeyboardButton("Buy", callback_data=f"buy_{str(current_index)}")],
            [InlineKeyboardButton("Next", callback_data="next")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_photo(photo=character['img_url'], caption=caption_message, reply_markup=reply_markup, parse_mode='HTML')

        # Update the user's data to store the current index
        context.user_data["current_index"] = (current_index + 1) % len(characters)

        LOGGER.info("Character displayed in the shop.")

    except Exception as e:
        LOGGER.error(f"Error occurred: {e}")
        await update.message.reply_text("An error occurred while displaying the shop. Please try again later.")


async def buy_character(update: Update, context: CallbackContext) -> None:

    query = update.callback_query
    user_id = query.from_user.id
    

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass
    # Check if the user is the one who initiated the shop command
    if user_id != context.user_data.get("shop_user_id"):
        await query.answer("You are not authorized to perform this action.")
        return

    try:
        # Extract character index from callback query
        character_index = int(query.data.split("_")[1])

        # Retrieve character data from the database
        characters_cursor = shops_collection.find()
        characters = await characters_cursor.to_list(length=None)

        if character_index >= len(characters):
            await query.answer("Character not found.")
            return

        character = characters[character_index]

        # Retrieve user data including wallet balance
        user = await user_collection.find_one({"id": user_id})
        if not user:
            await query.answer("User not found.")
            return

        # Check affordability
        price = character["price"]
        current_balance = user.get("tokens", 0)
        if current_balance < price:
            await query.answer(f"Insufficient funds. You need {price - current_balance} more tokens to buy this character.", show_alert=True)
            return

        # Deduct coins from user's wallet
        new_tokens = current_balance - price

        # Add character to user's collection
        character_id = str(character["_id"])
        character_data = {
            "_id": ObjectId(),  # Generate a new ObjectId for the character entry
            "img_url": character["img_url"],
            "name": character["name"],
            "anime": character["anime"],
            "rarity": character["rarity"],
            "id": character["id"],
            "message_id": character.get("message_id")  # Optional, if message_id is available
        }

        if "characters" not in user:
            user["characters"] = []

        user["characters"].append(character_data)

        # Update user data in the database
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"tokens": new_tokens, "characters": user["characters"]}}
        )

        # Confirmation message
        await query.answer("Character purchased successfully.")

    except Exception as e:
        LOGGER.error(f"Error buying character: {e}")
        await query.answer("An error occurred while processing the purchase. Please try again later.", show_alert=True)


async def next_item(update: Update, context: CallbackContext) -> None:

    user_id = update.callback_query.from_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass

    try:
        # Check if the user is the one who initiated the shop command
        if update.callback_query.from_user.id != context.user_data.get("shop_user_id"):
            await update.callback_query.answer("You are not authorized to perform this action.")
            return
        
        # Retrieve characters/items from the database
        characters_cursor = shops_collection.find()
        characters = await characters_cursor.to_list(length=None)

        if not characters:
            await update.callback_query.answer("No characters found in the shop.")
            return

        # Get the current character index from context.user_data
        current_index = context.user_data.get("current_index", 0)

        # Calculate the index of the next character
        next_index = (current_index + 1) % len(characters)

        # Display the next character
        character = characters[next_index]
        caption_message = f"🛍️ **Welcome to the Luxury Shop!** 🛍️\n\n" \
                         f"🔹 **Character:** {character['name']}\n" \
                         f"🔺 **Anime:** {character['anime']}\n" \
                         f"💡 **Rarity:** {character['rarity']}\n" \
                         f"💸 **Price:** {character['price']} tokens\n" \
                         f"🔢 **ID:** {character['id']}\n" \
                         f"📝 **About:** {character['about']}\n\n" \
                         f"**Unleash Your Inner Otaku and Buy Now! 🎊**"
        keyboard = [
            [InlineKeyboardButton("Buy", callback_data=f"buy_{str(next_index)}")],
            [InlineKeyboardButton("Next", callback_data="next")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Update the user's data to store the current index
        context.user_data["current_index"] = next_index

        await update.callback_query.message.edit_media(
            media=InputMediaPhoto(media=character['img_url'], caption=caption_message),
            reply_markup=reply_markup
        )

        await update.callback_query.answer()  # Acknowledge the callback

        LOGGER.info("Next item displayed in the shop.")

    except Exception as e:
        LOGGER.error(f"Error occurred: {e}")
        await update.callback_query.answer("An error occurred while displaying the next item. Please try again later.")"""


async def bonus_coins(update: Update, context: CallbackContext) -> None:

    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass

    if not await is_member(user_id):
        group_link = "https://t.me/blade_x_community"  # Replace with the actual group invite link
        message = (
            "You need to be a member of our exclusive group to use this command.\n"
            "Join now and explore the amazing features awaiting you!\n\n"
        )
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✨ Join the Group ✨", url=group_link)]]
        )
        await update.message.reply_text(message, reply_markup=reply_markup)
        return
          
    try:

        # Retrieve user ID
        user_id = update.effective_user.id
        
        # Check if user has claimed bonus today
        last_bonus_time = await user_collection.find_one({"id": user_id}, projection={"last_bonus_time": 1})
        if last_bonus_time and (datetime.now() - last_bonus_time.get("last_bonus_time", datetime.min)) < timedelta(days=1):
            await update.message.reply_text("Yᴏᴜ Hᴀᴠᴇ Aʟʀᴇᴀᴅʏ Cʟᴀɪᴍᴇᴅ Yᴏᴜʀ Dᴀɪʟʏ Rᴇᴡᴀʀᴅ")
            return

        # Add bonus coins to the user's account
        await add_coins(user_id, 1000)

        # Update last bonus time for the user
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"last_bonus_time": datetime.now()}},
            upsert=True
        )

        # Send a message confirming the bonus coins were added
        await update.message.reply_text("🎉 Cᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs! 🎉\n\nYᴏᴜ'ᴠᴇ Cʟᴀɪᴍᴇᴅ Yᴏᴜʀ Dᴀɪʟʏ Bᴏɴᴜs Oғ 1000 Cᴏɪɴs! EɴJᴏʏ")

    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")


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



application.add_handler(CallbackQueryHandler(next_item, pattern="^next$"))
application.add_handler(CallbackQueryHandler(buy_character, pattern=r'^buy_\d+$'))
application.add_handler(CommandHandler(['Shop', 'shopmenu'], show_shop))
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

