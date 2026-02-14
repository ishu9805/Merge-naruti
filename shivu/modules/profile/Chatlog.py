import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import RPCError, ChatAdminRequired, UserNotParticipant
from shivu import shivuups as app, userbot
LOG_GROUP_ID="8366850759"

# Configuration
AUTHORIZED_USER_IDS = {8411935064}  # Your user ID
BOT_INVITE_LINK = "https://t.me/Naruto_Waifu_Husbando_Bot?startgroup=true"
photo = "https://files.catbox.moe/c93u0p.jpg"  # Your image URL

@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message):    
    chat = message.chat
    bot_id = app.me.id
    
    for member in message.new_chat_members:
        if member.id == bot_id:
            try:
                # Try to get chat invite link
                try:
                    link = await app.export_chat_invite_link(chat.id)
                except (ChatAdminRequired, UserNotParticipant):
                    try:
                        if getattr(userbot, "is_connected", False):
                            link = await userbot.export_chat_invite_link(chat.id)
                        else:
                            link = "Private Group (No permission to get link)"
                    except Exception:
                        link = "Private Group (No permission to get link)"
                except Exception:
                    try:
                        if getattr(userbot, "is_connected", False):
                            link = await userbot.export_chat_invite_link(chat.id)
                        else:
                            link = "Private Group"
                    except Exception:
                        link = "Private Group"
                
                # Welcome message with button
                welcome_msg = (
                    f"✨ Hello {chat.title} members!\n"
                    f"🤖 I'm {app.me.first_name}, your waifu husbando collection bot!\n"
                    f"📚 Use /help to see all available commands!\n\n"
                    f"🌟 Add me to your groups to start collecting!"
                )
                
                # Create add button
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ", url=BOT_INVITE_LINK)],
                    [InlineKeyboardButton("Hᴇʟᴘ", callback_data="help_command")]
                ])
                
                # Send welcome message with random photo
                await app.send_photo(
                    chat.id,
                    photo=photo,
                    caption=welcome_msg,
                    reply_markup=keyboard
                )
                
                # Log to admin channel
                try:
                    count = await app.get_chat_members_count(chat.id)
                    log_msg = (
                        f"📝 Bot Added to New Group\n\n"
                        f"📌 Chat Name: {chat.title}\n"
                        f"🍂 Chat ID: {chat.id}\n"
                        f"👤 Added By: {message.from_user.mention if message.from_user else 'Unknown'}\n"
                        f"👥 Members: {count}\n"
                        f"🔗 Chat Link: {link}\n"
                        f"#NewGroup @naruto_dev"
                    )
                    
                    await app.send_photo(
                        LOG_GROUP_ID,
                        photo=photo,
                        caption=log_msg
                    )
                    
                except Exception as log_error:
                    error_msg = f"Error logging to channel: {str(log_error)}"
                    await app.send_message(LOG_GROUP_ID, error_msg)
                
            except Exception as e:
                error_msg = f"Error in new chat handler: {str(e)}"
                try:
                    await app.send_message(LOG_GROUP_ID, error_msg)
                except Exception:
                    pass  # Avoid infinite error loop

@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    bot_id = app.me.id
    
    if message.left_chat_member and message.left_chat_member.id == bot_id:
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
            try:
                await app.send_message(LOG_GROUP_ID, error_msg)
            except Exception:
                pass  # Avoid infinite error loop
