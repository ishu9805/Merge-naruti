import urllib.request
from pymongo import ReturnDocument
import os
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT, OWNER_ID, user_collection

from shivu import shops_collection
from telegraph import upload_file
from pyrogram import filters
from shivu import shivuu, collection
from pyrogram.types import InputMediaPhoto
import os


# Channel ID for posting character information (replace with your actual channel ID)
CHARA_CHANNEL_ID = -1002117539029

import os
import requests
from shivu import shivuu, collection
from pyrogram import filters

# Define the wrong format message and rarity map
WRONG_FORMAT_TEXT = """Wrong ❌ format...  eg. /upload reply to photo muzan-kibutsuji Demon-slayer 3

format:- /upload reply character-name anime-name rarity-number

use rarity number accordingly rarity Map

rarity_map = {1: "⚪️ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium", 5: "💮 Special Edition", 6: "🔮 Limited Edition", 7: "💸 Premium Edition", 8: "🌤 Summer", 9: "🎐 Celestial", 10: "❄️ Winter", 11: "💝 Valentine", 12: "🎃 Halloween", 13: "🎄 Christmas Special", 14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐", 15: "🎭 Cosplay Master 🎭"}
"""

# Define the channel ID and rarity map
CHARA_CHANNEL_ID = -1002117539029
rarity_map = {
    1: "⚪️ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium",
    5: "💮 Special Edition", 6: "🔮 Limited Edition", 7: "💸 Premium Edition",
    8: "🌤 Summer", 9: "🎐 Celestial", 10: "❄️ Winter", 11: "💝 Valentine",
    12: "🎃 Halloween", 13: "🎄 Christmas Special", 14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    15: "🎭 Cosplay Master 🎭", 16: "🎖 Apex Lot ( AUCTION )"
}
# Function to find the next available ID for a character


from asyncio import Lock

# Global set to keep track of active IDs and a lock for safe access
active_ids = set()
id_lock = Lock()
import requests

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

# Command to upload character information
@shivuu.on_message(filters.command(["upload"]) & filters.user([6965783469, 7036155390, 6759666329, 7228816990, 7469481988, 5316848198, 7378476666, 5763471570]))
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
                'id': available_id
            }

            processing_message = await message.reply("<ᴘʀᴏᴄᴇꜱꜱɪɴɢ>....")
            path = await reply.download()

            # Upload image to Catbox
            catbox_url = upload_to_envs(path)
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
            await message.reply_text(f'CHARACTER ADDED.... id :- {available_id}')
        
        except Exception as e:
            await message.reply_text(f"Character Upload Unsuccessful. Error: {str(e)}")
        
        finally:
            os.remove(path)  # Clean up the downloaded file
            async with id_lock:
                active_ids.discard(available_id)  # Remove the ID from the active set once done
    else:
        await message.reply_text("Please reply to a photo or document.")
        
async def delete(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text('Incorrect format. Please use: /delete_character <id>')
            return

        # Extract character ID
        character_id = args[0]

        # Delete the character from the main collection
        main_result = await collection.delete_one({"id": character_id})
        if main_result.deleted_count == 0:
            await update.message.reply_text("Character not found in the main collection.")
            return

        # Delete the character from user collections
        user_result = await user_collection.update_many(
            {"characters.id": character_id},
            {"$pull": {"characters": {"id": character_id}}}
        )

        if user_result.modified_count > 0:
            await update.message.reply_text(
                f"Character with ID {character_id} deleted successfully.\n"
                f"Removed from {user_result.modified_count} user collections."
            )
        else:
            await update.message.reply_text(
                f"Character with ID {character_id} deleted from the main collection but not found in user collections."
            )

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

       

async def check_total_characters(update: Update, context: CallbackContext) -> None:
    try:
        total_characters = await collection.count_documents({})
        
        await update.message.reply_text(f"Total number of characters: {total_characters}")
    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")


async def add_sudo_user(update: Update, context: CallbackContext) -> None:
    if int(update.effective_user.id) == 6257270528:  # Replace OWNER_ID with the ID of the bot owner
        if update.message.reply_to_message and update.message.reply_to_message.from_user:
            new_sudo_user_id = str(update.message.reply_to_message.from_user.id)
            if new_sudo_user_id not in sudo_users:
                sudo_users.append(new_sudo_user_id)
                await update.message.reply_text("User added to sudo users.")
            else:
                await update.message.reply_text("User is already in sudo users.")
        else:
            await update.message.reply_text("Please reply to a message from the user you want to add to sudo users.")
    else:
        await update.message.reply_text("You are not authorized to use this command.")



async def updates(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        args = context.args
        if len(args) != 3:
            await update.message.reply_text('Incorrect format. Please use: /update_character_all id field new_value')
            return

        # Extract arguments
        character_id = args[0]
        field = args[1]
        new_value = args[2]

        # Check if the field is valid
        valid_fields = ['img_url', 'name', 'anime', 'rarity']
        if field not in valid_fields:
            await update.message.reply_text(f'Invalid field. Please use one of the following: {", ".join(valid_fields)}')
            return

        # Adjust value formatting
        if field in ['name', 'anime']:
            new_value = new_value.replace('-', ' ').title()
        elif field == 'rarity':
            rarity_map = {
                1: "⚪️ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium",
                5: "💮 Special Edition", 6: "🔮 Limited Edition", 7: "💸 Premium Edition",
                8: "🌤 Summer", 9: "🎐 Celestial", 10: "❄️ Winter", 11: "💝 Valentine",
                12: "🎃 Halloween", 13: "🎄 Christmas Special", 14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
                15: "🎭 Cosplay Master 🎭", 16: "🎖 Apex Lot ( AUCTION )"
            }
            try:
                new_value = rarity_map[int(new_value)]
            except (ValueError, KeyError):
                await update.message.reply_text('Invalid rarity. Please provide a valid rarity number.')
                return

        collection_result = await collection.update_one(
            {"id": character_id},
            {"$set": {field: new_value}}
        )
        # Update the character in `user_collection`
        user_result = await user_collection.update_many(
            {"characters.id": character_id},
            {"$set": {f"characters.$[elem].{field}": new_value}},
            array_filters=[{"elem.id": character_id}]
        )

        total_modified = collection_result.modified_count + user_result.modified_count

        if total_modified == 0:
            await update.message.reply_text("Character not found in any collection.")
        else:
            await update.message.reply_text(f"Character updated successfully in {total_modified} documents across all collections.")

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

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
            



ADD_SUDO_USER_HANDLER = CommandHandler('add_sudo_user', add_sudo_user, block=False)
application.add_handler(ADD_SUDO_USER_HANDLER)
       
        

ADD_SUDO_USER_HANDLER = CommandHandler('addsudo', add_sudo_user, block=False)
application.add_handler(ADD_SUDO_USER_HANDLER)


application.add_handler(CommandHandler("total", check_total_characters))


DELETE_HANDLER = CommandHandler('delete', delete, block=False)
application.add_handler(DELETE_HANDLER)
UPDATE_HANDLER = CommandHandler('update', updates, block=False)
application.add_handler(UPDATE_HANDLER)


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
        
