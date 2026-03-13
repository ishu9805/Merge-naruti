# ──────────────────────────────────────────────
# SHIVU MODULE : START MENU (Pure Pyrogram)
# ──────────────────────────────────────────────

import asyncio
import random
import traceback
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
    LOG_CHANNEL,
)
from shivu.modules.block import block_dec, temp_block, block_cbq

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


async def get_bot_username(client):
    try:
        me = await client.get_me()
        if me and me.username:
            return me.username
    except Exception:
        pass
    return BOT_USERNAME






async def log_start_error(client, where, error, user_id=None, chat_id=None):
    details = [
        "⚠️ #start_error",
        f"Where: `{where}`",
        f"Error: `{type(error).__name__}: {error}`",
    ]
    if user_id is not None:
        details.append(f"User ID: `{user_id}`")
    if chat_id is not None:
        details.append(f"Chat ID: `{chat_id}`")

    tb = traceback.format_exc()
    if tb and tb != "NoneType: None\n":
        details.append(f"Traceback:\n```\n{tb[-2800:]}\n```")

    try:
        await client.send_message(LOG_CHANNEL, "\n".join(details))
    except Exception:
        pass


def build_support_buttons(bot_username):
    return [
        [IKB("💬 Support Chat", url="https://t.me/animechatiac"),
         IKB("📢 Updates", url="https://t.me/hidden_naruto")],
        [IKB("➕ Add to Group", url=f"https://t.me/{bot_username}?startgroup=true")],
        [IKB("❓ Help", callback_data="help"),
         IKB("🌟 Credits", callback_data="credits")],
    ]

def escape_markdown_text(value):
    if not value:
        return "Ninja"
    escape_chars = "_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{ch}" if ch in escape_chars else ch for ch in str(value))


async def play_start_animation(message, user_first_name):
    frames = [
        "⚡ Initializing shinobi network",
        "🔥 Charging chakra",
        "🌌 Summoning anime universe",
        "✨ Preparing your dashboard",
    ]
    loading = await message.reply_text("🚀 Launching Naruto Universe...")
    for idx, frame in enumerate(frames, start=1):
        dots = "." * ((idx % 3) + 1)
        await loading.edit_text(
            f"{frame}{dots}\n\n👋 Welcome, {user_first_name}!"
        )
        await asyncio.sleep(0.45)
    return loading


async def send_start_media(client, chat_id, caption, buttons):
    welcome_video = random.choice(START_VIDEOS) if START_VIDEOS else None

    if welcome_video:
        try:
            await client.send_video(
                chat_id=chat_id,
                video=welcome_video,
                caption=caption,
                reply_markup=IKM(buttons),
            )
            return
        except Exception:
            try:
                await client.send_animation(
                    chat_id=chat_id,
                    animation=welcome_video,
                    caption=caption,
                    reply_markup=IKM(buttons),
                )
                return
            except Exception:
                pass

    await client.send_message(
        chat_id=chat_id,
        text=caption,
        reply_markup=IKM(buttons),
    )

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
    [IKB("💬 Support Chat", url="https://t.me/animechatiac"),
     IKB("📢 Updates", url="https://t.me/hidden_naruto")],
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
    bot_username = await get_bot_username(_)
    dynamic_buttons = build_support_buttons(bot_username)
    safe_first_name = escape_markdown_text(user.first_name)

    try:
        await init_user(user.id, user.username, user.first_name)
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
    except Exception as error:
        await log_start_error(_, "start_private:db_init", error, user.id, message.chat.id)

    loader = None
    try:
        loader = await play_start_animation(message, safe_first_name)
    except Exception as error:
        await log_start_error(_, "start_private:animation", error, user.id, message.chat.id)

    caption = f"""
{Font.TITLE.format(f"Welcome {safe_first_name}!")}

{Font.HIGHLIGHT.format("Ready to start your collection?")}

{Font.ITALIC}Use the buttons below to navigate:{Font.ITALIC}
    """

    if loader:
        try:
            await loader.delete()
        except Exception:
            pass

    try:
        await send_start_media(_, user.id, caption, dynamic_buttons)
    except Exception as error:
        await log_start_error(_, "start_private:send_start_media", error, user.id, message.chat.id)
        await message.reply_text(
            "⚠️ Something went wrong while loading media. Please try /start again.",
            reply_markup=IKM(dynamic_buttons),
        )

# ──────────────────────────────────────────────
# /start in groups
# ──────────────────────────────────────────────
@app.on_message(filters.command("start") & filters.group)
@block_dec
async def start_group(_, message):
    try:
        bot_username = await get_bot_username(_)
        await message.reply_text(
        f"""
{Font.TITLE.format("Naruto Collection Game")}

{Font.ITALIC}To start playing, please initiate me in DMs!{Font.ITALIC}
        """,
        reply_markup=IKM([
            [IKB("✨ Start in DM", url=f"https://t.me/{bot_username}?start=start")]
        ])
    )
    except Exception as error:
        await log_start_error(_, "start_group:reply", error, message.from_user.id if message.from_user else None, message.chat.id)

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
    bot_username = await get_bot_username(_)
    dynamic_buttons = build_support_buttons(bot_username)
    try:
        await send_start_media(_, query.from_user.id, start_text, dynamic_buttons)
    except Exception as error:
        await log_start_error(_, "main_menu:send_start_media", error, query.from_user.id, query.message.chat.id)
        await _.send_message(
            query.from_user.id,
            start_text,
            reply_markup=IKM(dynamic_buttons),
        )
