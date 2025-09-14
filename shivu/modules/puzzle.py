import re
from pyrogram import filters
from pyrogram.types import Message
from shivu import (
    shivuups as app,
    collectionps as collection,
    user_collectionps as user_collection,
    puzzle_collectionps as puzzle_collection,  # new collection
)
from . import dev_filter

PUZZLE_CHAT_ID = -1002783891820  # only this chat can play


@app.on_message(filters.command("addpuzzle") & dev_filter)
async def add_puzzle(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.text:
        return await message.reply_text("⚠️ Reply to a puzzle text with `/addpuzzle <answer> - <attempts> - <char_id> - <amount>`")

    try:
        _, args = message.text.split(maxsplit=1)
        answer, attempts, char_id, amount = [x.strip() for x in args.split("-")]
        attempts, amount = int(attempts), int(amount)
    except Exception:
        return await message.reply_text("⚠️ Usage:\nReply to puzzle text\n`/addpuzzle answer - attempts - char_id - amount`")

    puzzle = {
        "question": message.reply_to_message.text,
        "answer": answer.lower(),
        "attempts": attempts,
        "char_id": char_id,
        "amount": amount,
        "active": True,
        "attempts_used": {}  # user_id: count
    }

    await puzzle_collection.delete_many({})  # only 1 active puzzle at a time
    await puzzle_collection.insert_one(puzzle)

    await message.reply_text("✅ Puzzle added successfully!")


@app.on_message(filters.command("hint"))
async def puzzle_hint(client, message: Message):
    if message.chat.id != PUZZLE_CHAT_ID:
        return
    puzzle = await puzzle_collection.find_one({"active": True})
    if not puzzle:
        return await message.reply_text("⚠️ No active puzzle right now.")
    await message.reply_text(f"🧩 Puzzle:\n\n{puzzle['question']}")


@app.on_message(filters.command("answer"))
async def puzzle_answer(client, message: Message):
    if message.chat.id != PUZZLE_CHAT_ID:
        return

    if len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: /answer your_text")

    user_id = message.from_user.id
    user_answer = " ".join(message.command[1:]).strip().lower()

    puzzle = await puzzle_collection.find_one({"active": True})
    if not puzzle:
        return await message.reply_text("⚠️ No active puzzle right now.")

    attempts_used = puzzle.get("attempts_used", {}).get(str(user_id), 0)
    if attempts_used >= puzzle["attempts"]:
        return await message.reply_text("❌ You have used all your attempts.")

    if user_answer == puzzle["answer"]:
        if puzzle["amount"] <= 0:
            return await message.reply_text("❌ Prize already claimed by others.")

        # get character info
        char = await collection.find_one({"id": puzzle["char_id"]})
        if not char:
            return await message.reply_text("⚠️ Character not found in DB.")

        # add prize to user
        await user_collection.update_one(
            {"id": user_id},
            {"$push": {"characters": char}},
            upsert=True
        )

        # decrease prize count
        await puzzle_collection.update_one(
            {"_id": puzzle["_id"]},
            {"$inc": {"amount": -1}}
        )

        return await message.reply_text(
            f"🎉 Correct! You won:\n\n"
            f"**{char['name']}** from {char['anime']}\n"
            f"Rarity: {char['rarity']}"
        )
    else:
        # increment attempts
        await puzzle_collection.update_one(
            {"_id": puzzle["_id"]},
            {"$inc": {f"attempts_used.{user_id}": 1}}
        )
        return await message.reply_text("❌ Wrong answer!")
  
