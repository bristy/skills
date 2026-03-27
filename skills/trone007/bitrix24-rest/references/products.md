# Products and Product Rows

> **Note:** These endpoints use assumed Vibe Platform paths. Verify actual endpoints at runtime or check Vibe API documentation.

Product catalog management and attaching product rows to CRM entities (deals, quotes, invoices).

## Endpoints

| Action | Command |
|--------|---------|
| List products | `vibe.py --raw GET /v1/products --json` |
| Get product | `vibe.py --raw GET /v1/products/123 --json` |
| Create product | `vibe.py --raw POST /v1/products --body '{"name":"Widget","price":1000,"currencyId":"RUB"}' --confirm-write --json` |
| Product rows on deal | `vibe.py --raw GET /v1/deals/123/products --json` |
| Set product rows | `vibe.py --raw POST /v1/deals/123/products --body '{"rows":[{"productId":1,"quantity":5,"price":1000}]}' --confirm-write --json` |

## Key Fields (camelCase)

Product fields:

- `id` — product ID
- `name` — product name
- `price` — price per unit
- `currencyId` — currency code (e.g., `RUB`, `USD`)
- `active` — whether product is active
- `description` — product description
- `sectionId` — product category/section ID
- `measureCode` — unit of measure code

Product row fields:

- `productId` — ID from catalog (optional if using `productName`)
- `productName` — product name (auto-filled from catalog if `productId` given)
- `price` — price per unit including discounts and taxes
- `quantity` — quantity (default 1)
- `discountTypeId` — 1 = absolute, 2 = percentage
- `discountRate` — discount in percent
- `taxRate` — tax rate in percent
- `taxIncluded` — whether tax is included in price
- `sort` — sort order

## Copy-Paste Examples

### List all products

```bash
vibe.py --raw GET /v1/products --json
```

### Get a specific product

```bash
vibe.py --raw GET /v1/products/456 --json
```

### Create a product

```bash
vibe.py --raw POST /v1/products --body '{
  "name": "Widget Pro",
  "price": 1500,
  "currencyId": "RUB",
  "active": true
}' --confirm-write --json
```

### Get product rows on a deal

```bash
vibe.py --raw GET /v1/deals/123/products --json
```

### Set product rows on a deal

```bash
vibe.py --raw POST /v1/deals/123/products --body '{
  "rows": [
    {"productId": 456, "price": 1500, "quantity": 2},
    {"productName": "Custom Service", "price": 5000, "quantity": 1}
  ]
}' --confirm-write --json
```

## Common Pitfalls

- Setting product rows replaces all existing rows — always include all desired rows in one call.
- You can use either `productId` (from catalog) or `productName` (ad hoc) for each row.
- Currency codes must match portal settings — verify valid codes at runtime.
- Discount and tax fields interact — if `taxIncluded` is set, `price` already contains tax.
- Product sections/categories are managed separately — list them to find valid `sectionId` values.
