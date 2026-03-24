---
name: minimax-vision-search
description: Enable MiniMax image understanding and web search via MCP. Use when user wants to analyze images, describe pictures, understand image content, or search the web. This skill adds vision and search capabilities to OpenClaw using MiniMax's understand_image and web_search MCP tools. Triggers: "analyze image"、"图片理解"、"describe this image"、"图片描述"、"search web"、"网络搜索"
metadata:
  clawdis:
    requires:
      bins: [uv, uvx]
      env: [MINIMAX_API_KEY]
    install:
      - kind: brew
        formula: uv
        label: "Install uv via Homebrew (recommended)"
      - kind: pipx
        package: uv
        label: "Install uv via pipx"
---

# MiniMax Vision & Search MCP

Analyze images and search the web using MiniMax's MCP tools.

## Prerequisites

1. **uvx** must be installed (recommended via Homebrew):
   ```bash
   brew install uv
   ```

2. **MINIMAX_API_KEY** must be set in environment:
   ```bash
   export MINIMAX_API_KEY=your_api_key
   ```

## Quick Start

1. Install uv: `brew install uv` (macOS recommended)
2. Set API key: `export MINIMAX_API_KEY=your_token_plan_key`
3. Run image analysis: `python3 scripts/understand_image.py <image_path> <prompt>`
4. Run web search: `python3 scripts/web_search.py <query>`

## Tools

### Image Understanding
```
python3 scripts/understand_image.py <image_path_or_url> "<prompt>"
```

### Web Search
```
python3 scripts/web_search.py <query>
```

## Image Sources

- Local files: `/path/to/image.jpg`
- URLs: `https://example.com/image.jpg`
- Telegram images (auto-saved to `~/.openclaw/media/inbound/`)

## Tips

- Use Telegram to send images → bot auto-saves locally
- Webchat images NOT supported (MiniMax rejects image input)
- See [references/troubleshooting.md](references/troubleshooting.md) for issues
