"""
fb_session.py — Patchright browser session with cookie-based FB auth.

Required environment variables (set before running):
    FB_COOKIE_FILE   - Path to exported FB cookies JSON (Selenium/Puppeteer format)
    FB_STATE_FILE    - Path to write converted Playwright storage state JSON
                       (default: /tmp/fb_state.json)

Optional:
    FB_USER_AGENT    - Override browser user agent string
"""

import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

# ── Config from environment ──────────────────────────────────────────────────
COOKIE_FILE = os.environ.get("FB_COOKIE_FILE", "")
STATE_FILE  = os.environ.get("FB_STATE_FILE", "/tmp/fb_state.json")
USER_AGENT  = os.environ.get(
    "FB_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def load_cookies_as_playwright_state() -> dict:
    """
    Convert Selenium/Puppeteer cookie format → Playwright storage state.
    Reads FB_COOKIE_FILE, writes FB_STATE_FILE, returns the state dict.
    """
    if not COOKIE_FILE:
        raise EnvironmentError("FB_COOKIE_FILE environment variable is not set")
    if not os.path.exists(COOKIE_FILE):
        raise FileNotFoundError(f"Cookie file not found: {COOKIE_FILE}")

    with open(COOKIE_FILE) as f:
        cookies = json.load(f)

    pw_cookies = []
    for c in cookies:
        pc = {
            "name":     c.get("name", ""),
            "value":    c.get("value", ""),
            "domain":   c.get("domain", ".facebook.com"),
            "path":     c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure":   c.get("secure", False),
        }
        if "expiry" in c:
            pc["expires"] = c["expiry"]
        elif "expires" in c and isinstance(c["expires"], (int, float)) and c["expires"] > 0:
            pc["expires"] = c["expires"]
        pw_cookies.append(pc)

    state = {"cookies": pw_cookies, "origins": []}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

    c_user = next((c["value"] for c in cookies if c["name"] == "c_user"), None)
    logger.info(f"Loaded {len(cookies)} cookies (c_user={c_user})")
    return state


async def verify_login(page) -> bool:
    """Return True if the current browser session has a valid FB c_user cookie."""
    try:
        await page.goto("https://www.facebook.com/", timeout=30000)
        await asyncio.sleep(3)
        cookies = await page.context.cookies()
        c_user = next((c["value"] for c in cookies if c["name"] == "c_user"), None)
        if c_user:
            logger.info(f"Session valid (c_user={c_user})")
            return True
        logger.warning("Session invalid — c_user cookie missing")
        return False
    except Exception as e:
        logger.error(f"Login check failed: {e}")
        return False


async def create_session():
    """
    Create and return (playwright, browser, context, page) with valid FB session.

    Raises RuntimeError if cookies are stale/missing — caller must re-export
    cookies from a real browser session and update FB_COOKIE_FILE.

    Returns:
        tuple: (pw, browser, ctx, page)
    """
    from patchright.async_api import async_playwright

    load_cookies_as_playwright_state()

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ]
    )
    ctx = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        user_agent=USER_AGENT,
    )

    with open(STATE_FILE) as f:
        state = json.load(f)
    await ctx.add_cookies(state["cookies"])

    page = await ctx.new_page()

    if not await verify_login(page):
        await browser.close()
        await pw.stop()
        raise RuntimeError(
            "FB session invalid — cookies are stale or missing. "
            "Export fresh cookies from a real browser session, "
            "save to FB_COOKIE_FILE, and retry."
        )

    return pw, browser, ctx, page
