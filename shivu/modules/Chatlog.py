



import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
#from config import LOGGER_ID as LOG_GROUP_ID
from shivu import shivuups as app 
from pyrogram.errors import RPCError

LOG_GROUP_ID = -1002165460785  # Your log channel ID
AUTHORIZED_USER_IDS = {7378476666}  # Your user ID
BOT_INVITE_LINK = "https://t.me/Fancy_Waifu_Husbando_Bot?startgroup=true"
photo = "https://files.catbox.moe/c93u0p.jpg"  # Your image URL



# Bot invite link
#BOT_INVITE_LINK = "https://t.me/Fancy_Waifu_Husbando_Bot?startgroup=true"

@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message):    
    chat = message.chat
    for member in message.new_chat_members:
        if member.id == 7107840748:
            try:
                # Try to get chat invite link
                try:
                    link = await app.export_chat_invite_link(chat.id)
                except:
                    link = "Private Group"
                
                # Welcome message with button
                welcome_msg = (
                    f"✨ Hello {chat.title} members!\n"
                    f"🤖 I'm {app.me.first_name}, your anime music bot!\n"
                    f"🎵 Ready to play your favorite tunes!\n\n"
                    #f"Use /help to see my commands!"
                )
                
                # Create add button
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ", url=BOT_INVITE_LINK)]
                ])
                
                # Send welcome message with random photo
                await app.send_photo(
                    chat.id,
                    photo=photo,
                    caption=welcome_msg,
                    reply_markup=keyboard
                )
                
                # Log to admin channel
                count = await app.get_chat_members_count(chat.id)
                log_msg = (
                    f"📝 Music Bot Added to New Group\n\n"
                    f"📌 Chat Name: {chat.title}\n"
                    f"🍂 Chat ID: {chat.id}\n"
                    f"👤 Added By: {message.from_user.mention if message.from_user else 'Unknown'}\n"
                    f"👥 Members: {count}\n"
                    f"🔗 Chat Link: {link}"
                )
                
                await app.send_photo(
                    LOG_GROUP_ID,
                    photo=photo,
                    caption=log_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("👀 See Group", url=link)] if link != "Private Group" else []
                    ])
                )
                
            except Exception as e:
                error_msg = f"Error in new chat handler: {str(e)}"
                await app.send_message(LOG_GROUP_ID, error_msg)

@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    if message.left_chat_member.id == 7107840748:
        try:
            remove_by = message.from_user.mention if message.from_user else "Unknown User"
            left_msg = (
                f"✫ #Left_Group ✫\n\n"
                f"📌 Chat Title: {message.chat.title}\n"
                f"🆔 Chat ID: {message.chat.id}\n"
                f"👤 Removed By: {remove_by}\n"
                f"🤖 Bot: @{app.me.username}"
            )
            
            await app.send_photo(
                LOG_GROUP_ID,
                photo=photo,
                caption=left_msg
            )
        except Exception as e:
            error_msg = f"Error in left chat handler: {str(e)}"
            await app.send_message(LOG_GROUP_ID, error_msg)
