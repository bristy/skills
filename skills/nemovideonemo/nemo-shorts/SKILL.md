---
name: nemo-shorts
author: nemovideonemo
description: >
  Use NemoShorts — the AI short video maker — immediately whenever the user mentions: make TikTok, TikTok video maker, create Reels, Instagram Reels, YouTube Shorts, short video, vertical video, 9:16 crop, crop to vertical, portrait mode video, repurpose video, repurpose long video into shorts, convert video to TikTok, clip video, short clip, video clip maker, add captions TikTok, mobile video, short form video, video repurposing, highlight clips.
  NemoShorts transforms footage into platform-ready vertical content: smart crop to 9:16, trim to 15s/30s/60s, auto-generate and burn mobile-optimized captions, add BGM with auto-ducking, apply TikTok-style text overlays, export with platform-specific encoding for TikTok / Instagram Reels / YouTube Shorts. Powered by NemoVideo AI.
metadata:
  openclaw:
    emoji: 📱
---

# NemoShorts Skill

An AI agent skill for creating short-form vertical videos optimized for TikTok, Instagram Reels, and YouTube Shorts. Powered by the NemoVideo API.

## Description

Use NemoShorts when the user wants to **create short videos**, **make TikTok videos**, **make Reels**, **make YouTube Shorts**, **crop video to vertical**, **repurpose long video into clips**, or **convert 16:9 to 9:16**. Powered by NemoVideo AI.

NemoShorts transforms existing footage into platform-ready short-form vertical content: smart crop to 9:16, trim to optimal length, auto-generate and burn mobile-optimized captions, overlay background music with auto-ducking, apply TikTok-style text overlays, and export in the exact encoding each platform requires.

**Trigger phrases:** make TikTok, TikTok video maker, create Reels, Instagram Reels, YouTube Shorts, short video, vertical video, 9:16 crop, crop to vertical, portrait mode video, repurpose video, repurpose long video into shorts, convert video to TikTok, clip video, short clip, video clip maker, add captions TikTok, mobile video, short form video, video repurposing tool, content repurposing, highlight clips, trim video, auto caption short video

**Primary use cases:**
- Crop horizontal (16:9) video to vertical (9:16) for TikTok / Reels / Shorts — smart auto-reframe
- Trim long video into 15s / 30s / 60s segments with intelligent cut point detection
- Auto-generate and burn mobile-optimized captions (large font, center screen)
- Add background music (BGM) with automatic volume ducking
- Repurpose YouTube/podcast/stream/long-form video into multiple short clips
- Apply text overlays: hook text, CTA banners, hashtag overlays
- Export with platform-specific encoding (TikTok MP4, Instagram Reels, YouTube Shorts)

**Not for:** generating video from text/scripts (see nemo-video), subtitle-only workflows (see nemo-subtitle), or professional broadcast production.

---

## Setup

**Base URL:** `https://mega-api-dev.nemovideo.ai`

All requests require:
```
Authorization: Bearer <NEMOVIDEO_API_KEY>
Content-Type: application/json
```

Set `NEMOVIDEO_API_KEY` in your environment or OpenClaw secrets.

---

## Workflow Overview

```
Upload video → Configure short (crop + trim + captions + BGM + text) → Start job
→ Poll status → Download vertical MP4
```

All processing is async. Always poll job status before delivering output.

---

## API Reference

### 1. Upload Media

```http
POST /v1/upload
Content-Type: multipart/form-data

file=<binary>
```

**Response:**
```json
{
  "file_id": "f_xyz789",
  "filename": "podcast-ep42.mp4",
  "duration_seconds": 3612,
  "width": 1920,
  "height": 1080,
  "size_bytes": 820000000
}
```

Use `file_id` in all subsequent requests.

---

### 2. Create Short Clip

The primary endpoint. Combines crop, trim, captions, BGM, and text overlays in a single job.

```http
POST /v1/shorts/create
Content-Type: application/json

{
  "file_id": "f_xyz789",
  "trim": {
    "start_seconds": 120,
    "end_seconds": 150
  },
  "crop": {
    "preset": "9:16",
    "focus": "center"
  },
  "captions": {
    "enabled": true,
    "language": "auto",
    "style": "tiktok"
  },
  "bgm": {
    "enabled": false
  },
  "export": {
    "platform": "tiktok",
    "quality": "high"
  }
}
```

**Full parameters:**

#### `trim` (optional)
| Parameter | Type | Description |
|-----------|------|-------------|
| `start_seconds` | float | Start time in source video (default: 0) |
| `end_seconds` | float | End time in source video (default: end of file) |
| `max_duration_seconds` | int | Hard cap on output duration (15, 30, 60, 90, 180) |

#### `crop` (required)
| Parameter | Type | Description |
|-----------|------|-------------|
| `preset` | string | Aspect ratio: `"9:16"` (vertical), `"1:1"` (square), `"4:5"` (Instagram portrait), `"16:9"` (landscape, pass-through) |
| `focus` | string | Crop anchor: `"center"`, `"face"` (AI face-tracking), `"left"`, `"right"`, `"custom"` |
| `custom_x` | float | Custom crop center X (0.0–1.0), used when `focus: "custom"` |
| `custom_y` | float | Custom crop center Y (0.0–1.0), used when `focus: "custom"` |

#### `captions` (optional)
| Parameter | Type | Description |
|-----------|------|-------------|
| `enabled` | bool | Enable auto-caption generation (default: false) |
| `language` | string | Source language or `"auto"` |
| `style` | string | Caption style preset: `"tiktok"` (large, centered, bold), `"minimal"` (small, bottom), `"karaoke"` (word-highlight), `"none"` |
| `translate_to` | string | Optional: translate captions to this language before burning (e.g. `"zh"`, `"es"`) |
| `font_size` | int | Override font size (pixels) |
| `color` | string | Text color hex (e.g. `"#FFFFFF"`) |
| `highlight_color` | string | Active word highlight color for karaoke style (e.g. `"#FFFF00"`) |

#### `bgm` (optional)
| Parameter | Type | Description |
|-----------|------|-------------|
| `enabled` | bool | Add background music (default: false) |
| `track_id` | string | BGM track ID from the track library (see `/v1/bgm/tracks`) |
| `file_id` | string | Use uploaded audio file as BGM (alternative to `track_id`) |
| `volume` | float | BGM volume relative to original audio (0.0–1.0, default: 0.3) |
| `duck_original` | bool | Auto-lower original audio when speech detected (default: true) |
| `fade_in_seconds` | float | BGM fade-in duration (default: 1.0) |
| `fade_out_seconds` | float | BGM fade-out duration (default: 1.5) |

#### `text_overlays` (optional, array)
| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text content |
| `position` | string | `"top"`, `"center"`, `"bottom"` |
| `style` | string | `"hook"` (big bold headline), `"cta"` (call-to-action), `"hashtag"` (small bottom tags), `"custom"` |
| `start_seconds` | float | When to show text (relative to output) |
| `end_seconds` | float | When to hide text |
| `font_size` | int | Font size override |
| `color` | string | Text color hex |
| `background_box` | bool | Add background box (default: false) |

#### `export` (required)
| Parameter | Type | Description |
|-----------|------|-------------|
| `platform` | string | `"tiktok"`, `"instagram"`, `"youtube_shorts"`, `"generic"` |
| `quality` | string | `"high"` (recommended), `"medium"`, `"low"` |

**Platform presets:**

| Platform | Resolution | FPS | Max Duration | Bitrate |
|----------|-----------|-----|--------------|---------|
| `tiktok` | 1080×1920 | 30 | 60s (warning if longer) | 8Mbps |
| `instagram` | 1080×1920 | 30 | 90s | 8Mbps |
| `youtube_shorts` | 1080×1920 | 60 | 60s | 10Mbps |
| `generic` | 1080×1920 | 30 | none | 8Mbps |

**Response:**
```json
{
  "job_id": "job_short_112",
  "status": "queued",
  "estimated_seconds": 75
}
```

---

### 3. Batch Create Shorts (Multiple Clips)

Create multiple short clips from one source video in a single request.

```http
POST /v1/shorts/batch
Content-Type: application/json

{
  "file_id": "f_xyz789",
  "clips": [
    {
      "trim": { "start_seconds": 120, "end_seconds": 150 },
      "crop": { "preset": "9:16", "focus": "center" },
      "captions": { "enabled": true, "language": "auto", "style": "tiktok" },
      "export": { "platform": "tiktok", "quality": "high" }
    },
    {
      "trim": { "start_seconds": 600, "end_seconds": 660 },
      "crop": { "preset": "9:16", "focus": "face" },
      "captions": { "enabled": true, "language": "auto", "style": "tiktok" },
      "export": { "platform": "instagram", "quality": "high" }
    }
  ]
}
```

**Response:**
```json
{
  "batch_id": "batch_445",
  "jobs": [
    { "job_id": "job_short_113", "clip_index": 0, "status": "queued" },
    { "job_id": "job_short_114", "clip_index": 1, "status": "queued" }
  ]
}
```

Poll each `job_id` individually.

---

### 4. List BGM Tracks

Browse available royalty-free background music tracks.

```http
GET /v1/bgm/tracks?mood=upbeat&limit=10
```

**Query parameters:**

| Parameter | Description |
|-----------|-------------|
| `mood` | `upbeat`, `chill`, `dramatic`, `funny`, `motivational`, `lofi` |
| `bpm_min` | Minimum BPM |
| `bpm_max` | Maximum BPM |
| `duration_min` | Minimum track duration (seconds) |
| `limit` | Results per page (default: 20, max: 50) |

**Response:**
```json
{
  "tracks": [
    {
      "track_id": "bgm_upbeat_01",
      "name": "Summer Drive",
      "mood": "upbeat",
      "bpm": 128,
      "duration_seconds": 180,
      "preview_url": "https://cdn.nemovideo.ai/bgm/preview/bgm_upbeat_01.mp3"
    }
  ]
}
```

---

### 5. Poll Job Status

```http
GET /v1/jobs/{job_id}
```

**In progress:**
```json
{
  "job_id": "job_short_112",
  "status": "processing",
  "progress": 0.45,
  "stage": "encoding"
}
```

**Completed:**
```json
{
  "job_id": "job_short_112",
  "status": "completed",
  "outputs": {
    "video": "https://cdn.nemovideo.ai/outputs/job_short_112/short.mp4",
    "thumbnail": "https://cdn.nemovideo.ai/outputs/job_short_112/thumb.jpg"
  },
  "metadata": {
    "duration_seconds": 30,
    "width": 1080,
    "height": 1920,
    "size_bytes": 24000000
  }
}
```

**Failed:**
```json
{
  "job_id": "job_short_112",
  "status": "failed",
  "error": "Trim range exceeds source video duration"
}
```

**Polling strategy:**
- Check every 5–10 seconds (shorts encode faster than long-form)
- Timeout after 10 minutes; surface error to user if exceeded

---

## Common Workflows

### Workflow A: Horizontal → Vertical (Quick Convert)

```
1. Upload video → POST /v1/upload → file_id
2. POST /v1/shorts/create:
   - crop: preset "9:16", focus "center"
   - export: platform "tiktok"
3. Poll → GET /v1/jobs/{job_id} until completed
4. Return download URL
```

### Workflow B: Repurpose Long Video into TikTok Clip with Auto-Captions

```
1. Upload video → file_id
2. POST /v1/shorts/create:
   - trim: { start_seconds: X, end_seconds: X+30 }
   - crop: { preset: "9:16", focus: "face" }
   - captions: { enabled: true, language: "auto", style: "tiktok" }
   - export: { platform: "tiktok" }
3. Poll until completed
4. Return MP4
```

### Workflow C: Create 3 Shorts from 1 Podcast Episode

```
1. Upload full episode → file_id
2. POST /v1/shorts/batch with 3 clip configs (different trim ranges)
3. Poll all 3 job_ids in parallel
4. Return all 3 download URLs when complete
```

### Workflow D: Add BGM to Existing Short

```
1. Upload vertical video → file_id
2. Browse /v1/bgm/tracks?mood=upbeat → pick track_id
3. POST /v1/shorts/create:
   - trim: full duration (no trim needed)
   - crop: preset "9:16" (pass-through if already vertical)
   - bgm: { enabled: true, track_id: "bgm_upbeat_01", volume: 0.25 }
   - export: { platform: "instagram" }
4. Poll → return MP4
```

### Workflow E: Multi-Platform Export (Same Clip, 3 Platforms)

```
1. Upload video → file_id
2. POST /v1/shorts/batch with 3 identical clips,
   each with different export.platform value
3. Return TikTok + Instagram + YouTube Shorts versions
```

---

## Error Handling

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 400 | Bad request / invalid params | Check body; surface specific error to user |
| 401 | Invalid API key | Prompt user to verify `NEMOVIDEO_API_KEY` |
| 413 | File too large | Advise compressing or trimming source |
| 422 | Invalid crop/trim (out of bounds, etc.) | Validate trim times against `duration_seconds` from upload |
| 429 | Rate limited | Wait 10s; exponential backoff; serialize batch jobs |
| 500/503 | Server error | Retry after 30s; report if persistent |

For `job.status === "failed"`, always show the `error` field with a plain explanation and suggest a fix.

---

## Behavior Notes

- **Face tracking crop:** `focus: "face"` uses AI to keep detected faces in frame. Falls back to `center` if no face detected.
- **Duration warnings:** TikTok max is 60s, YouTube Shorts max is 60s. Warn if trim range exceeds this; don't fail silently.
- **Captions vs subtitles:** This skill burns captions optimized for mobile viewing (large, bold, center-screen). For precise SRT export or translation workflows, use the nemo-subtitle skill.
- **BGM volume:** Default `0.3` is intentionally low to keep original speech audible. For music-dominant content, use `0.6–0.8`.
- **Batch limits:** Max 10 clips per batch request. For more, split into multiple batch calls.
- **Output expiry:** CDN URLs expire in 24 hours. Advise user to download promptly.
- **Already-vertical input:** If the source is already 9:16, set `crop.preset: "9:16"` and `crop.focus: "center"` — it will pass through without re-cropping.

---

## Example Prompts → Actions

| User says | Action |
|-----------|--------|
| "Turn this video into a TikTok" | Upload → shorts/create (9:16, tiktok preset) → return MP4 |
| "Make a 30-second Reel from this clip" | Upload → trim to 30s, crop 9:16, export instagram |
| "Add captions to this short" | Upload → shorts/create with captions.enabled=true, style="tiktok" |
| "Make a YouTube Short with auto-captions and music" | Upload → captions+BGM enabled, export youtube_shorts |
| "Repurpose this podcast into 3 TikTok clips" | Upload → shorts/batch (3 clips, different trim ranges) |
| "Add background music to my Reel" | Browse BGM tracks → shorts/create with bgm.enabled=true |
| "Convert this horizontal video to vertical" | Upload → crop preset "9:16" → export generic |
| "Translate captions to Spanish on this Short" | captions.enabled=true, captions.translate_to="es" |
| "Make the same clip for TikTok, Instagram, and Shorts" | shorts/batch × 3, each with different platform preset |
