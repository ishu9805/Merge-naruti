from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from shivu import (
    user_totals_collectionps as user_totals_collection,
    shivuups as shivuu,
    PARTNER
)
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store pagination data in memory
pagination_data: Dict[int, Dict[str, List]] = {}  # {user_id: {"data": [], "page": 0}}

@shivuu.on_message(filters.command("checkfreq"))
async def check_frequencies(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if user is in the PARTNER list
    if str(user_id) not in PARTNER:
        await message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        # Find all chat frequencies that:
        # 1. Exist (field exists)
        # 2. Are not 70 or 100
        abnormal_freqs = await user_totals_collection.find({
            "message_frequency": {
                "$exists": True,
                "$nin": [70, 100]
            }
        }).to_list(length=None)

        if not abnormal_freqs:
            await message.reply_text("✅ All chats either have default frequencies (70 or 100) or no frequency set.")
            return

        # Store data for pagination
        pagination_data[user_id] = {
            "data": abnormal_freqs,
            "page": 0
        }

        # Send first page
        await send_page(client, message, user_id)

        logger.info(f"Frequencies checked by {user_id}. Found {len(abnormal_freqs)} non-default settings.")

    except Exception as e:
        error_msg = f"❌ Failed to check frequencies. Error: {str(e)}"
        await message.reply_text(error_msg)
        logger.error(f"Error in checkfreq command by {user_id}: {str(e)}")

async def send_page(client: Client, message: Message, user_id: int):
    data = pagination_data.get(user_id)
    if not data:
        return

    page = data["page"]
    all_data = data["data"]
    total_pages = (len(all_data) + 14) // 15  # Calculate total pages (15 items per page)

    # Get current page items
    start_idx = page * 15
    end_idx = start_idx + 15
    page_items = all_data[start_idx:end_idx]

    # Build response text
    response = f"📊 Chats with custom frequencies (Page {page + 1}/{total_pages}):\n\n"
    for idx, chat in enumerate(page_items, start=start_idx + 1):
        chat_id = chat.get('chat_id', 'Unknown')
        freq = chat['message_frequency']  # We know this exists due to our query
        response += f"{idx}. Chat ID: {chat_id} - Frequency: {freq}\n"

    # Build navigation buttons
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"freq_prev_{user_id}"))
    if end_idx < len(all_data):
        buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"freq_next_{user_id}"))

    reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

    # Edit or send new message
    if message.from_user.is_self:  # If it's our own message (for callback updates)
        await message.edit_text(response, reply_markup=reply_markup)
    else:
        await message.reply_text(response, reply_markup=reply_markup)

@shivuu.on_callback_query(filters.regex(r"^freq_(prev|next)_(\d+)$"))
async def handle_pagination(client, callback_query):
    action, user_id = callback_query.data.split('_')[1], int(callback_query.data.split('_')[2])
    
    # Verify the user
    if callback_query.from_user.id != user_id:
        await callback_query.answer("This menu isn't for you!", show_alert=True)
        return

    data = pagination_data.get(user_id)
    if not data:
        await callback_query.answer("Data expired, please run the command again.", show_alert=True)
        return

    # Update page number
    if action == "prev":
        data["page"] -= 1
    elif action == "next":
        data["page"] += 1

    # Ensure page stays within bounds
    data["page"] = max(0, min(data["page"], (len(data["data"]) + 14) // 15 - 1))

    # Update the message
    await send_page(client, callback_query.message, user_id)
    await callback_query.answer()
