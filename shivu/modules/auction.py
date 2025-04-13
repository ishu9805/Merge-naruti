from datetime import datetime
import asyncio
from pyrogram import Client, filters
from shivu import UPDATE_CHAT, SUPPORT_CHAT, CHARA_CHANNEL_ID, required_group_id, PHOTO_URL, OWNER_ID, PARTNER
from shivu import (
    collectionps as collection,
    top_global_groups_collectionps as top_global_groups_collection,
    group_user_totals_collectionps as group_user_totals_collection,
    user_collectionps as user_collection,
    user_totals_collectionps as user_totals_collection,
    shivuups as shivuu,
    shivuups as app,
    applicationps as application,
    SUPPORT_CHATps as SUPPORT,
    UPDATE_CHATps as UPDATE_CHAT,
    dbps as db,
    pmusersps as pmusers,
    ban_collectionps as ban_collection,
    user_countps as user_count, 
    chat_dataps as chat_data,
)


auction_collection = db["auctions"]

# Store auction details globally
auction_data = {}



@app.on_message(filters.command("stauc") & filters.user([7378476666]))
async def start_auction(client, message):
    # Command validation
    if len(message.command) < 3:
        await message.reply_text("Usage: /stauc <waifu_id> <starting_bid>")
        return

    waifu_id = message.command[1]
    try:
        starting_bid = int(message.command[2])
    except ValueError:
        await message.reply_text("Starting bid must be a number.")
        return

    # Check if an auction is already active
    active_auction = await auction_collection.find_one({"active": True})
    if active_auction:
        await message.reply_text("Another auction is already running. Please wait for it to end.")
        return

    # Fetch waifu from the main collection
    waifu = await collection.find_one({"id": waifu_id})
    if not waifu:
        await message.reply_text(f"No Character found with ID `{waifu_id}`.")
        return

    # Create a new auction entry
    auction_data = {
        "waifu_id": waifu["id"],
        "waifu_name": waifu.get("name", "Unknown Name"),
        "waifu_anime": waifu.get("anime", "Unknown Anime"),
        "rarity": waifu.get("rarity", "Unknown Rarity"),
        "starting_bid": starting_bid,
        "highest_bid": starting_bid,
        "highest_bidder": None,
        "active": True,
        "last_bid_time": None,
        "img_url": waifu.get("img_url", None)
    }
    await auction_collection.insert_one(auction_data)

    # Build and send the auction message
    auction_message = f"🛎 **Auction Started!**\n\n"
    auction_message += f"**CHARACTER:** {waifu.get('name', 'Unknown Name')} ({waifu.get('anime', 'Unknown Anime')})\n"
    auction_message += f"**Starting Bid:** {starting_bid}\n"
    auction_message += f"**Rarity:** {waifu.get('rarity', 'Unknown Rarity')}\n\n"
    auction_message += "Place your bids with `/bid <amount>`!"

    if waifu.get("img_url"):
        await client.send_photo(
            message.chat.id,
            waifu["img_url"],
            caption=auction_message
        )
    else:
        await message.reply_text(auction_message)




@app.on_message(filters.command("endauction") & filters.user([7378476666]))
async def end_auction(client, message):
    # Fetch the active auction
    active_auction = await auction_collection.find_one({"active": True})
    if not active_auction:
        await message.reply_text("No auction is currently running.")
        return

    winner_id = active_auction["highest_bidder"]
    winner_username = active_auction.get("highest_bidder_username", "Unknown")
    winning_bid = active_auction["highest_bid"]

    # Validate winner's coins
    while winner_id:
        winner_data = await user_collection.find_one({"id": winner_id})

        if not winner_data:
            await message.reply_text(f"User {winner_id} does not exist.")
            break

        winner_coins = winner_data.get("coins", 0)

        if winner_coins >= winning_bid:
            # Deduct coins and assign the character
            await user_collection.update_one(
                {"id": winner_id},
                {"$inc": {"coins": -winning_bid}}
            )

            # Add the waifu to the winner's collection
            waifu_data = {
                "id": active_auction["waifu_id"],
                "name": active_auction["waifu_name"],
                "anime": active_auction["waifu_anime"],
                "rarity": active_auction["rarity"],
                "img_url": active_auction["img_url"]
            }

            if "characters" not in winner_data:
                winner_data["characters"] = []
            winner_data["characters"].append(waifu_data)

            await user_collection.update_one(
                {"id": winner_id},
                {"$set": {"characters": winner_data["characters"]}}
            )

            # Notify the group
            await client.send_message(
                message.chat.id,
                f"The auction for {active_auction['waifu_name']} has ended.\n\n"
                f"🎉 **Winner:** {winner_username}\n"
                f"💰 **Winning Bid:** {winning_bid}\n"
                f"**Character Added to Their Collection!**"
            )

            # Remove the auction document
            await auction_collection.delete_one({"_id": active_auction["_id"]})
            return

        # If the current highest bidder doesn't have enough coins
        await client.send_message(
            message.chat.id,
            f"⚠️ The highest bidder @{winner_username} does not have enough coins ({winner_coins}/{winning_bid}). "
            "Falling back to the next highest bidder..."
        )

        # Set the next highest bidder (you'll need to implement bid tracking to support this logic)
        # For simplicity, resetting to None here (no previous bids)
        winner_id = None  # Replace this with logic to fetch the next highest bidder
        winner_username = "No Username"
        winning_bid = active_auction["starting_bid"]

    # If no valid bidders remain
    await client.send_message(
        message.chat.id,
        f"The auction for {active_auction['waifu_name']} has ended.\n\n"
        f"last highest bidder send message to @anime_arts_21"
    )
    await auction_collection.delete_one({"_id": active_auction["_id"]})



# Helper function to send periodic updates
async def periodic_auction_update(client):
    global auction_data
    while auction_data.get("active"):
        # Send periodic updates to the group (every 5 minutes)
        await asyncio.sleep(600)  # 5 minutes
        if auction_data["highest_bidder"]:
            # Send highest bid info
            await client.send_message(
                -1002610579411,
                f"🏷 **Auction Update:**\n\n"
                f"Highest Bid: {auction_data['highest_bid']}\n"
                f"Highest Bidder: @{auction_data['highest_bidder']}\n"
                f"Current CHARACTER: {auction_data['waifu_name']} ({auction_data['waifu_anime']})"
            )
        else:
            await client.send_message(
                -1002610579411,
                f"🏷 **Auction Update:**\n\n"
                f"No bids yet for {auction_data['waifu_name']} ({auction_data['waifu_anime']})\n"
                f"Starting Bid: {auction_data['starting_bid']}"
            )


@app.on_message(filters.command("bid"))
async def place_bid(client, message):
    # Fetch the active auction
    active_auction = await auction_collection.find_one({"active": True})
    if not active_auction:
        await message.reply_text("No active auction is running currently.")
        return

    if len(message.command) < 2:
        await message.reply_text("Usage: `/bid <amount>`\nExample: `/bid 150`")
        return

    try:
        bid_amount = int(message.command[1])
    except ValueError:
        await message.reply_text("Please provide a valid number for your bid.")
        return

    # Fetch user data
    user_data = await user_collection.find_one({"id": message.from_user.id})
    if not user_data:
        await message.reply_text("User data not found.")
        return

    user_coins = user_data.get("coins", 0)
    if user_coins < bid_amount:
        await message.reply_text("You don't have enough coins for this bid.")
        return

    if bid_amount <= active_auction["highest_bid"]:
        await message.reply_text("Your bid must be higher than the current highest bid.")
        return

    # Notify the former highest bidder that they have been outbid
    winner_username = active_auction.get("highest_bidder_username", "Unknown")
    await client.send_message(
        -1002338924488,
        f"{winner_username} ⚠️ You have been outbid in the auction for {active_auction['waifu_name']} ({active_auction['waifu_anime']}).\n"
        f"The new highest bid is {bid_amount} by @{message.from_user.username}."
    )

    # Update the auction with the new bid
    highest_bidder_username = (
        f"@{message.from_user.username}" if message.from_user.username else "No Username"
    )
    await auction_collection.update_one(
        {"_id": active_auction["_id"]},
        {
            "$set": {
                "highest_bid": bid_amount,
                "highest_bidder": message.from_user.id,
                "highest_bidder_username": highest_bidder_username,
                "last_bid_time": datetime.utcnow()
            }
        }
    )

    await message.reply_text(
        f"Your bid of {bid_amount} has been placed for {active_auction['waifu_name']}!\n"
        f"Current Highest Bid: {bid_amount}\n"
        f"Highest Bidder: @{highest_bidder_username}"
    )

    await message.send_message(
        chat_id= -1002610579411,
        f"New Bid: {bid_amount} by @{message.from_user.username}\n"
        f"Current Highest Bidder: @{message.from_user.username}",
    )
    
        



@app.on_message(filters.command("auction"))
async def view_auction(client, message):
    # Fetch the active auction data
    active_auction = await auction_collection.find_one({"active": True})

    if not active_auction:
        await message.reply_text(
            "No active auction is running at the moment.",
        )
        return

    # Get waifu details from the active auction
    waifu_id = active_auction["waifu_id"]
    waifu_name = active_auction["waifu_name"]
    waifu_anime = active_auction["waifu_anime"]
    starting_bid = active_auction["starting_bid"]
    highest_bid = active_auction["highest_bid"]
    highest_bidder_id = active_auction["highest_bidder"]
    waifu_image_url = active_auction.get("img_url", None)

    
    waifu_rarity = active_auction.get("rarity", "Unknown Rarity")
    highest_bidder = active_auction["highest_bidder_username"]

    # Prepare the message content
    auction_message = f"🛎 **Current Auction**\n\n"
    auction_message += f"**Waifu:** {waifu_name} ({waifu_anime})\n"
    auction_message += f"**Starting Bid:** {starting_bid}\n"
    auction_message += f"**Highest Bid:** {highest_bid} by @{highest_bidder}\n"
    auction_message += f"**Rarity:** {waifu_rarity}\n\n"
    auction_message += "Use `/bid <amount>` to place your bid!\n"

    # If there is an image URL, send the photo with the caption
    if waifu_image_url:
        await client.send_photo(
            message.chat.id,
            waifu_image_url,
            caption=auction_message
        )
    else:
        await message.reply_text(
            auction_message
        )
