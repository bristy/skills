# Tasks

Use this file for task CRUD, searching, time tracking, and filtering.

## Entity CRUD

| Action | Command |
|--------|---------|
| List tasks | `vibe.py tasks --json` |
| Get task | `vibe.py tasks/123 --json` |
| Create task | `vibe.py tasks --create --body '{"title":"Task","responsibleId":5,"deadline":"2026-04-01"}' --confirm-write --json` |
| Update task | `vibe.py tasks/123 --update --body '{"title":"Updated title"}' --confirm-write --json` |
| Delete task | `vibe.py tasks/123 --delete --confirm-destructive --json` |
| Search tasks | `vibe.py tasks/search --body '{"filter":{"responsibleId":{"$eq":5},"status":{"$ne":5}}}' --json` |
| Complete task | `vibe.py tasks/123 --update --body '{"status":5}' --confirm-write --json` |
| Fields | `vibe.py tasks/fields --json` |

## Time Tracking

```bash
# Get time entries for a task
python3 scripts/vibe.py --raw GET /v1/tasks/123/time --json

# Add time entry
python3 scripts/vibe.py --raw POST /v1/tasks/123/time \
  --body '{"seconds":3600,"comment":"Work done"}' \
  --confirm-write --json
```

## Key Fields

All field names use camelCase:

- `title` — task name
- `responsibleId` — assigned user
- `createdById` — task creator
- `deadline` — due date/time
- `status` — task status (see Statuses below)
- `priority` — task priority
- `description` — task description
- `groupId` — project group ID

Use `tasks/fields` to discover all available fields including custom fields:

```bash
python3 scripts/vibe.py tasks/fields --json
```

## Statuses

- `1` — new
- `2` — waiting (pending)
- `3` — in progress
- `4` — supposedly completed (awaiting approval)
- `5` — completed
- `6` — deferred

## Filter Syntax

MongoDB-style operators:

| Operator | Meaning | Example |
|----------|---------|---------|
| `$eq` | Equals | `{"responsibleId":{"$eq":5}}` |
| `$ne` | Not equal | `{"status":{"$ne":5}}` |
| `$gt` | Greater than | `{"priority":{"$gt":0}}` |
| `$gte` | Greater or equal | `{"deadline":{"$gte":"2026-03-10"}}` |
| `$lt` | Less than | `{"deadline":{"$lt":"2026-03-08"}}` |
| `$lte` | Less or equal | `{"deadline":{"$lte":"2026-03-10"}}` |
| `$contains` | Contains substring | `{"title":{"$contains":"urgent"}}` |
| `$in` | In list | `{"status":{"$in":[1,2,3]}}` |

## Common Use Cases

### Overdue tasks

Tasks where deadline has passed but task is not completed or deferred:

```bash
python3 scripts/vibe.py tasks/search \
  --body '{"filter":{"responsibleId":{"$eq":1},"deadline":{"$lt":"2026-03-24"},"status":{"$lt":5}}}' --json
```

### Active tasks for a user

```bash
# Get current user ID
python3 scripts/vibe.py --raw GET /v1/me --json

# List active (non-completed, non-deferred) tasks
python3 scripts/vibe.py tasks/search \
  --body '{"filter":{"responsibleId":{"$eq":1},"status":{"$in":[1,2,3,4]}}}' --json
```

### Tasks with deadline on a specific date

```bash
python3 scripts/vibe.py tasks/search \
  --body '{"filter":{"deadline":{"$gte":"2026-03-10","$lte":"2026-03-10"}}}' --json
```

### Create a task with priority

```bash
python3 scripts/vibe.py tasks --create \
  --body '{"title":"Urgent task","responsibleId":1,"deadline":"2026-03-15","priority":2}' \
  --confirm-write --json
```

### Tasks in a project group

```bash
python3 scripts/vibe.py tasks/search \
  --body '{"filter":{"groupId":{"$eq":10}}}' --json
```

## Working Rules

- Field names are camelCase: `responsibleId`, `createdById`, `deadline`, `groupId`.
- Pagination: use `page` and `pageSize` query parameters.
- Get user ID from `GET /v1/me` before filtering by `responsibleId`.
- Use `tasks/fields` to discover available fields before writing.
- For read-only requests, execute immediately.
- Use `--raw` mode for time tracking endpoints.

## Good MCP Queries

- `tasks task list filter`
- `task checklistitem`
- `task commentitem`
- `task planner`
