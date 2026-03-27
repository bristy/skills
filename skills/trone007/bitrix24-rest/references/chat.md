# Chat and Notifications

Use this file for messenger dialogs, chats, history, notifications, and file delivery into chats.

> **Channels** (broadcast chats) -- see `references/channels.md`.
> **Bots** -- see `references/bots.md`.

## Endpoints

| Action | Command |
|--------|---------|
| Recent chats | `vibe.py --raw GET /v1/chats/recent --json` |
| Find chat | `vibe.py --raw GET '/v1/chats/find?query=project' --json` |
| Get chat info | `vibe.py --raw GET /v1/chats/123 --json` |
| Create group chat | `vibe.py --raw POST /v1/chats --body '{"type":"chat","title":"Project discussion","userIds":[1,2]}' --confirm-write --json` |
| Update chat | `vibe.py --raw PATCH /v1/chats/123 --body '{"title":"Updated title"}' --confirm-write --json` |
| Get messages | `vibe.py --raw GET /v1/chats/123/messages --json` |
| Search messages | `vibe.py --raw GET '/v1/chats/123/messages?search=contract' --json` |
| Send message | `vibe.py --raw POST /v1/chats/123/messages --body '{"message":"Hello team"}' --confirm-write --json` |
| Update message | `vibe.py --raw PATCH /v1/chats/123/messages/456 --body '{"message":"Updated text"}' --confirm-write --json` |
| Delete message | `vibe.py --raw DELETE /v1/chats/123/messages/456 --confirm-destructive --json` |
| Mark as read | `vibe.py --raw POST /v1/chats/read-all --confirm-write --json` |
| Send notification | `vibe.py --raw POST /v1/notifications --body '{"userId":5,"message":"Alert!"}' --confirm-write --json` |

## Key Fields

All field names use camelCase:

- `chatId` -- chat identifier
- `type` -- chat type (`chat`, `open`, `openChannel`)
- `title` -- chat name
- `userIds` -- array of participant user IDs
- `message` -- message text
- `messageId` -- message identifier

## Dialog Addressing

Chats are addressed by numeric `chatId`. Direct dialogs use user ID.

## Common Use Cases

### Send a message to a chat

```bash
python3 scripts/vibe.py --raw POST /v1/chats/42/messages \
  --body '{"message":"Hello team"}' \
  --confirm-write --json
```

### Read chat history

```bash
python3 scripts/vibe.py --raw GET '/v1/chats/42/messages?limit=20' --json
```

### Search messages in a chat

```bash
python3 scripts/vibe.py --raw GET '/v1/chats/42/messages?search=contract&limit=20' --json
```

Supports date filters via query params: `dateFrom`, `dateTo` (ISO 8601).

### Create a group chat

```bash
python3 scripts/vibe.py --raw POST /v1/chats \
  --body '{"type":"chat","title":"Project discussion","userIds":[1,2,5]}' \
  --confirm-write --json
```

### List chat participants

```bash
python3 scripts/vibe.py --raw GET /v1/chats/42/users --json
```

### Add users to chat

```bash
python3 scripts/vibe.py --raw POST /v1/chats/42/users \
  --body '{"userIds":[5,6,7]}' \
  --confirm-write --json
```

### Remove user from chat

```bash
python3 scripts/vibe.py --raw DELETE /v1/chats/42/users/5 --confirm-destructive --json
```

### Send a notification

```bash
python3 scripts/vibe.py --raw POST /v1/notifications \
  --body '{"userId":5,"message":"Your deal was approved!"}' \
  --confirm-write --json
```

## Formatting

Bitrix24 chat uses BB-code. Do not double-convert if Markdown is already converted to BB-code.

## Common Pitfalls

- Use numeric `chatId`, not string prefixes like `chat42`.
- Send notification requires `userId` -- you cannot notify by chat ID.
- Search string must be longer than 2 characters.
- Write operations require `--confirm-write`, delete operations require `--confirm-destructive`.
