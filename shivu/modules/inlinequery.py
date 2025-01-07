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
    characters = []

    if query.startswith('collection.'):
        # User collection search
        try:
            user_id, search_terms = query.split('.', 1)[1].split(' ', 1)
        except ValueError:
            user_id, search_terms = query.split('.', 1)[1], ""

        if user_id.isdigit():
            user = user_collection_cache.get(user_id)
            if not user:
                user = await user_collection.find_one({'id': int(user_id)})
                if user:
                    user_collection_cache[user_id] = user

            if user:
                characters = user.get('characters', [])
                if search_terms:
                    regex = re.compile(search_terms, re.IGNORECASE)
                    characters = [
                        char for char in characters
                        if regex.search(char['name']) or regex.search(char['anime']) or regex.search(char['rarity'])
                    ]
    else:
        # Global search
        if query:
            regex = re.compile(query, re.IGNORECASE)
            characters = await collection.find({"$or": [
                {"name": regex}, {"anime": regex}, {"rarity": regex}
            ]}).to_list(length=None)
        else:
            characters = all_characters_cache.get('all_characters') or await collection.find({}).to_list(length=None)
            all_characters_cache['all_characters'] = characters

    # Pagination
    paginated_characters = characters[offset:offset + limit]
    next_offset = str(offset + limit) if len(paginated_characters) == limit else ""

    results = []
    for character in paginated_characters:
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
                    id=f"{character['id']}_vid_{time.time()}",
                    thumb_url=character['vid_url'],
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

    await update.answer(results, next_offset=next_offset, cache_time=5, is_gallery=True)
