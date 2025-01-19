from pyrogram import filters
from pyrogram.types import Message
from shivu import user_collection
from shivu import shivuu as app

# Rarity-to-price mapping
rarity_prices = {
    "⚪️ Common": 10, "🟣 Rare": 15, "🟡 Legendary": 20, "🟢 Medium": 30,
    "💮 Special Edition": 40, "🔮 Limited Edition": 50, "💸 Premium Edition": 60,
    "🌤 Summer": 25, "🎐 Celestial": 35, "❄️ Winter": 25, "💝 Valentine": 30,
    "🎃 Halloween": 40, "🎄 Christmas Special": 50
}

@app.on_message(filters.command("sell", prefixes="/"))
async def sell_character(client, message: Message):
    user_id = message.from_user.id

    if len(message.command) != 3:
        await message.reply("❌ **Usage**: /sell <character_id> <amount>")
        return

    character_id = message.command[1]
    try:
        amount = int(message.command[2])  # Convert amount to integer
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.reply("❌ **The amount must be a positive number.**")
        return

    try:
        user = await user_collection.find_one({'id': user_id})

        if not user or 'characters' not in user:
            await message.reply("⚠️ **You don't have any characters in your collection.**")
            return

        # Find the characters matching the given character_id
        matching_characters = [char for char in user['characters'] if char['id'] == character_id]

        if not matching_characters or len(matching_characters) < amount:
            await message.reply("❌ **You don't have enough of this character to sell.**")
            return

        # Use the rarity name directly from the character
        rarity_name = matching_characters[0].get('rarity')
        coins_per_character = rarity_prices.get(rarity_name)

        if coins_per_character is None:
            await message.reply("❌ **This character cannot be sold.**")
            return

        # Calculate total coins earned
        total_coins = coins_per_character * amount

        # Remove the specified number of characters from the user's collection
        for _ in range(amount):
            user['characters'].remove(matching_characters.pop())

        await user_collection.update_one({'id': user_id}, {'$set': {'characters': user['characters']}})

        # Update the user's coin balance
        await add_coins(user_id, total_coins)

        character_name = matching_characters[0]['name']

        await message.reply(
            f"✨ **You sold {amount}x {rarity_name} {character_name} for {total_coins} coins 💸!**"
        )
        await client.send_message(chat_id=7378476666, text="✨ ** {user_id} sold {amount}x {rarity_name} {character_name} for {total_coins} coins 💸!**")

    except Exception as e:
        await message.reply("❌ **An error occurred while processing your request.**")
        print(f"Error selling character: {e}")


async def add_coins(user_id: int, coins: int) -> None:
    """Increment the user's coin balance."""
    user = await user_collection.find_one({'id': user_id})
    if 'coins' not in user:
        await user_collection.update_one({'id': user_id}, {'$set': {'coins': 0}})
    await user_collection.update_one({'id': user_id}, {'$inc': {'coins': coins}})


@app.on_message(filters.command("selllist", prefixes="/"))
async def selllist(client, message: Message):
    price_list = "\n".join([f"{rarity}: **{price} coins**" for rarity, price in rarity_prices.items()])
    message_text = (
        "🔖 **Character Rarity Prices**:\n"
        f"{price_list}\n\n"
        "💡 **To sell a character, use the following command:**\n"
        "💬 /sell <character_id> <amount>\n"
        "**Example**: /sell 12345 3\n"
        "This will sell 3 characters with ID 12345.\n"
    )

    await message.reply(message_text)
      
