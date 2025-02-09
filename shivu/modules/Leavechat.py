from pyrogram import Client, filters
from pymongo import MongoClient
import asyncio
from shivu import shivuu as app
from shivu import db

ac = db['allowedchat']

LOG_CHANNEL_ID = -1002455650183
MIN_MEMBER_COUNT = 30  # Minimum number of members to keep the group


# Function to add chat ID
async def add_chat_id(chat_id):
    try:
        if ac.find_one({"chat_id": chat_id}):
            return f"Chat ID {chat_id} already exists in allowed chats."
        
        ac.insert_one({"chat_id": chat_id})
        return f"Chat ID {chat_id} added to allowed chats."
    except Exception as e:
        return f"Error adding chat ID {chat_id}: {e}"

# Function to remove chat ID
async def remove_chat_id(chat_id):
    try:
        result = ac.delete_one({"chat_id": chat_id})
        
        if result.deleted_count == 1:
            return f"Chat ID {chat_id} removed from allowed chats."
        else:
            return f"Chat ID {chat_id} not found in allowed chats."
    except Exception as e:
        return f"Error removing chat ID {chat_id}: {e}"

# Command to add chat ID
@app.on_message(filters.command("addchat") & filters.user([7378476666]))
async def handle_add_chat(client, message):
    if len(message.command) != 2:
        await message.reply_text("Usage: /addchat <chat_id>")
        return

    chat_id = message.command[1]
    try:
        chat_id = int(chat_id)  # Ensure chat_id is an integer
        response = await add_chat_id(chat_id)
        await message.reply_text(response)
    except ValueError:
        await message.reply_text("Invalid chat ID. Please provide a valid integer.")

# Command to remove chat ID
@app.on_message(filters.command("delchat") & filters.user([7378476666]))
async def handle_remove_chat(client, message):
    if len(message.command) != 2:
        await message.reply_text("Usage: /delchat <chat_id>")
        return

    chat_id = message.command[1]
    try:
        chat_id = int(chat_id)  # Ensure chat_id is an integer
        response = await remove_chat_id(chat_id)
        await message.reply_text(response)
    except ValueError:
        await message.reply_text("Invalid chat ID. Please provide a valid integer.")

@app.on_message(filters.new_chat_members, group=2)
async def welcome_new_member(client, message):
    try:
        chat = message.chat
        bot_count = 0
        
        # Count the number of bots in the chat
        async for member in app.get_chat_members(chat.id):
            if member.user.is_bot:
                bot_count += 1
            
        total_members = await app.get_chat_members_count(chat.id)
        non_bot_count = total_members - bot_count
        
        username = message.chat.username if message.chat.username else "𝐏ʀɪᴠᴀᴛᴇ 𝐆ʀᴏᴜᴘ"
        
        # Check if the chat ID is in the allowed list
        if ac.find_one({"chat_id": chat.id}):
            return  # Do not leave the chat if it's in the allowed list
        
        # Check if the non-bot member count is below the threshold
        if non_bot_count < MIN_MEMBER_COUNT:
            await app.send_message(message.chat.id, "🚫 Leaving this group as it appears to be a spam group. If this is incorrect, please contact @sashtadeb to review.")
            await app.leave_chat(chat.id)
            msg = (f"Left group: {chat.title} (ID: {chat.id}, Members: {non_bot_count}), "
                   f"link = @{username}")
            await app.send_message(LOG_CHANNEL_ID, msg)

    except Exception as e:
        error_message = f"Error leaving group {chat.title}: {e}"
        await app.send_message(LOG_CHANNEL_ID, error_message)

