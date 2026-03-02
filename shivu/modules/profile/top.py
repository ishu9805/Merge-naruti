import asyncio
import os
import random
import html
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, Application, ContextTypes, CallbackQueryHandler


from cachetools import TTLCache
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
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
    dm_collection,
    userbot
)
# Logging setup
import json

from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient
from bson import json_util
import time

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)

# Configuration
TARGET_CHAT_ID = 6902029663 # Move to environment variables in production
ALLOWED_USER_IDS = 6902029663


# Cache for user and group data
USER_CACHE = TTLCache(maxsize=1000, ttl=3600)  # Cache with 1-hour TTL
GROUP_CACHE = TTLCache(maxsize=100, ttl=3600)  # Cache with 1-hour TTL

# Initialize the scheduler
scheduler = AsyncIOScheduler()



TASK_MILESTONES = {
    300: {
        'type': 'special',
        'rarity': '💮 Special Edition',
        'message': "🎉 300 messages! Claim your 💮 Special Edition with /sclaim",
        'grab_required': 4
    },
    1000: {
        'type': 'limited', 
        'rarity': '🔮 Limited Edition',
        'message': "🌟 1000 messages! Choose 🔮 Limited Edition with /lclaim",
        'grab_required': 7
    }
}


async def perform_backup():
    """Perform the actual backup operation"""
    json_filename = f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        LOGGER.info("Starting database backup...")
        
        # Fetch data from MongoDB collections
        collection_data = await collection.find().to_list(None)
        user_collection_data = await user_collection.find().to_list(None)

        # Combine data
        data = {
            "collection": collection_data,
            "user_collection": user_collection_data,
        }

        # Save to JSON file
        with open(json_filename, "w") as json_file:
            json.dump(data, json_file, indent=4, default=json_util.default)
        LOGGER.info("JSON file created successfully.")

        # Send the file
        await app.send_document(
            chat_id=TARGET_CHAT_ID,
            document=json_filename,
            caption=f"Database Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        LOGGER.info("Backup sent successfully.")
        
    except Exception as e:
        LOGGER.error(f"Backup failed: {e}", exc_info=True)
        raise
    finally:
        # Clean up the file
        if os.path.exists(json_filename):
            try:
                os.remove(json_filename)
            except Exception as e:
                LOGGER.warning(f"Could not remove temporary file: {e}")

async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for manual backup command"""
    user = update.effective_user
    if user.id != ALLOWED_USER_IDS:
        await update.message.reply_text("You are not authorized to perform backups.")
        LOGGER.warning(f"Unauthorized backup attempt by user {user.id}")
        return

    try:
        await update.message.reply_text("Starting manual backup process...")
        await perform_backup()
        await update.message.reply_text("✅ Backup completed and sent successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Backup failed: {str(e)}")
        LOGGER.error(f"Manual backup failed: {e}", exc_info=True)


    
    
    
def reset_dm_collection():
    """Reset the collection every week (call this periodically)"""
    last_reset = dm_collection.find_one({"_id": "last_reset"})
    if not last_reset or (datetime.now() - last_reset["date"]) >= timedelta(weeks=1):
        dm_collection.delete_many({})  # Clear all user entries
        dm_collection.insert_one({"_id": "last_reset", "date": datetime.now()})


    

# Function to create necessary indexes
async def create_indexes():
    await user_collection.create_index([("total_characters", -1)])
    await top_global_groups_collection.create_index([("count", -1)])
    await group_user_totals_collection.create_index([("group_id", 1), ("count", -1)])

# Fetch user data from cache or DB
async def get_user_data(user_id: int):
    if user_id in USER_CACHE:
        return USER_CACHE[user_id]
    user = await user_collection.find_one({"id": user_id})
    if user:
        USER_CACHE[user_id] = user
    return user

# Fetch group data from cache or DB
async def get_group_data(group_id: int):
    if group_id in GROUP_CACHE:
        return GROUP_CACHE[group_id]
    group = await group_user_totals_collection.find_one({"group_id": group_id})
    if group:
        GROUP_CACHE[group_id] = group
    return group

# Scheduled tasks
async def reset_daily_tops():
    """Reset daily_top for all users at midnight."""
    await user_collection.update_many({}, {"$set": {"daily_top": 0}})
    LOGGER.info("Daily tops reset.")

async def reset_weekly_tops():
    """Reset weekly_top for all users at midnight on Sunday."""
    await user_collection.update_many({}, {"$set": {"weekly_top": 0}})
    LOGGER.info("Weekly tops reset.")

async def reset_monthly_tops():
    """Reset monthly_top for all users at midnight on the last day of the month."""
    await user_collection.update_many({}, {"$set": {"monthly_top": 0}})
    LOGGER.info("Monthly tops reset.")


async def reset_all_tasks_daily():
    try:
        LOGGER.info("⏰ Running daily task reset...")
        start_time = time.time()
        
        # Reset all users' milestones and counts
        update_query = {
            **{f"claimed_{milestone}": False for milestone in TASK_MILESTONES.keys()},
            "count": 0,  # Reset message count
            "grab": 0    # Reset grab count
        }
        
        # Update all documents in the collection
        result = await user_totals_collection.update_many(
            {},
            {'$set': update_query}
        )
        
        # Also reset grab counts in user_collection
        grab_reset_result = await user_collection.update_many(
            {},
            {'$set': {'grab': 0}}
        )
        
        LOGGER.info(
            f"✅ Reset {result.modified_count} users' tasks and "
            f"{grab_reset_result.modified_count} users' grab counts "
            f"in {time.time()-start_time:.2f}s"
        )
        
        # Notify support chat
        await app.send_message(
            -1002606804832,
            f"🔄 Daily task reset completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• Reset {result.modified_count} users' tasks\n"
            f"• Reset {grab_reset_result.modified_count} users' grab counts\n"
            f"• Cleared in-memory message counters"
        )
        
    except Exception as e:
        LOGGER.error(f"Failed to reset tasks: {str(e)}", exc_info=True)
     
async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for manual backup command"""
    user = update.effective_user
    if user.id != ALLOWED_USER_IDS:
        await update.message.reply_text("You are not authorized to perform backups.")
        LOGGER.warning(f"Unauthorized backup attempt by user {user.id}")
        return

    try:
        # await update.message.reply_text("Starting manual backup process...")
        await reset_all_tasks_daily()
        await update.message.reply_text("✅.")
    except Exception as e:
        await update.message.reply_text(f"❌ Backup failed: {str(e)}")
        LOGGER.error(f"Manual backup failed: {e}", exc_info=True)

scheduler.add_job(reset_all_tasks_daily, 'cron', hour=0, minute=0)
scheduler.add_job(reset_daily_tops, 'cron', hour=0, minute=0)  # Every day at midnight
scheduler.add_job(reset_weekly_tops, 'cron', day_of_week='sun', hour=0, minute=0) 
scheduler.add_job(reset_dm_collection, 'cron', day_of_week='sun', hour=0, minute=0) # Every Sunday at midnight
scheduler.add_job(reset_monthly_tops, 'cron', day='last', hour=0, minute=0)  # Last day of the month at midnight
scheduler.add_job(perform_backup, 'cron', hour=0, minute=0)  # Every day at midnight
        

# Start the scheduler
scheduler.start()

# Command handlers
async def daily_top_grabbers(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is banned
    if await ban_collection.find_one({"user_id": user_id}):
        return

    try:
        # Fetch top users based on daily_top field
        cursor = user_collection.find(
            {},  # No time filter, as daily_top is already updated
            {"username": 1, "first_name": 1, "daily_top": 1}
        ).sort("daily_top", -1).limit(10)

        leaderboard_data = await cursor.to_list(length=10)

        # Generate the leaderboard message
        leaderboard_message = "<b>TOP 10 DAILY GRABBERS</b>\n\n"
        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
            daily_top = user.get('daily_top', 0)
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{daily_top}</b>\n'

        # Send the leaderboard with a random photo
        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        LOGGER.error(f"Error in daily_top_grabbers: {e}")
        await update.message.reply_text("An error occurred while generating the daily leaderboard.")

async def weekly_top_grabbers(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is banned
    if await ban_collection.find_one({"user_id": user_id}):
        return

    try:
        # Fetch top users based on weekly_top field
        cursor = user_collection.find(
            {},  # No time filter, as weekly_top is already updated
            {"username": 1, "first_name": 1, "weekly_top": 1}
        ).sort("weekly_top", -1).limit(10)

        leaderboard_data = await cursor.to_list(length=10)

        # Generate the leaderboard message
        leaderboard_message = "<b>TOP 10 WEEKLY GRABBERS</b>\n\n"
        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
            weekly_top = user.get('weekly_top', 0)
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{weekly_top}</b>\n'

        # Send the leaderboard with a random photo
        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        LOGGER.error(f"Error in weekly_top_grabbers: {e}")
        await update.message.reply_text("An error occurred while generating the weekly leaderboard.")

async def monthly_top_grabbers(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if the user is banned
    if await ban_collection.find_one({"user_id": user_id}):
        return

    try:
        # Fetch top users based on monthly_top field
        cursor = user_collection.find(
            {},  # No time filter, as monthly_top is already updated
            {"username": 1, "first_name": 1, "monthly_top": 1}
        ).sort("monthly_top", -1).limit(10)

        leaderboard_data = await cursor.to_list(length=10)

        # Generate the leaderboard message
        leaderboard_message = "<b>TOP 10 MONTHLY GRABBERS</b>\n\n"
        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
            monthly_top = user.get('monthly_top', 0)
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{monthly_top}</b>\n'

        # Send the leaderboard with a random photo
        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        LOGGER.error(f"Error in monthly_top_grabbers: {e}")
        await update.message.reply_text("An error occurred while generating the monthly leaderboard.")




SUPPORT_GROUP_LINK = "https://t.me/animechatiac"
SUPPORT_BUTTON_TEXT = "✨ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ✨"


def leaderboard_keyboard_ptb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏆 ᴛᴏᴘ", callback_data="switch_lb:top"),
            InlineKeyboardButton("👥 ᴛᴏᴘɢʀᴏᴜᴘs", callback_data="switch_lb:topgroups"),
        ],
        [
            InlineKeyboardButton("💸 ᴄᴏɪɴᴛᴏᴘ", callback_data="switch_lb:cointop"),
            InlineKeyboardButton("⚡ ᴛᴏᴋᴇɴᴛᴏᴘ", callback_data="switch_lb:tokentop"),
        ],
        [InlineKeyboardButton(SUPPORT_BUTTON_TEXT, url=SUPPORT_GROUP_LINK)],
    ])


async def resolve_user_line(user_doc: dict, metric: str, rank: int) -> str:
    user_id = user_doc.get("id")
    value = user_doc.get(metric, 0)

    resolved_name = html.escape(str(user_doc.get("first_name") or user_doc.get("username") or f"User {user_id}"))[:30]
    link = f"tg://user?id={user_id}"

    if getattr(userbot, "is_connected", False) and user_id is not None:
        try:
            u = await userbot.get_users(user_id)
            resolved_name = html.escape((u.first_name or resolved_name))[:30]
            if u.username:
                link = f"https://t.me/{u.username}"
            else:
                link = f"tg://user?id={u.id}"
        except Exception:
            pass

    return f"{rank}. <a href=\"{link}\"><b>{resolved_name}</b></a> ➾ <b>{value}</b>"


async def resolve_group_line(group_doc: dict, rank: int) -> str:
    group_id = group_doc.get("group_id")
    count = group_doc.get("count", 0)
    group_name = html.escape(group_doc.get("group_name", "Unknown"))[:30]

    if getattr(userbot, "is_connected", False) and group_id is not None:
        try:
            chat = await userbot.get_chat(group_id)
            gtitle = html.escape(chat.title or group_name)[:30]
            if getattr(chat, "username", None):
                glink = f"https://t.me/{chat.username}"
                return f"{rank}. <a href=\"{glink}\"><b>{gtitle}</b></a> ➾ <b>{count}</b>"
            return f"{rank}. <b>{gtitle}</b> ➾ <b>{count}</b>"
        except Exception:
            pass

    return f"{rank}. <b>{group_name}</b> ➾ <b>{count}</b>"


async def get_user_rank_by_metric(user_id: int, metric: str):
    user_doc = await user_collection.find_one({"id": user_id}, {metric: 1, "id": 1})
    if not user_doc:
        return None

    value = user_doc.get(metric, 0)
    higher_count = await user_collection.count_documents({metric: {"$gt": value}})
    return higher_count + 1


async def build_leaderboard_caption(mode: str, requester_id=None) -> str:
    if mode == "top":
        cursor = user_collection.find({}, {"id": 1, "username": 1, "first_name": 1, "total_characters": 1}).sort("total_characters", -1).limit(10)
        data = await cursor.to_list(length=10)
        lines = ["<b>TOP 10 USERS WITH MOST CHARACTERS</b>", ""]
        for i, user in enumerate(data, start=1):
            lines.append(await resolve_user_line(user, "total_characters", i))

        if requester_id is not None:
            my_rank = await get_user_rank_by_metric(requester_id, "total_characters")
            lines.append("")
            lines.append(f"<b>My Rank:</b> <b>{my_rank if my_rank is not None else 'Not ranked yet'}</b>")
        return "\n".join(lines)

    if mode == "topgroups":
        cursor = top_global_groups_collection.find({}, {"group_id": 1, "group_name": 1, "count": 1}).sort("count", -1).limit(10)
        data = await cursor.to_list(length=10)
        lines = ["<b>TOP 10 GROUPS WHO GUESSED MOST CHARACTERS</b>", ""]
        for i, group in enumerate(data, start=1):
            lines.append(await resolve_group_line(group, i))
        return "\n".join(lines)

    if mode == "cointop":
        data = await user_collection.aggregate([
            {"$project": {"id": 1, "username": 1, "first_name": 1, "coins": 1}},
            {"$sort": {"coins": -1}},
            {"$limit": 10},
        ]).to_list(length=10)
        lines = ["<b>Top 10 Users by Coins:</b>", ""]
        for i, user in enumerate(data, start=1):
            lines.append(await resolve_user_line(user, "coins", i) + " coins")

        if requester_id is not None:
            my_rank = await get_user_rank_by_metric(requester_id, "coins")
            lines.append("")
            lines.append(f"<b>My Rank:</b> <b>{my_rank if my_rank is not None else 'Not ranked yet'}</b>")
        return "\n".join(lines)

    if mode == "tokentop":
        data = await user_collection.aggregate([
            {"$project": {"id": 1, "username": 1, "first_name": 1, "tokens": 1}},
            {"$sort": {"tokens": -1}},
            {"$limit": 10},
        ]).to_list(length=10)
        lines = ["<b>Top 10 Users by Tokens:</b>", ""]
        for i, user in enumerate(data, start=1):
            lines.append(await resolve_user_line(user, "tokens", i) + " tokens")

        if requester_id is not None:
            my_rank = await get_user_rank_by_metric(requester_id, "tokens")
            lines.append("")
            lines.append(f"<b>My Rank:</b> <b>{my_rank if my_rank is not None else 'Not ranked yet'}</b>")
        return "\n".join(lines)

    return "<b>Leaderboard not found.</b>"


async def send_or_edit_leaderboard(target_message, mode: str, requester_id=None, edit: bool = False):
    caption = await build_leaderboard_caption(mode, requester_id=requester_id)
    markup = leaderboard_keyboard_ptb()

    if edit:
        await target_message.edit_caption(caption=caption, parse_mode='HTML', reply_markup=markup)
    else:
        photo_url = random.choice(PHOTO_URL)
        await target_message.reply_photo(photo=photo_url, caption=caption, parse_mode='HTML', reply_markup=markup)


# Fetch top 10 global groups
async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    try:
        await send_or_edit_leaderboard(update.message, "topgroups", requester_id=user_id, edit=False)
    except Exception as e:
        LOGGER.error(f"Error in global_leaderboard: {e}")
        await update.message.reply_text("An error occurred while generating the leaderboard.")

# Fetch top 10 users in a specific group
async def ctop(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return  # Do nothing if the user is banned

    try:
        chat_id = update.effective_chat.id
        leaderboard_data = GROUP_CACHE.get(f'group_leaderboard_{chat_id}')
        if not leaderboard_data:
            cursor = group_user_totals_collection.find({"group_id": chat_id}, {"username": 1, "first_name": 1, "count": 1}).sort("count", -1).limit(10)
            leaderboard_data = await cursor.to_list(length=10)
            GROUP_CACHE[f'group_leaderboard_{chat_id}'] = leaderboard_data  # Cache the data

        leaderboard_message = "<b>TOP 10 USERS WHO GUESSED CHARACTERS MOST TIME IN THIS GROUP..</b>\n\n"
        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
            character_count = user['count']
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'
        
        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        LOGGER.error(f"Error in ctop: {e}")
        await update.message.reply_text("An error occurred while generating the group leaderboard.")

# Fetch top 10 users globally (using total_characters field)
async def leaderboard(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    try:
        await send_or_edit_leaderboard(update.message, "top", requester_id=user_id, edit=False)
    except Exception as e:
        LOGGER.error(f"Error in leaderboard: {e}")
        await update.message.reply_text("An error occurred while generating the user leaderboard.")


async def switch_leaderboard_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    data = (query.data or "").split(":")
    if len(data) != 2 or data[0] != "switch_lb":
        return

    mode = data[1]
    if mode not in {"top", "topgroups", "cointop", "tokentop"}:
        return

    try:
        await send_or_edit_leaderboard(query.message, mode, requester_id=query.from_user.id, edit=True)
    except Exception as e:
        LOGGER.error(f"Error in switch leaderboard callback: {e}")
        await query.answer("Failed to load leaderboard.", show_alert=True)

# Display statistics (only for the owner)
async def stats(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in PARTNER:
        return
    try:
        user_count = await user_collection.estimated_document_count()
        group_count = await group_user_totals_collection.count_documents({})
        await update.message.reply_text(f'Total Users: {user_count}\nTotal Groups: {group_count}')
    except Exception as e:
        LOGGER.error(f"Error in stats: {e}")
        await update.message.reply_text("An error occurred while fetching statistics.")

# Initialize the bot with handlers
application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('top', leaderboard, block=False))
application.add_handler(CallbackQueryHandler(switch_leaderboard_callback, pattern=r'^switch_lb:'))
application.add_handler(CommandHandler("backup", backup_command))
application.add_handler(CommandHandler("resetalltasks", task_command))

# Add command handlers
application.add_handler(CommandHandler('dailytop', daily_top_grabbers, block=False))
application.add_handler(CommandHandler('weeklytop', weekly_top_grabbers, block=False))
application.add_handler(CommandHandler('monthlytop', monthly_top_grabbers, block=False))
