from pyrogram import Client, filters
from pyrogram.types import Message
from shivu import user_collection, collection
from .lock import command_lock
from . import app
import random

# Global variables to store giveaway data
giveaway_character = None
participants = []

# Start a giveaway
@app.on_message(filters.command("rgiveaway"))

async def start_giveaway(client: Client, message: Message):
    global giveaway_character, participants

    # Check if the user is an admin (replace ADMIN_ID with your ID)
    ADMIN_ID = 7378476666
    if message.from_user.id != ADMIN_ID:
        #await message.reply("🚫 **You are not authorized to start a giveaway.**")
        return

    # Check if a character ID is provided
    if len(message.command) < 2:
        #await message.reply("❌ **Usage:** `/rgiveaway <character_id>`")
        return

    character_id = message.command[1]

    # Fetch the character from the database
    character = await collection.find_one({"id": character_id})
    if not character:
        await message.reply("❌ **Character not found in the database.**")
        return

    # Store the character in the global variable
    giveaway_character = character
    participants = []  # Reset participants list

    # Send a photo with caption to the specified chat ID
    try:
        await client.send_photo(
            chat_id=-1001999201034,  # Replace with your chat ID
            photo=character.get("img_url"),
            caption=(
                f"🎉 **Giveaway Started!**\n"
                f"🏆 **Character:** {character.get('name', 'Unknown')}\n"
                f"🌟 **Rarity:** {character.get('rarity', 'Unknown')}\n"
                f"💬 **Use /participate to join the giveaway!**\n"
                f"🎁 **Winner will be selected randomly from participants.**"
            )
        )
    except Exception as e:
        print(f"Error sending giveaway start message: {e}")

    await message.reply("✅ **Giveaway started successfully!**")


# Participate in the giveaway
@app.on_message(filters.command("participate"))
@command_lock
async def participate_giveaway(client: Client, message: Message):
    global participants

    # Check if a giveaway is active
    if not giveaway_character:
        await message.reply("❌ **No active giveaway.**")
        return

    user_id = message.from_user.id

    # Check if the user is already participating
    if user_id in participants:
        await message.reply("ℹ️ **You are already participating in the giveaway.**")
        return

    # Add the user to the participants list
    participants.append(user_id)
    await message.reply("✅ **You have successfully joined the giveaway!**")


# End the giveaway and select a winner
@app.on_message(filters.command("endgiveaway"))
@command_lock
async def end_giveaway(client: Client, message: Message):
    global giveaway_character, participants

    # Check if the user is an admin (replace ADMIN_ID with your ID)
    ADMIN_ID = 7378476666
    if message.from_user.id != ADMIN_ID:
        
        return

    # Check if a giveaway is active
    if not giveaway_character:
        
        return

    # Check if there are enough participants
    if len(participants) <= 10:
        await message.reply("❌ **Giveaway canceled. Not enough participants (minimum 3 required).**")
        giveaway_character = None
        participants = []
        return

    # Select a random winner
    winner_id = random.choice(participants)

    # Fetch the winner's data
    winner = await user_collection.find_one({"id": winner_id})
    if not winner:
        await message.reply("❌ **Winner not found in the database.**")
        return

    # Add the character to the winner's collection
    await user_collection.update_one(
        {"id": winner_id},
        {"$push": {"characters": giveaway_character}}
    )

    # Send a DM to the winner
    try:
        await client.send_photo(
            chat_id=winner_id,
            photo=giveaway_character.get("ima_url"),
            caption=(
                f"🎉 **Congratulations! You won the giveaway!**\n"
                f"🏆 **Character:** {giveaway_character.get('name', 'Unknown')}\n"
                f"🌟 **Rarity:** {giveaway_character.get('rarity', 'Unknown')}\n"
                f"💬 **Check your collection to see your new character!**"
            )
        )
    except Exception as e:
        print(f"Error sending DM to winner: {e}")

    # Announce the winner in the group
    await message.send_message(
        chat_id=-1001999201034,
        text=
        f"🎉 **Giveaway ended!**\n"
        f"🏆 **Winner:** [{winner.get('first_name', 'GRABBER')}](tg://user?id={winner_id})\n"
        f"🌟 **Character:** {giveaway_character.get('name', 'Unknown')}, {giveaway_character.get('rarity')}"
    )

    # Reset the giveaway
    giveaway_character = None
    participants = []
