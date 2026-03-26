---
name: fotor-openapi-sdk
description: >-
  Generate images and videos via Fotor OpenAPI using a standalone Python SDK.
  Supports Text-to-Image, Image-to-Image, Text-to-Video, Image-to-Video,
  Start/End Frame Interpolation, Multi-Image Video, Image Upscale, and
  Background Removal. Handles parallel batch execution and task status
  monitoring. Use when user requests AI image generation, video generation,
  image upscaling, background removal, or batch media production. Only
  requires FOTOR_OPENAPI_KEY.
---

# Fotor OpenAPI SDK

Async-first Python SDK for the Fotor OpenAPI. No MCP, no S3 -- just an API key.

## Setup

1. **Ensure SDK installed** (run once, skipped if already present):
   ```bash
   python scripts/ensure_sdk.py
   ```
2. **Ensure `FOTOR_OPENAPI_KEY`** is set in environment.

## Scripts

### `scripts/ensure_sdk.py`

Cross-platform (Windows / macOS / Linux) script to check and install `fotor-sdk` from PyPI. Run before any task. Outputs JSON with `status` and `version`.

- **No args** — install only if missing (fast, no network if already installed)
- **`--upgrade`** — upgrade to latest PyPI version

### `scripts/run_task.py`

Execute one or more Fotor tasks from JSON. Handles client init, polling, and progress.

**Single task:**
```bash
echo '{"task_type":"text2image","params":{"prompt":"A cat","model_id":"seedream-4-5-251128"}}' \
  | python scripts/run_task.py
```

**Batch (array):**
```bash
echo '[
  {"task_type":"text2image","params":{"prompt":"A cat","model_id":"seedream-4-5-251128"},"tag":"cat"},
  {"task_type":"text2video","params":{"prompt":"Sunset","model_id":"kling-v3","duration":5},"tag":"sunset"}
]' | python scripts/run_task.py --concurrency 5
```

**Options:** `--input FILE`, `--concurrency N` (default 5), `--poll-interval S` (default 2.0), `--timeout S` (default 1200).

**Output:** JSON with `task_id`, `status`, `success`, `result_url`, `error`, `elapsed_seconds`, `tag`.

## Reference Files

Read these before selecting a model or constructing parameters:

- `references/image_models.md` -- image model IDs, T2I/I2I capabilities, resolution/ratio support
- `references/video_models.md` -- video model IDs, T2V/I2V/SE/MI capabilities, duration, audio
- `references/parameter_reference.md` -- full function signatures and parameter tables for all 8 task types

## Workflow

1. Run `python scripts/ensure_sdk.py` to confirm SDK availability.
2. Verify `FOTOR_OPENAPI_KEY` is set.
3. Read the appropriate model reference to choose `model_id`.
4. **Quick path** -- pipe JSON into `scripts/run_task.py` (works for both single and batch).
5. **Custom path** -- write inline Python using the SDK directly (see examples below).
6. Check `result_url` in output. Chain `image_upscale` if higher resolution needed.

## Available Task Types

| task_type | Function | Required Params |
|-----------|----------|-----------------|
| `text2image` | `text2image()` | `prompt`, `model_id` |
| `image2image` | `image2image()` | `prompt`, `model_id`, `image_urls` |
| `image_upscale` | `image_upscale()` | `image_url` |
| `background_remove` | `background_remove()` | `image_url` |
| `text2video` | `text2video()` | `prompt`, `model_id` |
| `single_image2video` | `single_image2video()` | `prompt`, `model_id`, `image_url` |
| `start_end_frame2video` | `start_end_frame2video()` | `prompt`, `model_id`, `start_image_url`, `end_image_url` |
| `multiple_image2video` | `multiple_image2video()` | `prompt`, `model_id`, `image_urls` (≥2) |

For full parameter details (defaults, `on_poll`, `**extra`), read `references/parameter_reference.md`.

## Inline Python Examples

When `scripts/run_task.py` is insufficient (custom logic, chaining, progress callbacks):

### Client Init

```python
import os
from fotor_sdk import FotorClient
client = FotorClient(api_key=os.environ["FOTOR_OPENAPI_KEY"])
```

### Single Task

```python
from fotor_sdk import text2image
result = await text2image(client, prompt="A diamond kitten", model_id="seedream-4-5-251128")
print(result.result_url)
```

### Batch with TaskRunner

```python
from fotor_sdk import TaskRunner, TaskSpec
runner = TaskRunner(client, max_concurrent=5)
specs = [
    TaskSpec("text2image", {"prompt": "A cat", "model_id": "seedream-4-5-251128"}, tag="cat"),
    TaskSpec("text2video", {"prompt": "Sunset", "model_id": "kling-v3", "duration": 5}, tag="sunset"),
]
results = await runner.run(specs)
```

### Video with Audio

```python
from fotor_sdk import text2video
result = await text2video(client, prompt="Jazz band", model_id="kling-v3",
                          audio_enable=True, audio_prompt="Smooth jazz")
```

## TaskResult

```python
result.success          # bool: True when COMPLETED with result_url
result.result_url       # str | None
result.status           # TaskStatus: COMPLETED / FAILED / TIMEOUT / IN_PROGRESS / CANCELLED
result.error            # str | None (e.g. "NSFW_CONTENT")
result.elapsed_seconds  # float
result.metadata         # dict (includes "tag" from TaskRunner)
```

## Error Handling

- **Single task**: catch `FotorAPIError` (has `.code` attribute).
- **Batch**: check `result.success` per item; runner never raises on individual failures.
- **NSFW**: appears as `error="NSFW_CONTENT"` in TaskResult.

## SDK Internals (debugging)

| Task | API Path |
|------|----------|
| Image generation | `/v1/aiart/imagegeneration/{model_id}` |
| Image upscale | `/v1/aiart/imgupscale` |
| Background removal | `/v1/aiart/backgroundremover` |
| Text-to-video | `/v1/aiart/text2video/{model_id}` |
| Image-to-video | `/v1/aiart/img2video/{model_id}` |
| Start/end frame | `/v1/aiart/startend2video/{model_id}` |
| Multi-image video | `/v1/aiart/character2video/{model_id}` |
| Task status | `/v1/aiart/tasks/{task_id}` |

Image sizes auto-calculated from `aspect_ratio` + `resolution` (see `references/parameter_reference.md`).

Enable debug logging: `logging.getLogger("fotor_sdk").setLevel(logging.DEBUG)`
