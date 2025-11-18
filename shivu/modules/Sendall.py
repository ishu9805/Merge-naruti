from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from shivu import applicationps as application, collectionps as collection
from pymongo.errors import PyMongoError


from pyrogram import filters
from shivu import shivuups as app

OWNER_ID = 8535832693
CHANNEL_ID = -1003295207951

# ---------------------------------------------------------
# TYPE MAP
# ---------------------------------------------------------
type_map = {
    "⚽": "Football", "🏀": "Basketball", "🎊": "Cheerleader", "🏖": "Summer",
    "☃️": "Winter", "🎃": "Halloween", "🎄": "Christmas", "🥻": "Saree",
    "🏴‍☠️": "Pirate", "👑": "Royalty", "🚨": "Officer", "👘": "Kimono",
    "👙": "Bikini", "🎒": "School", "🏜": "Egypt", "🎀": "Serena",
    "💍": "Wedding", "🩺": "Doctor", "💪": "GYM", "🧹": "Maid",
    "🐰": "Bunny", "💝": "Valentine", "🏐": "Volleyball", "🍷": "Drunk",
    "🎩": "Assembly", "🎨": "Coloured", "🚓": "Police", "💉": "Nurses",
    "🦠": "Toxic", "🧧": "Chinese New Year", "🪽": "Angelic", "🍫": "Chocolates",
    "🔞": "+18", "🧬": "Cross-Verse", "👶": "Chibi", "🪙": "Treasure"
}

# ---------------------------------------------------------
# RARITY MAP
# ---------------------------------------------------------
rarity_map = {
    1: "⚪️ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium",
    5: "💮 Special Edition", 6: "🔮 Limited Edition", 7: "💸 Premium Edition",
    8: "🌤 Summer", 9: "🎐 Celestial", 10: "❄️ Winter", 11: "💝 Valentine",
    12: "🎃 Halloween", 13: "🎄 Christmas Special", 14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    15: "🎭 Cosplay Master 🎭", 16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨", 17: "🎖 Apex Lot ( AUCTION )",
    18: "🍑 Echhi", 19: "☠️ 𝕯𝖎𝖛𝖎𝖓𝖊", 20: "☔ Monsoon", 21: "🪸 Aquatic",
    22: "🎨 Artistic", 23: "💳 VIP SLOT", 24: "👶 Chibi", 25: "🏴‍☠️ Marauds"
}


# ---------------------------------------------------------
# Detect art type from name
# ---------------------------------------------------------
def detect_character_type(name: str):
    for emoji, typename in type_map.items():
        if emoji in name:
            return f"*{typename}*"
    return None


# ---------------------------------------------------------
# Build caption
# ---------------------------------------------------------
def generate_caption(char_id, name, anime, rarity):
    rarity_text = rarity_map.get(rarity, "Unknown")
    ctype = detect_character_type(name)

    type_block = f"🎨 *Type:* {ctype}\n" if ctype else ""

    caption = f"""
╔══✦❀•°:🎭:°•❀✦══╗
        *CHARACTER UNLOCKED*
╚══✦❀•°:💫:°•❀✦══╝

🆔 *ID:* `{char_id}`
👤 *Name:* {name}
📺 *Anime:* {anime}

{type_block}🌟 *Rarity:* {rarity_text}

╭───────────────────╮
    *COLLECT • TRADE • OWN*
╰───────────────────╯
"""
    return caption


# ---------------------------------------------------------
# Send character (photo/video auto)
# ---------------------------------------------------------
async def send_character(chat_id, data):
    char_id = data["_id"]
    name = data["name"]
    anime = data["anime"]
    rarity = data["rarity"]
    url = data["img_url"]  # supports image or video url

    caption = generate_caption(char_id, name, anime, rarity)

    try:
        if url.endswith(".mp4"):
            await app.send_video(
                chat_id,
                video=url,
                caption=caption,
                parse_mode="markdown"
            )
        else:
            await app.send_photo(
                chat_id,
                photo=url,
                caption=caption,
                parse_mode="markdown"
            )
    except Exception as e:
        print("Send error:", e)


# ---------------------------------------------------------
# /send (send 1 character by ID)
# ---------------------------------------------------------
@app.on_message(filters.command("send") & filters.user(OWNER_ID))
async def send_single(_, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /send <id>")

    try:
        char_id = int(message.command[1])
    except:
        return await message.reply("❌ Invalid ID format.")

    data = await collection.find_one({"_id": char_id})
    if not data:
        return await message.reply("❌ Character not found.")

    await send_character(message.chat.id, data)


# ---------------------------------------------------------
# /sendall — send to Database Channel
# ---------------------------------------------------------
@app.on_message(filters.command("sendall") & filters.user(OWNER_ID))
async def send_all(_, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /sendall <id>")

    try:
        char_id = int(message.command[1])
    except:
        return await message.reply("❌ Invalid ID format.")

    data = await collection.find_one({"_id": char_id})
    if not data:
        return await message.reply("❌ Character not found.")

    await send_character(CHANNEL_ID, data)

    await message.reply("✅ Character sent to database channel.")
