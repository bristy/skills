# Calendar

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation.

Calendar events, sections, recurrence, and availability checks. Covers personal calendars, group calendars, and meetings.

**CRITICAL:** There is NO `calendar.get` method. The correct approach is `calendar.event.get` with mandatory `type` and `ownerId`.

## Endpoints

| Action | Command |
|--------|---------|
| Get events | `vibe.py --raw GET '/v1/calendar/events?type=user&ownerId=5&from=2026-03-24&to=2026-03-25' --json` |
| Create event | `vibe.py --raw POST /v1/calendar/events --body '{"type":"user","ownerId":5,"name":"Meeting","from":"2026-03-25T10:00:00","to":"2026-03-25T11:00:00"}' --confirm-write --json` |
| Get sections | `vibe.py --raw GET '/v1/calendar/sections?type=user&ownerId=5' --json` |
| Check availability | `vibe.py --raw POST /v1/calendar/accessibility --body '{"users":[5,10],"from":"2026-03-25","to":"2026-03-26"}' --json` |

## Key Fields (camelCase)

- `type` — one of: `user`, `group`, `company_calendar`
- `ownerId` — user ID for `user` type, group ID for `group`, `0` for `company_calendar`
- `name` — event title
- `from` / `to` — date range (`YYYY-MM-DD` for dates, ISO 8601 for datetime)
- `description` — event description
- `attendees` — list of invited user IDs
- `location` — event location string

## Copy-Paste Examples

### Get today's events for user 5

```bash
vibe.py --raw GET '/v1/calendar/events?type=user&ownerId=5&from=2026-03-24&to=2026-03-24' --json
```

### Create a meeting tomorrow

```bash
vibe.py --raw POST /v1/calendar/events --body '{
  "type": "user",
  "ownerId": 5,
  "name": "Team Standup",
  "from": "2026-03-25T09:00:00",
  "to": "2026-03-25T09:30:00",
  "description": "Daily sync",
  "attendees": [5, 10, 15]
}' --confirm-write --json
```

### Check availability for two users

```bash
vibe.py --raw POST /v1/calendar/accessibility --body '{
  "users": [5, 10],
  "from": "2026-03-25",
  "to": "2026-03-26"
}' --json
```

### List calendar sections

```bash
vibe.py --raw GET '/v1/calendar/sections?type=user&ownerId=5' --json
```

## Common Pitfalls

- **No `calendar.get`** — always use `calendar.event.get` with `type` and `ownerId`. Without these the call fails.
- `type` and `ownerId` are mandatory for event queries — omitting them returns an error, not an empty list.
- Date-only params use `YYYY-MM-DD`, not datetime. Datetime params use full ISO 8601.
- Check `calendar.accessibility` before proposing meeting slots to avoid double-booking.
- Group calendar events need `type=group` and the group ID as `ownerId`.
