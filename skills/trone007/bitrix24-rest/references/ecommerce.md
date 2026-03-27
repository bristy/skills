# E-Commerce

Use this file for e-commerce entities -- payments, basket items, and order statuses.

## Payments

| Action | Command |
|--------|---------|
| List payments | `vibe.py payments --json` |
| Get payment | `vibe.py payments/123 --json` |
| Create payment | `vibe.py payments --create --body '{"orderId":1,"amount":5000,"currency":"RUB","paySystemId":1}' --confirm-write --json` |
| Update payment | `vibe.py payments/123 --update --body '{"paid":true}' --confirm-write --json` |
| Delete payment | `vibe.py payments/123 --delete --confirm-destructive --json` |
| Search payments | `vibe.py payments/search --body '{"filter":{"paid":{"$eq":true}}}' --json` |
| Fields | `vibe.py payments/fields --json` |

## Basket Items

| Action | Command |
|--------|---------|
| List basket items | `vibe.py basket-items --json` |
| Get basket item | `vibe.py basket-items/123 --json` |
| Create basket item | `vibe.py basket-items --create --body '{"orderId":1,"productId":10,"quantity":2,"price":1500}' --confirm-write --json` |
| Update basket item | `vibe.py basket-items/123 --update --body '{"quantity":3}' --confirm-write --json` |
| Delete basket item | `vibe.py basket-items/123 --delete --confirm-destructive --json` |
| Search basket items | `vibe.py basket-items/search --body '{"filter":{"orderId":{"$eq":1}}}' --json` |
| Fields | `vibe.py basket-items/fields --json` |

## Order Statuses

| Action | Command |
|--------|---------|
| List order statuses | `vibe.py order-statuses --json` |
| Get order status | `vibe.py order-statuses/N --json` |
| Create order status | `vibe.py order-statuses --create --body '{"statusId":"CUSTOM","name":"Custom Status","sort":100}' --confirm-write --json` |
| Update order status | `vibe.py order-statuses/N --update --body '{"name":"Renamed Status"}' --confirm-write --json` |
| Delete order status | `vibe.py order-statuses/N --delete --confirm-destructive --json` |
| Fields | `vibe.py order-statuses/fields --json` |

## Key Fields

### Payment fields (camelCase)

- `orderId` -- parent order ID
- `amount` -- payment amount
- `currency` -- currency code (e.g. `RUB`, `USD`)
- `paid` -- payment status (boolean)
- `paySystemId` -- payment system ID
- `datePaid` -- payment date

### Basket item fields (camelCase)

- `orderId` -- parent order ID
- `productId` -- product catalog ID
- `quantity` -- item quantity
- `price` -- item price per unit
- `name` -- product name
- `discount` -- discount amount

### Order status fields (camelCase)

- `statusId` -- status code (string)
- `name` -- display name
- `sort` -- sort order
- `description` -- status description

## Filter Syntax

MongoDB-style operators in search:

| Operator | Meaning | Example |
|----------|---------|---------|
| `$eq` | Equals | `{"paid":{"$eq":true}}` |
| `$gte` | Greater or equal | `{"amount":{"$gte":1000}}` |
| `$lte` | Less or equal | `{"amount":{"$lte":50000}}` |
| `$in` | In list | `{"currency":{"$in":["RUB","USD"]}}` |

## Common Pitfalls

- Use `basket-items` with a hyphen, not `basketItems` or `basket_items`.
- Order status IDs are string codes (e.g. `N`, `P`, `F`), not numeric.
- Payment amounts do not include currency -- always specify `currency` separately.
- Write operations require `--confirm-write`, delete operations require `--confirm-destructive`.
