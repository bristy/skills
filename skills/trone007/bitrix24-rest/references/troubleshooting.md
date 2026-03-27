# Troubleshooting

Use this file when Vibe Platform calls fail or the agent cannot reach the portal.

## Default Behavior

Do the first diagnosis yourself before asking the user anything.

Preferred order:

1. Run `scripts/check_connection.py --json`
2. Inspect the result: HTTP status, error code, message
3. Report concrete findings and one next fix
4. Only guide the user to vibecode.bitrix24.tech if no valid key exists

## Error Mapping

| HTTP | Code | What happened | User message |
|------|------|--------------|-------------|
| 401 | AUTH_REQUIRED | Key invalid | "Ключ не подошёл. Создайте новый на vibecode.bitrix24.tech" |
| 403 | KEY_REVOKED | Key disabled | "Ваш ключ был отключён. Создайте новый на vibecode.bitrix24.tech" |
| 403 | SCOPE_DENIED | Missing permissions | "Нет доступа к этому разделу. Создайте новый ключ с полными правами" |
| 404 | NOT_FOUND | Record not found | "Не нашёл запись с таким номером" |
| 422 | BITRIX_ERROR | Bitrix24 internal error | "Битрикс24 вернул ошибку, попробуйте позже" |
| 429 | RATE_LIMIT | Rate limited | Auto-pause ~45s + retry (user never sees this) |
| 502 | BITRIX_UNAVAILABLE | Portal down | "Портал Битрикс24 временно недоступен" |
| 400 | VALIDATION_ERROR | Agent error | Log, don't show to user |
| 500 | INTERNAL_ERROR | Server error | "Сервис временно недоступен" |

## Typical Failure: No Key Configured

If `check_connection.py` reports no key or `"source": "missing"`:

- Show the user onboarding instructions
- Direct them to vibecode.bitrix24.tech to create a key
- Once the key is configured, verify with `check_connection.py --json`

## Typical Failure: Key Invalid (401)

HTTP 401 with code `AUTH_REQUIRED`:

- The key was entered incorrectly or has expired
- Tell the user to create a new key on vibecode.bitrix24.tech
- Do not ask the user to debug the key — just replace it

## Typical Failure: Key Revoked (403)

HTTP 403 with code `KEY_REVOKED`:

- The key was disabled by the portal administrator
- Tell the user to create a new key on vibecode.bitrix24.tech

## Typical Failure: Missing Scope (403)

HTTP 403 with code `SCOPE_DENIED`:

- The key does not have permissions for the requested module
- Tell the user to create a new key with all scopes (full permissions) on vibecode.bitrix24.tech
- Name the specific module that was denied (CRM, Tasks, Calendar, etc.) if available in the error

## Typical Failure: Rate Limit (429)

HTTP 429 with code `RATE_LIMIT`:

- Handled automatically by vibe.py — pause ~45 seconds and retry
- The user should never see this error
- If retries are exhausted, report to the user that Bitrix24 is temporarily overloaded

## Typical Failure: Portal Unavailable (502)

HTTP 502 with code `BITRIX_UNAVAILABLE`:

- The Bitrix24 portal is temporarily down
- Auto-retry once after a short pause
- If still failing, tell the user: the portal is temporarily unavailable, try again in a few minutes

## User-Facing Style

Prefer:

- what you checked
- what failed
- what is already confirmed working
- one next action
- plain business language ("связь с Битрикс24", "доступ к CRM")
- doing the next safe step yourself before asking the user

Avoid:

- long lists of shell commands for the user
- asking for confirmation before a simple retry
- exposing API keys or secrets
- talking about curl, HTTP, JSON, DNS, or config mechanics unless explicitly asked
- multiple-choice menus
- technical jargon (status codes, error codes) in user-facing messages

## Response Templates

Bad:

- "What you need to do now: 1. go to settings 2. copy the key 3. run the check script 4. verify the response..."

Better for missing key:

- "Сейчас доступ к Битрикс24 не подключен. Подключитесь через vibecode.bitrix24.tech."

Better when auth failed:

- "Связь с Битрикс24 есть, но ключ не подтверждён. Создайте новый ключ."

Better when portal down:

- "Не удаётся связаться с Битрикс24. Попробуйте через пару минут."

## Autonomous Retry Rule

For safe read-only requests:

- Execute immediately
- If it fails, run `check_connection.py --json`
- If fixable, retry once automatically
- Only then report the blocker

Do not ask "Should I try again?" — just do it.
