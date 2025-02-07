from pyrogram import Client, filters
import asyncio
from shivu import shivuu as app

LOG_CHANNEL_ID = -1002455650183

@app.on_message(filters.new_chat_members, group=2)
async def welcome_new_member(client, message):
    try:
        chat = message.chat
        bot = 0
        async for member in app.get_chat_members(chat.id):
            user = member.user
            if user.is_bot:
                bot += 1
            
        c = await app.get_chat_members_count(chat.id)
        count = c-bot
        username = (
                    message.chat.username if message.chat.username else "𝐏ʀɪᴠᴀᴛᴇ 𝐆ʀᴏᴜᴘ"
        )
        if count < 25:
            await app.leave_chat(chat.id)
            msg = f"Left group: {chat.title} (ID: {chat.id}, Members: {count}), link = @{username}"
            await app.send_message(LOG_CHANNEL_ID, msg)

    except Exception as e:
        error_message = f"Error leaving group {chat.title}: {e}"
        await app.send_message(LOG_CHANNEL_ID, error_message)


