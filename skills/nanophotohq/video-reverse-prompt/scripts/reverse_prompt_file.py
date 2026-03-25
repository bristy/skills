#!/usr/bin/env python3
import argparse
import base64
import json
import pathlib
import sys
import urllib.error
import urllib.request

API_URL = "https://nanophoto.ai/api/sora-2/reverse-prompt"
MAX_FILE_BYTES = 30 * 1024 * 1024
SUPPORTED_LOCALES = {"en", "zh", "zh-TW", "ja", "ko", "es", "fr", "de", "pt", "ru", "ar"}


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a local MP4 file to NanoPhoto.AI Video Reverse Prompt API.")
    parser.add_argument("video", help="Path to a local .mp4 file")
    parser.add_argument("--api-key", help="NanoPhoto API key. Defaults to NANOPHOTO_API_KEY env var.")
    parser.add_argument("--locale", default="en", help="Output locale (default: en)")
    parser.add_argument("--timeout", type=int, default=1800, help="Request timeout in seconds (default: 1800)")
    args = parser.parse_args()

    api_key = args.api_key or __import__("os").environ.get("NANOPHOTO_API_KEY")
    if not api_key:
        fail("Missing API key. Set NANOPHOTO_API_KEY or pass --api-key.")

    if args.locale not in SUPPORTED_LOCALES:
        fail(f"Unsupported locale: {args.locale}. Supported: {', '.join(sorted(SUPPORTED_LOCALES))}")

    path = pathlib.Path(args.video).expanduser().resolve()
    if not path.exists():
        fail(f"File not found: {path}")
    if path.suffix.lower() != ".mp4":
        fail("Only .mp4 files are supported.")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        fail(f"File too large: {size} bytes (> {MAX_FILE_BYTES} bytes / 30 MB limit)")

    video_base64 = base64.b64encode(path.read_bytes()).decode("ascii")
    payload = {
        "videoSource": "file",
        "locale": args.locale,
        "videoFile": video_base64,
        "videoFileName": path.name,
    }

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            sys.stdout.write(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", "replace")
        fail(f"HTTP {exc.code}: {error_body}")
    except urllib.error.URLError as exc:
        fail(f"Request failed: {exc}")


if __name__ == "__main__":
    main()
