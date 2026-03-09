import urllib.request
from pymongo import ReturnDocument
import os
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
import requests
from pyrogram import filters
from pyrogram.types import InputMediaPhoto
from pyrogram import Client
from pyrogram.types import Message
from pymongo import UpdateOne
import random
import aiohttp
import asyncio
from pathlib import Path

try:
    from telegraph import upload_file
except Exception:
    def upload_file(_file_path):
        raise RuntimeError("telegraph package is not installed")

from shivu.modules import sudo_filter, uploader_filter
from shivu import UPDATE_CHAT, SUPPORT_CHAT, required_group_id, PHOTO_URL, OWNER_ID, PARTNER
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
    UPDATE_CHATps as UPDATE_CHAT_PS,
    dbps as db,
    pmusersps as pmusers,
    ban_collectionps as ban_collection,
    user_countps as user_count, 
    chat_dataps as chat_data,
)
# import sendall helpers
from shivu.modules.Sendall import generate_caption, _send_media_to_channel
# Channel ID for posting character information
CHARA_CHANNEL_ID = -1003295207951
UPLOAD_MEDIA_CHANNEL_ID = -1003724861652
UPLOAD_MEDIA_CHANNEL_USERNAME = "abcdefgh_naruto"

# Your imgBB API Key
IMGBB_API_KEY = "6d52008ec9026912f9f50c8ca96a09c3"

# Define the wrong format message and rarity map
WRONG_FORMAT_TEXT = """Wrong ❌ format...  eg. /upload reply to photo muzan-kibutsuji Demon-slayer 3

format:- /upload reply character-name anime-name rarity-number

use rarity number accordingly rarity Map

rarity_map = {
    1: "⚪️ Common",
    2: "🟣 Rare",
    3: "🟡 Legendary",
    4: "🟢 Medium",
    5: "💮 Special Edition",
    6: "🔮 Limited Edition",
    7: "💸 Premium Edition",
    8: "🌤 Summer",
    9: "🎐 Celestial",
    10: "❄️ Winter",
    11: "💝 Valentine",
    12: "🎃 Halloween",
    13: "🎄 Christmas Special",
    14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    15: "🎭 Cosplay Master 🎭",
    16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨",
    17: "🎖 Apex Lot ( AUCTION )",
    18: "🍑 Echhi",
    19: "☠️ 𝕯𝖎𝖛𝖎𝖓𝖊",
    20: "☔ Monsoon",
    21: "🪸 Aquatic",
    22: "🎨 Artistic",
    23: "💳 VIP SLOT",
    24: "👶 Chibi",
    25: "🏴‍☠️ Marauds"
}
"""

# Define the channel ID and rarity map
rarity_map = {
    1: "⚪️ Common",
    2: "🟣 Rare",
    3: "🟡 Legendary",
    4: "🟢 Medium",
    5: "💮 Special Edition",
    6: "🔮 Limited Edition",
    7: "💸 Premium Edition",
    8: "🌤 Summer",
    9: "🎐 Celestial",
    10: "❄️ Winter",
    11: "💝 Valentine",
    12: "🎃 Halloween",
    13: "🎄 Christmas Special",
    14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    15: "🎭 Cosplay Master 🎭",
    16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨",
    17: "🎖 Apex Lot ( AUCTION )",
    18: "🍑 Echhi",
    19: "☠️ 𝕯𝖎𝖛𝖎𝖓𝖊",
    20: "☔ Monsoon",
    21: "🪸 Aquatic",
    22: "🎨 Artistic",
    23: "💳 VIP SLOT",
    24: "👶 Chibi",
    25: "🏴‍☠️ Marauds"
}


# Global set to keep track of active IDs and a lock for safe access
active_ids = set()
id_lock = asyncio.Lock()

async def upload_to_imgbb(file_path, api_key=IMGBB_API_KEY):
    """
    Upload image to imgBB (primary upload service)
    """
    url = "https://api.imgbb.com/1/upload"
    
    # Read the file
    with open(file_path, "rb") as file:
        file_data = file.read()
    
    # Create form data
    data = aiohttp.FormData()
    data.add_field('key', api_key)
    data.add_field('image', file_data, filename=os.path.basename(file_path))
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            result = await response.json()
            
            if response.status == 200 and result.get("success"):
                return result["data"]["url"]
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"ImgBB upload fbailed: {error_msg}")

async def upload_to_telegraph(file_path):
    """
    Upload image to Telegraph (fallback option)
    """
    try:
        # Use the synchronous telegraph upload function
        result = upload_file(file_path)
        if isinstance(result, list) and len(result) > 0:
            return f"https://telegra.ph{result[0]}"
        else:
            raise Exception("Telegraph upload failed")
    except Exception as e:
        raise Exception(f"Telegraph upload error: {str(e)}")

async def upload_to_catbox(file_path):
    """
    Upload image to Catbox (secondary fallback option)
    """
    url = "https://catbox.moe/user/api.php"
    
    # Read the file
    with open(file_path, "rb") as file:
        file_data = file.read()
    
    # Create form data
    data = aiohttp.FormData()
    data.add_field('reqtype', 'fileupload')
    data.add_field('fileToUpload', file_data, filename=os.path.basename(file_path))
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            if response.status == 200:
                return (await response.text()).strip()
            else:
                raise Exception(f"Catbox upload failed with status {response.status}")

async def upload_image_with_fallback(file_path):
    """
    Try multiple image hosting services with fallback - imgBB as primary
    """
    services = [
        upload_to_imgbb,  # Primary - imgBB
        upload_to_telegraph,  # First fallback - Telegraph
        upload_to_catbox,  # Second fallback - Catbox
    ]
    
    last_error = None
    for service in services:
        try:
            print(f"Trying {service.__name__}...")
            url = await service(file_path)
            print(f"Success with {service.__name__}: {url}")
            return url
        except Exception as e:
            print(f"Failed with {service.__name__}: {str(e)}")
            last_error = e
            continue
    
    raise Exception(f"All image hosting services failed. Last error: {str(last_error)}")


def build_channel_message_link(message_id: int) -> str:
    """Build a public t.me link for the archive channel message."""
    return f"https://t.me/{UPLOAD_MEDIA_CHANNEL_USERNAME}/{message_id}"


async def archive_media_and_get_payload(client: Client, source_message: Message):
    """
    Send replied photo/video to the upload media channel and return storage payload.
    """
    downloaded_path = await source_message.download()
    suffix = Path(downloaded_path).suffix.lower()

    try:
        if source_message.video or suffix in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
            archived_msg = await client.send_video(
                chat_id=UPLOAD_MEDIA_CHANNEL_ID,
                video=downloaded_path,
            )
            payload = {
                "media_type": "video",
                "file_id": archived_msg.video.file_id,
                "message_link": build_channel_message_link(archived_msg.id),
            }
        else:
            archived_msg = await client.send_photo(
                chat_id=UPLOAD_MEDIA_CHANNEL_ID,
                photo=downloaded_path,
            )
            payload = {
                "media_type": "photo",
                "file_id": archived_msg.photo.file_id,
                "message_link": build_channel_message_link(archived_msg.id),
            }
        return payload
    finally:
        if downloaded_path and os.path.exists(downloaded_path):
            os.remove(downloaded_path)



def check_file_size(file_path, max_size_mb=30):
    """
    Check if file size is within limits
    """
    file_size = os.path.getsize(file_path)
    if file_size > max_size_mb * 1024 * 1024:
        raise Exception(f"File size ({file_size/1024/1024:.2f} MB) exceeds the {max_size_mb} MB limit.")
    return True

async def find_available_id():
    """
    Find the next available ID for a character
    """
    async with id_lock:
        cursor = collection.find().sort('id', 1)
        ids = [doc['id'] for doc in await cursor.to_list(length=None)]
        
        # Handle case where no documents exist
        if not ids:
            candidate_id = "01"
            active_ids.add(candidate_id)
            return candidate_id
        
        # Convert to integers for proper comparison
        int_ids = [int(id) for id in ids]
        
        for i in range(1, max(int_ids) + 2):
            candidate_id = str(i).zfill(2)
            if candidate_id not in ids and candidate_id not in active_ids:
                active_ids.add(candidate_id)
                return candidate_id
        return str(max(int_ids) + 1).zfill(2)

async def find_available_ids():
    """
    Find available IDs without reserving them
    """
    async with id_lock:
        cursor = collection.find().sort('id', 1)
        ids = [doc['id'] for doc in await cursor.to_list(length=None)]
        
        # Handle case where no documents exist
        if not ids:
            return "01"
        
        # Convert to integers for proper comparison
        int_ids = [int(id) for id in ids]
        
        for i in range(1, max(int_ids) + 2):
            candidate_id = str(i).zfill(2)
            if candidate_id not in ids and candidate_id not in active_ids:
                return candidate_id
        return str(max(int_ids) + 1).zfill(2)


@app.on_message(filters.command('delete') & sudo_filter)
async def delete(client: Client, message: Message):
    args = message.text.split(maxsplit=1)[1:]
    if len(args) != 1:
        await message.reply_text('Incorrect format... Please use: /delete ID')
        return

    character_id = args[0]
    character = await collection.find_one_and_delete({'id': character_id})

    if character:
        caption = (
            "❌ <b>CHARACTER DELETED</b>\n\n"
            f"🆔 ID: {character['id']}\n"
            f"👤 Name: {character['name']}\n"
            f"🎌 Anime: {character['anime']}\n"
            f"🌟 Rarity: {character['rarity']}\n\n"
            "✦━━━━━━━━━━━━━━━━━━━━✦"
        )

        await app.send_message(
            chat_id=CHARA_CHANNEL_ID,
            text=caption,
            parse_mode="HTML"
        )
        
    if character:
        bulk_operations = []
        async for user in user_collection.find():
            if 'characters' in user:
                user['characters'] = [char for char in user['characters'] if char['id'] != character_id]
                bulk_operations.append(
                    UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
                )

        if bulk_operations:
            await user_collection.bulk_write(bulk_operations)

        await message.reply_text('Character deleted from database and all user collections.')
    else:
        await message.reply_text('Character not found in database.')

async def check_total_characters(update: Update, context: CallbackContext) -> None:
    try:
        total_characters = await collection.count_documents({})
        await update.message.reply_text(f"Total number of characters: {total_characters}")
    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")

async def check(update: Update, context: CallbackContext) -> None:    
    try:
        args = context.args
        if len(context.args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /check id')
            return
            
        context.args[0]
        character = await collection.find_one({'id': args[0]}) 
            
        if character:
            # If character found, send the information along with the image URL
            message = f"<b>Character Name:</b> {character['name']}\n" \
                      f"<b>Anime Name:</b> {character['anime']}\n" \
                      f"<b>Rarity:</b> {character['rarity']}\n" \
                      f"<b>ID:</b> {character['id']}\n"

            if 'img_url' in character:
                await context.bot.send_photo(chat_id=update.effective_chat.id,
                                             photo=character['img_url'],
                                             caption=message,
                                             parse_mode='HTML')
            elif 'vid_url' in character:
                await context.bot.send_video(chat_id=update.effective_chat.id,
                                             video=character['vid_url'],
                                             caption=message,
                                             parse_mode='HTML')
        else:
             await update.message.reply_text("Character not found.")
    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")

application.add_handler(CommandHandler("total", check_total_characters))

@app.on_message(filters.command('update') & uploader_filter)
async def update(client: Client, message: Message):
    args = message.text.split(maxsplit=3)[1:]
    if len(args) != 3:
        await message.reply_text('Incorrect format. Please use: /update id field new_value')
        return

    character_id = args[0]
    field = args[1]
    new_value = args[2]

    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text('Character not found.')
        return

    valid_fields = ['img_url', 'name', 'anime', 'rarity']
    if field not in valid_fields:
        await message.reply_text(f'Invalid field. Please use one of the following: {", ".join(valid_fields)}')
        return

    if field in ['name', 'anime']:
        new_value = new_value.replace('-', ' ').title()
    elif field == 'rarity':
        try:
            new_value = rarity_map[int(new_value)]
        except KeyError:
            await message.reply_text('Invalid rarity. Please use a number between 1 and 22.')
            return

    await collection.update_one({'id': character_id}, {'$set': {field: new_value}})
    # refresh character
    updated_character = await collection.find_one({'id': character_id})

    await _send_media_to_channel(
        updated_character,
        action="updated",
        actor_id=message.from_user.id,
        actor_name=message.from_user.first_name
    )

    bulk_operations = []
    async for user in user_collection.find():
        if 'characters' in user:
            for char in user['characters']:
                if char['id'] == character_id:
                    char[field] = new_value
            bulk_operations.append(
                UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
            )

    if bulk_operations:
        await user_collection.bulk_write(bulk_operations)

    await message.reply_text('Update done in Database and all user collections.')

@app.on_message(filters.command('r') & sudo_filter)
async def update_rarity(client: Client, message: Message):
    args = message.text.split(maxsplit=2)[1:]
    if len(args) != 2:
        await message.reply_text('Incorrect format. Please use: /r id rarity')
        return

    character_id = args[0]
    new_rarity = args[1]

    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text('Character not found.')
        return

    try:
        new_rarity_value = rarity_map[int(new_rarity)]
    except KeyError:
        await message.reply_text('Invalid rarity. Please use a number between 1 and 22.')
        return

    await collection.update_one({'id': character_id}, {'$set': {'rarity': new_rarity_value}})

    bulk_operations = []
    async for user in user_collection.find():
        if 'characters' in user:
            for char in user['characters']:
                if char['id'] == character_id:
                    char['rarity'] = new_rarity_value
            bulk_operations.append(
                UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
            )

    if bulk_operations:
        await user_collection.bulk_write(bulk_operations)

    await message.reply_text('Rarity updated in Database and all user collections.')

@app.on_message(filters.command('arrange') & sudo_filter)
async def arrange_characters(client: Client, message: Message):
    characters = await collection.find().sort('id', 1).to_list(length=None)
    if not characters:
        await message.reply_text('No characters found in the database.')
        return

    old_to_new_id_map = {}
    new_id_counter = 1

    bulk_operations = []
    for character in characters:
        old_id = character['id']
        new_id = str(new_id_counter).zfill(2)
        old_to_new_id_map[old_id] = new_id

        if old_id != new_id:
            bulk_operations.append(
                UpdateOne({'_id': character['_id']}, {'$set': {'id': new_id}})
            )
        new_id_counter += 1

    if bulk_operations:
        await collection.bulk_write(bulk_operations)

    user_bulk_operations = []
    async for user in user_collection.find():
        if 'characters' in user:
            for char in user['characters']:
                if char['id'] in old_to_new_id_map:
                    char['id'] = old_to_new_id_map[char['id']]
            user_bulk_operations.append(
                UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
            )

    if user_bulk_operations:
        await user_collection.bulk_write(user_bulk_operations)

    await message.reply_text('Characters have been rearranged and IDs updated successfully.')

CHECK_HANDLER = CommandHandler('f', check, block=False)
application.add_handler(CHECK_HANDLER)

@shivuu.on_message(filters.command("vadd") & uploader_filter)
async def upload_video_character(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        await message.reply_text("Please reply to a video or video document.")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.reply_text("Wrong format. Use: /vadd (reply to video) character-name anime-name")
        return

    character_name = args[1].replace('-', ' ').title()
    anime = args[2].replace('-', ' ').title()

    available_id = None
    try:
        available_id = await find_available_id()
        media_payload = await archive_media_and_get_payload(client, reply)

        if media_payload['media_type'] != 'video':
            await message.reply_text("❌ Please reply to a valid video file.")
            return

        character = {
            'name': character_name,
            'anime': anime,
            'rarity': "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣",
            'id': available_id,
            'vid_url': media_payload['file_id'],
            'message_link': media_payload['message_link'],
            'slock': "false",
            'added': message.from_user.id
        }

        await client.send_video(
            chat_id=CHARA_CHANNEL_ID,
            video=media_payload['file_id'],
            caption=(
                f"🎥 **New Character Added** 🎥\n\n"
                f"Character Name: {character_name}\n"
                f"Anime Name: {anime}\n"
                f"Rarity: '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣'\n"
                f"ID: {available_id}\n"
                f"Added by [{message.from_user.first_name}](tg://user?id={message.from_user.id})"
            ),
        )

        await collection.insert_one(character)
        await message.reply_text("✅ Video character added successfully.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to upload character. Error: {e}")
    finally:
        if available_id:
            async with id_lock:
                active_ids.discard(available_id)



@shivuu.on_message(filters.command(["updateimg"]) & uploader_filter)
async def update_image(client, message):
    """
    Command to update character image by replying to a photo with the character ID
    Format: /updateimg [character_id]
    """
    reply = message.reply_to_message
    if not reply or not (reply.photo or reply.document):
        await message.reply_text("Please reply to a photo or document with this command.")
        return
        
    args = message.text.split()
    if len(args) != 2:
        await message.reply_text("Wrong format. Use: /updateimg [character_id] (reply to image)")
        return
    
    character_id = args[1]
    
    # Check if character exists
    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text(f"Character with ID {character_id} not found.")
        return
    
    try:
        processing_message = await message.reply("<ᴜᴘᴅᴀᴛɪɴɢ ɪᴍᴀɢᴇ...>")
        
        media_payload = await archive_media_and_get_payload(client, reply)
        media_file_id = media_payload['file_id']
        media_type = media_payload['media_type']

        update_fields = {'message_link': media_payload['message_link']}
        if media_type == 'video':
            update_fields['vid_url'] = media_file_id
            update_fields['img_url'] = character.get('img_url', '')
        else:
            update_fields['img_url'] = media_file_id
            update_fields['vid_url'] = character.get('vid_url', '')

        # Update character in the database
        await collection.update_one(
            {'id': character_id},
            {'$set': update_fields}
        )

        # Update all user collections that have this character
        bulk_operations = []
        async for user in user_collection.find():
            if 'characters' in user:
                for char in user['characters']:
                    if char['id'] == character_id:
                        char.update(update_fields)
                bulk_operations.append(
                    UpdateOne({'_id': user['_id']}, {'$set': {'characters': user['characters']}})
                )

        if bulk_operations:
            await user_collection.bulk_write(bulk_operations)

        # Send confirmation message
        await message.reply_text(f"✅ Media updated successfully for character ID: {character_id}")

        # Send updated character info to channel
        caption = (
            f"🔄 **Character Media Updated** 🔄\n"
            f"\n━━━━━━━━━━━━━━━━━━\n"
            f"🔹 **Name:** {character['name']}\n"
            f"🔸 **Anime:** {character['anime']}\n"
            f"🔹 **ID:** {character_id}\n"
            f"🔸 **Rarity:** {character['rarity']}\n"
            f"Updated by [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n"
            f"\n━━━━━━━━━━━━━━━━━━\n"
        )

        if media_type == 'video':
            await client.send_video(
                chat_id=CHARA_CHANNEL_ID,
                video=media_file_id,
                caption=caption,
            )
        else:
            await client.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=media_file_id,
                caption=caption,
            )

    except Exception as e:
        error_msg = f"❌ Image update failed. Error: {str(e)}"
        await message.reply_text(error_msg)
        print(error_msg)  # Log the error for debugging
    
SUPPORT_ID = -1003159072405
@app.on_message(filters.group & filters.chat(SUPPORT_ID))
async def auto_upload_from_group(client, message):
    """
    Auto-upload character from group posts - extracts info from caption
    Format in caption: "Character Name - Anime Name - Rarity Number"
    Example: "Naruto Uzumaki - Naruto - 3"
    """
    
    # For groups, get the user who sent the message
    if message.from_user:
        uploader = message.from_user.id
    else:
        uploader = "Unknown"  # Fallback for anonymous sends
    
    # Check if message has caption with required format
    if not message.caption:
        await client.send_message(
            chat_id=message.chat.id,
            text="❌ No caption found. Please use format: Character Name - Anime Name - Rarity Number"
        )
        return
    
    try:
        # Parse caption - expected format: "Name - Anime - Rarity"
        parts = [part.strip() for part in message.caption.split('-')]
        
        if len(parts) != 3:
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Wrong caption format. Use: Character Name - Anime Name - Rarity Number\n\nExample: `Naruto Uzumaki - Naruto - 3`"
            )
            return
        
        character_name = parts[0].title()
        anime = parts[1].title()
        
        try:
            rarity = int(parts[2])
        except ValueError:
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Rarity must be a number. Please use a valid rarity number."
            )
            return
        
        # Validate rarity value
        if rarity not in rarity_map:
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ Invalid rarity value. Please use a valid rarity number from 1-25."
            )
            return
        
        rarity_text = rarity_map[rarity]
        available_id = None
        
        try:
            available_id = await find_available_id()
            
            # Archive media to upload channel and store file/link metadata
            media_payload = await archive_media_and_get_payload(client, message)

            # Prepare character data
            character = {
                'name': character_name,
                'anime': anime,
                'rarity': rarity_text,
                'id': available_id,
                'slock': "false",
                'uploader': uploader,
                'message_link': media_payload['message_link'],
            }

            if media_payload['media_type'] == 'video':
                character['vid_url'] = media_payload['file_id']
            else:
                character['img_url'] = media_payload['file_id']
            
            # Insert character into the database
            await collection.insert_one(character)

            # Send additional confirmation
            await client.send_message(
                chat_id=message.chat.id,
                text=f"✅ CHARACTER ADDED SUCCESSFULLY! ID: {available_id}"
            )
            
        except Exception as e:
            error_msg = f"❌ Character Upload Unsuccessful. Error: {str(e)}"
            await client.send_message(chat_id=message.chat.id, text=error_msg)  # Fixed: send to group instead of CHARA_CHANNEL_ID
            print(error_msg)  # Log the error for debugging
        
        finally:
            if available_id:
                async with id_lock:
                    active_ids.discard(available_id)
                    
    except Exception as e:
        error_msg = f"❌ Error processing auto-upload: {str(e)}"
        await client.send_message(chat_id=message.chat.id, text=error_msg)  # Fixed: send to group instead of CHARA_CHANNEL_ID
        print(error_msg)


@shivuu.on_message(filters.command(["upload"]) & uploader_filter)
async def ul(client, message):
    """
    Command to upload character information
    """
    reply = message.reply_to_message
    if not reply or not (reply.photo or reply.document):
        await message.reply_text("Please reply to a photo or document.")
        return
        
    args = message.text.split()
    if len(args) != 4:
        await client.send_message(chat_id=message.chat.id, text=WRONG_FORMAT_TEXT)
        return
    
    # Extract character details from the command arguments
    character_name = args[1].replace('-', ' ').title()
    anime = args[2].replace('-', ' ').title()
    
    try:
        rarity = int(args[3])
    except ValueError:
        await message.reply_text("Rarity must be a number.")
        return
    
    # Validate rarity value
    if rarity not in rarity_map:
        await message.reply_text("Invalid rarity value. Please use a valid rarity number.")
        return
    
    rarity_text = rarity_map[rarity]
    available_id = None
    
    try:
        available_id = await find_available_id()
        processing_message = await message.reply("<ᴘʀᴏᴄᴇꜱꜱɪɴɢ>....")
        
        # Archive media to upload channel and store file/link metadata
        media_payload = await archive_media_and_get_payload(client, reply)
        
        # Prepare character data
        character = {
            'name': character_name,
            'anime': anime,
            'rarity': rarity_text,
            'id': available_id,
            'slock': "false",
            'added': message.from_user.id,
            'message_link': media_payload['message_link']
        }

        if media_payload['media_type'] == 'video':
            character['vid_url'] = media_payload['file_id']
        else:
            character['img_url'] = media_payload['file_id']
        
        # Insert character into the database
        await collection.insert_one(character)
        await _send_media_to_channel(
            character,
            action="added",
            actor_id=message.from_user.id,
            actor_name=message.from_user.first_name
        )
        
        await message.reply_text(f'✅ CHARACTER ADDED SUCCESSFULLY! ID: {available_id}')
        
    except Exception as e:
        error_msg = f"❌ Character Upload Unsuccessful. Error: {str(e)}"
        await message.reply_text(error_msg)
        print(error_msg)  # Log the error for debugging
    
    finally:
        if available_id:
            async with id_lock:
                active_ids.discard(available_id)
