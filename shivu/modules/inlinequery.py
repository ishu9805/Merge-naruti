import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING, DESCENDING

from telegram import Update, InlineQueryResultPhoto
from telegram.ext import InlineQueryHandler, CallbackContext, CommandHandler, CallbackQueryHandler 
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import user_collection, collection, application, db
from html import escape
from cachetools import TTLCache
from pymongo import ASCENDING
from telegram import Update, InlineQueryResultPhoto
from telegram.ext import InlineQueryHandler
from shivu import user_collection, collection, application, db


# MongoDB Indexing (using ASCENDING for faster queries)
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('name', ASCENDING)])
db.characters.create_index([('rarity', ASCENDING)])

db.user_collection.create_index([('id', ASCENDING)])
db.user_collection.create_index([('characters.id', ASCENDING)])

# Caches
all_characters_cache = TTLCache(maxsize=10000, ttl=3600)  # Cache for global characters
user_collection_cache = TTLCache(maxsize=10000, ttl=60)   # Cache for user data


# Inline Query Handler
async def inlinequery(update: Update, context) -> None:
    query = update.inline_query.query.strip()
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0
    limit = 20  # Number of results per page

    # Process User Collection Queries
    if query.startswith('collection.'):
        user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
        if user_id.isdigit():
            user = user_collection_cache.get(user_id) or await user_collection.find_one({'id': int(user_id)})
            user_collection_cache[user_id] = user

            if user:
                user_characters = user.get('characters', [])
                # Filter by search terms if provided
                if search_terms:
                    regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                    user_characters = [
                        c for c in user_characters
                        if regex.search(c.get('name', '')) or regex.search(c.get('anime', '')) or regex.search(c.get('rarity', ''))
                    ]
            else:
                user_characters = []

            # Paginate results
            characters = user_characters[offset:offset + limit]
            next_offset = str(offset + limit) if len(characters) == limit else ''
        else:
            characters = []
            next_offset = ''

    # Process Global Character Queries
    else:
        if query:
            regex = re.compile(query, re.IGNORECASE)
            characters = await collection.find(
                {"$or": [{"name": regex}, {"anime": regex}, {"rarity": regex}]},
                sort=[('id', ASCENDING)]
            ).skip(offset).limit(limit).to_list(length=None)
        else:
            # Use cache for global characters
            all_characters = all_characters_cache.get('all_characters')
            if not all_characters:
                all_characters = await collection.find({}, sort=[('id', ASCENDING)]).to_list(length=None)
                all_characters_cache['all_characters'] = all_characters

            characters = all_characters[offset:offset + limit]

        next_offset = str(offset + limit) if len(characters) == limit else ''

    # Prepare Inline Query Results
    results = []
    for character in characters:
        global_count = await user_collection.count_documents({'characters.id': character['id']})
        anime_characters = await collection.count_documents({'anime': character['anime']})

        if query.startswith('collection.'):
            user_character_count = sum(c['id'] == character['id'] for c in user['characters'])
            user_anime_characters = sum(c['anime'] == character['anime'] for c in user['characters'])
            caption = f"<b> Look At <a href='tg://user?id={user['id']}'>{(escape(user.get('first_name', user['id'])))}</a>'s Character</b>\n\n🌸: <b>{character['name']} (x{user_character_count})</b>\n🏖️: <b>{character['anime']} ({user_anime_characters}/{anime_characters})</b>\n<b>{character['rarity']}</b>\n\n<b>🆔️:</b> {character['id']}</b>\n\n<b>Globally Guessed {global_count} Times...</b>"
        else:
            caption = f"<b>Look At This Character!!</b>\n\n🌸:<b> {character['name']}</b>\n🏖️: <b>{character['anime']}</b>\n<b>{character['rarity']}</b>\n🆔️: <b>{character['id']}</b>\n\n<b>Globally Guessed {global_count} Times...</b>"

        results.append(
            InlineQueryResultPhoto(
                id=f"{character['id']}_{time.time()}",
                photo_url=character['img_url'],
                thumbnail_url=character['img_url'],
                caption=caption,
                parse_mode='HTML',
            )
        )

    # Answer Inline Query
    await update.inline_query.answer(results, next_offset=next_offset, cache_time=3)


# Add Handler to Application
application.add_handler(InlineQueryHandler(inlinequery, block=False))
