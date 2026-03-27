#!/usr/bin/env python3
"""Configuration management for Vibe Platform API key."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "bitrix24-skill" / "config.json"
BASE_URL = "https://vibecode.bitrix24.tech"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """Read config file, return dict or empty dict on failure."""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def save_config(path: Path, data: dict) -> None:
    """Write config dict to file, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_key(config_file: str | None = None) -> str | None:
    """Return api_key from config or None."""
    path = Path(config_file).expanduser() if config_file else DEFAULT_CONFIG_PATH
    config = load_config(path)
    key = config.get("api_key")
    return key if isinstance(key, str) and key.strip() else None


def persist_key(key: str, config_file: str | None = None) -> Path:
    """Save api_key to config. Returns config path."""
    path = Path(config_file).expanduser() if config_file else DEFAULT_CONFIG_PATH
    config = load_config(path)
    config["api_key"] = key.strip()
    config["base_url"] = BASE_URL
    save_config(path, config)
    return path


def mask_key(key: str) -> str:
    """Mask key: first 10 chars + **** + last 2. E.g. vibe_api_ab****cd."""
    if len(key) <= 12:
        return key[:4] + "****"
    return key[:10] + "****" + key[-2:]


def get_cached_user(config_file: str | None = None) -> dict | None:
    """Return cached {user_id, timezone} or None."""
    path = Path(config_file).expanduser() if config_file else DEFAULT_CONFIG_PATH
    config = load_config(path)
    user_id = config.get("user_id")
    if user_id is not None:
        return {"user_id": user_id, "timezone": config.get("timezone", "")}
    return None


def cache_user_data(user_id: int, timezone: str = "", config_file: str | None = None) -> None:
    """Save user_id and timezone to config."""
    path = Path(config_file).expanduser() if config_file else DEFAULT_CONFIG_PATH
    config = load_config(path)
    config["user_id"] = user_id
    if timezone:
        config["timezone"] = timezone
    save_config(path, config)


def migrate_old_config(config_file: str | None = None) -> bool:
    """Detect old webhook_url config, back up, and remove it. Returns True if migration happened."""
    path = Path(config_file).expanduser() if config_file else DEFAULT_CONFIG_PATH
    config = load_config(path)
    if "webhook_url" not in config:
        return False
    # Back up
    backup = path.with_suffix(".json.bak")
    shutil.copy2(path, backup)
    # Remove old keys
    del config["webhook_url"]
    config.pop("user_id", None)
    config.pop("timezone", None)
    save_config(path, config)
    return True
