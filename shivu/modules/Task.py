import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import random
import time
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from . import sudo_filter as sudo, dev_filter
from shivu import (
    collectionps as collection,
    user_collectionps as user_collection,
    user_totals_collectionps as user_totals_collection,
    shivuups as app,
    OWNER_ID
)
from pyrogram.errors import FloodWait

# Initialize global variables
claim_locks = defaultdict(asyncio.Lock)
pending_claims = {}
message_counts = defaultdict(int)
lock = asyncio.Lock()
BATCH_SIZE = 100
SUPPORT_CHAT_ID = -1002606804832
MAX_OWNERS = 4
CLAIM_TIMEOUT = 300  # 5 minutes for pending claims

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("shivu_claims.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Milestone configuration
TASK_MILESTONES = {
    300: {
        'type': 'special',
        'rarity': '💮 Special Edition',
        'message': "🎉 300 messages! Claim your 💮 Special Edition with /sclaim",
        'grab_required': 2
    },
    1000: {
        'type': 'limited', 
        'rarity': '🔮 Limited Edition',
        'message': "🌟 1000 messages! Choose 🔮 Limited Edition with /lclaim",
        'grab_required': 4
    }
}

# Helper Functions
async def acquire_user_lock(user_id):
    try:
        await asyncio.wait_for(claim_locks[user_id].acquire(), timeout=30)
        return True
    except asyncio.TimeoutError:
        return False

async def release_user_lock(user_id):
    if claim_locks[user_id].locked():
        claim_locks[user_id].release()

async def get_user_count(user_id):
    async with lock:
        in_memory = message_counts.get(user_id, 0)
    user_data = await user_totals_collection.find_one({'user_id': user_id})
    db_count = user_data.get('count', 0) if user_data else 0
    return db_count + in_memory

async def get_grab_count(user_id):
    user_data = await user_collection.find_one({'id': user_id})
    return user_data.get('grab', 0) if user_data else 0

async def get_character_owners(char_id):
    count = await user_collection.count_documents({
        'characters.id': char_id
    })
    return count

async def cleanup_pending_claims():
    while True:
        await asyncio.sleep(60)
        current_time = time.time()
        expired = [uid for uid, claim in pending_claims.items() 
                  if current_time - claim['timestamp'] > CLAIM_TIMEOUT]
        for uid in expired:
            try:
                await app.send_message(uid, "⌛ Your pending claim has expired")
                del pending_claims[uid]
            except Exception:
                continue

# Scheduled Tasks


# Commands
@cmd
@app.on_message(filters.command("task"))
async def task_command(client, message):
    user_id = message.from_user.id
    total = await get_user_count(user_id)
    grab_count = await get_grab_count(user_id)
    
    response = [
        "📊 **Your Task Progress**",
        f"💬 Messages: {total} [GROUP](https://t.me/+CE94ttBftcNlNDk1)",
        f"⚡ Legendary Grabs: {grab_count}",
        "",
        "🎯 **Milestone Rewards**:"
    ]
    
    all_completed = True
    for milestone, data in sorted(TASK_MILESTONES.items()):
        status = "✅" if total >= milestone else "◻️"
        remaining = max(0, milestone - total)
        rarity = data.get('rarity', 'Reward')
        
        if 'grab_required' in data and data['grab_required'] > 0:
            grab_status = "✅" if grab_count >= data['grab_required'] else "❌"
            response.append(
                f"{status} {rarity} at {milestone} messages ({remaining} left) "
                f"& {grab_status} {data['grab_required']} grabs needed"
            )
        else:
            response.append(
                f"{status} {rarity} at {milestone} messages ({remaining} left)"
            )
        
        user_data = await user_totals_collection.find_one({'user_id': user_id})
        claim_field = f"claimed_{milestone}"
        if not user_data or not user_data.get(claim_field, False):
            all_completed = False
    
    if all_completed:
        response.append("\n🎉 You've completed ALL milestones!")
        response.append("You can reset your tasks with /reset_task to start over")
    
    await message.reply_text("\n".join(response))

@cmd
@app.on_message(filters.command("resetalltasks") & sudo)
async def reset_all_tasks_command(client, message):
    """Reset task progress for all users (Admin only)"""
    try:
        if len(message.command) == 1 or message.command[1].lower() != "confirm":
            return await message.reply(
                "⚠️ **Danger Zone** ⚠️\n"
                "This will reset ALL users' task progress!\n\n"
                "To confirm, use:\n"
                "/resetalltasks confirm\n\n"
                "Add 'dryrun' to test first:\n"
                "/resetalltasks confirm dryrun"
            )

        dry_run = "dryrun" in message.command
        processing_msg = await message.reply(
            f"🔄 {'Dry run' if dry_run else 'Processing'} global task reset..."
        )

        milestones = list(TASK_MILESTONES.keys())
        update_query = {f"claimed_{milestone}": False for milestone in milestones}
        
        total_users = await user_totals_collection.count_documents({})
        
        if dry_run:
            result = {"modified_count": total_users}
        else:
            result = await user_totals_collection.update_many(
                {},
                {"$set": update_query}
            )
            
            async with lock:
                message_counts.clear()

        report = (
            f"📊 **Global Task Reset Complete** {'(Dry Run)' if dry_run else ''}\n"
            f"• Total users: {total_users}\n"
            f"• Reset users: {result.modified_count}\n"
            f"• Milestones reset: {', '.join(map(str, milestones))}\n"
            f"• In-memory counts cleared: {not dry_run}\n\n"
        )
        
        if dry_run:
            report += "ℹ️ This was a dry run - no changes were made"
        else:
            report += f"✅ Successfully reset all tasks at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        await processing_msg.edit_text(report)
        
        await app.send_message(
            SUPPORT_CHAT_ID,
            f"♻️ Global task reset executed by {message.from_user.mention}\n" + report
        )

    except Exception as e:
        logger.error(f"Global reset error: {str(e)}", exc_info=True)
        error_msg = f"❌ Global reset failed: {str(e)}"
        await message.reply(error_msg)
        await app.send_message(OWNER_ID, error_msg)

# 
