
from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuups as app, collectionps as collection
import re
from collections import Counter

rarity_map = {
    1: "⚪️ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium",
    5: "💮 Special Edition", 6: "🔮 Limited Edition", 7: "💸 Premium Edition",
    8: "🌤 Summer", 9: "🎐 Celestial", 10: "❄️ Winter", 11: "💝 Valentine",
    12: "🎃 Halloween", 13: "🎄 Christmas Special", 14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    15: "🎭 Cosplay Master 🎭", 17: "🎖 Apex Lot ( AUCTION )", 16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨",
    18: "🍑 Echhi", 19: "☠️ 𝕯𝖎𝖛𝖎𝖓𝖊", 20: "☔ Monsoon", 21: "🪸 Aquatic",
    22: "🎨 Artistic", 23: "💳 VIP SLOT", 24: "👶 Chibi", 25: "🏴‍☠️ Marauds", 26: "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣"
}

@app.on_message(filters.command("detail"))
async def char_count(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("⚠️ Usage: /char <character_name>")
        return

    search_word = " ".join(message.command[1:]).strip()
    regex_pattern = rf"\b{re.escape(search_word)}\b"

    cursor = collection.find(
        {"name": {"$regex": regex_pattern, "$options": "i"}},
        {"rarity": 1, "name": 1}
    )
    characters = await cursor.to_list(length=None)

    if not characters:
        await message.reply_text(f"❌ No characters found containing word: {search_word}")
        return

    rarity_counter = Counter([c.get("rarity", "Unknown") for c in characters])
    total_count = len(characters)

    response = [f"✅ Total characters containing **{search_word}**: `{total_count}`\n"]
    for rarity, count in rarity_counter.items():
        rarity_name = rarity_map.get(rarity, rarity)
        response.append(f"{rarity_name} → `{count}`")

    await message.reply_text("\n".join(response))
    

import os
import requests
from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuups as shivuu

def upload_to_envs(file_path=None, file_url=None, expires=None, secret=None):
    url = "https://envs.sh"
    files = {}
    data = {}
    if file_path:
        try:
            files = {'file': open(file_path, 'rb')}
        except Exception as e:
            return f"❌ Error opening file: {str(e)}"
    elif file_url:
        data = {'url': file_url}
    if secret:
        data['secret'] = secret
    if expires:
        data['expires'] = expires
    try:
        response = requests.post(url, files=files, data=data)
        if file_path:
            files['file'].close()
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"❌ Upload failed. Status: {response.status_code}\n{response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Error during upload: {str(e)}"

def check_file_size(file_path, max_size_mb=20):
    if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
        raise Exception("⚠️ File size exceeds the 20 MB limit.")

@shivuu.on_message(filters.command("envs") & filters.reply)
def envs_upload(client, message: Message):
    reply = message.reply_to_message
    if not reply.video:
        message.reply("⚠️ Please reply to a video with /envs")
        return
    try:
        file_path = reply.download(file_name=f"downloads/{reply.id}.mp4")
        check_file_size(file_path, max_size_mb=20)
        url = upload_to_envs(file_path=file_path)
        if url and url.startswith("http"):
            message.reply(f"✅ Uploaded successfully!\n\n🔗 Link: `{url}`", disable_web_page_preview=True)
        else:
            message.reply(str(url))
    except Exception as e:
        message.reply(f"❌ Error: {str(e)}")
    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)




from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuups as app, user_collectionps as user_collection


@app.on_message(filters.command("topcollectors"))
async def top_collectors(client, message: Message):
    pipeline = [
        {"$project": {"id": 1, "characters": 1}},
        {"$addFields": {"count": {"$size": {"$ifNull": ["$characters", []]}}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    top_users = await user_collection.aggregate(pipeline).to_list(length=20)

    if not top_users:
        return await message.reply_text("⚠️ No users found in the database.")

    text = "🏆 **Top 20 Collectors** 🏆\n\n"
    rank = 1
    for user in top_users:
        uid = user["id"]
        count = user.get("count", 0)
        try:
            tg_user = await client.get_users(uid)
            name = tg_user.first_name
        except Exception:
            name = "Unknown"
        text += f"**{rank}. {name}** (`{uid}`) → `{count}` cards\n"
        rank += 1

    await message.reply_text(text)


from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuups as app

rarity_map = {
    1: "⚪️ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium",
    5: "💮 Special Edition", 6: "🔮 Limited Edition", 7: "💸 Premium Edition",
    8: "🌤 Summer", 9: "🎐 Celestial", 10: "❄️ Winter", 11: "💝 Valentine",
    12: "🎃 Halloween", 13: "🎄 Christmas Special", 14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    15: "🎭 Cosplay Master 🎭", 17: "🎖 Apex Lot ( AUCTION )", 16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨",
    18: "🍑 Echhi", 19: "☠️ 𝕯𝖎𝖛𝖎𝖓𝖊", 20: "☔ Monsoon", 21: "🪸 Aquatic",
    22: "🎨 Artistic", 23: "💳 VIP SLOT", 24: "👶 Chibi", 25: "🏴‍☠️ Marauds", 26: "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣"
}


@app.on_message(filters.command("profile"))
async def profile_cmd(client, message: Message):
    args = message.text.split(maxsplit=1)
    user_data = None
    target_user_id = None

    if len(args) == 1 and not message.reply_to_message:
        target_user_id = message.from_user.id
    elif message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    elif len(args) > 1:
        query = args[1].strip()
        if query.isdigit():
            user_data = await user_collection.find_one({"id": int(query)})
        else:
            user_data = await user_collection.find_one(
                {"username": {"$regex": f"^{re.escape(query)}", "$options": "i"}}
            )
        if not user_data:
            return await message.reply_text("❌ User not found in database.")
        target_user_id = user_data["id"]

    if not user_data:
        user_data = await user_collection.find_one({"id": target_user_id})
    if not user_data:
        return await message.reply_text("❌ This user is not registered in the database.")

    try:
        tg_user = await client.get_users(target_user_id)
        display_name = tg_user.first_name or user_data.get("name") or "Unknown"
        current_username = f"@{tg_user.username}" if tg_user.username else "No username"
    except Exception:
        display_name = user_data.get("name") or user_data.get("first_name") or "Unknown"
        current_username = f"@{user_data['username']}" if user_data.get("username") else "No username (unavailable)"

    old_username = user_data.get("username", "Not saved")
    characters = user_data.get("characters", [])
    rarity_counter = Counter([char.get("rarity", "Unknown") for char in characters])
    total_count = len(characters)

    rarity_text = [f"📦 **Total Characters:** `{total_count}`"]
    for rarity, count in rarity_counter.items():
        rarity_display = rarity if rarity in rarity_map.values() else rarity
        rarity_text.append(f"{rarity_display} → `{count}`")

    text = (
        f"👤 **Profile Info**\n\n"
        f"👑 Name: `{display_name}`\n"
        f"📛 Old Username: `{old_username}`\n"
        f"🔹 Current Username: {current_username}\n\n"
        + "\n".join(rarity_text)
    )

    button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📂 Open Collection", switch_inline_query_current_chat=f"collection.img.{target_user_id}")]]
    )

    await message.reply_text(text, reply_markup=button)




from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuups as app, BOT_USERNAME

@app.on_message(filters.command("inline"))
async def inline_button(client, message: Message):
    if "-" not in message.text:
        await message.reply_text(
            "⚠️ Usage: /inline <name> - <rarity>\n"
            "Example: `/inline roronoa zoro - limited`",
            quote=False
        )
        return

    # Remove the command itself
    query = message.text.split(" ", 1)[1].strip()

    # Split by `-`
    parts = query.split("-", 1)
    name = parts[0].strip()
    rarity = parts[1].strip() if len(parts) > 1 else "Unknown"

    inline_text = f".name. {name} .rarity. {rarity}"

    button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔍 Open Inline", switch_inline_query_current_chat=inline_text)]]
    )

    await message.reply_text(
        f"Here’s your inline search:\n**Name:** `{name}`\n**Rarity:** `{rarity}`",
        reply_markup=button
    )
  
