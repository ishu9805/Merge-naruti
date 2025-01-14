from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CallbackContext
from bson import ObjectId
from shivu import shops_collection, user_collection, ban_collection
import logging
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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CallbackContext
from bson import ObjectId
from shivu import shops_collection, user_collection, ban_collection
import logging


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from bson import ObjectId
from shivu import shops_collection, user_collection, ban_collection, application
from pymongo import ReturnDocument
import logging

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)

# Display the shop
async def show_shop(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    try:
        characters_cursor = shops_collection.find()
        characters = await characters_cursor.to_list(length=None)

        # Filter characters with non-zero quantity
        characters = [char for char in characters if char['quantity'] > 0]
        if not characters:
            await update.message.reply_text("🚨 **No characters found in the shop!** 🚨")
            return

        # Initialize shop data in user context
        context.user_data["shop_characters"] = characters
        context.user_data["current_index"] = 0

        await send_shop_item(update, context)

    except Exception as e:
        LOGGER.error(f"Error occurred in shop: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")

# Send a specific character item based on the current index
async def send_shop_item(update, context, edit=False) -> None:
    characters = context.user_data.get("shop_characters", [])
    current_index = context.user_data.get("current_index", 0)

    if not characters or current_index >= len(characters):
        return

    character = characters[current_index]
    caption_message = (
        f"🛍️ **Luxury Shop** 🛍️\n\n"
        f"🔹 **Character:** {character['name']}\n"
        f"🔺 **Anime:** {character['anime']}\n"
        f"💡 **Rarity:** {character['rarity']}\n"
        f"💸 **Price:** {character['price']} tokens\n"
        f"🔢 **ID:** {character['id']}\n"
        f"🔢 **Quantity Available:** {character['quantity']}\n\n"
        f"**Unleash Your Inner Otaku and Buy Now! 🎊**"
    )

    keyboard = [
        [InlineKeyboardButton("Buy", callback_data=f"buy_{current_index}")],
        [
            InlineKeyboardButton("Previous", callback_data="previous"),
            InlineKeyboardButton("Next", callback_data="next"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.message.edit_media(
            InputMediaPhoto(media=character['img_url'], caption=caption_message, parse_mode='Markdown'),
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_photo(
            photo=character['img_url'],
            caption=caption_message,
            reply_markup=reply_markup,
            parse_mode='Markdown',
        )

# Handle navigation (Next/Previous buttons)
async def navigate_shop(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    action = query.data

    try:
        characters = context.user_data.get("shop_characters", [])
        current_index = context.user_data.get("current_index", 0)

        if not characters:
            await query.answer("No characters available.")
            return

        if action == "next":
            context.user_data["current_index"] = (current_index + 1) % len(characters)
        elif action == "previous":
            context.user_data["current_index"] = (current_index - 1) % len(characters)

        await send_shop_item(update, context, edit=True)
        await query.answer()

    except Exception as e:
        LOGGER.error(f"Error in navigation: {e}")
        await query.answer("An error occurred. Please try again later.", show_alert=True)

# Handle Buy button click
async def buy_character(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    try:
        # Get character index
        character_index = int(query.data.split("_")[1])
        characters = context.user_data.get("shop_characters", [])

        if character_index >= len(characters):
            await query.answer("Character not found.")
            return

        character = characters[character_index]

        # Ask for confirmation
        caption_message = (
            f"🛍️ **Confirm Purchase!** 🛍️\n\n"
            f"🔹 **Character:** {character['name']}\n"
            f"💸 **Price:** {character['price']} tokens\n\n"
            f"Do you want to proceed?"
        )
        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data=f"confirm_{character_index}")],
            [InlineKeyboardButton("Cancel", callback_data="cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_caption(caption_message, reply_markup=reply_markup, parse_mode='Markdown')
        await query.answer()

    except Exception as e:
        LOGGER.error(f"Error in buy button: {e}")
        await query.answer("An error occurred. Please try again later.", show_alert=True)

# Confirm purchase
async def confirm_purchase(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    try:
        # Get character index
        character_index = int(query.data.split("_")[1])
        characters = context.user_data.get("shop_characters", [])

        if character_index >= len(characters):
            await query.answer("Character not found.")
            return

        character = characters[character_index]
        user = await user_collection.find_one({"id": user_id})

        if not user:
            await query.answer("User not found.")
            return

        # Check user's token balance
        price = character["price"]
        current_balance = user.get("tokens", 0)
        if current_balance < price:
            await query.answer(f"Insufficient funds. You need {price - current_balance} more tokens.", show_alert=True)
            return

        # Deduct price and add character
        new_tokens = current_balance - price
        character_data = {
            "_id": ObjectId(),
            "img_url": character["img_url"],
            "name": character["name"],
            "anime": character["anime"],
            "rarity": character["rarity"],
            "id": character["id"],
        }
        if "characters" not in user:
            user["characters"] = []
        user["characters"].append(character_data)

        # Update quantities
        if character['quantity'] > 1:
            await shops_collection.update_one(
                {"id": character["id"]}, {"$inc": {"quantity": -1}}
            )
        else:
            await shops_collection.delete_one({"id": character["id"]})

        await user_collection.update_one(
            {"id": user_id}, {"$set": {"tokens": new_tokens, "characters": user["characters"]}}
        )

        await query.answer("Purchase successful!")
        await query.message.edit_caption(f"🎉 **Character purchased:** {character['name']}!", parse_mode='Markdown')

    except Exception as e:
        LOGGER.error(f"Error in confirm button: {e}")
        await query.answer("An error occurred. Please try again later.", show_alert=True)

# Cancel action
async def cancel_action(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer("Purchase canceled.")
    await query.message.edit_caption("❌ **Purchase canceled.**", parse_mode='Markdown')

# Add handlers
application.add_handler(CommandHandler(['shop', 'shopmenu'], show_shop))
application.add_handler(CallbackQueryHandler(navigate_shop, pattern=r'^(next|previous)$'))
application.add_handler(CallbackQueryHandler(buy_character, pattern=r'^buy_\d+$'))
application.add_handler(CallbackQueryHandler(confirm_purchase, pattern=r'^confirm_\d+$'))
application.add_handler(CallbackQueryHandler(cancel_action, pattern=r'^cancel$'))




async def add_character_to_shop(update: Update, context: CallbackContext) -> None:
    try:
        # Check if the user is authorized (you can implement your own logic here)
        if str(update.effective_user.id) not in PARTNER:
            await update.message.reply_text("You are not authorized to use this command.")
            return

        # Check if the correct number of arguments is provided
        if len(context.args) != 3:
            await update.message.reply_text("Usage: /addsh <id> <price> <quantity>")
            return

        character_id = context.args[0]
        price = int(context.args[1])
        quantity = int(context.args[2])

        # Retrieve character data from the original collection
        character = await collection.find_one({"id": character_id})

        if not character:
            await update.message.reply_text("Character not found in the original collection.")
            return

        # Prepare the character data to be added to the shop
        character_data = {
            "name": character["name"],
            "anime": character["anime"],
            "rarity": character["rarity"],
            "price": price,
            "id": character["id"],
            "img_url": character["img_url"],
            "quantity": quantity
        }

        # Insert the character into the shops_collection
        await shops_collection.insert_one(character_data)

        await update.message.reply_text(f"Character '{character['name']}' added to the shop with price {price} and quantity {quantity}.")

    except Exception as e:
        LOGGER.error(f"Error occurred while adding character to shop: {e}")
        await update.message.reply_text("An error occurred while adding the character to the shop. Please try again later.")

# Add the command handler to your application
application.add_handler(CommandHandler("addsh", add_character_to_shop))
