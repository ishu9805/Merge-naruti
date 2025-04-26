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

import asyncio
import logging
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import (
    PeerIdInvalid, 
    FloodWait, 
    ChatWriteForbidden, 
    UserIsBlocked,
    ChannelPrivate,
    ChatAdminRequired
)
from . import dev_filter
from shivu import (
    collection,
    top_global_groups_collection,
    group_user_totals_collection,
    user_collection,
    user_totals_collection,
    shivuu as app
)

# Configurable settings
MESSAGE_DELAY = 2  # Delay after every 7 messages
PROGRESS_UPDATE_INTERVAL = 25  # Update progress every 25 users/groups
MAX_RETRIES = 3  # Maximum retry attempts for failed sends

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BroadcastStats:
    def __init__(self):
        self.user_success = 0
        self.group_success = 0
        self.fail_count = 0
        self.message_count = 0
        self.skipped_groups = 0

    def get_report(self):
        return (
            f"📊 Broadcast Report:\n"
            f"✅ Users reached: {self.user_success}\n"
            f"✅ Groups reached: {self.group_success}\n"
            f"❌ Failed attempts: {self.fail_count}\n"
            f"⏩ Skipped groups: {self.skipped_groups}"
        )

def create_forward_markup(original_chat_id, message_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🔗 Forward Message",
            url=f"https://t.me/c/{str(original_chat_id).replace('-100', '')}/{message_id}"
        )
    ]])

async def send_message_with_retry(client, target_id, replied_message, stats):
    for attempt in range(MAX_RETRIES):
        try:
            if replied_message.text:
                # For text messages, send with forward button
                sent_msg = await client.send_message(
                    target_id,
                    replied_message.text,
                    reply_markup=create_forward_markup(
                        replied_message.chat.id,
                        replied_message.id
                    )
                )
            else:
                media_caption = replied_message.caption or ""
                markup = create_forward_markup(
                    replied_message.chat.id,
                    replied_message.id
                )
                
                if replied_message.document:
                    sent_msg = await client.send_document(
                        target_id,
                        replied_message.document.file_id,
                        caption=media_caption,
                        reply_markup=markup
                    )
                elif replied_message.photo:
                    sent_msg = await client.send_photo(
                        target_id,
                        replied_message.photo.file_id,
                        caption=media_caption,
                        reply_markup=markup
                    )
                elif replied_message.video:
                    sent_msg = await client.send_video(
                        target_id,
                        replied_message.video.file_id,
                        caption=media_caption,
                        reply_markup=markup
                    )
                else:
                    # For other media types, just forward
                    sent_msg = await client.forward_messages(
                        target_id,
                        replied_message.chat.id,
                        replied_message.id
                    )
            
            stats.message_count += 1
            return True
            
        except FloodWait as e:
            wait_time = e.value
            logger.warning(f"FloodWait for {target_id}, waiting {wait_time} seconds (attempt {attempt + 1})")
            await asyncio.sleep(wait_time)
            continue
            
        except (PeerIdInvalid, ChatWriteForbidden, UserIsBlocked, ChannelPrivate):
            logger.info(f"Message not sent to {target_id} (invalid/blocked/private)")
            return False
            
        except ChatAdminRequired:
            logger.info(f"Admin required in {target_id}, skipping")
            return False
            
        except Exception as e:
            logger.error(f"Error sending to {target_id} (attempt {attempt + 1}): {str(e)}")
            if attempt == MAX_RETRIES - 1:
                return False
            await asyncio.sleep(1)
    
    return False

async def update_progress(progress_message, stats, additional_text=""):
    try:
        text = (
            f"📢 Broadcast in progress...\n"
            f"{additional_text}\n"
            f"✅ Users sent: {stats.user_success}\n"
            f"✅ Groups sent: {stats.group_success}\n"
            f"❌ Failed attempts: {stats.fail_count}"
        )
        await progress_message.edit_text(text)
    except Exception as e:
        logger.error(f"Error updating progress: {e}")

async def broadcast_to_users(client, stats, progress_message, replied_message):
    total_users = await user_collection.count_documents({})
    processed = 0
    
    async for user in user_collection.find({}):
        user_id = user.get('id')
        if not user_id:
            continue
            
        success = await send_message_with_retry(client, user_id, replied_message, stats)
        if success:
            stats.user_success += 1
        else:
            stats.fail_count += 1
            
        processed += 1
        if processed % PROGRESS_UPDATE_INTERVAL == 0:
            await update_progress(
                progress_message,
                stats,
                f"📤 Broadcasting to users... ({processed}/{total_users})"
            )
        
        # Add delay after every 7 messages
        if processed % 7 == 0:
            await asyncio.sleep(MESSAGE_DELAY)

async def broadcast_to_groups(client, stats, progress_message, replied_message):
    total_groups = await top_global_groups_collection.count_documents({})
    processed = 0
    unique_group_ids = set()
    
    async for group in top_global_groups_collection.find({}):
        group_id = group.get('group_id')
        if not group_id or group_id in unique_group_ids:
            continue
            
        unique_group_ids.add(group_id)
        success = await send_message_with_retry(client, group_id, replied_message, stats)
        if success:
            stats.group_success += 1
        else:
            stats.fail_count += 1
            
        processed += 1
        if processed % PROGRESS_UPDATE_INTERVAL == 0:
            await update_progress(
                progress_message,
                stats,
                f"📤 Broadcasting to groups... ({processed}/{total_groups})"
            )
        
        # Add delay after every 7 messages
        if processed % 7 == 0:
            await asyncio.sleep(MESSAGE_DELAY)

@app.on_message(filters.command("broadcast") & dev_filter)
async def broadcast_command(client, message):
    replied_message = message.reply_to_message
    if not replied_message:
        await message.reply_text("❌ Please reply to a message to broadcast it.")
        return

    # Send initial progress message
    progress_message = await message.reply_text("📢 Starting broadcast... Gathering recipients...")

    stats = BroadcastStats()

    try:
        # Broadcast to users
        await update_progress(progress_message, stats, "🔄 Starting user broadcast...")
        await broadcast_to_users(client, stats, progress_message, replied_message)

        # Broadcast to groups
        await update_progress(progress_message, stats, "🔄 Starting group broadcast...")
        await broadcast_to_groups(client, stats, progress_message, replied_message)

        # Final report
        await progress_message.edit_text(
            stats.get_report() + "\n\n🌟 Broadcast completed!"
        )
    except Exception as e:
        logger.error(f"Broadcast failed: {e}")
        await progress_message.edit_text(
            f"⚠️ Broadcast interrupted due to an error:\n{str(e)}\n\n"
            + stats.get_report()
            )
