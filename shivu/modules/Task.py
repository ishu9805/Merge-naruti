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
TASK_MILESTONES = {
    300: {
        'type': 'special',
        'rarity': '💮 Special Edition',
        'message': "🎉 300 messages! Claim your 💮 Special Edition with /special_claim"
    },
    800: {
        'type': 'limited', 
        'rarity': '🔮 Limited Edition',
        'message': "🌟 800 messages! Choose 🔮 Limited Edition with /limited_claim",
        'grab_required': 2  # 2 legendary grabs required
    },
    2000: {
        'type': 'referral',
        'rarities': ['❄️ Winter', '💝 Valentine', '🎃 Halloween', '🎄 Christmas'],
        'message': "🏆 2000 messages! Get referral code with /referral_claim"
    },
    3500: {
        'type': 'ultimate',
        'rarity': '💎 Ultimate Edition',
        'message': "🚀 3500 messages! Claim 💎 Ultimate Edition with /ultimate_claim",
        'grab_required': 15  # 15 legendary grabs required
    },
    4000: {
        'type': 'celestial',
        'rarity': '🎐 Celestial',
        'message': "✨ 4000 messages! Claim 🎐 Celestial with /celestial_claim"
    }
}

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

async def update_counts():
    """Periodically update counts in database"""
    while True:
        await asyncio.sleep(60)  # Update every minute
        async with lock:
            if not message_counts:
                continue
                
            bulk_ops = [
                UpdateOne(
                    {'user_id': uid},
                    {'$inc': {'count': cnt}},
                    upsert=True
                ) for uid, cnt in message_counts.items() if cnt > 0
            ]
            
            if bulk_ops:
                await user_totals_collection.bulk_write(bulk_ops)
                message_counts.clear()

@app.on_startup()
async def startup():
    asyncio.create_task(update_counts())

@app.on_message(filters.text & filters.group & filters.chat(SUPPORT_CHAT_ID))
async def count_messages(client, message):
    user_id = message.from_user.id
    
    async with lock:
        message_counts[user_id] += 1
        
        # Immediate update if batch size reached
        if message_counts[user_id] >= BATCH_SIZE:
            await user_totals_collection.update_one(
                {'user_id': user_id},
                {'$inc': {'count': message_counts[user_id]}},
                upsert=True
            )
            message_counts[user_id] = 0
            
            # Check for milestones after bulk update
            user_data = await user_totals_collection.find_one({'user_id': user_id})
            total = user_data.get('count', 0) if user_data else 0
            
            for milestone, data in TASK_MILESTONES.items():
                if total == milestone:
                    # Check grab requirements if needed
                    if 'grab_required' in data:
                        grab_count = await get_grab_count(user_id)
                        if grab_count >= data['grab_required']:
                            await client.send_message(user_id, data['message'])
                    else:
                        await client.send_message(user_id, data['message'])
                    break

@app.on_message(filters.command("task"))
async def task_command(client, message):
    user_id = message.from_user.id
    total = await get_user_count(user_id)
    grab_count = await get_grab_count(user_id)
    
    response = [
        "📊 **Your Task Progress**",
        f"💬 Messages: {total}",
        f"⚡ Legendary Grabs: {grab_count}",
        "",
        "🎯 **Milestone Rewards**:"
    ]
    
    for milestone, data in TASK_MILESTONES.items():
        status = "✅" if total >= milestone else "◻️"
        remaining = max(0, milestone - total)
        
        if 'grab_required' in data:
            grab_status = "✅" if grab_count >= data['grab_required'] else "❌"
            response.append(
                f"{status} {data['rarity']} at {milestone} messages ({remaining} left) "
                f"& {grab_status} {data['grab_required']} grabs needed"
            )
        else:
            response.append(
                f"{status} {data['rarity']} at {milestone} messages ({remaining} left)"
            )
    
    await message.reply_text("\n".join(response))

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
        f"- 15 grabs needed for 3500 messages reward ({'✅' if grab_count >= 15 else '❌'})"
    ]
    
    await message.reply_text("\n".join(response))

@app.on_message(filters.command("special_claim"))
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

@app.on_message(filters.command("limited_claim"))
async def claim_limited(client, message):
    user_id = message.from_user.id
    total = await get_user_count(user_id)
    
    if total < 800:
        return await message.reply("❌ You need 800 messages to claim this reward!")
    
    # Check grab requirements
    passed, msg = await check_grab_requirements(user_id, 800)
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
        chars = await collection.find(
            {'rarity': '🔮 Limited Edition'}
        ).to_list(length=50)
        
        if not chars:
            return await message.reply("⚠️ No limited characters available!")
        
        char_list = "\n".join([f"{c['name']} ({c['anime']}) - ID: `{c['id']}`" for c in chars[:20]])
        await message.reply_text(
            f"🔮 Available Limited Edition Characters:\n\n{char_list}\n\n"
            "Reply with: /limited_claim <character_id>"
        )

@app.on_message(filters.command("ultimate_claim"))
async def claim_ultimate(client, message):
    user_id = message.from_user.id
    total = await get_user_count(user_id)
    
    if total < 3500:
        return await message.reply("❌ You need 3500 messages to claim this reward!")
    
    # Check grab requirements
    passed, msg = await check_grab_requirements(user_id, 3500)
    if not passed:
        return await message.reply(msg)
    
    user_data = await user_totals_collection.find_one({'user_id': user_id})
    if user_data and user_data.get('claimed_3500'):
        return await message.reply("⚠️ You've already claimed this reward!")
    
    # Check if user provided a character ID
    if len(message.command) > 1:
        char_id = message.command[1]
        char = await collection.find_one({
            'id': char_id,
            'rarity': '💎 Ultimate Edition'
        })
        
        if not char:
            return await message.reply("❌ Invalid ID or not an Ultimate Edition character!")
        
        # Add to user's collection
        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': char}},
            upsert=True
        )
        
        # Mark as claimed
        await user_totals_collection.update_one(
            {'user_id': user_id},
            {'$set': {'claimed_3500': True}},
            upsert=True
        )
        
        return await message.reply_photo(
            char['img_url'],
            caption=f"🎁 Ultimate Edition Claimed!\n\n{char['name']}\n{char['rarity']}\n{char['anime']}"
        )
    else:
        # Show list of available Ultimate Edition characters if no ID provided
        chars = await collection.find(
            {'rarity': '💎 Ultimate Edition'}
        ).to_list(length=50)
        
        if not chars:
            return await message.reply("⚠️ No ultimate characters available!")
        
        char_list = "\n".join([f"{c['name']} ({c['anime']}) - ID: `{c['id']}`" for c in chars[:20]])
        await message.reply_text(
            f"💎 Available Ultimate Edition Characters:\n\n{char_list}\n\n"
            "Reply with: /ultimate_claim <character_id>"
        )

# ... [Keep all your existing referral, celestial, and exchange commands] ...

# Character grab detection handler
@app.on_message(filters.text & filters.group & filters.chat(SUPPORT_CHAT_ID))
async def detect_grabs(client, message):
    # This assumes your system has a way to detect when a legendary character is grabbed
    # Modify this according to how your character collection system works
    if hasattr(message, 'is_legendary_grab') and message.is_legendary_grab:
        user_id = message.from_user.id
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'grab': 1}},
            upsert=True
        )

if __name__ == "__main__":
    app.run()
