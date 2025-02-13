import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import random
import re
from datetime import datetime
from pytz import timezone
from . import user_collection, app, nopvt
from .watchers import scrabble_watcher
from .block import block_dec, temp_block

# Predefined list of words






active_scrabbles = {}
MAX_ATTEMPTS = 3
WIN_LIMIT = 15
COOLDOWN_TIME = 50
cooldown_users = {}

# Define allowed rarities (not used in this version)
ALLOWED_RARITIES = {
    "⚪️ Common",
    "🟣 Rare",
    "🟡 Legendary",
    "🟢 Medium",
    "💮 Special Edition"
}

LIMITED_EDITION_RARITY = "🔮 Limited Edition"

# Probability of getting a Limited Edition character (e.g., 5% chance)
LIMITED_EDITION_CHANCE = 0.05

def is_new_day(last_win_time):
    ist = timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    last_win_ist = last_win_time.astimezone(ist)
    return now_ist.date() != last_win_ist.date()

def get_random_word():
    # Select a random word from the predefined list
    return random.choice(WORDS_LIST)

def scramble_word(word):
    if len(word) <= 5:
        return word
    word_list = list(word)
    random.shuffle(word_list)
    return ''.join(word_list)

def scramble_phrase(phrase):
    words = phrase.split()
    scrambled_words = [scramble_word(word) for word in words]
    return ' '.join(scrambled_words)

def provide_hint(phrase, attempts):
    words = phrase.split()
    if attempts == 1:
        return f"🔍 Hint: {' '.join([word[:2] + '_' * (len(word) - 2) for word in words])}"
    elif attempts == 2:
        return f"🔍 Hint: {' '.join([word[:2] + '_' * (len(word) - 3) + word[-1] for word in words])}"
    else:
        return f"🔍 Hint: {' '.join([word[:2] + '_' * (len(word) - 3) + word[-1] for word in words])}"

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

    phrase = get_random_word()
    scrambled_phrase = scramble_phrase(phrase)

    active_scrabbles[user_id] = {
        'phrase': phrase,
        'scrambled_phrase': scrambled_phrase,
        'start_time': datetime.now(),
        'attempts': 0
    }

    await message.reply_text(
        f"🎲 **Welcome to Word Resembled Game!** 🎲\n\n"
        f"🔠 Unshuffle this phrase:\n\n"
        f"✨ `{scrambled_phrase}` ✨\n\n"
        f"⏳ You have *{MAX_ATTEMPTS} attempts* to guess the phrase.\n"
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
        user_data = {'id': user_id, 'wins': 0, 'last_win_time': datetime.min, 'limited_edition_awarded': False}
    else:
        if 'wins' not in user_data:
            user_data['wins'] = 0
        if 'limited_edition_awarded' not in user_data:
            user_data['limited_edition_awarded'] = False

    if answer.lower() == scrabble_data['phrase'].lower():
        now = datetime.now()

        user_data['wins'] += 1
        user_data['last_win_time'] = now

        # Check if the user gets a Limited Edition character (random chance)
        if not user_data['limited_edition_awarded'] and random.random() < LIMITED_EDITION_CHANCE:
            await message.reply_text(
                f"🎉 *You won!* 🎉\n\n"
                f"🏆 You've unlocked a **🔮 Limited Edition** reward!\n\n"
                f"💰 You've also won 100 coins!"
            )
            await user_collection.update_one({'id': user_id}, {'$inc': {'coins': 100}})
            user_data['limited_edition_awarded'] = True

        # Award regular reward on every 10th win
        elif user_data['wins'] % 10 == 0:
            await message.reply_text(
                f"🎉 *You won!* 🎉\n\n"
                f"🏆 You've reached a milestone! Here's 50 coins!\n\n"
                f"💰 Total Wins: {user_data['wins']}"
            )
            await user_collection.update_one({'id': user_id}, {'$inc': {'coins': 50}})
    
        else:
            gold = random.randint(20, 60)
            await message.reply_text(
                f"🎉 *You won!* 🎉\n\n"
                f"💰 You've won {gold} coins!\n\n"
                f"🏆 Total Wins: {user_data['wins']}"
            )
            await user_collection.update_one({'id': user_id}, {'$inc': {'coins': gold}})

        del active_scrabbles[user_id]

        cooldown_users[user_id] = datetime.now()
        asyncio.create_task(remove_cooldown(user_id))

    elif scrabble_data['attempts'] >= MAX_ATTEMPTS:
        await message.reply_text(
            f"❌ *Out of attempts!* ❌\n\n"
            f"🔠 The correct phrase was: `{scrabble_data['phrase']}`"
        )
        del active_scrabbles[user_id]
    else:
        hint = provide_hint(scrabble_data['phrase'], scrabble_data['attempts'])
        await message.reply_text(
            f"❌ *Incorrect!* ❌\n\n"
            f"🔠 Scrambled Phrase: `{scrabble_data['scrambled_phrase']}`\n\n"
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
