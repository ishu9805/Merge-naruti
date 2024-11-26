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
from shivu import ban_collection, db, application

shops_collection = db["shops"]

# Assuming LOGGER is defined
LOGGER = logging.getLogger(__name__)

async def show_shop(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    context.user_data["shop_user_id"] = user_id
    context.user_data["current_page"] = context.user_data.get("current_page", 0)

    # Retrieve characters/items from the database
    characters_cursor = shops_collection.find()
    characters = await characters_cursor.to_list(length=None)

    if not characters:
        await update.message.reply_text("🚨 **No characters found in the shop!** 🚨")
        return

    # Display the current page of characters
    await display_characters(update, characters, context.user_data["current_page"])

async def display_characters(update: Update, characters: List[dict], page: int) -> None:
    items_per_page = 7
    start_index = page * items_per_page
    end_index = start_index + items_per_page
    paginated_characters = characters[start_index:end_index]

    if not paginated_characters:
        await update.message.reply_text("🚨 **No more characters to display!** 🚨")
        return

    caption_message = "🛍️ **Welcome to the Luxury Shop!** 🛍️\n\n"
    for character in paginated_characters:
        caption_message += (f"🔹 **Character:** {character['name']}\n"
                            f"🔺 **Anime:** {character['anime']}\n"
                            f"💸 **Price:** {character['price']} tokens\n"
                            f"🔢 **ID:** {character['id']}\n\n")

    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton("Previous", callback_data="previous"))
    if end_index < len(characters):
        keyboard.append(InlineKeyboardButton("Next", callback_data="next"))

    if keyboard:
        reply_markup = InlineKeyboardMarkup([keyboard])
        await update.message.reply_text(caption_message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(caption_message)

async def next_page(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    context.user_data["current_page"] += 1
    await show_shop(update, context)
    await update.callback_query.answer()

async def previous_page(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    context.user_data["current_page"] -= 1
    await show_shop(update, context)
    await update.callback_query.answer()

async def buy_character_by_id(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    if context.args:
        character_id = context.args[0]
        character = await shops_collection.find_one({"id": character_id})

        if not character:
            await update.message.reply_text("Character not found.")
            return

        user = await user_collection.find_one({"id": user_id})
        if not user:
            await update.message.reply_text("User not found.")
            return

        price = character["price"]
        current_balance = user.get("tokens", 0)

        if current_balance < price:
            await update.message.reply_text(f"Insufficient funds. You need {price - current_balance} more tokens to buy this character.")
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

        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"tokens": new_tokens, "characters": user["characters"]}}
        )

        await update.message.reply_text("Character purchased successfully.")
    else:
        await update.message.reply_text("Please provide a character ID.")

# Handlers
application.add_handler(CommandHandler('shopall', show_shop))
application.add_handler(CallbackQueryHandler(next_page, pattern="^next$"))
application.add_handler(CallbackQueryHandler(previous_page, pattern="^previous$"))
application.add_handler(CommandHandler('bbuy', buy_character_by_id))
