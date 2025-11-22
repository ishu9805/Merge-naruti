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

# Assuming these are defined elsewhere in your code
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

from pyrogram.enums import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from bson import ObjectId
from shivu import shops_collectionps as shops_collection, user_collectionps as user_collection, applicationps as application
import logging

# shop_semi_strict.py
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultPhoto,
    InlineQuery,
)
from pyrogram.enums import ParseMode

from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import ReturnDocument
import uuid
import math

# -------------------------
# IMPORT YOUR APP & DB
# -------------------------
from shivu import (
    shivuups as app,                 # Pyrogram Client instance
    collectionps as collection,      # main characters collection
    daily_shopps as daily_shop_collection,  # shop collection
    user_collectionps as user_collection
)

# -------------------------
# CONFIG
# -------------------------
SHOP_TTL_HOURS = 48  # 2 days reset
PAGE_SIZE = 6

PRICING = {
    "events": {"price": 1000, "currency": "tokens"},
    "special": {"price": 50, "currency": "tokens"},
    "limited": {"price": 150, "currency": "tokens"},
    "premium": {"price": 50000, "currency": "coins"},
    "seasonal": {"price": 300, "currency": "tokens"},
}

WANTED_COUNTS = {
    "events": 1,
    "special": 1,
    "limited": 1,
    "premium": 2,
    "seasonal": 1,
}

POOL_QUERIES = {
    "events": {"rarity": {"$regex": r"(Events|🧧|Event)", "$options": "i"}},
    "special": {"rarity": {"$regex": r"(Special|💮)", "$options": "i"}},
    "limited": {"rarity": {"$regex": r"(Limited Edition|🔮|Limited)", "$options": "i"}},
    "premium": {"rarity": {"$regex": r"(Premium|💸)", "$options": "i"}},
    "seasonal": {"$or": [
        {"rarity": {"$regex": r"(Summer|Winter|Celestial|Valentine|Halloween|Christmas)", "$options": "i"}}
    ]},
}

GLOBAL_LIMITS = {
    "premium": 5,
    "events": 3,
    "seasonal": 10
}

# -------------------------
# HELPERS
# -------------------------
def now():
    return datetime.utcnow()

def gen_code():
    return uuid.uuid4().hex[:8].upper()

def gen_session_id():
    return uuid.uuid4().hex[:6]

def shop_expires_at():
    return now() + timedelta(hours=SHOP_TTL_HOURS)

def nice_countdown_text(expires_at):
    # Style C: ultra stylish anime style
    delta = expires_at - now()
    if delta.total_seconds() <= 0:
        return "⏳ 𝙍𝙚𝙨𝙚𝙩 𝙞𝙣: 0h 0m\n✨ 𝙎𝙝𝙤𝙥 𝙧𝙚𝙛𝙧𝙚𝙨𝙝𝙚𝙨 𝙚𝙫𝙚𝙧𝙮 2 𝙙𝙖𝙮𝙨!"
    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)
    return f"⏳ 𝙍𝙚𝙨𝙚𝙩 𝙞𝙣: {hours}h {minutes}m  \n✨ 𝙎𝙝𝙤𝙥 𝙧𝙚𝙛𝙧𝙚𝙨𝙝𝙚𝙨 𝙚𝙫𝙚𝙧𝙮 2 𝙙𝙖𝙮𝙨!"

def normalize_currency_field(currency_str):
    """
    Map currency descriptor to user field name.
    Accepts 'coins' or 'tokens' (case-insensitive).
    """
    if not currency_str:
        return None
    c = currency_str.lower()
    if c in ("coins", "coin"):
        return "coins"
    if c in ("tokens", "token"):
        return "tokens"
    return None

def aesthetic_caption(item, user_balance=None):
    char = item["character"]
    base = (
        f"🛒 **{char.get('name','Unknown')}**\n"
        f"📺 {char.get('anime','Unknown')}\n"
        f"✨ {char.get('rarity','')}\n\n"
        f"💰 Price: `{item['price']}` {item.get('currency','tokens')}\n"
        f"🆔 Code: `{item['code']}`\n"
    )
    if user_balance is not None:
        base += f"\n💵 Your balance: `{user_balance}` {item.get('currency','')}\n"
    expires_at = item.get("expires_at", shop_expires_at())
    base += f"\n{nice_countdown_text(expires_at)}"
    return base

# -------------------------
# SHOP GENERATION (2-day)
# -------------------------
async def generate_shop_if_needed():
    await daily_shop_collection.delete_many({"expires_at": {"$lte": now()}})
    active = await daily_shop_collection.find({"expires_at": {"$gt": now()}}).to_list(length=None)
    if active:
        return active

    new_items = []
    for pool, count in WANTED_COUNTS.items():
        if count <= 0:
            continue
        q = POOL_QUERIES.get(pool, {})
        try:
            sampled = await collection.aggregate([{"$match": q}, {"$sample": {"size": count}}]).to_list(length=count)
        except Exception:
            sampled = await collection.find(q).to_list(length=None)
            import random as _r
            sampled = _r.sample(sampled, min(len(sampled), count)) if sampled else []

        for char in sampled:
            currency = PRICING.get(pool, {"price": 100, "currency": "tokens"})["currency"]
            norm_cur = normalize_currency_field(currency) or "tokens"
            new_items.append({
                "code": gen_code(),
                "character": {
                    "id": char.get("id"),
                    "name": char.get("name"),
                    "anime": char.get("anime"),
                    "rarity": char.get("rarity"),
                    "img_url": char.get("img_url")
                },
                "pool": pool,
                "price": PRICING.get(pool, {"price": 100})["price"],
                "currency": norm_cur,
                "expires_at": shop_expires_at(),
                "sold_to": []
            })
    if new_items:
        await daily_shop_collection.insert_many(new_items)
    return await daily_shop_collection.find({"expires_at": {"$gt": now()}}).to_list(length=None)

# -------------------------
# SHOP ENTRY (command)
# -------------------------
@app.on_message(filters.command("shop"))
async def cmd_shop_entry(client, message):
    # This opens inline shop prepopulated for the opener with a session id
    owner_id = message.from_user.id
    session = gen_session_id()
    # Pre-fill the inline query with owner/session so callback_data can be owner-verified
    starter = f"shop.prince owner={owner_id} session={session}"
    kb = InlineKeyboardMarkup([
        # switch_inline_query_current_chat will open inline composer in same chat
        [InlineKeyboardButton("🛒 OPEN SHOP", switch_inline_query_current_chat=starter)]
    ])
    await message.reply_text("🛒 **Click below to open the Shop (semi-private controls)**", reply_markup=kb)

# -------------------------
# INLINE QUERY HANDLER (supports pagination & sorting)
# Query format examples:
#  - "shop.prince owner=123 session=abc"                (defaults page=1 sort=default)
#  - "shop.prince owner=123 session=abc page=2"
#  - "shop.prince owner=123 session=abc sort=price_asc"
# -------------------------
def parse_inline_query(q: str):
    # returns dict with page, sort, owner, session
    page = 1
    sort = "default"
    owner = None
    session = None
    parts = q.split()
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            if k == "page":
                try:
                    page = max(1, int(v))
                except:
                    page = 1
            elif k == "sort":
                sort = v
            elif k == "owner":
                owner = v
            elif k == "session":
                session = v
    return {"page": page, "sort": sort, "owner": owner, "session": session}

def sort_items_list(items, sort_key):
    if sort_key == "price_asc":
        return sorted(items, key=lambda x: x.get("price", 0))
    if sort_key == "price_desc":
        return sorted(items, key=lambda x: -x.get("price", 0))
    if sort_key == "name":
        return sorted(items, key=lambda x: x["character"].get("name","").lower())
    if sort_key == "rarity":
        return sorted(items, key=lambda x: x["character"].get("rarity",""))
    return items

@app.on_inline_query()
async def handle_shop_inline(client: Client, inline_query: InlineQuery):
    q = inline_query.query.strip()
    if not q.lower().startswith("shop.prince"):
        return

    params = parse_inline_query(q)
    page = params["page"]
    sort_mode = params["sort"]
    owner = params["owner"]
    session = params["session"]

    # Ensure owner/session exist — fallback to inline opener if missing
    if not owner:
        owner = str(inline_query.from_user.id)
    if not session:
        session = gen_session_id()

    items = await generate_shop_if_needed()
    total_items = len(items)
    items = sort_items_list(items, sort_mode)

    total_pages = max(1, math.ceil(total_items / PAGE_SIZE))
    if page > total_pages:
        page = total_pages

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = items[start:end]

    results = []
    uid = inline_query.from_user.id
    user_doc = await user_collection.find_one({"id": uid}) or {}

    for it in page_items:
        ch = it["character"]
        price = it["price"]
        currency_field = it.get("currency", "tokens")
        user_balance = user_doc.get(currency_field, 0)
        caption = aesthetic_caption(it, user_balance=user_balance)

        # callback_data includes owner and session so we can semi-lock BUY/confirm/cancel
        cb_buy = f"buyshop_{it['code']}_{owner}_{session}"
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 BUY", callback_data=cb_buy)]
        ])

        results.append(
            InlineQueryResultPhoto(
                photo_url=ch.get("img_url") or "",
                thumb_url=ch.get("img_url") or "",
                title=f"{ch.get('rarity','')} • {ch.get('name','Unknown')}",
                description=f"{price} {currency_field}",
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )
        )

    prev_page = max(1, page - 1)
    next_page = min(total_pages, page + 1)
    base_token = f"shop.prince owner={owner} session={session}"

    nav_buttons = [
        InlineKeyboardButton("⏮ Prev", switch_inline_query_current_chat=f"{base_token} page={prev_page} sort={sort_mode}"),
        InlineKeyboardButton("⏭ Next", switch_inline_query_current_chat=f"{base_token} page={next_page} sort={sort_mode}")
    ]
    sort_row = [
        InlineKeyboardButton("Sort: Price↑", switch_inline_query_current_chat=f"{base_token} page=1 sort=price_asc"),
        InlineKeyboardButton("Sort: Price↓", switch_inline_query_current_chat=f"{base_token} page=1 sort=price_desc")
    ]
    sort_row2 = [
        InlineKeyboardButton("Sort: Name", switch_inline_query_current_chat=f"{base_token} page=1 sort=name"),
        InlineKeyboardButton("Sort: Rarity", switch_inline_query_current_chat=f"{base_token} page=1 sort=rarity")
    ]

    nav_caption = (
        f"📜 Page {page}/{total_pages}  •  Items: {total_items}\n"
        f"{nice_countdown_text(items[0].get('expires_at') if items else shop_expires_at())}\n\n"
        "Use the buttons to change page or sorting."
    )

    thumb = items[0]["character"].get("img_url") if items else ""
    results.append(
        InlineQueryResultPhoto(
            photo_url=thumb or "https://telegra.ph/file/placeholder.png",
            thumb_url=thumb or "https://telegra.ph/file/placeholder.png",
            title=f"🔧 Shop Controls",
            description=f"Page {page}/{total_pages}  •  Sort: {sort_mode}",
            caption=nav_caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([nav_buttons, sort_row, sort_row2])
        )
    )

    await inline_query.answer(results=results, cache_time=0, is_personal=True, switch_pm_text="Open Shop", switch_pm_parameter="open_shop")

# -------------------------
# BUY STEP 1 (BUY button click) - semi-strict owner check
# -------------------------
@app.on_callback_query(filters.regex(r"^buyshop_"))
async def buy_step1(client, cq):
    data = cq.data  # e.g. buyshop_CODE_owner_session
    parts = data.split("_", 3)
    if len(parts) < 4:
        return await cq.answer("Invalid request.", show_alert=True)
    _, code, owner_str, session = parts
    try:
        owner_id = int(owner_str)
    except:
        owner_id = None

    requester = cq.from_user.id

    # Semi-strict: allow viewing but only owner can proceed to buy
    if requester != owner_id:
        return await cq.answer("❌ You cannot buy from someone else's shop.", show_alert=True)

    # Now we (owner) can proceed
    item = await daily_shop_collection.find_one({"code": code})
    if not item:
        return await cq.answer("❌ Item not found or expired.", show_alert=True)

    char = item["character"]
    price = item["price"]
    currency = item.get("currency", "tokens")
    currency_field = normalize_currency_field(currency) or "tokens"

    # check ownership
    already = await user_collection.find_one({"id": requester, "characters.id": char.get("id")})
    if already:
        return await cq.answer("❌ You already own this character.", show_alert=True)

    # global limit quick check
    pool = item.get("pool")
    if pool in GLOBAL_LIMITS:
        count = await daily_shop_collection.count_documents({"character.id": char.get("id"), "sold_to": {"$exists": True}})
        if count >= GLOBAL_LIMITS[pool]:
            return await cq.answer("❌ This character already reached its global limit.", show_alert=True)

    # balance check
    user = await user_collection.find_one({"id": requester}) or {}
    bal = user.get(currency_field, 0)
    if bal < price:
        return await cq.answer(f"❌ Not enough {currency_field}.\nYou have: {bal}\nNeed: {price}", show_alert=True)

    # Build confirm/cancel buttons — include owner & session to keep chain validated
    cb_confirm = f"confirmbuy_{code}_{owner_str}_{session}"
    cb_cancel = f"cancelbuy_{code}_{owner_str}_{session}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data=cb_confirm),
         InlineKeyboardButton("❌ Cancel", callback_data=cb_cancel)]
    ])

    caption = (
        f"🛒 **Purchase Confirmation**\n\n"
        f"**{char.get('name')}**\n"
        f"📺 {char.get('anime')}\n"
        f"✨ {char.get('rarity')}\n\n"
        f"💰 Price: `{price}` {currency_field}\n"
        f"💵 Your balance: `{bal}` {currency_field}\n\n"
        "Proceed with purchase?"
    )

    # cq.message may be None for inline - always send to user DM
    try:
        await client.send_photo(chat_id=requester, photo=char.get("img_url"), caption=caption, reply_markup=kb)
        await cq.answer()
    except Exception as e:
        await cq.answer("❌ Failed to show confirmation. Try in PM.", show_alert=True)

# -------------------------
# BUY STEP 2 (Confirm handler) - semi-strict owner check
# -------------------------
@app.on_callback_query(filters.regex(r"^confirmbuy_"))
async def buy_confirm(client, cq):
    data = cq.data
    parts = data.split("_", 3)
    if len(parts) < 4:
        return await cq.answer("Invalid request.", show_alert=True)
    _, code, owner_str, session = parts
    try:
        owner_id = int(owner_str)
    except:
        owner_id = None

    requester = cq.from_user.id
    # only owner can confirm
    if requester != owner_id:
        return await cq.answer("❌ This confirmation belongs to another user.", show_alert=True)

    item = await daily_shop_collection.find_one({"code": code})
    if not item:
        return await cq.answer("❌ Item expired.", show_alert=True)

    char = item["character"]
    char_id = char.get("id")
    pool = item.get("pool")
    price = item.get("price")
    currency = item.get("currency", "tokens")
    currency_field = normalize_currency_field(currency) or "tokens"

    # ownership check
    already = await user_collection.find_one({"id": requester, "characters.id": char_id})
    if already:
        return await cq.answer("❌ You already own this character.", show_alert=True)

    # global limit check
    if pool in GLOBAL_LIMITS:
        count = await daily_shop_collection.count_documents({"character.id": char_id, "sold_to": {"$exists": True}})
        if count >= GLOBAL_LIMITS[pool]:
            return await cq.answer("❌ Global purchase limit reached for this character.", show_alert=True)

    # deduct funds atomically
    user_filter = {"id": requester, currency_field: {"$gte": price}}
    updated_user = await user_collection.find_one_and_update(
        user_filter,
        {"$inc": {currency_field: -price}},
        return_document=ReturnDocument.AFTER
    )

    if not updated_user:
        return await cq.answer(f"❌ Insufficient {currency_field} to complete purchase.", show_alert=True)

    # add character to user's characters array
    await user_collection.update_one(
        {"id": requester},
        {"$push": {"characters": {
            "_id": ObjectId(),
            "id": char_id,
            "name": char.get("name"),
            "anime": char.get("anime"),
            "rarity": char.get("rarity"),
            "img_url": char.get("img_url"),
            "acquired_at": now()
        }}}
    )

    # append sold_to only if not already present
    await daily_shop_collection.update_one(
        {"code": code, "sold_to": {"$ne": requester}},
        {"$push": {"sold_to": requester}}
    )

    # Send success message to owner
    try:
        await client.send_photo(
            chat_id=requester,
            photo=char.get("img_url"),
            caption=(
                f"🎉 **Successfully Purchased {char.get('name')}!**\n\n"
                f"💰 Spent `{price}` {currency_field}\n"
                f"✨ Added to your collection."
            )
        )
        await cq.answer()
    except:
        await cq.answer("✅ Purchase completed. Check your messages.", show_alert=True)

# -------------------------
# CANCEL (semi-strict)
# -------------------------
@app.on_callback_query(filters.regex(r"^cancelbuy_"))
async def buy_cancel(client, cq):
    data = cq.data
    parts = data.split("_", 3)
    if len(parts) < 4:
        return await cq.answer("Invalid request.", show_alert=True)
    _, code, owner_str, session = parts
    try:
        owner_id = int(owner_str)
    except:
        owner_id = None

    requester = cq.from_user.id
    if requester != owner_id:
        return await cq.answer("❌ You cannot cancel someone else's purchase.", show_alert=True)

    # inform owner in private chat
    try:
        await client.send_message(chat_id=requester, text="❌ Purchase cancelled.")
        await cq.answer()
    except:
        await cq.answer("❌ Purchase cancelled.", show_alert=True)

# -------------------------
# OPTIONAL: force regenerate shop (owner only is not enforced here, add check if you want)
# -------------------------
@app.on_message(filters.command("regenshop") & filters.private)
async def regen_shop_cmd(client, message):
    await daily_shop_collection.delete_many({"expires_at": {"$gt": now()}})
    items = await generate_shop_if_needed()
    await message.reply_text(f"✅ Shop regenerated: {len(items)} items.")
