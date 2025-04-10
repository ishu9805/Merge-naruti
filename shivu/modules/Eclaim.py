import asyncio
import logging
from datetime import datetime, timedelta
import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
from .lock import command_lock as cmdl


# Summer Claim Configuration
SUNNY_CHAT_ID = -1002610579411
BEACH_PARTY_LINK = "https://t.me/+GI1fWK_cYnA3OTFl"
SUMMER_RARITY = "🌤 Summer"
VACATION_COOLDOWN = timedelta(days=7)  # 1 week between claims

# Beach umbrella emoji lock system 🏖
summer_claim_locks = {}

@cmdl
@app.on_message(filters.command("eclaim"))
async def summer_claim(client, message: t.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = message.from_user.mention
    
    # Check if we're at the beach party 🏝
    if chat_id != SUNNY_CHAT_ID:
        summer_kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("☀️ Join Summer Party ☀️", url=BEACH_PARTY_LINK)]]
        )
        await message.reply_text(
            "🏖 **Beach Access Required**\n\n"
            "You need to be at our *summer splash party* to use this command!\n"
            "The waves are perfect and the characters are waiting...\n\n"
            "Come join us at the beach! 🏄‍♂️",
            reply_markup=summer_kb,
            disable_web_page_preview=True
        )
        return
    
    # Get your beach towel (lock) 🏖
    if user_id not in summer_claim_locks:
        summer_claim_locks[user_id] = asyncio.Lock()
    
    async with summer_claim_locks[user_id]:
        try:
            # Check if user brought sunscreen (started bot)
            user = await user_collection.find_one({"id": user_id})
            if not user:
                await message.reply_text(
                    "🧴 **Oops!**\n\n"
                    "You need to apply some *bot sunscreen* first!\n"
                    "Send /start in DM to protect yourself from errors!"
                )
                return
            
            # Check last beach visit
            last_dip = user.get("last_summer_claim")
            if last_dip:
                last_visit = last_dip.replace(tzinfo=None)
                since_last = datetime.utcnow() - last_visit
                
                if since_last < VACATION_COOLDOWN:
                    remaining = VACATION_COOLDOWN - since_last
                    days = remaining.days
                    hours, remainder = divmod(remaining.seconds, 3600)
                    minutes = remainder // 60
                    
                    await message.reply_text(
                        "⛱ **Beach Rules**\n\n"
                        f"You already collected your *summer souvenir* this week, {mention}!\n\n"
                        f"🌴 Next dive-in: *{days}d {hours}h {minutes}m*\n"
                        f"The ocean needs time to replenish its treasures!"
                    )
                    return
            
            # Find a fresh summer character
            owned_characters = {char['id'] for char in user.get('characters', [])}
            
            summer_treasure = await collection.aggregate([
                {'$match': {
                    'rarity': SUMMER_RARITY,
                    'id': {'$nin': list(owned_characters)}
                }},
                {'$sample': {'size': 1}}
            ]).to_list(length=1)
            
            if not summer_treasure:
                await message.reply_text(
                    "🌅 **Low Tide Warning**\n\n"
                    "All the summer characters are playing hide and seek!\n"
                    "Try again later when the tide brings new treasures ashore."
                )
                return
            
            character = summer_treasure[0]
            
            # Update your summer scrapbook
            await user_collection.update_one(
                {'id': user_id},
                {
                    '$push': {'characters': character},
                    '$set': {'last_summer_claim': datetime.utcnow()}
                },
                upsert=True
            )
            
            # Show your summer catch
            await message.reply_photo(
                photo=character['img_url'],
                caption=(
                    f"🏄‍♂️ **Summer Splash!** 🏖\n\n"
                    f"{mention} caught a *{SUMMER_RARITY}* character!\n\n"
                    f"🏖 **Beachcomber's Log**\n"
                    f"✨ Name: {character['name']}\n"
                    f"📺 Anime: {character['anime']}\n\n"
                    f"⛱ *Come back in 1 week for another beach adventure!*\n"
                    f"The summer festival continues... ☀️"
                )
            )
            
            # Update your collection stats
            await user_count.update_one(
                {'user_id': user_id},
                {'$inc': {
                    'ccount': 1,
                    f'rarity_count.{SUMMER_RARITY}': 1
                }},
                upsert=True
            )
            
            # Beach cleanup on error
        except Exception as e:
            logging.error(f"Beach party error for {user_id}: {str(e)}", exc_info=True)
            await message.reply_text(
                "🌊 **Wipeout!**\n\n"
                "A big wave crashed our beach party!\n"
                "The life guards are working on it - try again later!"
            )
