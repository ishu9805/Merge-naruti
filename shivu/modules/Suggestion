from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from . import app, user_collection, collection
from .watchers import suggest_watcher
import asyncio

SUPPORT_CHAT_ID = -1002338924488
SUGGESTION_CHANNEL_ID = -1002334436126

@app.on_message(filters.text | filters.photo, group=suggest_watcher)
async def suggestion_command(client, message):
    if message.from_user is None:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    # Handle text or photo caption gracefully
    if message.photo:
        text = message.caption.strip() if message.caption else ""
    else:
        text = message.text.strip() if message.text else ""

    if "@suggestion" not in text.lower():
        return

    if chat_id == SUPPORT_CHAT_ID:
        if not text:
            await message.reply("Please provide a suggestion in your message after @suggestion.")
            return

        if message.photo:
            # Send message with photo to the suggestion channel
            sent_message = await client.send_photo(
                chat_id=SUGGESTION_CHANNEL_ID,
                photo=message.photo.file_id,
                caption=f"**New Suggestion**\n\n{text}\n\n**Status:** Pending...",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Check Status", url=f"https://t.me/naruto_support_chat/{message.id}")]
                ])
            )
        else:
            # Send text message to the suggestion channel
            sent_message = await client.send_message(
                chat_id=SUGGESTION_CHANNEL_ID,
                text=f"**New Suggestion**\n\n{text}\n\n**Status:** Pending...",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Check Status", url=f"https://t.me/naruto_support_chat/{message.id}")]
                ])
            )

        await message.reply(
            "Your suggestion has been added! Please check the status using the button below.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Check Status", url=f"https://t.me/naruto_suggestion/{sent_message.id}")]
            ])
        )
    else:
        await message.reply(
            "You can only submit suggestions in the official suggestions group.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Here", url="https://t.me/naruto_support_chat")]
            ])
            )
