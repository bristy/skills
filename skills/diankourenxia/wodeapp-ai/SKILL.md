---
name: wodeapp-ai
description: "WodeApp AI Engine — token-efficient, unified credit pool, zero-deploy. Text, image, video (Doubao Seedance + Kling AI), structured JSON, TTS, visual workflows, headless workflow API, no-code page building. 343+ models, MCP-native."
homepage: https://wodeapp.ai
author: WodeApp Team
requiredEnv:
  - WODEAPP_API_KEY
---

# WodeApp AI Skill Pack

> **EN** One skill pack to unlock all WodeApp AI capabilities.
>
> **中文** 只需接入一个 Skill 包，即可解锁 WodeApp 全部 AI 能力。

---

## Core Capabilities

### 🤖 Text Generation
Copywriting · Summaries · Translation · Code  
**Models**: GPT-4o, Claude 3.5, Gemini, DeepSeek, Qwen

### 🎨 Image Generation
Text-to-image · Image-to-image · Style transfer  
**Models**: Seedream 3.0, Imagen 4, Flux

### 📊 Structured JSON
Schema-compliant JSON output from any model  
**Models**: All supported models

### 🎙️ Text-to-Speech
Multi-language · Multi-voice · Custom voice cloning  
**Models**: Doubao TTS, Edge TTS, Kling TTS

### 🎬 Video Generation
Text/image → dynamic video  
**Models**: Doubao Seedance, Kling AI

### ⚡ Visual Workflow
Drag-and-drop multi-step AI pipelines — 19 step types, no code needed

### 🔗 Headless Workflow API
Discover, run, and poll workflows via REST — programmatic execution without browser

### 🌐 Page Builder
One sentence → full interactive page with 60+ UI components

### 🚀 Zero-Deploy
One-click publish with auto domain (`*.wodeapp.ai`) + SSL

---

## Why WodeApp?

- **Token-Efficient** — Smart routing, same quality, 80% less cost
- **Unified Credit Pool** — One balance for 343+ models, no multi-platform hassle
- **Zero-Deploy** — Auto domain + SSL, no server needed
- **MCP Plug & Play** — Auto-discover all tools, zero config
- **Visual Workflows** — Form → AI → Review → Publish, drag-and-drop

---

## Quick Setup

### 1. Get API Key

Sign up at [wodeapp.ai](https://wodeapp.ai) → **API Skills** → **Generate API Key**

```bash
export WODEAPP_API_KEY="sk_live_xxxxxxxxxx"
```

### 2. MCP Server (Recommended)

Add to your MCP client config (`claude_desktop_config.json` or Cursor settings):

```json
{
  "mcpServers": {
    "wodeapp": {
      "type": "sse",
      "url": "https://wodeapp.ai/mainserver/mcp",
      "headers": { "X-API-Key": "${WODEAPP_API_KEY}" }
    }
  }
}
```

> [!WARNING]
> Use environment variable `$WODEAPP_API_KEY` — never hardcode API keys in config files.

---

## MCP Tools (9 auto-discovered)

| Tool | Description |
|------|-------------|
| `ai_generate_text` | AI text generation (343+ models) |
| `ai_generate_image` | Text-to-image / image-to-image |
| `list_projects` | List user projects |
| `create_project` | Create from template |
| `get_project` | Get project details |
| `get_page` | Get page JSON config |
| `list_actions` | List executable actions |
| `execute_action` | Execute action / workflow |
| `publish_project` | Publish to production |

---

## REST API Examples

All requests require `X-API-Key` header.

**Text generation**
```bash
curl -X POST https://wodeapp.ai/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $WODEAPP_API_KEY" \
  -d '{"message":"Write a brand tagline","model":"gemini-2.0-flash"}'
```

**Image generation**
```bash
curl -X POST https://wodeapp.ai/api/ai/image/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $WODEAPP_API_KEY" \
  -d '{"prompt":"Coffee beans close-up","size":"16:9","model":"seedream-3.0"}'
```

**Video generation** (Doubao Seedance)
```bash
curl -X POST https://wodeapp.ai/api/ai/video \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $WODEAPP_API_KEY" \
  -d '{"prompt":"Barista latte art close-up","model":"seedance"}'
```

**Structured JSON**
```bash
curl -X POST https://wodeapp.ai/api/ai/json \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $WODEAPP_API_KEY" \
  -d '{"message":"Generate 3 prompts","systemPrompt":"Return {prompts:[{title,content}]}"}'
```

> Local dev: replace domain with `http://localhost:4100`

---

## Headless Workflow API

Programmatic workflow execution — no browser needed.

```bash
# Step 1: Discover workflow schema
curl https://my-project.wodeapp.ai/runtime-server/api/workflow/schema \
  -H "x-subdomain-project: my-project"

# Step 2: Execute workflow
curl -X POST https://my-project.wodeapp.ai/runtime-server/api/workflow/run \
  -H "Content-Type: application/json" \
  -H "x-subdomain-project: my-project" \
  -d '{"inputs": {"text": "Product description here"}}'
# → { "runId": "uuid", "status": "running", "pollUrl": "..." }

# Step 3: Poll for results
curl https://my-project.wodeapp.ai/runtime-server/api/workflow/run/{runId} \
  -H "x-subdomain-project: my-project"
# → { "status": "completed", "outputs": { ... } }
```

---

## Endpoints

| Service | Production | Local Dev |
|---------|-----------|-----------|
| Main | `https://wodeapp.ai/mainserver/api` | `localhost:3100/mainserver/api` |
| Runtime | `https://wodeapp.ai/api` | `localhost:4100/api` |
| Workflow | `https://{project}.wodeapp.ai/runtime-server/api/workflow` | `localhost:4100/runtime-server/api/workflow` |
| MCP | `https://wodeapp.ai/mainserver/mcp` | `localhost:3100/mainserver/mcp` |

---

## Rate Limits & Security

**Rate Limits**

| Layer | Value |
|-------|-------|
| Per-user concurrency | 5 |
| Global concurrency | 30 |
| Guest daily | 500 credits |
| Project daily | 2,000 credits |
| Insufficient balance | HTTP 402 |

**Security Best Practices**

- **Key storage** — Always use env vars, never hardcode
- **Scoped keys** — Create project-scoped keys with billing limits
- **Revocation** — Revoke compromised keys instantly at wodeapp.ai
- **Data policy** — Prompts sent to AI providers for processing only, never stored for training

---

## Environment Variables

```bash
WODEAPP_API_KEY=sk_live_xxx          # Required
WODEAPP_MAIN_SERVER=http://...       # Optional override
WODEAPP_RUNTIME_SERVER=http://...    # Optional override
```

---

`ai` `text-generation` `image-generation` `video-generation` `tts` `mcp` `no-code` `zero-deploy` `page-builder` `workflow` `visual-workflow` `headless-workflow` `workflow-api` `agent-tools` `multi-model` `gpt-4o` `claude` `gemini` `deepseek` `doubao` `seedance` `kling` `seedream` `imagen` `flux` `qwen` `token-efficient`
