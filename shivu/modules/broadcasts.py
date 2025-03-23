import asyncio
import logging
from pyrogram import filters
from pyrogram.errors import PeerIdInvalid, FloodWait, ChatWriteForbidden, UserIsBlocked
from . import dev_filter
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
# Configurable settings
MESSAGE_DELAY = 2  # Delay after every 7 messages
PROGRESS_UPDATE_INTERVAL = 25  # Update progress every 25 users/groups

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_message(filters.command("broadcast") & dev_filter)
async def broadcast(_, message):
    replied_message = message.reply_to_message
    if not replied_message:
        await message.reply_text("❌ Please reply to a message to broadcast it.")
        return

    # Send initial progress message
    progress_message = await message.reply_text("📢 Starting the broadcast. Sending the message to all users and groups...")

    success_count = 0
    fail_count = 0
    message_count = 0
    user_success = 0  # Define user_success here
    group_success = 0  # Define group_success here

    # Function to send the message
    async def send_message(target_id):
        nonlocal success_count, fail_count, message_count
        try:
            if replied_message.text:
                x = message.reply_to_message.id
                y = message.chat.id
                await app.forward_messages(target_id, y, x)
            else:
                media_caption = replied_message.caption if replied_message.caption else ""
                if replied_message.document:
                    await app.send_document(target_id, replied_message.document.file_id, caption=media_caption)
                elif replied_message.photo:
                    await app.send_photo(target_id, replied_message.photo.file_id, caption=media_caption)
                elif replied_message.video:
                    await app.send_video(target_id, replied_message.video.file_id, caption=media_caption)

            success_count += 1
            message_count += 1
        except (PeerIdInvalid, ChatWriteForbidden, UserIsBlocked):
            fail_count += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await send_message(target_id)  # Retry after waiting
        except Exception as e:
            logger.error(f"Error sending to {target_id}: {e}")
            fail_count += 1

        # Introduce a delay after every 7 messages
        if message_count % 7 == 0:
            await asyncio.sleep(MESSAGE_DELAY)

    # Function to update progress
    async def update_progress():
        nonlocal user_success, group_success  # Access outer scope variables
        await progress_message.edit_text(
            f"📢 Broadcast in progress...\n"
            f"✅ Users sent: {user_success}\n"
            f"✅ Groups sent: {group_success}\n"
            f"❌ Failed attempts: {fail_count}"
        )

    # Send to users
    user_cursor = user_collection.find({})
    async for user in user_cursor:
        user_id = user.get('id')
        if user_id:
            await send_message(user_id)
            user_success += 1

            # Update progress every PROGRESS_UPDATE_INTERVAL users
            if user_success % PROGRESS_UPDATE_INTERVAL == 0:
                await update_progress()

    # Send to groups
    group_cursor = top_global_groups_collection.find({})
    unique_group_ids = set()
    async for group in group_cursor:
        group_id = group.get('group_id')
        if group_id and group_id not in unique_group_ids:
            unique_group_ids.add(group_id)
            await send_message(group_id)
            group_success += 1

            # Update progress every PROGRESS_UPDATE_INTERVAL groups
            if group_success % PROGRESS_UPDATE_INTERVAL == 0:
                await update_progress()

    # Final report
    await progress_message.edit_text(
        f"✅ Broadcast completed!\n"
        f"✅ Users sent: {user_success}\n"
        f"✅ Groups sent: {group_success}\n"
        f"❌ Failed attempts: {fail_count}"
    )
