from pyrogram import Client, filters
from pyrogram.types import BotCommand
from shivu import shivuups as app

@app.on_message(filters.command("setcommand"))
async def set_commands(client, message):
    commands = [
        BotCommand("task", "📝 Complete tasks for rewards"),
        BotCommand("guess", "🎯 Catch a character"),
        BotCommand("gift", "🎁 Gift a character to someone"),
        BotCommand("trade", "🤝 Trade characters with others"),
        BotCommand("top", "🏆 View global top grabbers"),
        BotCommand("ctop", "🏅 View group-specific top grabbers"),
        BotCommand("mycollection", "📜 View your character collection"),
        BotCommand("topgroups", "🏘️ View top groups by activity"),
        BotCommand("nhmode", "🔄 Toggle bot mode"),
        BotCommand("fav", "❤️ Add a character to your favorites"),
        BotCommand("check", "🔍 Look up a character by ID"),
        BotCommand("rarities", "💎 View characters by rarity"),
        BotCommand("daily", "🗓️ Claim your daily coins"),
        BotCommand("weekly", "📅 Claim your weekly coins"),
        BotCommand("bonus", "🎉 Collect bonus rewards"),
        BotCommand("changetime", "⏰ Adjust spawn rate"),
        BotCommand("convert", "💰 Convert coins into tokens"),
        BotCommand("tconvert", "💎 Convert tokens into coins"),
        BotCommand("shopmenu", "🛒 Browse premium characters in the shop"),
        BotCommand("balance", "💵 View your current balance"),
        BotCommand("cointop", "👑 See the top coin holders"),
        BotCommand("tokentop", "🏅 See the top token holders"),
        BotCommand("redeem", "🎟️ Redeem a special code"),
        BotCommand("dailycode", "📦 Generate a daily coin code"),
        BotCommand("credeem", "🎫 Redeem your coin code"),
        BotCommand("hclaim", "🎁 Claim your daily special reward"),
        
        #BotCommand("work", "💼 Earn coins by working"),
        #BotCommand("supportgroup", "🆘 Get help from support group"),
        BotCommand("nclaim", "🤑 Claim your earnings")
    ]

    try:
        await client.set_bot_commands(commands)
        await message.reply_text("✅ Bot commands have been updated successfully!")
    except Exception as e:
        await message.reply_text(f"❌ Failed to set commands: {e}")
