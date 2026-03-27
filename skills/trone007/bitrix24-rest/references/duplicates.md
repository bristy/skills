# CRM Duplicate Search

Use this file for finding potential duplicate contacts, companies, and leads by phone or email.

## Endpoints

| Action | Command |
|--------|---------|
| Find by phone | `vibe.py --raw POST /v1/duplicates/find --body '{"type":"PHONE","values":["+79001234567"]}' --json` |
| Find by email | `vibe.py --raw POST /v1/duplicates/find --body '{"type":"EMAIL","values":["user@example.com"]}' --json` |
| Find by name | `vibe.py --raw POST /v1/duplicates/find --body '{"type":"NAME","values":["John Doe"]}' --json` |
| Batch search | `vibe.py --raw POST /v1/duplicates/find --body '{"type":"PHONE","values":["+79001234567","+79009876543"]}' --json` |

## Key Fields

- `type` -- search criterion: `PHONE`, `EMAIL`, `NAME`
- `values` -- array of values to search for (can search multiple at once)

## Response Structure

Returns potential duplicates grouped by entity type:

- `contacts` -- matching contact IDs
- `companies` -- matching company IDs
- `leads` -- matching lead IDs

Each match includes the entity ID and the field that matched.

## Common Use Cases

### Check if a phone number already exists in CRM

```bash
python3 scripts/vibe.py --raw POST /v1/duplicates/find \
  --body '{"type":"PHONE","values":["+79001234567"]}' \
  --json
```

### Check for email duplicates

```bash
python3 scripts/vibe.py --raw POST /v1/duplicates/find \
  --body '{"type":"EMAIL","values":["user@example.com"]}' \
  --json
```

### Search multiple phones at once

```bash
python3 scripts/vibe.py --raw POST /v1/duplicates/find \
  --body '{"type":"PHONE","values":["+79001234567","+79009876543","+79005551234"]}' \
  --json
```

### Pre-check before creating a contact

Before creating a new contact, check for duplicates:

```bash
# 1. Check if phone exists
python3 scripts/vibe.py --raw POST /v1/duplicates/find \
  --body '{"type":"PHONE","values":["+79001234567"]}' \
  --json

# 2. If no duplicates, create the contact
python3 scripts/vibe.py contacts --create \
  --body '{"name":"John","lastName":"Doe","phone":"+79001234567"}' \
  --confirm-write --json
```

## Common Pitfalls

- Always use international phone format with `+` prefix (e.g. `+79001234567`).
- `values` is an array even for a single value -- wrap in brackets: `["+79001234567"]`.
- This is a read-only search endpoint -- it does not merge or delete duplicates.
- The response may return empty arrays if no duplicates are found.
- Duplicate search is not a filter -- it uses fuzzy matching on phone/email/name.
