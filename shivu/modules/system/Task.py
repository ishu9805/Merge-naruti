import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import random
import time
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from shivu.modules import sudo_filter, dev_filter
from shivu import (
    collectionps as collection,
    user_collectionps as user_collection,
    user_totals_collectionps as user_totals_collection,
    shivuups as app,
    OWNER_ID
)

from shivu.modules.lock import command_lock as cmd



# Initialize global variables
claim_locks = defaultdict(asyncio.Lock)
pending_claims = {}
character_claims = defaultdict(int)  # Tracks global claim counts per character
message_counts = defaultdict(int)
lock = asyncio.Lock()
BATCH_SIZE = 100
SUPPORT_CHAT_ID = -1002606804832
MAX_OWNERS = 10  # For limited edition characters
CLAIM_TIMEOUT = 300  # 5 minutes for pending claims

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("shivu_claims.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Milestone configuration
TASK_MILESTONES = {
    300: {
        'type': 'special',
        'rarity': '💮 Special Edition',
        'message': "🎉 300 messages! Claim your 💮 Special Edition with /sclaim",
        'grab_required': 3
    },
    1000: {
        'type': 'limited', 
        'rarity': '🔮 Limited Edition',
        'message': "🌟 1000 messages! Choose 🔮 Limited Edition with /lclaim",
        'grab_required': 5
    }
}

# Helper Functions
async def acquire_user_lock(user_id):
    """Acquire a lock for a user to prevent concurrent claims"""
    try:
        await asyncio.wait_for(claim_locks[user_id].acquire(), timeout=30)
        return True
    except asyncio.TimeoutError:
        logger.warning(f"Timeout acquiring lock for user {user_id}")
        return False

async def release_user_lock(user_id):
    """Release the lock for a user"""
    if claim_locks[user_id].locked():
        claim_locks[user_id].release()

async def get_user_count(user_id):
    """Get total message count for a user (in-memory + database)"""
    async with lock:
        in_memory = message_counts.get(user_id, 0)
    user_data = await user_totals_collection.find_one({'user_id': user_id})
    db_count = user_data.get('count', 0) if user_data else 0
    return db_count + in_memory

async def get_grab_count(user_id):
    """Get total grab count for a user"""
    user_data = await user_collection.find_one({'id': user_id})
    return user_data.get('grab', 0) if user_data else 0

async def update_character_claims():
    """Initialize character claim counts from database"""
    logger.info("Updating character claim counts from database...")
    async for char in collection.find({}):
        owners = await user_collection.count_documents({
            'characters.id': char['id']
        })
        character_claims[char['id']] = owners
    logger.info(f"Updated claim counts for {len(character_claims)} characters")

async def get_character_claim_count(char_id):
    """Get current claim count for a character"""
    if not character_claims:  # First run
        await update_character_claims()
    return character_claims.get(char_id, 0)

async def increment_character_claim(char_id):
    """Increment claim count for a character"""
    character_claims[char_id] = character_claims.get(char_id, 0) + 1
    logger.info(f"Incremented claim count for character {char_id} to {character_claims[char_id]}")



async def validate_claim_requirements(user_id, milestone):
    """Validate if user meets all requirements for a claim"""
    if milestone not in TASK_MILESTONES:
        return False, "❌ Invalid milestone! Available milestones:\n• 300 - 💮 Special Edition\n• 1000 - 🔮 Limited Edition"
    
    total_messages = await get_user_count(user_id)
    if total_messages < milestone:
        return False, f"❌ You need {milestone} messages to claim this reward! You have {total_messages}/{milestone}."
    
    grab_count = await get_grab_count(user_id)
    required_grabs = TASK_MILESTONES[milestone].get('grab_required', 0)
    if grab_count < required_grabs:
        return False, f"❌ You need {required_grabs} legendary grabs for this reward! You have {grab_count}/{required_grabs}."
    
    claim_field = f"claimed_{milestone}"
    user_data = await user_totals_collection.find_one({'user_id': user_id})
    if user_data and user_data.get(claim_field):
        return False, "⚠️ You've already claimed this reward!"
    
    return True, ""

# Commands
@cmd
@app.on_message(filters.command("task"))
async def task_command(client, message):
    """Show user's task progress and available rewards"""
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
    
    await message.reply_text("\n".join(response))

@cmd
@app.on_message(filters.command("resetclaim"))
async def reset_pending_claim(client, message):
    """Allow users to reset their pending claims"""
    user_id = message.from_user.id
    
    if user_id not in pending_claims:
        return await message.reply("ℹ️ You don't have any pending claims to reset.")
    
    try:
        char_id = pending_claims[user_id]['char_id']
        del pending_claims[user_id]
        logger.info(f"User {user_id} reset their pending claim for character {char_id}")
        await message.reply("✅ Your pending claim has been reset. You can now make new claims.")
    except Exception as e:
        logger.error(f"Error resetting claim for user {user_id}: {str(e)}")
        await message.reply("❌ Failed to reset your claim. Please try again later.")

@cmd
@app.on_message(filters.command("nclaim"))
async def unified_claim(client, message):
    """Handle all types of claims through a unified command"""
    user_id = message.from_user.id
    
    # Check for pending claims
    if user_id in pending_claims:
        claim_data = pending_claims[user_id]
        await message.reply(
            f"⚠️ You have a pending {claim_data['rarity']} claim!\n"
            f"Character: {claim_data['char_name']}\n"
            "Please confirm or cancel it with /resetclaim before making new claims."
        )
        return
    
    # Acquire user lock
    if not await acquire_user_lock(user_id):
        return await message.reply("🚫 The system is currently processing your previous request. Please wait a moment and try again.")
    00
    try:
        if len(message.command) < 2:
            await release_user_lock(user_id)
            return await message.reply(
                "❌ First complete the /task to claim!\n"
                "Available milestones:\n\n"
                "• /nclaim 300 - 💮 Special Edition (automatic)\n"
                "• /nclaim 1000 [id] - 🔮 Limited Edition (choice)\n"
            )
        
        milestone = int(message.command[1])
        
        # Validate claim requirements
        is_valid, error_msg = await validate_claim_requirements(user_id, milestone)
        if not is_valid:
            await release_user_lock(user_id)
            return await message.reply(error_msg)
        
        # Handle different claim types
        if milestone == 300:
            await handle_automatic_claim(client, message, user_id, milestone, '💮 Special Edition')
        elif milestone == 1000:
            if len(message.command) < 3:
                await release_user_lock(user_id)
                return await message.reply(
                    f"❌ Please provide character ID for this reward!\n"
                    f"Usage: /nclaim {milestone} [character_id]\n"
                    f"Check available characters with /list{milestone}"
                )
            char_id = message.command[2]
            await handle_id_claim(client, message, user_id, milestone, char_id, '🔮 Limited Edition')
        else:
            await release_user_lock(user_id)
            return await message.reply("❌ Invalid milestone! Available: 300 or 1000")
            
    except ValueError:
        await release_user_lock(user_id)
        await message.reply("❌ Please enter a valid number (300 or 1000)")
    except Exception as e:
        logger.error(f"Claim processing error for user {user_id}: {str(e)}", exc_info=True)
        await message.reply("❌ An error occurred while processing your claim. Please try again later.")
        await release_user_lock(user_id)

async def handle_automatic_claim(client, message, user_id, milestone, rarity):
    """Handle automatic claim for special edition characters"""
    try:
        char = await collection.aggregate([
            {'$match': {'rarity': rarity}},
            {'$sample': {'size': 1}}
        ]).to_list(length=1)
        
        if not char:
            await release_user_lock(user_id)
            return await message.reply(f"⚠️ No {rarity} characters available!")
        
        char = char[0]
        
        # Check owner count for limited edition
        if rarity == '🔮 Limited Edition':
            owner_count = await get_character_claim_count(char['id'])
            if owner_count >= MAX_OWNERS:
                await release_user_lock(user_id)
                return await message.reply("❌ This Limited Edition character has reached maximum claims! Try another one.")
        
        # Process the claim
        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': char}},
            upsert=True
        )
        
        # Update claim count if limited edition
        if rarity == '🔮 Limited Edition':
            await increment_character_claim(char['id'])
        
        # Mark as claimed
        await user_totals_collection.update_one(
            {'user_id': user_id},
            {'$set': {f'claimed_{milestone}': True}},
            upsert=True
        )
        
        # Send success message
        await message.reply_photo(
            char['img_url'],
            caption=f"🎉 {rarity} Claimed!\n\n{char['name']}\n{char['rarity']}\n{char['anime']}"
        )
        
    except Exception as e:
        logger.error(f"Error in automatic claim for user {user_id}: {str(e)}")
        await message.reply("❌ Failed to process automatic claim. Please try again.")
    finally:
        await release_user_lock(user_id)

async def handle_id_claim(client, message, user_id, milestone, char_id, rarity):
    """Handle claim with specific character ID"""
    try:
        # Check claim count first
        claim_count = await get_character_claim_count(char_id)
        if claim_count >= MAX_OWNERS:
            await release_user_lock(user_id)
            return await message.reply(
                "❌ This character has reached the maximum claim limit (4 users).\n"
                "Please choose another character with /list1000"
            )

        char = await collection.find_one({
            'id': char_id,
            'rarity': rarity
        })
        
        if not char:
            await release_user_lock(user_id)
            return await message.reply(
                f"❌ Character not found or not {rarity}!\n"
                f"Use /list{milestone} to see available options."
            )

        sup = char.get('slock')
        if sup == 'True':
            await release_user_lock(user_id)
            return await message.reply("❌ This character is locked and cannot be claimed!")
        
        # Store pending claim
        pending_claims[user_id] = {
            'char_id': char_id,
            'milestone': milestone,
            'char_name': char['name'],
            'rarity': rarity,
            'message_id': message.id,
            'timestamp': time.time()
        }
        
        # Create confirmation buttons
        confirm_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm Claim", callback_data=f"confirm_{milestone}_{char_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_claim")]
        ])
        
        # Send confirmation message
        sent_msg = await message.reply_photo(
            char['img_url'],
            caption=f"⚠️ Confirm {rarity} Claim:\n\n"
                    f"{char['name']}\n{char['rarity']}\n{char['anime']}\n\n"
                    "Are you sure?",
            reply_markup=confirm_buttons
        )
        
        pending_claims[user_id]['confirmation_message_id'] = sent_msg.id
        
    except Exception as e:
        logger.error(f"Error in ID claim for user {user_id}: {str(e)}")
        await message.reply("❌ Failed to process claim. Please try again.")
        await release_user_lock(user_id)

# Callback Handlers
@app.on_callback_query(filters.regex(r"^confirm_(\d+)_(.+)$"))
async def confirm_claim(client, callback_query):
    """Handle claim confirmation with global count tracking"""
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if user_id not in pending_claims:
        await callback_query.answer("No pending claim found!", show_alert=True)
        return await callback_query.message.delete()
    
    try:
        milestone = int(data.split('_')[1])
        char_id = data.split('_')[2]
        
        pending_data = pending_claims[user_id]
        if pending_data['char_id'] != char_id or pending_data['milestone'] != milestone:
            await callback_query.answer("Claim data mismatch!", show_alert=True)
            return await callback_query.message.delete()
        
        rarity = TASK_MILESTONES[milestone]['rarity']
        char = await collection.find_one({'id': char_id, 'rarity': rarity})
        
        if not char:
            await callback_query.answer("Character no longer available!", show_alert=True)
            if user_id in pending_claims:
                del pending_claims[user_id]
            return await callback_query.message.delete()
        

        # Process the claim
        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': char}},
            upsert=True
        )
        
        # Update global claim count for limited edition
        if rarity == '🔮 Limited Edition':
            await increment_character_claim(char_id)
        
        # Mark as claimed
        await user_totals_collection.update_one(
            {'user_id': user_id},
            {'$set': {f'claimed_{milestone}': True}},
            upsert=True
        )
        
        # Update the message
        await callback_query.message.edit_caption(
            f"🎉 {rarity} Claimed!\n\n"
            f"{char['name']}\n{char['rarity']}\n{char['anime']}\n\n"
            "✅ Successfully added to your collection!",
            reply_markup=None
        )
        
        if user_id in pending_claims:
            del pending_claims[user_id]
            
        await callback_query.answer("Claim successful!", show_alert=False)
        
    except Exception as e:
        logger.error(f"Error in confirm_claim: {str(e)}", exc_info=True)
        await callback_query.answer("Failed to process claim!", show_alert=True)
        if user_id in pending_claims:
            del pending_claims[user_id]

@app.on_callback_query(filters.regex(r"^cancel_claim$"))
async def cancel_claim(client, callback_query):
    """Handle claim cancellation"""
    user_id = callback_query.from_user.id
    if user_id in pending_claims:
        del pending_claims[user_id]
    
    try:
        await callback_query.message.edit_caption(
            "❌ Claim cancelled",
            reply_markup=None
        )
        await callback_query.answer("Claim cancelled!", show_alert=False)
    except Exception as e:
        logger.error(f"Error cancelling claim: {str(e)}")
        await callback_query.answer("Failed to cancel claim!", show_alert=True)






@cmd
@app.on_message(filters.command("tpending"))
async def reset_pending_claim(client, message):  # noqa: F811
    """Allow users to reset their pending claims"""
    user_id = message.from_user.id
    
    if user_id not in pending_claims:
        return await message.reply("ℹ️ You don't have any pending claims to reset.")
    
    try:
        # Get pending claim details
        pending_data = pending_claims[user_id]
        char_name = pending_data['char_name']
        rarity = pending_data['rarity']
        
        # Create confirmation buttons
        confirm_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, reset my claim", callback_data="confirm_nreset")],
            [InlineKeyboardButton("❌ No, keep it", callback_data="cancel_nreset")]
        ])
        
        # Send confirmation message
        await message.reply(
            f"⚠️ Are you sure you want to reset your pending {rarity} claim?\n"
            f"Character: {char_name}\n\n"
            "You'll be able to make a new claim after resetting.",
            reply_markup=confirm_buttons
        )
        
    except Exception as e:
        logger.error(f"Error preparing reset for user {user_id}: {str(e)}")
        await message.reply("❌ Failed to process reset request. Please try again later.")

@app.on_callback_query(filters.regex(r"^confirm_nreset$"))
async def confirm_reset_claim(client, callback_query):
    """Handle reset confirmation"""
    user_id = callback_query.from_user.id
    
    if user_id not in pending_claims:
        await callback_query.answer("No pending claim to reset!", show_alert=True)
        return await callback_query.message.delete()
    
    try:
        # Get pending claim details before deleting
        pending_data = pending_claims[user_id]
        char_name = pending_data['char_name']
        rarity = pending_data['rarity']
        
        # Remove the pending claim
        del pending_claims[user_id]
        
        # Update the message
        await callback_query.message.edit_text(
            f"✅ Your pending {rarity} claim for {char_name} has been reset.\n"
            "You can now make a new claim when ready.",
            reply_markup=None
        )
        
        await callback_query.answer("Claim reset successful!", show_alert=False)
        logger.info(f"User {user_id} reset their pending claim for {char_name}")
        
    except Exception as e:
        logger.error(f"Error confirming reset for user {user_id}: {str(e)}")
        await callback_query.answer("Failed to reset claim!", show_alert=True)

@app.on_callback_query(filters.regex(r"^cancel_nreset$"))
async def cancel_reset_claim(client, callback_query):
    """Handle reset cancellation"""
    user_id = callback_query.from_user.id
    
    try:
        await callback_query.message.edit_text(
            "❌ Reset cancelled. Your pending claim remains active.",
            reply_markup=None
        )
        await callback_query.answer("Reset cancelled", show_alert=False)
    except Exception as e:
        logger.error(f"Error cancelling reset for user {user_id}: {str(e)}")
        await callback_query.answer("Failed to cancel reset!", show_alert=True)

