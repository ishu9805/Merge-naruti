import asyncio
from pymongo import MongoClient
from pyrogram import Client, filters
from shivu import shivuu as app, collection, db

# Initialize the Pyrogram client
@app.on_message(filters.command("b"))
async def send_characters(client, message):
    try:
        # Fetch the character ID from the command
        character_id = message.command[1]
        
        # Fetch character data from MongoDB asynchronously
        character = await collection.find_one({'id': character_id})
        if not character:
            await app.send_message(chat_id="-1002398468292", text=f"🚫 *Character with ID {character_id} not found.*")
            return

        # Access character data directly
        character_id = character.get('id', '❓')
        character_name = character.get('name', '❓')
        character_anime = character.get('anime', '❓')
        rarity_id = character.get('rarity', '❓')
        image_url = character.get('img_url', '')
        video_url = character.get('vid_url', '')

        # Generate rarity message
        rarity_message = {
            "⚪️ Common": "🌱 Simple yet charming!",
            "🟣 Rare": "✨ A gem worth collecting!",
            "🟡 Legendary": "🌟 Legends never die!",
            "🟢 Medium": "🔄 A balance of power!",
            "💮 Special Edition": "🎉 Limited and exclusive treasures await!",
            "🔮 Limited Edition": "⏳ Catch it before it disappears!",
            "💸 Premium Edition": "👑 Luxury at its finest!",
            "🌤 Summer": "🏖️ Embrace the sunshine and fun!",
            "🎐 Celestial": "🌌 Reach for the stars and beyond!",
            "❄️ Winter": "⛄ Experience the magic of winter wonderland!",
            "💝 Valentine": "💖 Love is in the air!",
            "🎃 Halloween": "🦇 Get ready for spooky surprises!",
            "🎄 Christmas Special": "❄️ Celebrate the joy of the season!",
            "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐": "🌌 Boundless and extraordinary!",
            "🎭 Cosplay Master 🎭": "🎭 Crafting the art of transformation!",
            "🎗️ 𝘼𝙣𝙞𝙢𝙖𝙩𝙚𝙙": "🎞️ A stunning motion picture of art in action!"
        }.get(rarity_id, "Unknown rarity")

        # Create caption
        caption = (
            f"⛩️🌸 **Anime Character Showcase!** 🍥☯🍜\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👑 **Name:** {character_name}\n"
            f"🎥 **Anime:** {character_anime}\n"
            f"🌈 **Rarity:** {rarity_id}\n"
            f"📜 **ID:** {character_id}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{rarity_message}\n"
        )

        try:
            # Choose media based on available URL
            if image_url:
                await app.send_photo(chat_id="-1002398468292", photo=image_url, caption=caption)
            elif video_url:
                await app.send_video(chat_id="-1002398468292", video=video_url, caption=caption, supports_streaming=True)
            else:
                await app.send_message(chat_id=message.chat.id, text="🚫 *No media available for this character.*")

        except Exception as send_exception:
            print(f"Error sending character ID {character_id}: {str(send_exception)}")
            if "Peer is invalid" in str(send_exception):
                await app.send_message(chat_id=message.chat.id, text="🚫 *Invalid peer detected, stopping further messages.*")
                return  # Stop further execution if peer is invalid

    except Exception as e:
        await app.send_message(chat_id=message.chat.id, text=f"🚫 *Error:* {str(e)}")
