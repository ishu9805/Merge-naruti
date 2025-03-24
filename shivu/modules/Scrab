import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import random
from datetime import datetime
from pytz import timezone
from . import nopvt
from .watchers import scrabble_watcher
from .block import block_dec, temp_block

from datetime import datetime

from . import sudo_filter
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
from pyrogram import Client, filters
from pyrogram.types import Message
import random
from datetime import datetime
from pytz import timezone
from . import nopvt
from .watchers import scrabble_watcher
from .block import block_dec, temp_block
from . import sudo_filter

# Game constants
MAX_ATTEMPTS = 3
WIN_LIMIT = 15
COOLDOWN_TIME = 50  # Normal cooldown after winning
XSCRAMBLE_COOLDOWN = 30  # Cooldown after canceling game
LIMITED_EDITION_CHANCE = 0.01

# Game state trackers
active_scrabbles = {}
cooldown_users = {}  # Tracks both win cooldowns and cancel cooldowns

# Rarity definitions
ALLOWED_RARITIES = {
    "⚪️ Common",
    "🟣 Rare",
    "🟡 Legendary",
    "🟢 Medium"
}
LIMITED_EDITION_RARITY = "🔮 Limited Edition"

async def get_limited_edition_character():
    try:
        limited_characters = await collection.find({'rarity': LIMITED_EDITION_RARITY}).to_list(length=None)
        if not limited_characters:
            raise ValueError("No Limited Edition characters found")
        return random.choice(limited_characters)
    except Exception as e:
        print(f"Error getting limited edition character: {e}")
        return await get_random_character()

async def get_random_character():
    pipeline = [
        {'$match': {
            'id': {'$gte': '01', '$lte': '4100'},
            'rarity': {'$in': list(ALLOWED_RARITIES)},
            '$expr': {'$gt': [{'$strLenCP': {'$arrayElemAt': [{'$split': ['$name', ' ']}, 0]}}, 5]}
        }},
        {'$sample': {'size': 1}}
    ]
    character = await collection.aggregate(pipeline).next()
    return character

def scramble_word(word):
    if len(word) <= 5:
        return word
    word_list = list(word)
    random.shuffle(word_list)
    return ''.join(word_list)

def provide_hint(word, attempts):
    if attempts == 1:
        return f"🔍 Hint: {word[:2]}{'_' * (len(word) - 2)}"
    elif attempts == 2:
        return f"🔍 Hint: {word[:2]}{'_' * (len(word) - 3)}{word[-1]}"
    else:
        return f"🔍 Hint: {word[:2]}{'_' * (len(word) - 4)}{word[-2:]}"

@app.on_message(filters.command("scramble"))
@block_dec
async def scrabble(client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return

    # Check for any cooldown (either from winning or canceling)
    if user_id in cooldown_users:
        remaining = int((cooldown_users[user_id] - datetime.now()).total_seconds())
        if remaining > 0:
            await message.reply_text(
                f"⏳ Please wait {remaining} seconds before starting a new game."
            )
            return

    if user_id in active_scrabbles:
        await message.reply_text(
            "🚨 You already have an active game!\n"
            "Finish it or use /xscramble to cancel."
        )
        return

    character = await get_random_character()
    first_word = character['name'].split()[0]
    scrambled_word = scramble_word(first_word)

    active_scrabbles[user_id] = {
        'character': character,
        'word': first_word,
        'scrambled_word': scrambled_word,
        'start_time': datetime.now(),
        'attempts': 0
    }

    await message.reply_text(
        f"🎲 **Word Scramble Game** 🎲\n\n"
        f"🔠 Unscramble this word:\n\n"
        f"✨ `{scrambled_word}` ✨\n\n"
        f"⏳ You have {MAX_ATTEMPTS} attempts\n"
        f"❌ Cancel with /xscramble"
    )

@app.on_message(filters.command("xscramble"))
@block_dec
async def cancel_scramble(client, message: Message):
    user_id = message.from_user.id

    if user_id not in active_scrabbles:
        await message.reply_text(
            "⚠️ You don't have an active game!\n"
            "Start one with /scramble"
        )
        return

    # Remove game and set cooldown
    del active_scrabbles[user_id]
    cooldown_users[user_id] = datetime.now() + timedelta(seconds=XSCRAMBLE_COOLDOWN)
    asyncio.create_task(remove_cooldown(user_id))

    await message.reply_text(
        f"🛑 Game cancelled!\n\n"
        f"⏳ You can play again in {XSCRAMBLE_COOLDOWN} seconds."
    )

@app.on_message(~filters.me, group=scrabble_watcher)
async def check_answer(client, message: Message):
    if message.from_user is None:
        return
    
    user_id = message.from_user.id
    if user_id not in active_scrabbles:
        return

    if message.sticker or message.text.startswith('/'):
        return

    answer = message.text.strip()
    game = active_scrabbles[user_id]
    game['attempts'] += 1

    user_data = await user_collection.find_one({'id': user_id}) or {
        'id': user_id,
        'wins': 0,
        'last_win_time': datetime.min,
        'has_limited': False
    }

    if answer.lower() == game['word'].lower():
        # Win handling (same as before)
        del active_scrabbles[user_id]
        cooldown_users[user_id] = datetime.now() + timedelta(seconds=COOLDOWN_TIME)
        asyncio.create_task(remove_cooldown(user_id))
        
        # Rest of your win logic here...
        
    elif game['attempts'] >= MAX_ATTEMPTS:
        # Loss handling
        await message.reply_text(
            f"❌ Game over! The word was: `{game['word']}`"
        )
        del active_scrabbles[user_id]
    else:
        # Hint for wrong answer
        hint = provide_hint(game['word'], game['attempts'])
        await message.reply_text(
            f"❌ Wrong! {hint}\n"
            f"Attempts left: {MAX_ATTEMPTS - game['attempts']}"
        )

async def remove_cooldown(user_id):
    await asyncio.sleep(max(
        COOLDOWN_TIME,
        XSCRAMBLE_COOLDOWN
    ))
    if user_id in cooldown_users:
        del cooldown_users[user_id]

@app.on_message(filters.command("rstw") & sudo_filter)
async def reset_wins(client, message: Message):
    await user_collection.update_many(
        {},
        {'$set': {'wins': 0, 'last_win_time': datetime.min, 'has_limited': False}}
    )
    await message.reply_text("✅ All user win counts and limited status reset!")
