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
        character_id = character['id'] if 'id' in character else '❓'
        character_name = character['name'] if 'name' in character else '❓'
        character_anime = character['anime'] if 'anime' in character else '❓'
        rarity_id = character['rarity'] if 'rarity' in character else '❓'
        image_url = character['img_url'] if 'img_url' in character else ''

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
            "🎭 Cosplay Master 🎭": "🎭 Crafting the art of transformation!"
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
            # Send image with caption
            if image_url:
                await app.send_photo(chat_id="-1002398468292", photo=image_url, caption=caption)
        except Exception as send_exception:
            print(f"Error sending character ID {character_id}: {str(send_exception)}")
            if "Peer is invalid" in str(send_exception):
                await app.send_message(chat_id="-1002398468292", text="🚫 *Invalid peer detected, stopping further messages.*")
                return  # Stop further execution if peer is invalid

    except Exception as e:
        await app.send_message(chat_id="-1002398468292", text=f"🚫 *Error:* {str(e)}")
