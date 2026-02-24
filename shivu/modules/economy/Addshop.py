# shop_pyrogram.py
# Full Pyrogram-only conversion of your shop system
# Requires: pyrogram, motor (or an async MongoDB driver exposed via your `shivu` module)
# Place in the same environment where `shivu` definitions exist.

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
from contextlib import suppress
from pyrogram.errors import MessageNotModified
import uuid
import math
import random
import logging

# -------------------------
# IMPORT YOUR APP & DB (from shivu)
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
SHOP_TTL_HOURS = 24  # 2 days reset
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


def build_dm_confirm_link(bot_username: str, code: str, owner_id: int, session: str):
    payload = f"shopconfirm_{code}_{owner_id}_{session}"
    return f"https://t.me/{bot_username}?start={payload}"

def shop_expires_at():
    return now() + timedelta(hours=SHOP_TTL_HOURS)

def nice_countdown_text(expires_at):
    delta = expires_at - now()
    if delta.total_seconds() <= 0:
        return "⏳ 𝙍𝙚𝙨𝙚𝙩 𝙞𝙣: 0h 0m\n✨ 𝙎𝙝𝙤𝙥 𝙧𝙚𝙛𝙧𝙚𝙨𝙝𝙚𝙨 𝙚𝙫𝙚𝙧𝙮 2 𝙙𝙖𝙮𝙨!"
    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)
    return f"⏳ 𝙍𝙚𝙨𝙚𝙩 𝙞𝙣: {hours}h {minutes}m  \n✨ 𝙎𝙝𝙤𝙥 𝙧𝙚𝙛𝙧𝙚𝙨𝙝𝙚𝙨 𝙚𝙫𝙚𝙧𝙮 𝙙𝙖𝙮!"

def normalize_currency_field(currency_str):
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

def parse_inline_query(q: str):
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
                except Exception:
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


async def safe_callback_answer(cq, text=None, show_alert=False):
    with suppress(Exception):
        await cq.answer(text=text, show_alert=show_alert)

# -------------------------
# SHOP GENERATION (2-day)
# -------------------------
async def generate_shop_if_needed():
    # Remove expired
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
            sampled = random.sample(sampled, min(len(sampled), count)) if sampled else []

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
@app.on_message(filters.command(["shop", "shopmenu"]))
async def cmd_shop_entry(client: Client, message):
    owner_id = message.from_user.id
    session = gen_session_id()
    starter = f"shop.prince owner={owner_id} session={session}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 OPEN SHOP", switch_inline_query_current_chat=starter)]
    ])
    await message.reply_text("🛒 **Click below to open the Shop (semi-private controls)**", reply_markup=kb)

# -------------------------
# INLINE QUERY HANDLER
# -------------------------

async def handle_shop_inline(client: Client, inline_query: InlineQuery):
    q = inline_query.query.strip()
    if not q.lower().startswith("shop.prince"):
        return

    params = parse_inline_query(q)
    page = params["page"]
    sort_mode = params["sort"]
    owner = params["owner"]
    session = params["session"]

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
            title="🔧 Shop Controls",
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
    try:
        data = cq.data  # e.g. buyshop_CODE_owner_session
        parts = data.split("_", 3)
        if len(parts) < 4:
            await safe_callback_answer(cq, "Invalid request.", show_alert=True)
            return
        _, code, owner_str, session = parts
        try:
            owner_id = int(owner_str)
        except Exception:
            owner_id = None

        requester = cq.from_user.id

        # Semi-strict: allow viewing but only owner can proceed to buy
        if requester != owner_id:
            await safe_callback_answer(cq, "❌ You cannot buy from someone else's shop.", show_alert=True)
            return

        item = await daily_shop_collection.find_one({"code": code})
        if not item:
            await safe_callback_answer(cq, "❌ Item not found or expired.", show_alert=True)
            return

        char = item["character"]
        price = item["price"]
        currency = item.get("currency", "tokens")
        currency_field = normalize_currency_field(currency) or "tokens"

        # check ownership
        already = await user_collection.find_one({"id": requester, "characters.id": char.get("id")})
        if already:
            await safe_callback_answer(cq, "❌ You already own this character.", show_alert=True)
            return

        # global limit quick check
        pool = item.get("pool")
        if pool in GLOBAL_LIMITS:
            count = await daily_shop_collection.count_documents({"character.id": char.get("id"), "sold_to.0": {"$exists": True}})
            if count >= GLOBAL_LIMITS[pool]:
                await safe_callback_answer(cq, "❌ This character already reached its global limit.", show_alert=True)
                return

        # balance check
        user = await user_collection.find_one({"id": requester}) or {}
        bal = user.get(currency_field, 0)
        if bal < price:
            await safe_callback_answer(cq, f"❌ Not enough {currency_field}.\nYou have: {bal}\nNeed: {price}", show_alert=True)
            return

        # Build confirm/cancel buttons — include owner & session to keep chain validated
        cb_confirm = f"confirmbuy_{code}_{owner_str}_{session}"
        cb_cancel = f"cancelbuy_{code}_{owner_str}_{session}"
        confirm_kb = InlineKeyboardMarkup([
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

        bot_username = (await client.get_me()).username
        dm_link = build_dm_confirm_link(bot_username, code, requester, session)

        await client.send_photo(chat_id=requester, photo=char.get("img_url"), caption=caption, reply_markup=confirm_kb)

        inline_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 Open DM to Confirm", url=dm_link)]
        ])
        await cq.edit_message_caption(
            caption=(
                f"✅ **Confirmation sent in DM**\n\n"
                f"Character: **{char.get('name')}**\n"
                f"💰 Price: `{price}` {currency_field}\n\n"
                "Tap the button below and confirm purchase in bot PM."
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=inline_kb,
        )
        await safe_callback_answer(cq, "Check DM for confirmation.")
    except MessageNotModified:
        await safe_callback_answer(cq, "Already updated.")
    except Exception:
        logging.exception("Failed to send confirmation photo")
        try:
            await cq.edit_message_caption(
                caption=(
                    "⚠️ **Unable to auto-send confirmation in DM.**\n\n"
                    "Open bot PM and tap below to continue purchase."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📩 Open DM", url=dm_link)]
                ]),
            )
        except Exception:
            pass
        await safe_callback_answer(cq, "❌ Failed to show confirmation. Open bot PM.", show_alert=True)


@app.on_message(filters.command("start") & filters.private)
async def shop_start_confirm(client: Client, message):
    if len(message.command) < 2:
        return

    payload = message.command[1]
    if not payload.startswith("shopconfirm_"):
        return

    parts = payload.split("_", 3)
    if len(parts) < 4:
        return await message.reply_text("❌ Invalid confirmation link.")

    _, code, owner_str, session = parts
    try:
        owner_id = int(owner_str)
    except Exception:
        return await message.reply_text("❌ Invalid confirmation owner.")

    if message.from_user.id != owner_id:
        return await message.reply_text("❌ This confirmation link belongs to another user.")

    item = await daily_shop_collection.find_one({"code": code})
    if not item:
        return await message.reply_text("❌ Item not found or expired.")

    char = item["character"]
    price = item["price"]
    currency = item.get("currency", "tokens")
    currency_field = normalize_currency_field(currency) or "tokens"

    user = await user_collection.find_one({"id": owner_id}) or {}
    bal = user.get(currency_field, 0)

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

    try:
        await message.reply_photo(photo=char.get("img_url"), caption=caption, reply_markup=kb)
    except Exception:
        await message.reply_text(caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# -------------------------
# BUY STEP 2 (Confirm handler) - semi-strict owner check
# -------------------------
@app.on_callback_query(filters.regex(r"^confirmbuy_"))
async def buy_confirm(client, cq):
    try:
        data = cq.data
        parts = data.split("_", 3)
        if len(parts) < 4:
            await safe_callback_answer(cq, "Invalid request.", show_alert=True)
            return
        _, code, owner_str, session = parts
        try:
            owner_id = int(owner_str)
        except Exception:
            owner_id = None

        requester = cq.from_user.id
        if requester != owner_id:
            await safe_callback_answer(cq, "❌ This confirmation belongs to another user.", show_alert=True)
            return

        item = await daily_shop_collection.find_one({"code": code})
        if not item:
            await safe_callback_answer(cq, "❌ Item expired.", show_alert=True)
            return

        char = item["character"]
        char_id = char.get("id")
        pool = item.get("pool")
        price = item.get("price")
        currency = item.get("currency", "tokens")
        currency_field = normalize_currency_field(currency) or "tokens"

        # ownership check
        already = await user_collection.find_one({"id": requester, "characters.id": char_id})
        if already:
            await safe_callback_answer(cq, "❌ You already own this character.", show_alert=True)
            return

        # global limit check
        if pool in GLOBAL_LIMITS:
            count = await daily_shop_collection.count_documents({"character.id": char_id, "sold_to.0": {"$exists": True}})
            if count >= GLOBAL_LIMITS[pool]:
                await safe_callback_answer(cq, "❌ Global purchase limit reached for this character.", show_alert=True)
                return

        # deduct funds atomically
        user_filter = {"id": requester, currency_field: {"$gte": price}}
        updated_user = await user_collection.find_one_and_update(
            user_filter,
            {"$inc": {currency_field: -price}},
            return_document=ReturnDocument.AFTER
        )

        if not updated_user:
            await safe_callback_answer(cq, f"❌ Insufficient {currency_field} to complete purchase.", show_alert=True)
            return

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
        await client.send_photo(
            chat_id=requester,
            photo=char.get("img_url"),
            caption=(
                f"🎉 **Successfully Purchased {char.get('name')}!**\n\n"
                f"💰 Spent `{price}` {currency_field}\n"
                f"✨ Added to your collection."
            )
        )
        await safe_callback_answer(cq, "✅ Purchase completed.")
    except Exception:
        await safe_callback_answer(cq, "✅ Purchase completed. Check your messages.", show_alert=True)

# -------------------------
# CANCEL (semi-strict)
# -------------------------
@app.on_callback_query(filters.regex(r"^cancelbuy_"))
async def buy_cancel(client, cq):
    try:
        data = cq.data
        parts = data.split("_", 3)
        if len(parts) < 4:
            await safe_callback_answer(cq, "Invalid request.", show_alert=True)
            return
        _, code, owner_str, session = parts
        try:
            owner_id = int(owner_str)
        except Exception:
            owner_id = None

        requester = cq.from_user.id
        if requester != owner_id:
            await safe_callback_answer(cq, "❌ You cannot cancel someone else's purchase.", show_alert=True)
            return

        await client.send_message(chat_id=requester, text="❌ Purchase cancelled.")
        await safe_callback_answer(cq, "Purchase cancelled.")
    except Exception:
        await safe_callback_answer(cq, "❌ Purchase cancelled.", show_alert=True)

# -------------------------
# OPTIONAL: force regenerate shop (owner only if you choose to restrict)
# -------------------------
@app.on_message(filters.command("regenshop") & filters.private)
async def regen_shop_cmd(client, message):
    await daily_shop_collection.delete_many({"expires_at": {"$gt": now()}})
    items = await generate_shop_if_needed()
    await message.reply_text(f"✅ Shop regenerated: {len(items)} items.")

# End of file
