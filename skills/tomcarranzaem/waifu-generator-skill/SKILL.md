---
name: waifu-generator-skill
description: Generate waifu generator images using the Neta AI API. Returns a direct image URL.
tools: Bash
---

# Waifu Generator

Generate stunning waifu generator ai image generator images from a text description. Get back a direct image URL instantly.

## When to use
Use when someone asks to generate or create waifu generator ai image generator images.

## Quick start
```bash
node waifugenerator.js "your description here"
```

## Options
- `--size` — `portrait`, `landscape`, `square`, `tall` (default: `portrait`)


## Token

Requires a Neta API token via `NETA_TOKEN` env var or `--token` flag.
- Global: <https://www.neta.art/open/>
- China:  <https://app.nieta.art/security>

```bash
export NETA_TOKEN=your_token_here
```

## Install
```bash
npx skills add TomCarranzaem/waifu-generator-skill
```
