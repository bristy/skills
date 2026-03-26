#!/usr/bin/env python3
"""Run one or more Fotor tasks from a JSON spec on stdin or file.

Single task:
  echo '{"task_type":"text2image","params":{"prompt":"A cat","model_id":"seedream-4-5-251128"}}' | python scripts/run_task.py

Batch (array of specs):
  echo '[{"task_type":"text2image","params":{"prompt":"A cat","model_id":"seedream-4-5-251128"},"tag":"cat"},
        {"task_type":"text2video","params":{"prompt":"Sunset","model_id":"kling-v3"},"tag":"sunset"}]' | python scripts/run_task.py

Options:
  --input FILE       Read specs from FILE instead of stdin
  --concurrency N    Max parallel tasks (default: 5)
  --poll-interval S  Seconds between polls (default: 2.0)
  --timeout S        Max polling seconds (default: 1200)

Output: JSON array of results, one per task.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from fotor_sdk import (
    FotorClient,
    TaskRunner,
    TaskSpec,
    TaskResult,
    TaskStatus,
    FotorAPIError,
    text2image,
    image2image,
    image_upscale,
    background_remove,
    text2video,
    single_image2video,
    start_end_frame2video,
    multiple_image2video,
)

_TASK_FN = {
    "text2image": text2image,
    "image2image": image2image,
    "image_upscale": image_upscale,
    "background_remove": background_remove,
    "text2video": text2video,
    "single_image2video": single_image2video,
    "start_end_frame2video": start_end_frame2video,
    "multiple_image2video": multiple_image2video,
}


def _result_to_dict(r: TaskResult) -> dict:
    return {
        "task_id": r.task_id,
        "status": r.status.name,
        "success": r.success,
        "result_url": r.result_url,
        "error": r.error,
        "elapsed_seconds": round(r.elapsed_seconds, 2),
        "tag": r.metadata.get("tag", ""),
    }


async def _run_single(client: FotorClient, spec: dict) -> dict:
    task_type = spec.get("task_type", "")
    params = spec.get("params", {})
    fn = _TASK_FN.get(task_type)
    if fn is None:
        return {"task_id": "", "status": "FAILED", "success": False,
                "error": f"Unknown task_type: {task_type}", "result_url": None,
                "elapsed_seconds": 0, "tag": spec.get("tag", "")}
    try:
        result = await fn(client, **params)
        d = _result_to_dict(result)
        d["tag"] = spec.get("tag", "")
        return d
    except FotorAPIError as e:
        return {"task_id": "", "status": "FAILED", "success": False,
                "error": f"{e} (code={e.code})", "result_url": None,
                "elapsed_seconds": 0, "tag": spec.get("tag", "")}


async def _run_batch(client: FotorClient, specs: list[dict], concurrency: int) -> list[dict]:
    runner = TaskRunner(client, max_concurrent=concurrency)
    task_specs = [
        TaskSpec(
            task_type=s.get("task_type", ""),
            params=s.get("params", {}),
            tag=s.get("tag", ""),
        )
        for s in specs
    ]

    def _progress(total, completed, failed, in_progress, latest):
        tag = latest.metadata.get("tag", latest.task_id)
        status = "OK" if latest.success else latest.status.name
        print(f"[{completed+failed}/{total}] {tag} -> {status}", file=sys.stderr)

    results = await runner.run(task_specs, on_progress=_progress)
    return [_result_to_dict(r) for r in results]


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run Fotor tasks from JSON")
    parser.add_argument("--input", help="JSON file path (default: stdin)")
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=1200)
    args = parser.parse_args()

    api_key = os.environ.get("FOTOR_OPENAPI_KEY", "")
    if not api_key:
        print(json.dumps({"error": "FOTOR_OPENAPI_KEY not set"}), file=sys.stderr)
        return 1

    client = FotorClient(
        api_key=api_key,
        endpoint=os.environ.get("FOTOR_OPENAPI_ENDPOINT", "https://api.fotor.com"),
        poll_interval=args.poll_interval,
        max_poll_seconds=args.timeout,
    )

    raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
    data = json.loads(raw.strip())

    if isinstance(data, dict):
        result = await _run_single(client, data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif isinstance(data, list):
        results = await _run_batch(client, data, args.concurrency)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "Input must be a JSON object or array"}), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
