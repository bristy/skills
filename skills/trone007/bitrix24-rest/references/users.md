# Users, Departments, and Org Structure

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation. The `/v1/me` endpoint is confirmed.

User lookup, department hierarchy, subordinates, and org-structure queries.

## Endpoints

| Action | Command |
|--------|---------|
| Current user | `vibe.py --raw GET /v1/me --json` |
| List users | `vibe.py --raw GET /v1/users --json` |
| Get user | `vibe.py --raw GET /v1/users/5 --json` |
| Get departments | `vibe.py --raw GET /v1/departments --json` |
| Get subordinates | `vibe.py --raw GET '/v1/users?managerId=5' --json` |

## Key Fields (camelCase)

- `id` — user ID
- `name` — full name
- `email` — email address
- `position` — job title
- `departmentId` — department ID
- `managerId` — direct manager's user ID
- `active` — whether the user is active
- `phone` — work phone number

Department fields:

- `id` — department ID
- `name` — department name
- `parentId` — parent department ID (for building hierarchy tree)
- `headId` — user ID of department head

## Copy-Paste Examples

### Get current user identity

```bash
vibe.py --raw GET /v1/me --json
```

### List all active users

```bash
vibe.py --raw GET /v1/users --json
```

### Get a specific user

```bash
vibe.py --raw GET /v1/users/5 --json
```

### Get all departments

```bash
vibe.py --raw GET /v1/departments --json
```

### Get subordinates of a manager

```bash
vibe.py --raw GET '/v1/users?managerId=5' --json
```

## Common Pitfalls

- Always start with `/v1/me` to get the current webhook user's ID — do not assume it.
- Department hierarchy uses `parentId` — build a tree from flat list by grouping on this field.
- `headId` in department data gives the head's user ID directly.
- Pagination may apply — check response for `next` or `total` fields.
- User search by name may require separate query parameters — verify at runtime.
