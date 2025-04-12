from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)
from pyrogram.errors import BadRequest
from shivu import shivuups as app

# Game states storage
game_invites = {}
active_games = {}

def new_board():
    return [[" " for _ in range(3)] for _ in range(3)]

def create_board_keyboard(board, current_player, game_id):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            row.append(
                InlineKeyboardButton(
                    text=board[i][j] if board[i][j] != " " else "⬜",
                    callback_data=f"ttt_move_{game_id}_{i}_{j}_{current_player}",
                )
            )
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("Surrender", callback_data=f"ttt_surrender_{game_id}_{current_player}")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_invite_keyboard(game_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"ttt_accept_{game_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"ttt_reject_{game_id}")
        ]
    ])

def check_winner(board):
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != " ":
            return row[0]
    
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != " ":
            return board[0][col]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    
    if all(cell != " " for row in board for cell in row):
        return "Draw"
    
    return None

@app.on_message(filters.command(["tictactoe", "ttt"]) & filters.group)
async def invite_player(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply("Please reply to the user you want to play with using /tictactoe")
        return
    
    challenger = message.from_user.id
    opponent = message.reply_to_message.from_user.id
    
    if challenger == opponent:
        await message.reply("You can't play with yourself!")
        return
    
    # Check if either player is already in a game
    for game_id, game in active_games.items():
        if challenger in game["players"] or opponent in game["players"]:
            await message.reply("One of you is already in a game!")
            return
    
    game_id = f"{message.chat.id}_{message.id}"
    
    # Store the invitation
    game_invites[game_id] = {
        "challenger": challenger,
        "opponent": opponent,
        "chat_id": message.chat.id,
        "message_id": None
    }
    
    # Send the invitation message
    sent_message = await message.reply(
        f"{(await client.get_users(challenger)).mention} has challenged "
        f"{(await client.get_users(opponent)).mention} to a game of Tic-Tac-Toe!\n\n"
        f"Will you accept?",
        reply_markup=create_invite_keyboard(game_id)
    )
    
    # Store the message ID
    game_invites[game_id]["message_id"] = sent_message.id

@app.on_callback_query(filters.regex(r"^ttt_accept_"))
async def accept_invite(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    game_id = data[2]
    
    if game_id not in game_invites:
        await callback_query.answer("Invitation expired!", show_alert=True)
        return
    
    invite = game_invites[game_id]
    
    # Check if the user clicking is the intended opponent
    if callback_query.from_user.id != invite["opponent"]:
        await callback_query.answer("This invitation isn't for you!", show_alert=True)
        return
    
    # Remove the invitation
    del game_invites[game_id]
    
    # Create the game
    active_games[game_id] = {
        "board": new_board(),
        "players": [invite["challenger"], invite["opponent"]],
        "current_player": invite["challenger"],
        "chat_id": invite["chat_id"],
        "message_id": None
    }
    
    # Edit the original message to show the game board
    await client.edit_message_text(
        chat_id=invite["chat_id"],
        message_id=invite["message_id"],
        text=f"🎮 Tic-Tac-Toe Game 🎮\n\n"
             f"Player X: {(await client.get_users(invite['challenger'])).mention}\n"
             f"Player O: {(await client.get_users(invite['opponent'])).mention}\n\n"
             f"Current turn: {(await client.get_users(invite['challenger'])).mention} (X)",
        reply_markup=create_board_keyboard(
            active_games[game_id]["board"],
            active_games[game_id]["current_player"],
            game_id
        )
    )
    
    # Store the game message ID
    active_games[game_id]["message_id"] = invite["message_id"]
    
    await callback_query.answer("Game started!")

@app.on_callback_query(filters.regex(r"^ttt_reject_"))
async def reject_invite(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    game_id = data[2]
    
    if game_id not in game_invites:
        await callback_query.answer("Invitation expired!", show_alert=True)
        return
    
    invite = game_invites[game_id]
    
    # Check if the user clicking is the intended opponent
    if callback_query.from_user.id != invite["opponent"]:
        await callback_query.answer("This invitation isn't for you!", show_alert=True)
        return
    
    # Delete the invitation
    await client.delete_messages(
        chat_id=invite["chat_id"],
        message_ids=invite["message_id"]
    )
    del game_invites[game_id]
    
    await callback_query.answer("Game invitation rejected!")

@app.on_callback_query(filters.regex(r"^ttt_move_"))
async def handle_move(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    game_id = data[2]
    row = int(data[3])
    col = int(data[4])
    player = int(data[5])
    
    if game_id not in active_games:
        await callback_query.answer("Game not found or expired!", show_alert=True)
        return
    
    game = active_games[game_id]
    
    # Check if it's the player's turn
    if callback_query.from_user.id != game["current_player"]:
        await callback_query.answer("It's not your turn!", show_alert=True)
        return
    
    # Check if the player is actually in this game
    if callback_query.from_user.id not in game["players"]:
        await callback_query.answer("You're not part of this game!", show_alert=True)
        return
    
    # Check if the cell is empty
    if game["board"][row][col] != " ":
        await callback_query.answer("This cell is already taken!", show_alert=True)
        return
    
    # Make the move
    symbol = "X" if game["current_player"] == game["players"][0] else "O"
    game["board"][row][col] = symbol
    
    # Check for winner
    winner = check_winner(game["board"])
    
    if winner:
        # Game over
        if winner == "Draw":
            result_text = "It's a draw!"
        else:
            winner_player = game["players"][0] if winner == "X" else game["players"][1]
            result_text = f"{(await client.get_users(winner_player)).mention} ({winner}) wins!"
        
        # Update the message with final board and result
        await client.edit_message_text(
            chat_id=game["chat_id"],
            message_id=game["message_id"],
            text=f"🎮 Tic-Tac-Toe Game 🎮\n\n"
                 f"Player X: {(await client.get_users(game['players'][0])).mention}\n"
                 f"Player O: {(await client.get_users(game['players'][1])).mention}\n\n"
                 f"{result_text}",
            reply_markup=create_board_keyboard(game["board"], None, game_id)
        )
        
        # Remove the game from storage
        del active_games[game_id]
    else:
        # Switch turns
        game["current_player"] = game["players"][1] if game["current_player"] == game["players"][0] else game["players"][0]
        
        # Update the message with new board state
        await client.edit_message_text(
            chat_id=game["chat_id"],
            message_id=game["message_id"],
            text=f"🎮 Tic-Tac-Toe Game 🎮\n\n"
                 f"Player X: {(await client.get_users(game['players'][0])).mention}\n"
                 f"Player O: {(await client.get_users(game['players'][1])).mention}\n\n"
                 f"Current turn: {(await client.get_users(game['current_player'])).mention} "
                 f"({'X' if game['current_player'] == game['players'][0] else 'O'})",
            reply_markup=create_board_keyboard(
                game["board"],
                game["current_player"],
                game_id
            )
        )
    
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^ttt_surrender_"))
async def handle_surrender(client: Client, callback_query: CallbackQuery):
    data = callback_query.data.split("_")
    game_id = data[2]
    player = int(data[3])
    
    if game_id not in active_games:
        await callback_query.answer("Game not found or expired!", show_alert=True)
        return
    
    game = active_games[game_id]
    
    # Check if the player is actually in this game
    if callback_query.from_user.id not in game["players"]:
        await callback_query.answer("You're not part of this game!", show_alert=True)
        return
    
    # Determine the winner (the other player)
    winner = game["players"][1] if callback_query.from_user.id == game["players"][0] else game["players"][0]
    
    # Update the message with surrender result
    await client.edit_message_text(
        chat_id=game["chat_id"],
        message_id=game["message_id"],
        text=f"🎮 Tic-Tac-Toe Game 🎮\n\n"
             f"Player X: {(await client.get_users(game['players'][0])).mention}\n"
             f"Player O: {(await client.get_users(game['players'][1])).mention}\n\n"
             f"{(await client.get_users(callback_query.from_user.id)).mention} surrendered!\n"
             f"{(await client.get_users(winner)).mention} wins!",
        reply_markup=create_board_keyboard(game["board"], None, game_id)
    )
    
    # Remove the game from storage
    del active_games[game_id]
    await callback_query.answer()

print("Bot is running...")
app.run()
