"""
Shared Playwright browser management for Content Claw.

Provides a reusable browser context manager and a persistent browser daemon
that scripts connect to via CDP (Chrome DevTools Protocol).

Usage as context manager (single script):
    from scripts.browser import create_browser
    with create_browser(cookie_path="creds/reddit-cookies.json") as page:
        page.goto("https://reddit.com")

Usage with daemon (cross-script, persistent):
    from scripts.browser import connect_to_daemon, ensure_daemon
    ensure_daemon()  # starts daemon if not running
    page = connect_to_daemon(cookie_path="creds/reddit-cookies.json")
"""

import json
import os
import signal
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path


DAEMON_STATE_FILE = Path(__file__).parent.parent / ".browser-daemon.json"
STEALTH_INIT = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
DEFAULT_VIEWPORT = {"width": 1280, "height": 800}
BROWSER_ARGS = ["--disable-blink-features=AutomationControlled", "--no-sandbox"]


def load_cookies(context, cookie_path: str | None):
    """Load cookies into a browser context if path exists."""
    if cookie_path and Path(cookie_path).exists():
        cookies = json.loads(Path(cookie_path).read_text())
        context.add_cookies(cookies)


@contextmanager
def create_browser(cookie_path: str | None = None, headless: bool = True):
    """Context manager that yields a Page with stealth settings and optional cookies.

    Browser is launched on enter and closed on exit.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=BROWSER_ARGS)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport=DEFAULT_VIEWPORT,
            locale="en-US",
        )
        load_cookies(context, cookie_path)
        page = context.new_page()
        page.add_init_script(STEALTH_INIT)
        try:
            yield page
        finally:
            context.close()
            browser.close()


@contextmanager
def create_browser_context(cookie_path: str | None = None, headless: bool = True):
    """Context manager that yields (page, context, browser) for multi-page operations."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=BROWSER_ARGS)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport=DEFAULT_VIEWPORT,
            locale="en-US",
        )
        load_cookies(context, cookie_path)
        page = context.new_page()
        page.add_init_script(STEALTH_INIT)
        try:
            yield page, context, browser
        finally:
            context.close()
            browser.close()


def _find_free_port() -> int:
    """Find a free port for the browser daemon."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def ensure_daemon() -> dict:
    """Start the browser daemon if not running. Returns connection info."""
    if DAEMON_STATE_FILE.exists():
        state = json.loads(DAEMON_STATE_FILE.read_text())
        # Check if process is alive
        try:
            os.kill(state["pid"], 0)
            # Check if CDP endpoint responds
            import httpx
            resp = httpx.get(f"http://localhost:{state['port']}/json/version", timeout=2)
            if resp.status_code == 200:
                return state
        except (OSError, Exception):
            pass
        # Stale state file, clean up
        DAEMON_STATE_FILE.unlink(missing_ok=True)

    # Launch new daemon
    port = _find_free_port()
    proc = subprocess.Popen(
        [
            sys.executable, "-c",
            f"""
import json, signal, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
browser = p.chromium.launch(
    headless=True,
    args={BROWSER_ARGS!r} + ["--remote-debugging-port={port}"],
)

state = {{"pid": __import__("os").getpid(), "port": {port}, "ws_endpoint": browser.contexts[0].pages[0].url if browser.contexts else ""}}
Path("{DAEMON_STATE_FILE}").write_text(json.dumps(state))

def shutdown(sig, frame):
    browser.close()
    p.stop()
    Path("{DAEMON_STATE_FILE}").unlink(missing_ok=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

# Keep alive, auto-shutdown after 30 min idle
while True:
    time.sleep(1800)
    browser.close()
    p.stop()
    Path("{DAEMON_STATE_FILE}").unlink(missing_ok=True)
    sys.exit(0)
"""
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Wait for daemon to be ready
    for _ in range(30):
        if DAEMON_STATE_FILE.exists():
            state = json.loads(DAEMON_STATE_FILE.read_text())
            return state
        time.sleep(0.5)

    raise RuntimeError("Browser daemon failed to start within 15 seconds")


def stop_daemon():
    """Stop the browser daemon if running."""
    if not DAEMON_STATE_FILE.exists():
        return
    state = json.loads(DAEMON_STATE_FILE.read_text())
    try:
        os.kill(state["pid"], signal.SIGTERM)
    except OSError:
        pass
    DAEMON_STATE_FILE.unlink(missing_ok=True)


def connect_to_daemon(cookie_path: str | None = None):
    """Connect to the running browser daemon and return a new page.

    Falls back to create_browser if daemon is not available.
    """
    try:
        state = ensure_daemon()
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        browser = p.chromium.connect_over_cdp(f"http://localhost:{state['port']}")
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport=DEFAULT_VIEWPORT,
            locale="en-US",
        )
        load_cookies(context, cookie_path)
        page = context.new_page()
        page.add_init_script(STEALTH_INIT)
        return page
    except Exception:
        # Fallback to direct browser launch
        return None
