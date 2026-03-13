---
name: giggle-generation-image
description: Supports text-to-image and image-to-image. Use when the user needs to create or generate images. Use cases: (1) Generate from text description, (2) Use reference images, (3) Customize model, aspect ratio, resolution. Triggers: generate image, draw, create image, AI art.
version: "0.0.4"
license: MIT
metadata:
  {
    "openclaw":
      {
        "emoji": "📂",
        "requires": { "bins": ["python3"], "env": ["GIGGLE_API_KEY"] },
        "primaryEnv": "GIGGLE_API_KEY",
      },
  }
---

[简体中文](./SKILL.zh-CN.md) | English

# Giggle Image Generation (Multi-Model)

Generates AI images via giggle.pro's Generation API. Supports multiple models.

**API Key**: Load priority 1) `~/.openclaw/.env` (preferred) 2) System environment variable `GIGGLE_API_KEY`. The script will prompt if not configured.

> **No inline Python**: All commands must be executed via the `exec` tool. **Never** use `python3 << 'EOF'` or heredoc inline code.

## Supported Models

| Model | Description |
|-------|-------------|
| seedream45 | Seedream, realistic and creative |
| midjourney | Midjourney style |
| nano-banana-2 | Nano Banana 2 |
| nano-banana-2-fast | Nano Banana 2 fast |

---

## Execution Flow (Three-Phase Dual-Path)

Image generation typically takes 30–120 seconds. Uses "fast submit + Cron poll + sync fallback" three-phase architecture.

> **Important**: **Never** pass `GIGGLE_API_KEY` in exec's `env` parameter. API Key is read from `~/.openclaw/.env` or system environment.

---

### Phase 1: Submit Task (exec completes in ~10 seconds)

**First send a message to the user**: "Image generation in progress, usually takes 30–120 seconds. Results will be sent automatically."

```bash
# Text-to-image (default seedream45)
python3 scripts/generation_api.py \
  --prompt "description" --aspect-ratio 16:9 \
  --model seedream45 --resolution 2K \
  --no-wait --json

# Text-to-image - Midjourney
python3 scripts/generation_api.py \
  --prompt "description" --model midjourney \
  --aspect-ratio 16:9 --resolution 2K \
  --no-wait --json

# Image-to-image - Reference URL
python3 scripts/generation_api.py \
  --prompt "Convert to oil painting style, keep composition" \
  --reference-images "https://example.com/photo.jpg" \
  --model nano-banana-2-fast \
  --no-wait --json

# Batch generate multiple images
python3 scripts/generation_api.py \
  --prompt "description" --generate-count 4 \
  --no-wait --json
```

Response example:
```json
{"status": "started", "task_id": "xxx"}
```

**Immediately store task_id in memory** (`addMemory`):
```
giggle-generation-image task_id: xxx (submitted: YYYY-MM-DD HH:mm)
```

---

### Phase 2: Register Cron (45 second interval)

Use the `cron` tool to register the polling job. **Strictly follow the parameter format**:

```json
{
  "action": "add",
  "job": {
    "name": "giggle-generation-image-<first 8 chars of task_id>",
    "schedule": {
      "kind": "every",
      "everyMs": 45000
    },
    "payload": {
      "kind": "systemEvent",
      "text": "Image task poll: exec python3 scripts/generation_api.py --query --task-id <full task_id>, handle stdout per Cron logic. If stdout is non-JSON plain text, forward to user and remove Cron. If stdout is JSON, do not send message, keep waiting. If stdout is empty, remove Cron immediately."
    },
    "sessionTarget": "main"
  }
}
```

**Cron trigger handling** (based on exec stdout):

| stdout pattern | Action |
|----------------|--------|
| Non-empty plain text (not starting with `{`) | **Forward to user as-is**, **remove Cron** |
| stdout empty | Already pushed, **remove Cron immediately, do not send message** |
| JSON (starts with `{`, has `"status"` field) | Do not send message, do not remove Cron, keep waiting |

---

### Phase 3: Sync Wait (optimistic path, fallback when Cron hasn't fired)

**Execute this step whether or not Cron registration succeeded.**

```bash
python3 scripts/generation_api.py --query --task-id <task_id> --poll --max-wait 180
```

**Handling logic**:

- Returns plain text (image ready/failed message) → **Forward to user as-is**, remove Cron
- stdout empty → Cron already pushed, remove Cron, do not send message
- exec timeout → Cron continues polling

---

## New Request vs Query Old Task

**When the user initiates a new image generation request**, **must run Phase 1 to submit a new task**. Do not reuse old task_id from memory.

**Only when the user explicitly asks about a previous task's progress** should you query the old task_id from memory.

---

## Parameter Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--prompt` | required | Image description prompt |
| `--model` | seedream45 | seedream45, midjourney, nano-banana-2, nano-banana-2-fast |
| `--aspect-ratio` | 16:9 | 16:9, 9:16, 1:1, 3:4, 4:3, 2:3, 3:2, 21:9 |
| `--resolution` | 2K | Text-to-image: 1K, 2K, 4K (image-to-image partially supported) |
| `--generate-count` | 1 | Number of images to generate |
| `--reference-images` | - | Image-to-image reference; supports URL, base64, asset_id |
| `--watermark` | false | Add watermark (image-to-image) |

---

## Image-to-Image Reference: Three Input Methods

The image-to-image API's `reference_images` is an array of objects. Each element can be one of these three formats (can be mixed):

### Method 1: URL

```json
{
  "prompt": "A cute orange cat sitting on the windowsill in the sun, realistic style",
  "reference_images": [
    {
      "url": "https://assets.ggltest.com/private/test_ai_director/0ebc2ffa7512a58df5/9y91pxl0hju.thumb.jpg?Expires=1772409599000&Key-Pair-Id=K271ZF3SQS38SK&Signature=..."
    }
  ],
  "generate_count": 1,
  "model": "nano-banana-2-fast",
  "aspect_ratio": "16:9",
  "watermark": false
}
```

### Method 2: Base64

```json
{
  "prompt": "A cute orange cat sitting on the windowsill in the sun, realistic style",
  "reference_images": [
    {
      "base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    }
  ],
  "generate_count": 1,
  "model": "nano-banana-2-fast",
  "aspect_ratio": "16:9",
  "watermark": false
}
```

> Base64 format: Pass the raw Base64 string directly. Do not add the `data:image/xxx;base64,` prefix.

### Method 3: asset_id

```json
{
  "prompt": "A cute orange cat sitting on the windowsill in the sun, realistic style",
  "reference_images": [
    {
      "asset_id": "vvsdsfsdf"
    }
  ],
  "generate_count": 1,
  "model": "nano-banana-2-fast",
  "aspect_ratio": "16:9",
  "watermark": false
}
```

> For multiple reference images, add more objects to the `reference_images` array.

---

## Interaction Guide

**When the user request is vague, guide per the steps below. If the user has provided enough info, run the command directly.**

### Step 1: Model Selection

```
Question: "Which model would you like to use?"
Title: "Image Model"
Options:
- "seedream45 - Realistic & creative (recommended)"
- "midjourney - Artistic style"
- "nano-banana-2 - High quality"
- "nano-banana-2-fast - Fast generation"
multiSelect: false
```

### Step 2: Aspect Ratio

```
Question: "What aspect ratio do you need?"
Title: "Aspect Ratio"
Options:
- "16:9 - Landscape (wallpaper/cover) (recommended)"
- "9:16 - Portrait (mobile)"
- "1:1 - Square"
- "Other ratios"
multiSelect: false
```

### Step 3: Generation Mode

```
Question: "Do you need reference images?"
Title: "Generation Mode"
Options:
- "No - Text-to-image only"
- "Yes - Image-to-image (style transfer)"
multiSelect: false
```

### Step 4: Execute and Display

Follow the execution flow: send message → Phase 1 submit → Phase 2 register Cron → Phase 3 sync wait.

When results arrive, forward exec stdout to the user as-is.

**Link return rule**: Image links in results must be **full signed URLs** (with Policy, Key-Pair-Id, Signature query params). Correct: `https://assets.giggle.pro/...?Policy=...&Key-Pair-Id=...&Signature=...`. Wrong: do not return unsigned URLs with only the base path (no query params).
