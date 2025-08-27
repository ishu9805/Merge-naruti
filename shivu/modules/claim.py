
import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
    force 
)
from shivu.modules.lock import command_lock as cmd
from shivu.modules.fjoin import check_membership as fj
DEVS = (7378476666)
CHAT_ID = "-1002338924488"

CHARACTERS_PER_PAGE = 10
# Lock dictionary to track command processing
claim_lock = {}

# New emoji list for fun responses

        
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



@cmd
@app.on_message(filters.command(["hclaim"]))
async def hclaim(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention


    if str(message.chat.id) != "-1002783891820":
        await message.reply_text("you can only use this command here @hclaim_support")
        return
        
    if message.forward_date:
        return

    # Create a unique lock key for this user
    lock_key = f"hclaim_{user_id}"
    
    # Check if command is already being processed for this user
    if lock_key in claim_lock:
        await message.reply_text("⏳ Your claim request is already being processed. Please wait.")
        return

    # Set the lock before any processing begins
    claim_lock[lock_key] = True
    
    try:
        # Check if the user is banned
        user = await user_collection.find_one({"id": user_id})
        if not user:
            await message.reply_text(f"Please start the bot in DM first [start](https://t.me/Naruto_waifu_husbando_bot?start=start)")
            return

        
        # Get user data with atomic operation to prevent race conditions
        user_data = await user_collection.find_one_and_update(
            {'id': user_id},
            {'$setOnInsert': {
                'id': user_id,
                'username': message.from_user.username,
                'characters': [],
                'last_daily_reward': None
            }},
            upsert=True,
            return_document=True
        )

        # Check last claim time with timezone awareness
        last_claimed = user_data.get('last_daily_reward')
        if last_claimed:
            last_claimed = last_claimed.replace(tzinfo=None)
            now = datetime.utcnow()
            
            if last_claimed.date() == now.date():
                remaining = (last_claimed + timedelta(days=1)) - now
                formatted_time = await format_time_delta(remaining)
                await message.reply_text(f"⏳ You've already claimed today! Next reward in: `{formatted_time}`")
                return

        # Get unique character with transaction to ensure atomicity
        async with await db.client.start_session() as session:
            async with session.start_transaction():
                unique_characters = await get_unique_characters(user_id)
                
                if not unique_characters:
                    await message.reply_text("🚫 No unique characters available right now. Try again later!")
                    return

                # Update all collections in a single transaction
                await user_collection.update_one(
                    {'id': user_id},
                    {
                        '$push': {'characters': {'$each': unique_characters}},
                        '$set': {
                            'last_daily_reward': datetime.utcnow(),
                            'username': message.from_user.username
                        }
                    },
                    session=session
                )
                
                await user_count.update_one(
                    {'user_id': user_id},
                    {'$inc': {'ccount': 1}},
                    upsert=True,
                    session=session
                )
                
                for character in unique_characters:
                    rarity = character['rarity']
                    await user_count.update_one(
                        {'user_id': user_id},
                        {'$inc': {f'rarity_count.{rarity}': 1}},
                        upsert=True,
                        session=session
                    )

        # Send the reward message after successful transaction
        for character in unique_characters:
            await message.reply_photo(
                photo=character['img_url'],
                caption=(
                    f"🎉 Congratulations {mention}! 🌟\n"
                    f"✨ *Name*: {character['name']}\n"
                    f"🧬 *Rarity*: {character['rarity']}\n"
                    f"📺 *Anime*: {character['anime']}\n"
                    f"🍀 *Come back tomorrow for another claim!*"
                )
            )

    except Exception as e:
        logging.error(f"Error in hclaim for user {user_id}: {str(e)}", exc_info=True)
        await message.reply_text("⚠️ An error occurred while processing your claim. Please try again later.")
    finally:
        # Always release the lock when done
        claim_lock.pop(lock_key, None)


#@app.on_message(filters.command(["check"]))
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
        


@app.on_message(filters.command(["find"]))
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

@app.on_callback_query(filters.regex(r"next_(.+)_(\d+)"))
async def next_page_callback(_, callback_query: t.CallbackQuery):
    anime_name, page = callback_query.data.split("_")[1], int(callback_query.data.split("_")[2])
    characters = await collection.find({'anime': anime_name}).to_list(length=None)
    await send_character_page(callback_query.message, characters, anime_name, page)
    await callback_query.answer()
