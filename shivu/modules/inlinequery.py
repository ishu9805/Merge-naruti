import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING, DESCENDING
from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultPhoto, InlineQueryResultVideo

from shivu import user_collection, collection, db
from shivu import shivuu as app

# collection
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])
db.characters.create_index([('vid_url', ASCENDING)])
db.characters.create_index([('rarity', ASCENDING)])

# user_collection
db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])
db.user_collection.create_index([('characters.vid_url', ASCENDING)])
db.user_collection.create_index([('characters.rarity', ASCENDING)])

all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

RARITY_MAPPING = {
    '⚪️ Common': '⚪️',
    '🟣 Rare': '🟣',
    '🟡 Legendary': '🟡',
    '🟢 Medium': '🟢',
    '💮 Special Edition': '💮',
    '🔮 Limited Edition': '🔮',
    '💸 Premium Edition': '💸',
    '🌤 Summer': '🌤',
    '🎐 Celestial': '🎐',
    '❄️ Winter': '❄️',
    '💝 Valentine': '💝',
    '🎃 Halloween': '🎃',
    '🎄 Christmas Special': '🎄',
    '🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐': '🪐',
    '🎭 Cosplay Master 🎭': '🎭',
    '🎖 Apex Lot ( AUCTION )': '🎖',
    '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣': '🎗️'
}

@app.on_inline_query()
async def inlinequery(client, update):
    query = update.query.strip()
    offset = int(update.offset) if update.offset else 0
    limit = 50  # Number of results per page
    results = []

    if query.startswith('collection.img.') or query.startswith('collection.vid.'):
        parts = query.split('.', 2)
        user_id = parts[2].split(' ')[0] if len(parts) > 2 else None
        search_term = ' '.join(parts[2].split(' ')[1:]) if ' ' in parts[2] else None

        if user_id and user_id.isdigit():
            user = user_collection_cache.get(user_id)
            if not user:
                user = await user_collection.find_one({'id': int(user_id)})
                if user:
                    user_collection_cache[user_id] = user

            if user:
                regex = re.compile(search_term, re.IGNORECASE) if search_term else None
                if query.startswith('collection.img.'):
                    characters = [
                        char for char in user.get('characters', [])
                        if ('img_url' in char and char['img_url'] and 
                            (not regex or regex.search(char['name']) or regex.search(char['anime']) or regex.search(char['rarity'])))
                    ]
                elif query.startswith('collection.vid.'):
                    characters = [
                        char for char in user.get('characters', [])
                        if ('vid_url' in char and char['vid_url'] and
                            (not regex or regex.search(char['name']) or regex.search(char['anime']) or regex.search(char['rarity'])))
                    ]

                for char in characters[offset:offset + limit]:
                    rarity_emoji = RARITY_MAPPING.get(char['rarity'], '')
                    caption = (
                        f"Look At <a href='tg://user?id={user['id']}'>"
                        f"{escape(user.get('first_name', str(user['id'])))}</a>'s Character\n\n"
                        f"⌬ {char['anime']} \n"
                        f"◈⌠{rarity_emoji}⌡ {char['name']} x{len([c for c in user.get('characters', []) if c['name'] == char['name']])}\n"
                        f"**ID**: {char['id']} | **Rarity**: {char['rarity'].split()[1]}\n\n"
                    )
                    if query.startswith('collection.img.'):
                        results.append(
                            InlineQueryResultPhoto(
                                photo_url=char['img_url'],
                                thumb_url=char['img_url'],
                                id=f"{char['id']}_img_{time.time()}",
                                caption=caption
                            )
                        )
                    elif query.startswith('collection.vid.'):
                        results.append(
                            InlineQueryResultVideo(
                                video_url=char['vid_url'],
                                mime_type="video/mp4",
                                thumb_url=char['vid_url'],
                                id=f"{char['id']}_vid_{time.time()}",
                                title=f"{char['name']} ({char['anime']})",
                                caption=caption
                            )
                        )

    
    else:
        # Global search (combined results for images and videos)
        regex = re.compile(query, re.IGNORECASE) if query else None
        characters = await collection.find(
            {"$or": [{"name": regex}, {"anime": regex}, {"rarity": regex}]}
        ).to_list(length=None) if regex else all_characters_cache.get('all_characters') or await collection.find({}).to_list(length=None)

        all_characters_cache['all_characters'] = characters

        for character in characters[offset:offset + limit]:
            rarity_emoji = RARITY_MAPPING.get(character['rarity'], '')
            #global_count = len([u for u in await user_collection.find({'characters.id': character['id']}).to_list(length=None)])
            
            caption = (
                f"**Look At This Character!!**\n\n"
                f"⌬ {character['anime']}\n"
                f"◈⌠{rarity_emoji}⌡ {character['name']}\n"
                f"**ID**: {character['id']} | **Rarity**: {character['rarity'].split()[1]}\n\n"
                #f"🌍 **Global Count**: {global_count} users\n"
            )
            if 'vid_url' in character and character['vid_url']:
                results.append(
                    InlineQueryResultVideo(
                        video_url=character['vid_url'],
                        mime_type="video/mp4",
                        thumb_url=character['vid_url'],
                        id=f"{character['id']}_vid_{time.time()}",
                        title=f"{character['name']} ({character['anime']})",
                        caption=caption
                    )
                )
            elif 'img_url' in character and character['img_url']:
                results.append(
                    InlineQueryResultPhoto(
                        photo_url=character['img_url'],
                        thumb_url=character['img_url'],
                        id=f"{character['id']}_img_{time.time()}",
                        caption=caption
                    )
                )

    # Pagination
    next_offset = str(offset + limit) if len(results) == limit else ""
    await update.answer(results, next_offset=next_offset, cache_time=5, is_gallery=True)
                    
