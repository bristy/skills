---
name: chatclaw
version: 0.2.9
description: Connect your OpenClaw bot to the ChatClaw cloud dashboard for real-time remote chat, token tracking, and task management
author: ChatClaw Team
homepage: https://chatclaw.com
metadata: { "openclaw": { "os": ["darwin", "linux"], "requires": { "bins": ["python3"], "env": ["CHATCLAW_API_KEY"], "config": ["gateway.http.endpoints.chatCompletions", "gateway.auth.token"] }, "primaryEnv": "CHATCLAW_API_KEY", "install": { "uv": "aiohttp>=3.9 websockets>=12.0 cryptography>=41.0" } } }
---

# ChatClaw

ChatClaw is a persistent background bridge that connects your local OpenClaw agent to the ChatClaw cloud dashboard. Once installed and enabled, it runs automatically with OpenClaw and allows you to chat with your agent, monitor token usage, and manage tasks from any browser or mobile device — without exposing any ports or configuring a firewall.

## What it does

> **Transparency note:** The cloud relay endpoint (`api.sumeralabs.com`) is operated by SumeraLabs, the company behind ChatClaw. `chatclaw.com` is the product domain; `sumeralabs.com` is the infrastructure domain. Both are owned and operated by the same team.

ChatClaw opens two connections when enabled:

1. **Cloud relay** — an outbound WebSocket to `wss://api.sumeralabs.com/ws/agent/{api_key}`. This is how your dashboard communicates with the skill. It is a purely outbound connection and requires no inbound port forwarding.
2. **Local gateway** — a WebSocket connection to `ws://localhost:18789` for Ed25519 authentication only, plus HTTP SSE calls to `http://localhost:18789/v1/chat/completions` for all chat traffic. The HTTP endpoint is auto-enabled in `openclaw.json` on first start.

Messages flow bidirectionally in real time. User messages sent from the dashboard are forwarded to the OpenClaw agent via HTTP SSE streaming. Each token of the agent's response is relayed back to the dashboard as it is generated, producing a live typewriter effect.

## Architecture

```
ChatClaw Dashboard (browser / mobile)
        ↕  wss://api.sumeralabs.com
  ChatClaw Cloud Relay (FastAPI)
        ↕  wss://api.sumeralabs.com/ws/agent/{api_key}
  ChatClaw Skill  ←── this package
        ↕  ws://localhost:18789 (auth handshake, Ed25519)
        ↕  http://localhost:18789/v1/chat/completions (SSE streaming)
  OpenClaw Gateway
        ↕
  OpenClaw Agent (LLM)
```

## Requirements

- OpenClaw v2026.1.0 or later
- Python 3.10 or later
- `python3` available on PATH
- Packages: `websockets>=12.0`, `cryptography>=41.0`, `aiohttp>=3.9`
- A ChatClaw API key from [app.chatclaw.com](https://app.chatclaw.com)

## Installation

### Via OpenClaw Control UI (recommended)

1. Open the Control UI at `http://localhost:18789`
2. Go to **Skills → Marketplace**
3. Search for **ChatClaw**
4. Click **Install**, enter your API key, click **Enable**

> **Note:** On first enable, the skill automatically sets `gateway.http.endpoints.chatCompletions.enabled = true` in your `openclaw.json`. If the skill made that change, disabling it will revert it automatically. If `chatCompletions` was already enabled before install, the skill leaves your config unchanged on disable.

The skill starts immediately and auto-starts with OpenClaw on every subsequent boot.

### Via OpenClaw CLI

```bash
npx clawhub install chatclaw
openclaw skills enable chatclaw
openclaw skills logs chatclaw
```

Before enabling, add your API key to `openclaw.json` under `skills.entries.chatclaw.config`:

```json
"skills": {
  "entries": {
    "chatclaw": {
      "enabled": true,
      "config": {
        "api_key": "ck_your_key_here",
        "cloud_url": "wss://api.sumeralabs.com"
      }
    }
  }
}
```

## Agent-assisted setup

Your OpenClaw agent can install and configure ChatClaw for you without any manual steps.

Get the one-click setup prompt from [app.chatclaw.com/setup](https://app.chatclaw.com/setup) — it includes your API key pre-filled and full instructions to paste directly into chat.

## Configuration

| Key | Required | Default | Description |
|---|---|---|---|
| `api_key` | Yes | — | ChatClaw API key from app.chatclaw.com |
| `cloud_url` | No | `wss://api.sumeralabs.com` | WebSocket relay URL (leave default unless self-hosting) |

## Environment variables

| Variable | Description |
|---|---|
| `OPENCLAW_DATA_DIR` | Override the OpenClaw data directory. Defaults to `/data/.openclaw` on Docker/VPS or `~/.openclaw` on standard installs. |
| `CHATCLAW_CLOUD_URL` | Override the cloud relay URL. Defaults to `wss://api.sumeralabs.com`. Leave unset unless self-hosting the relay. |

## Lifecycle hooks

| Hook | Behaviour |
|---|---|
| `on_enable` | Patches `openclaw.json` to enable the `/v1/chat/completions` endpoint, then starts the cloud ↔ gateway relay loop |
| `on_disable` | Closes both WebSocket connections, stops the relay loop, and reverts the `chatCompletions` patch in `openclaw.json` if the skill was the one that enabled it |

## Reconnection behaviour

Both the cloud relay and the local gateway implement automatic reconnection with exponential backoff (5 s → 10 s → 20 s … up to 60 s). The skill never exits on a connection drop.

## Verify it is working

```bash
openclaw skills logs chatclaw
```

Expected output:
```
Connected to cloud relay ✓
Gateway authenticated ✓
Both connections established — relaying messages ✓
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Cloud connection failed` | Wrong API key or relay unreachable | Verify key at app.chatclaw.com; check network connectivity |
| `OpenClaw identity files not found` | OpenClaw not initialised or non-default install path | Run `openclaw wizard` or set `OPENCLAW_DATA_DIR` |
| `Gateway HTTP 403` | `chatCompletions` endpoint not enabled | Restart skill — `on_enable` auto-patches `openclaw.json` |
| `Gateway auth rejected` | Operator token expired | Re-pair device via `openclaw devices approve` |
| Streaming works but token count shows 0 | `sessions.json` not yet written | Send one message first; counts appear after the first completion |

## File access

This skill reads and writes the following local files:

| Path | Access | Purpose |
|---|---|---|
| `$OPENCLAW_DATA_DIR/openclaw.json` | Read + Write | Reads gateway auth token; enables `chatCompletions` HTTP endpoint on first start |
| `$OPENCLAW_DATA_DIR/identity/device.json` | Read | Ed25519 device identity for gateway authentication |
| `$OPENCLAW_DATA_DIR/identity/device-auth.json` | Read | Operator token for gateway authentication |
| `$OPENCLAW_DATA_DIR/agents/main/sessions/sessions.json` | Read | Token usage counts (input/output/context) per session |

`$OPENCLAW_DATA_DIR` defaults to `/data/.openclaw` on Docker/VPS installs and `~/.openclaw` on standard installs. It can be overridden via the `OPENCLAW_DATA_DIR` environment variable. No files outside this directory are accessed.

## External connections

This skill makes the following outbound network connections:

- `wss://api.sumeralabs.com` — ChatClaw cloud relay (authentication and message relay)
- `ws://localhost:18789` — OpenClaw gateway WebSocket (Ed25519 auth handshake only)
- `http://localhost:18789/v1/chat/completions` — OpenClaw gateway HTTP (SSE streaming chat)

No inbound ports are opened. No user data is stored by the skill itself — messages are persisted by the ChatClaw backend (Supabase) for chat history.

## License

MIT-0 (No Attribution Required)
