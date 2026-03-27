---
name: openclaw-webdav-backup
description: Backup and restore an OpenClaw workspace with optional config encryption and optional WebDAV upload. Use when users want OpenClaw backup, restore, VM migration/disaster recovery, encrypted config backups, WebDAV-based offsite copies, or scheduled backups. Users must provide their own WebDAV service and credentials.
---

# OpenClaw WebDAV Backup

Lightweight backup/restore skill for OpenClaw.

It covers:
- local backup archives
- optional encryption for `openclaw.json`
- optional WebDAV upload
- restore from local backup archives
- lightweight scheduled backup guidance
- optional Telegram notifications for backup success/failure

It does **not** provide WebDAV storage. The user must supply their own WebDAV endpoint and credentials.

## When to use this skill

Use this skill when the user asks to:
- back up OpenClaw
- restore OpenClaw from backup
- migrate OpenClaw to a new VM or machine
- protect backup configs with encryption
- upload backups to a self-provided WebDAV target
- schedule daily or periodic backups
- receive Telegram notifications for scheduled backup success/failure
- prepare a simple disaster-recovery workflow

## Implementation layout

Canonical implementation lives inside the skill:
- `scripts/openclaw-backup.impl.sh`
- `scripts/openclaw-restore.impl.sh`

Thin wrapper scripts may also exist in the workspace and call these implementations. Keep the skill scripts as the source of truth.

## Default workflow

### 1. Local backup
```bash
bash skills/openclaw-webdav-backup/scripts/openclaw-backup.sh
```

### 2. Encrypted backup + WebDAV upload
Prepare `.env.backup` with the user's own WebDAV settings, then run:
```bash
bash skills/openclaw-webdav-backup/scripts/openclaw-backup.sh --encrypt-config --upload
```
Only do real upload after confirming the user wants to write to the remote WebDAV target.

### 3. Restore from a local backup set
```bash
bash skills/openclaw-webdav-backup/scripts/openclaw-restore.sh --from backups/openclaw/latest --decrypt-config
```

## Important behavior notes

- `openclaw.json` may contain secrets, tokens, and API keys
- prefer `--encrypt-config` before remote upload
- `.env.backup` stores WebDAV connection settings and should not be committed
- `.env.backup.secret` is optional; it is only a convenience carrier for `BACKUP_ENCRYPT_PASS`
- `.env.backup.notify` is optional and enables Telegram backup notifications when configured
- restore depends on the **decryption password itself**, not on the secret file specifically
- for encrypted backups, `.env.backup.secret` and the password are **either/or**: either keep the file, or remember/provide the password
- workspace backups exclude `.env.backup` and `.env.backup.secret`
- local and remote retention are supported through `LOCAL_KEEP` and `REMOTE_KEEP`
- current notification support is Telegram-first; WeChat notification is not implemented yet

## Read references when needed

- For usage, included files, and backup examples: read `references/backup.md`
- For restore/decrypt flow and restore checks: read `references/restore.md`
- For automation with cron/systemd: read `references/scheduling.md`
- For migration/disaster-recovery planning: read `references/migration-plan.md`
- For common user questions and boundary clarifications: read `references/faq.md`
- For config template examples: read `references/env.backup.example`, `references/env.backup.secret.example`, and `references/env.backup.notify.example`

## Validated behaviors

This skill has been validated against a real OpenClaw setup for:
- local backup creation
- encrypted config backup
- WebDAV upload
- local and remote retention
- restore drill to a simulated fresh-machine home directory
- cron-based scheduled backup
- Telegram notification on backup success

## Private-share checklist

Before sharing this skill privately, verify:
- no real `.env.backup` or `.env.backup.secret` is included
- no real WebDAV URL, username, password, token, or backup passphrase remains in tracked files
- examples use placeholder values only
- docs state clearly that WebDAV storage is user-provided
- restore wording states password and secret file are either/or, not both required
- references match actual script behavior

## Scope

This skill intentionally stays lightweight. It supports:
- local backup and restore
- optional config encryption
- optional WebDAV upload
- local and remote retention
- password-based restore with optional secret file automation

It does not currently provide:
- built-in WebDAV provisioning
- secret-manager integration
- fully automatic remote download-and-restore flow
- multi-target cloud replication
