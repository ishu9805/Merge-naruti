import random
from pyrogram import filters
from pyrogram.types import Message
from shivu import (
    shivuups as app,
    collectionps as collection,
    user_collectionps as user_collection,
    giveaway_collectionps as giveaway_collection,
)
from . import dev_filter

rarity_map = {
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
    16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨",
    17: "🎖 Apex Lot ( AUCTION )",
    18: "🍑 Echhi",
    19: "☠️ 𝕯𝖎𝖛𝖎𝖓𝖊",
    20: "☔ Monsoon",
    21: "🪸 Aquatic",
    22: "🎨 Artistic",
    23: "💳 VIP SLOT",
    24: "🎗️ 𝘼𝙈𝙑 𝙃𝙞𝙣𝙙𝙞 𝙀𝙙𝙞𝙩𝙞𝙤𝙣"
}

@app.on_message(filters.command("takepart"))
async def takepart_cmd(client, message: Message):
    uid = message.from_user.id
    uname = message.from_user.username.lower() if message.from_user.username else None



    if str(message.chat.id) != "-1002783891820":
        await message.reply_text("you can only use this command here @hclaim_support")
        return
        
    already = await giveaway_collection.find_one({"id": uid})
    if already:
        await message.reply_text("✅ You already joined today's giveaway.")
        return
    await giveaway_collection.insert_one({"id": uid, "username": uname})
    await message.reply_text("✅ Joined the giveaway. Good luck!")
  

@app.on_message(filters.command("endoftheday") & dev_filter)
async def end_of_day_cmd(client, message: Message):
    participants = await giveaway_collection.find().to_list(length=None)
    if not participants:
        await message.reply_text("⚠️ No participants found for today's giveaway.")
        return

    allowed_rarities = [rarity_map[5], rarity_map[6]]  # Special or Limited (text values)
    distributed = 0
    failed = 0

    for p in participants:
        uid = p["id"]
        # sample one character whose rarity text is Special or Limited
        sampled = await collection.aggregate([
            {"$match": {"rarity": {"$in": allowed_rarities}}},
            {"$sample": {"size": 1}}
        ]).to_list(length=1)

        if not sampled:
            failed += 1
            continue

        card = sampled[0]
        reward = {
            "id": card.get("id"),
            "name": card.get("name"),
            "anime": card.get("anime"),
            "rarity": card.get("rarity")
        }
        if card.get("img_url"):
            reward["img_url"] = card.get("img_url")
        if card.get("vid_url"):
            reward["vid_url"] = card.get("vid_url")

        await user_collection.update_one(
            {"id": uid},
            {
                "$setOnInsert": {"id": uid, "username": p.get("username")},
                "$push": {"characters": reward}
            },
            upsert=True
        )

        caption = (
            f"🎁 Giveaway Reward 🎁\n\n"
            f"Name: {reward['name']}\n"
            f"Anime: {reward['anime']}\n"
            f"Rarity: {reward['rarity']}\n"
            f"ID: {reward.get('id', 'N/A')}"
        )

        try:
            if reward.get("img_url"):
                await client.send_photo(chat_id=uid, photo=reward["img_url"], caption=caption)
            elif reward.get("vid_url"):
                await client.send_video(chat_id=uid, video=reward["vid_url"], caption=caption)
            else:
                await client.send_message(chat_id=uid, text=caption)
            distributed += 1
        except Exception:
            failed += 1
            # cannot DM this user (maybe privacy) — we still added to their DB record

    # announce two random participants to the channel (ID or username if available)
    if participants:
        announce_count = min(2, len(participants))
        chosen = random.sample(participants, announce_count)
        lines = []
        for c in chosen:
            if c.get("username"):
                lines.append(f"@{c['username']}")
            else:
                lines.append(f"`{c['id']}`")
        announce_text = "🏆 Selected participants:\n" + "\n".join(lines)
        try:
            await client.send_message(-1001999201034, announce_text)
        except Exception:
            pass

    await giveaway_collection.delete_many({})
    await message.reply_text(f"✅ Giveaway finished. Distributed: {distributed}. DM failed: {failed}.")



from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuups as app, giveaway_collectionps as giveaway_collection

@app.on_message(filters.command("participants"))
async def participants_cmd(client, message: Message):
    total = await giveaway_collection.count_documents({})
    await message.reply_text(f"📊 Total Giveaway Participants: **{total}**")
