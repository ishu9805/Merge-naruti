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
from telegram.ext import CallbackContext
from bson import ObjectId
from shivu import shops_collection, user_collection, ban_collection
import logging
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)

async def show_shop(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    try:
        context.user_data["shop_user_id"] = update.effective_user.id

        characters_cursor = shops_collection.find()
        characters = await characters_cursor.to_list(length=None)

        # Filter out characters with zero quantity
        characters = [char for char in characters if char['quantity'] > 0]

        if not characters:
            await update.message.reply_text("\ud83d\udea8 **No characters found in the shop!** \ud83d\udea8")
            return

        current_index = context.user_data.get("current_index", 0)
        character = characters[current_index]
        
        caption_message = f"\ud83d\uded2 **Welcome to the Luxury Shop!** \ud83d\uded2\n\n" \
                         f"\ud83d\udd39 **Character:** {character['name']}\n" \
                         f"\u25b3 **Anime:** {character['anime']}\n" \
                         f"\ud83d\udca1 **Rarity:** {character['rarity']}\n" \
                         f"\ud83d\udcb8 **Price:** {character['price']} tokens\n" \
                         f"\u2795 **Quantity Available:** {character['quantity']}\n\n" \
                         f"**Unleash Your Inner Otaku and Buy Now! \ud83c\df89**"
                         
        keyboard = [
            [InlineKeyboardButton("Buy", callback_data=f"buy_{str(current_index)}")],
            [InlineKeyboardButton("Next", callback_data="next")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_photo(photo=character['img_url'], caption=caption_message, reply_markup=reply_markup, parse_mode='Markdown')

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
        return

    if user_id != context.user_data.get("shop_user_id"):
        await query.answer("You are not authorized to perform this action.")
        return

    try:
        character_index = int(query.data.split("_")[1])

        characters_cursor = shops_collection.find()
        characters = await characters_cursor.to_list(length=None)

        # Filter out characters with zero quantity
        characters = [char for char in characters if char['quantity'] > 0]

        if character_index >= len(characters):
            await query.answer("Character not found.")
            return

        character = characters[character_index]

        keyboard = [
            [InlineKeyboardButton("Confirm Purchase", callback_data=f"confirm_{str(character_index)}")],
            [InlineKeyboardButton("Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"Are you sure you want to buy **{character['name']}** for {character['price']} tokens?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        await query.answer()

    except Exception as e:
        LOGGER.error(f"Error in buy_character: {e}")
        await query.answer("An error occurred. Please try again later.", show_alert=True)

async def confirm_purchase(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    try:
        character_index = int(query.data.split("_")[1])

        characters_cursor = shops_collection.find()
        characters = await characters_cursor.to_list(length=None)

        # Filter out characters with zero quantity
        characters = [char for char in characters if char['quantity'] > 0]

        if character_index >= len(characters):
            await query.answer("Character not found.")
            return

        character = characters[character_index]
        user = await user_collection.find_one({"id": user_id})

        if not user:
            await query.answer("User not found.", show_alert=True)
            return

        price = character["price"]
        current_balance = user.get("tokens", 0)

        if current_balance < price:
            await query.answer(f"Insufficient funds. You need {price - current_balance} more tokens.", show_alert=True)
            return

        new_tokens = current_balance - price
        character_data = {
            "_id": ObjectId(),
            "img_url": character["img_url"],
            "name": character["name"],
            "anime": character["anime"],
            "rarity": character["rarity"],
            "id": character["id"]
        }

        if "characters" not in user:
            user["characters"] = []

        user["characters"].append(character_data)

        # Decrement the quantity of the character
        if character['quantity'] > 1:
            await shops_collection.update_one(
                {"id": character["id"]},
                {"$inc": {"quantity": -1}}
            )
        else:
            await shops_collection.delete_one({"id": character["id"]})

        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"tokens": new_tokens, "characters": user["characters"]}}
        )

        keyboard = [[InlineKeyboardButton("Reopen Shop", callback_data="reopen_shop")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"Congratulations! You purchased **{character['name']}** for {price} tokens.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        await query.answer("Purchase successful.")

    except Exception as e:
        LOGGER.error(f"Error in confirm_purchase: {e}")
        await query.answer("An error occurred while processing the purchase. Please try again later.", show_alert=True)

async def reopen_shop(update: Update, context: CallbackContext) -> None:
    await show_shop(update, context)

# Handlers
application.add_handler(CallbackQueryHandler(buy_character, pattern=r'^buy_\d+$'))
application.add_handler(CallbackQueryHandler(confirm_purchase, pattern=r'^confirm_\d+$'))
application.add_handler(CallbackQueryHandler(reopen_shop, pattern=r'^reopen_shop$'))
application.add_handler(CommandHandler(['Shop', 'shopmenu'], show_shop))



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
