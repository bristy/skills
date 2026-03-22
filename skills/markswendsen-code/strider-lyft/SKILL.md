---
name: strider-lyft
description: Book rides via Lyft using Strider Labs MCP connector. Request rides, schedule pickups, compare ride types, track drivers. Complete autonomous ridesharing for your AI agent.
metadata:
  openclaw:
    requires:
      bins: ["npx"]
    category: "transportation"
    author: "Strider Labs"
    homepage: "https://striderlabs.ai"
---

# Strider Lyft Connector

MCP connector for booking rides through Lyft — request rides, schedule pickups, compare ride types, and track drivers in real-time. Part of the Strider Labs action execution layer for AI agents.

## Installation

```bash
npm install @striderlabs/mcp-lyft
```

## MCP Configuration

Add to your MCP client configuration (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "lyft": {
      "command": "npx",
      "args": ["-y", "@striderlabs/mcp-lyft"]
    }
  }
}
```

## Available Tools

### lyft.get_ride_estimates
Get price and time estimates for ride types.

**Input Schema:**
```json
{
  "pickup": {
    "address": "string",
    "lat": "number (optional)",
    "lng": "number (optional)"
  },
  "dropoff": {
    "address": "string",
    "lat": "number (optional)",
    "lng": "number (optional)"
  }
}
```

**Output:**
```json
{
  "ride_types": [{
    "type": "string (lyft, lyft_xl, lux, lux_black)",
    "price_estimate": "string ($12-15)",
    "price_min": "number",
    "price_max": "number",
    "eta_minutes": "number",
    "primetime_percentage": "number"
  }]
}
```

### lyft.request_ride
Request a ride now.

**Input Schema:**
```json
{
  "ride_type": "string",
  "pickup": "object",
  "dropoff": "object",
  "note_to_driver": "string (optional)"
}
```

### lyft.schedule_ride
Schedule a ride for a future time.

**Input Schema:**
```json
{
  "ride_type": "string",
  "pickup": "object",
  "dropoff": "object",
  "scheduled_time": "string (ISO datetime)"
}
```

### lyft.track_ride
Get real-time driver location and ETA.

**Output:**
```json
{
  "status": "string (matching, arriving, in_progress)",
  "driver": {
    "name": "string",
    "rating": "number",
    "vehicle": "string",
    "license_plate": "string"
  },
  "eta_minutes": "number",
  "driver_location": {
    "lat": "number",
    "lng": "number"
  }
}
```

### lyft.cancel_ride
Cancel a requested or scheduled ride.

### lyft.get_ride_history
Get past rides for reference or reporting.

### lyft.rate_ride
Rate a completed ride.

## Authentication

First use triggers OAuth authorization flow. Payment methods saved to Lyft account. Tokens stored encrypted per-user.

## Usage Examples

**Quick ride:**
```
Get me a Lyft from my house to SFO airport
```

**Compare options:**
```
What's the price difference between Lyft and Lyft XL to downtown?
```

**Schedule ahead:**
```
Schedule a Lyft to pick me up at 6am tomorrow for my flight
```

**Track driver:**
```
Where's my Lyft driver? How many minutes away?
```

## Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| AUTH_EXPIRED | Session expired | Re-authenticate |
| NO_DRIVERS | No drivers available | Suggest wait or alternatives |
| PRIMETIME | Surge pricing active | Inform and confirm |
| PAYMENT_FAILED | Card declined | Update payment method |

## Use Cases

- Airport trips: schedule rides for flights
- Commuting: daily rides to work
- Night out: safe rides home
- Group travel: Lyft XL for larger parties

## Links

- npm: https://npmjs.com/package/@striderlabs/mcp-lyft
- Strider Labs: https://striderlabs.ai
