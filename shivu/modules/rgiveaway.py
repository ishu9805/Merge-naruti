from pyrogram import Client, filters
from pyrogram.types import Message
from shivu import user_collection, collection
from . import app
from .lock import command_lock
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
# Participate in the giveaway
@app.on_message(filters.command("participate"))
@command_lock
async def participate_giveaway(client: Client, message: Message):
    if not giveaway.character:
        await message.reply("❌ **No active giveaway.**")
        return

    user_id = message.from_user.id
    if user_id in giveaway.participants:
        await message.reply("ℹ️ **You are already participating in the giveaway.**")
        return

    giveaway.participants.append(user_id)
    await message.reply(f"✅ **You have successfully joined the giveaway!**\n👥 **Total Participants:** {len(giveaway.participants)}")
    await client.send_message(
        chat_id=-1002338924488,
        text=(
            f"[{message.from_user.first_name}](tg://user?id={user_id}) participated\n"
            f"👥 **Total Participants:** {len(giveaway.participants)}"
        )
    )

# End the giveaway and select a winner
# End the giveaway
@app.on_message(filters.command("endgiveaway"))
@command_lock
async def end_giveaway(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("🚫 **You are not authorized to end the giveaway.**")
        return

    if not giveaway.character:
        await message.reply("❌ **No active giveaway to end.**")
        return

    if len(giveaway.participants) < 1:
        await message.reply("❌ **No participants in the giveaway.**")
        return

    winner_id = random.choice(giveaway.participants)
    winner = await user_collection.find_one({"id": winner_id})
    if not winner:
        await message.reply("❌ **Winner not found in the database.**")
        return

    await user_collection.update_one(
        {"id": winner_id},
        {"$push": {"characters": giveaway.character}}
    )

    caption = (
        f"🎉 **Congratulations! You won the giveaway!**\n"
        f"🏆 **Character:** {giveaway.character.get('name', 'Unknown')}\n"
        f"🌟 **Rarity:** {giveaway.character.get('rarity', 'Unknown')}\n"
        f"💬 **Check your collection to see your new character!**"
    )
    await send_photo_with_caption(client, winner_id, giveaway.character.get("img_url"), caption)

    await client.send_message(
        chat_id=CHAT_ID,
        text=(
            f"🎉 **Giveaway ended!**\n"
            f"🏆 **Winner:** [{winner.get('first_name', 'GRABBER')}](tg://user?id={winner_id})\n"
            f"🌟 **Character:** {giveaway.character.get('name', 'Unknown')}, {giveaway.character.get('rarity')}\n"
            f"👥 **Total Participants:** {len(giveaway.participants)}"
        )
    )

    giveaway.character = None
    giveaway.participants = []
