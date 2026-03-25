---
name: fb-group-scanner
description: >
  CREDENTIALS REQUIRED: FB_COOKIE_FILE (Facebook session cookies JSON — treat as password),
  FB_STATE_FILE (Playwright state path, writable). Optional: FB_DRY_RUN (default true — no
  live comments until explicitly set false), FB_USER_AGENT, NOTIFY_WEBHOOK.
  INSTALL: pip install patchright && python -m patchright install chromium (PyPI + Playwright
  Chromium distribution). Scans Facebook groups for keyword-matching posts using Patchright
  (stealth Chromium), GraphQL response interception, and human-like mouse/scroll behavior.
  Auto-comments on matches. Use when building a bot that monitors FB groups for targeted
  hiring posts, comments on them, and notifies via webhook. Security: runs in dry-run mode
  by default; requires explicit opt-in for live commenting; no hardcoded endpoints or keys.
metadata:
  {
    "openclaw":
      {
        "requires":
          {
            "bins": ["python3"],
          },
        "install":
          [
            {
              "id": "patchright",
              "kind": "shell",
              "command": "pip install -r scripts/requirements.txt",
              "label": "Install patchright (PyPI)",
            },
            {
              "id": "chromium",
              "kind": "shell",
              "command": "python -m patchright install chromium",
              "label": "Install Chromium binary (patchright/Playwright distribution)",
            },
          ],
      },
  }
---

# FB Group Scanner Skill

Scan Facebook groups for targeted posts and auto-comment using undetected browser automation.

## ⚠️ Before You Start

**This skill requires Facebook session cookies (treat as a password) and performs automated
actions on Facebook. Use only on accounts and groups you have explicit permission to automate.
May violate Facebook's Terms of Service. You are responsible for compliance.**

- Run in dry-run mode first (`FB_DRY_RUN=true`, the default)
- Use a dedicated/throwaway FB account — never your personal account
- Run in a container or VM, not directly on your host
- `FB_COOKIE_FILE` grants full account access — store with `chmod 600`, never in git

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FB_COOKIE_FILE` | ✅ | Path to Facebook cookies JSON (Selenium format). Secret — treat as password. |
| `FB_STATE_FILE` | ✅ | Writable path for Playwright storage state (default: `/tmp/fb_state.json`) |
| `FB_DRY_RUN` | — | `true` (default) = scan only. `false` = live commenting enabled. |
| `FB_USER_AGENT` | Optional | Override browser user agent |
| `NOTIFY_WEBHOOK` | Optional | Webhook URL for match alerts. Skill skips notifications if unset. |

## Install

```bash
pip install -r scripts/requirements.txt
python -m patchright install chromium
```

Source: `patchright` from PyPI; Chromium binary from the Playwright/patchright official distribution.

## How to Get Cookies

1. Log in to Facebook in real Chrome (manually, once, on a dedicated account)
2. Export all `facebook.com` cookies as JSON via EditThisCookie or DevTools
3. `chmod 600 /path/to/cookies.json` → set `FB_COOKIE_FILE` to that path

Cookies last ~30–90 days. Re-export manually when expired — no automated re-login is included.

## Architecture

```
Patchright browser (stealth Chromium — patches navigator.webdriver + CDP detection)
  └─ Cookie auth (no login form)
       └─ Navigate group feed → intercept GraphQL responses passively
            └─ Filter posts: trigger phrase + topic keyword − exclusions
                 └─ FB_DRY_RUN=true → log match
                    FB_DRY_RUN=false → comment + screenshot + webhook notify
```

## 1. Session (scripts/fb_session.py)

```python
from fb_session import create_session
pw, browser, ctx, page = await create_session()
# Reads FB_COOKIE_FILE + FB_STATE_FILE from env
# Raises RuntimeError if cookies are stale — re-export from real browser
```

## 2. GraphQL Interception

```python
responses = []
async def capture(r):
    if "graphql" in r.url and r.status == 200:
        try: responses.append(await r.json())
        except: pass
page.on("response", capture)
await page.goto(group_url)
await asyncio.sleep(5)
```

See `references/graphql-patterns.md` for walking the response tree.

## 3. Human-Like Behavior (scripts/human_mouse.py)

- `human_scroll(page)` — variable-speed wheel ticks
- `human_click(page, x, y)` — bezier curve path + hover pause
- `human_type(page, text)` — variable WPM + typos + corrections
- `idle_mouse_drift(page)` — aimless drift while "reading"
- `reading_pause(min_s, max_s)` — random pre-action sleep

Timing: wait 3–8s after load, 50–120s between groups.

## 4. User Controls (implement before enabling)

```python
import os, re

# Default to safe/dry mode
DRY_RUN = os.environ.get("FB_DRY_RUN", "true").lower() == "true"

# PII redaction before any external send
def redact_pii(text):
    text = re.sub(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', '[EMAIL]', text)
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    return text

# Webhook — only if explicitly configured
NOTIFY_WEBHOOK = os.environ.get("NOTIFY_WEBHOOK", "")
```

## 5. Post Filtering

See `references/filter-logic.md` for the full pipeline:
1. Trigger phrase (hiring signal)
2. Topic keyword (target role)
3. Job title exclusions (headline only)
4. Seeking-work exclusions (service offers)

## 6. Scheduling

```python
import schedule, time, asyncio
schedule.every().hour.at(":00").do(lambda: asyncio.run(scan_bucket("A")))
schedule.every().hour.at(":30").do(lambda: asyncio.run(scan_bucket("B")))
while True:
    schedule.run_pending()
    time.sleep(30)
```

Operate 8am–11pm only. Track seen posts in SQLite to avoid duplicate comments.

## Files

| File | Purpose |
|------|---------|
| `scripts/fb_session.py` | Cookie session factory (env vars only) |
| `scripts/human_mouse.py` | Stealth mouse/scroll/type helpers |
| `scripts/requirements.txt` | Python deps (patchright) |
| `references/graphql-patterns.md` | FB GraphQL response parsing |
| `references/filter-logic.md` | Keyword filter logic + tuning |
