# send_characters_stylish.py
import asyncio
import logging
from typing import Any, Dict, List, Optional

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode   # ✅ NEW

# Use your bot import and DB collection
from shivu import shivuups as app, collectionps as collection

# CONFIG
CHANNEL_ID: int = -1003295207951
OWNER_ID: int = 8535832693
DELAY_BETWEEN_MESSAGES: float = 2.0
PROGRESS_UPDATE_EVERY: int = 50

# logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# ---------- TYPE & RARITY DATA ----------
TYPE_EMOJIS = {
    "Football": "⚽", "Basketball": "🏀", "Cheerleader": "🎊", "Summer": "🏖",
    "Winter": "☃️", "Halloween": "🎃", "Christmas": "🎄", "Saree": "🥻",
    "Pirate": "🏴‍☠️", "Royalty": "👑", "Officer": "🚨", "Kimono": "👘",
    "Bikini": "👙", "School": "🎒", "Egypt": "🏜", "Serena": "🎀",
    "Wedding": "💍", "Doctor": "🩺", "GYM": "💪", "Maid": "🧹",
    "Bunny": "🐰", "Valentine": "💝", "Volleyball": "🏐", "Drunk": "🍷",
    "Assembly": "🎩", "Coloured": "🎨", "Police": "🚓", "Nurses": "💉",
    "Toxic": "🦠", "Chinese New Year": "🧧", "Angelic": "🪽", 
    "Chocolates": "🍫", "+18": "🔞", "Cross-Verse": "🧬", "Chibi": "👶",
    "Treasure": "🪙"
}

RARITY_BANNERS = {
    1: "╔══ 💠 𝘾𝙤𝙢𝙢𝙤𝙣 💠 ══╗",
    2: "╔══ ✦ 𝙍𝙖𝙧𝙚 ✦ ══╗",
    3: "💫 𝐋𝐄𝐆𝐄𝐍𝐃𝐀𝐑𝐘 𝐃𝐑𝐎𝐏 💫",
    4: "〔 🌱 𝙈𝙚𝙙𝙞𝙪𝙢 𝙏𝙞𝙚𝙧 🌱 〕",
    5: "✿ 𝐒𝐩𝐞𝐜𝐢𝐚𝐥 𝐄𝐝𝐢𝐭𝐢𝐨𝐧 ✿",
    6: "🔮 𝐋𝐢𝐦𝐢𝐭𝐞𝐝 𝐄𝐝𝐢𝐭𝐢𝐨𝐧 🔮",
    7: "👑 𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐄𝐃𝐈𝐓𝐈𝐎𝐍 👑",
    8: "🌤 𝐒𝐮𝐦𝐦𝐞𝐫 𝐄𝐱𝐜𝐥𝐮𝐬𝐢𝐯𝐞 🌤",
    9: "🌌 𝐂𝐄𝐋𝐄𝐒𝐓𝐈𝐀𝐋 𝐓𝐈𝐄𝐑 🌌",
    10: "❄️ 𝐖𝐈𝐍𝐓𝐄𝐑 𝐄𝐗𝐂𝐋𝐔𝐒𝐈𝐕𝐄 ❄️",
    11: "💝 𝐕𝐚𝐥𝐞𝐧𝐭𝐢𝐧𝐞 𝐄𝐝𝐢𝐭𝐢𝐨𝐧 💝",
    12: "🎃 𝐇𝐚𝐥𝐥𝐨𝐰𝐞𝐞𝐧 𝐒𝐩𝐞𝐜𝐢𝐚𝐥 🎃",
    13: "🎄 𝐂𝐡𝐫𝐢𝐬𝐭𝐦𝐚𝐬 𝐌𝐚𝐠𝐢𝐜 🎄",
    14: "🪐 𝙊𝙈𝙉𝙄𝙑𝙀𝙍𝙎𝘼𝙇 𝙁𝙊𝙍𝘾𝙀 🪐",
    15: "🎭 𝐂𝐎𝐒𝐏𝐋𝐀𝐘 𝐌𝐀𝐒𝐓𝐄𝐑 🎭",
    16: "🧧 𝙀𝙑𝙀𝙉𝙏𝙎 𝐄𝐃𝐈𝐓𝐈𝐎𝐍 🧧",
    17: "🎖 𝐀𝐏𝐄𝐗 𝐀𝐔𝐂𝐓𝐈𝐎𝐍 𝐓𝐈𝐄𝐑 🎖",
    18: "🍑 𝐄𝐂𝐂𝐇𝐈𝐈 𝐄𝐃𝐈𝐓𝐈𝐎𝐍 🍑",
    19: "☠️ 𝐃𝐈𝐕𝐈𝐍𝐄 𝐁𝐋𝐄𝐒𝐒𝐄𝐃 ☠️",
    20: "☔ 𝐌𝐎𝐍𝐒𝐎𝐎𝐍 𝐄𝐃𝐈𝐓𝐈𝐎𝐍 ☔",
    21: "🪸 𝐀𝐪𝐮𝐚𝐭𝐢𝐜 𝐓𝐞𝐦𝐩𝐥𝐚𝐭𝐞 🪸",
    22: "🎨 𝐀𝐫𝐭𝐢𝐬𝐭𝐢𝐜 𝐄𝐱𝐜𝐥𝐮𝐬𝐢𝐯𝐞 🎨",
    23: "💳 𝐕𝐈𝐏 𝐒𝐋𝐎𝐓 💳",
    24: "👶 𝐂𝐇𝐈𝐁𝐈 𝐂𝐎𝐋𝐋𝐄𝐂𝐓𝐈𝐎𝐍 👶",
    25: "🏴‍☠️ 𝐌𝐀𝐑𝐀𝐔𝐃𝐒 𝐄𝐃𝐈𝐓𝐈𝐎𝐍 🏴‍☠️"
}

RARITY_LABELS = {
    1: "⚪️ Common",
    2: "🟣 Rare",
    3: "🟡 Legendary",
    4: "🟢 Medium",
    5: "💮 Special Edition",
    6: "🔮 Limited Edition",
    7: "💸 Premium Edition",
    8: "🌤 Summer",
    9: "🎐 Celestial",
    10: "❄️ Winter",
    11: "💝 Valentine",
    12: "🎃 Halloween",
    13: "🎄 Christmas Special",
    14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    15: "🎭 Cosplay Master 🎭",
    16: "🧧 Events",
    17: "🎖 Apex Lot ( AUCTION )",
    18: "🍑 Ecchi",
    19: "☠️ Divine",
    20: "☔ Monsoon",
    21: "🪸 Aquatic",
    22: "🎨 Artistic",
    23: "💳 VIP SLOT",
    24: "👶 Chibi",
    25: "🏴‍☠️ Marauds"
}

# ---------- HELPERS ----------
def _get_media_key(character: Dict[str, Any]) -> Optional[str]:
    for k in character.keys():
        kl = k.lower()
        if kl in ("img_url", "img", "photo", "image"):
            return k
        if kl in ("vid_url", "video", "vid"):
            return k
    return None


def _numeric_id_val(character: Dict[str, Any]) -> int:
    try:
        return int(character.get("id", 0))
    except:
        return 0


def _detect_type_from_doc(character: Dict[str, Any]) -> Optional[str]:
    t = character.get("type") or character.get("art") or character.get("art_name")
    if isinstance(t, str) and t.strip():
        for key, emo in TYPE_EMOJIS.items():
            if key.lower() in t.lower():
                return f"{emo} {key}"
        return t.strip()

    rarity_val = character.get("rarity")
    if isinstance(rarity_val, str):
        for key, emo in TYPE_EMOJIS.items():
            if key.lower() in rarity_val.lower():
                return f"{emo} {key}"

    name = character.get("name", "")
    for key, emo in TYPE_EMOJIS.items():
        if key.lower() in str(name).lower():
            return f"{emo} {key}"
    return None


def _render_banner_and_label(rarity_field: Any) -> (str, str):
    try:
        if isinstance(rarity_field, int) or (isinstance(rarity_field, str) and rarity_field.isdigit()):
            rnum = int(rarity_field)
            return RARITY_BANNERS.get(rnum, "✨ Character Drop ✨"), RARITY_LABELS.get(rnum, str(rnum))
    except:
        pass

    if isinstance(rarity_field, str):
        for num, label in RARITY_LABELS.items():
            plain_label = "".join(ch for ch in label if ch.isalnum() or ch.isspace()).strip().lower()
            if plain_label and plain_label.split()[0] in rarity_field.lower():
                return RARITY_BANNERS.get(num, "✨ Character Drop ✨"), label
        return "✨ Character Drop ✨", rarity_field

    return "✨ Character Drop ✨", str(rarity_field)

def _user_link(user_id: Optional[int], name: Optional[str] = None) -> str:
    if not user_id:
        return "Unknown"
    display = name or "User"
    return f'<a href="tg://user?id={user_id}">{display}</a>'


def generate_caption(
    character: Dict[str, Any],
    action: Optional[str] = None,   # "added" | "updated" | "deleted"
    actor_id: Optional[int] = None,
    actor_name: Optional[str] = None
) -> str:
    cid = character.get("id", "N/A")
    name = character.get("name", "Unknown")
    anime = character.get("anime", "Unknown")
    rarity_field = character.get("rarity", 1)

    banner, rarity_label = _render_banner_and_label(rarity_field)
    detected_type = _detect_type_from_doc(character)

    caption_lines = []
    caption_lines.append(banner)
    caption_lines.append("")
    caption_lines.append(f"🆔 <b>ID:</b> {cid}")
    caption_lines.append(f"👤 <b>Character:</b> {name}")
    caption_lines.append(f"🎌 <b>Anime:</b> {anime}")
    caption_lines.append("")

    if detected_type:
        caption_lines.append(f"✨ <i>Art Type: {detected_type}</i>")

    caption_lines.append(f"🌟 <b>Rarity:</b> {rarity_label}")
    caption_lines.append("")
    caption_lines.append("✦━━━━━━━━━━━━━━━━━━━━✦")

    # 🔔 ACTION FOOTER
    if action and actor_id:
        user = _user_link(actor_id, actor_name)
        if action == "added":
            caption_lines.append(f"➕ <b>Added by:</b> {user}")
        elif action == "updated":
            caption_lines.append(f"🔄 <b>Updated by:</b> {user}")
        elif action == "deleted":
            caption_lines.append(f"❌ <b>Deleted by:</b> {user}")

    return "\n".join(caption_lines)



# ---------- MEDIA SENDER ----------
async def _send_media_to_channel(
    character: Dict[str, Any],
    action: Optional[str] = None,
    actor_id: Optional[int] = None,
    actor_name: Optional[str] = None
) -> None:
    caption = generate_caption(
        character,
        action=action,
        actor_id=actor_id,
        actor_name=actor_name
    )
    media_key = _get_media_key(character)

    if media_key:
        if "vid" in media_key.lower():
            await app.send_video(
                chat_id=CHANNEL_ID,
                video=character[media_key],
                caption=caption,
                supports_streaming=True,
                parse_mode=ParseMode.HTML
            )
        else:
            await app.send_photo(
                chat_id=CHANNEL_ID,
                photo=character[media_key],
                caption=caption,
                parse_mode=ParseMode.HTML
            )
    else:
        await app.send_message(
            chat_id=CHANNEL_ID,
            text=caption,
            parse_mode=ParseMode.HTML
        )

# ---------- COMMANDS ----------
@app.on_message(filters.command("sendall") & filters.user([8213641719]))
async def send_all_characters(_, message: Message):
    parts = message.text.split(maxsplit=1)
    start_id = None
    if len(parts) > 1:
        try:
            start_id = int(parts[1].strip())
        except:
            await app.send_message(
                chat_id=message.chat.id,
                text="❌ Provide a valid numeric start id. Usage: /sendall <start_id>"
            )
            return

    try:
        total = await collection.count_documents({})
        if total == 0:
            await app.send_message(chat_id=message.chat.id, text="❌ Database empty — no characters found.")
            return

        progress_msg = await app.send_message(
            chat_id=message.chat.id,
            text=(
                f"⏳ Preparing to send <b>{total}</b> characters...\n"
                + (f"🚩 Starting from ID: <code>{start_id}</code>\n" if start_id else "")
                + f"🔁 Progress updates every {PROGRESS_UPDATE_EVERY} sends."
            ),
            parse_mode=ParseMode.HTML
        )

        docs = []
        async for doc in collection.find({}):
            docs.append(doc)
        docs.sort(key=_numeric_id_val)

        sent = failed = skipped = 0
        last_sent_id = None

        for idx, character in enumerate(docs, start=1):
            cur_id = _numeric_id_val(character)
            if start_id is not None and cur_id < start_id:
                skipped += 1
                continue

            try:
                await _send_media_to_channel(character)
                try:
                    await collection.update_one({"_id": character["_id"]}, {"$set": {"sented": True}})
                except Exception as eu:
                    log.warning("Could not mark sent for id %s: %s", cur_id, eu)

                sent += 1
                last_sent_id = cur_id
            except Exception as send_exc:
                log.exception("Failed to send id %s: %s", cur_id, send_exc)
                failed += 1

            if sent > 0 and sent % PROGRESS_UPDATE_EVERY == 0:
                try:
                    await progress_msg.edit_text(
                        (
                            f"⏳ Progress update\n\n"
                            f"📌 Processed index: {idx}/{total}\n"
                            f"✅ Sent: {sent}\n"
                            f"❌ Failed: {failed}\n"
                            f"⏭ Skipped: {skipped}\n"
                            f"🆔 Last ID: {last_sent_id or 'N/A'}"
                        ),
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass

            await asyncio.sleep(DELAY_BETWEEN_MESSAGES)

        await progress_msg.edit_text(
            (
                "🎉 Completed sending!\n\n"
                f"📦 Total: {total}\n"
                f"✅ Sent: {sent}\n"
                f"❌ Failed: {failed}\n"
                f"⏭ Skipped: {skipped}\n"
                f"🆔 Highest: {last_sent_id or 'N/A'}"
            ),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        await app.send_message(chat_id=message.chat.id, text=f"❌ Error: {e}")


@app.on_message(filters.command("sendone") & filters.user([8213641719]))
async def send_one_character(_, message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await app.send_message(chat_id=message.chat.id, text="❌ Usage: /sendone <character_id>")
        return

    char_id = parts[1].strip()
    try:
        character = await collection.find_one({"id": char_id})
        if not character and char_id.isdigit():
            character = await collection.find_one({"id": int(char_id)})

        if not character:
            await app.send_message(chat_id=message.chat.id, text=f"❌ Character `{char_id}` not found.")
            return

        try:
            await _send_media_to_channel(character)
            try:
                await collection.update_one({"_id": character["_id"]}, {"$set": {"sented": True}})
            except:
                pass

            await app.send_message(
                chat_id=message.chat.id,
                text=f"✅ Sent character `{char_id}`.",
                parse_mode=ParseMode.HTML
            )
        except Exception as send_exc:
            await app.send_message(chat_id=message.chat.id, text=f"❌ Error: {send_exc}")

    except Exception as e:
        await app.send_message(chat_id=message.chat.id, text=f"❌ Database error: {e}")


@app.on_message(filters.command("sendhelp") & filters.user([8213641719]))
async def _send_help(_, message: Message):
    await app.send_message(
        chat_id=message.chat.id,
        text=(
            "<b>📬 Send Commands Help</b>\n\n"
            "/sendall — send all characters.\n"
            "/sendall <start_id> — start from a specific ID.\n"
            "/sendone <id> — send one character.\n\n"
            "⚠️ Owner-only commands."
        ),
        parse_mode=ParseMode.HTML
)
