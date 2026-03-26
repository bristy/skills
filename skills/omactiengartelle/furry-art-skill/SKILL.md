---
name: furry-art-skill
description: Generate furry art images using the Neta AI API. Returns a direct image URL.
tools: Bash
---

# Furry Art Generator

Generate stunning furry art generator ai images from a text description. Get back a direct image URL instantly.

## When to use
Use when someone asks to generate or create furry art generator images.

## Quick start
```bash
node furryart.js "your description here"
```

## Options
- `--size` — `portrait`, `landscape`, `square`, `tall` (default: `square`)


## Token

Requires a Neta API token via `NETA_TOKEN` env var or `--token` flag.
- Global: <https://www.neta.art/open/>
- China:  <https://app.nieta.art/security>

```bash
export NETA_TOKEN=your_token_here
```

## Install
```bash
npx skills add omactiengartelle/furry-art-skill
```
