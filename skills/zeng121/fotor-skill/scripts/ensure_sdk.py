#!/usr/bin/env python3
"""Ensure fotor-sdk is installed, optionally upgrade to latest.

Usage:
    python scripts/ensure_sdk.py              # install only if missing
    python scripts/ensure_sdk.py --upgrade    # upgrade to latest PyPI version

Works on Windows, macOS, and Linux.
"""

import json
import subprocess
import sys


def _pip_install(*args: str) -> None:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", *args],
        stdout=sys.stderr,
        stderr=sys.stderr,
    )


def _sdk_version() -> str:
    return subprocess.check_output(
        [sys.executable, "-c", "import fotor_sdk; print(fotor_sdk.__version__)"],
        text=True,
    ).strip()


def main() -> None:
    upgrade = "--upgrade" in sys.argv

    if upgrade:
        print("Upgrading fotor-sdk from PyPI...", file=sys.stderr)
        _pip_install("--upgrade", "fotor-sdk")
        print(json.dumps({"status": "upgraded", "version": _sdk_version()}))
        return

    try:
        ver = _sdk_version()
        print(json.dumps({"status": "already_installed", "version": ver}))
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("fotor_sdk not found, installing from PyPI...", file=sys.stderr)
        _pip_install("fotor-sdk")
        print(json.dumps({"status": "installed", "version": _sdk_version()}))


if __name__ == "__main__":
    main()
