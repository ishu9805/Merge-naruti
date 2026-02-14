from pyrogram import filters

from shivu import user_collectionps as user_collection, shivuups as shivuu, PARTNER

AUTHORIZED_USER_ID = 8535832693

@shivuu.on_message(filters.command("ntransfer"))
async def transfer(client, message):
    if str(message.from_user.id) not in PARTNER:
        return

    if len(message.command) != 3:
        await message.reply_text("You need to provide two user IDs! Usage: /tr1 [Source User ID] [Target User ID]")
        return

    source_user_id, target_user_id = int(message.command[1]), int(message.command[2])

    source_user = await user_collection.find_one({'id': source_user_id})
    target_user = await user_collection.find_one({'id': target_user_id})

    if source_user == target_user:
        return
        
    if not source_user:
        await message.reply_text("The source user does not exist!")
        return

    if not source_user.get('characters'):
        await message.reply_text("The source user has no characters to transfer!")
        return

    if not target_user:
        await user_collection.insert_one({
            'id': target_user_id,
            'characters': source_user['characters']
        })
    else:
        await user_collection.update_one({'id': target_user_id}, {'$push': {'characters': {'$each': source_user['characters']}}})

    await user_collection.delete_one({'id': source_user_id})

    await message.reply_text(f"Successfully transferred all characters from user {source_user_id} to user {target_user_id} and deleted user {source_user_id}'s document.")
