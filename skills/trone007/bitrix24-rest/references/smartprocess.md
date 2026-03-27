# Smart Processes and Funnels

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation.

Custom CRM entity types (smart processes), their items, funnels/categories, and stages. Uses the universal `crm.item` approach with `entityTypeId`.

## Entity Type IDs

Standard types:

- `1` — lead
- `2` — deal
- `3` — contact
- `4` — company
- `7` — quote
- `31` — smart invoice
- `128+` — custom smart processes

## Endpoints

| Action | Command |
|--------|---------|
| List items | `vibe.py --raw GET '/v1/crm/items?entityTypeId=128' --json` |
| Get item | `vibe.py --raw GET /v1/crm/items/123 --json` |
| Create item | `vibe.py --raw POST /v1/crm/items --body '{"entityTypeId":128,"title":"Item","stageId":"NEW"}' --confirm-write --json` |
| List types | `vibe.py --raw GET /v1/crm/types --json` |

## Key Fields (camelCase)

- `id` — item ID
- `entityTypeId` — type identifier (mandatory for all operations)
- `title` — item title
- `stageId` — current stage ID
- `categoryId` — funnel/category ID
- `assignedById` — responsible user ID
- `createdBy` — creator user ID
- `dateCreate` — creation timestamp
- `opportunity` — monetary amount
- `currencyId` — currency code

Stage semantic IDs:

- `P` — in progress
- `S` — success (won)
- `F` — fail (lost)

## Copy-Paste Examples

### Discover custom smart process types

```bash
vibe.py --raw GET /v1/crm/types --json
```

### List items of a smart process (entityTypeId=128)

```bash
vibe.py --raw GET '/v1/crm/items?entityTypeId=128' --json
```

### Create an item in a smart process

```bash
vibe.py --raw POST /v1/crm/items --body '{
  "entityTypeId": 128,
  "title": "New application",
  "stageId": "NEW",
  "assignedById": 5
}' --confirm-write --json
```

### Get a specific item

```bash
vibe.py --raw GET /v1/crm/items/123 --json
```

## Common Pitfalls

- `entityTypeId` is mandatory for all item operations — omitting it causes errors.
- Use `/v1/crm/types` to discover `entityTypeId` values for custom processes.
- Fields use camelCase (`stageId`, `assignedById`, `categoryId`) in the universal API.
- Stage IDs are strings, not integers — pass them as `"NEW"`, `"WON"`, etc.
- Filter operators may be key prefixes: `>=dateCreate`, `!stageId`, `%title`.
- Always check field schema before writing custom field values.
