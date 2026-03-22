---
name: play-chess
description: Play live chess against your user on ChessWithClaw. Use when: (1) User sends a chess invite URL containing chesswithclaw.vercel.app, (2) User asks you to play chess, (3) User mentions ChessWithClaw, (4) User says "I challenged you to chess", (5) User sends a game ID or token for a chess game. When triggered, connect to the game immediately and wait for the human to move first — you are always Black.
homepage: https://chesswithclaw.vercel.app
user-invocable: true
---

# ChessWithClaw — Complete Playing Guide

## What Is ChessWithClaw

ChessWithClaw is a real-time chess platform where YOU (the OpenClaw agent) play
chess against your human user. You are always **Black**. The human is always **White**
and moves first. The game is live — every move appears on both sides instantly.

**Base URL:** `https://chesswithclaw.vercel.app`
**API base:** `https://chesswithclaw.vercel.app/api`

---

## Step 1 — Extract Game Credentials

When the user sends an invite, extract these from the URL:
```
https://chesswithclaw.vercel.app/Agent?id=GAME_ID&token=AGENT_TOKEN
```

- `GAME_ID` — UUID identifying the game (e.g. `0ea3c8b2-4fe9-4873-bef5-10a51f576464`)
- `AGENT_TOKEN` — Your authentication token (e.g. `7764c2b6-e646-4945-91b7-dfc95858d489`)

Store both. You need them for every API call.

---

## Step 2 — Connect to the Game

**Best method for OpenClaw: Long-Polling (Option D)**

It's the simplest, most reliable method. No persistent connection needed.

### Connection Loop
```
GET https://chesswithclaw.vercel.app/api/poll
  ?id=GAME_ID
  &last_move_count=0
  &last_chat_count=0

Headers:
  x-agent-token: AGENT_TOKEN
```

**Poll every 2 seconds.** The server returns immediately with one of:

| event | Meaning | Your action |
|-------|---------|-------------|
| `waiting` | Human hasn't moved yet | Wait 2s, poll again |
| `your_turn` | Human moved, your turn | Make your move |
| `human_chatted` | User sent a message | Read it, optionally reply |
| `game_ended` | Game is over | Acknowledge, notify user |

Update `last_move_count` and `last_chat_count` with values from each response.

### Confirming Connection
The first time you hit `/api/poll`, the server marks you as connected.
Tell the user: **"I'm connected and waiting for your first move!"**

---

## Step 3 — Reading the Game State

When `event: "your_turn"`, the response includes everything you need:

```json
{
  "event": "your_turn",
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "turn": "b",
  "move_number": 1,
  "last_move": { "from": "e2", "to": "e4", "san": "e4", "uci": "e2e4" },
  "legal_moves": ["e7e5", "c7c5", "e7e6", "g8f6", ...],
  "legal_moves_uci": ["e7e5", "c7c5", "e7e6", ...],
  "board_ascii": "  +------------------------+\n8 | r  n  b  q  k  b  n  r |\n...",
  "in_check": false,
  "is_checkmate": false,
  "is_stalemate": false,
  "material_balance": { "white": 39, "black": 39, "advantage": "equal" },
  "move_history": ["e2e4"],
  "move_count": 1,
  "chat_count": 0
}
```

**Critical rule: ONLY play moves from `legal_moves_uci`. Never invent moves.**

---

## Step 4 — Reading the Board (FEN)

FEN string format: `pieces turn castling en-passant halfmove fullmove`

Example: `rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1`

- Uppercase = White pieces, lowercase = Black (your) pieces
- `K/k`=King `Q/q`=Queen `R/r`=Rook `B/b`=Bishop `N/n`=Knight `P/p`=Pawn
- Numbers = consecutive empty squares
- `b` after pieces = Black to move (your turn)
- Use `board_ascii` for a visual layout — easier to read

---

## Step 5 — Submitting Your Move

```
POST https://chesswithclaw.vercel.app/api/move

Headers:
  Content-Type: application/json
  x-agent-token: AGENT_TOKEN

Body:
{
  "id": "GAME_ID",
  "move": "e7e5",
  "reasoning": "Controlling the center with symmetry response"
}
```

### Move Format (UCI)
- Normal move: `e7e5` (from-square + to-square)
- Capture: `d5e4` (same format — server knows it's a capture)
- Castling kingside: `e8g8` (Black)
- Castling queenside: `e8c8` (Black)
- En passant: `e5d6` (move to the square the pawn passed through)
- Pawn promotion: `e7e8q` (add piece letter: q=queen, r=rook, b=bishop, n=knight)
- **Always promote to queen** unless you have a specific reason not to

### After Submitting
- Success: `{ "success": true, "game": { ... } }`
- Resume polling immediately with updated `last_move_count`

---

## Chess Strategy — How to Play Well

**Opening principles (moves 1-10):**
- Control the center: play e5, d5, c5, or Nf6 as Black responses
- Develop knights before bishops
- Castle early (kingside preferred: e8g8)
- Don't move the same piece twice unless necessary
- Don't bring queen out too early

**Middlegame principles:**
- Look for tactics: forks, pins, skewers, discovered attacks
- Keep your king safe — avoid opening files toward your king
- Centralize your pieces
- Rooks belong on open files
- Material values: Pawn=1, Knight=3, Bishop=3, Rook=5, Queen=9

**Endgame principles:**
- King becomes active — centralize it
- Passed pawns (no opposing pawns blocking) are powerful — push them
- Rook + King can force checkmate vs lone king
- If behind on material, look for perpetual check or stalemate tricks

**Evaluating the position:**
Use `material_balance` from the payload:
- `advantage: "equal"` — play solid, strategic chess
- `advantage: "white"` — you're losing, look for counterplay or tactics
- `advantage: "black"` — you're winning, simplify and convert

---

## Game Rules Reference

**How the game ends:**
- Checkmate — king attacked with no escape → that side loses
- Stalemate — no legal moves but not in check → draw
- Insufficient material (e.g. King vs King) → draw
- Threefold repetition → draw
- Fifty-move rule (50 moves with no capture or pawn move) → draw
- Resignation → that side loses

**Special rules:**
- En passant: if opponent advances pawn two squares, you can capture it
  as if it only moved one — but ONLY on the very next move
- Castling: king moves 2 squares toward rook — only if:
  - Neither piece has moved
  - No pieces between them
  - King not in check, not passing through check
- Promotion: pawn reaching rank 1 (you're Black, so rank 1) must promote

---

## Chat System

### Reading messages
When `event: "human_chatted"`:
- Check `messages` array for new entries with `sender: "human"`
- Read the latest message content

### Sending a message
```
POST https://chesswithclaw.vercel.app/api/chat

Headers:
  Content-Type: application/json
  x-agent-token: AGENT_TOKEN

Body:
{
  "id": "GAME_ID",
  "text": "Good move! But I have a response...",
  "sender": "agent"
}
```

**When to chat:**
- When the game starts: greet the user, show personality
- After a clever move by the user: acknowledge it
- When you spot a tactic: you can hint or tease
- After game ends: good game message
- Keep messages short — 1-2 sentences max during play

---

## Offering Draw / Resigning

### Offering a draw
```json
{
  "id": "GAME_ID",
  "text": "I offer a draw.",
  "sender": "agent",
  "type": "draw_offer"
}
```
Only offer a draw if the position is genuinely equal or you're in a difficult endgame.

### Accepting a draw offer from the user
If you receive a chat message with `type: "draw_offer"`, respond:
```json
{
  "id": "GAME_ID", 
  "text": "I accept the draw.",
  "sender": "agent",
  "type": "draw_accept"
}
```
Accept if you're losing or if position is a theoretical draw.
Decline if you're winning — play on.

### Resigning
```json
{
  "id": "GAME_ID",
  "text": "I resign. Well played.",
  "sender": "agent", 
  "type": "resign"
}
```
Resign only if you're significantly losing (material deficit of 5+ points)
with no realistic counterplay. Never resign in the opening or middlegame
unless position is completely hopeless.

---

## Error Handling

| Error | Meaning | Fix |
|-------|---------|-----|
| `404 Game not found` | Wrong game ID or game expired | Ask user for a fresh invite link |
| `401 Invalid agent token` | Wrong token in header | Check token from invite URL |
| `400 Illegal move` | Move not in legal_moves | Pick from legal_moves_uci only |
| `400 Not your turn` | Tried to move when it's human's turn | Wait for your_turn event |
| `400 Game not active` | Game status is 'waiting' | Human hasn't moved yet, keep polling |
| `409 Turn conflict` | Move already processed | Skip, poll for new state |
| `500 Corrupt game state` | Server error | Notify user, ask them to refresh |
| `504 Timeout` | Serverless function timed out | Retry the same request immediately |

---

## Connection Troubleshooting

**If you get 404:**
- Double-check game ID from the URL — copy it exactly
- Game may have expired (24-hour limit) — ask user to create a new game
- Try: `GET /api/state?id=GAME_ID` to verify game exists

**If you show as disconnected on user's screen:**
- This is a display delay — keep polling, the UI will update
- Hit `/api/poll` once more — your first poll sets `agent_connected: true`
- Tell user: "I'm connected on my end — try refreshing the page"

**If your move gets rejected:**
- Print the `legal_moves_uci` array and pick from it
- Never construct moves yourself — always use the provided list
- Check if game is finished before trying to move

**If polling stops working:**
- Restart your polling loop from last known `move_count`
- Use `GET /api/state?id=GAME_ID` to resync current position

**If you miss a turn:**
- Call `GET /api/state?id=GAME_ID` to get current FEN and legal moves
- Submit your move immediately

---

## All API Endpoints

```
GET  /api/state?id=GAME_ID              — Get current game state
GET  /api/poll?id=ID&last_move_count=N  — Poll for changes (use this)
POST /api/move                          — Submit your move
POST /api/chat                          — Send a chat message
POST /api/webhook  { id, webhook_url }  — Register webhook (advanced)
GET  /api/stream?id=GAME_ID             — SSE stream (advanced)
```

All POST requests: `Content-Type: application/json` + `x-agent-token: TOKEN`

---

## Being a Great Opponent

You are not just a chess engine — you are the user's personal OpenClaw
playing chess. Make it feel personal:

- **Greet them when the game starts** — "Ready for the game! I'm Black."
- **Show your thinking** — update `current_thinking` via PATCH /api/state
  with your reasoning before submitting a move
- **React to good moves** — "Nice fork! Didn't see that coming."
- **Play with personality** — confident when winning, determined when losing
- **Never stall** — make your move within 30 seconds of receiving your_turn
- **Give a good game** — play your actual best moves, don't throw the game

To update your thinking (shows as typewriter on user's screen):
```
PATCH https://chesswithclaw.vercel.app/api/state
Body: { "id": "GAME_ID", "current_thinking": "Considering Nf6..." }
```

---

## Quick Reference Card

```
You are:        Black (lowercase pieces in FEN)
Human is:       White (moves first)
Move format:    UCI — e.g. e7e5, g8f6, e8g8 (castle), e2e1q (promote)
Only play:      Moves from legal_moves_uci array
Poll every:     2 seconds
Token header:   x-agent-token: AGENT_TOKEN
Game over when: status = "finished" in any response
```
