import random

from pyrogram import filters
from pyrogram.types import Message

from shivu import shivuups as app
from shivu.modules.lock import command_lock

from .constants import HOLI_EVENT_CHAT_ID, HOLI_EVENT_TITLE, HOLI_EVENT_DAYS, USAGE_LIMITS
from .service import (
    close_giveaway_and_pick_winner,
    create_giveaway,
    ensure_user,
    get_current_event_day,
    get_event_summary,
    join_giveaway,
    mark_challenge_done,
    mark_public_game_win,
    mark_riddle_win,
    mark_spin_reward,
    check_and_consume_daily_limit,
    add_coins,
)
from .styles import banner, fancy

PUBLIC_GAME_TARGETS = ["gulal", "rang", "pichkari", "masti", "dhol", "bura-na-mano"]
HOLI_RIDDLES = [
    {"q": "I am colorful powder used in Holi. What am I?", "a": "gulal"},
    {"q": "Festival where people play with colors?", "a": "holi"},
    {"q": "Water gun used in Holi fun?", "a": "pichkari"},
]

def _is_holi_group(message: Message) -> bool:
    return bool(message.chat and message.chat.id == HOLI_EVENT_CHAT_ID)


def _day_card(day_num: int, day_info: dict) -> str:
    return (
        f"📅 {fancy(f'Day {day_num}')}: {day_info['name']}\n"
        f"🎯 Focus: {day_info['focus']}\n"
        f"🧩 Challenge: {day_info['challenge']}\n"
        f"🪙 Reward: {day_info['reward']} coins"
    )


async def _consume_limit(user_id: int, action: str) -> tuple[bool, int]:
    return await check_and_consume_daily_limit(
        user_id=user_id,
        action=action,
        max_uses=USAGE_LIMITS[action]["max_uses"],
    )


async def _safe_react(message: Message, emoji: str) -> None:
    try:
        await message.react(emoji)
    except Exception:
        pass


@app.on_message(filters.command("holi"))
@command_lock
async def holi_home(_, message: Message):
    day_num, day_info = get_current_event_day()
    text = (
        f"{banner(HOLI_EVENT_TITLE, '4-Day Colors • Giveaway • Challenges • Games')}\n\n"
        f"{_day_card(day_num, day_info)}\n\n"
        f"🎁 {fancy('Giveaway')}: /holigiveaway, /holijoin, /holiend\n"
        f"🪙 {fancy('Daily Challenge')}: /holichallenge\n"
        f"🎮 {fancy('Public Guess')}: /holiguess <word>\n"
        f"🧠 {fancy('Public Riddle')}: /holiriddle <answer>\n"
        f"🎡 {fancy('Lucky Spin')}: /holispin\n"
        f"🗓 {fancy('4 Day Plan')}: /holidays\n"
        f"📊 {fancy('Full Event Check')}: /holicheck\n\n"
        f"🛡 Anti-spam limits are enabled for all Holi reward commands.\n"
        f"💥 {fancy('Main Event Place')}: <code>{HOLI_EVENT_CHAT_ID}</code>"
    )
    await message.reply_text(text)
    await _safe_react(message, "🔥")


@app.on_message(filters.command("holidays"))
@command_lock
async def holi_days_plan(_, message: Message):
    lines = [banner("Holi 4-Day Mega Plan")]
    for day_num in sorted(HOLI_EVENT_DAYS):
        lines.append("")
        lines.append(_day_card(day_num, HOLI_EVENT_DAYS[day_num]))

    lines.append("\n🎉 Giveaway + challenge operations are active only in official Holi chat.")
    await message.reply_text("\n".join(lines))


@app.on_message(filters.command("holigiveaway"))
@command_lock
async def holi_start_giveaway(_, message: Message):
    if not _is_holi_group(message):
        await message.reply_text("🎨 Holi giveaway can start only in the official Holi event group.")
        return

    day_num, day_info = get_current_event_day()
    await create_giveaway(message.from_user.id, message.from_user.first_name)
    await message.reply_text(
        f"{banner('Holi Giveaway Started')}\n\n"
        f"{_day_card(day_num, day_info)}\n\n"
        "🥳 Drop /holijoin to enter.\n"
        "🏆 Winner gets coins + 1 random character.\n"
        "🌈 Color your luck now!"
    )


@app.on_message(filters.command("holijoin"))
@command_lock
async def holi_join_giveaway(_, message: Message):
    if not _is_holi_group(message):
        await message.reply_text("🌈 Join this giveaway only in official Holi event group.")
        return

    allowed, left = await _consume_limit(message.from_user.id, "holijoin")
    if not allowed:
        await message.reply_text("⛔ Join limit reached for now. Please try again after reset.")
        return

    already_joined, total = await join_giveaway(message.from_user.id)
    if already_joined:
        await message.reply_text(f"You already joined! Total participants: {total}")
        return

    await message.reply_text(
        f"🎊 Entry confirmed. Total colorful participants: {total}\n"
        f"🛡 Join uses left today: {left}"
    )
    await _safe_react(message, "🎉")


@app.on_message(filters.command("holiend"))
@command_lock
async def holi_end_giveaway(_, message: Message):
    if not _is_holi_group(message):
        await message.reply_text("❌ This command is available only in official Holi event group.")
        return

    result = await close_giveaway_and_pick_winner()
    if not result:
        await message.reply_text("No active Holi giveaway found.")
        return

    if result["participants"] == 0:
        await message.reply_text("Giveaway closed with no participants this time.")
        return

    winner_id = result["winner_id"]
    character = result.get("winner_character")
    character_name = character.get("name", "Mystery Character") if character else "Mystery Character"

    await message.reply_text(
        f"{banner('Holi Giveaway Winner')}\n\n"
        f"👑 Winner: <a href='tg://user?id={winner_id}'>Festival Champion</a>\n"
        f"🪙 Coins: 1500\n"
        f"🧿 Character: {character_name}\n"
        f"👥 Participants: {result['participants']}",
        disable_web_page_preview=True,
    )
    await _safe_react(message, "🏆")


@app.on_message(filters.command("holichallenge"))
@command_lock
async def holi_challenge(_, message: Message):
    if not _is_holi_group(message):
        await message.reply_text("🚫 Holi challenge rewards are limited to official event group only.")
        return

    allowed, left = await _consume_limit(message.from_user.id, "holichallenge")
    if not allowed:
        await message.reply_text("⛔ Daily challenge limit reached. Come back after reset.")
        return

    day_num, day_info = get_current_event_day()
    await ensure_user(message.from_user.id, message.from_user.first_name)
    reward = await mark_challenge_done(message.from_user.id)
    dice_message = await app.send_dice(
        chat_id=message.chat.id,
        emoji="🎯",
        reply_to_message_id=message.id,
    )
    await message.reply_text(
        f"{banner('Challenge Complete')}\n\n"
        f"📅 Day {day_num} - {day_info['name']}\n"
        f"🎯 Challenge Dice Value: {dice_message.dice.value}\n"
        f"🔥 You completed today's Holi challenge and won {reward} coins!\n"
        f"🛡 Challenge uses left today: {left}"
    )
    await _safe_react(message, "✅")


@app.on_message(filters.command("holiguess"))
@command_lock
async def holi_public_game(_, message: Message):
    allowed, left = await _consume_limit(message.from_user.id, "holiguess")
    if not allowed:
        await message.reply_text("⛔ Guess limit reached for today. Try again tomorrow.")
        return

    if len(message.command) < 2:
        await message.reply_text(
            f"{banner('Holi Guess Game')}\n\n"
            f"Type: /holiguess <word>\n"
            f"Try one from: {', '.join(PUBLIC_GAME_TARGETS)}\n"
            f"🛡 Uses left today: {left}"
        )
        return

    guess = message.command[1].strip().lower()
    answer = random.choice(PUBLIC_GAME_TARGETS)

    if guess == answer:
        await ensure_user(message.from_user.id, message.from_user.first_name)
        reward = await mark_public_game_win(message.from_user.id)
        dice_message = await app.send_dice(
            chat_id=message.chat.id,
            emoji="🎲",
            reply_to_message_id=message.id,
        )
        await message.reply_text(
            f"🎉 {fancy('Perfect Guess')}! You won {reward} coins in public Holi game.\n"
            f"🎲 Dice rolled: {dice_message.dice.value}\n"
            f"🛡 Uses left today: {left}"
        )
        await _safe_react(message, "🎉")
        return

    await message.reply_text(
        f"😅 Nice try! Secret word was <b>{answer}</b>.\n"
        f"Play again with /holiguess <word>.\n"
        f"🛡 Uses left today: {left}"
    )


@app.on_message(filters.command("holiriddle"))
@command_lock
async def holi_riddle(_, message: Message):
    allowed, left = await _consume_limit(message.from_user.id, "holiriddle")
    if not allowed:
        await message.reply_text("⛔ Riddle limit reached for today. Try tomorrow.")
        return

    if len(message.command) < 2:
        riddle = random.choice(HOLI_RIDDLES)
        await message.reply_text(
            f"🧠 {banner('Holi Riddle')}\n\n"
            f"{riddle['q']}\n"
            f"Reply format: /holiriddle <answer>\n"
            f"🛡 Uses left today: {left}"
        )
        return

    user_answer = " ".join(message.command[1:]).strip().lower()
    valid_answers = {item["a"] for item in HOLI_RIDDLES}
    if user_answer not in valid_answers:
        await message.reply_text(
            f"❌ Wrong answer, but nice try!\n"
            f"🛡 Uses left today: {left}"
        )
        return

    await ensure_user(message.from_user.id, message.from_user.first_name)
    reward = await mark_riddle_win(message.from_user.id)
    dice_message = await app.send_dice(
        chat_id=message.chat.id,
        emoji="🎳",
        reply_to_message_id=message.id,
    )
    await message.reply_text(
        f"✅ Brilliant! Correct answer. You won {reward} Holi coins.\n"
        f"🎳 Bonus roll: {dice_message.dice.value}\n"
        f"🛡 Uses left today: {left}"
    )
    await _safe_react(message, "🧠")


@app.on_message(filters.command("holispin"))
@command_lock
async def holi_spin(_, message: Message):
    if not _is_holi_group(message):
        await message.reply_text("🎡 Lucky spin is available only in official Holi event group.")
        return

    allowed, left = await _consume_limit(message.from_user.id, "holispin")
    if not allowed:
        await message.reply_text("⛔ Spin limit reached for today. Try tomorrow.")
        return

    await ensure_user(message.from_user.id, message.from_user.first_name)
    dice_message = await app.send_dice(
        chat_id=message.chat.id,
        emoji="🎲",
        reply_to_message_id=message.id,
    )
    reward = await mark_spin_reward(message.from_user.id)
    jackpot_bonus = 0
    if dice_message.dice.value == 6:
        jackpot_bonus = 300
        reward += jackpot_bonus
        await add_coins(message.from_user.id, jackpot_bonus)

    await message.reply_text(
        f"🎡 Wheel spun successfully! You won {reward} coins.\n"
        f"🎲 Spin dice value: {dice_message.dice.value}\n"
        f"💥 Jackpot Bonus: {jackpot_bonus if jackpot_bonus else 0}\n"
        f"🛡 Spins left today: {left}"
    )
    await _safe_react(message, "🎡")


@app.on_message(filters.command("holistatus"))
@app.on_message(filters.command("holicheck"))
@command_lock
async def holi_status(_, message: Message):
    summary = await get_event_summary()
    active = summary.get("active_giveaway")
    last = summary.get("last_giveaway")

    active_participants = len(active.get("participants", [])) if active else 0
    last_winner = last.get("winner_id") if last else None
    day_num = summary["event_day"]
    day_info = summary["day_info"]

    txt = (
        f"{banner('Holi Event Dashboard')}\n\n"
        f"{_day_card(day_num, day_info)}\n\n"
        f"🎁 Active Giveaway: {'YES' if active else 'NO'}\n"
        f"👥 Active Participants: {active_participants}\n"
        f"🏅 Last Winner: {last_winner if last_winner else 'Not declared'}\n"
        f"🪙 Today Challenge Reward: {summary['challenge_reward']}\n"
        f"🎮 Public Game Reward: {summary['public_game_reward']}\n"
        f"📍 Event Chat: <code>{HOLI_EVENT_CHAT_ID}</code>\n\n"
        f"🛡 Anti-spam limits:\n"
        f"• /holichallenge: 3/day\n"
        f"• /holiguess: 8/day\n"
        f"• /holiriddle: 5/day\n"
        f"• /holispin: 2/day\n\n"
        f"💡 Commands: /holi /holidays /holigiveaway /holijoin /holiend /holichallenge /holiguess /holiriddle /holispin /holicheck"
    )
    await message.reply_text(txt)
