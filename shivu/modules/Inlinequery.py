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

    # Common filter parsing function
    def parse_filters(query_part):
        filters = {
            'rarity': None,
            'name': None,
            'anime': None,
            'id': None
        }
        
        # Parse structured filters (.rarity. value .anime. value etc)
        filter_parts = re.split(r'\.(rarity|name|anime|id)\.', query_part)
        
        for i in range(1, len(filter_parts), 2):
            filter_type = filter_parts[i]
            filter_value = filter_parts[i+1].split('.')[0].strip()
            if filter_type in filters:
                filters[filter_type] = filter_value
                
        return filters

    # USER COLLECTION SEARCH
    if query.startswith('collection.img.') or query.startswith('collection.vid.'):
        parts = query.split('.')
        media_type = parts[1]  # img or vid
        user_id = parts[2] if len(parts) > 2 and parts[2].isdigit() else None
        
        # Parse any filters after user ID
        filters = parse_filters('.'.join(parts[3:])) if len(parts) > 3 else {
            'rarity': None,
            'name': None,
            'anime': None,
            'id': None
        }

        if user_id:
            user = user_collection_cache.get(user_id)
            if not user:
                user = await user_collection.find_one({'id': int(user_id)})
                if user:
                    user_collection_cache[user_id] = user

            if user:
                all_characters = user.get('characters', [])
                
                # Filter based on media type
                if media_type == 'img':
                    characters = [char for char in all_characters if 'img_url' in char and char['img_url']]
                else:
                    characters = [char for char in all_characters if 'vid_url' in char and char['vid_url']]
                
                # Apply filters
                filtered_characters = []
                for char in characters:
                    match = True
                    if filters['rarity'] and filters['rarity'].lower() not in char['rarity'].lower():
                        match = False
                    if filters['name'] and filters['name'].lower() not in char['name'].lower():
                        match = False
                    if filters['anime'] and filters['anime'].lower() not in char['anime'].lower():
                        match = False
                    if filters['id'] and str(char['id']) != filters['id']:
                        match = False
                    if match:
                        filtered_characters.append(char)
                
                characters = filtered_characters
                
                # Sort and process results
                characters.sort(key=lambda x: x['id'], reverse=True)
                
                # Aggregate duplicates
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

                # Create results
                for char_data in list(aggregated_characters.values())[offset:offset + limit]:
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

                    if media_type == 'img':
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

    # GLOBAL SEARCH
    else:
        # Parse global search filters
        filters = parse_filters(query)
        has_filters = any(filters.values())
        
        if has_filters:
            # Build MongoDB query for filtered search
            mongo_query = []
            
            if filters['rarity']:
                mongo_query.append({'rarity': {'$regex': filters['rarity'], '$options': 'i'}})
            if filters['name']:
                mongo_query.append({'name': {'$regex': filters['name'], '$options': 'i'}})
            if filters['anime']:
                mongo_query.append({'anime': {'$regex': filters['anime'], '$options': 'i'}})
            if filters['id']:
                try:
                    mongo_query.append({'id': int(filters['id'])})
                except ValueError:
                    pass
            
            if mongo_query:
                query = {'$and': mongo_query} if len(mongo_query) > 1 else mongo_query[0]
                characters = await collection.find(query).sort('id', DESCENDING).to_list(length=None)
            else:
                characters = []
        else:
            # Default global search (no filters or empty query)
            if not query:
                characters = all_characters_cache.get('all_characters') 
                if not characters:
                    characters = await collection.find({}).sort('id', DESCENDING).to_list(length=None)
                    all_characters_cache['all_characters'] = characters
            else:
                # Simple text search
                regex = re.compile(query, re.IGNORECASE)
                characters = await collection.find(
                    {"$or": [{"name": regex}, {"anime": regex}, {"rarity": regex}]}
                ).sort('id', DESCENDING).to_list(length=None)

        # Process results for global search
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

        # Create global search results
        for character_data in list(aggregated_characters.values())[offset:offset + limit]:
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
