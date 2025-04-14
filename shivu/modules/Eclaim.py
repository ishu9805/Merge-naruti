import asyncio
import logging
from datetime import datetime, timedelta
import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import UPDATE_CHAT, SUPPORT_CHAT, CHARA_CHANNEL_ID, required_group_id, PHOTO_URL, PARTNER
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


import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Summer Claim Configuration
SUNNY_CHAT_ID = -1002610579411
BEACH_PARTY_LINK = "https://t.me/+GI1fWK_cYnA3OTFl"
SUMMER_RARITY = "🌤 Summer"
VACATION_COOLDOWN = timedelta(days=7)
MAX_CLAIM_USERS = 100  # Default maximum claims
OWNER_ID = ["7378476666"]
# Runtime storage
summer_claim_locks = {}
claimed_users_count = 0
current_max_claims = MAX_CLAIM_USERS

@cmdl
@app.on_message(filters.command("eclaim"))
async def summer_claim(client, message: t.Message):
    global claimed_users_count
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = message.from_user.mention
    
    # Check if we're at the beach party
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
    
    # Get lock for user
    if user_id not in summer_claim_locks:
        summer_claim_locks[user_id] = asyncio.Lock()
    
    async with summer_claim_locks[user_id]:
        try:
            # Check if user exists
            user = await user_collection.find_one({"id": user_id})
            if not user:
                await message.reply_text(
                    "🧴 **Oops!**\n\n"
                    "You need to apply some *bot sunscreen* first!\n"
                    "Send [start](https://t.me/Fancy_Waifu_Husbando_Bot?start=start) in DM to protect yourself from errors!"
                )
                return
            
            # Check claim limit
            if claimed_users_count >= current_max_claims:
                await message.reply_text(
                    "🏄‍♂️ **Event Ended**\n\n"
                    f"The summer event has reached its maximum capacity of {current_max_claims} participants!\n\n"
                    "Thanks for joining the beach party! Maybe next summer... 🌅"
                )
                return
            
            # Check cooldown
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
            
            # Check for slock status in existing characters
            has_slock = any(char.get('slock', False) for char in user.get('characters', []))
            
            # Find a summer character
            pipeline = [
                {'$match': {
                    'rarity': SUMMER_RARITY,
                    'id': {'$nin': [char['id'] for char in user.get('characters', [])]}
                }},
                {'$sample': {'size': 1}}
            ]
            
            # If user has slock:true character, get another one
            
            summer_treasure = await collection.aggregate(pipeline).to_list(length=1)
            
            if not summer_treasure:
                msg = "🌅 **Low Tide Warning**\n\nAll the summer characters are playing hide and seek!"
                if has_slock:
                    msg += "\n\nNo special slock characters available right now!"
                await message.reply_text(msg)
                return
            
            character = summer_treasure[0]
            character_data = {**character, "locked": True}
            
            # Update user collection
            await user_collection.update_one(
                {'id': user_id},
                {
                    '$push': {'characters': character_data},
                    '$set': {'last_summer_claim': datetime.utcnow()}
                },
                upsert=True
            )
            
            claimed_users_count += 1
            
            # Send character
            caption = (
                f"🏄‍♂️ **Summer Splash!** 🏖\n\n"
                f"{mention} caught a *{SUMMER_RARITY}* character!\n\n"
                f"🏖 **Beachcomber's Log**\n"
                f"✨ Name: {character['name']}\n"
                f"📺 Anime: {character['anime']}\n"
            )
            
            
            caption += f"\n⛱ *Come back in 1 week for another beach adventure!*"
            
            await message.reply_photo(
                photo=character['img_url'],
                caption=caption
            )
            
            # Update stats
            await user_count.update_one(
                {'user_id': user_id},
                {'$inc': {
                    'ccount': 1,
                    f'rarity_count.{SUMMER_RARITY}': 1
                }},
                upsert=True
            )
            
        except Exception as e:
            logging.error(f"Beach party error for {user_id}: {str(e)}", exc_info=True)
            await message.reply_text(
                "🌊 **Wipeout!**\n\n"
                "A big wave crashed our beach party!\n"
                "The life guards are working on it - try again later!"
            )

@cmdl
@app.on_message(filters.command("extend") & filters.user(OWNER_ID))
async def extend_summer_event(client, message: t.Message):
    global current_max_claims
    
    try:
        if len(message.command) < 2:
            await message.reply_text("Please specify number to extend by: /extend 50")
            return
            
        extend_by = int(message.command[1])
        if extend_by <= 0:
            await message.reply_text("Please provide a positive number")
            return
            
        current_max_claims += extend_by
        await message.reply_text(
            f"☀️ **Summer Event Extended**\n\n"
            f"Maximum claims increased by {extend_by}!\n"
            f"New maximum: {current_max_claims} users\n\n"
            f"Current claims: {claimed_users_count}/{current_max_claims}"
        )
    except ValueError:
        await message.reply_text("Please provide a valid number")
    except Exception as e:
        logging.error(f"Error extending summer event: {str(e)}")
        await message.reply_text(f"Error: {str(e)}")

@cmdl
@app.on_message(filters.command("resetsummer") & filters.user(OWNER_ID))
async def reset_summer_event(client, message: t.Message):
    global claimed_users_count, current_max_claims
    
    claimed_users_count = 0
    current_max_claims = MAX_CLAIM_USERS
    await message.reply_text(
        "☀️ **Summer Event Reset**\n\n"
        "Claim counter has been reset to 0!\n"
        f"Maximum claims reset to default: {MAX_CLAIM_USERS}\n\n"
        "First users can now claim summer characters again!"
    )

@cmdl
@app.on_message(filters.command("summerstatus") & filters.user(OWNER_ID))
async def summer_status(client, message: t.Message):
    await message.reply_text(
        "🏖 **Summer Event Status**\n\n"
        f"Users claimed: {claimed_users_count}/{current_max_claims}\n"
        f"Cooldown: {VACATION_COOLDOWN.days} days\n"
        f"Special slock bonus: Enabled\n\n"
        "Commands:\n"
        "/extend [number] - Increase max claims\n"
        "/resetsummer - Reset counter and max claims"
)
