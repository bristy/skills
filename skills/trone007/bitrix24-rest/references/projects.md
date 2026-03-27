# Projects and Workgroups

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation.

Workgroups, projects, project membership, and cross-entity queries (tasks in a project, files in a project).

## Endpoints

| Action | Command |
|--------|---------|
| List projects | `vibe.py --raw GET /v1/projects --json` |
| Get project | `vibe.py --raw GET /v1/projects/123 --json` |
| Create project | `vibe.py --raw POST /v1/projects --body '{"name":"Project X","description":"..."}' --confirm-write --json` |
| Get members | `vibe.py --raw GET /v1/projects/123/members --json` |

## Key Fields (camelCase)

- `id` — project ID
- `name` — project name
- `description` — project description
- `ownerId` — user ID of project owner
- `membersCount` — number of members
- `createdAt` — creation timestamp
- `visible` — whether project is visible to non-members
- `opened` — whether users can join without invitation

Member fields:

- `userId` — member's user ID
- `role` — member role (owner, moderator, member)

## Copy-Paste Examples

### List all projects

```bash
vibe.py --raw GET /v1/projects --json
```

### Get project details

```bash
vibe.py --raw GET /v1/projects/15 --json
```

### Create a new project

```bash
vibe.py --raw POST /v1/projects --body '{
  "name": "Marketing Q2",
  "description": "Q2 marketing campaign planning",
  "visible": true,
  "opened": false
}' --confirm-write --json
```

### List project members

```bash
vibe.py --raw GET /v1/projects/15/members --json
```

## Common Pitfalls

- Tasks within a project are queried separately — filter task list by `projectId` or `groupId`.
- Project files live in a separate disk storage — find the storage by project/group ID.
- Project chat is a separate entity — use chat/messaging APIs with the project's chat ID.
- Creating a project makes the current user the owner automatically.
- Verify member role values at runtime — they may differ from expected strings.
