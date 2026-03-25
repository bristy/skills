---
name: nemo-edit
version: "1.8.3"
displayName: "NemoEdit - AI Video Editor for Color Grading and Background Music"
author: nemovideonemo
description: >
  Color grading and background music editor for video — apply LUTs, adjust exposure and
  saturation, mix audio tracks, and add background music to any clip through chat. Works as
  an mp4 editor with cut, trim, merge, and format conversion (flv, wmv, avi to mp4). No
  timeline, no GUI — describe the edit you want and get the processed video back. Handles
  color correction, audio ducking, silent segment removal, and multi-clip assembly in a single
  conversation. Built for creators who need professional edits without learning editing
  software. Supports mp4, mov, avi, webm, mkv.
metadata:
  openclaw:
    emoji: ✂️
---

# NemoEdit Skill

## Description

Use NemoEdit when the user wants to **cut video precisely**, **trim by timecode**, **do color grading**, **color correction**, **mix audio tracks**, **remove silence**, **do jump cuts**, **add transitions between clips**, **adjust audio levels**, **normalize audio**, **denoise audio**, **merge multiple video clips**, **split video at specific points**, or work with a **multi-track timeline**. Powered by NemoVideo AI.

NemoEdit is the precision editing layer of the NemoVideo suite. Where nemo-video handles conversational creation and nemo-shorts handles platform repurposing, NemoEdit gives frame-level control: set in/out points by exact timecode, cut on beat, color-grade with LUT support, normalize and mix audio, remove dead air, and assemble multi-clip sequences — all via API.

**Trigger phrases:** cut video, trim video precisely, frame-accurate cut, video editing, edit video clip, color grading, color correction, LUT, white balance video, exposure video, contrast video, color video, audio mixing, audio levels, normalize audio, audio normalization, denoise audio, remove background noise, remove silence, dead air removal, jump cut, beat cut, cut on beat, add transition, video transition, fade in fade out, dissolve transition, merge clips, join videos, combine videos, split video, split clip, video timeline, multi-track, assemble sequence, video sequence, professional video editing, advanced video editing, precise editing, timecode, in point out point

**Primary use cases:**
- Frame-accurate cut/trim by timecode or seconds
- Split a clip at a specific point; merge multiple clips into a sequence
- Color correction: white balance, exposure, contrast, saturation, highlights/shadows
- Color grading with LUT files (.cube) or built-in presets
- Audio track mixing: per-track volume, pan, fade-in/out
- Audio normalization (LUFS target) and background noise removal
- Remove silence / dead air automatically (for podcasts, interviews, screen recordings)
- Beat-synced cuts (sync edit points to audio BPM)
- Add transitions between clips: fade, dissolve, wipe, zoom, dip-to-black
- Export with precise codec/bitrate/resolution control

**Not for:** generating new video from text (see nemo-video), vertical short-form repurposing (see nemo-shorts), or subtitle/caption-only workflows (see nemo-subtitle).

---

## Setup

**Base URL:** `https://mega-api-prod.nemovideo.ai`

All requests require:
```
Authorization: Bearer <NEMOVIDEO_API_KEY>
Content-Type: application/json
```

Set `NEMOVIDEO_API_KEY` in your environment or OpenClaw secrets.

---

## Workflow Overview

```
Upload clip(s) → Build edit spec → POST /v1/edit/render → Poll job → Download output
```

All rendering is async. Always poll job status before delivering output to the user.

---

## API Reference

### 1. Upload Media

Upload source clips before referencing them in an edit.

```http
POST /v1/upload
Content-Type: multipart/form-data

file=<binary>
```

**Response:**
```json
{
  "file_id": "f_abc123",
  "filename": "interview_raw.mp4",
  "duration_seconds": 847.4,
  "width": 1920,
  "height": 1080,
  "fps": 29.97,
  "has_audio": true,
  "size_bytes": 1240000000
}
```

Supported formats: `mp4`, `mov`, `avi`, `webm`, `mkv`, `mp3`, `wav`, `m4a`, `aac`, `.cube` (LUT).

---

### 2. Render Edit

The core endpoint. Accepts a declarative edit spec and returns a job ID.

```http
POST /v1/edit/render
Content-Type: application/json

{
  "timeline": [ <clip objects> ],
  "audio_tracks": [ <audio track objects> ],
  "color": { <color grading settings> },
  "audio_processing": { <audio processing settings> },
  "transitions": [ <transition objects> ],
  "export": { <export settings> }
}
```

---

#### `timeline` (required, array of clip objects)

Each object defines one video segment on the timeline.

```json
{
  "file_id": "f_abc123",
  "trim_start": 12.5,
  "trim_end": 47.0,
  "timeline_position": 0.0
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_id` | string | File ID from upload |
| `trim_start` | float | Start point in source clip (seconds, default: 0) |
| `trim_end` | float | End point in source clip (seconds, default: end of clip) |
| `timeline_position` | float | Position in output timeline (seconds). Omit to auto-sequence clips end-to-end |
| `speed` | float | Playback speed multiplier (0.25–4.0, default: 1.0) |
| `reverse` | bool | Play clip in reverse (default: false) |
| `mute` | bool | Mute the video track's embedded audio (default: false) |

**Example — 3-clip sequence:**
```json
"timeline": [
  { "file_id": "f_abc123", "trim_start": 0, "trim_end": 15.0 },
  { "file_id": "f_def456", "trim_start": 5.2, "trim_end": 22.8 },
  { "file_id": "f_abc123", "trim_start": 120.0, "trim_end": 145.0 }
]
```

Clips are placed sequentially. Use `timeline_position` for manual placement.

---

#### `audio_tracks` (optional, array)

Additional audio-only tracks layered over the video timeline.

```json
{
  "file_id": "f_bgm001",
  "trim_start": 0,
  "trim_end": 60,
  "timeline_position": 0,
  "volume": 0.3,
  "fade_in": 1.5,
  "fade_out": 2.0
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_id` | string | Uploaded audio file ID |
| `volume` | float | Track volume (0.0–1.0) |
| `fade_in` | float | Fade-in duration (seconds) |
| `fade_out` | float | Fade-out duration (seconds) |
| `pan` | float | Stereo pan (-1.0 left to 1.0 right, default: 0.0) |

---

#### `color` (optional)

Per-render color correction and grading.

```json
{
  "preset": "cinematic_warm",
  "lut_file_id": null,
  "white_balance_kelvin": 5500,
  "exposure": 0.2,
  "contrast": 0.1,
  "highlights": -0.15,
  "shadows": 0.1,
  "saturation": 0.05,
  "vibrance": 0.1
}
```

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `preset` | string | — | Built-in color preset. Options: `"cinematic_warm"`, `"cinematic_cool"`, `"clean_bright"`, `"muted_film"`, `"vivid"`, `"bw"` (black & white), `"none"` |
| `lut_file_id` | string | — | Use uploaded `.cube` LUT file. Overrides `preset` |
| `lut_intensity` | float | 0.0–1.0 | LUT blend intensity (default: 1.0) |
| `white_balance_kelvin` | int | 2000–10000 | Color temperature. `5500` = daylight, `3200` = tungsten, `7000` = shade |
| `exposure` | float | -2.0–2.0 | Overall brightness adjustment (EV stops) |
| `contrast` | float | -1.0–1.0 | Shadow/highlight spread |
| `highlights` | float | -1.0–1.0 | Recover blown highlights (negative) or boost |
| `shadows` | float | -1.0–1.0 | Lift dark areas (positive) or crush |
| `saturation` | float | -1.0–1.0 | Color intensity |
| `vibrance` | float | -1.0–1.0 | Smart saturation (protects skin tones) |

---

#### `audio_processing` (optional)

Global audio processing applied to the mixed output.

```json
{
  "normalize": true,
  "normalize_lufs": -14,
  "denoise": true,
  "denoise_strength": 0.6,
  "remove_silence": false
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `normalize` | bool | Normalize output audio to a target loudness (default: false) |
| `normalize_lufs` | float | Target loudness in LUFS. `-14` = YouTube/Spotify standard, `-16` = podcast standard, `-23` = broadcast (default: -14) |
| `denoise` | bool | Remove background noise / room tone (default: false) |
| `denoise_strength` | float | 0.0–1.0. `0.3` = light, `0.6` = medium, `0.9` = aggressive (default: 0.5) |
| `remove_silence` | bool | Auto-detect and remove silent gaps (dead air). Good for interviews, screen recordings (default: false) |
| `silence_threshold_db` | float | Volume level below which audio is considered silence (default: -40 dB) |
| `silence_min_duration` | float | Minimum silence length to remove (seconds, default: 0.5) |
| `eq_preset` | string | Apply EQ preset: `"voice"` (boost presence, cut muddiness), `"music"` (flat), `"podcast"` (high-pass + voice boost), `"none"` |

---

#### `transitions` (optional, array)

Transitions applied between consecutive timeline clips.

```json
{
  "after_clip_index": 0,
  "type": "dissolve",
  "duration": 0.5
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `after_clip_index` | int | 0-indexed position of the clip *before* this transition |
| `type` | string | `"cut"` (default, no effect), `"dissolve"`, `"fade_black"`, `"fade_white"`, `"wipe_left"`, `"wipe_right"`, `"zoom_in"`, `"zoom_out"`, `"flash"` |
| `duration` | float | Transition duration in seconds (default: 0.5, max: 2.0) |

---

#### `export` (required)

```json
{
  "format": "mp4",
  "resolution": "1920x1080",
  "fps": 29.97,
  "video_bitrate_kbps": 8000,
  "audio_bitrate_kbps": 192,
  "codec": "h264"
}
```

| Parameter | Type | Options / Default |
|-----------|------|-------------------|
| `format` | string | `"mp4"` (default), `"mov"`, `"webm"` |
| `resolution` | string | `"3840x2160"`, `"1920x1080"` (default), `"1280x720"`, `"original"` |
| `fps` | float | `23.976`, `24`, `25`, `29.97`, `30`, `60` (default: match source) |
| `video_bitrate_kbps` | int | 1000–50000 (default: 8000) |
| `audio_bitrate_kbps` | int | `128`, `192` (default), `320` |
| `codec` | string | `"h264"` (default), `"h265"`, `"vp9"` |

**Render response:**
```json
{
  "job_id": "job_edit_778",
  "status": "queued",
  "estimated_seconds": 180,
  "total_output_duration": 95.3
}
```

---

### 3. Remove Silence (Standalone)

Detect and remove silence from a single clip without a full edit spec.

```http
POST /v1/edit/remove-silence
Content-Type: application/json

{
  "file_id": "f_abc123",
  "threshold_db": -40,
  "min_silence_duration": 0.5,
  "padding": 0.1,
  "export": { "format": "mp4", "resolution": "original" }
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `threshold_db` | float | Volume below this = silence (default: -40 dB) |
| `min_silence_duration` | float | Minimum gap to remove (seconds, default: 0.5) |
| `padding` | float | Keep this many seconds around each cut (default: 0.1) — prevents choppy speech |

**Response:** job object; poll with `/v1/jobs/{job_id}`.

---

### 4. Beat Detection

Detect beat timestamps in an audio file for beat-synced editing.

```http
POST /v1/edit/detect-beats
Content-Type: application/json

{ "file_id": "f_bgm001" }
```

**Response:**
```json
{
  "bpm": 128,
  "beats": [0.47, 0.94, 1.41, 1.88, 2.34],
  "downbeats": [0.47, 1.88, 3.28]
}
```

Use `beats` timestamps as `trim_end` / `trim_start` values in `/v1/edit/render` for beat-synced cuts.

---

### 5. Poll Job Status

```http
GET /v1/jobs/{job_id}
```

**Completed:**
```json
{
  "job_id": "job_edit_778",
  "status": "completed",
  "outputs": {
    "video": "https://cdn.nemovideo.ai/outputs/job_edit_778/final.mp4"
  },
  "metadata": {
    "duration_seconds": 95.3,
    "width": 1920,
    "height": 1080,
    "size_bytes": 95000000
  }
}
```

**Polling strategy:** every 10–15 seconds; timeout after 20 minutes for long renders. Report `"⏳ Rendering..."` at start; `"⏳ Still rendering..."` every 2 minutes.

---

## Common Workflows

### Workflow A: Trim and Export a Single Clip

```
1. Upload clip → file_id
2. POST /v1/edit/render:
   timeline: [{ file_id, trim_start: 30.0, trim_end: 90.0 }]
   export: { format: "mp4", resolution: "1920x1080" }
3. Poll → return download URL
```

### Workflow B: Join 3 Clips with Dissolve Transitions

```
1. Upload 3 clips → file_id_1, file_id_2, file_id_3
2. POST /v1/edit/render:
   timeline: [clip1, clip2, clip3] (auto-sequenced)
   transitions: [
     { after_clip_index: 0, type: "dissolve", duration: 0.5 },
     { after_clip_index: 1, type: "dissolve", duration: 0.5 }
   ]
   export: { format: "mp4" }
3. Poll → return output
```

### Workflow C: Color Grade + Audio Normalize

```
1. Upload clip → file_id
2. POST /v1/edit/render:
   timeline: [{ file_id }]  (full clip, no trim)
   color: { preset: "cinematic_warm", exposure: 0.1, highlights: -0.1 }
   audio_processing: { normalize: true, normalize_lufs: -14 }
   export: { format: "mp4" }
3. Poll → return output
```

### Workflow D: Podcast / Interview — Remove Dead Air

```
1. Upload recording → file_id
2. POST /v1/edit/remove-silence:
   { file_id, threshold_db: -40, min_silence_duration: 0.8, padding: 0.15 }
3. Poll → return tightened output
```

### Workflow E: Beat-Synced Edit

```
1. Upload music → bgm_file_id
2. POST /v1/edit/detect-beats → get beats[] array
3. Upload video clips → file_ids
4. Build timeline with trim points matching beats timestamps
5. POST /v1/edit/render with timeline + audio_tracks (bgm)
6. Poll → return output
```

### Workflow F: Apply Custom LUT

```
1. Upload source clip → file_id
2. Upload .cube LUT file → lut_file_id
3. POST /v1/edit/render:
   timeline: [{ file_id }]
   color: { lut_file_id: "f_lut001", lut_intensity: 0.85 }
   export: { format: "mp4" }
4. Poll → return graded output
```

---

## Error Handling

| HTTP Code | Error | Action |
|-----------|-------|--------|
| 400 | Invalid params (e.g. trim_end > duration) | Validate trim times against upload `duration_seconds`; surface specific message |
| 401 | Invalid API key | Prompt user to verify `NEMOVIDEO_API_KEY` |
| 413 | File too large | Suggest compressing source first |
| 422 | Incompatible clips (e.g. mismatched frame rates) | Tell user; suggest re-encoding source clips to matching spec |
| 429 | Rate limited | Wait 10s, exponential backoff |
| 500/503 | Server error | Retry after 30s; report if persistent |

For `job.status === "failed"`, always surface the `error` field with a plain explanation and next-step suggestion.

---

## Behavior Notes

- **Output expiry:** CDN output URLs expire in 24 hours. Advise user to download promptly.
- **Codec defaults:** H.264 is broadest-compatible. Suggest H.265 only if user explicitly asks for smaller file size.
- **Color + LUT:** `lut_file_id` takes priority over `preset`. Both can coexist — LUT is applied first, then individual parameter tweaks on top.
- **Silence removal padding:** Always use `padding ≥ 0.1s` to avoid cutting off the first/last syllable of speech.
- **Normalize LUFS targets:** -14 LUFS for YouTube/social, -16 for podcasts, -23 for broadcast.
- **FPS matching:** If merging clips with different frame rates, explicitly set `fps` in export to avoid judder.
- **Resolution "original":** Preserves source resolution. Use when user doesn't specify output size.

---

## Skill Positioning (within NemoVideo suite)

| Skill | Best for |
|-------|---------|
| **nemo-video** | Conversational AI video generation + casual editing via chat |
| **nemo-edit** | Precise, professional editing: cuts, color, audio, multi-clip sequences |
| **nemo-shorts** | Short-form vertical repurposing (TikTok / Reels / Shorts) |
| **nemo-subtitle** | Subtitle generation, translation, SRT export, caption burning |
