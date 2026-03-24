# Telegram Footer Patch

![Footer Preview](./assets/footer-preview.jpg)

Patch OpenClaw's Telegram reply pipeline to append a one-line footer in private chats (`🧠 Model + 💭 Think + 📊 Context`).

## What it does
- Adds a one-line footer for Telegram private-chat replies
- Shows model, think level, and context usage in one line
- Supports dry-run preview
- Creates a backup before any file change
- Supports rollback and verification after restart
- Targets current OpenClaw bundle layouts conservatively; final success must be confirmed by a real Telegram private-chat reply

## Recommended flow
1. Dry-run
2. Apply
3. Restart the gateway (**required** to take effect)
4. Send a real Telegram private-chat test message and verify the footer in the actual delivered reply

> Smoke test / marker verification only proves the patch hit candidate bundle files. If the real Telegram reply still has no footer, treat it as not fixed yet.

## Validated version boundary
- **Live-validated:** OpenClaw **2026.3.22**
- **Live-validated bundle path:** `/usr/lib/node_modules/openclaw/dist/agent-runner.runtime-BWpOtdxK.js`
- **Not live-validated:** other OpenClaw versions/builds
- **Claim boundary:** for untested versions, say “may be compatible” / “compatibility logic added”, not “supported”

## Before you run
- This updates OpenClaw frontend bundle files under `.../openclaw/dist/`.
- Run `python3 scripts/patch_reply_footer.py --dry-run` first.
- Confirm backups exist (`*.bak.telegram-footer.*`) and test rollback (`python3 scripts/revert_reply_footer.py --dry-run`).
- Use only on systems you control.

## Key files
- `SKILL.md` — usage guidance
- `scripts/patch_reply_footer.py` — patch script
- `scripts/revert_reply_footer.py` — rollback script
- `CHANGELOG.md` — release notes
- `LICENSE` — MIT license
