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
WORDS_LIST = [

    # Popular Anime Characters (Main Series)
    "Naruto Uzumaki", "Sasuke Uchiha", "Sakura Haruno", "Kakashi Hatake",
    "Itachi Uchiha", "Gaara", "Shikamaru Nara", "Ino Yamanaka", "Hinata Hyuga",
    "Rock Lee", "Neji Hyuga", "Tsunade Senju", "Jiraiya", "Minato Namikaze", 
    "Madara Uchiha", "Hashirama Senju", "Obito Uchiha", "Kushina Uzumaki",
    "Pain (Nagato)", "Konan", "Deidara", "Hidan", "Zetsu", "Kabuto Yakushi", 

    "Monkey D. Luffy", "Roronoa Zoro", "Nami", "Sanji Vinsmoke", 
    "Nico Robin", "Usopp", "Franky", "Brook", "Jinbe", "Shanks", 
    "Portgas D. Ace", "Gol D. Roger", "Kaido", "Big Mom", "Trafalgar Law", 
    "Eustass Kid", "Yamato", "Boa Hancock", 

    # Bleach: Thousand-Year Blood War
    "Ichigo Kurosaki", "Rukia Kuchiki", "Renji Abarai", 
    "Byakuya Kuchiki", "Toshiro Hitsugaya", "Uryu Ishida", 
    "Yhwach", "Kenpachi Zaraki", "Shunsui Kyoraku", "Sosuke Aizen",

    # Expand more series here, adding a variety of genres and sources...

    # Honkai Star Rail
    "Trailblazer", "Kafka", "Silver Wolf", "Dan Heng", "March 7th", 
    "Himeko", "Welt", "Bronya", "Seele", "Clara", "Gepard", "Serval", 
    "Sampo", "Natasha", "Hook", "Pela", "Arlan", "Asta", "Yanqing", 
    "Bailu", "Jing Yuan", "Tingyun", "Luocha", "Sushang", "Fu Xuan", 
    "Yukong", "Blade", "Topaz", "Guinaifen", "Hanabi", "Jingliu", 

    # Games: Genshin Impact
    "Albedo", "Amber", "Barbara", "Beidou", "Bennett", "Chongyun", 
    "Diluc", "Diona", "Eula", "Fischl", "Ganyu", "Hu Tao", "Jean", 
    "Kaeya", "Kazuha", "Keqing", "Klee", "Lisa", "Mona", "Ningguang", 
    "Noelle", "Qiqi", "Razor", "Rosaria", "Sayu", "Sucrose", "Tartaglia", 
    "Venti", "Xiangling", "Xiao", "Xinyan", "Yanfei", "Yoimiya", 
    "Zhongli", "Itto", "Gorou", "Shenhe", "Yelan", "Kuki Shinobu", 
    "Tighnari", "Collei", "Dori", "Candace", "Cyno", "Alhaitham", 

    # Studio Ghibli Characters
    "Chihiro Ogino", "Haku Kohaku", "Sophie Hatter", "Howl Pendragon",
    "San (Princess Mononoke)", "Ashitaka", "Kiki (Kiki's Delivery Service)",
    "Totoro", "Mei Kusakabe", "Satsuki Kusakabe", 

    # Light Novels
    "Ainz Ooal Gown", "Shalltear Bloodfallen", "Albedo (Overlord)",
    "Kirito (SAO)", "Asuna Yuuki", "Eugeo (Sword Art Online)", 
    "Hajime Nagumo (Arifureta)", "Kaori Shirasaki", 

    # Manga / Webtoons
    "Sung Jin-Woo (Solo Leveling)", "Cha Hae-In", "Gojou Satoru", 
    "Itadori Yuji", "Fushiguro Megumi", "Ryomen Sukuna", 

    # Dota 2 / MOBA Games
    "Invoker", "Anti-Mage", "Crystal Maiden", "Riki", "Lina", 
    "Phantom Assassin", "Spectre", "Windranger", "Ember Spirit", 

    # Overwatch
    "Tracer", "Reaper", "Widowmaker", "Mercy", "D.Va", 
    "Bastion", "Hanzo", "Genji", "Lucio", "Zenyatta", 

    # Genshin Impact
    "Albedo", "Amber", "Barbara", "Beidou", "Bennett", "Chongyun", 
    "Diluc", "Diona", "Eula", "Fischl", "Ganyu", "Hu Tao", "Jean", 
    "Kaeya", "Kazuha", "Keqing", "Klee", "Lisa", "Mona", "Ningguang", 
    "Noelle", "Qiqi", "Razor", "Rosaria", "Sayu", "Sucrose", "Tartaglia", 
    "Venti", "Xiangling", "Xiao", "Xinyan", "Yanfei", "Yoimiya", 
    "Zhongli", "Itto", "Gorou", "Shenhe", "Yelan", "Kuki Shinobu", 
    "Tighnari", "Collei", "Dori", "Candace", "Cyno", "Alhaitham", 
    "Dehya", "Mika", "Kirara", "Lynette", "Lyney", "Freminet", 
    "Neuvillette", "Wriothesley", "Navia", "Clorinde", "Arlecchino",

    # Honkai Star Rail
    "Trailblazer", "Kafka", "Silver Wolf", "Dan Heng", "March 7th", 
    "Himeko", "Welt", "Bronya", "Seele", "Clara", "Gepard", "Serval", 
    "Sampo", "Natasha", "Hook", "Pela", "Arlan", "Asta", "Yanqing", 
    "Bailu", "Jing Yuan", "Tingyun", "Luocha", "Sushang", "Fu Xuan", 
    "Yukong", "Blade", "Topaz", "Guinaifen", "Hanabi", "Jingliu", 
    "Imbibitor Lunae", "Lynx", "Herta", "Qingque", "Svarog", "Cocolia", 
    "Aurora", "Gu Yuan", "Yun Yun", "Jia Nan", "Tian Lei", 

    # BTTH
    "Xiao Yan", "Xiao Xun'er", "Nalan Yanran", "Yao Lao", "Hun Tiandi", 
    "Hai Po Dong", "Jia Xing Tian", "Zi Yan", "Fa Ma", "Mu Chen", 
    "Dou Sheng", "Dou Zun", "Queen Medusa", "Han Feng", "Tian Lei", 

    # Douglas (The Legendary Mechanic)
    "Han Xiao", "Hila", "Aurora", "Herlous", "Aroshia", "Feidin", 
    "Black Star", "EsGod", "Manison", "Reynold", "Hila Nanobot", 

    # Trending Anime (Attack on Titan, Demon Slayer, Jujutsu Kaisen, etc.)
    "Eren Yeager", "Mikasa Ackerman", "Armin Arlert", "Levi Ackerman", 
    "Hange Zoe", "Jean Kirstein", "Reiner Braun", "Annie Leonhart", 
    "Zeke Yeager", "Historia Reiss", "Tanjiro Kamado", "Nezuko Kamado", 
    "Zenitsu Agatsuma", "Inosuke Hashibira", "Kyojuro Rengoku", 
    "Satoru Gojo", "Yuji Itadori", "Megumi Fushiguro", "Ryomen Sukuna", 
    "Yuta Okkotsu", "Jing Yuan", "Ichigo Kurosaki", "Byakuya Kuchiki", 
    "Shunsui Kyoraku", "Rukia Kuchiki", "Seishiro Nagi", "Yoichi Isagi", 
    "Takemichi Hanagaki", "Mikey", "Draken", "Hajime Nagumo", 
    "Rudeus Greyrat", "Sylphy", "Kaori Shirasaki", "Rimuru Tempest", 
    "Milim Nava", "Vash the Stampede", "Loid Forger", "Yor Forger", 
    "Anya Forger", "Denji Chainsaw", "Makima", "Power", "Aki Hayakawa"


    # Playable Characters
    "Trailblazer", "Kafka", "Silver Wolf", "Dan Heng", "March 7th", 
    "Himeko", "Welt", "Bronya", "Seele", "Clara", "Gepard", 
    "Serval", "Sampo", "Natasha", "Hook", "Pela", "Arlan", 
    "Asta", "Yanqing", "Bailu", "Jing Yuan", "Tingyun", 
    "Luocha", "Sushang", "Fu Xuan", "Yukong", "Blade", "Topaz", 
    "Guinaifen", "Hanabi", "Jingliu", "Imbibitor Lunae", "Lynx", 
    "Herta", "Qingque", "Svarog",

    # Antagonists & NPCs
    "Cocolia", "Svarog", "Bronya Rand", "Stelle", "Caelus", 
    "Elio", "Sampo Koski", "Hook Ingenuity", "Silvermane Guards", 
    "Aurora", "Natasha Pupil", "Svarog Automaton",

    # Organizations
    "Astral Express", "Antimatter Legion", "Xianzhou Alliance", 
    "Stellaron Hunters", "Ebon Deer", "Genius Society", 

    # Planets & Factions
    "Jarilo VI", "Herta Space Station", "Belobog", "Xianzhou Luofu", 
    "The Abundance", "The Hunt", "The Preservation", "The Nihility", 
    "The Destruction", "The Harmony", "The Elation",

    # Others
    "Kafka Stellaron", "Jing Yuan Arbiter", "Blade Mara", "Pela Tactician",
    "Luocha Physician", "Yanqing Prodigy", "Tingyun Ambassador", 
    "Fu Xuan Diviner", "Yukong Navigator", "Topaz Prospector", 
    "Imbibitor Lunae", "Clara Engineering", "Bronya Supreme Guardian", 
    "March Memory", "Dan Heng Vidyadhara", "Seele Butterfly",
    "Himeko Navigator", "Welt Observer", "Hook Underworld", "Qingque Divination"

    "Aether", "Lumine", "Venti", "Amber", "Kaeya", "Lisa", "Jean", 
    "Diluc", "Razor", "Barbara", "Fischl", "Beidou", "Ningguang", 
    "Xiangling", "Xingqiu", "Chongyun", "Keqing", "Sucrose", 
    "Mona", "Diona", "Albedo", "Ganyu", "Hu Tao", "Rosaria", 
    "Eula", "Kazuha", "Yoimiya", "Ayaka", "Sayu", "Kokomi", 
    "Raiden", "Sara", "Gorou", "Itto", "Shenhe", "Yunjin", 
    "Yae Miko", "Ayato", "Collei", "Tighnari", "Cyno", 
    "Candace", "Nilou", "Nahida", "Layla", "Faruzan", "Wanderer", 
    "Dehya", "Mika", "Baizhu", "Kaveh", "Alhaitham", "Lynette", 
    "Lyney", "Neuvillette", "Furina", "Arlecchino", "Clorinde", 
    "Chiori", "La Signora", "Pantalone", "Pierro", "Dottore", 
    "Sandrone", "Pulcinella", "Tartaglia", "Scaramouche", 
    "Kaedehara Kazuha", "Kamisato Ayaka", "Kamisato Ayato", 
    "Sangonomiya Kokomi", "Raiden Shogun", "Arataki Itto", 
    "Yae Miko", "Thoma", "Shikanoin Heizou", "Yun Jin", "Candace", 
    "Dehya", "Tighnari", "Collei", "Cyno", "Alhaitham", 
    "Kaveh", "Mika", "Baizhu", "Furina", "Lynette", "Lyney", 
    "Neuvillette", "Dainsleif", "Zhongli", "Eula Lawrence", 
    "Klee Gunnhildr", "Jean Gunnhildr", "Diluc Ragnvindr", 
    "Kaeya Alberich", "Amber Burbank", "Bennett", "Xiangling", 
    "Beidou", "Ningguang", "Razor", "Fischl von Luftschloss Narfidort", 
    "Barbara Pegg", "Rosaria Deacon", "Sucrose Scholarly", "Xinyan", 
    "Hu Tao", "Mona Megistus", "Chongyun", "Xingqiu", "Zhongli", 
    "Qiqi", "Ganyu", "Keqing", "Diona", "Albedo", "Yelan", 
    "Traveler"
]





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
