"""
human_mouse.py — Human-like mouse movements, scrolling, and typing helpers.

Uses bezier curves with gaussian jitter to simulate natural hand movement.
All delays are randomized to avoid detectable patterns.
"""

import asyncio
import random
import math


def _bezier_points(x0, y0, x1, y1, steps=25):
    """
    Generate bezier curve points between two coordinates with a random control point.
    This mimics the curved, slightly-wobbly path of a real mouse.
    """
    # Random control point offset (makes the curve arc naturally)
    cx = (x0 + x1) / 2 + random.uniform(-80, 80)
    cy = (y0 + y1) / 2 + random.uniform(-60, 60)

    points = []
    for i in range(steps + 1):
        t = i / steps
        # Quadratic bezier formula
        px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1
        py = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1
        # Add small gaussian jitter (hand tremor)
        px += random.gauss(0, 0.8)
        py += random.gauss(0, 0.8)
        points.append((px, py))

    return points


def _step_delay(distance: float) -> float:
    """
    Calculate per-step delay based on Fitts's Law approximation.
    Faster over long distances, slower near the target.
    """
    base = random.uniform(0.004, 0.009)
    if distance < 50:
        return base * 2.5   # Slow down near target
    elif distance > 400:
        return base * 0.6   # Speed up for long moves
    return base


async def move_to(page, x: float, y: float, current_x: float = None, current_y: float = None):
    """Move mouse from current position to (x, y) via a bezier curve."""
    if current_x is None or current_y is None:
        # Start from a plausible position if unknown
        current_x = random.uniform(300, 800)
        current_y = random.uniform(200, 600)

    distance = math.hypot(x - current_x, y - current_y)
    steps = max(15, min(40, int(distance / 12)))
    points = _bezier_points(current_x, current_y, x, y, steps=steps)
    delay = _step_delay(distance)

    for px, py in points:
        await page.mouse.move(px, py)
        await asyncio.sleep(delay + random.gauss(0, delay * 0.3))


async def human_click(page, x: float, y: float, current_x: float = None, current_y: float = None,
                      button: str = "left", pre_hover_ms: float = None):
    """
    Move to target and click like a human:
    1. Bezier curve movement
    2. Slight hover pause
    3. Down + short hold + Up
    """
    await move_to(page, x, y, current_x, current_y)

    # Pause before clicking (human reaction time)
    hover_ms = pre_hover_ms if pre_hover_ms else random.uniform(0.08, 0.25)
    await asyncio.sleep(hover_ms)

    # Mouse down, micro-hold, mouse up (simulate finger press)
    await page.mouse.down(button=button)
    await asyncio.sleep(random.uniform(0.05, 0.18))
    await page.mouse.up(button=button)

    return x, y  # Return for chaining as "current position"


async def human_click_element(page, locator, jitter: float = 4.0):
    """
    Click a Playwright locator with human-like behavior.
    Aims slightly off-center (like a real person).
    """
    box = await locator.bounding_box()
    if not box:
        await locator.click()
        return

    # Click slightly off-center with jitter
    x = box['x'] + box['width'] * random.uniform(0.35, 0.65) + random.gauss(0, jitter)
    y = box['y'] + box['height'] * random.uniform(0.35, 0.65) + random.gauss(0, jitter)

    # Clamp to element bounds
    x = max(box['x'] + 2, min(box['x'] + box['width'] - 2, x))
    y = max(box['y'] + 2, min(box['y'] + box['height'] - 2, y))

    await human_click(page, x, y)


async def human_scroll(page, target_y: float = None, direction: str = "down",
                       min_px: int = 200, max_px: int = 600):
    """
    Scroll like a human: variable-speed wheel events with micro-pauses.
    Uses multiple small wheel ticks instead of one big jump.
    """
    total = random.randint(min_px, max_px) * (1 if direction == "down" else -1)
    ticks = random.randint(4, 10)
    per_tick = total / ticks

    # Move mouse to random area of viewport before scrolling (like a real user)
    scroll_x = random.uniform(300, 900)
    scroll_y = random.uniform(200, 600)
    await page.mouse.move(scroll_x + random.gauss(0, 20), scroll_y + random.gauss(0, 20))

    for i in range(ticks):
        tick_amount = per_tick * random.uniform(0.7, 1.3)
        await page.mouse.wheel(0, tick_amount)
        await asyncio.sleep(random.uniform(0.04, 0.14))

    await asyncio.sleep(random.uniform(0.3, 1.2))


async def human_scroll_to(page, target_scroll_y: int):
    """Scroll to approximate Y position using incremental human-like scrolling."""
    current = await page.evaluate("window.scrollY")
    diff = target_scroll_y - current

    if abs(diff) < 50:
        return

    direction = "down" if diff > 0 else "up"
    steps = random.randint(3, 7)
    step_size = abs(diff) / steps

    for _ in range(steps):
        px = int(step_size * random.uniform(0.7, 1.3))
        await human_scroll(page, direction=direction, min_px=px, max_px=px + 40)


async def idle_mouse_drift(page, duration: float = 2.0):
    """
    Move the mouse aimlessly for a bit — like a user reading before acting.
    """
    x = random.uniform(300, 900)
    y = random.uniform(200, 500)
    end_time = asyncio.get_event_loop().time() + duration

    while asyncio.get_event_loop().time() < end_time:
        nx = x + random.gauss(0, 30)
        ny = y + random.gauss(0, 20)
        nx = max(100, min(1100, nx))
        ny = max(100, min(700, ny))
        await move_to(page, nx, ny, x, y)
        x, y = nx, ny
        await asyncio.sleep(random.uniform(0.15, 0.5))


async def human_type(page, text: str, wpm_range: tuple = (55, 90),
                     typo_rate: float = 0.015):
    """
    Type text with human-like variable speed, micro-pauses, and occasional typos.

    Args:
        wpm_range: Min/max words per minute
        typo_rate: Probability of a typo per character (followed by backspace correction)
    """
    wpm = random.uniform(*wpm_range)
    base_delay = 60 / (wpm * 5)  # avg delay per character

    for i, char in enumerate(text):
        # Occasional typo
        if char.isalpha() and random.random() < typo_rate:
            # Type a nearby wrong key and immediately correct it
            wrong = random.choice('qwertyuiopasdfghjklzxcvbnm')
            await page.keyboard.type(wrong)
            await asyncio.sleep(random.uniform(0.08, 0.2))
            await page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.05, 0.15))

        # Type the real character
        await page.keyboard.type(char)

        # Variable delay: slower at start of words, faster in bursts
        delay = base_delay * random.lognormvariate(0, 0.4)
        delay = max(0.025, min(0.35, delay))

        # Occasional longer pause (thinking, shifting hands)
        if random.random() < 0.04:
            delay += random.uniform(0.3, 1.2)

        # Slightly longer after punctuation or spaces
        if char in ' ,.!?':
            delay += random.uniform(0.05, 0.18)

        await asyncio.sleep(delay)


async def reading_pause(min_s: float = 1.5, max_s: float = 5.0):
    """Pause like a human reading before taking action."""
    await asyncio.sleep(random.uniform(min_s, max_s))


async def pre_action_hesitate(page=None):
    """Short pre-action hesitation — human tendency to pause before clicking."""
    if page and random.random() < 0.4:
        await idle_mouse_drift(page, duration=random.uniform(0.5, 1.5))
    await asyncio.sleep(random.uniform(0.1, 0.5))
