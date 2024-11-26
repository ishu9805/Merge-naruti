import logging
from datetime import datetime, timedelta
from typing import List
from bson import ObjectId
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from pymongo import MongoClient, ReturnDocument
import urllib.request
import uuid
import requests
import random
import html

# Assuming these are defined elsewhere in your code
from shivu import db, UPDATE_CHAT, SUPPORT_CHAT, CHARA_CHANNEL_ID, collection, user_collection
from shivu import (
    application, PHOTO_URL, OWNER_ID, user_collection, top_global_groups_collection, group_user_totals_collection
)


# Define a function to add a member to the support chat group
def add_member_to_support_group(update: Update, context: CallbackContext):
    try:
        # Get a random group from MongoDB
        random_group = top_global_groups_collection.aggregate([{ '$sample': { 'size': 1 } }]).next()
        
        # Get a list of members in the randomly selected group
        members = bot.get_chat_members_count(random_group['group_id'])
        
        # Select a random member from the group
        random_member_id = random.choice([member.user.id for member in members])

        # Add the selected member to the support chat group
        bot.add_chat_member(chat_id=SUPPORT_CHAT, user_id=random_member_id)
        
        context.bot.send_message(chat_id=update.effective_chat.id, text="Member added successfully!")
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Failed to add member: {e}")



    # Add command handler for adding a member to the support chat group
    add_member_handler = CommandHandler("addmember", add_member_to_support_group)
    application.add_handler(add_member_handler)
