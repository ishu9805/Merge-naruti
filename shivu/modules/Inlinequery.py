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

    # Pre-compiled regex patterns for faster matching
    FILTER_PATTERN = re.compile(r'\.(rarity|name|anime|id)\.([^\.]+)')
    SPACE_PATTERN = re.compile(r'\s+')

    async def parse_filters(query_part):
        filters = {
            'rarity': None,
            'name': None,
            'anime': None,
            'id': None
        }
        
        # Use regex to find all filter patterns at once
        for match in FILTER_PATTERN.finditer(query_part):
            filter_type, filter_value = match.groups()
            if filter_type in filters:
                filters[filter_type] = SPACE_PATTERN.sub(' ', filter_value.strip())
                
        return filters

    # USER COLLECTION SEARCH - OPTIMIZED
    if query.startswith(('collection.img.', 'collection.vid.')):
        start_time = time.time()
        parts = query.split('.', 3)
        media_type = parts[1]
        user_id = parts[2] if len(parts) > 2 and parts[2].isdigit() else None
        
        # Get user collection with optimized caching
        user = None
        if user_id:
            user = user_collection_cache.get(user_id)
            if not user:
                user = await user_collection.find_one(
                    {'id': int(user_id)},
                    projection={'characters': 1, 'id': 1}
                )
                if user:
                    user_collection_cache[user_id] = user

        if user:
            # Apply media type filter first to reduce dataset
            media_field = 'img_url' if media_type == 'img' else 'vid_url'
            pipeline = [
                {'$match': {'id': user['id']}},
                {'$unwind': '$characters'},
                {'$match': {f'characters.{media_field}': {'$exists': True, '$ne': None}}},
                {'$group': {'_id': '$characters.id', 'char': {'$first': '$characters'}, 'count': {'$sum': 1}}}
            ]
            
            # Parse and apply additional filters
            filters = await parse_filters(parts[3] if len(parts) > 3 else '')
            
            # Build aggregation match stages for filters
            match_stages = []
            for filter_type, value in filters.items():
                if value:
                    if filter_type == 'id':
                        match_stages.append({'_id': int(value) if value.isdigit() else 0})
                    else:
                        match_stages.append({f'char.{filter_type}': {'$regex': value, '$options': 'i'}})
            
            if match_stages:
                pipeline.insert(2, {'$match': {'$and': match_stages}})
            
            # Execute aggregation pipeline
            aggregated_chars = await user_collection.aggregate(pipeline).to_list(length=None)
            
            # Sort by ID descending (newest first)
            aggregated_chars.sort(key=lambda x: x['_id'], reverse=True)
            
            # Process results
            for char_data in aggregated_chars[offset:offset + limit]:
                char = char_data['char']
                count = char_data['count']
                rarity_emoji = RARITY_MAPPING.get(char['rarity'], '')
                
                # Get anime stats with cache
                anime = char['anime']
                total_anime_count = anime_count_cache.get(anime)
                if total_anime_count is None:
                    total_anime_count = await collection.count_documents({'anime': anime})
                    anime_count_cache[anime] = total_anime_count
                
                # Get user's count for this anime
                anime_chars = [c for c in user.get('characters', []) if c.get('anime') == anime]
                user_anime_count = len(anime_chars)

                caption = (
                    f"Look At <a href='tg://user?id={user['id']}'>{escape(user.get('first_name', str(user['id'])))}</a>'s Character\n\n"
                    f"⌬ {anime} 〔{user_anime_count}/{total_anime_count}〕\n"
                    f"◈⌠{rarity_emoji}⌡ {char['name']} x{count}\n"
                    f"**ID**: {char['id']} | **Rarity**: {char['rarity'].split()[1]}\n"
                )

                media_url = char['img_url'] if media_type == 'img' else char['vid_url']
                result_id = f"{char['id']}_{media_type}_{time.time()}"
                
                if media_type == 'img':
                    results.append(InlineQueryResultPhoto(
                        photo_url=media_url,
                        thumb_url=media_url,
                        id=result_id,
                        caption=caption
                    ))
                else:
                    results.append(InlineQueryResultVideo(
                        video_url=media_url,
                        mime_type="video/mp4",
                        thumb_url=media_url,
                        id=result_id,
                        title=f"{char['name']} ({char['anime']})",
                        caption=caption
                    ))

    # GLOBAL SEARCH - OPTIMIZED
    else:
        filters = await parse_filters(query)
        has_filters = any(filters.values())
        
        if has_filters:
            # Build optimized MongoDB query
            query = {}
            if filters['rarity']:
                query['rarity'] = {'$regex': filters['rarity'], '$options': 'i'}
            if filters['name']:
                query['name'] = {'$regex': filters['name'], '$options': 'i'}
            if filters['anime']:
                query['anime'] = {'$regex': filters['anime'], '$options': 'i'}
            if filters['id'] and filters['id'].isdigit():
                query['id'] = int(filters['id'])
            
            characters = await collection.find(query).sort('id', DESCENDING).to_list(length=None)
        else:
            if not query:
                characters = all_characters_cache.get('all_characters')
                if not characters:
                    characters = await collection.find({}).sort('id', DESCENDING).to_list(length=None)
                    all_characters_cache['all_characters'] = characters
            else:
                characters = await collection.find(
                    {"$or": [
                        {"name": {'$regex': query, '$options': 'i'}},
                        {"anime": {'$regex': query, '$options': 'i'}},
                        {"rarity": {'$regex': query, '$options': 'i'}}
                    ]}
                ).sort('id', DESCENDING).to_list(length=None)

        # Process results with optimized ownership count lookup
        char_ids = [char['id'] for char in characters]
        ownership_counts = await user_collection.count_documents(
            {'characters.id': {'$in': char_ids}},
            limit=100
        )
        
        for character in characters[offset:offset + limit]:
            rarity_emoji = RARITY_MAPPING.get(character['rarity'], '')
            
            # Get anime stats with cache
            anime = character['anime']
            total_anime_count = anime_count_cache.get(anime)
            if total_anime_count is None:
                total_anime_count = await collection.count_documents({'anime': anime})
                anime_count_cache[anime] = total_anime_count

            caption = (
                f"✨ **OwO! Check out this waifu!** ✨\n\n"
                f"🎬 **Anime**: {anime} [{total_anime_count}]\n"
                f"🆔 **ID**: {character['id']}\n"
                f"🌟 **Name**: {character['name']}\n"
                f"🔮 **Rarity**: {character['rarity']}\n"
                f"👥 **Owned by**: {ownership_counts} users\n"
            )

            if 'vid_url' in character and character['vid_url']:
                results.append(InlineQueryResultVideo(
                    video_url=character['vid_url'],
                    mime_type="video/mp4",
                    thumb_url=character['vid_url'],
                    id=f"{character['id']}_vid_{time.time()}",
                    title=f"{character['name']} ({character['anime']})",
                    caption=caption
                ))
            else:
                results.append(InlineQueryResultPhoto(
                    photo_url=character['img_url'],
                    thumb_url=character['img_url'],
                    id=f"{character['id']}_img_{time.time()}",
                    caption=caption
                ))

    # Pagination
    next_offset = str(offset + limit) if len(results) == limit else ""
    await update.answer(results, next_offset=next_offset, cache_time=6, is_gallery=True)
