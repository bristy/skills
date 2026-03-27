# Open Lines

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation.

Omnichannel customer communication: website chat, Telegram, WhatsApp, Facebook, VK, and other channels. Open Lines route incoming conversations to operators.

## Endpoints

| Action | Command |
|--------|---------|
| List configs | `vibe.py --raw GET /v1/openlines/configs --json` |
| Get session | `vibe.py --raw GET /v1/openlines/sessions/123 --json` |
| List sessions | `vibe.py --raw GET '/v1/openlines/sessions?status=active' --json` |
| Close session | `vibe.py --raw POST /v1/openlines/sessions/123/close --confirm-write --json` |
| Assign operator | `vibe.py --raw POST /v1/openlines/sessions/123/assign --body '{"operatorId":5}' --confirm-write --json` |

## Key Fields (camelCase)

Config fields:

- `id` — line config ID
- `lineName` — display name of the line
- `active` — whether the line is active
- `crm` — CRM integration enabled
- `crmCreate` — lead creation mode

Session fields:

- `id` — session ID
- `chatId` — associated chat ID
- `status` — session status (`active`, `closed`, etc.)
- `operatorId` — assigned operator user ID
- `dateCreate` — session start timestamp
- `dateClose` — session close timestamp

## Copy-Paste Examples

### List all Open Line configs

```bash
vibe.py --raw GET /v1/openlines/configs --json
```

### Get a specific session

```bash
vibe.py --raw GET /v1/openlines/sessions/469 --json
```

### List active sessions

```bash
vibe.py --raw GET '/v1/openlines/sessions?status=active' --json
```

### Close a session

```bash
vibe.py --raw POST /v1/openlines/sessions/469/close --confirm-write --json
```

### Assign an operator to a session

```bash
vibe.py --raw POST /v1/openlines/sessions/469/assign --body '{
  "operatorId": 5
}' --confirm-write --json
```

## Common Pitfalls

- Open Lines may require a specific scope (`imopenlines`) — ensure the webhook has it.
- Session history requires both `chatId` and `sessionId` — one alone is not sufficient.
- There may be no method to list all active sessions across all lines — you may need to query per-line.
- Closing a session is irreversible — the conversation cannot be reopened.
- Operator assignment transfers the dialog — the previous operator loses access.
- Attachment and keyboard objects in messages are typically limited to 30 KB each.
