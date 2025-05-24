import logging
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
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu.modules.lock import command_lock as cmd

claim_locks = defaultdict(asyncio.Lock)
pending_claims = {}
message_counts = defaultdict(int)
lock = asyncio.Lock()
BATCH_SIZE = 100
SUPPORT_CHAT_ID = -1002606804832

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("shivu_claims.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TASK_MILESTONES = {
    300: {
        'type': 'special',
        'rarity': '💮 Special Edition',
        'message': "🎉 300 messages! Claim your 💮 Special Edition with /sclaim",
        'grab_required': 2
    },
    1000: {
        'type': 'limited', 
        'rarity': '🔮 Limited Edition',
        'message': "🌟 1000 messages! Choose 🔮 Limited Edition with /lclaim",
        'grab_required': 4
    }
}

async def acquire_user_lock(user_id):
    try:
        await asyncio.wait_for(claim_locks[user_id].acquire(), timeout=30)
        return True
    except asyncio.TimeoutError:
        return False

async def release_user_lock(user_id):
    if claim_locks[user_id].locked():
        claim_locks[user_id].release()

async def get_user_count(user_id):
    async with lock:
        in_memory = message_counts.get(user_id, 0)
    user_data = await user_totals_collection.find_one({'user_id': user_id})
    db_count = user_data.get('count', 0) if user_data else 0
    return db_count + in_memory

async def get_grab_count(user_id):
    user_data = await user_collection.find_one({'id': user_id})
    return user_data.get('grab', 0) if user_data else 0

async def get_character_owners(char_id):
    count = await user_collection.count_documents({
        'characters.id': char_id
    })
    return count

@cmd
@app.on_message(filters.command("task"))
async def task_command(client, message):
    user_id = message.from_user.id
    total = await get_user_count(user_id)
    grab_count = await get_grab_count(user_id)
    
    response = [
        "📊 **Your Task Progress**",
        f"💬 Messages: {total} [GROUP](https://t.me/+CE94ttBftcNlNDk1)",
        f"⚡ Legendary Grabs: {grab_count}",
        "",
        "🎯 **Milestone Rewards**:"
    ]
    
    all_completed = True
    for milestone, data in sorted(TASK_MILESTONES.items()):
        status = "✅" if total >= milestone else "◻️"
        remaining = max(0, milestone - total)
        rarity = data.get('rarity', 'Reward')
        
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
        
        user_data = await user_totals_collection.find_one({'user_id': user_id})
        claim_field = f"claimed_{milestone}"
        if not user_data or not user_data.get(claim_field, False):
            all_completed = False
    
    if all_completed:
        response.append("\n🎉 You've completed ALL milestones!")
        response.append("You can reset your tasks with /reset_task to start over")
    
    await message.reply_text("\n".join(response))

@cmd
@app.on_message(filters.command("nclaim"))
async def unified_claim(client, message):
    user_id = message.from_user.id
    
    if user_id in pending_claims:
        claim_data = pending_claims[user_id]
        await message.reply(
            f"⚠️ You have a pending {claim_data['rarity']} claim!\n"
            f"Character: {claim_data['char_name']}\n"
            "Please confirm or cancel it before making new claims."
        )
        return
    
    if not await acquire_user_lock(user_id):
        return await message.reply("🚫 The system is currently processing your previous request. Please wait a moment and try again.")
    
    try:
        if len(message.command) < 2:
            await release_user_lock(user_id)
            return await message.reply(
                "❌ First complete the /task to claim!\n"
                "Available milestones:\n\n"
                "• /nclaim 300 - 💮 Special Edition (automatic)\n"
                "• /nclaim 1000 [id] - 🔮 Limited Edition (choice)\n"
            )
        
        try:
            milestone = int(message.command[1])
            
            if milestone not in TASK_MILESTONES:
                await release_user_lock(user_id)
                return await message.reply(
                    "❌ Invalid milestone! Available milestones:\n"
                    "• 300 - 💮 Special Edition\n"
                    "• 1000 - 🔮 Limited Edition\n"
                )
            
            if milestone != 300 and len(message.command) < 3:
                await release_user_lock(user_id)
                return await message.reply(
                    f"❌ Please provide character ID for this reward!\n"
                    f"Usage: /nclaim {milestone} [character_id]\n"
                    f"Check available characters with /list{milestone}"
                )
            
            total_messages = await get_user_count(user_id)
            grab_count = await get_grab_count(user_id)
            required_grabs = TASK_MILESTONES[milestone].get('grab_required', 0)
            
            if total_messages < milestone:
                await release_user_lock(user_id)
                return await message.reply(
                    f"❌ You need {milestone} messages to claim this reward! "
                    f"You have {total_messages}/{milestone}."
                )
            
            if grab_count < required_grabs:
                await release_user_lock(user_id)
                return await message.reply(
                    f"❌ You need {required_grabs} legendary grabs for this reward! "
                    f"You have {grab_count}/{required_grabs}."
                )
            
            claim_field = f"claimed_{milestone}"
            user_data = await user_totals_collection.find_one({'user_id': user_id})
            if user_data and user_data.get(claim_field):
                await release_user_lock(user_id)
                return await message.reply("⚠️ You've already claimed this reward!")
            
            if milestone == 300:
                await handle_automatic_claim(client, message, user_id, milestone, '💮 Special Edition')
            elif milestone == 1000:
                char_id = message.command[2]
                await handle_id_claim(client, message, user_id, milestone, char_id, '🔮 Limited Edition')
                
        except ValueError:
            await release_user_lock(user_id)
            await message.reply("❌ Please enter a valid number (300 or 1000)")
        except Exception as e:
            logging.error(f"Claim processing error for user {user_id}: {str(e)}", exc_info=True)
            await message.reply("❌ An error occurred while processing your claim. Please try again later.")
            await release_user_lock(user_id)
            
    except Exception as e:
        logging.error(f"Unexpected error in unified_claim for user {user_id}: {str(e)}", exc_info=True)
        await message.reply("⚠️ A system error occurred. Please try again later.")
    finally:
        await release_user_lock(user_id)

async def handle_automatic_claim(client, message, user_id, milestone, rarity):
    char = await collection.aggregate([
        {'$match': {'rarity': rarity}},
        {'$sample': {'size': 1}}
    ]).to_list(length=1)
    
    if not char:
        return await message.reply(f"⚠️ No {rarity} characters available!")
    
    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': char[0]}},
        upsert=True
    )
    
    await user_totals_collection.update_one(
        {'user_id': user_id},
        {'$set': {f'claimed_{milestone}': True}},
        upsert=True
    )
    
    await message.reply_photo(
        char[0]['img_url'],
        caption=f"🎉 {rarity} Claimed!\n\n{char[0]['name']}\n{char[0]['rarity']}\n{char[0]['anime']}"
    )

async def handle_id_claim(client, message, user_id, milestone, char_id, rarity):
    char = await collection.find_one({
        'id': char_id,
        'rarity': rarity
    })
    
    if not char:
        return await message.reply(
            f"❌ Character not found or not {rarity}!\n"
            f"Use /list{milestone} to see available options."
        )

    sup = char.get('slock')
    if sup == 'True':
        return await message.reply("❌ This character is locked and cannot be claimed!")
    
    owner_count = await get_character_owners(char_id)
    if owner_count >= 4:
        return await message.reply(
            "❌ This Limited Edition character has already been claimed by 4 users!\n"
            "Please choose another character."
        )
    
    pending_claims[user_id] = {
        'char_id': char_id,
        'milestone': milestone,
        'char_name': char['name'],
        'rarity': rarity,
        'message_id': message.id,
        'timestamp': time.time()
    }
    
    confirm_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Claim", callback_data=f"tttconfirm_{milestone}_{char_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="tcancel_claim")]
    ])
    
    await message.reply_photo(
        char['img_url'],
        caption=f"⚠️ Confirm {rarity} Claim:\n\n"
                f"{char['name']}\n{char['rarity']}\n{char['anime']}\n\n"
                "Are you sure?",
        reply_markup=confirm_buttons
    )

@app.on_callback_query(filters.regex(r"^tttconfirm_(\d+)_(.+?)(?:_(.+))?$"))
async def confirm_claim(client, callback_query):
    user_id = callback_query.from_user.id
    
    if user_id not in pending_claims:
        await callback_query.answer("No pending claim found!", show_alert=True)
        return await callback_query.message.edit_reply_markup()
    
    try:
        milestone = int(callback_query.matches[0].group(1))
        char_id = callback_query.matches[0].group(2)
        
        pending_data = pending_claims.get(user_id)
        if not pending_data or pending_data['char_id'] != char_id or pending_data['milestone'] != milestone:
            await callback_query.answer("Claim data mismatch!", show_alert=True)
            return await callback_query.message.edit_reply_markup()
        
        rarity = TASK_MILESTONES[milestone]['rarity']
        
        owner_count = await get_character_owners(char_id)
        if owner_count <= 4:
            await callback_query.answer("This character is no longer available!", show_alert=True)
            return await callback_query.message.edit_reply_markup()
        
        char = await collection.find_one({
            'id': char_id,
            'rarity': rarity
        })
        
        if not char:
            await callback_query.answer("Character no longer available!", show_alert=True)
            return await callback_query.message.edit_reply_markup()

        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': char}},
            upsert=True
        )
        
        await user_totals_collection.update_one(
            {'user_id': user_id},
            {'$set': {f'claimed_{milestone}': True}},
            upsert=True
        )
        
        if user_id in pending_claims:
            del pending_claims[user_id]
        
        await callback_query.message.edit_caption(
            f"🎉 {rarity} Claimed!\n\n"
            f"{char['name']}\n{char['rarity']}\n{char['anime']}\n\n"
            "✅ Successfully added to your collection!",
            reply_markup=None
        )
        await callback_query.answer()
        
    except Exception as e:
        logging.error(f"Confirmation error: {str(e)}")
        if user_id in pending_claims:
            del pending_claims[user_id]
        await callback_query.answer("Failed to process claim!", show_alert=True)


@app.on_callback_query(filters.regex(r"^tcancel_claim$"))
async def cancel_claim(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in pending_claims:
        del pending_claims[user_id]
    await callback_query.message.edit_caption(
        "❌ Claim cancelled",
        reply_markup=None
    )
    await callback_query.answer("Claim cancelled!", show_alert=True)
