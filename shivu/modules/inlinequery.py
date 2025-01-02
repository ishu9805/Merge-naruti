import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING, DESCENDING

from telegram import Update, InlineQueryResultPhoto
from telegram.ext import InlineQueryHandler, CallbackContext, CommandHandler, CallbackQueryHandler 
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from shivu import user_collection, collection, application, db


# collection
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])
db.characters.create_index([('rarity', ASCENDING)])

# user_collection
db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])
db.user_collection.create_index([('characters.rarity', ASCENDING)])

all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.strip()
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0
    limit = 30  # Number of results per page
    characters = []

    if query.startswith('collection.'):
        # User collection search
        user_id, *search_terms = query.split(' ')[0].split('.')[1], ' '.join(query.split(' ')[1:])
        if user_id.isdigit():
            user = user_collection_cache.get(user_id)
            if not user:
                user = await user_collection.find_one({'id': int(user_id)})
                if user:
                    user_collection_cache[user_id] = user
            
            if user:
                # Use dictionary for unique characters
                unique_characters = {char['id']: char for char in user.get('characters', [])}
                characters = list(unique_characters.values())

                if search_terms:
                    regex = re.compile(' '.join(search_terms), re.IGNORECASE)
                    characters = [
                        char for char in characters
                        if regex.search(char['name']) or regex.search(char['anime']) or regex.search(char['rarity'])
                    ]
        else:
            characters = []
    else:
        # Global search
        if query:
            regex = re.compile(query, re.IGNORECASE)
            characters = await collection.find({"$or": [{"name": regex}, {"anime": regex}, {"rarity": regex}]}).to_list(length=None)
        else:
            characters = all_characters_cache.get('all_characters') or await collection.find({}).to_list(length=None)
            all_characters_cache['all_characters'] = characters

    # Pagination
    paginated_characters = characters[offset:offset + limit]
    next_offset = str(offset + limit) if len(paginated_characters) == limit else ""

    results = []
    for character in paginated_characters:
        global_count = await user_collection.count_documents({'characters.id': character['id']})
        anime_count = await collection.count_documents({'anime': character['anime']})

        caption = (
            f"<b>Look At This Character!!</b>\n\n"
            f"🌸: <b>{character['name']}</b>\n"
            f"🏖️: <b>{character['anime']}</b>\n"
            f"<b>{character['rarity']}</b>\n"
            f"🆔️: <b>{character['id']}</b>\n\n"
            f"<b>Globally Guessed {global_count} Times...</b>"
        )

        results.append(
            InlineQueryResultPhoto(
                thumbnail_url=character['img_url'],
                id=f"{character['id']}_{time.time()}",
                photo_url=character['img_url'],
                caption=caption,
                parse_mode='HTML',
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)



application.add_handler(InlineQueryHandler(inlinequery, block=False))
