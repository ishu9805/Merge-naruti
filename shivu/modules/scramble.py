import asyncio
import os
import random
import string
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
#from . import app
#from shivu import user_collection, collection, db
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

scrambled_codes_collection = db["scrambleds"]



# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)


def generate_random_code(length: int = 6) -> str:
    """Generate a random code of specified length."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def scramble_code(code: str) -> str:
    """Scramble a code by shuffling its characters."""
    code_list = list(code)
    random.shuffle(code_list)
    return ''.join(code_list)

def generate_hint(code: str) -> str:
    """Generate a hint for the code in the format a_ _ b_ _ or c_d _ _ _."""
    hint = list(code)
    length = len(hint)
    
    # Decide how many characters to reveal based on code length
    if length <= 4:
        reveal_indices = [0, -1]  # Reveal first and last characters
    else:
        reveal_indices = [0, 2, -1]  # Reveal first, third, and last characters
    
    for i in range(length):
        if i not in reveal_indices:
            hint[i] = '_'
    
    return ' '.join(hint)




@app.on_message(filters.command("gameplay") & filters.user(7378476666))
async def send_scrambled_code(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if the user provided a character ID
    if len(message.command) < 2:
        await message.reply_text("❌ Please provide a character ID. Usage: /scramble <character_id>")
        return

    character_id = message.command[1]

    # Fetch the character from the database
    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text(f"🚫 Character with ID {character_id} not found.")
        return

    # Extract character details
    character_name = character.get('name', '❓')
    character_anime = character.get('anime', '❓')
    rarity = character.get('rarity', '❓')
    image_url = character.get('img_url', '')

    # Generate and scramble the code
    original_code = generate_random_code()
    scrambled_code = scramble_code(original_code)

    # Store the code and character in the database
    await scrambled_codes_collection.insert_one({
        "original_code": original_code,
        "scrambled_code": scrambled_code,
        "character": character,
        "claimed": False
    })

    # Send the scrambled code as a photo to the specified chat
    target_chat_id = -1001999201034 # Re your target chat ID
    await send_scrambled_photo(client, target_chat_id, scrambled_code, character, original_code)

    # Notify the user
    await message.reply_text(
        f"🎲 A scrambled code for **{character_name}** ({character_anime}) has been sent to the group. "
        f"Check it out and unscramble it to claim your character!"
    )



async def send_scrambled_photo(client: Client, chat_id: int, scrambled_code: str, character: dict, original_code: dict):
    """Send the scrambled code as a photo with a caption."""
    # Extract character details
    character_name = character.get('name', '❓')
    character_anime = character.get('anime', '❓')
    rarity = character.get('rarity', '❓')
    image_url = character.get('img_url', '')

    hint = generate_hint(original_code)

    # Caption with instructions
    caption = (
        f"🔍 Unscramble the code to claim your character:\n\n"
        f"**Character:** {character_name}\n"
        f"**Anime:** {character_anime}\n"
        f"**Rarity:** {rarity}\n\n"
        f"UNSCRAMBLED :- <code>{scrambled_code}</code>\n"
        f"**Hint:** `{hint}`\n\n"
        f"Use /solve <code> to claim your reward!"
    )

    # Send the photo to the specified chat
    await client.send_photo(
        chat_id=chat_id,
        photo=image_url,
        caption=caption
    )


@app.on_message(filters.command("solve"))
async def unscramble_code(client: Client, message: Message):
    user_id = message.from_user.id
    user_guess = " ".join(message.command[1:]).strip().lower()

    if not user_guess:
        await message.reply_text("❌ Please provide a code to unscramble.")
        return

    # Fetch the user's active scrambled code
    code_data = await scrambled_codes_collection.find_one({"claimed": False})
    if not code_data:
        await message.reply_text("❌ No active scrambled code found.")
        return

    if not code_data:
        await message.reply_text("❌ No active scrambled code found. Use /scramble to get a new one.")
        return

    # Check if the user's guess matches the original code
    if user_guess == code_data["original_code"]:
        # Reward the user with the character
        character = code_data["character"]
        await user_collection.update_one(
            {"id": user_id},
            {"$push": {"characters": character}},
            upsert=True
        )

        # Mark the code as claimed
        await scrambled_codes_collection.update_one(
            {"_id": code_data["_id"]},
            {"$set": {"claimed": True}}
        )

        await message.reply_text(
            f"🎉 Congratulations! You unscrambled the code correctly.\n\n"
            f"🏆 You have received: {character['name']} ({character['anime']})"
        )
        target = -1001999201034
        await client.send_message(chat_id=target, text= f"code is claimed by <a href='tg://user?id={user_id}'>user</a>")
            
    else:
        await message.reply_text("❌ Incorrect code. Try again!")

