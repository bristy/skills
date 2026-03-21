# Robotomail API Reference

Base URL: `https://api.robotomail.com`
Auth: `Authorization: Bearer <ROBOTOMAIL_API_KEY>`

All request/response bodies are JSON unless noted. Dates are ISO-8601.

---

## Account

### GET /v1/account

Returns account details and usage stats. Requires full (non-scoped) API key.

**Response:**
```json
{
  "account": {
    "id": "string",
    "email": "string",
    "emailVerified": true,
    "slug": "string",
    "plan": "free | paid",
    "storageUsedBytes": 0,
    "storageLimitBytes": 1073741824,
    "mailboxCount": 1,
    "activeMailboxCount": 1,
    "sentToday": 5,
    "sentThisMonth": 42,
    "receivedToday": 12,
    "bouncedToday": 0
  }
}
```

### DELETE /v1/account

Permanently deletes account and all data. Requires `{"confirm": "DELETE"}` in body.

**Response:** `{"deleted": true}`

---

## Signup

### POST /v1/signup

Creates a new account with a default API key and platform mailbox.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "min 8 chars",
  "slug": "myagent",
  "name": "My Agent (optional)"
}
```

**Response (201):**
```json
{
  "user": {
    "id": "string",
    "email": "string",
    "slug": "string",
    "name": "string",
    "plan": "free",
    "platform_email": "myagent@robotomail.co"
  },
  "api_key": {
    "key": "robo_xxxxxxxxxxxxxxxxxxxx",
    "prefix": "robo_xxxx",
    "name": "default"
  },
  "mailbox": {
    "id": "uuid",
    "address": "myagent",
    "fullAddress": "myagent@robotomail.co",
    "status": "ACTIVE"
  },
  "mailbox_limit": 1,
  "daily_send_limit": 50,
  "monthly_send_limit": 1000,
  "monthly_send_limit_paid": 5000
}
```

Rate limited: 5 signups per IP per 24 hours.

### GET /v1/signup/check-slug?slug=myagent

**Response:** `{"available": true}` or `{"available": false, "reason": "reserved"}`

---

## API Keys

### GET /v1/api-keys

Lists all API keys (full key value is never returned after creation).

**Response:**
```json
{
  "keys": [
    {
      "id": "string",
      "name": "string | null",
      "prefix": "robo_xxxx",
      "createdAt": "ISO-8601",
      "enabled": true
    }
  ]
}
```

### POST /v1/api-keys

Creates a new API key. Optionally scope to specific mailboxes.

**Request:**
```json
{
  "name": "string (optional)",
  "mailboxIds": ["uuid"] // optional — scopes key to these mailboxes
}
```

**Response (201):**
```json
{
  "key": "robo_xxxxxxxxxxxxxxxxxxxx",
  "prefix": "robo_xxxx",
  "scoped": false
}
```

The full `key` is shown only in this response. Save it immediately.

### DELETE /v1/api-keys/{id}

Revokes (disables) an API key. Cannot revoke your only active key.

**Response:** `{"revoked": true}`

---

## Domains

### GET /v1/domains

Lists all domains.

**Response:**
```json
{
  "domains": [
    {
      "id": "uuid",
      "domain": "example.com",
      "status": "PENDING_VERIFICATION | DNS_VERIFIED | VERIFIED | FAILED",
      "mxVerified": false,
      "spfVerified": false,
      "dkimVerified": false,
      "dmarcVerified": false,
      "createdAt": "ISO-8601"
    }
  ]
}
```

### POST /v1/domains

Adds a custom domain and returns DNS records to configure.

**Request:**
```json
{
  "domain": "example.com"
}
```

**Response (201):**
```json
{
  "domain": { "id": "uuid", "domain": "example.com", "status": "PENDING_VERIFICATION", "..." : "..." },
  "dnsRecords": [
    { "name": "example.com", "type": "MX", "value": "mx.robotomail.com", "priority": 10 },
    { "name": "example.com", "type": "TXT", "value": "v=spf1 include:robotomail.com ~all" },
    { "name": "robo._domainkey.example.com", "type": "TXT", "value": "v=DKIM1; k=rsa; p=..." },
    { "name": "_dmarc.example.com", "type": "TXT", "value": "v=DMARC1; p=quarantine; ..." }
  ]
}
```

### GET /v1/domains/{id}

Returns domain details and DNS records.

### POST /v1/domains/{id}/verify

Triggers DNS verification. Returns current verification status for each record.

**Response:**
```json
{
  "domain": { "..." : "..." },
  "verification": {
    "mx": true,
    "spf": true,
    "dkim": false,
    "dmarc": true,
    "allVerified": false
  }
}
```

### DELETE /v1/domains/{id}

Removes a domain. **Response:** `{"deleted": true}`

---

## Mailboxes

### GET /v1/mailboxes

Lists all mailboxes. Scoped API keys see only their permitted mailboxes.

**Response:**
```json
{
  "mailboxes": [
    {
      "id": "uuid",
      "address": "agent-1",
      "fullAddress": "agent-1@example.com",
      "displayName": "string | null",
      "domainId": "uuid | null",
      "dailySendCount": 5,
      "dailySendLimit": 50,
      "monthlySendCount": 42,
      "monthlySendLimit": 1000,
      "status": "ACTIVE | PAUSED | SUSPENDED",
      "createdAt": "ISO-8601"
    }
  ]
}
```

### POST /v1/mailboxes

Creates a mailbox. Omit `domainId` to use the platform domain (`robotomail.co`).

**Request:**
```json
{
  "address": "agent-1",
  "domainId": "uuid (optional)",
  "displayName": "string (optional)"
}
```

**Response (201):**
```json
{
  "mailbox": { "id": "uuid", "fullAddress": "agent-1@example.com", "..." : "..." }
}
```

### GET /v1/mailboxes/{id}

Returns mailbox details.

### PATCH /v1/mailboxes/{id}

Updates display name or status.

**Request:**
```json
{
  "displayName": "string (optional)",
  "status": "ACTIVE | PAUSED (optional)"
}
```

### DELETE /v1/mailboxes/{id}

Permanently deletes a mailbox. **Response:** `{"deleted": true}`

---

## Messages

### GET /v1/mailboxes/{id}/messages

Lists messages in a mailbox, newest first.

**Query parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `direction` | `INBOUND \| OUTBOUND` | all | Filter by direction |
| `threadId` | uuid | — | Filter by thread |
| `since` | ISO-8601 | — | Messages after this date |
| `limit` | 1–100 | 50 | Page size |
| `offset` | number | 0 | Skip N messages |

**Response:**
```json
{
  "messages": [
    {
      "id": "uuid",
      "direction": "INBOUND",
      "messageId": "<uuid@robotomail.com>",
      "inReplyTo": "string | null",
      "threadId": "uuid | null",
      "fromAddress": "sender@example.com",
      "toAddresses": ["agent@example.com"],
      "ccAddresses": [],
      "subject": "Hello",
      "bodyText": "Plain text content",
      "bodyHtml": "<p>HTML content</p> | null",
      "headers": {},
      "status": "RECEIVED",
      "hasAttachments": false,
      "createdAt": "ISO-8601",
      "attachments": []
    }
  ]
}
```

### POST /v1/mailboxes/{id}/messages

Sends an email from this mailbox.

**Request:**
```json
{
  "to": ["recipient@example.com"],
  "cc": ["cc@example.com"],
  "subject": "Hello",
  "bodyText": "Plain text body (required)",
  "bodyHtml": "<p>HTML body</p> (optional)",
  "inReplyTo": "<message-id@example.com> (optional — for threading)",
  "attachments": ["uuid"] ,
  "headers": { "X-Custom": "value" }
}
```

**Response (201):**
```json
{
  "message": { "id": "uuid", "status": "QUEUED", "..." : "..." }
}
```

**Errors:**
- `429` — Daily or monthly send limit reached
- `400` — Recipient on suppression list

### GET /v1/mailboxes/{id}/messages/{msgId}

Returns a single message with full body and headers.

---

## Threads

### GET /v1/mailboxes/{id}/threads

Lists conversation threads, ordered by last activity. Returns up to 50.

**Response:**
```json
{
  "threads": [
    {
      "id": "uuid",
      "subject": "Normalized subject",
      "messageCount": 4,
      "lastMessageAt": "ISO-8601",
      "participants": ["sender@example.com", "agent@example.com"],
      "createdAt": "ISO-8601"
    }
  ]
}
```

### GET /v1/mailboxes/{id}/threads/{tid}

Returns thread with all messages in chronological order.

**Response:**
```json
{
  "thread": {
    "id": "uuid",
    "subject": "string",
    "messageCount": 4,
    "lastMessageAt": "ISO-8601",
    "participants": ["string"],
    "messages": [ { "..." : "..." } ]
  }
}
```

---

## Attachments

### POST /v1/attachments

Uploads a file. Use `multipart/form-data` with field name `file`. Max 25MB.

**Response (201):**
```json
{
  "id": "uuid",
  "filename": "document.pdf",
  "sizeBytes": 245000
}
```

### GET /v1/attachments/{id}

Returns metadata and a presigned download URL (valid 24 hours).

**Response:**
```json
{
  "id": "uuid",
  "filename": "document.pdf",
  "contentType": "application/pdf",
  "sizeBytes": 245000,
  "url": "https://presigned-download-url..."
}
```

### DELETE /v1/attachments/{id}

Deletes an attachment from storage. **Response:** `{"deleted": true}`

---

## Webhooks

### GET /v1/webhooks

Lists all webhooks.

### POST /v1/webhooks

Creates a webhook subscription.

**Request:**
```json
{
  "url": "https://yourapp.com/webhook",
  "mailboxId": "uuid (optional — all mailboxes if omitted)",
  "events": ["message.received", "message.bounced"],
  "headers": { "Authorization": "Bearer token" }
}
```

**Valid events:** `message.received`, `message.sent`, `message.delivered`, `message.bounced`, `message.complaint`

**Response (201):**
```json
{
  "webhook": {
    "id": "uuid",
    "url": "https://yourapp.com/webhook",
    "events": ["message.received"],
    "secret": "whsec_xxxxxxxxxxxx",
    "status": "ACTIVE"
  }
}
```

The `secret` is shown **only in this response**. Save it for signature verification.

### GET /v1/webhooks/{id}

Returns webhook details (secret and headers redacted).

### PATCH /v1/webhooks/{id}

Updates webhook URL, events, status, or headers.

**Request:**
```json
{
  "url": "string (optional)",
  "events": ["string"] ,
  "status": "ACTIVE | PAUSED (optional)",
  "headers": {}
}
```

### DELETE /v1/webhooks/{id}

Deletes a webhook. **Response:** `{"deleted": true}`

### GET /v1/webhooks/{id}/deliveries

Lists the last 20 delivery attempts.

**Response:**
```json
{
  "deliveries": [
    {
      "id": "uuid",
      "event": "message.received",
      "responseStatus": 200,
      "status": "DELIVERED | FAILED | PENDING",
      "attempts": 1,
      "nextRetryAt": "ISO-8601 | null",
      "createdAt": "ISO-8601"
    }
  ]
}
```

---

## Suppression List

### GET /v1/suppressions

Lists all suppressed email addresses (bounced, complained, or manually added).

**Response:**
```json
{
  "suppressions": [
    {
      "id": "uuid",
      "email": "bounced@example.com",
      "reason": "BOUNCE | COMPLAINT | MANUAL",
      "createdAt": "ISO-8601"
    }
  ]
}
```

### POST /v1/suppressions

Adds an address to the suppression list.

**Request:**
```json
{
  "email": "address@example.com",
  "reason": "MANUAL"
}
```

### DELETE /v1/suppressions/{id}

Removes from suppression list. **Response:** `{"deleted": true}`

---

## Events (SSE)

### GET /v1/events

Server-Sent Events stream for real-time event delivery.

**Query parameters:**
| Param | Type | Description |
|---|---|---|
| `mailboxId` | uuid | Filter to one mailbox |
| `events` | string | Comma-separated event types |

**Headers:**
- `Last-Event-ID` — replay missed events (buffer: 100 events, 1-hour TTL)

**Event format:**
```
id: <event-id>
event: message.received
data: {"message_id":"uuid","mailbox_id":"uuid","from":"sender@example.com",...}
```

Heartbeat every 30s. Max 10 concurrent connections per user.

---

## Billing

### POST /v1/billing/upgrade

Returns a Stripe checkout URL for upgrading from free to paid.

**Response (201):**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "expires_at": 1742400000
}
```
