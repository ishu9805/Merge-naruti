
import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot, user_collection, collection, ban_collection, PARTNER, required_group_id 
from shivu import application, user_count
# Constants
DEVS = (7378476666)
CHAT_ID = "-1002338924488"
JOIN_URL = "https://t.me/naruto_support_chat"
CHARACTERS_PER_PAGE = 10

# Lock dictionary to track command processing
claim_lock = {}

# New emoji list for fun responses
async def is_member(user_id):
    """Check if a user is part of the required group."""
    try:
        member = await application.bot.get_chat_member(required_group_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False
        
async def format_time_delta(delta):
    seconds = delta.total_seconds()
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

async def get_unique_characters(user_id, target_rarities=['⚪️ Common', '🟣 Rare', '🟡 Legendary', '🟢 Medium', '💮 Special Edition']):
    try:
        user_data = await user_collection.find_one({'id': user_id}, {'characters': 1})
        user_character_ids = {char['id'] for char in user_data['characters']} if user_data else set()

        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': list(user_character_ids)}}},
            {'$sample': {'size': 1}}
        ]
        
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        print(f"Error fetching unique characters: {e}")
        return []



async def update_user_characters(user_id, characters):
    await user_collection.update_one(
        {'id': user_id},
        {
            '$push': {'characters': {'$each': characters}},
            '$set': {'last_daily_reward': datetime.utcnow()}
        }
    )


@bot.on_message(filters.command(["hclaim"]))
async def hclaim(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    if message.forward_date:
        return

    if user_id in claim_lock:
        await message.reply_text("Your claim request is already being processed. Please wait.")
        return

    # Set the lock
    claim_lock[user_id] = True

    try:
        user = await user_collection.find_one({"id": user_id})
        if not user:
            await message.reply_text(f"Please start the bot in DM first [start](https://t.me/fancy_waifu_husbando_bot?start=start)")
            return

        # Check if the user is banned
        is_banned = await ban_collection.find_one({"user_id": user_id})
        if is_banned:
            return

        if not await is_member(user_id):
            group_link = "https://t.me/blade_x_community"
            messages = (
                "You need to be a member of our exclusive group to use this command.\n"
                "Join now and explore the amazing features awaiting you!\n\n"
            )
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("✨ Join the Group ✨", url=group_link)]]
            )
            await message.reply_text(messages, reply_markup=reply_markup)
            return

        user_data = user or {
            'id': user_id,
            'username': message.from_user.username,
            'characters': [],
            'last_daily_reward': None
        }

        last_claimed_date = user_data.get('last_daily_reward')
        if last_claimed_date and last_claimed_date.date() == datetime.utcnow().date():
            remaining_time = timedelta(days=1) - (datetime.utcnow() - last_claimed_date)
            formatted_time = await format_time_delta(remaining_time)
            await message.reply_text(f"⏳ You've already claimed today! Next reward in: `{formatted_time}`")
            return

        unique_characters = await get_unique_characters(user_id)
        if not unique_characters:
            return await message.reply_text("🚫 No unique characters found.")

        await update_user_characters(user_id, unique_characters)
      
        for character in unique_characters:
            await message.reply_photo(
                photo=character['img_url'],
                caption=f"🎉 Congratulations {mention}! 🌟\n✨ *Name*: {character['name']}\n🧬 *Rarity*: {character['rarity']}\n📺 *Anime*: {character['anime']}\n🍀 *Come back tomorrow for another claim!*"
            )

    except Exception as e:
        logging.error(f"Error in hclaim for user {user_id}: {e}")
        await message.reply_text("An error occurred while processing your claim. Please try again later.")
    finally:
        claim_lock.pop(user_id, None)



@bot.on_message(filters.command(["check"]))
async def hfind(_, message: t.Message):
    if len(message.command) < 2:
        return await message.reply_text("📌 Please provide the ID 🆔", quote=True)
    
    waifu_id = message.command[1]
    waifu = await collection.find_one({'id': waifu_id})
    
    if not waifu:
        return await message.reply_text("🔍 No character found with that ID ❌", quote=True)
    
    # Fetch user ownership data
    user_ownership_data = await user_collection.aggregate([
        {'$match': {'characters.id': waifu_id}},
        {'$unwind': '$characters'},
        {'$match': {'characters.id': waifu_id}},
        {'$group': {'_id': '$id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]).to_list(length=10)
    
    global_count = sum(user['count'] for user in user_ownership_data)
    top_users = user_ownership_data[:10]  # Limit to the top 5 users for display

    # Build top collectors list
    usernames = []
    for user_info in top_users:
        user_id = user_info['_id']
        try:
            user = await bot.get_users(user_id)
            link = f"[{user.first_name}](tg://user?id={user.id})"
            usernames.append(f"{link} x{user_info['count']}")
        except Exception:
            usernames.append(f"[User {user_id}](tg://user?id={user_id}) x{user_info['count']}")
    
    # Escape Markdown characters in waifu fields
    escape_md = lambda text: text.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")
    waifu_name = escape_md(waifu['name'])
    waifu_rarity = escape_md(waifu['rarity'])
    waifu_anime = escape_md(waifu['anime'])
    waifu_id = waifu['id']

    # Prepare caption
    caption = (
        f"📜 **Character Info**\n"
        f"🧩 **Name**: {waifu_name}\n"
        f"🧬 **Rarity**: {waifu_rarity}\n"
        f"📺 **Anime**: {waifu_anime}\n"
        f"🆔 **ID**: {waifu_id}\n\n"
        f"🌍 **Global Count**: {global_count} users own this character.\n\n"
        f"🏆 **Top Collectors**:\n"
        + "\n".join(f"{i + 1}. {user}" for i, user in enumerate(usernames))
    )

    try:
        media_url = waifu.get('img_url') or waifu.get('vid_url')

        if 'vid_url' in waifu:
            # Send video
            send = await message.reply_video(video=media_url, caption=caption, supports_streaming=True)
        else:
            # Send photo
            send = await message.reply_photo(photo=media_url, caption=caption)

        # Optional: delete the message after 30 seconds
        await asyncio.sleep(30)
        await send.delete()
    except Exception as e:
        print(f"Error sending character info for ID {waifu_id}: {e}")
        await message.reply_text("🚫 Failed to send character information. Please try again later.")
        


@bot.on_message(filters.command(["find"]))
async def cfind(_, message: t.Message):
    if len(message.command) < 2:
        return await message.reply_text("Please provide the anime name.", quote=True)

    anime_name = " ".join(message.command[1:])
    characters = await collection.find({'anime': anime_name}).to_list(length=None)

    if not characters:
        return await message.reply_text(f"No characters found from the anime {anime_name}.", quote=True)

    page = 0
    await send_character_page(message, characters, anime_name, page)

async def send_character_page(message, characters, anime_name, page):
    start = page * CHARACTERS_PER_PAGE
    end = start + CHARACTERS_PER_PAGE
    paginated_characters = characters[start:end]

    captions = [
        f"🎏 Name: {char['name']}\n🪅 ID: {char['id']}\n🧩 Rarity: {char['rarity']}\n"
        for char in paginated_characters
    ]
    response = "\n".join(captions)

    keyboard = []
    if end < len(characters):
        keyboard.append([InlineKeyboardButton("Next", callback_data=f"next_{anime_name}_{page+1}")])

    await message.reply_text(
        f"🍁 Characters from {anime_name} (Page {page + 1}):\n\n{response}",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
        quote=True
    )

@bot.on_callback_query(filters.regex(r"next_(.+)_(\d+)"))
async def next_page_callback(_, callback_query: t.CallbackQuery):
    anime_name, page = callback_query.data.split("_")[1], int(callback_query.data.split("_")[2])
    characters = await collection.find({'anime': anime_name}).to_list(length=None)
    await send_character_page(callback_query.message, characters, anime_name, page)
    await callback_query.answer()
