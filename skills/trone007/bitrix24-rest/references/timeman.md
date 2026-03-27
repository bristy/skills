# Time Tracking and Work Reports

Use this file for work day management, time tracking, and work schedules.

## Work Day Management

| Action | Command |
|--------|---------|
| Open day | `vibe.py --raw POST /v1/workday/open --confirm-write --json` |
| Close day | `vibe.py --raw POST /v1/workday/close --confirm-write --json` |
| Pause | `vibe.py --raw POST /v1/workday/pause --confirm-write --json` |
| Status | `vibe.py --raw GET /v1/workday/status --json` |
| Status (other user) | `vibe.py --raw GET '/v1/workday/status?userId=42' --json` |
| Settings | `vibe.py --raw GET /v1/workday/settings --json` |
| User settings | `vibe.py --raw GET '/v1/workday/settings?userId=42' --json` |
| Schedule | `vibe.py --raw GET /v1/workday/schedule --json` |

## Key Fields

- `status` -- work day status: `OPENED`, `CLOSED`, `PAUSED`, `EXPIRED`
- `userId` -- user ID (defaults to current user)

Status values:

- `OPENED` -- work day is active
- `CLOSED` -- work day is finished
- `PAUSED` -- work day is paused
- `EXPIRED` -- opened before today and never closed

## Absence Reports

| Action | Command |
|--------|---------|
| Get absence report | `vibe.py --raw GET '/v1/workday/reports/absence?userId=42&month=3&year=2026' --json` |
| List department users | `vibe.py --raw GET '/v1/workday/reports/users?departmentId=5' --json` |
| Submit absence explanation | `vibe.py --raw POST /v1/workday/reports/absence --body '{"userId":42,"dateFrom":"2026-03-10","dateTo":"2026-03-10","reason":"Doctor appointment"}' --confirm-write --json` |

## Task Time Tracking

Task time tracking is in `references/tasks.md`. Use:

```bash
# Get time entries for a task
python3 scripts/vibe.py --raw GET /v1/tasks/456/time --json

# Add time entry
python3 scripts/vibe.py --raw POST /v1/tasks/456/time \
  --body '{"seconds":3600,"comment":"Development work"}' \
  --confirm-write --json
```

## Common Use Cases

### Check work day status

```bash
python3 scripts/vibe.py --raw GET /v1/workday/status --json
```

### Check another user's status

```bash
python3 scripts/vibe.py --raw GET '/v1/workday/status?userId=42' --json
```

### Start work day

```bash
python3 scripts/vibe.py --raw POST /v1/workday/open --confirm-write --json
```

### End work day

```bash
python3 scripts/vibe.py --raw POST /v1/workday/close --confirm-write --json
```

### Pause work day

```bash
python3 scripts/vibe.py --raw POST /v1/workday/pause --confirm-write --json
```

### Get user work schedule

```bash
python3 scripts/vibe.py --raw GET '/v1/workday/settings?userId=42' --json
```

### Get absence report

```bash
python3 scripts/vibe.py --raw GET '/v1/workday/reports/absence?userId=42&month=3&year=2026' --json
```

## Building Department Reports

To build a time report for a department:

1. Get department employees: `vibe.py --raw GET '/v1/workday/reports/users?departmentId=5' --json`
2. For each employee, get status: `vibe.py --raw GET '/v1/workday/status?userId=ID' --json`
3. For detailed reports: `vibe.py --raw GET '/v1/workday/reports/absence?userId=ID&month=3&year=2026' --json`
4. For task time: `vibe.py --raw GET /v1/tasks/TASKID/time --json`

## Common Pitfalls

- Status defaults to current user -- pass `userId` query param for other users.
- Absence reports require `userId`, `month`, and `year` (all mandatory).
- Access to other users' reports depends on role (manager/admin).
- Time entries use `seconds` field, not hours.
- Write operations require `--confirm-write`.

## Note: No Email API

Bitrix24 has no REST API for reading or sending individual emails from Bitrix24 mailboxes.
