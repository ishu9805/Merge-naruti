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

application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))
