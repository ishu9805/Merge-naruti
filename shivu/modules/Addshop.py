from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CallbackContext
from bson import ObjectId
import logging
import urllib.request
import uuid
import requests
import random
import html
import logging
from pymongo import ReturnDocument
from typing import List
from bson import ObjectId
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from datetime import datetime, timedelta

1# Assuming these are defined elsewhere in your code
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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CallbackContext
from bson import ObjectId
import logging


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from bson import ObjectId
from pymongo import ReturnDocument
import logging
async def add_character_to_shop(update: Update, context: CallbackContext) -> None:


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from bson import ObjectId
from shivu import shops_collectionps as shops_collection, user_collectionps as user_collection, applicationps as application
import logging

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)


"""
Pyrogram + Motor: 3-day rotating Inline Shop module
- Inline browsing: @YourBotUsername shop
- Text preview: /shop
- Buy: /buy <code>
- Regenerates shop every 3 days (on-demand at /shop or inline)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

from bson import ObjectId
from pymongo import ReturnDocument

from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultPhoto, InputTextMessageContent, InlineQuery

# --- ADJUST THESE IMPORTS TO MATCH YOUR PROJECT ---
from shivu import (
    shivuups as app,                # Pyrogram Client
    collectionps as collection,     # main characters collection (Motor)
    daily_shopps as daily_shop_collection,  # Motor collection for shop items (create if missing)
    user_collectionps as user_collection,   # users collection (Motor)
    PARTNER                          # partner/admin list (optional)
)
# ------------------------------------------------------------------

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
LOGGER = logging.getLogger("rotating-shop")

# --- Configuration (from your spec) ---
SHOP_TTL_DAYS = 3  # refresh every 3 days

PRICING = {
    "events": {"price": 1000, "currency": "tokens"},
    "special": {"price": 50, "currency": "tokens"},
    "limited": {"price": 150, "currency": "tokens"},
    "premium": {"price": 50000, "currency": "coins"},
    "seasonal": {"price": 300, "currency": "tokens"},
}

# Desired counts (from your last message)
WANTED_COUNTS = {
    "events": 1,
    "special": 1,
    "limited": 1,
    "premium": 2,
    "seasonal": 1,
}

# Map a "pool name" to a mongodb match expression for rarity field
# Adjust the regex substrings if your database uses different text.
POOL_QUERIES = {
    "events": {"rarity": {"$regex": r"(Events|🧧|Event)", "$options": "i"}},
    "special": {"rarity": {"$regex": r"(Special Edition|💮|Special)", "$options": "i"}},
    "limited": {"rarity": {"$regex": r"(Limited Edition|🔮|Limited)", "$options": "i"}},
    "premium": {"rarity": {"$regex": r"(Premium|💸|Premium Edition)", "$options": "i"}},
    # seasonal: look for any of the seasonal tags in rarity or in a 'tags' array (flexible)
    "seasonal": {"$or": [
        {"rarity": {"$regex": r"(Summer|Winter|Celestial|Valentine|Halloween|Christmas)", "$options": "i"}},
        {"tags": {"$in": ["Summer", "Winter", "Celestial", "Valentine", "Halloween", "Christmas"]}}
    ]},
}

# utils
def _now_utc() -> datetime:
    return datetime.utcnow()

def _expires_at_now_plus_days(days: int) -> datetime:
    return _now_utc() + timedelta(days=days)

def _gen_code() -> str:
    return uuid.uuid4().hex[:8].upper()

def _aesthetic_caption(item: Dict[str, Any]) -> str:
    char = item["character"]
    price = item["price"]
    currency = item["currency"]
    return (
        f"🛒 **{char.get('name')}**\n"
        f"📺 {char.get('anime', 'Unknown')}\n"
        f"✨ {char.get('rarity', '')}\n\n"
        f"💸 Price: `{price}` {currency}\n"
        f"🆔 Code: `{item['code']}`\n\n"
        "To buy: `/buy {}` (copy the code)".format(item['code'])
    )

# ---------- SHOP GENERATION ----------
async def _generate_shop_if_needed() -> List[Dict[str, Any]]:
    """
    Ensure there is a shop with unexpired items.
    If not, generate new shop items based on WANTED_COUNTS and POOL_QUERIES.
    Returns list of active shop items (docs).
    """
    now = _now_utc()
    # Remove expired items (optional cleanup)
    await daily_shop_collection.delete_many({"expires_at": {"$lte": now}})

    # Check for any active items (not expired)
    active_cursor = daily_shop_collection.find({"expires_at": {"$gt": now}, "available": True})
    active = await active_cursor.to_list(length=None)
    if active:
        return active

    # No active shop — create a fresh one
    LOGGER.info("No active shop found. Generating new shop...")
    new_items = []

    # For each pool, sample the required number of characters
    for pool_name, count in WANTED_COUNTS.items():
        if count <= 0:
            continue
        match_query = POOL_QUERIES.get(pool_name, {})
        # Use aggregation with $match + $sample for random picks
        pipeline = [{"$match": match_query}, {"$sample": {"size": count}}]
        try:
            sampled = await collection.aggregate(pipeline).to_list(length=count)
        except Exception:
            # Fallback: simple find + sample in python
            sampled = await collection.find(match_query).to_list(length=None)
            import random as _rnd
            sampled = _rnd.sample(sampled, min(len(sampled), count)) if sampled else []

        # Create shop item documents for each sampled character
        for char_doc in sampled:
            code = _gen_code()
            pool_price_cfg = PRICING.get(pool_name, {"price": 100, "currency": "tokens"})
            doc = {
                "code": code,
                "character": {
                    "id": char_doc.get("id"),
                    "name": char_doc.get("name"),
                    "anime": char_doc.get("anime"),
                    "rarity": char_doc.get("rarity"),
                    "img_url": char_doc.get("img_url"),
                },
                "pool": pool_name,
                "price": pool_price_cfg["price"],
                "currency": pool_price_cfg["currency"],   # 'tokens' or 'coins'
                "available": True,
                "created_at": now,
                "expires_at": _expires_at_now_plus_days(SHOP_TTL_DAYS),
            }
            new_items.append(doc)

    if new_items:
        # insert many
        await daily_shop_collection.insert_many(new_items)
        LOGGER.info("Inserted %d new shop items.", len(new_items))

    active_cursor = daily_shop_collection.find({"expires_at": {"$gt": now}, "available": True})
    return await active_cursor.to_list(length=None)

# ---------- /shop (text preview) ----------
@app.on_message(filters.command("shop") & filters.private)
async def cmd_shop(client: Client, message):
    items = await _generate_shop_if_needed()
    if not items:
        await message.reply_text("🚨 The shop is currently empty. Check back later.")
        return

    # Build a short listing
    lines = ["🛍️ **Current Shop** — updates every 3 days\n"]
    for i, it in enumerate(items):
        ch = it["character"]
        lines.append(f"{i+1}. {ch.get('rarity','')} • **{ch.get('name')}** — `{it['price']}` {it['currency']} — Code: `{it['code']}`")
    lines.append("\n✨ Browse Inline: Type `@YourBotUsername shop` in any chat.")
    await message.reply_text("\n".join(lines), parse_mode="markdown")

# ---------- Inline query (browse items with pictures) ----------
@app.on_inline_query()
async def inline_shop(client: Client, inline_query: InlineQuery):
    q = inline_query.query.strip().lower()
    # We only return results when user types: "shop" or queries starting with "shop"
    if not q or not q.startswith("shop"):
        return

    items = await _generate_shop_if_needed()
    results = []
    for it in items:
        ch = it["character"]
        title = f"{ch.get('rarity','')} • {ch.get('name')}"
        descr = f"Price: {it['price']} {it['currency']}"
        caption = _aesthetic_caption(it)
        try:
            results.append(
                InlineQueryResultPhoto(
                    photo_url=ch.get("img_url") or "",
                    thumb_url=ch.get("img_url") or "",
                    title=title,
                    description=descr,
                    caption=caption,
                    parse_mode="markdown"
                )
            )
        except Exception:
            # skip malformed entries
            continue

    # Answer inline query
    # cache_time=0 so users always see fresh shop (or set >0 to reduce load)
    await inline_query.answer(results=results, cache_time=0, is_personal=True)

# ---------- /buy <code> ----------
@app.on_message(filters.command("buy") & filters.private)
async def cmd_buy(client: Client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("Usage: `/buy <CODE>` — find the code from the inline result or /shop listing.", parse_mode="markdown")
        return

    code = args[1].strip().upper()
    uid = message.from_user.id
    now = _now_utc()

    # Step 1: reserve the item atomically (only if available and not expired)
    reserved = await daily_shop_collection.find_one_and_update(
        {"code": code, "available": True, "expires_at": {"$gt": now}},
        {"$set": {"available": False, "reserved_by": uid, "reserved_at": now}},
        return_document=ReturnDocument.AFTER
    )

    if not reserved:
        await message.reply_text("❌ Item not available or code invalid / expired.")
        return

    price = int(reserved["price"])
    currency = reserved.get("currency", "tokens")
    char = reserved["character"]

    # Step 2: attempt to deduct funds atomically
    user_filter = {"id": uid, currency: {"$gte": price}}
    user_update = {
        "$inc": {currency: -price},
        "$push": {"characters": {
            "_id": ObjectId(),
            "id": char.get("id"),
            "name": char.get("name"),
            "anime": char.get("anime"),
            "rarity": char.get("rarity"),
            "img_url": char.get("img_url"),
            "acquired_at": now
        }}
    }

    updated_user = await user_collection.find_one_and_update(
        user_filter,
        user_update,
        return_document=ReturnDocument.AFTER
    )

    if not updated_user:
        # Insufficient funds — rollback reservation
        await daily_shop_collection.update_one(
            {"code": code, "reserved_by": uid},
            {"$set": {"available": True}, "$unset": {"reserved_by": "", "reserved_at": ""}}
        )
        await message.reply_text(f"💸 Insufficient funds. You need `{price}` {currency} to buy this item.")
        return

    # Step 3: finalize sale
    await daily_shop_collection.update_one(
        {"code": code, "reserved_by": uid},
        {"$set": {"sold_to": uid, "sold_at": now}}
    )

    await message.reply_text(f"🎉 Purchase complete! You bought **{char.get('name')}** for `{price}` {currency}.\nIt was added to your collection.", parse_mode="markdown")

# ---------- Admin helper (optional) ----------
def _is_partner(user_id: int) -> bool:
    if not PARTNER:
        return False
    try:
        s = {int(x) if isinstance(x, str) and x.isdigit() else x for x in PARTNER}
        return int(user_id) in s
    except Exception:
        return False

@app.on_message(filters.command("regenshop") & filters.private)
async def cmd_regenshop(client: Client, message):
    """Force regenerate shop (partner only)"""
    if not _is_partner(message.from_user.id):
        await message.reply_text("⛔ You are not authorized.")
        return
    # delete existing active
    await daily_shop_collection.delete_many({"expires_at": {"$gt": _now_utc()}})
    items = await _generate_shop_if_needed()
    await message.reply_text(f"✅ Shop regenerated with {len(items)} items.")

# End of module
