from functools import wraps
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import StopPropagation
import logging

from telegram import Update, InlineKeyboardButton as TgInlineKeyboardButton, InlineKeyboardMarkup as TgInlineKeyboardMarkup
from telegram.ext import CallbackContext
from typing import Callable, Any
from shivu import shivuups as app


# Global command lock dictionary
command_locksp = {}


async def is_started(context: CallbackContext, user_id: int) -> bool:
    try:
        await context.bot.get_chat(user_id)
        return True
    except Exception:
        return False


async def is_started_pyro(client: Client, user_id: int) -> bool:
    try:
        await client.get_chat(user_id)
        return True
    except Exception:
        return False


async def _build_dm_start_url_pyro(client: Client) -> str:
    try:
        me = await client.get_me()
        if getattr(me, "username", None):
            return f"https://t.me/{me.username}?start=start"
    except Exception:
        pass
    return "https://t.me/animechatiac"


# Decorator to enforce DM start (PTB)
def must_dm(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if not update.effective_user or not update.effective_chat:
            return

        user_id = update.effective_user.id
        chat_type = update.effective_chat.type

        if chat_type != "private" and not await is_started(context, user_id):
            username = getattr(context.bot, "username", None)
            if not username:
                try:
                    me = await context.bot.get_me()
                    username = getattr(me, "username", None)
                except Exception:
                    username = None

            start_link = f"https://t.me/{username}?start=start" if username else "https://t.me/animechatiac"
            keyboard = TgInlineKeyboardMarkup(
                [[TgInlineKeyboardButton("✨ Start Bot In DM", url=start_link)]]
            )
            if update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ Please start the bot in DM first (and make sure you haven't blocked it).",
                    reply_markup=keyboard,
                )
            return

        await func(update, context, *args, **kwargs)

    return wrapper


@app.on_message(filters.group & filters.regex(r"^/"), group=-100)
async def require_dm_start_for_all_commands(client: Client, message: Message):
    if not message.from_user:
        return

    if await is_started_pyro(client, message.from_user.id):
        return

    start_link = await _build_dm_start_url_pyro(client)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✨ Start Bot In DM", url=start_link)]]
    )
    await message.reply_text(
        "⚠️ Please start the bot in DM first (and make sure you haven't blocked it).",
        reply_markup=keyboard,
    )
    raise StopPropagation


def ptbcommand_lock(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args: Any, **kwargs: Any) -> None:
        user_id = update.effective_user.id  # Get the user ID from the update

        # Check if the user is already executing a command
        if user_id in command_locks:
            await update.message.reply_text("⏳ Please wait until your previous command is finished.")
            return

        # Lock the command for this user
        command_locksp[user_id] = True

        try:
            # Execute the command
            await func(update, context, *args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again later.")
        finally:
            # Unlock the command for this user
            command_locksp.pop(user_id, None)

    return wrapper

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
