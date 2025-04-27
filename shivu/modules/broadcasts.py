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



# Configurable settings
MESSAGE_DELAY = 1  # Delay between messages to prevent flooding
MAX_RETRIES = 3    # Maximum retry attempts for failed sends
PROGRESS_UPDATE_INTERVAL = 25  # Update progress every X sends

# Store broadcast data
broadcast_data = {
    "message": None,    # The message to broadcast
    "buttons": [],      # List of buttons to include
    "is_active": False  # Whether a broadcast is in progress
}

# Set up logging
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
        self.start_time = None
    
    def get_progress(self):
        if self.total == 0:
            return "0%"
        return f"{int((self.success + self.failed) / self.total * 100)}%"
    
    def get_report(self):
        duration = "N/A"
        if self.start_time:
            duration = str(int((asyncio.get_event_loop().time() - self.start_time) / 60)) + "m"
        
        return (
            f"📊 Broadcast Report\n"
            f"✅ Success: {self.success}\n"
            f"❌ Failed: {self.failed}\n"
            f"⏱ Duration: {duration}\n"
            f"📈 Completion: {self.get_progress()}"
        )

@app.on_message(filters.command("setbroadcast") & dev_filter)
async def set_broadcast_message(client, message):
    if broadcast_data["is_active"]:
        await message.reply("⚠️ A broadcast is already in progress. Please wait.")
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Please reply to a message to set as broadcast")
        return
    
    broadcast_data["message"] = message.reply_to_message
    broadcast_data["buttons"] = []
    
    await message.reply(
        "✅ Broadcast message set!\n"
        "Use /preview to see it\n"
        "Use /addbutton to add buttons\n"
        "Use /clearbuttons to remove all buttons"
    )

@app.on_message(filters.command("preview") & dev_filter)
async def preview_broadcast(client, message):
    if not broadcast_data.get("message"):
        await message.reply("❌ No broadcast message set. Use /setbroadcast first")
        return
    
    try:
        # Create keyboard markup from stored buttons
        keyboard = []
        current_row = []
        
        for btn in broadcast_data["buttons"]:
            current_row.append(InlineKeyboardButton(btn["text"], url=btn["url"]))
            if btn["new_row"]:
                keyboard.append(current_row)
                current_row = []
        
        if current_row:
            keyboard.append(current_row)
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        # Preview the message
        if broadcast_data["message"].text:
            await client.send_message(
                message.chat.id,
                broadcast_data["message"].text,
                reply_markup=reply_markup
            )
        else:
            caption = broadcast_data["message"].caption or ""
            if broadcast_data["message"].photo:
                await client.send_photo(
                    message.chat.id,
                    broadcast_data["message"].photo.file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            elif broadcast_data["message"].document:
                await client.send_document(
                    message.chat.id,
                    broadcast_data["message"].document.file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            elif broadcast_data["message"].video:
                await client.send_video(
                    message.chat.id,
                    broadcast_data["message"].video.file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            else:
                await message.reply("⚠️ Media type not supported for preview")
                
    except Exception as e:
        await message.reply(f"❌ Error previewing message: {str(e)}")

@app.on_message(filters.command("addbutton") & dev_filter)
async def add_buttons(client, message):
    if not message.text or len(message.text.split()) < 2:
        await message.reply(
            "❌ Invalid format. Use:\n"
            "<code>/addbutton Text - URL | Text - URL</code>\n\n"
            "Example:\n"
            "<code>/addbutton Google - https://google.com | GitHub - https://github.com</code>\n\n"
            "Use <code>|</code> for buttons on same line"
        )
        return
    
    try:
        # Parse button definitions
        input_text = " ".join(message.text.split()[1:])
        button_defs = [b.strip() for b in input_text.split('|') if b.strip()]
        
        added = 0
        for i, def_ in enumerate(button_defs):
            parts = def_.split('-', 1)
            if len(parts) != 2:
                continue
            
            text = parts[0].strip()
            url = parts[1].strip()
            
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Add button (new_row=True for first button in each group)
            broadcast_data["buttons"].append({
                "text": text,
                "url": url,
                "new_row": i == 0  # First button in group starts new row
            })
            added += 1
        
        await message.reply(f"✅ Added {added} button(s). Use /preview to see them.")
    except Exception as e:
        await message.reply(f"❌ Error adding buttons: {str(e)}")

@app.on_message(filters.command("clearbuttons") & dev_filter)
async def clear_buttons(client, message):
    broadcast_data["buttons"] = []
    await message.reply("✅ All buttons cleared")

async def send_broadcast_message(client, target_id):
    # Prepare keyboard markup
    keyboard = []
    current_row = []
    
    for btn in broadcast_data["buttons"]:
        current_row.append(InlineKeyboardButton(btn["text"], url=btn["url"]))
        if btn["new_row"]:
            keyboard.append(current_row)
            current_row = []
    
    if current_row:
        keyboard.append(current_row)
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    # Send the message with retries
    for attempt in range(MAX_RETRIES):
        try:
            if broadcast_data["message"].text:
                await client.send_message(
                    target_id,
                    broadcast_data["message"].text,
                    reply_markup=reply_markup
                )
            else:
                caption = broadcast_data["message"].caption or ""
                if broadcast_data["message"].photo:
                    await client.send_photo(
                        target_id,
                        broadcast_data["message"].photo.file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                elif broadcast_data["message"].document:
                    await client.send_document(
                        target_id,
                        broadcast_data["message"].document.file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                elif broadcast_data["message"].video:
                    await client.send_video(
                        target_id,
                        broadcast_data["message"].video.file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                else:
                    await client.forward_messages(
                        target_id,
                        broadcast_data["message"].chat.id,
                        broadcast_data["message"].id
                    )
            return True
            
        except FloodWait as e:
            wait_time = e.value
            logger.warning(f"FloodWait for {target_id}, waiting {wait_time}s (attempt {attempt + 1})")
            await asyncio.sleep(wait_time)
            continue
            
        except (PeerIdInvalid, ChatWriteForbidden, UserIsBlocked, ChannelPrivate):
            logger.info(f"Can't send to {target_id} (invalid/blocked/private)")
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

async def run_broadcast(client, message, target_ids, target_name):
    if not broadcast_data.get("message"):
        await message.reply("❌ No broadcast message set. Use /setbroadcast first")
        return
    
    if broadcast_data["is_active"]:
        await message.reply("⚠️ A broadcast is already in progress")
        return
    
    total = len(target_ids)
    if total == 0:
        await message.reply(f"❌ No {target_name} found to broadcast to")
        return
    
    broadcast_data["is_active"] = True
    stats = BroadcastStats(total)
    stats.start_time = asyncio.get_event_loop().time()
    
    progress_msg = await message.reply(
        f"📤 Starting broadcast to {total} {target_name}...\n"
        f"{stats.get_report()}"
    )
    
    try:
        for i, target_id in enumerate(target_ids):
            if not broadcast_data["is_active"]:  # Check if cancelled
                break
                
            success = await send_broadcast_message(client, target_id)
            if success:
                stats.success += 1
            else:
                stats.failed += 1
            
            # Update progress periodically
            if i % PROGRESS_UPDATE_INTERVAL == 0 or i == total - 1:
                try:
                    await progress_msg.edit_text(
                        f"📤 Broadcasting to {target_name}...\n"
                        f"{stats.get_report()}"
                    )
                except Exception as e:
                    logger.error(f"Error updating progress: {e}")
            
            await asyncio.sleep(MESSAGE_DELAY)
        
        final_message = (
            f"✅ Broadcast completed!\n"
            f"{stats.get_report()}"
        )
        
    except Exception as e:
        final_message = (
            f"⚠️ Broadcast interrupted!\n"
            f"Error: {str(e)}\n"
            f"{stats.get_report()}"
        )
        logger.error(f"Broadcast error: {e}")
    
    finally:
        broadcast_data["is_active"] = False
        await progress_msg.edit_text(final_message)

@app.on_message(filters.command("gbroadcast") & dev_filter)
async def broadcast_to_groups(client, message):
    # Get all group IDs from database
    group_ids = []
    async for group in top_global_groups_collection.find({}):
        if group.get('group_id'):
            group_ids.append(group['group_id'])
    
    await run_broadcast(client, message, group_ids, "groups")

@app.on_message(filters.command("ubroadcast") & dev_filter)
async def broadcast_to_users(client, message):
    # Get all user IDs from database
    user_ids = []
    async for user in user_collection.find({}):
        if user.get('id'):
            user_ids.append(user['id'])
    
    await run_broadcast(client, message, user_ids, "users")

@app.on_message(filters.command("cancelbroadcast") & dev_filter)
async def cancel_broadcast(client, message):
    if broadcast_data["is_active"]:
        broadcast_data["is_active"] = False
        await message.reply("⏹ Broadcast cancelled")
    else:
        await message.reply("ℹ️ No active broadcast to cancel")          
