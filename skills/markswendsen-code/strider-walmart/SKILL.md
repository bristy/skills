---
name: strider-walmart
description: Shop Walmart via Strider Labs MCP connector. Search products, check store inventory, add items to cart, manage pickup/delivery. Complete autonomous shopping for your AI agent.
metadata:
  openclaw:
    requires:
      bins: ["npx"]
    category: "commerce"
    author: "Strider Labs"
    homepage: "https://striderlabs.ai"
---

# Strider Walmart Connector

MCP connector for shopping at Walmart — search products, check inventory, manage cart, and order for pickup or delivery. Part of the Strider Labs action execution layer for AI agents.

## Installation

```bash
npm install @striderlabs/mcp-walmart
```

## MCP Configuration

Add to your MCP client configuration (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "walmart": {
      "command": "npx",
      "args": ["-y", "@striderlabs/mcp-walmart"]
    }
  }
}
```

## Available Tools

### walmart.search_products
Search Walmart's catalog by keyword, category, or brand.

**Input Schema:**
```json
{
  "query": "string (search terms)",
  "category": "string (optional: grocery, electronics, home, etc.)",
  "sort": "string (optional: price_low, price_high, rating, relevance)",
  "store_id": "string (optional: for inventory check)"
}
```

**Output:**
```json
{
  "products": [{
    "id": "string",
    "name": "string",
    "price": "number",
    "rating": "number",
    "in_stock": "boolean",
    "pickup_available": "boolean",
    "delivery_available": "boolean",
    "image_url": "string"
  }]
}
```

### walmart.add_to_cart
Add products to shopping cart with specified quantity.

**Input Schema:**
```json
{
  "product_id": "string",
  "quantity": "number",
  "fulfillment": "string (pickup or delivery)"
}
```

### walmart.get_cart
Retrieve current cart contents and totals.

### walmart.checkout
Complete purchase with saved payment method.

**Input Schema:**
```json
{
  "fulfillment_type": "string (pickup or delivery)",
  "store_id": "string (for pickup)",
  "delivery_address": "object (for delivery)",
  "payment_method_id": "string"
}
```

### walmart.check_inventory
Check real-time inventory at a specific store.

### walmart.find_stores
Find nearby Walmart stores by location.

## Authentication

First use triggers OAuth authorization flow:
1. User is redirected to Walmart to authorize
2. Tokens are stored encrypted per-user
3. Automatic refresh handles token expiration

No API key required — connector manages OAuth flow.

## Usage Examples

**Search for groceries:**
```
Search Walmart for organic milk and add the best-rated one to my cart
```

**Weekly grocery order:**
```
Order my usual groceries from Walmart: eggs, bread, milk, bananas, chicken breast
```

**Check pickup availability:**
```
Is the PlayStation 5 available for pickup at my local Walmart?
```

## Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| AUTH_EXPIRED | Session expired | Re-authenticate |
| OUT_OF_STOCK | Item unavailable | Suggest alternatives |
| STORE_UNAVAILABLE | Store closed | Try different store |
| RATE_LIMITED | Too many requests | Retry after delay |

## Use Cases

- Weekly grocery shopping: automate recurring orders
- Price comparison: search across categories
- Pickup coordination: find items available at nearby stores
- Bulk ordering: household supplies and pantry staples

## Links

- npm: https://npmjs.com/package/@striderlabs/mcp-walmart
- Strider Labs: https://striderlabs.ai
