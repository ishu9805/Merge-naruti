import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import random
from datetime import datetime
from pytz import timezone
from . import collection, user_collection, app, nopvt
from .watchers import scrabble_watcher
from .block import block_dec, temp_block

from datetime import datetime

from . import user_collection, sudo_filter

@app.on_message(filters.command("rstw") & sudo_filter)
def reset_all_win_counts_command(client: Client, message: Message):
    try:
        user_collection.update_many({}, {'$set': {'wins': 0, 'last_win_time': datetime.min}})
        message.reply_text("Win counts have been reset for all users.")
    except Exception as e:
        message.reply_text(f"An error occurred while resetting win counts: {e}")


active_scrabbles = {}
MAX_ATTEMPTS = 3
WIN_LIMIT = 15
COOLDOWN_TIME = 50
cooldown_users = {}

# Define allowed rarities
ALLOWED_RARITIES = {
    "⚪️ Common",
    "🟣 Rare",
    "🟡 Legendary",
    "🟢 Medium"
}

LIMITED_EDITION_RARITY = "🔮 Limited Edition"

# Probability of getting a Limited Edition character (e.g., 5% chance)
LIMITED_EDITION_CHANCE = 0.01

async def get_limited_edition_character():
    try:
        # Fetch all Limited Edition characters
        limited_characters = await collection.find({'rarity': LIMITED_EDITION_RARITY}).to_list(length=None)
        
        if not limited_characters:
            raise ValueError("No Limited Edition characters found in the database.")
        
        # Return a random Limited Edition character
        return random.choice(limited_characters)
    except Exception as e:
        logger.error(f"Error fetching limited edition character: {e}")
        raise

def is_new_day(last_win_time):
    ist = timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    last_win_ist = last_win_time.astimezone(ist)
    return now_ist.date() != last_win_ist.date()

async def get_random_character():
    # Fetch characters with allowed rarities
    all_characters = await collection.find({
        'id': {'$gte': '01', '$lte': '4100'},
        'rarity': {'$in': list(ALLOWED_RARITIES)}
    }).to_list(length=None)
    
    if not all_characters:
        raise ValueError("No characters found with the allowed rarities.")
    
    while True:
        character = random.choice(all_characters)
        if len(character['name'].split()[0]) > 5:  # Ensure word length > 5
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
        return f"🔍 Hint: {word[:2]}{'_' * (len(word) - 3)}{word[-1]}"

@app.on_message(filters.command("scramble"))
@block_dec
@nopvt
async def scrabble(client, message: Message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    chat_id = message.chat.id
    
    if user_id in cooldown_users:
        remaining_time = COOLDOWN_TIME - (datetime.now() - cooldown_users[user_id]).total_seconds()
        remaining_time = max(remaining_time, 0)
        await message.reply_text(f"⏳ Please wait {int(remaining_time)} seconds before starting a new game.")
        return

    if user_id in active_scrabbles:
        await message.reply_text("🚨 You already have an active game. Finish it first! or use /xshuffle")
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
        f"🎲 **Welcome to Word Resembled Game!** 🎲\n\n"
        f"🔠 Unshuffle this word:\n\n"
        f"✨ `{scrambled_word}` ✨\n\n"
        f"⏳ You have *{MAX_ATTEMPTS} attempts* to guess the word.\n"
        f"❌ Use /xshuffle to end the game."
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
    scrabble_data = active_scrabbles[user_id]
    scrabble_data['attempts'] += 1

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        user_data = {'id': user_id, 'winss': 0, 'last_win_time': datetime.min, 'limited_edition_awarded': False}
    else:
        if 'winss' not in user_data:
            user_data['winss'] = 0
        if 'limited_edition_awarded' not in user_data:
            user_data['limited_edition_awarded'] = False

    if answer.lower() == scrabble_data['word'].lower():
        now = datetime.now()
        del active_scrabbles[user_id]
        user_data['winss'] += 1
        user_data['last_win_time'] = now
        await user_collection.update_one(
                {'id': user_id},
                {'$set': {'winss': user_data['winss'], 'last_win_time': now}},
                upsert=True
        )

        # Check if the user gets a Limited Edition character (random chance)
        if not user_data['limited_edition_awarded'] and random.random() < LIMITED_EDITION_CHANCE:
            limited_character = await get_limited_edition_character()
            await message.reply_photo(
                photo=limited_character['img_url'],
                caption=f"🎉 *You won!* 🎉\n\n"
                        f"🏆 {limited_character['name']} ({limited_character['rarity']}) has been added to your collection!"
            )
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': limited_character}})
            user_data['limited_edition_awarded'] = True

        # Award regular character on every 10th win
        elif user_data['winss'] % 10 == 0:
            character = await get_random_character()
            await message.reply_photo(
                photo=character['img_url'],
                caption=f"🎉 *You won!* 🎉\n\n"
                        f"🏆 {character['name']} ({character['rarity']}) has been added to your collection!"
            )
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': character}})
    
        else:
            gold = random.randint(20, 60)
            await message.reply_text(
                f"🎉 *You won!* 🎉\n\n"
                f"💰 You've won {gold} coins!\n\n"
                f"🏆 Total Wins: {user_data['winss']}"
            )
            await user_collection.update_one({'id': user_id}, {'$inc': {'coins': gold}})

        

        cooldown_users[user_id] = datetime.now()
        asyncio.create_task(remove_cooldown(user_id))

    elif scrabble_data['attempts'] >= MAX_ATTEMPTS:
        await message.reply_text(
            f"❌ *Out of attempts!* ❌\n\n"
            f"🔠 The correct word was: `{scrabble_data['word']}`"
        )
        del active_scrabbles[user_id]
    else:
        hint = provide_hint(scrabble_data['word'], scrabble_data['attempts'])
        await message.reply_text(
            f"❌ *Incorrect!* ❌\n\n"
            f"🔠 Scrambled Word: `{scrabble_data['scrambled_word']}`\n\n"
            f"{hint}\n\n"
            f"🔄 Try again!"
        )

async def remove_cooldown(user_id):
    await asyncio.sleep(COOLDOWN_TIME)
    if user_id in cooldown_users:
        del cooldown_users[user_id]

@app.on_message(filters.command("xshuffle"))
async def xscrabble(client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in active_scrabbles:
        del active_scrabbles[user_id]
        await message.reply_text("🛑 *Game terminated!* 🛑")
    else:
        await message.reply_text("⚠️ You don't have an active game to terminate.")
