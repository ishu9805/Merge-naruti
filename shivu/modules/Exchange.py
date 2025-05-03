import pytz
import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from shivu import collectionps as collection, user_collectionps as user_collection, shivuups as app
from . import sudo_filter
from .block import block_dec, temp_block



# List of prohibited rarities that cannot be exchanged
PROHIBITED_RARITIES = [
    "💸 Premium Edition",
    "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣",
    "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
    "🍑 Echhi",
    "🧧 𝙀𝙫𝙚𝙣𝙩𝙨",
    "🎭 Cosplay Master 🎭",
    "🎖 Apex Lot ( AUCTION )"
]

async def exchange_command(client: Client, message: Message, args: list[str]) -> None:
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(tz)

    # Allow exchanges on both Saturday (5) and Sunday (6)
    if now.weekday() not in [5, 6]:
        await message.reply_text("The /exchange command is only available on weekends (Saturday and Sunday).")
        return

    start_time = tz.localize(datetime.datetime.combine(now.date(), datetime.time(5, 30)))
    end_time = tz.localize(datetime.datetime.combine(now.date(), datetime.time(0, 30))) + datetime.timedelta(days=1)

    if not (start_time <= now <= end_time):
        await message.reply_text("The /exchange command is only available between 5:30 am and 12:30 midnight on weekends.")
        return

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await user_collection.insert_one({
            'id': user_id,
            'exchange_count': 0,
            'last_exchange': datetime.datetime.combine(now.date(), datetime.time.min, tz)
        })
        exchange_count = 0
    else:
        exchange_count = user_data.get('exchange_count', 0)
        last_exchange = user_data.get('last_exchange', None)
        if last_exchange is None or last_exchange.date() != now.date():
            # Reset exchange count and update the last_exchange date for a new day
            exchange_count = 0
            await user_collection.update_one(
                {'id': user_id},
                {
                    '$set': {
                        'exchange_count': 0,
                        'last_exchange': datetime.datetime.combine(now.date(), datetime.time.min, tz)
                    }
                }
            )

    # Increased limit to 5 exchanges per week
    if exchange_count >= 2:
        await message.reply_text("You've already used all 2 of your weekly exchanges.")
        return

    if len(args) != 2:
        await message.reply_text("Please use the command like this: /exchange <your_character_id> <desired_character_id>")
        return

    your_character_id = args[0]
    desired_character_id = args[1]

    if not user_data or 'characters' not in user_data:
        await message.reply_text("You don't have any characters to exchange.")
        return

    user_characters = user_data['characters']
    character_to_exchange = next((char for char in user_characters if char['id'] == your_character_id), None)

    if not character_to_exchange:
        await message.reply_text("You don't own the character you're trying to exchange.")
        return

    desired_character = await collection.find_one({'id': desired_character_id})
    if not desired_character:
        await message.reply_text("Couldn't find the character you want. Please check the ID and try again.")
        return

    # Check if desired character is in prohibited rarities
    if desired_character.get('rarity') in PROHIBITED_RARITIES:
        prohibited_list = "\n".join(PROHIBITED_RARITIES)
        await message.reply_text(
            f"Sorry, you can't exchange for these rarities:\n{prohibited_list}\n"
            f"The character you want is {desired_character['rarity']} rarity."
        )
        return

    # Check if rarities match
    if character_to_exchange.get('rarity') != desired_character.get('rarity'):
        await message.reply_text(
            "You can only exchange characters of the same rarity.\n"
            f"Your character: {character_to_exchange['rarity']}\n"
            f"Desired character: {desired_character['rarity']}"
        )
        return

    index_to_remove = next((i for i, char in enumerate(user_characters) if char['id'] == your_character_id), None)

    if index_to_remove is None:
        await message.reply_text("Something went wrong with the exchange. Please try again.")
        return

    new_characters = user_characters[:index_to_remove] + user_characters[index_to_remove + 1:]

    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'characters': new_characters}}
    )

    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': desired_character}}
    )

    updated_exchange_count = exchange_count + 1
    remaining_exchanges = 5 - updated_exchange_count

    # Update exchange count and last_exchange
    await user_collection.update_one(
        {'id': user_id},
        {'$set': {'exchange_count': updated_exchange_count, 'last_exchange': now}}
    )

    await message.reply_text(
        f"✅ Exchange successful!\n"
        f"You exchanged {character_to_exchange['name']} ({character_to_exchange['rarity']})\n"
        f"For {desired_character['name']} ({desired_character['rarity']})"
    )
    await message.reply_text(f"You have {remaining_exchanges} exchanges left this week.")

@app.on_message(filters.command("exchange"))
@block_dec
async def handle_exchange_command(client: Client, message: Message):
    args = message.text.split()[1:]
    await exchange_command(client, message, args)

@app.on_message(filters.command("ce") & sudo_filter)
async def handle_reset_exchange_counts(client: Client, message: Message):
    await user_collection.update_many({}, {'$set': {'exchange_count': 0, 'last_exchange': None}})
    await message.reply_text("All users' exchange counts have been reset.")
