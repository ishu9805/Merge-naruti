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

# Giveaway data
class EliminationGiveaway:
    def __init__(self):
        self.character1 = None  # Prize for the first winner
        self.character2 = None  # Prize for the second winner
        self.participants = []  # List of participant user IDs
        self.elimination_task = None  # Background task for elimination
        self.elimination_active = False  # Flag to indicate if elimination is active

giveaway = EliminationGiveaway()

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

    giveaway.character1 = character1
    giveaway.character2 = character2
    giveaway.participants = []
    giveaway.elimination_active = False  # Reset elimination flag

    # Prepare media group
    media = [
        InputMediaPhoto(character1.get("img_url"), caption=f"🏆 **Prize 1:** {character1.get('name', 'Unknown')}\n**ID:** {giveaway.character1.get('id')}\n**Rarity:**{giveaway.character1.get('rarity')}"),
        InputMediaPhoto(character2.get("img_url"), caption=f"🏆 **Prize 2:** {character2.get('name', 'Unknown')}\n**ID:** {giveaway.character1.get('id')}\n**Rarity:**{giveaway.character1.get('rarity')}")
    ]

    # Prepare caption
    caption = (
        f"🎉 **Elimination Giveaway Started!**\n"
        f"💬 **Use /join to participate!**\n"
        f"👥 **Participants:** {len(giveaway.participants)}"
    )

    # Send media group and caption
    await send_media_group_with_caption(client, CHAT_ID, media, caption)
    await message.reply("✅ **Elimination giveaway started successfully!**")

# Join the elimination giveaway
@app.on_message(filters.command("join"))
@command_lock
async def join_giveaway(client: Client, message: Message):
    if not giveaway.character1 or not giveaway.character2:
        await message.reply("❌ **No active elimination giveaway.**")
        return

    if giveaway.elimination_active:
        await message.reply("❌ **The elimination process has started. You can no longer join.**")
        return

    user_id = message.from_user.id
    if user_id in giveaway.participants:
        await message.reply("ℹ️ **You are already participating in the giveaway.**")
        return

    giveaway.participants.append(user_id)
    await message.reply(f"✅ **You have successfully joined the elimination giveaway!**\n👥 **Total Participants:** {len(giveaway.participants)}")
    await client.send_message(
        chat_id=-1002338924488,
        text=(
            f"[{message.from_user.first_name}](tg://user?id={user_id}) participated\n"
            f"👥 **Total Participants:** {len(giveaway.participants)}"
        )
    )
# Start the elimination process
@app.on_message(filters.command("startelimination"))
async def start_elimination(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID:
        #await message.reply("🚫 **You are not authorized to start the elimination process.**")
        return

    if not giveaway.character1 or not giveaway.character2:
        #await message.reply("❌ **No active elimination giveaway to start.**")
        return

    if len(giveaway.participants) < 2:
        await message.reply("❌ **Not enough participants to start elimination.**")
        return

    # Set elimination as active
    giveaway.elimination_active = True

    # Start the elimination task
    giveaway.elimination_task = asyncio.create_task(elimination_process(client))

    await message.reply("✅ **Elimination process started! No new participants can join.**")

# Elimination process
async def elimination_process(client: Client):
    while len(giveaway.participants) > 1:
        if len(giveaway.participants) > 40:
            eliminate_count = 3
        elif len(giveaway.participants) > 20:
            eliminate_count = 2
        elif len(giveaway.participants) > 5:
            eliminate_count = 1
        else:
            eliminate_count = 1  # Last 2 users: eliminate 1 to determine the winner

        # Eliminate users
        eliminated = random.sample(giveaway.participants, eliminate_count)
        giveaway.participants = [user for user in giveaway.participants if user not in eliminated]

        # Announce eliminated users
        eliminated_names = []
        for user_id in eliminated:
            user = await client.get_users(user_id)
            eliminated_names.append(f"[{user.first_name}](tg://user?id={user_id})")

        await client.send_message(
            chat_id=-1002338924488,
            text=(
                f"🚫 **Eliminated Users:** {', '.join(eliminated_names)}\n"
                f"👥 **Remaining Participants:** {len(giveaway.participants)}"
            )
        )

        # Wait for 1 minute before the next elimination
        await asyncio.sleep(45)

    # Determine the winners
    if len(giveaway.participants) == 2:
        winner1_id = giveaway.participants[0]
        winner2_id = giveaway.participants[1]

        # Fetch winner data
        winner1 = await client.get_users(winner1_id)
        winner2 = await client.get_users(winner2_id)

        # Prepare media group for winners
        media = [
            InputMediaPhoto(giveaway.character1.get("img_url"), caption=f"🏆 **Prize 1:** {giveaway.character1.get('name', 'Unknown')}\n**ID:** {giveaway.character1.get('id')}\n**Rarity:**{giveaway.character1.get('rarity')}"),
            InputMediaPhoto(giveaway.character2.get("img_url"), caption=f"🏆 **Prize 2:** {giveaway.character2.get('name', 'Unknown')}\n**ID:** {giveaway.character2.get('id')}\n**Rarity:**{giveaway.character2.get('rarity')}")
        ]

        # Prepare caption for winners
        caption = (
            f"🎉 **Final Two Standing!**\n"
            f"🥇 **First Place:** [{winner1.first_name}](tg://user?id={winner1_id})\n"
            f"🥈 **Second Place:** [{winner2.first_name}](tg://user?id={winner2_id})"
        )

        # Send media group and caption
        await send_media_group_with_caption(client, CHAT_ID, media, caption)

        # Assign prizes
        await user_collection.update_one(
            {"id": winner1_id},
            {"$push": {"characters": giveaway.character1}}
        )
        await user_collection.update_one(
            {"id": winner2_id},
            {"$push": {"characters": giveaway.character2}}
        )

        # Send DMs to winners
        await send_media_group_with_caption(
            client,
            winner1_id,
            media,
            f"🎉 **Congratulations! You won first place!**\n\n🏆 **Prize:** {giveaway.character1.get('name', 'Unknown')\n**ID:** {giveaway.character1.get('id')}\n**Rarity:**{giveaway.character1.get('rarity')}"
        )
        await send_media_group_with_caption(
            client,
            winner2_id,
            media,
            f"🎉 **Congratulations! You won second place!**\n🏆 **Prize:** {giveaway.character2.get('name', 'Unknown')\n**ID:** {giveaway.character2.get('id')}\n**Rarity:**{giveaway.character2.get('rarity')}"
        )

    # Reset giveaway data
    giveaway.character1 = None
    giveaway.character2 = None
    giveaway.participants = []
    giveaway.elimination_task = None
    giveaway.elimination_active = False
