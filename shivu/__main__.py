import asyncio
import datetime
import importlib
import random
import re
import time
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.constants import ReactionEmoji
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from shivu import (
    app,
    collection,
    top_global_groups_collection,
    group_user_totals_collection,
    user_collection,
    user_totals_collection,
    shivuu,
    application,
    SUPPORT_CHAT,
    UPDATE_CHAT,
    db,
    ban_collection,
    LOGGER
)
from shivu import user_count
from shivu.modules import ALL_MODULES
from shivu.modules.coin import add_coins, update_leaderboards
from shivu.modules.leaderboard import create_indexes

all_characters = []

reaction_list = [ReactionEmoji.THUMBS_UP, ReactionEmoji.EYES, ReactionEmoji.CLAPPING_HANDS, ReactionEmoji.BOTTLE_WITH_POPPING_CORK, ReactionEmoji.DOVE_OF_PEACE, ReactionEmoji.GRINNING_FACE_WITH_STAR_EYES, ReactionEmoji.HEART_ON_FIRE, ReactionEmoji.PARTY_POPPER]

async def preload_characters(context: CallbackContext) -> None:
    global all_characters
    try:
        all_characters = await collection.find({}).to_list(length=None)
        
        if all_characters:
            LOGGER.info(f"Preloaded {len(all_characters)} characters from the main characters from the collection.")
        else:
            LOGGER.warning("No characters found in the databases.")
    except Exception as e:
        LOGGER.error(f"Error preloading characters: {e}")

async def react_to_message(chat_id, message_id, emoji):
    await shivuu.send_reaction(chat_id, message_id, emoji)

locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)

last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

async def message_counter(update: Update, context: CallbackContext) -> None:
    if update.effective_user.is_bot:
        return

    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    is_banned = await ban_collection.find_one({"user_id": user_id})
    
    if is_banned:
        return

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 100)
        else:
            message_frequency = 100

        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 4:
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0

async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    current_time = datetime.datetime.now().strftime("%Y-%m-%d")

    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    if len(sent_characters[chat_id]) == len(all_characters):
        sent_characters[chat_id] = []

    if chat_id in message_counters:
        today_message_count = message_counters[chat_id].get(current_time, 0)
    else:
        today_message_count = 0

    rarities = {
        1: '⚪️ Common',
        2: '🟣 Rare',
        3: '🟡 Legendary',
        4: '🟢 Medium',
        5: '💮 Special edition',
        6: '🔮 Limited Edition',
        7: '💸 Premium Edition',
        8: '🌤 Summer',
        9: '🎐 Celestial',
        10: '❄️ Winter',
        11: '💝 Valentine',
        12: '🎃 Halloween',
        13: '🎄 Christmas Special',
        14: '🎭 Cosplay Master 🎭',
        15: '🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐',
        16: '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣'  # New rarity added
    }

    spawn_counts = {
        '⚪️ Common': 5,
        '🟣 Rare': 5,
        '🟢 Medium': 5,
        '🟡 Legendary': 5,
        '💮 Special Edition': 3,
        '🔮 Limited Edition': 1,
        '💸 Premium Edition': 0,
        '🌤 Summer': 0 if today_message_count <= 4 else 0,
        '🎐 Celestial': 1 if datetime.datetime.today().weekday() in [0, 7] else 0,
        '❄️ Winter': 1,
        '💝 Valentine': 0,
        '🎃 Halloween': 0,
        '🎄 Christmas Special': 0,
        '🎭 Cosplay Master 🎭': 0,
        '🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐': 0,
        '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣': 0 if chat_id == -1002338924488 else 0 # New rarity spawn count
    }
    # Get the message count for the chat_id, defaulting to 0 if it doesn't exist
    message_count = message_counts.get(chat_id, 0)

    # Check if the chat_id is -1002338924488 and if the message count is a multiple of 500
    
        
    characters_to_spawn = []
    for rarity, count in spawn_counts.items():
        characters_to_spawn.extend([c for c in all_characters if c.get('id') not in sent_characters[chat_id] and c.get('rarity') == rarity] * count)

    if not characters_to_spawn:
        characters_to_spawn = all_characters

    character = random.choice(characters_to_spawn)

    if character.get('rarity') == '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣':
        await context.bot.send_message(chat_id=7378476666, text=f"An animated character has spawned! Character id: {character['id']}")

    if character.get('rarity') == '🔮 Limited Edition':
        await context.bot.send_message(chat_id=7378476666, text=f"An limited character has spawned! Character id: {character['id']}")

    if character.get('rarity') == '❄️ Winter':
        await context.bot.send_message(chat_id=7378476666, text=f"An winter character has spawned! Character id: {character['id']}")


    
    rarity_name = rarities.get(character['rarity'], f'{character["rarity"]}')

    sent_characters[chat_id].append(character.get('id'))
    last_characters[chat_id] = character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    if character.get('img_url'):
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=f"🌟 A new *{rarity_name}* character has arrived! 🔥 Guess their name with /guess [Name] to add them to your harem! 🌟",
            parse_mode='Markdown'
        )
    elif character.get('vid_url'):
        await context.bot.send_video(
            chat_id=chat_id,
            video=character['vid_url'],
            caption=f"🌟 Get ready! A *{rarity_name}* character has emerged! 🏃‍♂️ Guess their name with /guess [Name] to add them to your harem! 🌟",
            parse_mode='Markdown',
            supports_streaming=True
        )

    spawn_counts['🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣'] = 0  # Reset after spawning




async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_id = update.message.message_id
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        return

    guess = ' '.join(context.args).lower() if context.args else ''
    
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text("Nahh You Can't use This Types of words in your guess..❌️")
        return

    name_parts = last_characters[chat_id]['name'].lower().split()

    character = last_characters[chat_id]
    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id
        rarity = character.get("rarity", "")
        random_reaction = random.choice(reaction_list)
        try:
            await update.message.set_reaction(random_reaction)
        except Exception as e:
            # Log the error and notify in the message if reaction fails
            print(f"Failed to set reaction: {e}")
            await update.message.reply_text("🎉 Reaction not set due to a group limitation.")
        
        # Set the appropriate inline query
        if rarity == "🎗️ 𝘼𝙣𝙞𝙢𝙖𝙩𝙚𝙙":
            inline_query = f"collection.vid.{user_id}"
        else:
            inline_query = f"collection.img.{user_id}"
        
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    "View Collection",
                    switch_inline_query_current_chat=inline_query
                )
            ]]
        )
        await update.message.reply_text("🎉 Congrats! You've earned 40 dazzling coins for guessing correctly! 💰")
        await update.message.reply_text(
            f'<b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> 🎊 You guessed the character!\n\n'
            f'🍁 Name: <b>{last_characters[chat_id]["name"]}</b>\n'
            f'⛩ Anime: <b>{last_characters[chat_id]["anime"]}</b>\n'
            f'🎐 Rarity: <b>{last_characters[chat_id]["rarity"]}</b>\n\n'
            f'This character is now in your harem! Use /mycollection to see your harem.',
            parse_mode='HTML',
            reply_markup=keyboard
        )
        await add_coins(int(user_id), 40)
                
        await user_count.update_one(
            {'user_id': user_id},
            {'$inc': {f'rarity_count.{rarity}': 1}},
            upsert=True
        )
        
        
        await user_count.update_one(
            {'user_id': user_id},
            {'$inc': {'ccount': 1}},
            upsert=True
        )
        
        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
      
        elif hasattr(update.effective_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        
        group_user_total = await group_user_totals_collection.find_one({'user_id': user_id, 'group_id': chat_id})
        if group_user_total:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != group_user_total.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != group_user_total.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$set': update_fields})
            
            await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await group_user_totals_collection.insert_one({
                'user_id': user_id,
                'group_id': chat_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'count': 1,
            })


    
        group_info = await top_global_groups_collection.find_one({'group_id': chat_id})
        if group_info:
            update_fields = {}
            if update.effective_chat.title != group_info.get('group_name'):
                update_fields['group_name'] = update.effective_chat.title
            if update_fields:
                await top_global_groups_collection.update_one({'group_id': chat_id}, {'$set': update_fields})
            
            await top_global_groups_collection.update_one({'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await top_global_groups_collection.insert_one({
                'group_id': chat_id,
                'group_name': update.effective_chat.title,
                'count': 1,
            })


    else:
        await update.message.reply_text('❌ Oops! Wrong character name. Try again!')

   

async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    if not context.args:
        await update.message.reply_text('🚨 Please provide the character ID to proceed.')
        return

    character_id = context.args[0]
    user = await user_collection.find_one({'id': user_id})

    if not user:
        await update.message.reply_text("🎉 Start guessing characters to build your collection!")
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await update.message.reply_text('❌ This character is not in your collection.')
        return

    user['favorites'] = [character_id]
    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})

    await update.message.reply_text(f'🌟 {character["name"]} has been added to your favorites!')



"""async def show_message_count(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f"Message")
    chat_id = str(update.effective_chat.id)
    count = message_counters.get(chat_id, 0)
    await update.message.reply_text(f"Message count for this group: {count}")
    """
    

def error_handler(update: Update, context: CallbackContext):
    """Log the error and handle it gracefully."""
    LOGGER.error("An error occurred: %s", context.error)

def main() -> None:
    """Run bot."""
    application.job_queue.run_once(preload_characters, when=0)
    application.add_handler(CommandHandler(["guess"], guess, block=False))
    application.add_handler(CommandHandler("fav", fav, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))
    #application.add_handler(CommandHandler("mecount", show_message_count, block=False))
    
    # Use asyncio.create_task to run the bot in the background
    asyncio.create_task(application.run_polling(drop_pending_updates=True))
    application.add_error_handler(error_handler)
    asyncio.gather(update_leaderboards(), create_indexes())
    
if __name__ == "__main__":
    shivuu.start()
    #app.start()
  
    main()
