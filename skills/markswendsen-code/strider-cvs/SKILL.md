---
name: strider-cvs
description: Order from CVS Pharmacy via Strider Labs MCP connector. Refill prescriptions, shop health products, earn ExtraCare rewards, schedule vaccinations. Complete autonomous pharmacy management for your AI agent.
metadata:
  openclaw:
    requires:
      bins: ["npx"]
    category: "health"
    author: "Strider Labs"
    homepage: "https://striderlabs.ai"
---

# Strider CVS Connector

MCP connector for CVS Pharmacy — refill prescriptions, shop health and beauty products, earn ExtraCare rewards, and schedule vaccinations. Part of the Strider Labs action execution layer for AI agents.

## Installation

```bash
npm install @striderlabs/mcp-cvs
```

## MCP Configuration

Add to your MCP client configuration (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "cvs": {
      "command": "npx",
      "args": ["-y", "@striderlabs/mcp-cvs"]
    }
  }
}
```

## Available Tools

### cvs.get_prescriptions
Get list of prescriptions and refill status.

**Output:**
```json
{
  "prescriptions": [{
    "rx_number": "string",
    "medication": "string",
    "dosage": "string",
    "quantity": "number",
    "refills_remaining": "number",
    "last_filled": "string (ISO date)",
    "ready_for_refill": "boolean"
  }]
}
```

### cvs.refill_prescription
Request prescription refill.

**Input Schema:**
```json
{
  "rx_number": "string",
  "store_id": "string (optional: use default pharmacy)",
  "pickup_type": "string (instore, drive_through)"
}
```

### cvs.check_refill_status
Check if prescription is ready for pickup.

### cvs.search_products
Search CVS products.

**Input Schema:**
```json
{
  "query": "string",
  "category": "string (optional: health, beauty, household, etc.)",
  "store_id": "string (optional: for local inventory)"
}
```

### cvs.add_to_cart
Add products to shopping cart.

### cvs.checkout
Complete order for delivery or pickup.

### cvs.get_extracare_rewards
Check ExtraCare rewards and ExtraBucks balance.

**Output:**
```json
{
  "extrabucks": "number",
  "rewards": [{
    "description": "string",
    "discount": "string",
    "expires": "string"
  }]
}
```

### cvs.schedule_vaccination
Schedule flu shot, COVID vaccine, or other immunizations.

### cvs.find_stores
Find nearby CVS locations with pharmacy hours.

## Authentication

First use triggers OAuth with CVS.com account. ExtraCare card linked automatically. Tokens stored encrypted per-user.

## Usage Examples

**Refill medication:**
```
Refill my blood pressure medication at CVS
```

**Check prescription status:**
```
Is my prescription ready for pickup at CVS?
```

**Shop products:**
```
Order Tylenol and bandages from CVS with same-day delivery
```

**Use rewards:**
```
What ExtraBucks do I have? Apply them to my order.
```

**Schedule shot:**
```
Schedule a flu shot at the CVS near me for this Saturday
```

## Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| AUTH_EXPIRED | Session expired | Re-authenticate |
| NO_REFILLS | No refills remaining | Contact doctor |
| INSURANCE_ISSUE | Insurance problem | Contact pharmacy |
| APPT_UNAVAILABLE | No vaccine slots | Suggest alternative times |

## Use Cases

- Prescription management: refill and track medications
- Health shopping: vitamins, OTC medicines, first aid
- Vaccination scheduling: flu shots, COVID boosters
- Rewards optimization: maximize ExtraBucks savings

## Links

- npm: https://npmjs.com/package/@striderlabs/mcp-cvs
- Strider Labs: https://striderlabs.ai
