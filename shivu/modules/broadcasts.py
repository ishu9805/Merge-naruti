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
    UPDATE_CHATps as UPDATE_CHAT_PS,
    dbps as db,
    pmusersps as pmusers,
    ban_collectionps as ban_collection,
    user_countps as user_count, 
    chat_dataps as chat_data,
)

from pyrogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    MessageEntity
)
from pyrogram.enums import MessageEntityType
from pyrogram.errors import (
    ChannelPrivate,
    ChatAdminRequired
)

# ===== CONFIGURATION =====
MESSAGE_DELAY = 1  # Seconds between messages
MAX_RETRIES = 3     # Max send attempts
PROGRESS_UPDATE_INTERVAL = 25  # Update progress every X messages

# ===== DATA STORAGE =====
broadcast_data = {
    "original_msg": None,  # The complete original message
    "is_active": False    # Broadcast status
}

# ===== LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BroadcastStats:
    def __init__(self, total):
        self.success = 0
        self.failed = 0
        self.total = total
        self.start_time = asyncio.get_event_loop().time()
    
    @property
    def progress(self):
        return f"{int((self.success + self.failed)/self.total*100)}%" if self.total else "0%"
    
    @property
    def duration(self):
        return f"{int((asyncio.get_event_loop().time()-self.start_time)/60)}m"
    
    def report(self):
        return (
            f"📊 Broadcast Report\n"
            f"✅ Success: {self.success}\n"
            f"❌ Failed: {self.failed}\n"
            f"⏱ Duration: {self.duration}\n"
            f"📈 Progress: {self.progress}"
        )

# ===== COMMAND HANDLERS =====

@app.on_message(filters.command("setbroadcast") & dev_filter)
async def set_broadcast(client, message):
    """Set the message to be broadcasted"""
    if broadcast_data["is_active"]:
        await message.reply("⚠️ Broadcast in progress. Please wait.")
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Please reply to a message")
        return
    
    broadcast_data["original_msg"] = message.reply_to_message
    await message.reply(
        "✅ Broadcast message set!\n"
        "Use /preview to check\n"
        "Use /addbutton to add buttons\n"
        "Use /clearbuttons to reset buttons"
    )

@app.on_message(filters.command("preview") & dev_filter)
async def preview_broadcast(client, message):
    """Preview the current broadcast message"""
    if not broadcast_data["original_msg"]:
        await message.reply("❌ No broadcast message set")
        return
    
    try:
        original = broadcast_data["original_msg"]
        
        # For text messages
        if original.text:
            await original.copy(
                chat_id=message.chat.id,
                reply_to_message_id=message.id
            )
        # For media messages
        else:
            await original.copy(
                chat_id=message.chat.id,
                caption=original.caption,
                caption_entities=original.caption_entities,
                reply_to_message_id=message.id
            )
    except Exception as e:
        await message.reply(f"❌ Preview failed: {str(e)}")

@app.on_message(filters.command("addbutton") & dev_filter)
async def add_button(client, message):
    """Add buttons to the broadcast message"""
    if not broadcast_data["original_msg"]:
        await message.reply("❌ No broadcast message set")
        return
    
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply(
                "❌ Format: /addbutton Text - URL | Text - URL\n"
                "Example: /addbutton Google - google.com | GitHub - github.com"
            )
            return
        
        buttons = []
        for btn_group in args[1].split('|'):
            btn_parts = btn_group.strip().split('-', 1)
            if len(btn_parts) == 2:
                text = btn_parts[0].strip()
                url = btn_parts[1].strip()
                if not url.startswith(('http://', 'https://')):
                    url = f'https://{url}'
                buttons.append({
                    "text": text,
                    "url": url,
                    "new_row": True
                })
        
        if not buttons:
            await message.reply("❌ No valid buttons found")
            return
        
        # Store buttons in the original message
        if not hasattr(broadcast_data["original_msg"], 'buttons'):
            broadcast_data["original_msg"].buttons = []
        
        broadcast_data["original_msg"].buttons.extend(buttons)
        await message.reply(f"✅ Added {len(buttons)} button(s)")
        
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command("clearbuttons") & dev_filter)
async def clear_buttons(client, message):
    """Remove all buttons from broadcast message"""
    if hasattr(broadcast_data["original_msg"], 'buttons'):
        broadcast_data["original_msg"].buttons = []
    await message.reply("✅ All buttons cleared")

# ===== BROADCAST CORE =====

async def send_message_with_retry(client, target_id):
    """Send the broadcast message with retry logic"""
    original = broadcast_data["original_msg"]
    
    for attempt in range(MAX_RETRIES):
        try:
            # Prepare reply markup if buttons exist
            reply_markup = None
            if hasattr(original, 'buttons') and original.buttons:
                keyboard = []
                row = []
                for btn in original.buttons:
                    row.append(InlineKeyboardButton(btn["text"], url=btn["url"]))
                    if btn.get("new_row"):
                        keyboard.append(row)
                        row = []
                if row:
                    keyboard.append(row)
                reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Handle text messages
            if original.text:
                await client.send_message(
                    target_id,
                    original.text,
                    entities=original.entities,
                    reply_markup=reply_markup
                )
            # Handle media messages
            else:
                await original.copy(
                    chat_id=target_id,
                    caption=original.caption,
                    caption_entities=original.caption_entities,
                    reply_markup=reply_markup
                )
            return True
            
        except FloodWait as e:
            wait_time = e.value
            logger.warning(f"FloodWait for {target_id}, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
            continue
            
        except (PeerIdInvalid, ChatWriteForbidden, UserIsBlocked, ChannelPrivate):
            logger.info(f"Can't send to {target_id} (invalid/blocked)")
            return False
            
        except ChatAdminRequired:
            logger.info(f"Admin required in {target_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending to {target_id}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                return False
            await asyncio.sleep(1)
    
    return False

async def run_broadcast(client, message, target_ids, target_name):
    """Execute the broadcast to specified targets"""
    if not broadcast_data["original_msg"]:
        await message.reply("❌ No broadcast message set")
        return
    
    if broadcast_data["is_active"]:
        await message.reply("⚠️ Broadcast already running")
        return
    
    total = len(target_ids)
    if not total:
        await message.reply(f"❌ No {target_name} found")
        return
    
    broadcast_data["is_active"] = True
    stats = BroadcastStats(total)
    progress_msg = await message.reply(f"📤 Starting broadcast to {total} {target_name}...\n{stats.report()}")
    
    try:
        for i, target_id in enumerate(target_ids):
            if not broadcast_data["is_active"]:
                break
                
            if await send_message_with_retry(client, target_id):
                stats.success += 1
            else:
                stats.failed += 1
            
            # Update progress periodically
            if i % PROGRESS_UPDATE_INTERVAL == 0 or i == total - 1:
                try:
                    await progress_msg.edit_text(
                        f"📤 Broadcasting to {target_name}...\n{stats.report()}"
                    )
                except Exception as e:
                    logger.error(f"Progress update failed: {e}")
            
            await asyncio.sleep(MESSAGE_DELAY)
        
        final_msg = f"✅ Broadcast complete!\n{stats.report()}"
        
    except Exception as e:
        final_msg = f"⚠️ Broadcast failed!\nError: {str(e)}\n{stats.report()}"
        logger.error(f"Broadcast error: {e}")
    
    finally:
        broadcast_data["is_active"] = False
        await progress_msg.edit_text(final_msg)

# ===== BROADCAST COMMANDS =====

@app.on_message(filters.command("gbroadcast") & dev_filter)
async def broadcast_groups(client, message):
    """Broadcast to all groups"""
    group_ids = []
    async for group in top_global_groups_collection.find({}):
        if group.get('group_id'):
            group_ids.append(group['group_id'])
    
    await run_broadcast(client, message, group_ids, "groups")

@app.on_message(filters.command("ubroadcast") & dev_filter)
async def broadcast_users(client, message):
    """Broadcast to all users"""
    user_ids = []
    async for user in user_collection.find({}):
        if user.get('id'):
            user_ids.append(user['id'])
    
    await run_broadcast(client, message, user_ids, "users")

@app.on_message(filters.command("cancelbroadcast") & dev_filter)
async def cancel_broadcast(client, message):
    """Cancel ongoing broadcast"""
    if broadcast_data["is_active"]:
        broadcast_data["is_active"] = False
        await message.reply("⏹ Broadcast cancelled")
    else:
        await message.reply("ℹ️ No active broadcast")
