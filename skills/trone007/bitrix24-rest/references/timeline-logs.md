# Timeline Logs

Use this file for extended CRM timeline entries -- custom log messages that appear in entity history with icons and formatting.

## Endpoints

| Action | Command |
|--------|---------|
| Create entry | `vibe.py --raw POST /v1/timeline-logs --body '{"entityTypeId":2,"entityId":123,"title":"Status update","text":"Deal moved to negotiation","iconCode":"info"}' --confirm-write --json` |
| Get entry | `vibe.py --raw GET /v1/timeline-logs/456 --json` |
| Update entry | `vibe.py --raw PATCH /v1/timeline-logs/456 --body '{"text":"Updated text"}' --confirm-write --json` |
| Delete entry | `vibe.py --raw DELETE /v1/timeline-logs/456 --confirm-destructive --json` |
| List entries | `vibe.py --raw GET '/v1/timeline-logs?entityTypeId=2&entityId=123' --json` |
| Pin entry | `vibe.py --raw POST /v1/timeline-logs/456/pin --confirm-write --json` |
| Unpin entry | `vibe.py --raw POST /v1/timeline-logs/456/unpin --confirm-write --json` |

## Key Fields

All field names use camelCase:

- `entityTypeId` -- CRM entity type (1=lead, 2=deal, 3=contact, 4=company, 7=quote, 31=smart invoice)
- `entityId` -- CRM entity ID
- `title` -- log entry title
- `text` -- log entry body text
- `iconCode` -- icon displayed next to the entry (see Icon Codes below)
- `createdAt` -- creation timestamp
- `authorId` -- user who created the entry

## Icon Codes

Available icon codes for timeline log entries:

| Code | Description |
|------|-------------|
| `info` | Information (blue circle i) |
| `warning` | Warning (yellow triangle) |
| `check` | Success/completed (green checkmark) |
| `call` | Phone call (phone icon) |
| `email` | Email (envelope icon) |
| `meeting` | Meeting (calendar/people icon) |

## Common Use Cases

### Add an info entry to a deal timeline

```bash
python3 scripts/vibe.py --raw POST /v1/timeline-logs \
  --body '{"entityTypeId":2,"entityId":123,"title":"Status update","text":"Deal moved to negotiation stage","iconCode":"info"}' \
  --confirm-write --json
```

### Add a warning to a lead

```bash
python3 scripts/vibe.py --raw POST /v1/timeline-logs \
  --body '{"entityTypeId":1,"entityId":456,"title":"Overdue follow-up","text":"No response in 7 days","iconCode":"warning"}' \
  --confirm-write --json
```

### Log a meeting note on a contact

```bash
python3 scripts/vibe.py --raw POST /v1/timeline-logs \
  --body '{"entityTypeId":3,"entityId":789,"title":"Meeting summary","text":"Discussed Q2 plans. Client interested in enterprise plan.","iconCode":"meeting"}' \
  --confirm-write --json
```

### Pin an important entry

```bash
python3 scripts/vibe.py --raw POST /v1/timeline-logs/456/pin --confirm-write --json
```

Pinned entries appear at the top of the entity timeline.

### List timeline entries for a deal

```bash
python3 scripts/vibe.py --raw GET '/v1/timeline-logs?entityTypeId=2&entityId=123' --json
```

### Update an entry

```bash
python3 scripts/vibe.py --raw PATCH /v1/timeline-logs/456 \
  --body '{"text":"Updated meeting notes: client confirmed budget approval"}' \
  --confirm-write --json
```

## Entity Type IDs

- `1` -- lead
- `2` -- deal
- `3` -- contact
- `4` -- company
- `7` -- quote
- `31` -- smart invoice
- `128+` -- custom smart process types

## Common Pitfalls

- `entityTypeId` is a number, not a string. Use `2` not `"deal"`.
- Both `entityTypeId` and `entityId` are required when creating an entry.
- `iconCode` is optional but recommended for visual clarity. Defaults to `info` if not specified.
- Timeline logs are different from timeline comments (`references/crm.md`) -- logs use camelCase fields throughout.
- Write operations require `--confirm-write`, delete operations require `--confirm-destructive`.
