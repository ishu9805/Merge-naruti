import asyncio
import os
import random
import html
import logging
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Application
from shivu import (
    application, PHOTO_URL, OWNER_ID, user_collection, 
    top_global_groups_collection, group_user_totals_collection, 
    sudo_users as SUDO_USERS, PARTNER, ban_collection
)
from cachetools import TTLCache

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for user and group data
USER_CACHE = TTLCache(maxsize=1000, ttl=3600)  # Cache with 1-hour TTL
GROUP_CACHE = TTLCache(maxsize=100, ttl=3600)  # Cache with 1-hour TTL

# Function to create necessary indexes
async def create_indexes():
    await user_collection.create_index([("total_characters", -1)])
    await top_global_groups_collection.create_index([("count", -1)])
    await group_user_totals_collection.create_index([("group_id", 1), ("count", -1)])

# Fetch user data from cache or DB
async def get_user_data(user_id: int):
    if user_id in USER_CACHE:
        return USER_CACHE[user_id]
    user = await user_collection.find_one({"id": user_id})
    if user:
        USER_CACHE[user_id] = user
    return user

# Fetch group data from cache or DB
async def get_group_data(group_id: int):
    if group_id in GROUP_CACHE:
        return GROUP_CACHE[group_id]
    group = await group_user_totals_collection.find_one({"group_id": group_id})
    if group:
        GROUP_CACHE[group_id] = group
    return group

# Fetch top 10 global groups
async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return  # Do nothing if the user is banned

    try:
        leaderboard_data = GROUP_CACHE.get('global_leaderboard')
        if not leaderboard_data:
            cursor = top_global_groups_collection.find({}, {"group_name": 1, "count": 1}).sort("count", -1).limit(10)
            leaderboard_data = await cursor.to_list(length=10)
            GROUP_CACHE['global_leaderboard'] = leaderboard_data  # Cache the data

        leaderboard_message = "<b>TOP 10 GROUPS WHO GUESSED MOST CHARACTERS</b>\n\n"
        for i, group in enumerate(leaderboard_data, start=1):
            group_name = html.escape(group.get('group_name', 'Unknown'))[:15] + '...'
            count = group['count']
            leaderboard_message += f'{i}. <b>{group_name}</b> ➾ <b>{count}</b>\n'
        
        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in global_leaderboard: {e}")
        await update.message.reply_text("An error occurred while generating the leaderboard.")

# Fetch top 10 users in a specific group
async def ctop(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return  # Do nothing if the user is banned

    try:
        chat_id = update.effective_chat.id
        leaderboard_data = GROUP_CACHE.get(f'group_leaderboard_{chat_id}')
        if not leaderboard_data:
            cursor = group_user_totals_collection.find({"group_id": chat_id}, {"username": 1, "first_name": 1, "count": 1}).sort("count", -1).limit(10)
            leaderboard_data = await cursor.to_list(length=10)
            GROUP_CACHE[f'group_leaderboard_{chat_id}'] = leaderboard_data  # Cache the data

        leaderboard_message = "<b>TOP 10 USERS WHO GUESSED CHARACTERS MOST TIME IN THIS GROUP..</b>\n\n"
        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
            character_count = user['count']
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'
        
        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in ctop: {e}")
        await update.message.reply_text("An error occurred while generating the group leaderboard.")

# Fetch top 10 users globally (using total_characters field)
async def leaderboard(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return  # Do nothing if the user is banned

    try:
        leaderboard_data = USER_CACHE.get('global_leaderboard')
        if not leaderboard_data:
            cursor = user_collection.find({}, {"username": 1, "first_name": 1, "total_characters": 1}).sort("total_characters", -1).limit(10)
            leaderboard_data = await cursor.to_list(length=10)
            USER_CACHE['global_leaderboard'] = leaderboard_data  # Cache the data

        leaderboard_message = "<b>TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"
        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
            total_characters = user.get('total_characters', 0)
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{total_characters}</b>\n'

        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in leaderboard: {e}")
        await update.message.reply_text("An error occurred while generating the user leaderboard.")

# Display statistics (only for the owner)
async def stats(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in PARTNER:
        return
    try:
        user_count = await user_collection.estimated_document_count()
        group_count = await group_user_totals_collection.count_documents({})
        await update.message.reply_text(f'Total Users: {user_count}\nTotal Groups: {group_count}')
    except Exception as e:
        logger.error(f"Error in stats: {e}")
        await update.message.reply_text("An error occurred while fetching statistics.")

# Initialize the bot with handlers
application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('top', leaderboard, block=False))


