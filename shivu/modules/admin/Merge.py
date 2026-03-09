from pyrogram import filters
from shivu import shivuups as app
from shivu import collectionps
from shivu import user_collectionps as users


@app.on_message(filters.command("merge"))
async def merge_characters(client, message):

    if len(message.command) < 3:
        await message.reply("Usage:\n/merge main_id other_id other_id ...")
        return

    main_id = message.command[1]
    old_ids = message.command[2:]

    merged_users = 0

    for old_id in old_ids:

        cursor = users.find({"characters.id": old_id})

        async for user in cursor:

            chars = user.get("characters", [])
            updated = False

            for c in chars:
                if str(c.get("id")) == old_id:
                    c["id"] = main_id
                    updated = True

            if updated:
                await users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"characters": chars}}
                )
                merged_users += 1

        await collectionps.delete_one({"id": old_id})

    await message.reply(
        f"✅ Merge completed\n\n"
        f"Main ID: `{main_id}`\n"
        f"Merged IDs: {' '.join(old_ids)}\n"
        f"Users updated: {merged_users}"
      )
