from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from shivu import applicationps as application, collectionps as collection
from pymongo.errors import PyMongoError


from pyrogram import filters
from shivu import shivuups as app
from shivu import collection  # your MongoDB collection


OWNER_ID = 8535832693
CHANNEL_ID = -1003295207951


# ---------------------------------------------------------
# TYPE MAP (Art variants)
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
# Detect Art Type
# ---------------------------------------------------------
def detect_character_type(name: str):
    for emoji, tname in type_map.items():
        if emoji in name:
            return f"*{tname}*"
    return None


# ---------------------------------------------------------
# Stylish Caption Generator ✨
# ---------------------------------------------------------
def generate_caption(char_id, name, anime, rarity):

    rarity_text = rarity_map.get(rarity, "Unknown")
    ctype = detect_character_type(name)

    type_line = f"🎨 *Type:* {ctype}\n" if ctype else ""

    caption = f"""
╔══✦❀•°:🎭:°•❀✦══╗
         *CHARACTER UNLOCKED*
╚══✦❀•°:💫:°•❀✦══╝

🆔 *ID:* `{char_id}`
👤 *Name:* {name}
📺 *Anime:* {anime}

{type_line}🌟 *Rarity:* {rarity_text}

╭───────────────────╮
   *COLLECT • TRADE • OWN*
╰───────────────────╯
"""
    return caption


# ---------------------------------------------------------
# Main Send Function
# ---------------------------------------------------------
async def send_character(chat_id, data):

    char_id = data["_id"]
    name = data["name"]
    anime = data["anime"]
    rarity = data["rarity"]
    url = data["img_url"]

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
# /send command — send by ID
# ---------------------------------------------------------
@app.on_message(filters.command("send") & filters.user(OWNER_ID))
async def send_single(_, message):
    if len(message.command) < 2:
        return await app.send_message(message.chat.id, "Usage: /send <id>")

    try:
        char_id = int(message.command[1])
    except:
        return await app.send_message(message.chat.id, "Invalid ID format.")

    data = collection.find_one({"_id": char_id})
    if not data:
        return await app.send_message(message.chat.id, "Character not found.")

    await send_character(message.chat.id, data)


# ---------------------------------------------------------
# /sendall — send to every user (broadcast)
# ---------------------------------------------------------
@app.on_message(filters.command("sendall") & filters.user(OWNER_ID))
async def send_all(_, message):
    if len(message.command) < 2:
        return await app.send_message(message.chat.id, "Usage: /sendall <id>")

    try:
        char_id = int(message.command[1])
    except:
        return await app.send_message(message.chat.id, "Invalid ID format.")

    data = collection.find_one({"_id": char_id})
    if not data:
        return await app.send_message(message.chat.id, "Character not found.")

    # Send to database channel first
    await send_character(CHANNEL_ID, data)

    await app.send_message(message.chat.id, "Broadcast sent successfully.")
