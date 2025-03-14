import os
import random
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from shivu import user_collection, collection
from .lock import command_lock

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
ADMIN_ID = int(os.getenv("ADMIN_ID", 7378476666))  # Replace with your admin ID
CHAT_ID = int(os.getenv("CHAT_ID", -1001999201034))  # Replace with your chat ID

# List of restricted character IDs (add the IDs you want to exclude)
RESTRICTED_CHARACTER_IDS = ["6591", "6586", "6588"]  # Replace with actual IDs

# Command to grab a Holi character
@command_lock
@app.on_message(filters.command("grabholi"))
async def grab_holi_character(client: Client, message: Message):
    try:
        # Restrict command to a specific chat
        if message.chat.id != -1002338924488:
            await message.reply("❌ **You can only use this command in @naruto_support_chat.**")
            return

        user_id = message.from_user.id

        # Check if the user has already claimed a Holi character
        user = await user_collection.find_one({"id": user_id})
        if user and user.get("holi_claimed", False):
            await message.reply("❌ **You have already claimed your Holi character!**")
            return

        # Fetch the user's collection
        if not user or len(user.get("characters", [])) < 10:
            await message.reply("❌ **You need at least 10 characters in your collection to claim a Holi character!**")
            return

        # Fetch Holi characters with rarity "🧧 Events" and exclude restricted IDs
        holi_characters = await collection.find({
            "rarity": "🧧 Events",
            "id": {"$nin": RESTRICTED_CHARACTER_IDS}  # Exclude restricted IDs
        }).to_list(length=100)  # Adjust length as needed

        if not holi_characters:
            await message.reply("❌ **No Holi characters available at the moment.**")
            return

        holi_character = random.choice(holi_characters)  # Get a random Holi character

        # Assign the Holi character to the user
        await user_collection.update_one(
            {"id": user_id},
            {
                "$push": {"characters": holi_character},  # Add the Holi character to the user's collection
                "$set": {"holi_claimed": True}  # Mark the user as having claimed a Holi character
            }
        )

        # Send the Holi character to the user
        await client.send_photo(
            chat_id=user_id,
            photo=holi_character.get("img_url"),
            caption=(
                f"🎉 **Congratulations! You have claimed a Holi character!**\n"
                f"🏆 **Name:** {holi_character.get('name', 'Unknown')}\n"
                f"**ID:** {holi_character.get('id')}\n"
                f"**Rarity:** {holi_character.get('rarity')}"
            )
        )

        await message.reply("✅ **You have successfully claimed your Holi character! Check your collection.**")
    except Exception as e:
        logger.error(f"Error in grab_holi_character: {e}")
        await message.reply("❌ **An error occurred while processing your request. Please try again later.**")

# Command to check how many users claimed the Holi character
@app.on_message(filters.command("holiusers"))
async def check_holi_users(client: Client, message: Message):
    try:
        # Only allow admins to use this command
        if message.from_user.id != ADMIN_ID:
            await message.reply("🚫 **You are not authorized to use this command.**")
            return

        # Get the number of users who claimed the Holi character
        num_users = await user_collection.count_documents({"holi_claimed": True})
        await message.reply(f"🎉 **Total users who claimed the Holi character:** {num_users}")
    except Exception as e:
        logger.error(f"Error in check_holi_users: {e}")
        await message.reply("❌ **An error occurred while processing your request. Please try again later.**")
