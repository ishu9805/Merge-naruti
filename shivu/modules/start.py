import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler

from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID, PHOTO_URL
from shivu import pm_users as collection, ban_collection  # Import the ban_collection

# Define the start command handler function
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    # Check if the user is banned
    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        return

    # Check if the user already exists in the database
    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🌟 New user alert! 🌟\n\nUser: <a href='tg://user?id={user_id}'>{escape(first_name)}</a> just started the bot!",
            parse_mode='HTML'
        )
    else:
        if user_data['first_name'] != first_name or user_data['username'] != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    # Shortened Welcome Message
    caption = (
        "✨🌸🌟 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐭𝐡𝐞 𝐎𝐭𝐚𝐤𝐮 𝐂𝐮𝐥𝐭𝐮𝐫𝐞 🌟🌸✨\n\n"
        "🌠 𝑯𝒆𝒚 𝒕𝒉𝒆𝒓𝒆, <b>{first_name}</b>! 🌠\n"
        "🎉 We’re excited to have you here! 🎉\n\n"
        "💫 It's a Waifu & Husbando mixed bot! 💫\n"
        "🌀 Summon Waifu & Husbando characters 🌀\n"
        "🎮 Use the /guess command to capture them and grow your collection 🎮\n"
        "🚀 𝑻𝒂𝒑 '𝑯𝒆𝒍𝒑' 𝒇𝒐𝒓 𝒎𝒐𝒓𝒆 𝒄𝒐𝒎𝒎𝒂𝒏𝒅𝒔 🚀\n\n"
        "╔═══════════════════╗\n"
        "    𝑳𝒆𝒕'𝒔 𝒈𝒆𝒕 𝒔𝒕𝒂𝒓𝒕𝒆𝒅! 🎊\n"
        "╚═══════════════════╝"
    ).format(first_name=escape(first_name))

    keyboard = [
        [InlineKeyboardButton("🎯 ADD ME TO YOUR GROUP 🎯", url='http://t.me/Fancy_Waifu_Husbando_Bot?startgroup=new')],
        [
            InlineKeyboardButton("💠 SUPPORT 💠", url='https://t.me/+xJdjLviEJvpmYjM9'),
            InlineKeyboardButton("📢 UPDATES 📢", url='https://t.me/Blade_updates')
        ],
        [
            InlineKeyboardButton("👨‍💻 DEVELOPER 👨‍💻", url='https://t.me/ALONE_X_HATER'),
            InlineKeyboardButton("🌐 NETWORK 🌐", url='https://t.me/BLADE_X_COMMUNITY')
        ],
        [InlineKeyboardButton("⚙️ HELP ⚙️", url='https://t.me/Blade_updates/22')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    photo_url = random.choice(PHOTO_URL)

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=photo_url,
        caption=caption,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# Add the start command handler to the application
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
