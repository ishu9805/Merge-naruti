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

        if not characters:
            await update.message.reply_text("🚨 **No characters found in the shop!** 🚨")
            return

        current_index = context.user_data.get("current_index", 0)
        character = characters[current_index]
        
        caption_message = f"🛍️ **Welcome to the Luxury Shop!** 🛍️\n\n" \
                         f"🔹 **Character:** {character['name']}\n" \
                         f"🔺 **Anime:** {character['anime']}\n" \
                         f"💡 **Rarity:** {character['rarity']}\n" \
                         f"💸 **Price:** {character['price']} tokens\n" \
                         f"🔢 **ID:** {character['id']}\n\n" \
                         f"**Unleash Your Inner Otaku and Buy Now! 🎊**"
                         
        keyboard = [
            [InlineKeyboardButton("Buy", callback_data=f"buy_{str(current_index)}")],
            [InlineKeyboardButton("Next", callback_data="next")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_photo(photo=character['img_url'], caption=caption_message, reply_markup=reply_markup, parse_mode='HTML')

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

        if character_index >= len(characters):
            await query.answer("Character not found.")
            return

        character = characters[character_index]

        user = await user_collection.find_one({"id": user_id})
        if not user:
            await query.answer("User  not found.")
            return

        price = character["price"]
        current_balance = user.get("tokens", 0)
        if current_balance < price:
            await query.answer(f"Insufficient funds. You need {price - current_balance} more tokens to buy this character.", show_alert=True)
            return

        new_tokens = current_balance - price

        character_data = {
            "_id": ObjectId(),
            "img_url": character["img_url"],
            "name": character["name"],
            "anime": character["anime"],
            "rarity": character["rarity"],
            "id": character["id"],
            "message_id": character.get("message_id")
        }

        if "characters" not in user:
            user["characters"] = []

        user["characters"].append(character_data)

        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"tokens": new_tokens, "characters": user["characters"]}}
        )

        await query.answer("Character purchased successfully.")

    except Exception as e:
        LOGGER.error(f"Error buying character: {e}")
        await query.answer("An error occurred while processing the purchase. Please try again later.", show_alert=True)

async def next_item(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    try:
        if update.callback_query.from_user.id != context.user_data.get("shop_user_id"):
            await update.callback_query.answer("You are not authorized to perform this action.")
            return
        
        characters_cursor = shops_collection.find()
        characters = await characters_cursor.to_list(length=None)

        if not characters:
            await update.callback_query.answer("No characters found in the shop.")
            return

        current_index = context.user_data.get("current_index", 0)
        next_index = (current_index + 1) % len(characters)

        character = characters[next_index]
        caption_message = f"🛍️ **Welcome to the Luxury Shop!** 🛍️\n\n" \
                         f"🔹 **Character:** {character['name']}\n" \
                         f"🔺 **Anime:** {character['anime']}\n" \
                         f"💡 **Rarity:** {character['rarity']}\n" \
                         f"💸 **Price:** {character['price']} tokens\n" \
                         f"🔢 **ID:** {character['id']}\n\n" \
                         f"**Unleash Your Inner Otaku and Buy Now! 🎊**"
                         
        keyboard = [
            [InlineKeyboardButton("Buy", callback_data=f"buy_{str(next_index)}")],
            [InlineKeyboardButton("Next", callback_data="next")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data["current_index"] = next_index

        await update.callback_query.message.edit_media(
            media=InputMediaPhoto(media=character['img_url'], caption=caption_message),
            reply_markup=reply_markup
        )

        await update.callback_query.answer()

        LOGGER.info("Next item displayed in the shop.")

    except Exception as e:
        LOGGER.error(f"Error occurred: {e}")
        await update.callback_query.answer("An error occurred while displaying the next item. Please try again later.")



application.add_handler(CallbackQueryHandler(next_item, pattern="^next$"))
application.add_handler(CallbackQueryHandler(buy_character, pattern=r'^buy_\d+$'))
application.add_handler(CommandHandler(['Shop', 'shopmenu'], show_shop))
      
      # Additional functions and handlers can be added here as needed.
