from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import random
import time
import asyncio
from shivu import (
    collectionps as collection,
    user_collectionps as user_collection,
    user_totals_collectionps as user_totals_collection,
    shivuups as app,
    
    OWNER_ID
)

# Global in-memory counter
message_counts = defaultdict(int)
lock = asyncio.Lock()
BATCH_SIZE = 100  # Update DB every 100 messages
SUPPORT_CHAT_ID = -1002545997671
# Task milestones configuration

# Updated TASK_MILESTONES with all required keys
TASK_MILESTONES = {
    300: {
        'type': 'special',
        'rarity': '💮 Special Edition',
        'message': "🎉 300 messages! Claim your 💮 Special Edition with /sclaim",
        'grab_required': 2  # Explicitly set for all milestones
    },
    700: {
        'type': 'limited', 
        'rarity': '🔮 Limited Edition',
        'message': "🌟 700 messages! Choose 🔮 Limited Edition with /lclaim",
        'grab_required': 4
    },
    2000: {
        'type': 'WVHC',
        'rarity': 'Referral Rewards',  # Added rarity field
        'rarities': ['❄️ Winter', '💝 Valentine', '🎃 Halloween', '🎄 Christmas'],
        'message': "🏆 2000 messages! Get referral code with /rclaim ID [CHOICE]",
        'grab_required': 9
    },
    3500: {
        'type': 'celestial',
        'rarity': '🎐 Celestial',
        'message': "✨ 3500 messages! Claim 🎐 Celestial with /cclaim id [choice]",
        'grab_required': 15
    }
}

# Updated task_command to handle missing keys safely
@app.on_message(filters.command("task"))
async def task_command(client, message):
    user_id = message.from_user.id
    total = await get_user_count(user_id)
    grab_count = await get_grab_count(user_id)
    
    response = [
        "📊 **Your Task Progress**",
        f"💬 Messages: {total} [GROUP](https://t.me/+F93IEsHpc2hkNDc1)",
        f"⚡ Legendary Grabs: {grab_count}",
        "",
        "🎯 **Milestone Rewards**:"
    ]
    
    for milestone, data in sorted(TASK_MILESTONES.items()):
        status = "✅" if total >= milestone else "◻️"
        remaining = max(0, milestone - total)
        
        # Safely get rarity with default
        rarity = data.get('rarity', 'Reward')
        
        # Handle both grab and non-grab milestones
        if 'grab_required' in data and data['grab_required'] > 0:
            grab_status = "✅" if grab_count >= data['grab_required'] else "❌"
            response.append(
                f"{status} {rarity} at {milestone} messages ({remaining} left) "
                f"& {grab_status} {data['grab_required']} grabs needed"
            )
        else:
            response.append(
                f"{status} {rarity} at {milestone} messages ({remaining} left)"
            )
    
    await message.reply_text("\n".join(response))


async def get_user_count(user_id):
    """Get combined in-memory + database count"""
    async with lock:
        in_memory = message_counts.get(user_id, 0)
    user_data = await user_totals_collection.find_one({'user_id': user_id})
    db_count = user_data.get('count', 0) if user_data else 0
    return db_count + in_memory

async def get_grab_count(user_id):
    """Get user's legendary grab count"""
    user_data = await user_collection.find_one({'id': user_id})
    return user_data.get('grab', 0) if user_data else 0

async def check_grab_requirements(user_id, milestone):
    """Check if user meets grab requirements for a milestone"""
    grab_count = await get_grab_count(user_id)
    required = TASK_MILESTONES[milestone].get('grab_required', 0)
    
    if grab_count < required:
        return False, f"❌ You need {required} legendary grabs (you have {grab_count}) to claim this reward!"
    return True, ""




@app.on_message(filters.command("mygrabs"))
async def check_grabs(client, message):
    user_id = message.from_user.id
    grab_count = await get_grab_count(user_id)
    
    response = [
        "🦅 **Legendary Grabs Progress**",
        f"⚡ Legendary Characters Grabbed: {grab_count}",
        "",
        "🎯 **Milestone Requirements**:",
        f"- 2 grabs needed for 800 messages reward ({'✅' if grab_count >= 2 else '❌'})",
        f"- 15 grabs reeded for 3500 messages reward ({'✅' if grab_count >= 15 else '❌'})"
    ]
    
    await message.reply_text("\n".join(response))

@app.on_message(filters.command("sclaim"))
async def claim_special(client, message):
    user_id = message.from_user.id
    total = await get_user_count(user_id)
    
    if total < 300:
        return await message.reply("❌ You need 300 messages to claim this reward!")
    
    # Check if already claimed
    user_data = await user_totals_collection.find_one({'user_id': user_id})
    if user_data and user_data.get('claimed_300'):
        return await message.reply("⚠️ You've already claimed this reward!")
    
    # Get random special character
    char = await collection.aggregate([
        {'$match': {'rarity': '💮 Special Edition'}},
        {'$sample': {'size': 1}}
    ]).to_list(length=1)
    
    if not char:
        return await message.reply("⚠️ No special characters available!")
    
    # Add to user's collection
    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': char[0]}},
        upsert=True
    )
    
    # Mark as claimed
    await user_totals_collection.update_one(
        {'user_id': user_id},
        {'$set': {'claimed_300': True}},
        upsert=True
    )
    
    await message.reply_photo(
        char[0]['img_url'],
        caption=f"🎁 Reward Claimed!\n\n{char[0]['name']}\n{char[0]['rarity']}\n{char[0]['anime']}"
    )


@app.on_message(filters.command("lclaim"))
async def claim_limited(client, message):
    user_id = message.from_user.id
    total = await get_user_count(user_id)
    
    if total < 700:
        return await message.reply("❌ You need 700 messages to claim this reward!")
    
    # Check grab requirements
    passed, msg = await check_grab_requirements(user_id, 700)
    if not passed:
        return await message.reply(msg)
    
    user_data = await user_totals_collection.find_one({'user_id': user_id})
    if user_data and user_data.get('claimed_800'):
        return await message.reply("⚠️ You've already claimed this reward!")
    
    # Check if user provided a character ID
    if len(message.command) > 1:
        char_id = message.command[1]
        char = await collection.find_one({
            'id': char_id,
            'rarity': '🔮 Limited Edition'
        })
        
        if not char:
            return await message.reply("❌ Invalid ID or not a Limited Edition character!")
        
        # Add to user's collection
        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': char}},
            upsert=True
        )
        
        # Mark as claimed
        await user_totals_collection.update_one(
            {'user_id': user_id},
            {'$set': {'claimed_800': True}},
            upsert=True
        )
        
        return await message.reply_photo(
            char['img_url'],
            caption=f"🎁 Limited Edition Claimed!\n\n{char['name']}\n{char['rarity']}\n{char['anime']}"
        )
    else:
        # Show list of available Limited Edition characters if no ID provided
        await message.reply("provide id too")



