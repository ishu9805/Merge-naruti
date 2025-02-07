from pyrogram import Client, filters

from shivu import shivuu as app

LOG_CHANNEL_ID = -1002455650183

@app.on_message(filters.new_chat_members)
def welcome_new_member(client, message):
    try:
        chat = message.chat
        count = await app.get_chat_members_count(chat.id)
        username = (
                    message.chat.username if message.chat.username else "𝐏ʀɪᴠᴀᴛᴇ 𝐆ʀᴏᴜᴘ"
        )
        if count < 35:
            await app.leave_chat(chat.id)
            msg = f"Left group: {chat.title} (ID: {chat.id}, Members: {count}), link = @{username}"
            await app.send_message(LOG_CHANNEL_ID, msg)

    except Exception as e:
        error_message = f"Error leaving group {chat.title}: {e}"
        await app.send_message(LOG_CHANNEL_ID, error_message)


