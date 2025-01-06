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

@app.on_inline_query()
async def inlinequery(client, update):
    query = update.query.strip()
    offset = int(update.offset) if update.offset else 0
    limit = 30  # Number of results per page
    results = []

    if query.startswith('collection.img.'):
        # User collection search for images
        user_id = query.split('.', 2)[2]
        if user_id.isdigit():
            user = user_collection_cache.get(user_id)
            if not user:
                user = await user_collection.find_one({'id': int(user_id)})
                if user:
                    user_collection_cache[user_id] = user

            if user:
                characters = [
                    char for char in user.get('characters', [])
                    if 'img_url' in char and char['img_url']
                ]
                for char in characters[offset:offset + limit]:
                    caption = (
                        f"<b>Look At This Character!!</b>\n\n"
                        f"🌸: <b>{char['name']}</b>\n"
                        f"🏖️: <b>{char['anime']}</b>\n"
                        f"<b>{char['rarity']}</b>\n"
                        f"🆔️: <b>{char['id']}</b>\n\n"
                    )
                    results.append(
                        InlineQueryResultPhoto(
                            photo_url=char['img_url'],
                            thumb_url=char['img_url'],
                            id=f"{char['id']}_img_{time.time()}",
                            caption=caption
                        )
                    )

    elif query.startswith('collection.vid.'):
        # User collection search for videos
        user_id = query.split('.', 2)[2]
        if user_id.isdigit():
            user = user_collection_cache.get(user_id)
            if not user:
                user = await user_collection.find_one({'id': int(user_id)})
                if user:
                    user_collection_cache[user_id] = user

            if user:
                characters = [
                    char for char in user.get('characters', [])
                    if 'vid_url' in char and char['vid_url']
                ]
                for char in characters[offset:offset + limit]:
                    caption = (
                        f"<b>Look At This Character!!</b>\n\n"
                        f"🌸: <b>{char['name']}</b>\n"
                        f"🏖️: <b>{char['anime']}</b>\n"
                        f"<b>{char['rarity']}</b>\n"
                        f"🆔️: <b>{char['id']}</b>\n\n"
                    )
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
            caption = (
                f"<b>Look At This Character!!</b>\n\n"
                f"🌸: <b>{character['name']}</b>\n"
                f"🏖️: <b>{character['anime']}</b>\n"
                f"<b>{character['rarity']}</b>\n"
                f"🆔️: <b>{character['id']}</b>\n\n"
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
    
