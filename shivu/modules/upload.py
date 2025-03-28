import urllib.request
from pymongo import ReturnDocument
import os
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
#, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT, OWNER_ID, user_collection
from . import uploader_filter

from telegraph import upload_file
from pyrogram import filters
#from shivu import shivuu, collection
from pyrogram.types import InputMediaPhoto
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import ReturnDocument, UpdateOne
import urllib.request
import random
from . import sudo_filter
#from shivu import application, collection, db, CHARA_CHANNEL_ID, user_collection
from . import uploader_filter
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
# Channel ID for posting character information (replace with your actual channel ID)
 

import os
import requests
#from shivu import shivuu, collection
from pyrogram import filters

# Define the wrong format message and rarity map
WRONG_FORMAT_TEXT = """Wrong ❌ format...  eg. /upload reply to photo muzan-kibutsuji Demon-slayer 3

format:- /upload reply character-name anime-name rarity-number

use rarity number accordingly rarity Map

rarity_map = {1: "⚪️ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium", 5: "💮 Special Edition", 6: "🔮 Limited Edition", 7: "💸 Premium Edition", 8: "🌤 Summer", 9: "🎐 Celestial", 10: "❄️ Winter", 11: "💝 Valentine", 12: "🎃 Halloween", 13: "🎄 Christmas Special", 14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐", 15: "🎭 Cosplay Master 🎭", 16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨"}
"""

# Define the channel ID and rarity map
rarity_map = {
    1: "⚪️ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium",
    5: "💮 Special Edition", 6: "🔮 Limited Edition", 7: "💸 Premium Edition",
    8: "🌤 Summer", 9: "🎐 Celestial", 10: "❄️ Winter", 11: "💝 Valentine",
    12: "🎃 Halloween", 13: "🎄 Christmas Special", 14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    15: "🎭 Cosplay Master 🎭", 17: "🎖 Apex Lot ( AUCTION )", 16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨"
}
# Function to find the next available ID for a character


from asyncio import Lock

# Global set to keep track of active IDs and a lock for safe access
active_ids = set()
id_lock = Lock()
import requests


def upload_to_catbox(file_path):
    url = "https://catbox.moe/user/api.php"
    # Set the payload to specify that the upload type is a file and choose the `fileupload` option
    payload = {
        'reqtype': 'fileupload',
    }
    # Open the file in binary mode and send it to Catbox
    files = {
        'fileToUpload': open(file_path, 'rb'),
    }
    # Send the POST request to Catbox with the file and payload
    response = requests.post(url, files=files, data=payload)

    # Check if the upload was successful
    if response.status_code == 200:
        return response.text.strip()  # Return the URL of the uploaded image
    else:
        raise Exception(f"Failed to upload to Catbox. Status Code: {response.status_code}")

# Example usage:


def upload_to_envs(file_path=None, file_url=None, expires=None, secret=None):
    url = "https://envs.sh"
    files = {}
    data = {}
    
    # If uploading a local file
    if file_path:
        try:
            files = {'file': open(file_path, 'rb')}
        except Exception as e:
            print(f"Error opening file: {str(e)}")
            return None
    
    # If uploading a remote URL
    elif file_url:
        data = {'url': file_url}
    
    # Add secret and expiration if provided
    if secret:
        data['secret'] = secret
    if expires:
        data['expires'] = expires  # Expiration time in hours
    
    # Try to make the request
    try:
        response = requests.post(url, files=files, data=data)
        
        # Close the file if it's a local file upload
        if file_path:
            files['file'].close()
        
        if response.status_code == 200:
            print("File uploaded successfully to envs.sh!")
            print("File URL:", response.text.strip())
            return response.text.strip()
        else:
            print("Failed to upload file to envs.sh.")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error during upload: {str(e)}")
        return None


def check_file_size(file_path, max_size_mb=20):
    if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
        raise Exception("File size exceeds the 10 MB limit.")
        


# Example usage:
# image_url = upload_to_catbox('path_to_your_image.jpg')
# print(image_url)

# Function to find the next available ID for a character
async def find_available_id():
    async with id_lock:  # Ensure only one upload can find and reserve an ID at a time
        cursor = collection.find().sort('id', 1)
        ids = [doc['id'] for doc in await cursor.to_list(length=None)]
        for i in range(1, max(map(int, ids)) + 2):  # +2 to account for the case where the max ID is the last one
            candidate_id = str(i).zfill(2)
            if candidate_id not in ids and candidate_id not in active_ids:
                active_ids.add(candidate_id)
                return candidate_id
        return str(max(map(int, ids)) + 1).zfill(2)  # Return the next available ID

async def find_available_ids():
    async with id_lock:  # Ensure only one upload can find and reserve an ID at a time
        cursor = collection.find().sort('id', 1)
        ids = [doc['id'] for doc in await cursor.to_list(length=None)]
        for i in range(1, max(map(int, ids)) + 2):  # +2 to account for the case where the max ID is the last one
            candidate_id = str(i).zfill(2)
            if candidate_id not in ids and candidate_id not in active_ids:
                #active_ids.add(candidate_id)
                return candidate_id
        return str(max(map(int, ids)) + 1).zfill(2) # Return the next available ID
        

@shivuu.on_message(filters.command(["uid"]) & uploader_filter)
async def ulo(client, message):
    available_id = await find_available_ids()
    await client.send_message(chat_id=message.chat.id, text=f"{available_id}")
            
# Command to upload character information
@shivuu.on_message(filters.command(["upload"]) & uploader_filter)
async def ul(client, message):
    reply = message.reply_to_message
    if reply and (reply.photo or reply.document):
        args = message.text.split()
        if len(args) != 4:
            await client.send_message(chat_id=message.chat.id, text=WRONG_FORMAT_TEXT)
            return
        
        # Extract cer details from the command arguments
        character_name = args[1].replace('-', ' ').title()
        anime = args[2].replace('-', ' ').title()
        rarity = int(args[3])
        
        # Validate rarity value
        if rarity not in rarity_map:
            await message.reply_text("Invalid rarity value. Please use a value between 1 and 13.")
            return
        
        rarity_text = rarity_map[rarity]
        
        try:
            available_id = await find_available_id()

            # Prepare character data
            character = {
                'name': character_name,
                'anime': anime,
                'rarity': rarity_text,
                'id': available_id,
                'added': message.from_user.id
            }

            processing_message = await message.reply("<ᴘʀᴏᴄᴇꜱꜱɪɴɢ>....")
            path = await reply.download()

            # Upload image to Catbox
            catbox_url = upload_to_catbox(path)
            character['img_url'] = catbox_url
            
            # Insert character into the database
            await collection.insert_one(character)

            # Send character details to the channel
            await client.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=catbox_url,
                caption=(
                    f"Character Name: {character_name}\n"
                    f"Anime Name: {anime}\n"
                    f"Rarity: {rarity_text}\n"
                    f"ID: {available_id}\n"
                    f"Added by [{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                ),
            )
            await client.send_photo(
                chat_id=-1002567797000,
                photo=catbox_url,
                caption = (
                f"🌟 **Character Detail** 🌟\n"
                    f"\n━━━━━━━━━━━━━━━━━━\n"
                    f"🔹 **Name:** {character_name}\n"
                    f"🔸 **Anime:** {anime}\n"
                    f"🔹 **ID:** {available_id}\n"
                    f"🔸 **Rarity:** {rarity_text}\n"
                    f"Added by [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n"
                    f"\n━━━━━━━━━━━━━━━━━━\n"
                ),
            )
            await message.reply_text(f'CHARACTER ADDED.... id :- {available_id}')
        
        except Exception as e:
            await message.reply_text(f"Character Upload Unsuccessful. Error: {str(e)}")
        
        finally:
            os.remove(path)  # Clean up the downloaded file
            async with id_lock:
                active_ids.discard(available_id)  # Remove the ID from the active set once done
    else:
        await message.reply_text("Please reply to a photo or document.")


        
@app.on_message(filters.command('delete') & sudo_filter)
async def delete(client: Client, message: Message):
    args = message.text.split(maxsplit=1)[1:]
    if len(args) != 1:
        await message.reply_text('Incorrect format... Please use: /delete ID')
        return

    character_id = args[0]
    character = await collection.find_one_and_delete({'id': character_id})
   
 

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
            
        character_id = context.args[0]
        
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
            await message.reply_text('Invalid rarity. Please use a number between 1 and 10.')
            return

   
    await collection.update_one({'id': character_id}, {'$set': {field: new_value}})
    await client.message(
                chat_id=7378476666,
            
                text=(
                    f"{character['id']}"
                    f"Added by [{message.from_user.first_name}](tg://user?id={message.from_user.id})"
                ),
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
        await message.reply_text('Invalid rarity. Please use a number between 1 and 10.')
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

    await message.reply_text('Characters have been rearranged and')
    



CHECK_HANDLER = CommandHandler('f', check, block=False)
application.add_handler(CHECK_HANDLER)

@shivuu.on_message(filters.command("vadd") & filters.user([7378476666]))
async def upload_video_character(client, message):
    args = message.text.split(maxsplit=3)
    if len(args) != 4:
        print("lol")
        return

    character_name = args[1].replace('-', ' ').title()
    anime = args[2].replace('-', ' ').title()
    
    vid_url = args[3]

    

    

    # Generate the next available ID
    available_id = await find_available_id()

    character = {
        'name': character_name,
        'anime': anime,
        'rarity': "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣",
        'id': available_id,
        'vid_url': vid_url,
    }

    try:
        # Send the video to the character channel
        await client.send_video(
            chat_id=CHARA_CHANNEL_ID,
            video=vid_url,
            caption=(
                f"🎥 **New Character Added** 🎥\n\n"
                f"Character Name: {character_name}\n"
                f"Anime Name: {anime}\n"
                f"Rarity: '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣'\n"
                f"ID: {available_id}\n"
                f"Added by [{message.from_user.first_name}](tg://user?id={message.from_user.id})"
            ),
        )

        # Insert the character data into MongoDB
        await collection.insert_one(character)

        await message.reply_text("✅ Video character added successfully.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to upload character. Error: {e}")
        
