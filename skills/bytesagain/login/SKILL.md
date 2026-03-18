---
version: "1.0.0"
author: BytesAgain
homepage: https://bytesagain.com
source: https://github.com/bytesagain/ai-skills
description: "Store, retrieve, and manage login credentials securely using bash and Python with local encryption. Use when saving website logins, API keys, or generating secure passwords."
---

# Login — Credential Manager & Password Vault

A local credential management tool for storing website logins, API keys, and service credentials securely. Features include password generation, credential search, strength checking, and encrypted export. All data is stored locally in JSONL format with optional field-level obfuscation.

## Prerequisites

- Python 3.6+
- Bash 4+

## Data Storage

All credential records are stored in `~/.login/data.jsonl`. Each record is a JSON object with fields including `id`, `type` (credential, note), `service`, `username`, `password` (base64-obfuscated), `url`, `tags`, `created_at`, `updated_at`, and optional metadata.

## Commands

Run via: `bash scripts/script.sh <command> [options]`

| Command | Description |
|---|---|
| `add` | Add a new credential entry with service name, username, password, and URL |
| `list` | List all stored credentials (passwords masked by default) |
| `get` | Retrieve a specific credential by ID or service name (shows password) |
| `update` | Update an existing credential's username, password, URL, or tags |
| `delete` | Remove a credential entry by ID |
| `search` | Search credentials by service name, username, URL, or tags |
| `generate` | Generate a secure random password with configurable length and rules |
| `strength` | Check the strength of a given password and provide improvement tips |
| `duplicate` | Find credentials with duplicate or similar passwords |
| `expire` | List credentials older than a specified number of days |
| `export` | Export credentials to encrypted JSON or CSV format |
| `import` | Import credentials from a JSON or CSV file |
| `help` | Show usage information |
| `version` | Print the tool version |

## Usage Examples

```bash
# Add a new credential
bash scripts/script.sh add --service "GitHub" --username "myuser" --password "s3cureP@ss" --url "https://github.com" --tags "dev,git"

# List all credentials (passwords masked)
bash scripts/script.sh list

# Get a specific credential (shows password)
bash scripts/script.sh get --service "GitHub"

# Get by ID
bash scripts/script.sh get --id abc123

# Update a credential
bash scripts/script.sh update --id abc123 --password "newP@ssw0rd!" --tags "dev,git,work"

# Delete a credential
bash scripts/script.sh delete --id abc123

# Search by tag
bash scripts/script.sh search --tag "dev"

# Search by service name
bash scripts/script.sh search --query "git"

# Generate a 20-character password
bash scripts/script.sh generate --length 20 --symbols --numbers --uppercase

# Generate without ambiguous characters
bash scripts/script.sh generate --length 16 --no-ambiguous

# Check password strength
bash scripts/script.sh strength --password "mypassword123"

# Find duplicate passwords
bash scripts/script.sh duplicate

# Find credentials older than 90 days
bash scripts/script.sh expire --days 90

# Export encrypted
bash scripts/script.sh export --format json --output credentials.json

# Import from file
bash scripts/script.sh import --file credentials.csv --format csv
```

## Output Format

`list` returns a masked table with service, username, and URL. `get` returns full JSON including the decoded password. `generate` outputs the generated password to stdout. `strength` returns a score (0-100) with a rating and tips. `duplicate` and `expire` return filtered credential lists.

## Notes

- Passwords are stored with base64 obfuscation — this is NOT encryption. For true security, use OS-level disk encryption.
- Password generation supports: uppercase, lowercase, digits, symbols, and exclusion of ambiguous characters (`0O1lI`).
- Strength scoring considers: length, character variety, common patterns, dictionary words, and entropy.
- Strength ratings: `weak` (0-30), `fair` (31-50), `good` (51-70), `strong` (71-90), `excellent` (91-100).
- The `expire` command helps identify stale credentials that should be rotated.
- The `duplicate` command identifies password reuse across services.
- Export with `--format json` includes all fields; CSV omits sensitive notes.
- Import supports merging or overwriting existing entries.
- All IDs are auto-generated 8-character hex strings.

---

Powered by BytesAgain | bytesagain.com | hello@bytesagain.com
