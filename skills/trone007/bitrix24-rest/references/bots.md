# Bot Platform

Use this file for creating and managing bots in the Bitrix24 messenger -- registration, messaging, commands, and event handling.

## Endpoints

| Action | Command |
|--------|---------|
| Register bot | `vibe.py --raw POST /v1/bots --body '{"name":"MyBot","type":"B"}' --confirm-write --json` |
| Update bot | `vibe.py --raw PATCH /v1/bots/123 --body '{"name":"UpdatedBot"}' --confirm-write --json` |
| Delete bot | `vibe.py --raw DELETE /v1/bots/123 --confirm-destructive --json` |
| Get events | `vibe.py --raw GET /v1/bots/123/events --json` |
| Send message | `vibe.py --raw POST /v1/bots/123/messages --body '{"chatId":456,"message":"Hello"}' --confirm-write --json` |
| Update message | `vibe.py --raw PATCH /v1/bots/123/messages/789 --body '{"message":"Updated text"}' --confirm-write --json` |
| Delete message | `vibe.py --raw DELETE /v1/bots/123/messages/789 --confirm-destructive --json` |
| Typing indicator | `vibe.py --raw POST /v1/bots/123/typing --body '{"chatId":456}' --confirm-write --json` |
| Register command | `vibe.py --raw POST /v1/bots/123/commands --body '{"command":"help","description":"Show help"}' --confirm-write --json` |
| Update command | `vibe.py --raw PATCH /v1/bots/123/commands/cmd1 --body '{"description":"Updated help"}' --confirm-write --json` |
| Delete command | `vibe.py --raw DELETE /v1/bots/123/commands/cmd1 --confirm-destructive --json` |

## Key Fields

All field names use camelCase:

- `name` -- bot display name
- `type` -- bot type: `B` (standard bot), `H` (hidden/service bot), `S` (supervisor bot)
- `chatId` -- target chat for messages
- `message` -- message text
- `command` -- slash command name (without leading /)
- `description` -- command description shown in command list

## Common Use Cases

### Register a new bot

```bash
python3 scripts/vibe.py --raw POST /v1/bots \
  --body '{"name":"SalesBot","type":"B"}' \
  --confirm-write --json
```

Returns a bot ID and `clientId`. Save the `clientId` -- it is required for all subsequent bot operations.

### Send a message from a bot

```bash
python3 scripts/vibe.py --raw POST /v1/bots/123/messages \
  --body '{"chatId":456,"message":"Your order has been shipped!"}' \
  --confirm-write --json
```

### Show typing indicator

```bash
python3 scripts/vibe.py --raw POST /v1/bots/123/typing \
  --body '{"chatId":456}' \
  --confirm-write --json
```

### Register a slash command

```bash
python3 scripts/vibe.py --raw POST /v1/bots/123/commands \
  --body '{"command":"help","description":"Show help menu"}' \
  --confirm-write --json
```

### Poll for bot events

```bash
python3 scripts/vibe.py --raw GET /v1/bots/123/events --json
```

Returns incoming messages and command invocations directed at the bot.

## Bot Types

- `B` -- standard bot, visible in chat list, can be invited to group chats
- `H` -- hidden/service bot, not visible in user lists, used for backend integrations
- `S` -- supervisor bot, has extended permissions

## Common Pitfalls

- Bots require a `clientId` returned at registration. Persist and reuse it for all bot API calls.
- Do not mix bot endpoints with regular chat endpoints -- use `/v1/bots/*` for bot-sent messages.
- Typing indicator expires after a few seconds -- send it periodically during long operations.
- Bot names must be unique within the portal.
- Write operations require `--confirm-write`, delete operations require `--confirm-destructive`.
