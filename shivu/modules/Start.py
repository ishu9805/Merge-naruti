from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import pm_users as collection, ban_collection

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    try:
        # Check if user is banned
        if await ban_collection.find_one({"user_id": user_id}):
            return

        # Check or update user data
        user_data = await collection.find_one({"_id": user_id})
        if user_data is None:
            await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"New user alert!\n\nUser: {first_name} (@{username or 'No Username'}) just started the bot!"
            )
        else:
            updates = {}
            if user_data.get('first_name') != first_name:
                updates['first_name'] = first_name
            if user_data.get('username') != username:
                updates['username'] = username
            if updates:
                await collection.update_one({"_id": user_id}, {"$set": updates})

        # Welcome message
        caption = (
            f"✨ _Welcome, {first_name}!_ ✨\n\n"
            "🌀 *Here’s what you can do:* 🌀\n\n"
            "➡️ *Summon Characters* \n"
            "    _Explore a world of Waifu & Husbando._\n\n"
            "➡️ *Play Games* \n"
            "    _Use `/guess` to capture and grow your collection._\n\n"
            "➡️ *Explore Features* \n"
            "    _Dive into commands and have fun!_\n\n"
            "⚙️ _Need help? Use the buttons below._\n\n"
            "`Let’s get started!` 🚀"
        )

        # Keyboard
        keyboard = [
            [InlineKeyboardButton("Add Me", url=f"http://t.me/fancy_waifu_husbando_bot?startgroup=new")],
            [
                InlineKeyboardButton("📩 Support", url=f"https://t.me/naruto_support_chat"),
                InlineKeyboardButton("📢 Updates", url=f"https://t.me/BLADE_X_COMMUNITY")
            ],
            [InlineKeyboardButton("🛠 Help", url=f"https://t.me/BLADE_X_COMMUNITY/489")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send welcome message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error in start command: {e}")

# Add the start command handler to the application
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
