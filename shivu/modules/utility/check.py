import asyncio
import logging
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuups as bot, userbot, user_collectionps as user_collection, collectionps as collection

def is_userbot_running() -> bool:
    """Return True when the userbot session is connected."""
    return bool(getattr(userbot, "is_connected", False))


async def fetch_user(user_id, use_userbot: bool = True):
    """Resolve a Telegram user with userbot first, then fall back to bot."""
    normalized_id = user_id
    if isinstance(user_id, str) and user_id.isdigit():
        normalized_id = int(user_id)

    # Prefer userbot: it can resolve users even when they never interacted with the bot.
    if use_userbot and is_userbot_running():
        try:
            return await userbot.get_users(normalized_id)
        except Exception:
            pass

    # Secondary fallback for users already known by the bot session.
    try:
        return await bot.get_users(normalized_id)
    except Exception:
        return None
    
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

async def build_user_links(top_users, offset=0, limit=10, use_userbot=True):
    """Build formatted user links for display with pagination."""
    usernames = []
    for i, user_info in enumerate(top_users[offset:offset+limit], start=offset+1):
        user_id = user_info['_id']
        try:
            user = await fetch_user(user_id, use_userbot=use_userbot)
            if not user:
                raise ValueError("User not resolvable")

            # Use username if available, otherwise fallback to silent mention
            if user.username:
                user_link = f"https://t.me/{user.username}"
            else:
                user_link = f"tg://user?id={user.id}"
            
            name = escape_md(user.first_name)
            usernames.append(f"{i}. [{name}]({user_link}) ×{user_info['count']}")
        except Exception as e:
            logging.error(f"Error getting user info for {user_id}: {e}")
            usernames.append(f"{i}. [User {user_id}](tg://user?id={user_id}) ×{user_info['count']}")
    return usernames

@bot.on_message(filters.command(["check"]))
async def hfind(_, message: t.Message):
    if len(message.command) < 2:
        return await message.reply_text("📌 Please provide the ID after the command.\nExample: `/check 123`")
    
    waifu_id = message.command[1].strip()
    offset = 0  # Default offset for pagination
    limit = 10   # Number of users to show per page
    
    # Check if there's a callback query with offset data
    if len(message.command) > 2 and message.command[2].isdigit():
        offset = int(message.command[2])
    
    #await message.reply_chat_action("typing")

    userbot_online = is_userbot_running()

    waifu = await get_character_info(waifu_id)
    if not waifu:
        return await message.reply_text("🔍 No character found with that ID. Please check the ID and try again.")
    
    try:
        user_ownership_data = await get_top_collectors(waifu_id, limit=50)  # Get more users for pagination
        global_count = sum(user['count'] for user in user_ownership_data)
        usernames = await build_user_links(user_ownership_data, offset, limit, use_userbot=userbot_online)
    except Exception as e:
        logging.error(f"Error getting collector data: {e}")
        return await message.reply_text("⚠️ An error occurred while fetching collector data. Please try again later.")

    # Prepare caption
    caption = (
        f"📜 **Character Info**\n"
        f"🧩 **Name**: {escape_md(waifu.get('name', 'N/A'))}\n"
        f"🧬 **Rarity**: {escape_md(waifu.get('rarity', 'N/A'))}\n"
        f"📺 **Anime**: {escape_md(waifu.get('anime', 'N/A'))}\n"
        f"🆔 **ID**: {waifu_id}\n\n"
        f"🌍 **Global Count**: {global_count} users own this character.\n\n"
    )
    
    if usernames:
        caption += "🏆 **Top Collectors**:\n" + "\n".join(usernames)

    if not userbot_online:
        caption += "\n\n⚠️ **Userbot Status**: Offline. Showing best effort results from bot cache only."
    
    # Create buttons for pagination
    buttons = []
    if offset > 0:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"check_prev_{waifu_id}_{offset}"))
    if offset + limit < len(user_ownership_data):
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"check_next_{waifu_id}_{offset}"))
    
    # Add close button
    buttons.append(InlineKeyboardButton("❌ Close", callback_data="close_message"))
    
    reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

    try:
        media_url = waifu.get('img_url') or waifu.get('vid_url')
        
        if not media_url:
            return await message.reply_text(
                caption, 
                reply_markup=reply_markup
            )

        if 'vid_url' in waifu:
            await message.reply_video(
                video=media_url,
                caption=caption,
                supports_streaming=True,
                reply_markup=reply_markup
            )
        else:
            await message.reply_photo(
                photo=media_url,
                caption=caption,
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logging.error(f"Error sending media for {waifu_id}: {e}")
        await message.reply_text(
            caption, 
            reply_markup=reply_markup
        )

@bot.on_callback_query(filters.regex(r"^check_(prev|next)_(\d+)_(\d+)$"))
async def paginate_collectors(_, query: t.CallbackQuery):
    action, waifu_id, offset = query.data.split('_')[1:]
    offset = int(offset)
    limit = 5
    
    if action == "prev":
        new_offset = max(0, offset - limit)
    else:
        new_offset = offset + limit
    
    # Edit the message with new offset
    await query.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Previous", callback_data=f"check_prev_{waifu_id}_{new_offset}"),
            InlineKeyboardButton("Next ➡️", callback_data=f"check_next_{waifu_id}_{new_offset}"),
            InlineKeyboardButton("❌ Close", callback_data="close_message")
        ]])
    )
    await query.answer()

@bot.on_callback_query(filters.regex("^close_message$"))
async def close_message(_, query: t.CallbackQuery):
    await query.message.delete()
    await query.answer("Closed the message", show_alert=False)
