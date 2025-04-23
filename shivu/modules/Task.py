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


@app.on_message(filters.command("nclaim"))
async def unified_claim(client, message):
    if len(message.command) < 2:
        return await message.reply(
            "❌ Please specify a milestone to claim!\n"
            "Available milestones:\n"
            "• /claim 300 - 💮 Special Edition (automatic)\n"
            "• /claim 700 [id] - 🔮 Limited Edition\n"
            "• /claim 2000 [id] - 🎁 WVHC Edition\n"
            "• /claim 3500 [id] - 🎐 Celestial Edition"
        )
    
    try:
        milestone = int(message.command[1])
        user_id = message.from_user.id
        
        # Check if milestone is valid
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
                f"Usage: /claim {milestone} [character_id]\n"
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
            await handle_id_claim(client, message, user_id, milestone, char_id, 'WVHC')
        elif milestone == 3500:
            char_id = message.command[2]
            await handle_id_claim(client, message, user_id, milestone, char_id, '🎐 Celestial')
            
    except ValueError:
        await message.reply("❌ Please enter a valid number (300, 700, 2000, or 3500)")
    except Exception as e:
        logging.error(f"Claim error: {str(e)}")
        await message.reply("❌ An error occurred. Please try again later.")

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

# Callback handler for confirmation
@app.on_callback_query(filters.regex(r"^tttconfirm_(\d+)_(.+)$"))
async def confirm_claim(client, callback_query):
    try:
        milestone = int(callback_query.matches[0].group(1))
        char_id = callback_query.matches[0].group(2)
        user_id = callback_query.from_user.id
        
        # Get the appropriate rarity for this milestone
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

# List commands for each milestone
@app.on_message(filters.command("list700"))
async def list_limited_chars(client, message):
    await list_available_chars(client, message, '🔮 Limited Edition')

@app.on_message(filters.command("list2000"))
async def list_wvhc_chars(client, message):
    await list_available_chars(client, message, 'WVHC')

@app.on_message(filters.command("list3500"))
async def list_celestial_chars(client, message):
    await list_available_chars(client, message, '🎐 Celestial')

async def list_available_chars(client, message, rarity):
    chars = await collection.find(
        {'rarity': rarity},
        {'id': 1, 'name': 1, 'anime': 1, 'img_url': 1}
    ).to_list(length=50)
    
    if not chars:
        return await message.reply(f"❌ No {rarity} characters available!")
    
    # Send as media group if more than 5 characters
    if len(chars) > 5:
        media_group = []
        for char in chars[:10]:  # Limit to 10 to avoid flooding
            media_group.append(
                InputMediaPhoto(
                    media=char['img_url'],
                    caption=f"ID: {char['id']}\n{char['name']} ({char['anime']})"
                )
            )
        await client.send_media_group(
            chat_id=message.chat.id,
            media=media_group
        )
        await message.reply(
            f"🔍 Available {rarity} Characters\n\n"
            "Use /claim [milestone] [id] to claim\n"
            f"Example: /claim {TASK_MILESTONES[list(TASK_MILESTONES.keys())[list(TASK_MILESTONES.values()).index({'rarity': rarity})]]} {chars[0]['id']}"
        )
    else:
        char_list = "\n".join(
            f"• {char['id']} - {char['name']} ({char['anime']})"
            for char in chars
        )
        await message.reply(
            f"🔍 Available {rarity} Characters:\n\n"
            f"{char_list}\n\n"
            "Use /claim [milestone] [id] to claim\n"
            f"Example: /claim {TASK_MILESTONES[list(TASK_MILESTONES.keys())[list(TASK_MILESTONES.values()).index({'rarity': rarity})]]} {chars[0]['id']}"
    )
