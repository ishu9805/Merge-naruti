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
from shivu.modules.lock import ptbcommand_lock as ptbcmd



all_characters = []
valentine_spawn_thresholds = {} 
amv_spawn_thresholds = {} # Store random thresholds for Valentine spawn
summer_spawn_thresholds = {}
reaction_list = [ReactionEmoji.THUMBS_UP, ReactionEmoji.EYES, ReactionEmoji.CLAPPING_HANDS, ReactionEmoji.BOTTLE_WITH_POPPING_CORK, ReactionEmoji.DOVE_OF_PEACE, ReactionEmoji.GRINNING_FACE_WITH_STAR_EYES, ReactionEmoji.HEART_ON_FIRE, ReactionEmoji.PARTY_POPPER]
current_amv_character = {}  # Tracks AMV characters per chat
amv_claim_limit = 1  #

AMV_GROUP_ID = -1002783891820 # Your main group ID
 # Spawn every 100 messages
MAX_AMV_OWNERS = 10  # Global ownership limit
amv_spawn_counter = 0  # Track message count for AMV spawns
amv_characters = []  # Stores preloaded AMV characters
# Add this near your other global variables
sent_message_info = {}  # {chat_id: {'character_id': str, 'message_count': int}}
spawned_characters = {}  # {chat_id: {character: dict, message_id: int, task: asyncio.Task}}
countdown_tasks = {}  

"""server = Flask(__name__)
@server.route("/")
def home():
    return "Bot is running"
"""
    

async def preload_characters(context: CallbackContext) -> None:
    global all_characters, amv_characters
    try:
        # Fetch characters with IDs between 1 and 4500
        all_characters = await collection.find({'id': {'$gte': '01', '$lte': '8000'}}).to_list(length=None)
        amv_characters = await collection.find({"vid_url": {"$exists": True}}).to_list(length=None)
        
        if all_characters:
            print(f"Preloaded {len(all_characters)} characters {len(amv_characters)}with IDs from 1 to 4500.")
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
total_message_counts2 ={}
amv_message_count = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)

last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


# Add these global variables near your other globals
spawn_cooldowns = {}  # {chat_id: timestamp}
SPAWN_COOLDOWN = 30  # seconds between spawns

async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    
    if temp_block(user_id):
        return

    # Check spawn cooldown
    current_time = time.time()
    if chat_id in spawn_cooldowns:
        if current_time - spawn_cooldowns[chat_id] < SPAWN_COOLDOWN:
            return  # Still in cooldown period

    # Initialize lock for this chat if it doesn't exist
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        # Check cooldown again inside lock to prevent race condition
        if chat_id in spawn_cooldowns:
            if current_time - spawn_cooldowns[chat_id] < SPAWN_COOLDOWN:
                return

        # Initialize counters if they don't exist
        if chat_id not in total_message_counts:
            total_message_counts[chat_id] = 0
            valentine_spawn_thresholds[chat_id] = random.randint(1000, 3000)
            summer_spawn_thresholds[chat_id] = random.randint(500, 2000)
            
            # Special AMV counter for the designated group
            if chat_id == "-1002783891820":  # AMV_GROUP_ID as string
                amv_message_count[chat_id] = 0
                amv_spawn_thresholds[chat_id] = random.randint(900, 2000)

        # Increment main counter
        total_message_counts[chat_id] += 1

        # Handle AMV group separately
        if chat_id == "-1002783891820":
            amv_message_count[chat_id] += 1
            if amv_message_count[chat_id] >= amv_spawn_thresholds[chat_id]:
                await spawn_amv_character(update, context)
                amv_message_count[chat_id] = 0
                amv_spawn_thresholds[chat_id] = random.randint(1000, 2500)
                spawn_cooldowns[chat_id] = current_time  # Set cooldown after AMV spawn
                return  # Prevent regular spawn after AMV

        # Check for user spam prevention
        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 6:
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                warned_users[user_id] = time.time()
                return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        # Initialize and increment regular message counter
        if chat_id not in message_counts:
            message_counts[chat_id] = 0
        message_counts[chat_id] += 1

        # Get message frequency from database
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        message_frequency = chat_frequency.get('message_frequency', 100) if chat_frequency else 100

        # Spawn regular character
        if message_counts[chat_id] >= message_frequency:
            await send_image(update, context)
            message_counts[chat_id] = 0
            spawn_cooldowns[chat_id] = current_time  # Set cooldown after regular spawn
            return  # Exit after spawning to prevent multiple spawns

        # Check for special spawns using relative threshold approach
        current_count = total_message_counts[chat_id]
        valentine_threshold = valentine_spawn_thresholds[chat_id]
        summer_threshold = summer_spawn_thresholds[chat_id]
        
        # Valentine spawn check
        if current_count >= valentine_threshold:
            await spawn_valentine_character(update, context)
            # Set next threshold relative to current count
            valentine_spawn_thresholds[chat_id] = current_count + random.randint(1200, 2500)
            spawn_cooldowns[chat_id] = current_time  # Set cooldown
            return  # Exit after special spawn
            
        # Summer spawn check (elif to prevent both spawning at once if thresholds overlap)
        elif current_count >= summer_threshold:
            await spawn_monsoon_character(update, context)
            # Set next threshold relative to current count
            summer_spawn_thresholds[chat_id] = current_count + random.randint(700, 1500)
            spawn_cooldowns[chat_id] = current_time  # Set cooldown
            return  # Exit after special spawn



async def spawn_diwali_character(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    current_time = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    # Filter for Diwali characters - Event rarity and name contains 🪔
    diwali_characters = [c for c in all_characters if c.get('rarity') == '🧧 𝙀𝙫𝙚𝙣𝙩𝙨' and '🪔' in c.get('name', '')]

    if not diwali_characters:
        print("No Diwali characters found in the database.")
        return

    # Select a random Diwali character
    character = random.choice(diwali_characters)
    
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

    if global_count >= 7:  # Limit for Diwali characters
        print(f"Diwali character {waifu_id} has been claimed by too many collectors.")
        return

    sent_characters[chat_id].append(character.get('id'))
    last_characters[chat_id] = character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    caption = (
        "🎆 *A Diwali Celebration Appears!* 🪔\n\n"
        "Lights are shining... can you **guess their name**?\n"
        "/guess [name] to claim this festive character! ✨\n\n"
    )
    
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

    # Special Diwali effect for admin notification
    await context.bot.send_message(
        chat_id="6902029663",
        text=(
            f"🎆 Diwali Alert! 🎆\n"
            f"Character ID: {character['id']} has appeared in chat {chat_id}\n"
            f"Only {7 - global_count} remaining claims available worldwide!"
        )
    )
    

async def spawn_amv_character(update: Update, context: CallbackContext):
    """Spawn a limited edition AMV character"""
    try:
        chat_id = update.effective_chat.id
        current_time = datetime.datetime.now().strftime("%Y-%m-%d")
        # Filter characters with available slots

        if chat_id not in sent_characters:
            sent_characters[chat_id] = []

        available_amvs = []
        for char in amv_characters:
            owners = await user_collection.count_documents(
                {"characters.id": char['id']}
            )
            if owners < MAX_AMV_OWNERS:
                available_amvs.append(char)
        
        if not available_amvs:
            await context.bot.send_message(chat_id=-1002783891820, text="hmm")
            return

        character = random.choice(available_amvs)

            
        sent_characters[chat_id].append(character.get('id'))
        last_characters[chat_id] = character

        if chat_id in first_correct_guesses:
            del first_correct_guesses[AMV_GROUP_ID]
 
        if chat_id in first_correct_guesses:
            del first_correct_guesses[chat_id]

        await context.bot.send_message(chat_id=-1002783891820, text="🎗️")
        await asyncio.sleep(2)
        # Store AMV character info

        msg = await context.bot.send_video(
            chat_id= chat_id,
            video=character['vid_url'],
            parse_mode='Markdown',
            supports_streaming=True,
            caption="🎬 **AMV CHARACTER APPEARED!** 🎬\n\n"
                    "💎 *Rarity:* AMV Edition (Ultra Rare)\n\n"
                    "✍️ Guess the character name with /guess [name] to claim it!"
        )
        
      
        
    except Exception as e:
        print(f"Error spawning AMV: {e}")




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
        await context.bot.send_message(chat_id=6902029663, text=f"🔮 Limited Edition !~! {character['id']} !~! {chat_id}")
    
    if character.get('rarity') == '🎄 Christmas Special':
        await context.bot.send_message(chat_id=6902029663, text=f"🎄 Christmas !~! {character['id']} !~! {chat_id}")
    
    if character.get('rarity') == '🎃 Halloween':
        await context.bot.send_message(chat_id=6902029663, text=f"🎃 Halloween !~! {character['id']} !~! {chat_id}")
    

    if character.get('rarity') == '💝 Valentine':
        await context.bot.send_message(chat_id=6902029663, text=f"💝 Valentine !~! {character['id']} !~! {chat_id}")

    
    if character.get('rarity') == '❄️ Winter':
        await context.bot.send_message(chat_id=6902029663, text=f"❄️ Winter !~! {character['id']} !~! {chat_id}")
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
    await context.bot.send_message(chat_id=6902029663, text=f"A celestial character chat :- {chat_id} Character id: {character['id']}")


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
    

    
sad = ["7801911051", "6902029663"]

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


async def now_command(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if str(user_id) not in sad:
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: /spawn {char|amv|}")
        return
    
    game_type = context.args[0].lower()
    
    if game_type == 'char':
        await send_image(update, context)
    elif game_type == 'amv':
        await spawn_amv_character(update, context)
    elif game_type == 'summer':
        await spawn_summer_character(update, context)
    elif game_type == 'celestial':
        await spawn_valentine_character(update, context)
    elif game_type == 'monsoon':
        await spawn_monsoon_character(update, context)
        

@block_dec_ptb
@ptbcmd
async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    first = update.effective_user.first_name
    username = update.effective_user.username
    title = update.effective_chat.title
    is_banned = await ban_collection.find_one({"user_id": user_id})
    
    if is_banned:
        return

    if temp_block(user_id):
        return

    # Check if there's an active character to guess
    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        return

    # Get the current character
    character = last_characters[chat_id]
    guess = ' '.join(context.args).lower() if context.args else ''
    
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text("Nahh You Can't use This Types of words in your guess..❌️")
        return

    name_parts = character['name'].lower().split()

    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):
        # Check ownership limit for AMV characters if this is an AMV
        if character.get("vid_url"):
            owners_count = await user_collection.count_documents({"characters.id": character['id']})
            if owners_count >= MAX_AMV_OWNERS:
                await update.message.reply_text("❌ This AMV character has reached the maximum number of owners!")
                return

        first_correct_guesses[chat_id] = user_id
        rarity = character.get("rarity", "")
        
        try:
            random_reaction = random.choice(reaction_list)
            await update.message.set_reaction(random_reaction)
        except Exception as e:
            print(f"Couldn't set reaction: {e}")

        # Prepare response based on character type
        if character.get("vid_url"):
            response_text = (
                f'<b><a href="tg://user?id={user_id}">{escape(first)}</a></b> 🎊 You guessed the AMV character!\n\n'
                f'🎬 Name: <b>{character["name"]}</b>\n'
                f'📀 Anime: <b>{character["anime"]}</b>\n'
                f'💎 Rarity: <b>🎗️ AMV Edition (Ultra Rare)</b>\n\n'
                f'This exclusive character is now in your collection!'
            )
        else:
            response_text = (
                f'<b><a href="tg://user?id={user_id}">{escape(first)}</a></b> 🎊 You guessed the character!\n\n'
                f'🍁 Name: <b>{character["name"]}</b>\n'
                f'⛩ Anime: <b>{character["anime"]}</b>\n'
                f'🎐 Rarity: <b>{character["rarity"]}</b>\n\n'
                f'This character is now in your harem!'
            )
            
        keyboard = None
        if character.get("img_url"):
            inline_query = f"collection.img.{user_id}"
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "View Collection",
                    switch_inline_query_current_chat=inline_query
                )
            ]])
        elif character.get("vid_url"):
            inline_query = f"collection.vid.{user_id}"
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "View AMV",
                    switch_inline_query_current_chat=inline_query
                )
            ]])

        await update.message.reply_text(
            response_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )

        if character.get('rarity') == "🟡 Legendary":
            await user_collection.update_one(
                {'id': user_id},
                {'$inc': {'grab': 1}},
                upsert=True
            )
        # Update user collection
        await update_user_collection(user_id, character, chat_id, username, first, title)
        
    else:
        await update.message.reply_text('❌ Oops! Wrong character name. Try again!')



async def update_user_collection(user_id: int, character: dict, chat_id: int, username, first, title):
    """Helper function to update user collection"""
    # Update user's collection
    await user_collection.update_one(
        {"id": user_id},
        {
            "$push": {"characters": character},
            "$inc": {
                "total_characters": 1,
                "daily_top": 1,
                "weekly_top": 1,
                "monthly_top": 1
            },
            "$set": {
                "username": username,
                "first_name": first
            }
        },
        upsert=True
    )
    
    # Update group user totals
    await group_user_totals_collection.update_one(
        {"user_id": user_id, "group_id": chat_id},
        {
            "$inc": {"count": 1},
            "$set": {
                "username": username,
                "first_name": first
            }
        },
        upsert=True
    )
    
    # Update global group stats
    await top_global_groups_collection.update_one(
        {"group_id": chat_id},
        {
            "$inc": {"count": 1},
            "$set": {"group_name": title}
        },
        upsert=True
    )


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


@block_dec_ptb
async def check_counters(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    if str(user_id) not in sad:
        return

    if chat_id in total_message_counts:
        msg = (f"📊 Counters for {chat_id}:\n"
               f"• Total messages: {total_message_counts[chat_id]}\n"
               f"• Next celestial: {valentine_spawn_thresholds[chat_id] - total_message_counts[chat_id]}\n"
               f"• Next Summer: {summer_spawn_thresholds[chat_id] - total_message_counts[chat_id]}")
        if chat_id == str(AMV_GROUP_ID):
            msg += f"\n• AMV messages: {amv_message_count[chat_id]}/{amv_spawn_thresholds[chat_id]}"
        await update.message.reply_text(msg)


def error_handler(update: Update, context: CallbackContext):
    """Log the error and handle it gracefully."""
    print("An error occurred: %s", context.error)


"""def run():
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))"""


def main() -> None:
    """Run bot."""
    application.job_queue.run_once(preload_characters, when=0)
    application.add_handler(CommandHandler(["guess"], guess, block=False))
    application.add_handler(CommandHandler(["cqmsg"], check_counters))
    application.add_handler(CommandHandler(["spawn"], now_command))
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
