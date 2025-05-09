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
    ban_collectionps as ban_collection
    
)
from shivu import user_countps as user_count, chat_dataps as chat_data
from shivu.modules import ALL_MODULES
from shivu.modules.coin import add_coins
#from shivu.modules.Task import update_counts
from shivu.modules.top import create_indexes
from shivu.modules.Hprofile import upgrade_chat_data
from shivu.modules.block import block_dec, temp_block, block_dec_ptb, block_cbq_ptb
import os
from threading import Thread
from flask import Flask



all_characters = []
valentine_spawn_thresholds = {} 
amv_spawn_thresholds = {} # Store random thresholds for Valentine spawn
summer_spawn_thresholds = {}
reaction_list = [ReactionEmoji.THUMBS_UP, ReactionEmoji.EYES, ReactionEmoji.CLAPPING_HANDS, ReactionEmoji.BOTTLE_WITH_POPPING_CORK, ReactionEmoji.DOVE_OF_PEACE, ReactionEmoji.GRINNING_FACE_WITH_STAR_EYES, ReactionEmoji.HEART_ON_FIRE, ReactionEmoji.PARTY_POPPER]
current_amv_character = {}  # Tracks AMV characters per chat
amv_claim_limit = 1  #

"""server = Flask(__name__)
@server.route("/")
def home():
    return "Bot is running"
"""
    

async def preload_characters(context: CallbackContext) -> None:
    global all_characters
    try:
        # Fetch characters with IDs between 1 and 4500
        all_characters = await collection.find({'id': {'$gte': '01', '$lte': '7000'}}).to_list(length=None)
        
        if all_characters:
            print(f"Preloaded {len(all_characters)} characters with IDs from 1 to 4500.")
        else:
            print("No characters found in the specified ID range.")
    except Exception as e:
        print(f"Error preloading characters: {e}")


async def update_total_characters_for_all_users():
    try:
        print("Updating total_characters for all users...")
        cursor = user_collection.find({})
        async for user in cursor:
            total_characters = len(user.get('characters', []))
            await user_collection.update_one(
                {"id": user["id"]},
                {"$set": {"total_characters": total_characters}}
            )
        print("Successfully updated total_characters for all users.")
    except Exception as e:
        print(f"Error updating total_characters: {e}")


async def react_to_message(chat_id, message_id, emoji):
    try:
       await shivuu.send_reaction(chat_id, message_id, emoji)
    except:
       pass

locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}
total_message_counts ={}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)

last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


@block_dec_ptb
async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    
    if temp_block(user_id):
        return

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        # Initialize total message count and random threshold for Valentine spawn
        if chat_id not in total_message_counts:
            total_message_counts[chat_id] = 0
            total_message_counts2[chat_id] = 0
            
            valentine_spawn_thresholds[chat_id] = random.randint(7000, 10000)
            summer_spawn_thresholds[chat_id]  = random.randint(1800, 4000)
            if chat_id == -1002606804832:
                amv_spawn_thresholds[chat_id] = random.randunt(600, 2000)
        # Increment total message count for the chat
        total_message_counts[chat_id] += 1
        total_message_counts2[chat_id] += 1
        # Existing logic for message frequency
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        message_frequency = chat_frequency.get('message_frequency', 100) if chat_frequency else 100

        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 6:
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

        # Check if total message count matches the random threshold
        if total_message_counts[chat_id] == valentine_spawn_thresholds[chat_id]:
            await spawn_valentine_character(update, context)
            # Reset the threshold for the next spawn
            valentine_spawn_thresholds[chat_id] = random.randint(2000, 5000)

        if total_message_counts[chat_id] == summer_spawn_thresholds[chat_id]:
            await spawn_summer_character(update, context)
            summer_spawn_thresholds[chat_id] = random.randint(650, 1000)
            total_message_counts[chat_id] = 0

        if total_message_counts2[chat_id] == amv_spawn_thresholds[chat_id]:
            await spawn_amv_character(update, context)
            # Reset the threshold for the next spawn
            amv_spawn_thresholds[chat_id] = random.randint(3000, 5000)
            


async def spawn_amv_character(update: Update, context: CallbackContext) -> None:
    """Spawn a special AMV character"""
    chat_id = update.effective_chat.id
    
    if chat_id not in sent_characters:
        sent_characters[chat_id] = []
        
    # Get only AMV characters that aren't locked
    amv_chars = [c for c in all_characters if c.get('rarity') == "🎗️ �𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣" and not c.get('slock', False)]
    
    if not amv_chars:
        print("No AMV characters available to spawn")
        return

    # Filter characters that haven't reached global claim limit
    available_chars = []
    for char in amv_chars:
        # Check how many users have claimed this character
        claim_count = await user_collection.count_documents({
            "characters.id": char["id"]
        })
        if claim_count < amv_claim_limit:
            available_chars.append(char)

    if not available_chars:
        print("All AMV characters have reached claim limit")
        return

    char = random.choice(available_chars)
    current_amv_character[chat_id] = {
        "name": char["name"],
        "anime": char["anime"],
        "rarity": char["rarity"],
        "id": char["id"],
        "img_url": char.get("img_url"),
        "vid_url": char.get("vid_url"),
        "claimed": False
    }

    # Send the AMV character with appropriate media
    caption = ("🎬 **AMV CHARACTER APPEARED!** 🎬\n\n"
              "💎 *Rarity:* AMV Edition (Ultra Rare)\n\n"
              "✍️ Guess the character name with `/guess [name]` to claim it!")
    
    try:
        if char.get("vid_url"):
            await context.bot.send_video(
                chat_id=chat_id,
                video=char["vid_url"],
                supports_streaming=True,
                caption=caption,
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=char["img_url"],
                caption=caption,
                parse_mode='Markdown'
            )
    except Exception as e:
        print(f"Error sending AMV character: {e}")


async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    current_time = datetime.datetime.now().strftime("%Y-%m-%d")

    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    alls_characters = [c for c in all_characters if not c.get('slock', False)]
    
    if not alls_characters:
        await update.effective_chat.send_message("No characters available to spawn right now.")
        return


    if len(sent_characters[chat_id]) == len(alls_characters):
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
        5: '🟣 Rare',
        6: '🟡 Legendary',
        7: '💮 Special Edition',
        6: '🟡 Legendary',
        8: '🔮 Limited Edition',
        9: '🟢 Medium',
        10: '💸 Premium Edition',
        11: '🌤 Summer',
        12: '🎐 Celestial',
        13: '❄️ Winter',
        14: '💝 Valentine',
        15: '🎃 Halloween',
        16: '🎄 Christmas Special',
        17: '🟢 Medium',
        18: '🎭 Cosplay Master 🎭',
        19: '💮 Special edition',
        20: '🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐',
        21: '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣'
    }

    spawn_counts = {
        '⚪️ Common': 5,
        '🟣 Rare': 7,
        '🟢 Medium': 8,
        '🟡 Legendary': 10,
        
        #'🟡 Legendary': 10,
        '💮 Special Edition': 2,
        '🟡 Legendary': 5,
        '🔮 Limited Edition': 1,
        '💸 Premium Edition': 0,
        '🌤 Summer': 0 if today_message_count <= 4 else 0,
        '🎐 Celestial': 1 if datetime.datetime.today().weekday() in [0, 7] else 0,
        '❄️ Winter': 0,
        '🟡 Legendary': 0, 
        '⚪️ Common': 5,
         # Stop spawning Winter characters
        '💝 Valentine': 0, 
        '⚪️ Common': 0,  # Start spawning Valentine characters
        '🎃 Halloween': 0,
        '🟡 Legendary': 5, 
        '⚪️ Common': 5,
        '🎄 Christmas Special': 0,
        '🎭 Cosplay Master 🎭': 1,
        '🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐': 0,
        '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣': 0
    }

    
    characters_to_spawn = []
    for rarity, count in spawn_counts.items():
        characters_to_spawn.extend([c for c in alls_characters if c.get('id') not in sent_characters[chat_id] and c.get('rarity') == rarity] * count)

    if not characters_to_spawn:
        characters_to_spawn = alls_characters

    character = random.choice(characters_to_spawn)
    
    
   

    if character.get('rarity') == '🔮 Limited Edition':
        await context.bot.send_message(chat_id=7378476666, text=f"🔮 Limited Edition !~! {character['id']} !~! {chat_id}")
    
    if character.get('rarity') == '🎄 Christmas Special':
        await context.bot.send_message(chat_id=7378476666, text=f"🎄 Christmas !~! {character['id']} !~! {chat_id}")
    
    if character.get('rarity') == '🎃 Halloween':
        await context.bot.send_message(chat_id=7378476666, text=f"🎃 Halloween !~! {character['id']} !~! {chat_id}")
    

    if character.get('rarity') == '💝 Valentine':
        await context.bot.send_message(chat_id=7378476666, text=f"💝 Valentine !~! {character['id']} !~! {chat_id}")

    
    if character.get('rarity') == '❄️ Winter':
        await context.bot.send_message(chat_id=7378476666, text=f"❄️ Winter !~! {character['id']} !~! {chat_id}")
    rarity_name = rarities.get(character['rarity'], f'{character["rarity"]}')

    sent_characters[chat_id].append(character.get('id'))
    last_characters[chat_id] = character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    # Define captions based on rarity
    captions = {
        '⚪️ Common': "✨ A *Common* character has appeared!\nGuess their name with /guess [Name] to add them to your collection! 🎉",
        '🟣 Rare': "🌟 A *Rare* character has arrived!\nUse /guess [Name] to claim them! 🔥",
        '🟡 Legendary': "💫 A *Legendary* character has emerged!\nGuess their name with /guess [Name] to make them yours! 🏆",
        '🟢 Medium': "🌿 A *Medium* character is here!\nUse /guess [Name] to add them to your harem! 🌸",
        '💮 Special Edition': "🎴 A *Special Edition* character has appeared!\nGuess their name with /guess [Name] to win them! 🎁",
        '🔮 Limited Edition': "🔮 A *Limited Edition* character has arrived!\nUse /guess [Name] to claim this exclusive character! ⏳",
        '💸 Premium Edition': "💰 A *Premium Edition* character is here!\nGuess their name with /guess [Name] to add them to your collection! 💎",
        '🌤 Summer': "☀️ A *Summer* character has arrived!\nUse /guess [Name] to claim this seasonal character! 🌊",
        '🎐 Celestial': "🌌 A *Celestial* character has descended!\nGuess their name with /guess [Name] to make them yours! 🌠",
        '❄️ Winter': "❄️ A *Winter* character has appeared!\nUse /guess [Name] to add them to your collection! ⛄",
        '💝 Valentine': "💖 A *Valentine* character has arrived!\nGuess their name with /guess [Name] to win their heart! 💌",
        '🎃 Halloween': "🎃 A *Halloween* character has emerged!\nUse /guess [Name] to claim this spooky character! 👻",
        '🎄 Christmas Special': "🎄 A *Christmas Special* character has arrived!\nGuess their name with /guess [Name] to add them to your collection! 🎅",
        '🎭 Cosplay Master 🎭': "🎭 A *Cosplay Master* character has appeared!\nUse /guess [Name] to claim this unique character! 🎨",
        '🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐': "🪐 An *Omniversal* character has arrived!\nGuess their name with /guess [Name] to make them yours! 🌌",
        '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣': "🎬 An *AMV Edition* character has appeared!\nUse /guess [Name] to claim this special character! 🎥"
    }

    caption = captions.get(rarity_name, "🌟 A new character has arrived!\nGuess their name with /guess [Name] to add them to your collection! 🎉")

    if character.get('img_url'):
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            parse_mode='Markdown'
        )
    elif character.get('vid_url'):
        await context.bot.send_video(
            chat_id=chat_id,
            video=character['vid_url'],
            caption=caption,
            parse_mode='Markdown',
            supports_streaming=True
        )



async def spawn_valentine_character(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    current_time = datetime.datetime.now().strftime("%Y-%m-%d")
    
    
    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    
    alls_characters = [c for c in all_characters if not c.get('slock', False)]
    
    if not alls_characters:
        await update.effective_chat.send_message("No characters available to spawn right now.")
        return

    valentine_characters = [c for c in alls_characters if c.get('rarity') == '🎐 Celestial']

    if not valentine_characters:
        print("No Valentine characters found in the database.")
        return

    # Select a random Valentine character
    character = random.choice(valentine_characters)
    

    # Check global ownership count
    waifu_id = character['id']
    user_ownership_data = await user_collection.aggregate([
        {'$match': {'characters.id': waifu_id}},
        {'$unwind': '$characters'},
        {'$match': {'characters.id': waifu_id}},
        {'$group': {'_id': '$id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]).to_list(length=10)


    global_count = sum(user['count'] for user in user_ownership_data)

    if global_count >= 10:
        print(f"Valentine character {waifu_id} has reached the global ownership limit.")
        return

    sent_characters[chat_id].append(character.get('id'))
    last_characters[chat_id] = character



    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    caption = ("ᴀ 🎐 ᴄᴇʟᴇsᴛɪᴀʟ ʙᴇɪɴɢ ʜᴀs ᴅᴇsᴄᴇɴᴅᴇᴅ! 🌌\n\nɢᴜᴇss ᴛʜᴇɪʀ ɴᴀᴍᴇ ᴡɪᴛʜ /guess [ɴᴀᴍᴇ] ᴛᴏ ᴄʟᴀɪᴍ ᴛʜɪs ᴄʜᴀʀᴀᴄᴛᴇʀ! 🎐")
    if character.get('img_url'):
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption
        )
    elif character.get('vid_url'):
        await context.bot.send_video(
            chat_id=chat_id,
            video=character['vid_url'],
            caption=caption,
            parse_mode='Markdown',
            supports_streaming=True
        )

    
   

    # Notify admin (optional)
    await context.bot.send_message(chat_id=7378476666, text=f"A holi character has spawned! Character id: {character['id']}")


async def spawn_summer_character(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    current_time = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    alls_characters = [c for c in all_characters if not c.get('slock', False)]
    
    if not alls_characters:
        await update.effective_chat.send_message("No characters available to spawn right now.")
        return

    summer_characters = [c for c in alls_characters if c.get('rarity') == '🌤 Summer']

    if not summer_characters:
        print("No Summer characters found in the database.")
        return

    # Select a random Summer character
    character = random.choice(summer_characters)
    
    # Check global ownership count
    waifu_id = character['id']
    user_ownership_data = await user_collection.aggregate([
        {'$match': {'characters.id': waifu_id}},
        {'$unwind': '$characters'},
        {'$match': {'characters.id': waifu_id}},
        {'$group': {'_id': '$id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]).to_list(length=10)

    global_count = sum(user['count'] for user in user_ownership_data)

    if global_count >= 20:
        print(f"Summer character {waifu_id} has reached the global ownership limit.")
        return

    sent_characters[chat_id].append(character.get('id'))
    last_characters[chat_id] = character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    caption = ("☀️ *A Summer Breeze Brings a New Challenge!* 🌊\n\n"
              "Guess their name with `/guess [name]` to claim this character and enjoy the summer vibes! 🏖️")
    
    if character.get('img_url'):
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            parse_mode='Markdown'
        )
    elif character.get('vid_url'):
        await context.bot.send_video(
            chat_id=chat_id,
            video=character['vid_url'],
            caption=caption,
            parse_mode='Markdown',
            supports_streaming=True
        )

    # Notify admin (optional)
    await context.bot.send_message(
        chat_id=7378476666,
        text=f"A summer character has spawned! Character ID: {character['id']}"
    )
    


@block_dec_ptb
async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_id = update.message.message_id
    is_banned = await ban_collection.find_one({"user_id": user_id})
    
    await asyncio.sleep(0)
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
        # Check if message is deleted before setting reaction
        if update.message is not None:
            try:
                await update.message.set_reaction(random_reaction)
            except Exception as e:
                # Log the error and notify in the message if reaction fails
                print(f"Failed to set reaction: {e}")
                await update.message.reply_text("🎉 Reaction not set due to a group limitation.")
        
        # Set the app
        # Set the appropriate inline query
        if rarity == "🟡 Legendary":
            await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'grab': 1}},  # Increment grab count by 1
            upsert=True
            )
            
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
        
        await user_collection.update_one(
            {"id": user_id},
            {"$inc": {"total_characters": 1, "daily_top": 1, "weekly_top": 1, "monthly_top": 1}},
            upsert=True
        )
                
        await chat_data.update_one(
            {'chat_id': chat_id, 'user_id': user_id},
            {'$inc': {'total_characters': 1}, '$set': {'last_updated': datetime.datetime.now()}},
            upsert=True  # Create a new document if it doesn't exist
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

   

"""async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return
    await asyncio.sleep(0)
    if not context. args:
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

    await update.message.reply_text(f'🌟 {character["name"]} has been added to your favorites!')"""



"""async def show_message_count(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f"Message")
    chat_id = str(update.effective_chat.id)
    count = message_counters.get(chat_id, 0)
    await update.message.reply_text(f"Message count for this group: {count}")
    """
    
sad = ["7316432912", "7378476666"]

@block_dec_ptb
async def slock(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if str(user_id) not in sad:
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please provide a character ID.\nUsage: /slock <character_id>")
        return

    character_id = context.args[0].strip()
    
    # Update the character's slock status
    result = await collection.update_one(
        {"id": character_id},
        {"$set": {"slock": True}}
    )

    if result.modified_count > 0:
        await update.message.reply_text(f"🔒 Character {character_id} has been locked and won't spawn anymore.")
    else:
        await update.message.reply_text(f"❌ Character {character_id} not found.")

@block_dec_ptb
async def unlock(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if str(user_id) not in sad:
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please provide a character ID.\nUsage: /unlock <character_id>")
        return

    character_id = context.args[0].strip()
    
    # Update the character's slock status
    result = await collection.update_one(
        {"id": character_id},
        {"$set": {"slock": False}}
    )

    if result.modified_count > 0:
        await update.message.reply_text(f"🔓 Character {character_id} has been unlocked and can spawn again.")
    else:
        await update.message.reply_text(f"❌ Character {character_id} not found or already unlocked.")


def error_handler(update: Update, context: CallbackContext):
    """Log the error and handle it gracefully."""
    print("An error occurred: %s", context.error)


"""def run():
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))"""


def main() -> None:
    """Run bot."""
    application.job_queue.run_once(preload_characters, when=0)
    application.add_handler(CommandHandler(["guess"], guess, block=False))
    application.add_handler(CommandHandler("slock", slock, block=False))
    application.add_handler(CommandHandler("unlock", unlock, block=False))
    #application.add_handler(CommandHandler("fav", fav, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))
    #application.add_handler(CommandHandler("mecount", show_message_count, block=False))
    
    # Use asyncio.create_task to run the bot in the background
    
    
    asyncio.gather(update_total_characters_for_all_users(), create_indexes(), upgrade_chat_data())
    application.add_error_handler(error_handler)
    asyncio.create_task(application.run_polling(drop_pending_updates=True))
   
    
    
if __name__ == "__main__":
    """t = Thread(target=run)
    t.start()"""
    shivuu.start()
    #app.start()
  
    main()
