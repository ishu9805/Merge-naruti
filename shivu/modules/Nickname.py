import asyncio
from telethon import events, Button
from telethon.sync import TelegramClient
from pymongo import MongoClient
from shivu import app
from shivu import user_collection, ban_collection

# Handler for the /nhmode command
@app.on(events.NewMessage(pattern='/nhmode'))
async def nhmode(event):
    user_id = event.sender_id

    is_banned = await ban_collection.find_one({"user_id": user_id})
    if is_banned:
        # If the user is banned, do nothing
        return
    else:
        pass
    buttons = [
        [
            Button.inline("See by Rarities", data="rarity_mode:see_by_rarities"),
            Button.inline("Default", data="rarity_mode:default")
        ]
    ]
    
    await event.respond("Select a rarity mode:", buttons=buttons)

# Handler for callback queries
# Handler for callback queries
@app.on(events.CallbackQuery)
async def callback_query_handler(event):
    try:
        data = event.data.decode('utf-8')

        if data == "rarity_mode:see_by_rarities":
            rarities_buttons = [
                [Button.inline("⚪️", data="rarity:⚪️ Common"), 
                 Button.inline("🟣", data="rarity:🟣 Rare"), 
                 Button.inline("🟡", data="rarity:🟡 Legendary"),
                 Button.inline("🟢", data="rarity:🟢 Medium")],
                [Button.inline("💮", data="rarity:💮 Special Edition"), 
                 Button.inline("🔮", data="rarity:🔮 Limited Edition"),
                 Button.inline("💸", data="rarity:💸 Premium Edition"),
                 Button.inline("🎖", data="rarity:🎖 Apex Lot ( AUCTION )")],
                [Button.inline("🌤", data="rarity:🌤 Summer"), 
                 Button.inline("🎐", data="rarity:🎐 Celestial"), 
                 Button.inline("☃️", data="rarity:❄️ Winter"),
                 Button.inline("💝", data="rarity:💝 Valentine")],
                [Button.inline("🎃", data="rarity:🎃 Halloween"), 
                 Button.inline("🎄", data="rarity:🎄 Christmas Special"),
                 Button.inline("🪐", data="rarity:🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐"), 
                 Button.inline("🎭", data="rarity:🎭 Cosplay Master 🎭")],
                [Button.inline("🎗️", data="rarity:🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣")]
            ]
            await event.edit("Select a rarity:", buttons=rarities_buttons)

        elif data.startswith("rarity:"):
            rarity_mode = data.split(":")[1]
            await user_collection.update_one(
                {'id': event.sender_id}, 
                {'$set': {'rarity_mode': rarity_mode}}, 
                upsert=True
            )
            await event.edit(f"Your rarity mode is now set to {rarity_mode}.")

        elif data == "rarity_mode:default":
            await user_collection.update_one(
                {'id': event.sender_id}, 
                {'$set': {'rarity_mode': 'All'}}, 
                upsert=True
            )
            await event.edit("Your rarity mode is now set to All.")

        # Schedule the deletion of the callback query message after 20 seconds
        await asyncio.sleep(20)
        await event.delete()

    except Exception as e:
        await event.answer("An error occurred. Please try again.", alert=True)
        print(f"Error handling callback query: {e}")
