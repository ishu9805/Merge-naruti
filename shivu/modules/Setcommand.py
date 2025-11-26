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


from pyrogram import Client, filters
from pyrogram.types import BotCommand, BotCommandScopeDefault
from shivu import shivuups as app

# ✨ 𝖊𝖑𝖎𝖙𝖊 𝖘𝖒𝖆𝖑𝖑-𝖈𝖆𝖕 𝖘𝖊𝖙 𝖈𝖔𝖒𝖒𝖆𝖓𝖉𝖘
@app.on_message(filters.command("setcommand2"))
async def set_commands(client, message):

    commands = [

        # 🌟 𝖌𝖆𝖒𝖊 & 𝖋𝖚𝖓
        BotCommand("task", "📝 ᴄᴏᴍᴘʟᴇᴛᴇ ᴛᴀsᴋs & ᴇᴀʀɴ ʀᴇᴡᴀʀᴅs"),
        BotCommand("guess", "🎯 ᴄᴀᴛᴄʜ ᴀ ʀᴀɴᴅᴏᴍ ᴄʜᴀʀᴀᴄᴛᴇʀ"),
        BotCommand("scramble", "🔡 sᴄʀᴀᴍʙʟᴇ ᴄʜᴀʟʟᴇɴɢᴇ"),

        # 💝 𝖘𝖔𝖈𝖎𝖆𝖑 & 𝖎𝖓𝖙𝖊𝖗𝖆𝖈𝖙𝖎𝖔𝖓
        BotCommand("gift", "🎁 ɢɪꜰᴛ ᴄʜᴀʀᴀᴄᴛᴇʀs ᴛᴏ ꜰʀɪᴇɴᴅs"),
        BotCommand("trade", "🤝 ᴛʀᴀᴅᴇ ᴄʜᴀʀᴀᴄᴛᴇʀs ᴇᴀsɪʟʏ"),
        BotCommand("profile", "👤 ᴠɪᴇᴡ ᴘʀᴏꜰɪʟᴇ (ʀᴇᴘʟʏ)"),

        # 📈 𝖙𝖔𝖕 𝖗𝖆𝖓𝖐𝖘
        BotCommand("top", "🏆 ɢʟᴏʙᴀʟ ᴛᴏᴘ ᴘʟᴀʏᴇʀs"),
        BotCommand("ctop", "🏅 ɢʀᴏᴜᴘ ᴛᴏᴘ ᴘʟᴀʏᴇʀs"),
        BotCommand("topgroups", "🏘️ ᴛᴏᴘ ᴀᴄᴛɪᴠᴇ ɢʀᴏᴜᴘs"),
        BotCommand("cointop", "👑 ᴛᴏᴘ ᴄᴏɪɴ ʜᴏʟᴅᴇʀs"),
        BotCommand("tokentop", "💎 ᴛᴏᴘ ᴛᴏᴋᴇɴ ʜᴏʟᴅᴇʀs"),

        # 🎒 𝖈𝖍𝖆𝖗𝖆𝖈𝖙𝖊𝖗 𝖘𝖞𝖘𝖙𝖊𝖒
        BotCommand("mycollection", "📜 ʏᴏᴜʀ ᴄʜᴀʀᴀᴄᴛᴇʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ"),
        BotCommand("rarities", "💎 ꜱᴏʀᴛ ʙʏ ʀᴀʀɪᴛʏ"),
        BotCommand("check", "🔍 ᴄʜᴇᴄᴋ ᴄʜᴀʀᴀᴄᴛᴇʀ ʙʏ ɪᴅ"),
        BotCommand("detail", "📖 ᴅᴇᴛᴀɪʟᴇᴅ ᴄʜᴀʀᴀᴄᴛᴇʀ ɪɴꜰᴏ"),
        BotCommand("inline", "🎭 ɪɴʟɪɴᴇ ꜱᴇᴀʀᴄʜ (ɴᴀᴍᴇ • ʀᴀʀɪᴛʏ)"),
        BotCommand("animelist", "📚 ᴀɴɪᴍᴇ ʟɪsᴛ"),

        # 💰 𝖎𝖓𝖈𝖔𝖒𝖊 & 𝖗𝖊𝖜𝖆𝖗𝖉𝖘
        BotCommand("daily", "🗓️ ᴅᴀɪʟʏ ᴄᴏɪɴs"),
        BotCommand("weekly", "📅 ᴡᴇᴇᴋʟʏ ᴄᴏɪɴs"),
        BotCommand("bonus", "🎉 ʙᴏɴᴜs ʀᴇᴡᴀʀᴅ"),
        BotCommand("convert", "💰 ᴄᴏɪɴ → ᴛᴏᴋᴇɴ"),
        BotCommand("tconvert", "💎 ᴛᴏᴋᴇɴ → ᴄᴏɪɴ"),
        BotCommand("hclaim", "🎁 ꜱᴘᴇᴄɪᴀʟ ʀᴇᴡᴀʀᴅ"),
        BotCommand("nclaim", "🤑 ᴄʟᴀɪᴍ ᴇᴀʀɴɪɴɢs"),
        BotCommand("balance", "💵 ᴄʜᴇᴄᴋ ʙᴀʟᴀɴᴄᴇ"),

        # 🛒 𝖘𝖍𝖔𝖕
        BotCommand("shopmenu", "🛒 ᴘʀᴇᴍɪᴜᴍ sʜᴏᴘ"),
        BotCommand("redeem", "🎟️ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ"),
        BotCommand("dailycode", "📦 ᴅᴀɪʟʏ ᴄᴏɪɴ ᴄᴏᴅᴇ"),
        BotCommand("credeem", "🎫 ʀᴇᴅᴇᴇᴍ ʏᴏᴜʀ ᴄᴏᴅᴇ"),

        # ⚙️ 𝖘𝖊𝖙𝖙𝖎𝖓𝖌𝖘
        BotCommand("changetime", "⏰ sᴘᴀᴡɴ ᴛɪᴍᴇ ᴄᴏɴᴛʀᴏʟ"),
        BotCommand("nhmode", "🔄 ᴛᴏɢɢʟᴇ ᴍᴏᴅᴇ"),
    ]

    try:
        await client.set_bot_commands(
            commands,
            scope=BotCommandScopeDefault()
        )

        await message.reply_text(
            "✨ **𝖈𝖔𝖒𝖒𝖆𝖓𝖉𝖘 𝖚𝖕𝖉𝖆𝖙𝖊𝖉 𝖌𝖑𝖔𝖇𝖆𝖑𝖑𝖞!**\n"
            "ᴇɴᴊᴏʏ ᴛʜᴇ ɴᴇᴡ ᴘʀᴏ ꜰᴏɴᴛ & ᴘʀᴇᴍɪᴜᴍ ᴜɪ. ⚡"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ **ᴇʀʀᴏʀ ᴜᴘᴅᴀᴛɪɴɢ ᴄᴏᴍᴍᴀɴᴅs:**\n\n`{e}`"
        )
