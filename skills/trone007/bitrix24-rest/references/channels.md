# Channels

Use this file for Bitrix24 channels -- broadcast-style chats where only owners/managers post and subscribers read.

Channels are a special chat type. They use the same chat endpoints with channel-specific parameters.

## How Channels Differ From Chats

| Feature | Chat | Channel |
|---------|------|---------|
| Who can post | All members | Only owner + managers |
| Type | `chat` / `open` | `openChannel` |
| Join | By invite | Self-subscribe (open) or invite |

## Endpoints

| Action | Command |
|--------|---------|
| List channels | `vibe.py --raw GET '/v1/chats/recent?onlyChannels=true' --json` |
| Create channel | `vibe.py --raw POST /v1/chats --body '{"type":"openChannel","title":"Company News","description":"Official announcements","userIds":[1,2]}' --confirm-write --json` |
| Get channel info | `vibe.py --raw GET /v1/chats/42 --json` |
| Rename channel | `vibe.py --raw PATCH /v1/chats/42 --body '{"title":"Company Updates 2026"}' --confirm-write --json` |
| Post to channel | `vibe.py --raw POST /v1/chats/42/messages --body '{"message":"Important update: new office hours"}' --confirm-write --json` |
| Read messages | `vibe.py --raw GET '/v1/chats/42/messages?limit=20' --json` |
| Search messages | `vibe.py --raw GET '/v1/chats/42/messages?search=policy' --json` |
| List subscribers | `vibe.py --raw GET /v1/chats/42/users --json` |
| Add subscribers | `vibe.py --raw POST /v1/chats/42/users --body '{"userIds":[5,6,7]}' --confirm-write --json` |
| Remove subscriber | `vibe.py --raw DELETE /v1/chats/42/users/5 --confirm-destructive --json` |
| Leave channel | `vibe.py --raw POST /v1/chats/42/leave --confirm-write --json` |
| Mute channel | `vibe.py --raw POST /v1/chats/42/mute --body '{"mute":true}' --confirm-write --json` |
| Pin channel | `vibe.py --raw POST /v1/chats/42/pin --body '{"pin":true}' --confirm-write --json` |

## Key Fields

All field names use camelCase:

- `chatId` -- channel chat ID
- `type` -- `openChannel` for public, `channel` for private, `generalChannel` for company-wide
- `title` -- channel name
- `description` -- channel description
- `userIds` -- subscriber user IDs

## Common Use Cases

### Create a channel

```bash
python3 scripts/vibe.py --raw POST /v1/chats \
  --body '{"type":"openChannel","title":"Company News","description":"Official company announcements","userIds":[1,2],"message":"Welcome to the channel!"}' \
  --confirm-write --json
```

Returns channel chat ID. Creator becomes the owner.

### List all subscribed channels

```bash
python3 scripts/vibe.py --raw GET '/v1/chats/recent?onlyChannels=true&limit=50' --json
```

### Post to a channel

```bash
python3 scripts/vibe.py --raw POST /v1/chats/42/messages \
  --body '{"message":"Important update: new office hours starting Monday"}' \
  --confirm-write --json
```

Only the channel owner and managers can post.

### Mute/unmute channel

```bash
# Mute
python3 scripts/vibe.py --raw POST /v1/chats/42/mute \
  --body '{"mute":true}' --confirm-write --json

# Unmute
python3 scripts/vibe.py --raw POST /v1/chats/42/mute \
  --body '{"mute":false}' --confirm-write --json
```

## Known Limitations

### Comments and threads

Comments on channel posts are a UI feature not fully exposed via API. Reply threading may not be retrievable.

### Channel discovery

Listing channels returns only channels the current user is subscribed to. There is no API to discover channels the user is NOT subscribed to. Users must subscribe via the Bitrix24 UI first.

## Common Pitfalls

- Only owner and managers can post messages. Regular subscribers get an access error.
- `onlyChannels=true` is required to filter channels from regular chats in the recent list.
- Subscribers can leave with the leave endpoint, but cannot rejoin without owner action.
- Channel types: `openChannel` (public), `channel` (private), `generalChannel` (company-wide).
