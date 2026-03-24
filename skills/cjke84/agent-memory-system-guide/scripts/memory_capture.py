#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap lightweight memory-capture files in a workspace."
    )
    parser.add_argument(
        "--workspace",
        required=True,
        help="Target workspace directory where memory files should be created.",
    )
    parser.add_argument(
        "--generated-at",
        help="Optional timestamp for the generated memory-capture header.",
    )
    return parser.parse_args()


def read_template(repo_root: Path, name: str) -> str:
    return (repo_root / "templates" / name).read_text(encoding="utf-8")


def ensure_file(path: Path, content: str) -> str:
    if path.exists():
        return "kept"
    path.write_text(content, encoding="utf-8")
    return "created"


def build_capture_content(repo_root: Path, generated_at: str) -> str:
    template = read_template(repo_root, "memory-capture.md").rstrip() + "\n"
    return (
        "# memory-capture.md\n\n"
        f"> Generated at: {generated_at}\n\n"
        f"{template}"
    )


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parents[1]
    generated_at = args.generated_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    session_status = ensure_file(
        workspace / "SESSION-STATE.md",
        read_template(repo_root, "SESSION-STATE.md"),
    )
    buffer_status = ensure_file(
        workspace / "working-buffer.md",
        read_template(repo_root, "working-buffer.md"),
    )

    capture_path = workspace / "memory-capture.md"
    capture_path.write_text(build_capture_content(repo_root, generated_at), encoding="utf-8")

    print(f"SESSION-STATE.md: {session_status}")
    print(f"working-buffer.md: {buffer_status}")
    print("memory-capture.md: refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
