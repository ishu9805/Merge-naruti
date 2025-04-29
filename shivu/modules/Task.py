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

# Global in-memory counter
message_counts = defaultdict(int)
lock = asyncio.Lock()
BATCH_SIZE = 100  # Update DB every 100 messages
SUPPORT_CHAT_ID = -1002606804832
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

@cmd # Updated task_command to handle missing keys safely
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
        
        # Check if all milestones are completed
        user_data = await user_totals_collection.find_one({'user_id': user_id})
        claim_field = f"claimed_{milestone}"
        if not user_data or not user_data.get(claim_field, False):
            all_completed = False
    
    if all_completed:
        response.append("\n🎉 You've completed ALL milestones!")
        response.append("You can reset your tasks with /reset_task to start over")
    
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



@cmd # Updated unified_claim function with proper WVHC handling
@app.on_message(filters.command("nclaim"))
async def unified_claim(client, message):
    if len(message.command) < 2:
        return await message.reply(
            "❌ First complete the /task to claim!\n"
            "Available milestones:\n\n"
            "• /nclaim 300 - 💮 Special Edition (automatic)\n"
            "• /nclaim 700 [id] - 🔮 Limited Edition (choice)\n"
            "• /nclaim 2000 [id] [variant] - 🎁 WVHC Edition (choice)\n"
            "• /nclaim 3500 [id] - 🎐 Celestial Edition (choice)"
        )
    
    try:
        milestone = int(message.command[1])
        user_id = message.from_user.id
        
        if milestone not in TASK_MILESTONES:
            return await message.reply(
                "❌ Invalid milestone! Available milestones:\n"
                "• 300 - 💮 Special Edition\n"
                "• 700 - 🔮 Limited Edition\n"
                "• 2000 - 🎁 WVHC Edition\n"
                "• 3500 - 🎐 Celestial Edition"
            )
        
        # Check ID requirements
        if milestone != 300 and len(message.command) < 3:
            return await message.reply(
                f"❌ Please provide character ID for this reward!\n"
                f"Usage: /nclaim {milestone} [character_id]\n"
                f"Check available characters with /list{milestone}"
            )
        
        # Get user progress
        total_messages = await get_user_count(user_id)
        grab_count = await get_grab_count(user_id)
        required_grabs = TASK_MILESTONES[milestone].get('grab_required', 0)
        
        # Check requirements
        if total_messages < milestone:
            return await message.reply(
                f"❌ You need {milestone} messages to claim this reward! "
                f"You have {total_messages}/{milestone}."
            )
        
        if grab_count < required_grabs:
            return await message.reply(
                f"❌ You need {required_grabs} legendary grabs for this reward! "
                f"You have {grab_count}/{required_grabs}."
            )
        
        # Check if already claimed
        claim_field = f"claimed_{milestone}"
        user_data = await user_totals_collection.find_one({'user_id': user_id})
        if user_data and user_data.get(claim_field):
            return await message.reply("⚠️ You've already claimed this reward!")
        
        # Handle claims based on milestone
        if milestone == 300:
            await handle_automatic_claim(client, message, user_id, milestone, '💮 Special Edition')
        elif milestone == 700:
            char_id = message.command[2]
            await handle_id_claim(client, message, user_id, milestone, char_id, '🔮 Limited Edition')
        elif milestone == 2000:
            char_id = message.command[2]
            if len(message.command) < 4:
                return await message.reply(
                    "❌ Please specify WVHC variant!\n"
                    "Usage: /nclaim 2000 [ID] [VARIANT]\n"
                    "Available variants:\n"
                    "• ❄️ Winter\n• 💝 Valentine\n"
                    "• 🎃 Halloween\n• 🎄 Christmas"
                )
            selected_rarity = ' '.join(message.command[3:])
            await handle_wvhc_claim(client, message, user_id, milestone, char_id, selected_rarity)
        elif milestone == 3500:
            char_id = message.command[2]
            await handle_id_claim(client, message, user_id, milestone, char_id, '🎐 Celestial')
            
    except ValueError:
        await message.reply("❌ Please enter a valid number (300, 700, 2000, or 3500)")
    except Exception as e:
        logging.error(f"Claim error: {str(e)}")
        await message.reply("❌ An error occurred. Please try again later.")

# Updated callback handler for WVHC variants
@cmd
@app.on_callback_query(filters.regex(r"^tttconfirm_(\d+)_(.+?)(?:_(.+))?$"))
async def confirm_claim(client, callback_query):
    try:
        milestone = int(callback_query.matches[0].group(1))
        char_id = callback_query.matches[0].group(2)
        variant_part = callback_query.matches[0].group(3)
        user_id = callback_query.from_user.id
        
        # For WVHC, use the variant from callback data
        if milestone == 2000 and variant_part:
            rarity = variant_part.replace('_', ' ')
        else:
            rarity = TASK_MILESTONES[milestone]['rarity']
        
        char = await collection.find_one({
            'id': char_id,
            'rarity': rarity
        })
        
        if not char:
            await callback_query.answer("Character no longer available!", show_alert=True)
            return await callback_query.message.edit_reply_markup()
        
        # Process the claim
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
        
        await callback_query.message.edit_caption(
            f"🎉 {rarity} Claimed!\n\n"
            f"{char['name']}\n{char['rarity']}\n{char['anime']}\n\n"
            "✅ Successfully added to your collection!",
            reply_markup=None
        )
        await callback_query.answer()
        
    except Exception as e:
        logging.error(f"Confirmation error: {str(e)}")
        await callback_query.answer("Failed to process claim!", show_alert=True)

    
@cmd
async def handle_wvhc_claim(client, message, user_id, milestone, char_id, selected_rarity):
    """Special handler for WVHC seasonal variants"""
    valid_rarities = ['❄️ Winter', '💝 Valentine', '🎃 Halloween', '🎄 Christmas']
    
    if selected_rarity not in valid_rarities:
        return await message.reply(
            "❌ Invalid WVHC variant! Choose from:\n"
            "• ❄️ Winter\n• 💝 Valentine\n"
            "• 🎃 Halloween\n• 🎄 Christmas"
        )
    
    char = await collection.find_one({
        'id': char_id,
        'rarity': selected_rarity
    })
    
    if not char:
        return await message.reply(
            f"❌ Character {char_id} not found as {selected_rarity} variant!\n"
            "Use /list2000 to see available options."
        )
    
    sup = char.get('slock')
    if sup == 'True':
        return await message.reply("❌ This character is locked and cannot be claimed!")
    
    # Rest of the claim processing remains same as handle_id_claim
    confirm_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Claim", callback_data=f"tttconfirm_{milestone}_{char_id}_{selected_rarity}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="tcancel_claim")]
    ])
    
    await message.reply_photo(
        char['img_url'],
        caption=f"⚠️ Confirm {selected_rarity} Claim:\n\n"
                f"{char['name']}\n{char['rarity']}\n{char['anime']}\n\n"
                "Are you sure?",
                reply_markup=confirm_buttons
    )



@cmd
async def handle_automatic_claim(client, message, user_id, milestone, rarity):
    """Handle automatic claims (no ID needed)"""
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

@cmd
async def handle_id_claim(client, message, user_id, milestone, char_id, rarity):
    """Handle claims requiring character ID"""
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
    # Add confirmation step
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


@cmd
@app.on_message(filters.command("reset_task"))
async def reset_task_command(client, message):
    user_id = message.from_user.id
    
    # Check if user has completed all milestones
    user_data = await user_totals_collection.find_one({'user_id': user_id})
    if not user_data:
        return await message.reply("❌ You haven't started any tasks yet!")
    
    
    confirm_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Reset", callback_data=f"confirm_reset_{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_reset")]
    ])
    
    await message.reply(
        "⚠️ This will reset ALL your task progress and claimed rewards!\n"
        "You'll need to complete all milestones again.\n\n"
        "Are you sure you want to reset?",
        reply_markup=confirm_buttons
    )


@cmd
@app.on_callback_query(filters.regex(r"^confirm_reset_(\d+)$"))
async def confirm_reset(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))
    if callback_query.from_user.id != user_id:
        return await callback_query.answer("This reset confirmation isn't for you!", show_alert=True)
    
    # Reset all task progress
    
    
    # Reset message count (both in DB and memory)
    async with lock:
        message_counts[user_id] = 0
    
    await user_totals_collection.delete_one(
        {'user_id': user_id}
        
    )
    await user_collection.update_one(
        {'id': user_id},
        {"$unset": {"grab": ""}}
        
    )
    await callback_query.message.edit_text(
        "♻️ All your task progress has been reset!\n"
        "You can now start completing milestones again from scratch."
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^cancel_reset$"))
async def cancel_reset(client, callback_query):
    await callback_query.message.edit_text("✅ Task reset cancelled. Your progress remains unchanged.")
    await callback_query.answer()



