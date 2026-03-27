# Telephony

Use this file for call record management in CRM. This does NOT make real phone calls -- it creates call records for integrating external PBX systems.

## Endpoints

| Action | Command |
|--------|---------|
| Register call | `vibe.py --raw POST /v1/calls/register --body '{"type":1,"phoneNumber":"+79001234567","userId":5}' --confirm-write --json` |
| Finish call | `vibe.py --raw POST /v1/calls/finish --body '{"callId":"...","duration":120}' --confirm-write --json` |
| Attach recording | `vibe.py --raw POST /v1/calls/recording/attach --body '{"callId":"...","fileUrl":"https://..."}' --confirm-write --json` |
| Attach transcript | `vibe.py --raw POST /v1/calls/transcript/attach --body '{"callId":"...","transcript":"Customer requested callback"}' --confirm-write --json` |
| Get statistics | `vibe.py --raw GET /v1/calls/statistics --json` |
| Get call details | `vibe.py --raw GET /v1/calls/abc123 --json` |
| List calls | `vibe.py --raw GET /v1/calls --json` |

## Key Fields

All field names use camelCase:

- `callId` -- unique call identifier (returned by register)
- `type` -- call direction: `1` (outbound), `2` (inbound), `3` (inbound with forwarding), `4` (callback)
- `phoneNumber` -- phone number in international format
- `userId` -- user who made/received the call
- `duration` -- call duration in seconds
- `statusCode` -- call result code
- `transcript` -- call transcript text
- `fileUrl` -- URL to call recording file

## Common Use Cases

### Register an outbound call

```bash
python3 scripts/vibe.py --raw POST /v1/calls/register \
  --body '{"type":1,"phoneNumber":"+79001234567","userId":5}' \
  --confirm-write --json
```

Returns `callId` for use in subsequent operations.

### Finish a call

```bash
python3 scripts/vibe.py --raw POST /v1/calls/finish \
  --body '{"callId":"abc123","duration":120,"statusCode":200}' \
  --confirm-write --json
```

### Attach transcript

```bash
python3 scripts/vibe.py --raw POST /v1/calls/transcript/attach \
  --body '{"callId":"abc123","transcript":"Customer agreed to meeting on Friday. Needs updated pricing proposal."}' \
  --confirm-write --json
```

### Get call statistics

```bash
python3 scripts/vibe.py --raw GET /v1/calls/statistics --json
```

## Call Type Codes

- `1` -- outbound call
- `2` -- inbound call
- `3` -- inbound with forwarding
- `4` -- callback request

## Common Pitfalls

- This does NOT make real phone calls. It creates call records in CRM for integrating external PBX systems.
- Always use international phone format with `+` prefix (e.g. `+79001234567`).
- You must call `register` first to get a `callId`, then `finish` to complete the record.
- Duration is in seconds, not minutes.
- Call records are linked to CRM entities (contacts/companies) automatically by phone number matching.
- Write operations require `--confirm-write`.
