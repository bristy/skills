# Access and Auth

## Vibe Key Setup

1. Go to [vibecode.bitrix24.tech](https://vibecode.bitrix24.tech).
2. Sign in with your Bitrix24 account.
3. Create a new key and select **all scopes** for full access.
4. Copy the key.
5. Save and verify:

```bash
python3 scripts/vibe.py --raw GET /v1/me --json
```

The script will prompt for the key on first run and save it to `~/.config/bitrix24-skill/config.json`. The `GET /v1/me` call verifies the key works.

## Replacing a Key

Edit `~/.config/bitrix24-skill/config.json` directly, or delete the file and re-run the setup command above.

```bash
# Option 1: delete config and re-setup
rm ~/.config/bitrix24-skill/config.json
python3 scripts/vibe.py --raw GET /v1/me --json

# Option 2: edit the config file
# Replace the "vibe_key" value with your new key
```

## Agent Setup Behavior

When a user asks for setup help or a REST call fails:

1. Check saved config with `scripts/check_connection.py --json`
2. If the user already shared a key in the conversation, save it and retry
3. Only ask the user for a key if no saved config exists

Mask the key in user-facing output.

## Permissions / Scopes

Select **all scopes** when creating the key. This gives full access to CRM, Tasks, Calendar, Drive, Chat, Users, and all other modules.

If a method returns a permission error, the key was likely created with limited scopes. Create a new key with all scopes selected.

## Official MCP Docs Endpoint

```text
https://mcp-dev.bitrix24.tech/mcp
```

Tools exposed by the server:

- `bitrix-search`
- `bitrix-app-development-doc-details`
- `bitrix-method-details`
- `bitrix-article-details`
- `bitrix-event-details`
