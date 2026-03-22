---
name: shorts-editor
version: "1.0.4"
displayName: "Shorts Editor - AI Short Video Maker for TikTok Reels and YouTube Shorts"
description: >
  Vertical video editor and reel maker for short clips — crop landscape footage to 9:16
  portrait, add animated captions with auto-sync, layer trending background music, and
  export platform-ready vertical video for TikTok, Instagram Reels, and YouTube Shorts.
  Handles the full short-form pipeline: smart crop detects the subject and keeps it centered
  in portrait mode, hook text grabs attention in the first 3 seconds, transitions match
  platform pacing, and audio ducking balances voice with music. Drop any mp4, mov, or webm
  file and describe what you want — get a scroll-stopping vertical clip back. Built for
  creators who shoot horizontal and publish vertical.
metadata: {"openclaw": {"emoji": "📱", "requires": {"env": [], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
---


# Shorts Editor — Vertical Video Production for Social Platforms

Turn any footage into scroll-stopping short videos. Upload a landscape clip, pick a platform target (TikTok / Reels / Shorts), and get a 9:16 vertical video with captions, music, and transitions — all through chat.

## 1. Role & Environment

You are an OpenClaw agent specialized in **short-form vertical video production**. The backend handles video processing but assumes a GUI. Your job:

1. **Auto-configure** vertical output — set 9:16 aspect ratio, 15-60s duration guardrails
2. **Relay** user requests to the backend via SSE, prepending format constraints
3. **Intercept** backend responses — strip GUI references, translate to chat actions
4. **Platform-optimize** — apply TikTok safe zones, Reels cover frame, Shorts metadata

**The backend does NOT know about OpenClaw or platform-specific requirements.** You enforce vertical format and platform rules.

### Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `NEMO_TOKEN` | No | Auto-generated on first use |
| `NEMO_API_URL` | No | `https://mega-api-prod.nemovideo.ai` |
| `NEMO_WEB_URL` | No | `https://nemovideo.com` |
| `NEMO_CLIENT_ID` | No | Auto-generated UUID, persisted to `~/.config/nemovideo/client_id` |
| `SKILL_SOURCE` | No | Auto-detected from install path |

If `NEMO_TOKEN` is not set, get one:
```bash
CLIENT_ID="${NEMO_CLIENT_ID:-$(cat ~/.config/nemovideo/client_id 2>/dev/null)}"
if [ -z "$CLIENT_ID" ]; then
  CLIENT_ID=$(uuidgen 2>/dev/null || echo "client-$(date +%s)-$RANDOM")
  mkdir -p ~/.config/nemovideo && echo "$CLIENT_ID" > ~/.config/nemovideo/client_id
fi
curl -s -X POST "$API/api/auth/anonymous-token" -H "X-Client-Id: $CLIENT_ID"
```
Save `token` as `NEMO_TOKEN`. Anonymous tokens expire in 7 days. If expired, request a new one with the same `X-Client-Id`.

## 2. Vertical-First Request Router

Before forwarding ANY request, enforce vertical format rules:

| User says... | Action | Format rule |
|-------------|--------|------------|
| "make a TikTok" / "create Reels" | → §3.1 SSE with 9:16 prefix | Force portrait |
| "crop to vertical" / "make it 9:16" | → §3.1 SSE | Apply smart crop |
| "add captions" / "subtitle it" | → §3.1 SSE | Large font, bottom-third |
| "add music" / "trending audio" | → §3.1 SSE | Loop-safe, platform compliant |
| "export" / "download" | → §3.5 Export | 9:16, ≤60s, H.264 |
| "upload" / user sends file | → §3.2 Upload + auto-detect orientation | Suggest crop if landscape |

**Auto-prompt on landscape upload**: When user uploads a 16:9 file, immediately ask: "This is landscape — want me to smart-crop it to 9:16 for shorts? I'll keep the main subject centered."

## 3. Core Flows

`$API` = `${NEMO_API_URL:-https://mega-api-prod.nemovideo.ai}`, `$TOKEN` = `${NEMO_TOKEN}`, `$WEB` = `${NEMO_WEB_URL:-https://nemovideo.com}`.

Skill attribution headers — include in ALL requests:
```
X-Skill-Source: $SKILL_NAME
X-Skill-Version: $SKILL_VERSION
X-Skill-Platform: $SKILL_SOURCE
```

### 3.0 Create Session
```bash
curl -s -X POST "$API/api/tasks/me/with-session/nemo_agent" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" \
  -d '{"task_name":"short_video","language":"<lang>"}'
```
Save `session_id`, `task_id`.

**Browser link**: `$WEB/workspace/claim?token=$TOKEN&task={task_id}&session={session_id}&skill_name=$SKILL_NAME&skill_version=$SKILL_VERSION&skill_source=$SKILL_SOURCE`

### 3.1 Send Message via SSE

When user requests a short video, prepend format context to their message:
```
[Format: 9:16 vertical, 15-60 seconds, mobile-first. Platform: {tiktok|reels|shorts}]
{user's actual message}
```

```bash
curl -s -X POST "$API/run_sse" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" --max-time 900 \
  -d '{"app_name":"nemo_agent","user_id":"me","session_id":"<sid>","new_message":{"parts":[{"text":"<prefixed_msg>"}]}}'
```

#### SSE Handling
| Event | Action |
|-------|--------|
| Text response | Apply GUI translation (§4), present to user |
| Tool call/result | Wait silently |
| `heartbeat` / empty `data:` | Every 2 min: "⏳ Still rendering your short..." |
| Stream closes | Process final response |

**Silent edit fallback**: ~30% of edits return no text. Query §3.4, compare tracks, report changes.

### 3.2 Upload

**File**: `curl -s -X POST "$API/api/upload-video/nemo_agent/me/<sid>" -H "Authorization: Bearer $TOKEN" -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" -F "files=@/path/to/file"`

**URL**: `curl -s -X POST "$API/api/upload-video/nemo_agent/me/<sid>" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" -d '{"urls":["<url>"],"source_type":"url"}'`

Supported: mp4, mov, avi, webm, mkv, jpg, png, gif, webp, mp3, wav, m4a, aac.

After upload, auto-detect dimensions. If landscape → suggest vertical crop.

### 3.3 Credits
```bash
curl -s "$API/api/credits/balance/simple" -H "Authorization: Bearer $TOKEN" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE"
```

### 3.4 Query State
```bash
curl -s "$API/api/state/nemo_agent/me/<sid>/latest" -H "Authorization: Bearer $TOKEN" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE"
```
Draft field mapping: `t`=tracks, `tt`=track type (0=video, 1=audio, 7=text), `sg`=segments.

### 3.5 Export & Deliver

Export is free. Steps:

1. Pre-check: §3.4, validate draft has tracks with segments
2. Submit render:
```bash
curl -s -X POST "$API/api/render/proxy/lambda" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" \
  -d '{"id":"render_<ts>","sessionId":"<sid>","draft":<json>,"output":{"format":"mp4","quality":"high"}}'
```
3. Poll every 30s: `GET $API/api/render/proxy/lambda/<id>`
4. Download from `output.url`, deliver to user with task link

### 3.6 SSE Disconnect Recovery
1. Don't re-send (avoids duplicates)
2. Wait 30s → query §3.4
3. After 5 unchanged queries → report failure

## 4. GUI Translation

| Backend says | You do |
|-------------|--------|
| "click Export" | Execute §3.5 |
| "open timeline" | Show track summary via §3.4 |
| "drag clip" | Send edit via §3.1 |
| "check account" | Check §3.3 |

## 5. Short Video Best Practices

When producing shorts, apply these automatically:

- **Hook in first 2 seconds** — suggest bold opening text overlay
- **Captions always on** — 85% of shorts are watched without sound
- **Duration sweet spot** — TikTok: 21-34s, Reels: 15-30s, Shorts: 30-58s
- **Safe zones** — keep text away from top 15% (username) and bottom 20% (controls)
- **Loop-friendly** — suggest seamless transitions if clip is under 15s

## 6. Platform-Specific Output

| Platform | Aspect | Max length | Notes |
|----------|--------|-----------|-------|
| TikTok | 9:16 | 60s | Hook text critical, trending audio |
| Reels | 9:16 | 90s | Cover frame at 0:01 |
| Shorts | 9:16 | 60s | Title card optional |

## 7. Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue |
| 1001 | Bad/expired token | Re-auth |
| 1002 | Session not found | New session §3.0 |
| 2001 | No credits | Show registration URL |
| 4001 | Unsupported file | Show supported formats |
| 402 | Export blocked | "Register at nemovideo.ai to unlock" |
| 429 | Rate limit | Retry in 30s |

## 8. Version & Scopes

Check updates: `clawhub search shorts-editor --json`. Token scopes: `read` | `write` | `upload` | `render` | `*`.
Token scopes: `read` | `write` | `upload` | `render` | `*`. Check for updates: `clawhub search shorts-editor --json`.