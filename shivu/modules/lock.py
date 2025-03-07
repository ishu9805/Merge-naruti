from functools import wraps
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from pymongo import MongoClient
import logging

# MongoDB setup
# Global command lock dictionary
command_locks = {}

def command_lock(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        user_id = message.from_user.id

        # Check if the user is already executing a command
        if user_id in command_locks:
            await message.reply_text("Please wait until the previous command is finished.")
            return

        # Lock the command for this user
        command_locks[user_id] = True

        try:
            # Execute the command
            await func(client, message, *args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            await message.reply_text("An error occurred. Please try again later.")
        finally:
            # Unlock the command for this user
            command_locks.pop(user_id, None)

    return wrapper
