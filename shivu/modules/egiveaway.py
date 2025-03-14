import os
import random
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto
from shivu import user_collection, collection
from . import app
from .lock import command_lock

# Environment variables
ADMIN_ID = int(os.getenv("ADMIN_ID", 7378476666))  # Replace with your admin ID
CHAT_ID = int(os.getenv("CHAT_ID", -1001999201034))  # Replace with your chat ID

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for giveaway data
giveaway_character1 = None  # Prize for the first winner
giveaway_character2 = None  # Prize for the second winner
giveaway_participants = []  # List of participant user IDs
giveaway_elimination_active = False  # Flag to indicate if elimination is active

# Helper function to send media group
async def send_media_group_with_caption(client, chat_id, media, caption):
    try:
        await client.send_media_group(chat_id=chat_id, media=media)
        await client.send_message(chat_id=chat_id, text=caption)
    except Exception as e:
        logger.error(f"Error sending media group: {e}")

# Start an elimination giveaway
@app.on_message(filters.command("egiveaway"))
async def start_elimination_giveaway(client: Client, message: Message):
    try:
        global giveaway_character1, giveaway_character2, giveaway_participants, giveaway_elimination_active

        if message.from_user.id != ADMIN_ID:
            return

        if len(message.command) < 3:
            await message.reply("❌ **Usage:** `/egiveaway <character_id> <character_id2>`")
            return

        character_id1 = message.command[1]
        character_id2 = message.command[2]

        # Fetch characters from the database
        character1 = await collection.find_one({"id": character_id1})
        character2 = await collection.find_one({"id": character_id2})

        if not character1 or not character2:
            await message.reply("❌ **One or both characters not found in the database.**")
            return

        giveaway_character1 = character1
        giveaway_character2 = character2
        giveaway_participants = []
        giveaway_elimination_active = False  # Reset elimination flag

        # Prepare media group
        media = [
            InputMediaPhoto(character1.get("img_url"), caption=f"🏆 **Prize 1:** {character1.get('name', 'Unknown')}\n**ID:** {character1.get('id')}\n**Rarity:** {character1.get('rarity')}"),
            InputMediaPhoto(character2.get("img_url"), caption=f"🏆 **Prize 2:** {character2.get('name', 'Unknown')}\n**ID:** {character2.get('id')}\n**Rarity:** {character2.get('rarity')}")
        ]

        # Prepare caption
        caption = (
            f"🎉 **Elimination Giveaway Started!**\n"
            f"💬 **Use /join to participate!**\n"
            f"👥 **Participants:** {len(giveaway_participants)}"
        )

        # Send media group and caption
        await send_media_group_with_caption(client, CHAT_ID, media, caption)
        await message.reply("✅ **Elimination giveaway started successfully!**")
    except Exception as e:
        logger.error(f"Error in start_elimination_giveaway: {e}")

# Join the elimination giveaway
@app.on_message(filters.command("join"))
@command_lock
async def join_giveaway(client: Client, message: Message):
    try:
        global giveaway_participants, giveaway_elimination_active

        if not giveaway_character1 or not giveaway_character2:
            await message.reply("❌ **No active elimination giveaway.**")
            return

        if giveaway_elimination_active:
            await message.reply("❌ **The elimination process has started. You can no longer join.**")
            return

        user_id = message.from_user.id
        if user_id in giveaway_participants:
            await message.reply("ℹ️ **You are already participating in the giveaway.**")
            return

        giveaway_participants.append(user_id)
        await message.reply(f"✅ **You have successfully joined the elimination giveaway!**\n👥 **Total Participants:** {len(giveaway_participants)}")
        await client.send_message(
            chat_id=-1002338924488,
            text=(
                f"[{message.from_user.first_name}](tg://user?id={user_id}) participated\n"
                f"👥 **Total Participants:** {len(giveaway_participants)}"
            )
        )
    except Exception as e:
        logger.error(f"Error in join_giveaway: {e}")

# Start the elimination process
@app.on_message(filters.command("startelimination"))
async def start_elimination(client: Client, message: Message):
    try:
        global giveaway_elimination_active

        if message.from_user.id != ADMIN_ID:
            await message.reply("🚫 **You are not authorized to start the elimination process.**")
            return

        if not giveaway_character1 or not giveaway_character2:
            await message.reply("❌ **No active elimination giveaway to start.**")
            return

        if len(giveaway_participants) < 2:
            await message.reply("❌ **Not enough participants to start elimination.**")
            return

        # Set elimination as active
        giveaway_elimination_active = True

        # Start the elimination task
        asyncio.create_task(elimination_process(client))

        await message.reply("✅ **Elimination process started! No new participants can join.**")
    except Exception as e:
        logger.error(f"Error in start_elimination: {e}")


async def elimination_process(client: Client):
    try:
        global giveaway_character1, giveaway_character2, giveaway_participants, giveaway_elimination_active

        while len(giveaway_participants) > 1:
            if len(giveaway_participants) > 40:
                eliminate_count = 5
            elif len(giveaway_participants) > 20:
                eliminate_count = 3
            elif len(giveaway_participants) > 5:
                eliminate_count = 2
            else:
                eliminate_count = 1  # Last 2 users: eliminate 1 to determine the winner

            # Ensure eliminate_count does not exceed participants
            eliminate_count = min(eliminate_count, len(giveaway_participants) - 1)

            # Eliminate users
            eliminated = random.sample(giveaway_participants, eliminate_count)
            giveaway_participants = [user for user in giveaway_participants if user not in eliminated]

            # Announce eliminated users
            eliminated_names = []
            for user_id in eliminated:
                user = await client.get_users(user_id)
                eliminated_names.append(f"[{user.first_name}](tg://user?id={user_id})")

            await client.send_message(
                chat_id=-1002338924488,
                text=(
                    f"🚫 **Eliminated Users:** {', '.join(eliminated_names)}\n"
                    f"👥 **Remaining Participants:** {len(giveaway_participants)}"
                )
            )

            # Send IDs of the last 5 participants to the group
            if len(giveaway_participants) <= 5:  # Changed condition to <= 5
                # Fetch user data for the last 5 participants
                last_five_users = []
                for user_id in giveaway_participants:
                    user = await client.get_users(user_id)  # Fetch user data
                    last_five_users.append(f"[{user.first_name}](tg://user?id={user_id})")

                # Construct the message
                last_five_ids = "\n".join(last_five_users)

                # Send the message
                await client.send_message(
                    chat_id=-1002338924488,
                    text=(
                        f"🎉 **Last {len(giveaway_participants)} Participants:**\n"
                        f"{last_five_ids}"
                    )
                )

            # Wait for 45 seconds before the next elimination
            await asyncio.sleep(45)

        # Determine the winners
        if len(giveaway_participants) == 2:
            winner1_id = giveaway_participants[0]
            winner2_id = giveaway_participants[1]

            # Fetch winner data
            winner1 = await client.get_users(winner1_id)
            winner2 = await client.get_users(winner2_id)

            # Prepare media for the first winner
            media = InputMediaPhoto(giveaway_character1.get("img_url"), caption=f"🏆 **Prize 1:** {giveaway_character1.get('name', 'Unknown')}\n**ID:** {giveaway_character1.get('id')}\n**Rarity:** {giveaway_character1.get('rarity')}")

            # Prepare caption for winners
            caption = (
                f"🎉 **Final Two Standing!**\n"
                f"🥇 **First Place:** [{winner1.first_name}](tg://user?id={winner1_id})\n"
                f"🥈 **Second Place:** [{winner2.first_name}](tg://user?id={winner2_id})"
            )

            # Send media and caption
            await client.send_message(chat_id=CHAT_ID, text=caption)

            # Assign prizes
            await user_collection.update_one(
                {"id": winner1_id},
                {"$push": {"characters": giveaway_character1}},
                upsert=True  # Create a new entry if the user does not exist
            )
            await user_collection.update_one(
                {"id": winner2_id},
                {"$push": {"characters": giveaway_character2}},
                upsert=True  # Create a new entry if the user does not exist
            )

            # Send DMs to winners
            await client.send_photo(
                chat_id=winner1_id,
                photo=giveaway_character1.get("img_url"),
                caption=(
                    f"🎉 **Congratulations! You won first place!**\n"
                    f"🏆 **Prize:** {giveaway_character1.get('name', 'Unknown')}\n"
                    f"**ID:** {giveaway_character1.get('id')}\n"
                    f"**Rarity:** {giveaway_character1.get('rarity')}"
                )
            )
            await client.send_photo(
                chat_id=winner2_id,
                photo=giveaway_character2.get("img_url"),
                caption=(
                    f"🎉 **Congratulations! You won second place!**\n"
                    f"🏆 **Prize:** {giveaway_character2.get('name', 'Unknown')}\n"
                    f"**ID:** {giveaway_character2.get('id')}\n"
                    f"**Rarity:** {giveaway_character2.get('rarity')}"
                )
            )

        # Reset giveaway data
        giveaway_character1 = None
        giveaway_character2 = None
        giveaway_participants = []
        giveaway_elimination_active = False
    except Exception as e:
        logger.error(f"Error in elimination_process: {e}")
