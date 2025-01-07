from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
from shivu import user_collection, ban_collection
from shivu import shivuu, user_count


from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
from shivu import user_collection, ban_collection
from shivu import shivuu

# Global variables to track pending gifts, trades, locks, and cooldowns
pending_gifts = {}          # Store pending gifts
pending_trades = {}         # Store pending trades
locked_users = set()        # Track users currently engaged in any process
locked_characters = set()   # Track characters currently involved in any process
cooldowns = {}              # Track users and their last confirmed gift or trade time
active_buttons = {}         # Track active buttons
lock = set()                # Set to track active callback processes

# Gift Command
@shivuu.on_message(filters.command("gift"))
async def gift(client, message):
    sender_id = message.from_user.id

    is_banned = await ban_collection.find_one({"user_id": sender_id})
    if is_banned:
        return

    # Check if the user has recently confirmed a gift (15 sec cooldown)
    if sender_id in cooldowns:
        time_since_last_gift = time.time() - cooldowns[sender_id]
        if time_since_last_gift < 15:  # Cooldown of 15 seconds
            await message.reply_text(f"⏳ Please wait **{int(15 - time_since_last_gift)} seconds** before gifting again!")
            return

    # Check if the user is locked (in an ongoing process)
    if sender_id in locked_users:
        await message.reply_text("⚠️ **You already have a pending process!** Complete it before starting another or use /dreset.")
        return    

    if not message.reply_to_message:
        await message.reply_text("❗ **Reply to a user's message** to gift a character!")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    # Prevent gifting to self
    if sender_id == receiver_id:
        await message.reply_text("🙅‍♂️ **You can't gift a character to yourself!**")
        return

    # Ensure the command includes a character ID
    if len(message.command) != 2:
        await message.reply_text("⚙️ **You need to provide a valid character ID!**")
        return

    character_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})

    # Check if the sender has the character
    character = next((character for character in sender['characters'] if character['id'] == character_id), None)

    if not character:
        await message.reply_text("❌ **You don't own this character** you are trying to gift!")
        return
    
    # Check if the character is locked (already in a pending transaction)
    if character_id in locked_characters:
        await message.reply_text("🔒 **This character is already involved in another transaction!**")
        return

    # Lock the user and the character
    locked_users.add(sender_id)
    locked_characters.add(character_id)
    
    # Create a unique identifier for the gift process (using timestamp)
    process_id = str(time.time())

    # Store pending gift data
    sent_message = await message.reply_text(
        f"🎁 {message.from_user.mention}, do you confirm gifting this character?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✅ Confirm Gift", callback_data=f"confirm_gift:{process_id}")],
                [InlineKeyboardButton("❌ Cancel Gift", callback_data=f"cancel_gift:{process_id}")]
            ]
        ))

    pending_gifts[(sender_id, receiver_id)] = {
        'character': character,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name,
        'process_id': process_id  # Track the unique process ID
    }

    # Mark the buttons as active
    active_buttons[(sender_id, process_id)] = True

# Callback for Confirming or Cancelling Gift
@shivuu.on_callback_query(filters.create(lambda _, __, query: query.data.startswith(("confirm_gift:", "cancel_gift:"))))
async def on_callback_query(client, callback_query):
    sender_id = callback_query.from_user.id
    data, process_id = callback_query.data.split(":")

    # Check if the callback is already being processed
    if process_id in lock:
        await callback_query.answer("❗ This action is already being processed!", show_alert =True)
        return

    # Add the process_id to the lock
    lock.add(process_id)

    # Check if the button is still active
    if not active_buttons.get((sender_id, process_id), False):
        await callback_query.answer("❗ This action is no longer valid!", show_alert=True)
        lock.remove(process_id)  # Remove from lock if action is invalid
        return

    for (s_id, r_id), gift in list(pending_gifts.items()):
        if s_id == sender_id and gift['process_id'] == process_id:
            break
    else:
        await callback_query.answer("❗ This action is no longer valid!", show_alert=True)
        lock.remove(process_id)  # Remove from lock if action is invalid
        return

    # Process confirmation or cancellation of gift
    if data == "confirm_gift":
        await callback_query.answer("✅ Gift successfully given!", show_alert=True)
        
        await callback_query.message.edit_text(
            f"🎉 **You have successfully gifted your character to** [{gift['receiver_first_name']}](tg://user?id={r_id})! 🥳")

        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': r_id})

        # Remove the character from the sender's collection
        sender['characters'].remove(gift['character'])
        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})

        # Add the character to the receiver's collection
        if receiver:
            await user_collection.update_one({'id': r_id}, {'$push': {'characters': gift['character']}})
        else:
            await user_collection.insert_one({
                'id': r_id,
                'username': gift['receiver_username'],
                'first_name': gift['receiver_first_name'],
                'characters': [gift['character']],
            })

        await user_count.update_one(
            {'user_id': sender_id},
            {'$inc': {'ccount': -1}},
            upsert=True
        ) 
        await user_count.update_one(
            {'user_id': r_id},
            {'$inc': {'ccount': 1}},
            upsert=True
        )        
        # Set the cooldown for the sender (15 seconds from now)
        cooldowns[sender_id] = time.time()

        # Clean up: remove the lock and pending gift
        del pending_gifts[(sender_id, r_id)]
        locked_users.remove(sender_id)
        locked_characters.remove(gift['character']['id'])

    elif data == "cancel_gift":
        # Remove the pending gift and unlock the user and character
        del pending_gifts[(sender_id, r_id)]
        locked_users.remove(sender_id)
        locked_characters.remove(gift['character']['id'])

        await callback_query.message.edit_text("❌ **Gift process cancelled.**")

    # Mark the buttons as inactive after processing
    active_buttons[(sender_id, process_id)] = False

    # Remove the process_id from the lock
    lock.remove(process_id)               
                

 # Trade Command
@shivuu.on_message(filters.command("trade"))
async def trade(client, message):
    sender_id = message.from_user.id

    is_banned = await ban_collection.find_one({"user_id": sender_id})
    if is_banned:
        return
    # Check if the user has recently confirmed a trade (15 sec cooldown)
    if sender_id in cooldowns:
        time_since_last_trade = time.time() - cooldowns[sender_id]
        if time_since_last_trade < 15:  # Cooldown of 15 seconds
            await message.reply_text(f"⏳ Please wait **{int(15 - time_since_last_trade)} seconds** before trading again!")
            return

    # Check if the user is locked (in an ongoing process)
    if sender_id in locked_users:
        await message.reply_text("⚠️ **You already have a pending process!** Complete it before starting another or use /dreset.")
        return    

    if not message.reply_to_message:
        await message.reply_text("❗ **Reply to a user's message** to initiate a trade!")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    # Prevent trading with self
    if sender_id == receiver_id:
        await message.reply_text("🙅‍♂️ **You can't trade with yourself!**")
        return

    # Ensure the command includes both character IDs
    if len(message.command) != 3:
        await message.reply_text("⚙️ **You need to provide both character IDs for the trade!**")
        return

    sender_character_id = message.command[1]
    receiver_character_id = message.command[2]

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    # Check if the sender has the character to trade
    sender_character = next((char for char in sender['characters'] if char['id'] == sender_character_id), None)
    if not sender_character:
        await message.reply_text("❌ **You don't own this character** you are trying to trade!")
        return

    # Check if the receiver has the character to trade
    receiver_character = next((char for char in receiver['characters'] if char['id'] == receiver_character_id), None)
    if not receiver_character:
        await message.reply_text("❌ **The user you're trying to trade with doesn't own this character!**")
        return

    # Check if either character is locked (already involved in another transaction)
    if sender_character_id in locked_characters or receiver_character_id in locked_characters:
        await message.reply_text("🔒 **One or both of the characters are already involved in another transaction!**")
        return

    # Lock the users and characters
    locked_users.add(sender_id)
    locked_users.add(receiver_id)
    locked_characters.add(sender_character_id)
    locked_characters.add(receiver_character_id)

    # Create a unique identifier for the trade process
    process_id = str(time.time())

    # Store pending trade data
    sent_message = await message.reply_text(
        f"🎁 {message.from_user.mention} has proposed a trade. **{receiver_first_name}**, do you accept?",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✅ Accept Trade", callback_data=f"confirm_trade_receiver:{process_id}")],
                [InlineKeyboardButton("❌ Reject Trade", callback_data=f"cancel_trade:{process_id}")]
            ]
        ))

    pending_trades[(sender_id, receiver_id)] = {
        'sender_character': sender_character,
        'receiver_character': receiver_character,
        'receiver_id': receiver_id,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name,
        'process_id': process_id  # Track the unique process ID
    }

# Callback for Confirming or Cancelling Trade
@shivuu.on_callback_query(filters.create(lambda _, __, query: query.data.startswith(("confirm_trade_receiver:", "cancel_trade:"))))
async def on_trade_callback_query(client, callback_query):
    sender_id = callback_query.from_user.id
    data, process_id = callback_query.data.split(":")

    for (s_id, r_id), trade in list(pending_trades.items()):
        # Ensure only the receiver (not sender) can confirm or cancel the trade
        if r_id == sender_id and trade['process_id'] == process_id:
            break
    else:
        await callback_query.answer("❗ This action is no longer valid or you are not authorized to perform it!", show_alert=True)
        return

    # Process confirmation or cancellation of trade
    if data == "confirm_trade_receiver":
        await callback_query.answer("✅ Trade successfully completed!", show_alert=True)

        await callback_query.message.edit_text(
            f"🎉 **The trade has been successfully completed between** [{trade['receiver_first_name']}](tg://user?id={r_id}) and [{s_id}](tg://user?id={s_id})! 🥳")

        sender = await user_collection.find_one({'id': s_id})
        receiver = await user_collection.find_one({'id': r_id})

        # Swap the characters between sender and receiver
        sender['characters'].remove(trade['sender_character'])
        receiver['characters'].remove(trade['receiver_character'])
        sender['characters'].append(trade['receiver_character'])
        receiver['characters'].append(trade['sender_character'])

        # Update the user collections in the database
        await user_collection.update_one({'id': s_id}, {'$set': {'characters': sender['characters']}})
        await user_collection.update_one({'id': r_id}, {'$set': {'characters': receiver['characters']}})

        # Set the cooldown for the sender (15 seconds from now)
        cooldowns[s_id] = time.time()

        # Clean up: remove the lock and pending trade
        del pending_trades[(s_id, r_id)]
        locked_users.remove(s_id)
        locked_users.remove(r_id)
        locked_characters.remove(trade['sender_character']['id'])
        locked_characters.remove(trade['receiver_character']['id'])

    elif data == "cancel_trade":
        # Remove the pending trade and unlock the users and characters
        del pending_trades[(s_id, r_id)]
        locked_users.remove(s_id)
        locked_users.remove(r_id)
        locked_characters.remove(trade['sender_character']['id'])
        locked_characters.remove(trade['receiver_character']['id'])

        await callback_query.message.edit_text("❌ **Trade process cancelled.**")
        

        
# Reset command to clear any pending processes
@shivuu.on_message(filters.command("dreset"))
async def reset_process(client, message):
    user_id = message.from_user.id
    if user_id in locked_users:
        # Remove any pending gift for the user
        pending_gifts_to_remove = [key for key in pending_gifts if key[0] == user_id or key[1] == user_id]
        for key in pending_gifts_to_remove:
            locked_characters.remove(pending_gifts[key]['character']['id'])
            del pending_gifts[key]

        # Remove any pending trade for the user
        pending_trades_to_remove = [key for key in pending_trades if key[0] == user_id or key[1] == user_id]
        for key in pending_trades_to_remove:
            locked_characters.remove(pending_trades[key]['sender_character']['id'])
            locked_characters.remove(pending_trades[key]['receiver_character']['id'])
            del pending_trades[key]

        locked_users.remove(user_id)
        await message.reply_text("✅ **All pending processes have been cleared!**")
    else:
        await message.reply_text("❗ **You don't have any pending processes to reset.**")
        
