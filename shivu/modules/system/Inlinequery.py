import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING, DESCENDING
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, InlineQueryResultVideo
from shivu.modules.Addshop import handle_shop_inline
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
    UPDATE_CHATps as UPDATE_CHAT_PS,
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
    '🧧 𝙀𝙫𝙚𝙣𝙩𝙨': '🧧',
    '🍑 Echhi': '🍑',
    '☠️ 𝕯𝖎𝖛𝖎𝖓𝖊': '☠️',
    '☔ Monsoon': '☔',
    '🪸 Aquatic': '🪸',
    '🎨 Artistic': '🎨',
    '💳 VIP SLOT': '💳',
    '👶 Chibi': '👶',
    '🏴‍☠️ Marauds': '🏴‍☠️',
    '🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣': '🎗️'
}



@app.on_inline_query()
async def inline_master(client, inline_query):
    q = inline_query.query.strip()

    # --- SHOP INLINE ---
    if q.lower().startswith("shop.prince"):
        return await handle_shop_inline(client, inline_query)

    # --- CHARACTER INLINE SEARCH ---
    return await handle_general_inline(client, inline_query)
    

async def handle_general_inline(client, update):
    query = update.query.strip()
    offset = int(update.offset) if update.offset else 0
    limit = 30
    results = []

    def owner_list_keyboard(character_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Owner List", switch_inline_query_current_chat=f"/check {character_id}")]
        ])

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
                                caption=caption,
                                reply_markup=owner_list_keyboard(char['id'])
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
                                caption=caption,
                                reply_markup=owner_list_keyboard(char['id'])
                            )
                        )


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

        # Process results with per-character ownership count
        for character in characters[offset:offset + limit]:
            rarity_emoji = RARITY_MAPPING.get(character['rarity'], '')
            
            # Get anime stats with cache
            anime = character['anime']
            total_anime_count = anime_count_cache.get(anime)
            if total_anime_count is None:
                total_anime_count = await collection.count_documents({'anime': anime})
                anime_count_cache[anime] = total_anime_count

            # Get ownership count for this specific character
            char_id = character['id']
            if char_id in character_user_count_cache:
                ownership_count = character_user_count_cache[char_id]
            else:
                ownership_count = await user_collection.count_documents(
                    {'characters.id': char_id}
                )
                character_user_count_cache[char_id] = ownership_count

            caption = (
                f"✨ **OwO! Check out this waifu!** ✨\n\n"
                f"🎬 **Anime**: {anime} [{total_anime_count}]\n"
                f"🆔 **ID**: {character['id']}\n"
                f"🌟 **Name**: {character['name']}\n"
                f"🔮 **Rarity**: {character['rarity']}\n"
                f"👥 **Owned by**: {ownership_count} users\n"
            )

            if 'vid_url' in character and character['vid_url']:
                results.append(InlineQueryResultVideo(
                    video_url=character['vid_url'],
                    mime_type="video/mp4",
                    thumb_url=character['vid_url'],
                    id=f"{character['id']}_vid_{time.time()}",
                    title=f"{character['name']} ({character['anime']})",
                    caption=caption,
                    reply_markup=owner_list_keyboard(character['id'])
                ))
            else:
                results.append(InlineQueryResultPhoto(
                    photo_url=character['img_url'],
                    thumb_url=character['img_url'],
                    id=f"{character['id']}_img_{time.time()}",
                    caption=caption,
                    reply_markup=owner_list_keyboard(character['id'])
                ))

    # Pagination
    next_offset = str(offset + limit) if len(results) == limit else ""
    await update.answer(results, next_offset=next_offset, cache_time=6, is_gallery=True)




from shivu import shivuups as app

@app.on_message(filters.command("finderrors"))
async def find_missing_media(client, message):
    try:
        # Find characters missing img_url
        missing_img = await collection.find({
            "$or": [
                {"img_url": {"$exists": False}},
                {"img_url": None},
                {"img_url": ""}
            ]
        }).to_list(length=None)
        
        # Find characters missing vid_url
        missing_vid = await collection.find({
            "$or": [
                {"vid_url": {"$exists": False}},
                {"vid_url": None},
                {"vid_url": ""}
            ]
        }).to_list(length=None)
        
        # Find characters missing both
        missing_both = await collection.find({
            "$or": [
                {"$and": [
                    {"$or": [{"img_url": {"$exists": False}}, {"img_url": None}, {"img_url": ""}]},
                    {"$or": [{"vid_url": {"$exists": False}}, {"vid_url": None}, {"vid_url": ""}]}
                ]}
            ]
        }).to_list(length=None)
        
        # Create response message
        response = "**Characters with Missing Media URLs:**\n\n"
        
        if missing_img:
            img_ids = [str(char.get('id', 'Unknown')) for char in missing_img]
            response += f"**Missing img_url ({len(missing_img)}):**\n{', '.join(img_ids)}\n\n"
        else:
            response += "✅ No characters missing img_url\n\n"
            
        if missing_vid:
            vid_ids = [str(char.get('id', 'Unknown')) for char in missing_vid]
            response += f"**Missing vid_url ({len(missing_vid)}):**\n{', '.join(vid_ids)}\n\n"
        else:
            response += "✅ No characters missing vid_url\n\n"
            
        if missing_both:
            both_ids = [str(char.get('id', 'Unknown')) for char in missing_both]
            response += f"**Missing both URLs ({len(missing_both)}):**\n{', '.join(both_ids)}\n\n"
        else:
            response += "✅ No characters missing both URLs\n\n"
        
        # Send the response
        if len(response) > 4096:
            # If message is too long, send as document
            with open("missing_media_report.txt", "w") as f:
                f.write(response)
            await message.reply_document("missing_media_report.txt", caption="Report of characters with missing media URLs")
        else:
            await message.reply_text(response)
            
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

