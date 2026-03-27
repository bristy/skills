# CRM

Use this file for deals, contacts, companies, leads, activities, timeline, and stage history.

## Entity CRUD

### Deals

| Action | Command |
|--------|---------|
| List deals | `vibe.py deals --json` |
| Get deal | `vibe.py deals/123 --json` |
| Create deal | `vibe.py deals --create --body '{"title":"Deal","stageId":"NEW","opportunity":50000}' --confirm-write --json` |
| Update deal | `vibe.py deals/123 --update --body '{"stageId":"WON"}' --confirm-write --json` |
| Delete deal | `vibe.py deals/123 --delete --confirm-destructive --json` |
| Search deals | `vibe.py deals/search --body '{"filter":{"opportunity":{"$gte":100000}}}' --json` |
| Aggregate | `vibe.py deals/aggregate --body '{"field":"opportunity","function":"sum"}' --json` |
| Fields | `vibe.py deals/fields --json` |

### Contacts

| Action | Command |
|--------|---------|
| List contacts | `vibe.py contacts --json` |
| Get contact | `vibe.py contacts/123 --json` |
| Create contact | `vibe.py contacts --create --body '{"name":"John","lastName":"Doe","phone":"+1234567890"}' --confirm-write --json` |
| Update contact | `vibe.py contacts/123 --update --body '{"phone":"+0987654321"}' --confirm-write --json` |
| Delete contact | `vibe.py contacts/123 --delete --confirm-destructive --json` |
| Search contacts | `vibe.py contacts/search --body '{"filter":{"name":{"$contains":"John"}}}' --json` |
| Fields | `vibe.py contacts/fields --json` |

### Companies

| Action | Command |
|--------|---------|
| List companies | `vibe.py companies --json` |
| Get company | `vibe.py companies/123 --json` |
| Create company | `vibe.py companies --create --body '{"title":"Acme Corp"}' --confirm-write --json` |
| Update company | `vibe.py companies/123 --update --body '{"title":"Acme Corporation"}' --confirm-write --json` |
| Delete company | `vibe.py companies/123 --delete --confirm-destructive --json` |
| Search companies | `vibe.py companies/search --body '{"filter":{"title":{"$contains":"Acme"}}}' --json` |
| Fields | `vibe.py companies/fields --json` |

### Leads

| Action | Command |
|--------|---------|
| List leads | `vibe.py leads --json` |
| Get lead | `vibe.py leads/123 --json` |
| Create lead | `vibe.py leads --create --body '{"title":"New Lead","name":"Jane","lastName":"Smith"}' --confirm-write --json` |
| Update lead | `vibe.py leads/123 --update --body '{"statusId":"CONVERTED"}' --confirm-write --json` |
| Delete lead | `vibe.py leads/123 --delete --confirm-destructive --json` |
| Search leads | `vibe.py leads/search --body '{"filter":{"statusId":{"$eq":"NEW"}}}' --json` |
| Fields | `vibe.py leads/fields --json` |

## Activities, Timeline, Stage History

Use `--raw` mode for these endpoints.

### Activities

```bash
# List activities for a deal
python3 scripts/vibe.py --raw GET '/v1/crm/activities?ownerTypeId=2&ownerId=123' --json

# Add activity
python3 scripts/vibe.py --raw POST /v1/crm/activities \
  --body '{"ownerTypeId":2,"ownerId":123,"typeId":2,"subject":"Follow-up call"}' \
  --confirm-write --json
```

### Timeline Todo

```bash
# Add todo to deal timeline
python3 scripts/vibe.py --raw POST /v1/crm/timeline/todos \
  --body '{"ownerTypeId":2,"ownerId":123,"deadline":"2026-03-15T15:00:00","title":"Follow up with client","description":"Call to discuss proposal","responsibleId":5}' \
  --confirm-write --json
```

### Timeline Comments

```bash
# Add comment to deal timeline
python3 scripts/vibe.py --raw POST /v1/crm/timeline/comments \
  --body '{"entityId":123,"entityType":"deal","comment":"Client confirmed budget approval"}' \
  --confirm-write --json
```

### Timeline Log

```bash
# Add log entry to timeline
python3 scripts/vibe.py --raw POST /v1/crm/timeline/log \
  --body '{"entityTypeId":2,"entityId":123,"title":"Price changed","text":"Price updated from 100k to 120k after negotiation","iconCode":"info"}' \
  --confirm-write --json
```

### Stage History

```bash
# Get stage history for deals
python3 scripts/vibe.py --raw GET '/v1/crm/stagehistory?entityTypeId=2&filter[createdTime][$gte]=2026-03-01' --json
```

## Filter Syntax

MongoDB-style operators replace prefix operators:

| Operator | Meaning | Example |
|----------|---------|---------|
| `$eq` | Equals | `{"stageId":{"$eq":"WON"}}` |
| `$ne` | Not equal | `{"stageId":{"$ne":"LOSE"}}` |
| `$gt` | Greater than | `{"opportunity":{"$gt":10000}}` |
| `$gte` | Greater or equal | `{"opportunity":{"$gte":100000}}` |
| `$lt` | Less than | `{"opportunity":{"$lt":50000}}` |
| `$lte` | Less or equal | `{"createdAt":{"$lte":"2026-03-01"}}` |
| `$contains` | Contains substring | `{"title":{"$contains":"urgent"}}` |
| `$in` | In list | `{"stageId":{"$in":["NEW","WON"]}}` |

Example: find deals with opportunity above 100k:

```bash
python3 scripts/vibe.py deals/search \
  --body '{"filter":{"opportunity":{"$gte":100000}}}' --json
```

## Key Fields

All field names use camelCase:

- `title` — deal/lead/company name
- `stageId` — pipeline stage
- `opportunity` — deal amount
- `currencyId` — currency code
- `contactId` — linked contact
- `companyId` — linked company
- `assignedById` — responsible user
- `createdAt` — creation timestamp
- `updatedAt` — last modification timestamp

Use `{entity}/fields` to discover all available fields including custom fields:

```bash
python3 scripts/vibe.py deals/fields --json
```

## Entity Type IDs

| ID | Entity |
|----|--------|
| 1 | Lead |
| 2 | Deal |
| 3 | Contact |
| 4 | Company |
| 5 | Invoice (old) |
| 7 | Quote |
| 31 | Smart Invoice (new) |
| 128+ | Custom smart processes |

## Common Use Cases

### Stuck deals (no activity for 14+ days)

```bash
python3 scripts/vibe.py deals/search \
  --body '{"filter":{"assignedById":{"$eq":1},"stageSemanticId":{"$eq":"P"},"updatedAt":{"$lt":"2026-03-10"}}}' --json
```

`stageSemanticId=P` = in progress (active pipeline).

### Deals by stage

```bash
python3 scripts/vibe.py deals/search \
  --body '{"filter":{"stageId":{"$in":["NEW","PREPARATION"]}}}' --json
```

### Total deal value

```bash
python3 scripts/vibe.py deals/aggregate \
  --body '{"field":"opportunity","function":"sum"}' --json
```

## Working Rules

- Read `{entity}/fields` before writing custom or portal-specific fields.
- Do not hardcode stage names across portals — pipelines and categories vary.
- Field names are camelCase: `opportunity`, `stageId`, `assignedById`.
- Pagination: use `page` and `pageSize` query parameters.
- Use entity CRUD commands for deals, contacts, companies, leads.
- Use `--raw` mode for activities, timeline, and stage history.

## Good MCP Queries

- `crm deal list add update`
- `crm contact company`
- `crm lead fields`
- `crm activity`
- `crm activity todo add`
- `crm timeline comment`
- `crm timeline logmessage`
- `crm livefeedmessage`
- `crm stagehistory`
- `crm item smart process`
