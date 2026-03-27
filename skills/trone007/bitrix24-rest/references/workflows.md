# Workflows (Business Processes)

Use this file for starting, managing, and completing business processes and their tasks.

## Endpoints

| Action | Command |
|--------|---------|
| Start process | `vibe.py --raw POST /v1/workflows/start --body '{"templateId":1,"documentId":"DEAL_123"}' --confirm-write --json` |
| Terminate process | `vibe.py --raw POST /v1/workflows/terminate --body '{"workflowId":"..."}' --confirm-write --json` |
| List instances | `vibe.py --raw GET /v1/workflows/instances --json` |
| Get instance | `vibe.py --raw GET /v1/workflows/instances/abc123 --json` |
| List templates | `vibe.py --raw GET /v1/workflows/templates --json` |
| Complete task | `vibe.py --raw POST /v1/workflows/task/complete --body '{"taskId":123,"status":1}' --confirm-write --json` |
| List tasks | `vibe.py --raw GET /v1/workflows/tasks --json` |
| Get task | `vibe.py --raw GET /v1/workflows/tasks/123 --json` |

## Triggers

| Action | Command |
|--------|---------|
| Fire trigger | `vibe.py --raw POST /v1/triggers/fire --body '{"code":"MY_TRIGGER","documentId":"DEAL_123"}' --confirm-write --json` |
| Add trigger | `vibe.py --raw POST /v1/triggers --body '{"code":"MY_TRIGGER","name":"Custom trigger","documentType":"deal"}' --confirm-write --json` |
| Delete trigger | `vibe.py --raw DELETE /v1/triggers/MY_TRIGGER --confirm-destructive --json` |
| List triggers | `vibe.py --raw GET /v1/triggers --json` |

## Key Fields

All field names use camelCase:

- `templateId` -- business process template ID
- `documentId` -- target document (e.g. `DEAL_123`, `LEAD_456`)
- `workflowId` -- running workflow instance ID
- `taskId` -- workflow task ID (approval/review step)
- `status` -- task completion status: `1` (approved), `2` (rejected), `3` (reviewed), `4` (cancelled)
- `code` -- trigger code (alphanumeric identifier)
- `documentType` -- entity type for trigger binding (`deal`, `lead`, `contact`, etc.)

## Common Use Cases

### Start a business process on a deal

```bash
python3 scripts/vibe.py --raw POST /v1/workflows/start \
  --body '{"templateId":1,"documentId":"DEAL_123"}' \
  --confirm-write --json
```

### List running workflow instances

```bash
python3 scripts/vibe.py --raw GET /v1/workflows/instances --json
```

### Complete an approval task

```bash
# Approve
python3 scripts/vibe.py --raw POST /v1/workflows/task/complete \
  --body '{"taskId":123,"status":1,"comment":"Approved by manager"}' \
  --confirm-write --json

# Reject
python3 scripts/vibe.py --raw POST /v1/workflows/task/complete \
  --body '{"taskId":123,"status":2,"comment":"Budget exceeded"}' \
  --confirm-write --json
```

### Terminate a running process

```bash
python3 scripts/vibe.py --raw POST /v1/workflows/terminate \
  --body '{"workflowId":"abc123"}' \
  --confirm-write --json
```

### List available templates

```bash
python3 scripts/vibe.py --raw GET /v1/workflows/templates --json
```

### Fire a custom trigger

```bash
python3 scripts/vibe.py --raw POST /v1/triggers/fire \
  --body '{"code":"MY_TRIGGER","documentId":"DEAL_123"}' \
  --confirm-write --json
```

## Task Statuses

- `1` -- approved
- `2` -- rejected
- `3` -- reviewed (acknowledged without approval/rejection)
- `4` -- cancelled

## Common Pitfalls

- `documentId` format is `ENTITY_ID` (e.g. `DEAL_123`, `LEAD_456`) -- include the entity type prefix.
- Workflow tasks are NOT the same as regular tasks in `references/tasks.md`. These are approval/review steps within a business process.
- Terminating a workflow stops all pending tasks in that process.
- Trigger codes are case-sensitive and must be unique.
- Write operations require `--confirm-write`, delete operations require `--confirm-destructive`.
