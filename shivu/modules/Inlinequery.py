import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING, DESCENDING
from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultPhoto, InlineQueryResultVideo

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

# Database Indexing
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])
db.characters.create_index([('vid_url', ASCENDING)])
db.characters.create_index([('rarity', ASCENDING)])

db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])
db.user_collection.create_index([('characters.vid_url', ASCENDING)])
db.user_collection.create_index([('characters.rarity', ASCENDING)])

# Caching
all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)
anime_count_cache = {}
character_user_count_cache = {}

# Rarity Mapping
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
    limit = 50
    results = []

    if query.startswith('collection.img.') or query.startswith('collection.vid.'):
        # User collection view
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
                
                # Get all characters first
                all_characters = user.get('characters', [])
                
                # Filter based on media type and search term
                if query.startswith('collection.img.'):
                    characters = [
                        char for char in all_characters
                        if ('img_url' in char and char['img_url'] and 
                            (not regex or regex.search(char['name']) or regex.search(char['anime']) or regex.search(char['rarity'])))
                    ]
                else:
                    characters = [
                        char for char in all_characters
                        if ('vid_url' in char and char['vid_url'] and
                            (not regex or regex.search(char['name']) or regex.search(char['anime']) or regex.search(char['rarity'])))
                    ]

                # Sort characters by ID in descending order (newest first)
                characters.sort(key=lambda x: x['id'], reverse=True)

                # Aggregate duplicates while maintaining order
                aggregated_characters = {}
                for char in characters:
                    char_id = char['id']
                    if char_id in aggregated_characters:
                        aggregated_characters[char_id]['count'] += 1
                    else:
                        aggregated_characters[char_id] = {
                            'character': char,
                            'count': 1
                        }

                # Convert to sorted list (already sorted by ID)
                sorted_characters = list(aggregated_characters.values())

                # Paginate results
                for char_data in sorted_characters[offset:offset + limit]:
                    char = char_data['character']
                    count = char_data['count']
                    rarity_emoji = RARITY_MAPPING.get(char['rarity'], '')

                    # Get anime count stats
                    user_anime_count = sum(1 for c in all_characters if c.get('anime') == char['anime'])
                    if char['anime'] in anime_count_cache:
                        total_anime_count = anime_count_cache[char['anime']]
                    else:
                        total_anime_count = await collection.count_documents({'anime': char['anime']})
                        anime_count_cache[char['anime']] = total_anime_count

                    caption = (
                        f"Look At <a href='tg://user?id={user['id']}'>{escape(user.get('first_name', str(user['id'])))}</a>'s Character\n\n"
                        f"⌬ {char['anime']} 〔{user_anime_count}/{total_anime_count}〕\n"
                        f"◈⌠{rarity_emoji}⌡ {char['name']} x{count}\n"
                        f"**ID**: {char['id']} | **Rarity**: {char['rarity'].split()[1]}\n"
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
                    else:
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
        # Global character search
        if not query:
            # Get all characters sorted by ID descending (newest first)
            characters = all_characters_cache.get('all_characters') 
            if not characters:
                characters = await collection.find({}).sort('id', DESCENDING).to_list(length=None)
                all_characters_cache['all_characters'] = characters
        else:
            # Search with query, sorted by ID descending
            regex = re.compile(query, re.IGNORECASE)
            characters = await collection.find(
                {"$or": [{"name": regex}, {"anime": regex}, {"rarity": regex}]}
            ).sort('id', DESCENDING).to_list(length=None)

        # Aggregate duplicates while maintaining order
        aggregated_characters = {}
        for character in characters:
            char_id = character['id']
            if char_id in aggregated_characters:
                aggregated_characters[char_id]['count'] += 1
            else:
                aggregated_characters[char_id] = {
                    'character': character,
                    'count': 1
                }

        # Already sorted by ID descending
        sorted_characters = list(aggregated_characters.values())

        # Paginate results
        for character_data in sorted_characters[offset:offset + limit]:
            character = character_data['character']
            count = character_data['count']
            rarity_emoji = RARITY_MAPPING.get(character['rarity'], '')

            # Get anime stats
            if character['anime'] in anime_count_cache:
                total_anime_count = anime_count_cache[character['anime']]
            else:
                total_anime_count = await collection.count_documents({'anime': character['anime']})
                anime_count_cache[character['anime']] = total_anime_count

            # Get ownership stats
            if character['id'] in character_user_count_cache:
                total_user_count = character_user_count_cache[character['id']]
            else:
                total_user_count = await user_collection.count_documents({'characters.id': character['id']})
                character_user_count_cache[character['id']] = total_user_count

            caption = (
                f"✨ **OwO! Check out this waifu!** ✨\n\n"
                f"🎬 **Anime**: {character['anime']} [{total_anime_count}]\n"
                f"🆔 **ID**: {character['id']}\n"
                f"🌟 **Name**: {character['name']}\n"
                f"🔮 **Rarity**: {character['rarity']}\n"
                f"👥 **Owned by**: {total_user_count} users\n"
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
            else:
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
    await update.answer(results, next_offset=next_offset, cache_time=6, is_gallery=True)
