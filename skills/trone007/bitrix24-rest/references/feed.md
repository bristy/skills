# Activity Stream (Feed)

Use this file for the Bitrix24 news feed -- posting, reading, commenting, and sharing messages in the company feed.

## Entity CRUD

| Action | Command |
|--------|---------|
| List posts | `vibe.py posts --json` |
| Get post | `vibe.py posts/755 --json` |
| Create post | `vibe.py posts --create --body '{"title":"News","message":"Update!"}' --confirm-write --json` |
| Update post | `vibe.py posts/755 --update --body '{"message":"Updated text"}' --confirm-write --json` |
| Delete post | `vibe.py posts/755 --delete --confirm-destructive --json` |
| Search posts | `vibe.py posts/search --body '{"filter":{"createdAt":{"$gte":"2026-03-01"}}}' --json` |
| Fields | `vibe.py posts/fields --json` |

## Comments and Sharing

| Action | Command |
|--------|---------|
| Add comment | `vibe.py posts/755/comments --create --body '{"text":"Great work!"}' --confirm-write --json` |
| List comments | `vibe.py posts/755/comments --json` |
| Share post | `vibe.py posts/755 --update --body '{"addRecipients":["U42"]}' --confirm-write --json` |

## Key Fields

All field names use camelCase:

- `title` -- post title (optional)
- `message` -- post body text
- `recipients` -- array of recipient codes
- `createdAt` -- creation timestamp
- `authorId` -- post author user ID
- `important` -- flag for pinnable posts

## Recipients

Feed messages use recipient codes:

- `UA` -- all authorized users
- `U<id>` -- specific user (e.g. `U1`, `U42`)
- `SG<id>` -- workgroup/project (e.g. `SG15`)
- `DR<id>` -- department including subdepartments (e.g. `DR5`)

Default recipient: `["UA"]` (everyone).

## Filter Syntax

MongoDB-style operators in search:

| Operator | Meaning | Example |
|----------|---------|---------|
| `$eq` | Equals | `{"authorId":{"$eq":5}}` |
| `$gte` | Greater or equal | `{"createdAt":{"$gte":"2026-03-01"}}` |
| `$lte` | Less or equal | `{"createdAt":{"$lte":"2026-03-31"}}` |
| `$contains` | Contains substring | `{"message":{"$contains":"quarterly"}}` |

## Common Use Cases

### Read recent feed posts

```bash
python3 scripts/vibe.py posts --json
```

### Post a message to the entire company

```bash
python3 scripts/vibe.py posts --create \
  --body '{"message":"Hello team!","recipients":["UA"]}' \
  --confirm-write --json
```

### Post to a specific department

```bash
python3 scripts/vibe.py posts --create \
  --body '{"title":"Department Update","message":"Monthly results are ready.","recipients":["DR5"]}' \
  --confirm-write --json
```

### Post to a project group

```bash
python3 scripts/vibe.py posts --create \
  --body '{"message":"Sprint review tomorrow at 10:00","recipients":["SG15"]}' \
  --confirm-write --json
```

### Add a comment

```bash
python3 scripts/vibe.py posts/755/comments --create \
  --body '{"text":"Great work!"}' \
  --confirm-write --json
```

### Search posts by date

```bash
python3 scripts/vibe.py posts/search \
  --body '{"filter":{"createdAt":{"$gte":"2026-03-01","$lte":"2026-03-31"}}}' \
  --json
```

## Common Pitfalls

- Posts are visible only to specified recipients. Use `recipients` to control visibility.
- Comments inherit visibility from the parent post.
- Default recipient is `["UA"]` (all users) if not specified.
- `important` flag makes a post pinnable with an optional expiration date.
- Write operations require `--confirm-write`, delete operations require `--confirm-destructive`.
