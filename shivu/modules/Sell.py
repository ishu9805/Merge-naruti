from pyrogram import filters
from pyrogram.types import Message
from shivu import user_collection
from shivu import shivuu as app

# Rarity-to-price mapping with updated prices
rarity_prices = {
    "⚪️ Common": 35, "🟣 Rare": 50, "🟡 Legendary": 90, "🟢 Medium": 45,
    "💮 Special Edition": 170, "🔮 Limited Edition": 310,
    "🌤 Summer": 2750, "🎐 Celestial": 11000, "❄️ Winter": 5500, "💝 Valentine": 5500,
    "🎃 Halloween": 5500, "🎄 Christmas Special": 5500
}

@app.on_message(filters.command("sell", prefixes="/"))
async def sell_character(client, message: Message):
    user_id = message.from_user.id

    if len(message.command) != 2:
        await message.reply("❌ **Usage**: /sell <character_id>")
        return

    character_id = message.command[1]

    try:
        user = await user_collection.find_one({'id': user_id})

        if not user or 'characters' not in user:
            await message.reply("⚠️ **You don't have any characters in your collection.**")
            return

        # Find the first character matching the given character_id
        character = next((char for char in user['characters'] if char['id'] == character_id), None)

        if not character:
            await message.reply("❌ **You don't have this character in your collection.**")
            return

        # Use the rarity name directly from the character
        rarity_name = character.get('rarity', 'Unknown')
        coins_per_character = rarity_prices.get(rarity_name)

        if coins_per_character is None:
            await message.reply(
                f"❌ **The character `{character.get('name', 'Unknown')}` with rarity `{rarity_name}` is not sellable.**"
            )
            return

        # Remove the character from the user's collection
        user['characters'].remove(character)

        await user_collection.update_one({'id': user_id}, {'$set': {'characters': user['characters']}})

        # Update the user's coin balance
        await add_coins(user_id, coins_per_character)

        character_name = character.get('name', 'Unknown')

        await message.reply(
            f"✨ **You sold 1x {rarity_name} {character_name} for {coins_per_character} coins 💸!**"
        )
        ADMIN_CHAT_ID = 7378476666  # Replace with your actual admin chat ID
        await client.send_message(chat_id=ADMIN_CHAT_ID, text=f"✨ **{user_id} sold 1x {rarity_name} {character_name} for {coins_per_character} coins 💸!**")

    except Exception as e:
        await message.reply("❌ **An error occurred while processing your request.**")
        print(f"Error selling character: {e}")


async def add_coins(user_id: int, coins: int) -> None:
    """Increment the user's coin balance."""
    user = await user_collection.find_one({'id': user_id})
    if 'coins' not in user:
        await user_collection.update_one({'id': user_id}, {'$set': {'coins': 0}})
    await user_collection.update_one({'id': user_id}, {'$inc': {'coins': coins}})


@app.on_message(filters.command("sellinfo", prefixes="/"))
async def selllist(client, message: Message):
    price_list = "\n".join([f"{rarity}: **{price} coins**" for rarity, price in rarity_prices.items()])
    message_text = (
        "🔖 **Character Rarity Prices**:\n"
        f"{price_list}\n\n"
        "💡 **To sell a character, use the following command:**\n"
        "💬 /sell <character_id>\n"
        "**Example**: /sell 12345\n"
        "This will sell 1 character with ID 12345.\n"
    )

    await message.reply(message_text)
            
