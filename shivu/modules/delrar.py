import logging
from telegram import Update
from telegram.ext import CallbackContext
from telegram import Update
from itertools import groupby
import math
from html import escape 
import random

from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import UPDATE_CHAT, SUPPORT_CHAT, CHARA_CHANNEL_ID, required_group_id, PHOTO_URL, OWNER_ID, PARTNER
from shivu import (
    collectionps as collection,
    top_global_groups_collectionps as top_global_groups_collection,
    group_user_totals_collectionps as group_user_totals_collection,
    user_collectionps as user_collection,
    user_totals_collectionps as user_totals_collection,
    shivuups as shivuu,
    shivuups as app,
    applicationps as application,
    SUPPORT_CHATps as SUPPORT,
    UPDATE_CHATps as UPDATE_CHAT,
    dbps as db,
    pmusersps as pmusers,
    ban_collectionps as ban_collection,
    user_countps as user_count, 
    chat_dataps as chat_data,
)
# Assuming rarity_map is predefined
rarity_map = {
    1: "⚪️ Common", 
    2: "🟣 Rare", 
    3: "🟡 Legendary", 
    4: "🟢 Medium", 
    5: "💮 Special Edition", 
    6: "🔮 Limited Edition", 
    7: "💸 Premium Edition", 
    8: "🌤 Summer", 
    9: "🎐 Celestial", 
    10: "❄️ Winter", 
    11: "💝 Valentine", 
    12: "🎃 Halloween", 
    13: "🎄 Christmas Special"
}

async def delete_rarity_characters(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in PARTNER:
        await update.message.reply_text('Ask My Owner...')
        return

    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text('Incorrect format. Please use: /delrar rarity_number user_id')
            return

        rarity_number = int(args[0])
        user_id = int(args[1])

        if rarity_number not in rarity_map:
            await update.message.reply_text('Invalid rarity number.')
            return

        rarity_to_delete = rarity_map[rarity_number]

        # Fetch the user's character list
        user = await user_collection.find_one({'id': user_id})
        if not user:
            await update.message.reply_text('User not found.')
            return

        # Filter out characters with the specified rarity
        original_character_count = len(user.get('characters', []))
        updated_characters = [character for character in user['characters'] if character['rarity'] != rarity_to_delete]
        removed_count = original_character_count - len(updated_characters)

        # Update the user's collection with the filtered list
        await user_collection.update_one({'id': user_id}, {'$set': {'characters': updated_characters}})

        await update.message.reply_text(f'{removed_count} characters with rarity "{rarity_to_delete}" have been deleted from user with ID {user_id}.')

    except ValueError:
        await update.message.reply_text('Invalid rarity number or user ID.')
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        await update.message.reply_text(f'An error occurred: {str(e)}')


import logging
from telegram import Update
from telegram.ext import CallbackContext
from collections import defaultdict

async def delete_rarities_duplicates(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in PARTNER:
        await update.message.reply_text('Ask My Owner...')
        return

    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text('Incorrect format. Please use: /delrar rarity_number user_id')
            return

        rarity_number = int(args[0])
        user_id = int(args[1])

        if rarity_number not in rarity_map:
            await update.message.reply_text('Invalid rarity number.')
            return

        rarity_to_delete = rarity_map[rarity_number]

        # Fetch the user's character list
        user = await user_collection.find_one({'id': user_id})
        if not user:
            await update.message.reply_text('User not found.')
            return

        # Count occurrences of each character
        character_counts = defaultdict(int)
        for character in user['characters']:
            if character['rarity'] == rarity_to_delete:
                character_counts[character['id']] += 1

        # Filter out duplicates, but keep one of each
        characters_to_keep = []
        for character in user['characters']:
            if character['rarity'] == rarity_to_delete:
                if character_counts[character['id']] > 1:
                    character_counts[character['id']] -= 1
                    continue  # Skip this duplicate, only one should remain
            characters_to_keep.append(character)

        removed_count = len(user['characters']) - len(characters_to_keep)

        # Update the user's collection with the filtered list
        await user_collection.update_one({'id': user_id}, {'$set': {'characters': characters_to_keep}})

        await update.message.reply_text(f'{removed_count} duplicate characters with rarity "{rarity_to_delete}" have been deleted from user with ID {user_id}. One of each character has been retained.')

    except ValueError:
        await update.message.reply_text('Invalid rarity number or user ID.')
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        await update.message.reply_text(f'An error occurred: {str(e)}')

# Add the command handler to the application
application.add_handler(CommandHandler("delrarone", delete_rarities_duplicates))

# Add the command handler to the application
application.add_handler(CommandHandler("delrar", delete_rarity_characters))


