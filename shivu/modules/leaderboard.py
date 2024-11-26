import asyncio 
import os
import random
import html
import logging
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Application
from shivu import (application, PHOTO_URL, OWNER_ID, user_collection, 
                   top_global_groups_collection, group_user_totals_collection, 
                   sudo_users as SUDO_USERS)
from cachetools import TTLCache
from shivu import PARTNER, ban_collection


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for user and group data
USER_CACHE = TTLCache(maxsize=1000, ttl=3600)  # Cache with 1-hour TTL
GROUP_CACHE = TTLCache(maxsize=100, ttl=3600)  # Cache with 1-hour TTL

# Function to create necessary indexes
async def create_indexes():
    await top_global_groups_collection.create_index([("count", -1)])
    await group_user_totals_collection.create_index([("group_id", 1), ("count", -1)])
    await user_collection.create_index([("characters", 1)])

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
        # If the user is banned, do nothing
        return
    else:
        pass

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
        # If the user is banned, do nothing
        return
    else:
        pass

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

# Fetch top 10 users globally
async def leaderboard(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass


    try:
        leaderboard_data = USER_CACHE.get('global_leaderboard')
        if not leaderboard_data:
            cursor = user_collection.find({}, {"username": 1, "first_name": 1, "characters": 1})
            leaderboard_data = await cursor.to_list(length=None)
            leaderboard_data.sort(key=lambda x: len(x.get('characters', [])), reverse=True)
            leaderboard_data = leaderboard_data[:10]
            USER_CACHE['global_leaderboard'] = leaderboard_data  # Cache the data

        leaderboard_message = "<b>TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"
        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
            character_count = len(user.get('characters', []))
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'
        
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

# Send user documents (only for sudo users)
async def send_users_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in PARTNER:
        await update.message.reply_text('Only for sudo users...')
        return
    try:
        cursor = user_collection.find({})
        users = []
        async for document in cursor:
            users.append(document)
        user_list = "\n".join(user['first_name'] for user in users)
        with open('users.txt', 'w') as f:
            f.write(user_list)
        with open('users.txt', 'rb') as f:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
        os.remove('users.txt')
    except Exception as e:
        logger.error(f"Error in send_users_document: {e}")
        await update.message.reply_text("An error occurred while sending user documents.")

# Send group documents (only for sudo users)
async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in PARTNER:
        await update.message.reply_text('Only for sudo users...')
        return
    try:
        cursor = top_global_groups_collection.find({})
        groups = []
        async for document in cursor:
            groups.append(document)
        group_list = "\n".join(group['group_name'] for group in groups)
        with open('groups.txt', 'w') as f:
            f.write(group_list)
        with open('groups.txt', 'rb') as f:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=f)
        os.remove('groups.txt')
    except Exception as e:
        logger.error(f"Error in send_groups_document: {e}")
        await update.message.reply_text("An error occurred while sending group documents.")

# Initialize the bot with handlers
application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))
application.add_handler(CommandHandler('top', leaderboard, block=False))


