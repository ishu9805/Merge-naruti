from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
import random
#from . import user_collection, app
from shivu import *
from .block import block_dec, temp_block, block_cbq
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

sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

BOT_NAME = "Naruto"
start_text = f"""
🌸 **welcome to {BOT_NAME}!** 🌸

an anime-based games bot! add me to your group to start your journey.

🎮 **features:**
- play fun anime-based games
- earn 🪙 coins
- collect rare characters
- and much more!

👉 **get started by adding me to your group or clicking the button below!**
"""

credits_text = """
🌟 **bot credits** 🌟

users below are the developers, uploaders, etc... of this bot. you can personally contact them for issues, but please avoid unnecessary dms.

🙏 **thank you!**
"""

support_buttons = [
    [IKB("💬 support", url=f"https://t.me/{SUPPORT_CHAT}"),
     IKB("📢 updates", url=f"https://t.me/{UPDATE_CHAT}")],
    [IKB("➕ add me to your group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
    [IKB("❓ help", url=f"https://t.me/{SUPPORT_CHAT}"),
     IKB("🌟 credits", callback_data="credits")]
]

@app.on_message(filters.command("start") & filters.private)
@block_dec
async def startp(_, message):
    id = message.from_user.id
    if temp_block(id):
        return
    user = await _.get_users(id)
    username = user.username
    first_name = user.first_name

    user_data = await user_collection.find_one({"id": id})

    if user_data:
        # Check if "created_at" key exists, if not, add it
        if "created_at" not in user_data:
            user_collection.update_one(
                {"id": id},
                {"$set": {"created_at": datetime.now()}}
            )
        if "characters" not in user_data:
            user_collection.update_one(
                {"id":id},
                {"$set": {"characters": []}}
            )
        user_collection.update_one(
            {"id": id},
            {
                "$set": {
                    "username": username,
                    "first_name": first_name
                }
            }
        )
    else:
        user_collection.insert_one(
            {
                "id": id,
                "username": username,
                "first_name": first_name,
                "coins": 100,  # starting coins
                "characters": [],
                "created_at": datetime.now()
            }
        )

    random_video = random.choice(PHOTO_URL)
    await _.send_video(
        chat_id=id,
        video=random_video,
        caption=start_text,
        reply_markup=IKM(support_buttons)
    )

@app.on_message(filters.command("start") & filters.group)
@block_dec
async def startg(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    await message.reply_text(
        "🚀 **to start using me, please click the button below to initiate in dm.**",
        reply_markup=IKM([
            [IKB("✨ start in dm", url=f"https://t.me/{BOT_USERNAME}?start=start")]
        ])
    )

@app.on_message(filters.command("credits"))
@block_dec
async def cred(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    await message.reply_text(
        text=credits_text,
        reply_markup=IKM([
            [IKB("👨‍💻 developers", callback_data="sdev"),
             IKB("👑 sudos", callback_data="ssudo")],
            [IKB("📤 uploaders", callback_data="suploader"),
             IKB("🔙 back", callback_data="main")]
        ])
    )

@app.on_callback_query(filters.regex("credits"))
@block_cbq
async def credcb(_, callback_query):
    await callback_query.edit_message_text(
        text=credits_text,
        reply_markup=IKM([
            [IKB("👨‍💻 developers", callback_data="sdev"),
             IKB("👑 sudos", callback_data="ssudo")],
            [IKB("📤 uploaders", callback_data="suploader"),
             IKB("🔙 back", callback_data="main")]
        ])
    )

@app.on_callback_query(filters.regex("sdev"))
@block_cbq
async def sdev(_, callback_query):
    await callback_query.edit_message_text(
        text="⏳ loading developer names...",
        reply_markup=IKM([
            [IKB("🔙 back", callback_data="credits")]
        ])
    )

    dev_buttons = []
    async for user in devb.find():
        dev_id = user.get("user_id")
        if dev_id:
            user_data = await user_collection.find_one({"id": dev_id})
            first_name = user_data.get("first_name", "unknown") if user_data else "unknown"
            dev_buttons.append(IKB(first_name, user_id=dev_id))

    rows = [dev_buttons[i:i+3] for i in range(0, min(len(dev_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text="**👨‍💻 developers:**",
        reply_markup=IKM(rows + [[IKB("🔙 back", callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("ssudo"))
@block_cbq
async def ssudo(_, callback_query):
    await callback_query.edit_message_text(
        text="⏳ loading sudo names...",
        reply_markup=IKM([
            [IKB("🔙 back", callback_data="credits")]
        ])
    )

    sudo_buttons = []
    async for user in sudb.find():
        sudo_id = user.get("user_id")
        if sudo_id:
            user_data = await user_collection.find_one({"id": sudo_id})
            first_name = user_data.get("first_name", "unknown") if user_data else "unknown"
            sudo_buttons.append(IKB(first_name, user_id=sudo_id))

    rows = [sudo_buttons[i:i+3] for i in range(0, min(len(sudo_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text="**👑 sudos:**",
        reply_markup=IKM(rows + [[IKB("🔙 back", callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("suploader"))
@block_cbq
async def suploader(_, callback_query):
    await callback_query.edit_message_text(
        text="⏳ loading uploader names...",
        reply_markup=IKM([
            [IKB("🔙 back", callback_data="credits")]
        ])
    )

    uploader_buttons = []
    async for user in uploaderdb.find():
        uploader_id = user.get("user_id")
        if uploader_id:
            user_data = await user_collection.find_one({"id": uploader_id})
            first_name = user_data.get("first_name", "unknown") if user_data else "unknown"
            uploader_buttons.append(IKB(first_name, user_id=uploader_id))

    rows = [uploader_buttons[i:i+3] for i in range(0, min(len(uploader_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text="**📤 uploaders:**",
        reply_markup=IKM(rows + [[IKB("🔙 back", callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("main"))
async def main(_, callback_query):
    random_video = random.choice(PHOTO_URL)
    await callback_query.edit_message_text(
        text=start_text,
        reply_markup=IKM(support_buttons)
    )
