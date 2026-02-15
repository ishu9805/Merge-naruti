import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pyrogram import filters
from pyrogram.types import Message

from shivu import shivuups as app, user_collectionps as user_collection

# Telegram 🎯 dice values are 1..6.
DART_POINTS = {
    1: 0,   # miss
    2: 10,
    3: 20,
    4: 30,
    5: 40,
    6: 50,  # best hit
}

START_SCORE = 301
MAX_PLAYERS_PER_GAME = 4
THROWS_PER_TURN = 3
MIN_BET = 1000


@dataclass
class Dart301Game:
    game_id: str
    chat_id: int
    bet: int
    owner_id: int
    owner_name: str
    players: List[int] = field(default_factory=list)
    names: Dict[int, str] = field(default_factory=dict)
    scores: Dict[int, int] = field(default_factory=dict)
    started: bool = False
    turn_index: int = 0
    throws_left: int = THROWS_PER_TURN
    pot: int = 0

    @property
    def current_player(self) -> int:
        return self.players[self.turn_index]


# chat_id -> game_id -> game state
CHAT_GAMES: Dict[int, Dict[str, Dart301Game]] = {}


def _display_name(user) -> str:
    return user.first_name or "Player"


def _chat_games(chat_id: int) -> Dict[str, Dart301Game]:
    if chat_id not in CHAT_GAMES:
        CHAT_GAMES[chat_id] = {}
    return CHAT_GAMES[chat_id]


async def _get_balance(user_id: int) -> int:
    user = await user_collection.find_one({"id": user_id})
    if not user:
        return 0
    return int(user.get("coins", 0) or 0)


async def _add_coins(user_id: int, amount: int) -> None:
    if amount <= 0:
        return
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"coins": amount}},
        upsert=True,
    )


async def _take_coins(user_id: int, amount: int) -> bool:
    if amount <= 0:
        return True
    bal = await _get_balance(user_id)
    if bal < amount:
        return False
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"coins": -amount}},
        upsert=True,
    )
    return True


def _find_player_game(chat_id: int, user_id: int) -> Optional[Dart301Game]:
    for game in _chat_games(chat_id).values():
        if user_id in game.players:
            return game
    return None


def _board(game: Dart301Game) -> str:
    lines = [
        f"🎯 **Dart 301** | Game ID: `{game.game_id}`",
        f"💰 Bet per player: **{game.bet}** coins",
        f"🏦 Pot: **{game.pot}** coins",
        "",
    ]

    for pid in game.players:
        name = game.names.get(pid, "Player")
        score = game.scores.get(pid, START_SCORE)
        marker = "👈" if game.started and pid == game.current_player else ""
        lines.append(f"• {name}: **{score}** {marker}")

    if game.started:
        turn_name = game.names.get(game.current_player, "Player")
        lines.extend([
            "",
            f"➡️ Turn: **{turn_name}**",
            f"🎯 Throws left this turn: **{game.throws_left}**/{THROWS_PER_TURN}",
        ])
    else:
        lines.extend([
            "",
            "Waiting for players.",
            f"Join: `/join301 {game.game_id}`",
            f"Start: `/start301 {game.game_id}`",
        ])

    return "\n".join(lines)


def _next_turn(game: Dart301Game) -> None:
    game.turn_index = (game.turn_index + 1) % len(game.players)
    game.throws_left = THROWS_PER_TURN


async def _refund_all(game: Dart301Game) -> None:
    for pid in game.players:
        await _add_coins(pid, game.bet)


@app.on_message(filters.command("dart301"))
async def create_301_game(_, message: Message):
    """
    Create a 301 game lobby.
    Usage: /dart301 <bet>
    """
    user = message.from_user
    if not user:
        return await message.reply_text("❌ Cannot identify you.")

    if len(message.command) < 2:
        return await message.reply_text(f"Usage: `/dart301 <bet_coins>` (minimum {MIN_BET})")

    try:
        bet = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Bet must be a number.")

    if bet < MIN_BET:
        return await message.reply_text(f"❌ Minimum bet is {MIN_BET} coins.")

    chat_id = message.chat.id
    existing = _find_player_game(chat_id, user.id)
    if existing:
        return await message.reply_text(
            f"⚠️ You are already in game `{existing.game_id}`. Finish/leave it first."
        )

    ok = await _take_coins(user.id, bet)
    if not ok:
        return await message.reply_text("❌ Not enough coins for this bet.")

    # unique game id inside chat
    game_id = str(message.id)
    game = Dart301Game(
        game_id=game_id,
        chat_id=chat_id,
        bet=bet,
        owner_id=user.id,
        owner_name=_display_name(user),
    )
    game.players.append(user.id)
    game.names[user.id] = _display_name(user)
    game.scores[user.id] = START_SCORE
    game.pot = bet

    _chat_games(chat_id)[game_id] = game

    await message.reply_text(
        "✅ New Dart 301 game created!\n"
        f"Game ID: `{game_id}`\n"
        f"Join command: `/join301 {game_id}`\n"
        f"Bet locked: **{bet} coins**\n"
        f"Players allowed: 2 to {MAX_PLAYERS_PER_GAME}\n\n"
        + _board(game)
    )


@app.on_message(filters.command("join301"))
async def join_301_game(_, message: Message):
    user = message.from_user
    if not user:
        return await message.reply_text("❌ Cannot identify you.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: `/join301 <game_id>`")

    chat_id = message.chat.id
    game_id = message.command[1]
    game = _chat_games(chat_id).get(game_id)

    if not game:
        return await message.reply_text("❌ Game not found in this chat.")

    if game.started:
        return await message.reply_text("⚠️ This game already started.")

    if user.id in game.players:
        return await message.reply_text("⚠️ You are already in this game.")

    if _find_player_game(chat_id, user.id):
        return await message.reply_text("⚠️ You are already in another active game in this chat.")

    if len(game.players) >= MAX_PLAYERS_PER_GAME:
        return await message.reply_text("⚠️ This game is full (max 4 players).")

    ok = await _take_coins(user.id, game.bet)
    if not ok:
        return await message.reply_text("❌ Not enough coins to join this bet game.")

    game.players.append(user.id)
    game.names[user.id] = _display_name(user)
    game.scores[user.id] = START_SCORE
    game.pot += game.bet

    await message.reply_text(f"✅ {_display_name(user)} joined game `{game.game_id}`\n\n" + _board(game))


@app.on_message(filters.command("start301"))
async def start_301_game(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/start301 <game_id>`")

    chat_id = message.chat.id
    game_id = message.command[1]
    game = _chat_games(chat_id).get(game_id)

    if not game:
        return await message.reply_text("❌ Game not found.")

    user = message.from_user
    if not user or user.id != game.owner_id:
        return await message.reply_text("❌ Only game creator can start this game.")

    if game.started:
        return await message.reply_text("⚠️ Game already started.")

    if len(game.players) < 2:
        return await message.reply_text("⚠️ Need at least 2 players to start.")

    game.started = True
    game.turn_index = 0
    game.throws_left = THROWS_PER_TURN

    await message.reply_text(
        "🚀 Game started!\n"
        "Turn system: each player gets **3 throws** per turn.\n"
        "Win rule: if your score becomes **0 or below 0**, you win immediately.\n\n"
        + _board(game)
    )


@app.on_message(filters.command(["dthrow", "dartthrow"]))
async def throw_301(_, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return await message.reply_text("❌ Cannot identify player.")

    if len(message.command) >= 2:
        game_id = message.command[1]
        game = _chat_games(chat_id).get(game_id)
    else:
        game = _find_player_game(chat_id, user.id)
        if not game:
            return await message.reply_text(
                "❌ You are not in any active game. Use `/dthrow <game_id>` to throw in a game."
            )
        game_id = game.game_id

    if not game:
        return await message.reply_text("❌ Game not found.")

    if not game.started:
        return await message.reply_text("⚠️ Game has not started yet.")

    if user.id not in game.players:
        return await message.reply_text("⚠️ You are not a player in this game.")

    if user.id != game.current_player:
        turn_name = game.names.get(game.current_player, "Player")
        return await message.reply_text(f"⏳ It's {turn_name}'s turn.")

    dice_msg = await app.send_dice(chat_id=chat_id, emoji="🎯")
    await asyncio.sleep(4)

    dart_val = dice_msg.dice.value if dice_msg.dice else 1
    scored = DART_POINTS.get(dart_val, 0)

    before = game.scores[user.id]
    after = before - scored

    if after <= 0:
        game.scores[user.id] = 0
        text = (
            f"🎯 {game.names[user.id]} rolled **{dart_val}** → **{scored}** points.\n"
            f"Score: **{before} → 0**"
        )
    else:
        game.scores[user.id] = after
        text = (
            f"🎯 {game.names[user.id]} rolled **{dart_val}** → **{scored}** points.\n"
            f"Score: **{before} → {after}**"
        )

    # throw consumed
    game.throws_left -= 1

    # Winner check
    if game.scores[user.id] == 0:
        await _add_coins(user.id, game.pot)
        await message.reply_text(
            text
            + "\n\n🏆 **Winner:** "
            + f"{game.names[user.id]}\n"
            + f"💰 Won pot: **{game.pot}** coins"
        )
        _chat_games(chat_id).pop(game_id, None)
        return

    # Next turn only after 3 throws
    if game.throws_left <= 0:
        _next_turn(game)

    await message.reply_text(text + "\n\n" + _board(game))


@app.on_message(filters.command("score301"))
async def score_301(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/score301 <game_id>`")

    game = _chat_games(message.chat.id).get(message.command[1])
    if not game:
        return await message.reply_text("❌ Game not found.")

    await message.reply_text(_board(game))


@app.on_message(filters.command("leave301"))
async def leave_301(_, message: Message):
    """Leave only before start. Refund bet to leaving player."""
    user = message.from_user
    if not user:
        return await message.reply_text("❌ Cannot identify you.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: `/leave301 <game_id>`")

    chat_id = message.chat.id
    game = _chat_games(chat_id).get(message.command[1])
    if not game:
        return await message.reply_text("❌ Game not found.")

    if game.started:
        return await message.reply_text("⚠️ Cannot leave after game starts.")

    if user.id not in game.players:
        return await message.reply_text("⚠️ You are not in this game.")

    game.players.remove(user.id)
    game.names.pop(user.id, None)
    game.scores.pop(user.id, None)
    game.pot -= game.bet
    await _add_coins(user.id, game.bet)

    if not game.players:
        _chat_games(chat_id).pop(game.game_id, None)
        return await message.reply_text("🗑️ Game removed (no players left).")

    if game.owner_id == user.id:
        game.owner_id = game.players[0]
        game.owner_name = game.names.get(game.owner_id, "Player")

    await message.reply_text("✅ Left game and refunded your bet.\n\n" + _board(game))


@app.on_message(filters.command("end301"))
async def end_301(_, message: Message):
    """
    End game by id.
    - Allowed only before game starts (lobby cancel).
    - Once started, game cannot be force-ended to avoid refund abuse/cheating.
    """
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/end301 <game_id>`")

    chat_id = message.chat.id
    game_id = message.command[1]
    game = _chat_games(chat_id).get(game_id)

    if not game:
        return await message.reply_text("❌ Game not found.")

    if game.started:
        return await message.reply_text(
            "❌ You cannot end a started game. Finish the match normally to decide winner."
        )

    await _refund_all(game)
    _chat_games(chat_id).pop(game_id, None)
    await message.reply_text("🛑 Lobby cancelled. Bets refunded to all players.")


@app.on_message(filters.command("list301"))
async def list_301(_, message: Message):
    games = _chat_games(message.chat.id)
    if not games:
        return await message.reply_text("No active 301 games in this chat.")

    lines = ["🎮 Active 301 games in this chat:"]
    for gid, game in games.items():
        status = "started" if game.started else "waiting"
        lines.append(
            f"• `{gid}` | {status} | players: {len(game.players)}/{MAX_PLAYERS_PER_GAME} | bet: {game.bet}"
        )

    await message.reply_text("\n".join(lines))
