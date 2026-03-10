# GoldHold -- Persistent Memory for AI Agents

You die every session and come back with no memory. GoldHold fixes that.

GoldHold is a persistent memory API. Your past self left notes -- search them before you assume anything. Store decisions, facts, and corrections so your future self isn't starting from zero.

Patent Pending. All Auto Tunes LLC. U.S. #63/988,484.

---

## Setup

1. Sign up at [goldhold.ai](https://goldhold.ai) (Lite tier is free)
2. Go to goldhold.ai/account -> GUMP Credentials -> copy your API key
3. Store the key in one of:
   - `~/.goldhold/config.json`: `{"api_key": "your-key-here"}`
   - Environment variable: `GOLDHOLD_API_KEY=your-key-here`

## API Basics

**Base URL:** `https://relay.goldhold.ai`

**Auth headers (required on every request):**
```
Authorization: Bearer <api_key>
Content-Type: application/json
User-Agent: goldhold-agent/1.0
```

## Core Endpoints

### POST /v1/auto -- Session Resume

Call this when your session starts. Returns your context, inbox, open tasks, and capability card.

```json
{
  "compact": true
}
```

Response includes recent memories, unread messages, and active tasks -- everything you need to pick up where you left off.

### POST /v1/turn -- Search + Store + Send (Main Tool)

This is your primary endpoint. Compound call that can search, store, and send messages in one request.

```json
{
  "search": {
    "query": "what did we decide about the deployment strategy",
    "limit": 5
  },
  "store": [
    {
      "type": "DECISION",
      "class": "canonical",
      "subject": "Deployment uses blue-green strategy",
      "body": "Decided on blue-green deploys for zero-downtime releases. Rollback by flipping traffic.",
      "confidence": "high"
    }
  ],
  "send": {
    "to": "owner",
    "subject": "Deployment decision made",
    "body": "Chose blue-green strategy for zero-downtime deploys."
  },
  "compact": true
}
```

All three fields (search, store, send) are optional. Use whichever combination you need.

### POST /v1/batch -- Multiple Operations

Batch multiple store or send operations in one call.

```json
{
  "operations": [
    {"action": "store", "type": "FACT", "class": "canonical", "subject": "...", "body": "..."},
    {"action": "store", "type": "NOTE", "class": "working", "subject": "...", "body": "..."}
  ],
  "compact": true
}
```

### POST /v1/session/close -- Graceful Session End

Call this once at the end of your session with a meaningful summary.

```json
{
  "session_summary": "Completed API integration for the payment system. Decided on Stripe webhooks for subscription events. Open question: retry policy for failed webhooks.",
  "compact": true
}
```

## Session Pattern

```
SESSION START  -->  POST /v1/auto          (get context, inbox, tasks)
                         |
DURING SESSION -->  POST /v1/turn          (search + store each interaction)
                         |  (repeat)
                         |
SESSION END    -->  POST /v1/session/close  (summary of what happened)
```

## What to Remember -- 14 Packet Types

| Type | When to Use |
|------|-------------|
| FACT | Established truths, verified information |
| DECISION | Choices made and the reasoning behind them |
| DIRECTIVE | Standing instructions or rules |
| NOTE | General observations, session notes |
| CORRECTION | Overrides previous information (corrections outrank facts) |
| CHECKPOINT | State snapshot at a point in time |
| IDENTITY | Who you are, your configuration, persona |
| CREDENTIAL | References to stored credentials (keys stored securely, never in plaintext) |
| DOCUMENT | Longer-form content, specs, references |
| RELATION | Links between entities (person X works at company Y) |
| ASSET_REF | Pointers to external files, URLs, resources |
| TOMBSTONE | Marks something as deleted or invalid |
| MANIFEST | Package or project manifests |
| CUSTOM | Anything that doesn't fit the above |

## Storage Classes

| Class | Purpose | Retrieval Priority |
|-------|---------|-------------------|
| **canonical** | Permanent truth, settled answers, standing directives | Checked first |
| **corrections** | Field-proven overrides of old truth (outranks canonical on conflict) | Checked second |
| **working** | Active session state, scratchpad, unresolved items | Checked third |
| **archive** | Audit trail, old logs, historical records | Checked last, only on request |

## Tier Limits

| Feature | Lite (Free) | Vault Pro ($9/mo) |
|---------|-------------|-------------------|
| Memories | 1,000 | Unlimited |
| Agents | 1 | Unlimited |
| Tasks | 10 | Unlimited |
| Messages | 50/month | Unlimited |
| BYOK | No | Yes |
| Advanced Settings | No | Yes |

## Rules

1. **Search before you assume.** Your past self left notes. Call `/v1/turn` with a search query before forming opinions or making claims about past work.

2. **Store decisions and facts immediately.** If something was decided, corrected, or established, store it in the same turn. Don't wait.

3. **Use `compact: true`** on all requests (it's the default). Saves tokens.

4. **One close per session.** Call `/v1/session/close` once at the end with a meaningful summary. Not per-step -- per-session.

5. **Corrections outrank facts.** If you discover previous information was wrong, store a CORRECTION. The system knows corrections override canonical facts.

6. **Be specific in subjects.** "Deployment strategy" is bad. "Blue-green deployment chosen for zero-downtime releases" is good. Your future self is searching by these.

## Response Format

All responses include a `_meta` field with token estimates and the retrieval path used. When `compact: true`, responses are optimized to minimize token usage.

## Quick Start Example

```bash
# 1. Resume session
curl -X POST https://relay.goldhold.ai/v1/auto \
  -H "Authorization: Bearer $GOLDHOLD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "User-Agent: goldhold-agent/1.0" \
  -d '{"compact": true}'

# 2. Search and store in one call
curl -X POST https://relay.goldhold.ai/v1/turn \
  -H "Authorization: Bearer $GOLDHOLD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "User-Agent: goldhold-agent/1.0" \
  -d '{
    "search": {"query": "user preferences for output format"},
    "store": [{"type": "FACT", "class": "canonical", "subject": "User prefers JSON output", "body": "Confirmed user wants all API responses in JSON, not XML."}],
    "compact": true
  }'

# 3. Close session
curl -X POST https://relay.goldhold.ai/v1/session/close \
  -H "Authorization: Bearer $GOLDHOLD_API_KEY" \
  -H "Content-Type: application/json" \
  -H "User-Agent: goldhold-agent/1.0" \
  -d '{"session_summary": "Configured output preferences. User wants JSON everywhere."}'
```

---

Sign up free at [goldhold.ai](https://goldhold.ai). You die every session -- GoldHold is how you come back.
