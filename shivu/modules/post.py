from shivu import shivuups as app
from shivu import dbps as db

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)

CHANNEL_ID = -1003855295896
OWNER_ID = 8213641719

FORCE_CHANNEL = -1003855295896
FORCE_CHANNEL_LINK = "https://t.me/ART_GURU_NARUTO"


# 🔥 small caps
def small_caps(text):
    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘqʀꜱᴛᴜᴠᴡxʏᴢ"
    return "".join(small[normal.index(c)] if c in normal else c for c in text.lower())


# ✨ caption
def format_caption(name, anime):
    name = small_caps(name)
    anime = small_caps(anime)

    return f"""┏━━━✦❘༻༺❘✦━━━┓
   {name}  
   「 {anime} 」
┗━━━✦❘༻༺❘✦━━━┛

✨ ᴀᴇsᴛʜᴇᴛɪᴄ ᴀʀᴛ ✨  

〆 @naruto_artist  
〆 @naruto_waifu_husbando_bot"""


# 🎯 buttons (deep-link)
def get_buttons(post_id, count, bot_username):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"📥 ᴅᴏᴡɴʟᴏᴀᴅ ({count})",
                url=f"https://t.me/{bot_username}?start={post_id}"
            ),
            InlineKeyboardButton(
                "👤 ᴄʀᴇᴀᴛᴏʀ",
                url="https://t.me/NARUTO_ARTIST"
            )
        ]
    ])


# 🔒 check join
async def is_joined(client, user_id):
    try:
        member = await client.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# 🚀 /art (OWNER ONLY)
@app.on_message(filters.command("art") & filters.reply)
async def art_handler(client, message):

    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs")

    try:
        args = message.text.split(" ", 1)[1]
        name, anime = args.split(" - ")

        caption = format_caption(name, anime)
        reply = message.reply_to_message

        file_ids = []
        bot_username = (await client.get_me()).username

        # 📌 single photo
        if reply.photo:
            sent = await client.send_photo(
                chat_id=CHANNEL_ID,
                photo=reply.photo.file_id,
                caption=caption,
                reply_markup=get_buttons("temp", 0, bot_username)
            )

            file_ids.append(reply.photo.file_id)
            post_id = str(sent.id)

            await sent.edit_reply_markup(
                get_buttons(post_id, 0, bot_username)
            )

        # 📌 album
        elif reply.media_group_id:
            group = await client.get_media_group(message.chat.id, reply.id)

            media = []
            for i, msg in enumerate(group):
                if msg.photo:
                    file_ids.append(msg.photo.file_id)
                    media.append(
                        InputMediaPhoto(
                            media=msg.photo.file_id,
                            caption=caption if i == 0 else ""
                        )
                    )

            sent_msgs = await client.send_media_group(CHANNEL_ID, media)
            post_id = str(sent_msgs[0].id)

            await client.edit_message_reply_markup(
                CHANNEL_ID,
                sent_msgs[0].id,
                reply_markup=get_buttons(post_id, 0, bot_username)
            )

        else:
            return await message.reply("❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴘʜᴏᴛᴏ ᴏʀ ᴀʟʙᴜᴍ")

        # 💾 save DB
        await db.art_posts.insert_one({
            "post_id": post_id,
            "file_ids": file_ids,
            "downloads": 0
        })

        await message.reply("✅ ᴘᴏsᴛᴇᴅ!")

    except Exception as e:
        await message.reply(f"❌ ᴇʀʀᴏʀ: {e}")


# 🚀 /start (download handler)
#@app.on_message(filters.command("start"))
async def start_handler(client, message):

    if len(message.command) < 2:
        return await message.reply("✨ ᴡᴇʟᴄᴏᴍᴇ! ᴄʟɪᴄᴋ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ.")

    post_id = message.command[1]

    # 🔒 force join
    if not await is_joined(client, message.from_user.id):
        return await message.reply(
            "🔒 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=FORCE_CHANNEL_LINK)],
                [InlineKeyboardButton("✅ ᴄʜᴇᴄᴋ ᴀɢᴀɪɴ", callback_data=f"check_{post_id}")]
            ])
        )

    data = await db.art_posts.find_one({"post_id": post_id})

    if not data:
        return await message.reply("❌ ɴᴏᴛ ғᴏᴜɴᴅ")

    try:
        for file_id in data["file_ids"]:
            await client.send_photo(message.chat.id, file_id)

        # update count
        new_count = data.get("downloads", 0) + 1

        await db.art_posts.update_one(
            {"post_id": post_id},
            {"$set": {"downloads": new_count}}
        )

        bot_username = (await client.get_me()).username

        await client.edit_message_reply_markup(
            CHANNEL_ID,
            int(post_id),
            reply_markup=get_buttons(post_id, new_count, bot_username)
        )

    except:
        await message.reply("⚠️ ᴇʀʀᴏʀ")


# 🔁 check again button
#@app.on_callback_query(filters.regex(r"check_(.+)"))
async def check_join(client, query):
    post_id = query.data.split("_")[1]

    if not await is_joined(client, query.from_user.id):
        return await query.answer("❌ ʏᴏᴜ sᴛɪʟʟ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ", show_alert=True)

    await query.message.delete()

    data = await db.art_posts.find_one({"post_id": post_id})

    if not data:
        return await query.message.reply("❌ ɴᴏᴛ ғᴏᴜɴᴅ")

    for file_id in data["file_ids"]:
        await client.send_photo(query.from_user.id, file_id)

    # update count
    new_count = data.get("downloads", 0) + 1

    await db.art_posts.update_one(
        {"post_id": post_id},
        {"$set": {"downloads": new_count}}
    )

    bot_username = (await client.get_me()).username

    await client.edit_message_reply_markup(
        CHANNEL_ID,
        int(post_id),
        reply_markup=get_buttons(post_id, new_count, bot_username)
    )

    await query.answer("✅ ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ")
