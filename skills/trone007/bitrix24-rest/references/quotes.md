# Quotes and Invoices

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation.

Commercial proposals (quotes) and smart invoices. Quotes are CRM entities for sending price offers to clients.

## Endpoints

| Action | Command |
|--------|---------|
| List quotes | `vibe.py --raw GET /v1/quotes --json` |
| Create quote | `vibe.py --raw POST /v1/quotes --body '{"title":"Quote","contactId":123,"opportunity":50000}' --confirm-write --json` |
| Smart invoices | `vibe.py --raw GET '/v1/crm/items?entityTypeId=31' --json` |

## Key Fields (camelCase)

Quote fields:

- `id` — quote ID
- `title` — quote title
- `statusId` — status (`DRAFT`, `SENT`, `APPROVED`, `DECLINED`)
- `opportunity` — total amount
- `currencyId` — currency code
- `contactId` — linked contact ID
- `companyId` — linked company ID
- `dealId` — linked deal ID
- `assignedById` — responsible user ID
- `beginDate` — start date
- `closeDate` — close date

Smart invoice fields (entityTypeId=31):

- `id` — invoice ID
- `title` — invoice title
- `stageId` — current stage
- `opportunity` — total amount
- `currencyId` — currency code
- `companyId` — linked company ID

## Copy-Paste Examples

### List all quotes

```bash
vibe.py --raw GET /v1/quotes --json
```

### Create a quote

```bash
vibe.py --raw POST /v1/quotes --body '{
  "title": "Quote for consulting services",
  "statusId": "DRAFT",
  "currencyId": "RUB",
  "opportunity": 50000,
  "companyId": 1,
  "contactId": 123,
  "assignedById": 5
}' --confirm-write --json
```

### List smart invoices

```bash
vibe.py --raw GET '/v1/crm/items?entityTypeId=31' --json
```

## Common Pitfalls

- Quotes and smart invoices are different entities — quotes use `/v1/quotes`, invoices use the universal `crm.item` API with `entityTypeId=31`.
- Legacy `crm.invoice.*` methods are deprecated — always use `crm.item.*` with `entityTypeId=31` for new invoices.
- Quote product rows may have a separate endpoint — verify at runtime.
- Invoice product rows use the universal product row API with owner type for smart invoices.
- Status values are strings (`DRAFT`, `SENT`, etc.) — verify available statuses at runtime.
