import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuups as bot, user_collectionps as user_collection, collectionps as collection
from shivu import applicationps as application

def escape_md(text: str) -> str:
    """Escape Markdown special characters."""
    if not text:
        return ""
    return text.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")

async def get_character_info(waifu_id: str):
    """Fetch character information from database."""
    try:
        return await collection.find_one({'id': waifu_id})
    except Exception as e:
        logging.error(f"Database error fetching character {waifu_id}: {e}")
        return None

async def get_top_collectors(waifu_id: str, limit: int = 10):
    """Fetch top collectors for a character."""
    try:
        pipeline = [
            {'$match': {'characters.id': waifu_id}},
            {'$unwind': '$characters'},
            {'$match': {'characters.id': waifu_id}},
            {'$group': {'_id': '$id', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]
        return await user_collection.aggregate(pipeline).to_list(length=limit)
    except Exception as e:
        logging.error(f"Database error fetching collectors for {waifu_id}: {e}")
        return []

async def build_user_links(top_users):
    """Build formatted user links for display."""
    usernames = []
    for user_info in top_users:
        user_id = user_info['_id']
        try:
            user = await bot.get_users(user_id)
            link = f"[{escape_md(user.first_name)}](tg://user?id={user.id})"
            usernames.append(f"{link} ×{user_info['count']}")
        except Exception as e:
            logging.error(f"Error getting user info for {user_id}: {e}")
            usernames.append(f"[User {user_id}](tg://user?id={user_id}) ×{user_info['count']}")
    return usernames

@bot.on_message(filters.command(["check"]))
async def hfind(_, message: t.Message):
    if len(message.command) < 2:
        return await message.reply_text("📌 Please provide the ID 🆔", quote=True)
    
    waifu_id = message.command[1].strip()
    
    # Show typing indicator
    #await message.reply_chat_action("typing")
    
    waifu = await get_character_info(waifu_id)
    if not waifu:
        return await message.reply_text("🔍 No character found with that ID ❌", quote=True)
    
    # Get ownership data in parallel
    user_ownership_data, _ = await asyncio.gather(
        get_top_collectors(waifu_id)
    )
    
    global_count = sum(user['count'] for user in user_ownership_data)
    usernames = await build_user_links(user_ownership_data)

    # Prepare caption
    caption = (
        f"📜 **Character Info**\n"
        f"🧩 **Name**: {escape_md(waifu['name'])}\n"
        f"🧬 **Rarity**: {escape_md(waifu['rarity'])}\n"
        f"📺 **Anime**: {escape_md(waifu['anime'])}\n"
        f"🆔 **ID**: {waifu['id']}\n\n"
        f"🌍 **Global Count**: {global_count} users own this character.\n\n"
    )
    
    if usernames:
        caption += f"🏆 **Top Collectors**:\n" + "\n".join(f"{i + 1}. {user}" for i, user in enumerate(usernames))

    try:
        media_url = waifu.get('img_url') or waifu.get('vid_url')
        if not media_url:
            return await message.reply_text(caption, quote=True)

        if 'vid_url' in waifu:
            sent = await message.reply_video(
                video=media_url,
                caption=caption,
                supports_streaming=True
            )
        else:
            sent = await message.reply_photo(
                photo=media_url,
                caption=caption
            )

        # Optional: delete after delay
        await asyncio.sleep(30)
        await sent.delete()
        
    except Exception as e:
        logging.error(f"Error sending media for {waifu_id}: {e}")
        await message.reply_text(caption, quote=True)
