from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuups as app
from shivu import anime_collection
from . import sudo_filter
import re
from datetime import datetime


# ------------------- HELPERS ------------------- #

def sanitize_anime_name(name: str) -> str:
    return re.sub(r"[^\w\s-]", "", name.strip().lower())


def format_title(name: str) -> str:
    fancy = name.title().replace(" ", " 𝄇 ")
    return f"✨ {fancy} ✨"


# ------------------- ADD FILTER ------------------- #

@app.on_message(filters.command("addanime") & sudo_filter)
async def add_filter(_, message: Message):
    if " - " not in message.text:
        await message.reply("Usage: /addanime <anime_name> - <link>")
        return

    anime_name = message.text.split(" ", 1)[1].split(" - ")[0].strip()
    link = message.text.split(" - ", 1)[1].strip()

    sanitized = sanitize_anime_name(anime_name)

    doc = await anime_collection.find_one({"anime_name": sanitized})

    # If anime exists → append link
    if doc:
        await anime_collection.update_one(
            {"anime_name": sanitized},
            {"$push": {"links": {"url": link, "added_by": message.from_user.id, "time": datetime.utcnow()}}}
        )
        await message.reply(f"➕ Added another link to '{anime_name}'.")
        return

    # If not exists → create
    await anime_collection.insert_one({
        "original_name": anime_name,
        "anime_name": sanitized,
        "links": [{
            "url": link,
            "added_by": message.from_user.id,
            "time": datetime.utcnow()
        }]
    })

    await message.reply(f"✨ Filter created for '{anime_name}' and link added.")


# ------------------- GET ANIME ------------------- #

@app.on_message(filters.command("anime"))
async def get_anime(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /anime <anime_name>")
        return

    anime_name = " ".join(message.command[1:])
    sanitized = sanitize_anime_name(anime_name)

    doc = await anime_collection.find_one({"anime_name": sanitized})

    if not doc:
        await message.reply(f"❌ '{anime_name}' not found.")
        return

    title = format_title(doc["original_name"])
    links = doc["links"]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔗 Link {i+1}", url=item["url"])]
        for i, item in enumerate(links)
    ])

    text = (
        f"{title}\n\n"
        f"📁 Total Links: {len(links)}\n"
        f"📖 Anime: {doc['original_name']}\n\n"
        f"Tap a button below to open the available links."
    )

    await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)


# ------------------- REMOVE FILTER ------------------- #

@app.on_message(filters.command("rmanine") & sudo_filter)
async def remove_filter(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /rmanime <anime_name>")
        return

    anime_name = " ".join(message.command[1:])
    sanitized = sanitize_anime_name(anime_name)

    removed = await anime_collection.delete_one({"anime_name": sanitized})

    if removed.deleted_count:
        await message.reply(f"🗑 Removed all links for '{anime_name}'.")
    else:
        await message.reply("No filter found.")


# ------------------- LIST FILTERS ------------------- #

@app.on_message(filters.command("totalanimes") & sudo_filter)
async def list_filters(_, message: Message):
    cursor = anime_collection.find()

    count = await anime_collection.count_documents({})
    if count == 0:
        await message.reply("No anime filters added yet.")
        return

    text = "📚 **Anime Filter List:**\n\n"
    async for item in cursor:
        text += f"• {item['original_name']}\n"

        if len(text) > 3500:
            await message.reply(text)
            text = ""

    if text:
        await message.reply(text)


# ------------------- START ------------------- #

@app.on_message(filters.command("aastart"))
async def start(_, message: Message):
    text = (
        "✨ **Anime Filter System** ✨\n\n"
        "Commands:\n"
        "➕ /addanime <name> - <link>\n"
        "🔍 /anime <name>\n"
        "🗑 /rmanine <name>\n"
        "📚 /totalanimes\n\n"
        "Supports multiple links per anime and stylish UI."
    )
    await message.reply(text)


print("Anime Filter System Loaded with Buttons & Multi-Link Support.")
