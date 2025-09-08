from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
import random
#from . import user_collection, app
from shivu import *
from .block import block_dec, temp_block, block_cbq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from itertools import groupby
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
import random
from datetime import datetime
from shivu import UPDATE_CHAT, SUPPORT_CHAT, CHARA_CHANNEL_ID, required_group_id, PHOTO_URL, OWNER_ID, PARTNER
from shivu import (
    collectionps as collection,
    top_global_groups_collectionps as top_global_groups_collection,
    group_user_totals_collectionps as group_user_totals_collection,
    user_collectionps as user_collection,
    user_totals_collectionps as user_totals_collection,
    shivuups as shivuu,
    shivuups as app,
    applicationps as application,
    SUPPORT_CHATps as SUPPORT,
    UPDATE_CHATps as UPDATE_CHAT,
    dbps as db,
    pmusersps as pmusers,
    ban_collectionps as ban_collection,
    user_countps as user_count, 
    chat_dataps as chat_data,
)

# Stylish fonts
class Font:
    BOLD = "**"
    ITALIC = "__"
    MONO = "`"
    STRIKE = "~~"
    TITLE = "✧ {} ✧"
    SUBHEAD = "✦ {} ✦"
    HIGHLIGHT = "✨ {} ✨"

# Database collections
sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

# Constants
BOT_NAME = "Naruto"
START_VIDEOS = PHOTO_URL

# Attractive start message with styling
start_text = f"""
{Font.TITLE.format("🌸 WELCOME TO NARUTO UNIVERSE 🌸")}

{Font.HIGHLIGHT.format("Anime Character Collection Game")}

{Font.SUBHEAD.format("Features:")}
• Collect rare anime characters
• Compete with friends
• Earn coins and rewards
• Trade characters
• Leaderboards

{Font.ITALIC}Begin your ninja journey today!{Font.ITALIC}

{Font.HIGHLIGHT.format("Get started by adding me to your group!")}
"""

# Enhanced credits text
credits_text = f"""
{Font.TITLE.format("🌟 CREDITS 🌟")}

{Font.SUBHEAD.format("Development Team:")}
• Developers
• Sudo Users
• Uploaders

{Font.ITALIC}Special thanks to our wonderful community!{Font.ITALIC}
"""

# Stylish buttons with emojis
support_buttons = [
    [IKB("💬 Support Chat", url=f"{SUPPORT_CHAT}"),
     IKB("📢 Updates", url=f"{UPDATE_CHAT}")],
    [IKB("➕ Add to Group", url=f"{BOT_USERNAME}")],
    [IKB("❓ Help", callback_data="help"),
     IKB("🌟 Credits", callback_data="credits")]
]

# Helper function for user initialization
async def init_user(user_id, username, first_name):
    await user_collection.update_one(
        {"id": user_id},
        {
            "$setOnInsert": {
                "coins": 100,
                "characters": [],
                "created_at": datetime.now(),
                "title": "Genin"
            },
            "$set": {
                "username": username,
                "first_name": first_name,
                "last_active": datetime.now()
            }
        },
        upsert=True
    )

# Enhanced start command with better visuals
@app.on_message(filters.command("start") & filters.private)
@block_dec
async def start_private(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    
    user = await _.get_users(user_id)
    await init_user(user_id, user.username, user.first_name)
    
    # Select random video with caption
    welcome_video = random.choice(START_VIDEOS)
    caption = f"""
{Font.TITLE.format(f"Welcome {user.first_name}!")}

{Font.HIGHLIGHT.format("Ready to start your collection?")}

{Font.ITALIC}Use the buttons below to navigate:{Font.ITALIC}
    """
    
    await _.send_video(
        chat_id=user_id,
        video=welcome_video,
        caption=caption,
        reply_markup=IKM(support_buttons)
    )

# Group start with better message
@app.on_message(filters.command("start") & filters.group)
@block_dec
async def start_group(_, message):
    await message.reply_text(
        f"""
{Font.TITLE.format("Naruto Collection Game")}

{Font.ITALIC}To start playing, please initiate me in DMs!{Font.ITALIC}
        """,
        reply_markup=IKM([
            [IKB("✨ Start in DM", url=f"https://t.me/{BOT_USERNAME}?start=start")]
        ])
    )

# Enhanced credits command
@app.on_message(filters.command("credits"))
@block_dec
async def show_credits(_, message):
    await message.reply_text(
        text=credits_text,
        reply_markup=IKM([
            [IKB("👨‍💻 Developers", callback_data="sdev"),
             IKB("👑 Sudo Users", callback_data="ssudo")],
            [IKB("📤 Uploaders", callback_data="suploader"),
             IKB("🔙 Back", callback_data="main")]
        ])
    )

# Helper function for listing team members
async def generate_team_buttons(collection, title):
    buttons = []
    async for user in collection.find():
        user_id = user.get("user_id")
        if user_id:
            try:
                user_data = await _.get_users(user_id)
                name = user_data.first_name
                buttons.append(IKB(f"👤 {name}", user_id=user_id))
            except:
                continue
    
    # Split into rows of 2 buttons each
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return rows

# Enhanced team display handlers
@app.on_callback_query(filters.regex("credits"))
@block_cbq
async def credits_callback(_, query):
    await query.edit_message_text(
        text=credits_text,
        reply_markup=IKM([
            [IKB("👨‍💻 Developers", callback_data="sdev"),
             IKB("👑 Sudo Users", callback_data="ssudo")],
            [IKB("📤 Uploaders", callback_data="suploader"),
             IKB("🔙 Back", callback_data="main")]
        ])
    )

@app.on_callback_query(filters.regex("sdev|ssudo|suploader"))
@block_cbq
async def show_team(_, query):
    team_type = query.data
    titles = {
        "sdev": ("👨‍💻 Developers", devb),
        "ssudo": ("👑 Sudo Users", sudb),
        "suploader": ("📤 Uploaders", uploaderdb)
    }
    
    title, collection = titles[team_type]
    await query.edit_message_text(
        text=f"{Font.TITLE.format(title)}\n\n{Font.ITALIC}Loading team members...{Font.ITALIC}",
        reply_markup=IKM([[IKB("🔙 Back", callback_data="credits")]])
    )
    
    buttons = await generate_team_buttons(collection, title)
    buttons.append([IKB("🔙 Back", callback_data="credits")])
    
    await query.edit_message_text(
        text=f"{Font.TITLE.format(title)}\n\n{Font.HIGHLIGHT.format('Our Amazing Team:')}",
        reply_markup=IKM(buttons)
    )

# Main menu callback
@app.on_callback_query(filters.regex("main"))
async def main_menu(_, query):
    welcome_video = random.choice(START_VIDEOS)
    await query.message.delete()
    await _.send_video(
        chat_id=query.from_user.id,
        video=welcome_video,
        caption=start_text,
        reply_markup=IKM(support_buttons)
    )



# In your start command handler (usually in a different file), add this:
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Add user to pmusers collection when they start the bot
    await pmusers.update_one(
        {'user_id': user_id},
        {'$set': {
            'user_id': user_id,
            'first_name': update.effective_user.first_name,
            'username': update.effective_user.username,
            #'started_at': datetime.now(),
            'blocked': False
        }},
        upsert=True
    )
    
    # Your existing start message code here
    #welcome_message = capsify("Welcome to the bot! Start chatting with me.")
    #await update.message.reply_text(welcome_message)

# Add this handler to your application
application.add_handler(CommandHandler("start", start))
