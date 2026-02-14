# ──────────────────────────────────────────────
# SHIVU MODULE : START MENU (Pure Pyrogram)
# ──────────────────────────────────────────────

import random
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from shivu import (
    shivuups as app,
    dbps as db,
    user_collectionps as user_collection,
    pmusersps as pmusers,
    UPDATE_CHATps as UPDATE_CHAT_PS,
    PHOTO_URL,
)
from .block import block_dec, temp_block, block_cbq

# ──────────────────────────────────────────────
# Font styling class
# ──────────────────────────────────────────────
class Font:
    BOLD = "**"
    ITALIC = "__"
    TITLE = "✧ {} ✧"
    SUBHEAD = "✦ {} ✦"
    HIGHLIGHT = "✨ {} ✨"

# ──────────────────────────────────────────────
# MongoDB collections
# ──────────────────────────────────────────────
sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
BOT_USERNAME = "Naruto_Waifu_Husbando_Bot"
START_VIDEOS = PHOTO_URL

# ──────────────────────────────────────────────
# Main start message
# ──────────────────────────────────────────────
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

credits_text = f"""
{Font.TITLE.format("🌟 CREDITS 🌟")}

{Font.SUBHEAD.format("Development Team:")}
• Developers
• Sudo Users
• Uploaders

{Font.ITALIC}Special thanks to our wonderful community!{Font.ITALIC}
"""

support_buttons = [
    [IKB("💬 Support Chat", url="https://t.me/anime_x_blade"),
     IKB("📢 Updates", url="https://t.me/NARUTOO_UPDATE")],
    [IKB("➕ Add to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
    [IKB("❓ Help", callback_data="help"),
     IKB("🌟 Credits", callback_data="credits")]
]

# ──────────────────────────────────────────────
# Initialize user data
# ──────────────────────────────────────────────
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

# ──────────────────────────────────────────────
# /start in private
# ──────────────────────────────────────────────
@app.on_message(filters.command("start") & filters.private)
@block_dec
async def start_private(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    user = message.from_user
    await init_user(user.id, user.username, user.first_name)

    # Add user to PM database
    await pmusers.update_one(
        {"user_id": user.id},
        {"$set": {
            "user_id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "blocked": False,
            "started_at": datetime.now()
        }},
        upsert=True
    )

    welcome_video = random.choice(START_VIDEOS)
    caption = f"""
{Font.TITLE.format(f"Welcome {user.first_name}!")}

{Font.HIGHLIGHT.format("Ready to start your collection?")}

{Font.ITALIC}Use the buttons below to navigate:{Font.ITALIC}
    """
    await _.send_video(
        chat_id=user.id,
        video=welcome_video,
        caption=caption,
        reply_markup=IKM(support_buttons)
    )

# ──────────────────────────────────────────────
# /start in groups
# ──────────────────────────────────────────────
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

# ──────────────────────────────────────────────
# /credits command
# ──────────────────────────────────────────────
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

# ──────────────────────────────────────────────
# Generate team buttons
# ──────────────────────────────────────────────
async def generate_team_buttons(_, collection):
    buttons = []
    async for user in collection.find():
        user_id = user.get("user_id")
        if user_id:
            try:
                user_data = await _.get_users(user_id)
                name = user_data.first_name
                buttons.append(IKB(f"👤 {name}", url=f"tg://user?id={user_id}"))
            except Exception:
                continue
    return [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

# ──────────────────────────────────────────────
# Callback: credits menu
# ──────────────────────────────────────────────
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

# ──────────────────────────────────────────────
# Callback: show teams
# ──────────────────────────────────────────────
@app.on_callback_query(filters.regex("sdev|ssudo|suploader"))
@block_cbq
async def show_team(_, query):
    data_map = {
        "sdev": ("👨‍💻 Developers", devb),
        "ssudo": ("👑 Sudo Users", sudb),
        "suploader": ("📤 Uploaders", uploaderdb)
    }
    title, collection = data_map[query.data]
    buttons = await generate_team_buttons(_, collection)
    buttons.append([IKB("🔙 Back", callback_data="credits")])

    await query.edit_message_text(
        text=f"{Font.TITLE.format(title)}\n\n{Font.HIGHLIGHT.format('Our Amazing Team:')}",
        reply_markup=IKM(buttons)
    )

# ──────────────────────────────────────────────
# Callback: main menu
# ──────────────────────────────────────────────
@app.on_callback_query(filters.regex("main"))
async def main_menu(_, query):
    await query.message.delete()
    welcome_video = random.choice(START_VIDEOS)
    await _.send_video(
        chat_id=query.from_user.id,
        video=welcome_video,
        caption=start_text,
        reply_markup=IKM(support_buttons)
    )
