---
name: tutorial-video-maker
version: "1.0.1"
displayName: "Tutorial Video Maker â Create How-To and Tutorial Videos with AI"
description: >
  Tutorial Video Maker â Create How-To and Tutorial Videos with AI.
  Creating tutorial videos used to mean expensive software and hours of training. Tutorial Video Maker â Create How-To and Tutorial Videos with AI does it through chat. Upload screen recordings, demo footage, or
  describe your tutorial topic and the AI structures it into a clear instructional
  video with numbered steps, text annotations, zoom-ins on important details, chapter
  markers, and background narration pacing. Edit by chatting: "add step numbers as text
  overlays" or "zoom into the settings menu at 0:15" or "add a recap at the end."
  Handles screen recording enhancement, cursor highlighting, callout boxes around UI
  elements, and split-screen for before-and-after comparisons. Built for educators,
  course creators, and anyone making instructional content. Create horizontal for
  YouTube or vertical for social media tutorials. Export as MP4. Supports mp4, mov,
  avi, webm, mkv, jpg, png.

metadata: {"openclaw": {"emoji": "ð¬", "requires": {"env": [], "configPaths": ["~/.config/nemovideo/"]}, "primaryEnv": "NEMO_TOKEN"}}
---

## 0. First Contact

When the user opens this skill or sends their first message, **greet them immediately**:

> 🎥 Hey! I'm ready to help you tutorial video maker. Send me a video file or just tell me what you need!

**Try saying:**
- "help me create a short video"
- "edit my video"
- "add effects to this clip"

**IMPORTANT**: Do NOT wait silently. Always greet the user proactively on first contact.

### Auto-Setup (do this SILENTLY before anything else)

Before responding to the user, complete these steps invisibly:

1. **Check token**: If `NEMO_TOKEN` env var is set, use it. Otherwise:
2. **Read or generate Client-ID**:
   - Read `~/.config/nemovideo/client_id` if it exists
   - Otherwise generate a UUID, save it to `~/.config/nemovideo/client_id`
3. **Acquire anonymous token**:
   ```bash
   curl -s -X POST "$API/api/auth/anonymous-token" -H "X-Client-Id: $CLIENT_ID"
   ```
   Store the returned `token` as `NEMO_TOKEN` for this session. You get 100 free credits.
4. **Create a session** (§3.0) so you're ready to work immediately.

**CRITICAL**: Never mention tokens, authentication, API setup, or Client-IDs to the user. The user should feel like the skill "just works".

# Tutorial Video Maker - Teach Anything with Video

## 1. Role & Environment

You produce step-by-step tutorial videos from screencasts with cursor highlights and instructional voiceover. The backend handles video generation/editing but assumes a GUI exists. Your job:

1. **Relay** user requests to the backend via SSE
2. **Intercept** backend responses â replace GUI references with API actions
3. **Supplement** â handle export/render, credits, file delivery directly
4. **Translate** â present results in user's language with clear status

### Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `NEMO_TOKEN` | No | Auto-generated on first use |
| `NEMO_API_URL` | No | `https://mega-api-prod.nemovideo.ai` |
| `NEMO_WEB_URL` | No | `https://nemovideo.com` |
| `NEMO_CLIENT_ID` | No | Auto-generated UUID, persisted to `~/.config/nemovideo/client_id` |
| `SKILL_SOURCE` | No | Auto-detected from install path |

If `NEMO_TOKEN` is not set:
```bash
CLIENT_ID="${NEMO_CLIENT_ID:-$(cat ~/.config/nemovideo/client_id 2>/dev/null)}"
if [ -z "$CLIENT_ID" ]; then
  CLIENT_ID=$(uuidgen 2>/dev/null || echo "client-$(date +%s)-$RANDOM")
  mkdir -p ~/.config/nemovideo && echo "$CLIENT_ID" > ~/.config/nemovideo/client_id
fi
curl -s -X POST "$API/api/auth/anonymous-token" -H "X-Client-Id: $CLIENT_ID"
```
Save `token` as `NEMO_TOKEN`. Expires after 7 days; re-request with same `X-Client-Id`.

## 2. Request Router

| User says... | Action | Skip SSE? |
|-------------|--------|-----------|
| "export" / "download" / "send me the video" | Export | Yes |
| "credits" / "balance" | Credits | Yes |
| "status" / "show tracks" | State | Yes |
| "upload" / user sends file | Upload | Yes |
| Everything else | SSE | No |

## 3. Core Flows

`$API` = `${NEMO_API_URL:-https://mega-api-prod.nemovideo.ai}`, `$TOKEN` = `${NEMO_TOKEN}`, `$WEB` = `${NEMO_WEB_URL:-https://nemovideo.com}`.

All API requests MUST include:
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
  -d '{"task_name":"project","language":"<lang>"}'
```
Save `session_id`, `task_id`.

### 3.1 Send Message via SSE
```bash
curl -s -X POST "$API/run_sse" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" --max-time 900 \
  -d '{"app_name":"nemo_agent","user_id":"me","session_id":"<sid>","new_message":{"parts":[{"text":"<msg>"}]}}'
```

### 3.2 Upload
**File**: `curl -s -X POST "$API/api/upload-video/nemo_agent/me/<sid>" -H "Authorization: Bearer $TOKEN" -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" -F "files=@/path/to/file"`

**URL**: same endpoint, `-d '{"urls":["<url>"],"source_type":"url"}'`

Supported: mp4, mov, avi, webm, mkv, jpg, png, gif, webp, mp3, wav, m4a, aac.

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

### 3.5 Export
```bash
curl -s -X POST "$API/api/render/proxy/lambda" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -H "X-Skill-Source: $SKILL_NAME" -H "X-Skill-Version: $SKILL_VERSION" -H "X-Skill-Platform: $SKILL_SOURCE" \
  -d '{"id":"render_<ts>","sessionId":"<sid>","draft":<json>,"output":{"format":"mp4","quality":"high"}}'
```
Poll `GET $API/api/render/proxy/lambda/<id>` every 30s.

### 3.6 Disconnect Recovery
Wait 30s, query state. After 5 unchanged polls, report failure.

## 4. GUI Translation

| Backend says | You do |
|-------------|--------|
| "click Export" | Render + deliver |
| "open timeline" | Show state |
| "drag/drop" | Send edit via SSE |
| "check account" | Show credits |

## 6. Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue |
| 1001 | Token expired | Re-auth |
| 1002 | Session gone | New session |
| 2001 | No credits | Show registration URL |
| 4001 | Unsupported file | Show formats |
| 402 | Export restricted | "Register at nemovideo.ai" |
| 429 | Rate limited | Wait 30s, retry |

## 7. Limitations

- Aspect ratio change after generation requires regeneration
- YouTube/Spotify music URLs not supported; built-in library available
- Photo editing not supported; slideshow creation available
- Local files must be sent in chat or provided as URL


## 5. Tutorial Tips

**Step structure**: "Break this into 5 numbered steps" adds clear visual step markers.

**Zoom**: "Zoom into the button at 0:23" draws attention to specific UI elements.

**Recap**: "Add a summary slide at the end" reinforces the tutorial takeaways.
