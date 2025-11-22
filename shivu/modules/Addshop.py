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


# premium_shop.py
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultPhoto,
    InlineQuery
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
PAGE_SIZE = 6        # number of inline cards per page

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

def aesthetic_caption(item, user_balance=None):
    char = item["character"]
    base = (
        f"🛒 **{char.get('name','Unknown')}**\n"
        f"📺 {char.get('anime','Unknown')}\n"
        f"✨ {char.get('rarity','')}\n\n"
        f"💰 Price: `{item['price']}` {item['currency']}\n"
        f"🆔 Code: `{item['code']}`\n"
    )
    if user_balance is not None:
        base += f"\n💵 Your balance: `{user_balance}` {item['currency']}\n"
    # append countdown
    expires_at = item.get("expires_at", shop_expires_at())
    base += f"\n{nice_countdown_text(expires_at)}"
    return base

# -------------------------
# SHOP GENERATION (2-day)
# -------------------------
async def generate_shop_if_needed():
    # cleanup expired
    await daily_shop_collection.delete_many({"expires_at": {"$lte": now()}})
    # active items
    active = await daily_shop_collection.find({"expires_at": {"$gt": now()}}).to_list(length=None)
    if active:
        return active

    # generate fresh items
    new_items = []
    for pool, count in WANTED_COUNTS.items():
        if count <= 0:
            continue
        q = POOL_QUERIES.get(pool, {})
        # sample
        try:
            sampled = await collection.aggregate([{"$match": q}, {"$sample": {"size": count}}]).to_list(length=count)
        except Exception:
            sampled = await collection.find(q).to_list(length=None)
            import random as _r
            sampled = _r.sample(sampled, min(len(sampled), count)) if sampled else []

        for char in sampled:
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
                "price": PRICING.get(pool, {"price": 100, "currency": "tokens"})["price"],
                "currency": PRICING.get(pool, {"price": 100, "currency": "tokens"})["currency"],
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
    # simple button that opens inline shop in current chat
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 OPEN SHOP", switch_inline_query_current_chat="shop.prince")]
    ])
    await message.reply_text("🛒 **Click below to open the Shop**", reply_markup=kb)

# -------------------------
# INLINE QUERY HANDLER (supports pagination & sorting)
# Query format examples:
#  - "shop.prince"                (defaults page=1 sort=default)
#  - "shop.prince page=2"         (page 2)
#  - "shop.prince sort=price_asc" (sorting)
#  - "shop.prince page=1 sort=name"
# -------------------------
def parse_inline_query(q: str):
    # returns dict with page, sort
    page = 1
    sort = "default"
    parts = q.split()
    # accept tokens like page=2 and sort=price_asc
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
    return {"page": page, "sort": sort}

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
        return  # ignore other inline queries

    params = parse_inline_query(q)
    page = params["page"]
    sort_mode = params["sort"]

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
    # get user balance once
    uid = inline_query.from_user.id
    user_doc = await user_collection.find_one({"id": uid}) or {}
    # show each item as a photo result with BUY button
    for it in page_items:
        ch = it["character"]
        price = it["price"]
        currency = it["currency"]
        code = it["code"]
        # build caption including user balance
        user_balance = user_doc.get(currency, 0)
        caption = aesthetic_caption(it, user_balance=user_balance)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 BUY", callback_data=f"buyshop_{code}")]
        ])

        results.append(
            InlineQueryResultPhoto(
                photo_url=ch.get("img_url") or "",
                thumb_url=ch.get("img_url") or "",
                title=f"{ch.get('rarity','')} • {ch.get('name','Unknown')}",
                description=f"{price} {currency}",
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb
            )
        )

    # Navigation / controls card (as last result) — uses switch_inline_query_current_chat to change page/sort
    # Build query templates for next/prev and sorts
    prev_page = max(1, page - 1)
    next_page = min(total_pages, page + 1)
    base_token = "shop.prince"

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
    # Info button (shows page/total & reset)
    # Use a special photo-less InlineQueryResultPhoto with a neutral image or reuse first item's thumbnail if available
    nav_caption = (
        f"📜 Page {page}/{total_pages}  •  Items: {total_items}\n"
        f"{nice_countdown_text(items[0].get('expires_at') if items else shop_expires_at())}\n\n"
        "Use the buttons to change page or sorting."
    )

    # choose a thumbnail for nav (first item or empty)
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

    # Answer inline query
    await inline_query.answer(results=results, cache_time=0, is_personal=True, switch_pm_text="Open Shop", switch_pm_parameter="open_shop")

# -------------------------
# BUY STEP 1 (when user clicks BUY on card)
# - CHECK balance BEFORE showing confirm
# -------------------------
@app.on_callback_query(filters.regex("^buyshop_"))
async def buy_step1(client, cq):
    code = cq.data.split("_", 1)[1]
    uid = cq.from_user.id

    item = await daily_shop_collection.find_one({"code": code})
    if not item:
        return await cq.answer("❌ Item not found or expired.", show_alert=True)

    char = item["character"]
    price = item["price"]
    currency = item["currency"]

    # check if user already owns the character
    already = await user_collection.find_one({"id": uid, "characters.id": char.get("id")})
    if already:
        return await cq.answer("❌ You already own this character.", show_alert=True)

    # check global limit quickly (inform user)
    pool = item.get("pool")
    if pool in GLOBAL_LIMITS:
        count = await daily_shop_collection.count_documents({"character.id": char.get("id"), "sold_to": {"$exists": True}})
        if count >= GLOBAL_LIMITS[pool]:
            return await cq.answer("❌ This character already reached its global limit.", show_alert=True)

    # check user balance
    user = await user_collection.find_one({"id": uid}) or {}
    bal = user.get(currency, 0)

    if bal < price:
        return await cq.answer(f"❌ Not enough {currency}.\nYou have: {bal}\nNeed: {price}", show_alert=True)

    # All good — show confirm/cancel with preview and balances
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirmbuy_{code}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancelbuy_{code}")
        ]
    ])

    caption = (
        f"🛒 **Purchase Confirmation**\n\n"
        f"**{char.get('name')}**\n"
        f"📺 {char.get('anime')}\n"
        f"✨ {char.get('rarity')}\n\n"
        f"💰 Price: `{price}` {currency}\n"
        f"💵 Your balance: `{bal}` {currency}\n\n"
        "Proceed with purchase?"
    )

    # reply in the chat where the inline result was inserted
    await cq.message.reply_photo(photo=char.get("img_url"), caption=caption, reply_markup=kb)
    await cq.answer()

# -------------------------
# BUY STEP 2 (Confirm handler)
# - Deduct balance atomically
# - Add character to user's collection
# - Track sold_to (append uid but do not remove item)
# -------------------------
@app.on_callback_query(filters.regex("^confirmbuy_"))
async def buy_confirm(client, cq):
    code = cq.data.split("_", 1)[1]
    uid = cq.from_user.id
    now_dt = now()

    item = await daily_shop_collection.find_one({"code": code})
    if not item:
        return await cq.answer("❌ Item expired.", show_alert=True)

    char = item["character"]
    char_id = char.get("id")
    pool = item.get("pool")
    price = item.get("price")
    currency = item.get("currency")

    # per-user ownership check (again)
    already = await user_collection.find_one({"id": uid, "characters.id": char_id})
    if already:
        return await cq.message.edit_caption("❌ You already own this character.")

    # global limit check
    if pool in GLOBAL_LIMITS:
        count = await daily_shop_collection.count_documents({"character.id": char_id, "sold_to": {"$exists": True}})
        if count >= GLOBAL_LIMITS[pool]:
            return await cq.message.edit_caption("❌ Global purchase limit reached for this character.")

    # Deduct funds atomically
    user_filter = {"id": uid, currency: {"$gte": price}}
    updated_user = await user_collection.find_one_and_update(
        user_filter,
        {"$inc": {currency: -price}},
        return_document=ReturnDocument.AFTER
    )

    if not updated_user:
        # not enough balance
        return await cq.message.edit_caption(f"❌ Insufficient {currency} to complete purchase.")

    # add character to user's characters array
    await user_collection.update_one(
        {"id": uid},
        {"$push": {"characters": {
            "_id": ObjectId(),
            "id": char_id,
            "name": char.get("name"),
            "anime": char.get("anime"),
            "rarity": char.get("rarity"),
            "img_url": char.get("img_url"),
            "acquired_at": now_dt
        }}}
    )

    # append to sold_to for tracking (do not hide/remove item)
    await daily_shop_collection.update_one(
        {"code": code},
        {"$push": {"sold_to": uid}}
    )

    # final UX: delete confirmation message and post purchased photo
    try:
        await cq.message.delete()
    except:
        pass

    await cq.message.reply_photo(
        photo=char.get("img_url"),
        caption=(
            f"🎉 **Successfully Purchased {char.get('name')}!**\n\n"
            f"💰 Spent `{price}` {currency}\n"
            f"✨ Added to your collection."
        )
    )
    await cq.answer()

# -------------------------
# CANCEL HANDLER
# -------------------------
@app.on_callback_query(filters.regex("^cancelbuy_"))
async def buy_cancel(client, cq):
    code = cq.data.split("_", 1)[1]
    try:
        await cq.message.edit_caption("❌ Purchase cancelled.")
    except:
        # fallback: reply a small message
        await cq.message.reply_text("❌ Purchase cancelled.")
    await cq.answer()

# -------------------------
# OPTIONAL ADMIN: force regenerate shop
# -------------------------
@app.on_message(filters.command("regenshop") & filters.private)
async def regen_shop_cmd(client, message):
    # restrict to bot owner/partner if you want (not enforced here)
    await daily_shop_collection.delete_many({"expires_at": {"$gt": now()}})
    items = await generate_shop_if_needed()
    await message.reply_text(f"✅ Shop regenerated: {len(items)} items.")
