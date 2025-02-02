import asyncio
from pymongo import MongoClient
from pyrogram import Client, filters
from shivu import shivuu as app, collection, db

CHAT_ID = -1002398468292  # Store chat ID in a variable

@app.on_message(filters.command("b"))
async def send_characters(client, message):
    try:
        # Ensure the user provided a character ID
        if len(message.command) < 2:
            await app.send_message(message.chat.id, "🚫 *Please provide a character ID!*")
            return

        character_id = message.command[1]

        # Fetch character data from MongoDB (without await, as it's synchronous)
        character = collection.find_one({'id': character_id})
        if not character:
            await app.send_message(CHAT_ID, f"🚫 *Character with ID {character_id} not found.*")
            return

        # Extract character details
        character_name = character.get('name', '❓')
        character_anime = character.get('anime', '❓')
        rarity_id = character.get('rarity', '❓')
        image_url = character.get('img_url', '')
        video_url = character.get('vid_url', '')

        caption = (
            f"🌟 **Character Detail** 🌟\n"
            f"\n━━━━━━━━━━━━━━━━━━\n"
            f"🔹 **Name:** {character_name}\n"
            f"🔸 **Anime:** {character_anime}\n"
            f"🔹 **ID:** {character_id}\n"
            f"🔸 **Rarity:** {rarity_id}\n"
            f"\n━━━━━━━━━━━━━━━━━━\n"
        
        )


        # Send the media
        try:
            if image_url:
                await app.send_photo(CHAT_ID, photo=image_url, caption=caption)
            elif video_url:
                await app.send_video(CHAT_ID, video=video_url, caption=caption, supports_streaming=True)
            else:
                await app.send_message(message.chat.id, "🚫 *No media available for this character.*")

        except Exception as send_exception:
            print(f"Error sending character ID {character_id}: {str(send_exception)}")
            if "Peer is invalid" in str(send_exception):
                await app.send_message(message.chat.id, "🚫 *Invalid peer detected, stopping further messages.*")
                return

    except Exception as e:
        await app.send_message(message.chat.id, f"🚫 *Error:* {str(e)}")
