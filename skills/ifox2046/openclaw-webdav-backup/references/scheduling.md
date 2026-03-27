# Scheduled backups

Two lightweight scheduling options are supported:
1. `cron`
2. `systemd timer`

## Cron example

Adjust paths for the target machine:
```cron
30 3 * * * cd "$HOME/.openclaw/workspace" && /usr/bin/bash scripts/openclaw-backup.sh --encrypt-config --upload >> "$HOME/.openclaw/workspace/logs/openclaw-backup.log" 2>&1
```

### Notes
- creates one encrypted backup per day at 03:30
- uploads to the user's own WebDAV target
- logs to `~/.openclaw/workspace/logs/openclaw-backup.log`

### Before enabling
- confirm `.env.backup` is configured
- confirm the backup password is available via env var, `.env.backup.secret`, or interactive setup where appropriate
- confirm a manual run succeeds first

## systemd timer

Example installation flow (adjust paths if needed):
```bash
mkdir -p ~/.config/systemd/user
cp "$HOME/.openclaw/workspace/ops/systemd/openclaw-backup.service" ~/.config/systemd/user/
cp "$HOME/.openclaw/workspace/ops/systemd/openclaw-backup.timer" ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now openclaw-backup.timer
```

## Logs and checks
```bash
crontab -l
journalctl --user -u openclaw-backup.service -n 100 --no-pager
tail -f "$HOME/.openclaw/workspace/logs/openclaw-backup.log"
```

## Retention reminder

The script already supports automatic cleanup:
- `LOCAL_KEEP`
- `REMOTE_KEEP`

Example:
```bash
LOCAL_KEEP=7 REMOTE_KEEP=7 bash scripts/openclaw-backup.sh --encrypt-config --upload
```
