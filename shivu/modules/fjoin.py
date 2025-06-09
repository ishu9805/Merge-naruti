from functools import wraps
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from pymongo import MongoClient
import logging


from telegram import Update
from telegram.ext import CallbackContext
from typing import Callable, Any
from shivu import applicationps as application

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant

def check_membership(group_id: int = -1002606804832, channel_id: int = -1002171454204):
    def decorator(func):
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args, **kwargs):
            user_id = message.from_user.id
            try:
                # Check group membership
                group_member = await client.get_chat_member(group_id, user_id)
                # Check channel membership
                #channel_member = await client.get_chat_member(channel_id, user_id)
                
                if group_member.status not in ("left", "kicked"): # and channel_member.status not in ("left", "kicked"):
                    return await func(client, message, *args, **kwargs)
            except UserNotParticipant:
                pass
            
            # Get invite links
            try:
                group_invite = await client.export_chat_invite_link(group_id)
                #channel_invite = await client.export_chat_invite_link(channel_id)
            except Exception as e:
                await message.reply_text("⚠️ Could not generate invite links. Please contact admin.")
                return

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Join Group", url=group_invite),
                        #InlineKeyboardButton("Join Channel", url=channel_invite)
                    ],
                    [InlineKeyboardButton("✅ I Joined", callback_data="check_joined")]
                ]
            )
            
            await message.reply_text(
                "⚠️ To use this command, please join our group and channel first!",
                reply_markup=keyboard
            )
        
        return wrapper
    return decorator

# Callback handler
@Client.on_callback_query(filters.regex("^check_joined$"))
async def check_joined_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    group_id = -1002606804832
    channel_id = -1002171454204
    
    try:
        # Check both group and channel membership
        group_member = await client.get_chat_member(group_id, user_id)
        #channel_member = await client.get_chat_member(channel_id, user_id)
        
        if group_member.status not in ("left", "kicked"): # and channel_member.status not in ("left", "kicked"):
            await callback_query.message.edit_text(
                "✅ Verification successful! You can now use the bot commands.",
                reply_markup=None  # Remove the buttons
            )
            return
    except Exception as e:
        print(f"Error checking membership: {e}")

    await callback_query.answer(
        "You need to join both the group and channel to continue!",
        show_alert=True
    )



from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram.error import BadRequest

def ptb_check_membership(group_id: int = -1002606804832, channel_id: int = -1002171454204):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            user_id = update.effective_user.id
            bot = context.bot
            
            try:
                # Check group membership
                group_member = await bot.get_chat_member(group_id, user_id)
                # Check channel membership
                #channel_member = await bot.get_chat_member(channel_id, user_id)
                
                if group_member.status not in ("left", "kicked"): # and channel_member.status not in ("left", "kicked"):
                    return await func(update, context, *args, **kwargs)
            except BadRequest:
                pass
            
            # Get invite links
            try:
                group_invite = await bot.export_chat_invite_link(group_id)
                #channel_invite = await bot.export_chat_invite_link(channel_id)
            except Exception as e:
                await update.message.reply_text("⚠️ Could not generate invite links. Please contact admin.")
                return

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Join Group", url=group_invite),
                        #InlineKeyboardButton("Join Channel", url=channel_invite)
                    ],
                    [InlineKeyboardButton("✅ I Joined", callback_data="check_joined")]
                ]
            )
            
            await update.message.reply_text(
                "⚠️ To use this command, please join our group and channel first!",
                reply_markup=keyboard
            )
        
        return wrapper
    return decorator

# Callback handler function
async def check_joined_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    group_id = -1002606804832
    channel_id = -1002171454204
    
    try:
        # Check both memberships
        group_member = await context.bot.get_chat_member(group_id, user_id)
        #channel_member = await context.bot.get_chat_member(channel_id, user_id)
        
        if group_member.status not in ("left", "kicked"):# and channel_member.status not in ("left", "kicked"):
            await query.edit_message_text(
                "✅ Verification successful! You can now use the bot commands.",
                reply_markup=None  # Remove buttons
            )
            return
    except BadRequest:
        pass
    
    await query.answer(
        "You must join both the group and channel to continue!",
        show_alert=True
    )

# Add this handler to your application
application.add_handler(CallbackQueryHandler(check_joined_callback, pattern="^check_joined$"))
