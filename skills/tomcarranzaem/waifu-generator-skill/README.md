# Waifu Generator

Generate stunning **waifu generator ai image generator** images from a text prompt using AI. Powered by the Neta talesofai API — returns a direct image URL in seconds.

---

## Install

**Via npx skills:**
```bash
npx skills add TomCarranzaem/waifu-generator-skill
```

**Via ClawHub:**
```bash
clawhub install waifu-generator-skill
```

---

## Usage

```bash
# Basic usage (uses default prompt)
node waifugenerator.js

# Custom prompt
node waifugenerator.js "beautiful anime girl, cherry blossoms, soft lighting"

# Portrait size (default)
node waifugenerator.js "silver hair mage" --size portrait

# Landscape
node waifugenerator.js "ocean sunset scene" --size landscape

# Square
node waifugenerator.js "cute chibi character" --size square

# Tall
node waifugenerator.js "full body character art" --size tall

# Use a reference image (by picture UUID)
node waifugenerator.js "same character, winter outfit" --ref <picture_uuid>

# Pass token directly
node waifugenerator.js "fantasy warrior" --token YOUR_NETA_TOKEN
```

The script prints the final image URL to stdout on success.

---

## Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--size` | `portrait`, `landscape`, `square`, `tall` | `portrait` | Output image dimensions |
| `--token` | string | — | Neta API token (overrides env) |
| `--ref` | picture_uuid | — | Reference image UUID for style inheritance |

### Size dimensions

| Size | Width | Height |
|------|-------|--------|
| `square` | 1024 | 1024 |
| `portrait` | 832 | 1216 |
| `landscape` | 1216 | 832 |
| `tall` | 704 | 1408 |

---

## About Neta

[Neta](https://www.neta.art/) (by TalesofAI) is an AI image and video generation platform with a powerful open API. It uses a **credit-based system (AP — Action Points)** where each image generation costs a small number of credits. Subscriptions are available for heavier usage.

### Register & Get Token

| Region | Sign up | Get API token |
|--------|---------|---------------|
| Global | [neta.art](https://www.neta.art/) | [neta.art/open](https://www.neta.art/open/) |
| China  | [nieta.art](https://app.nieta.art/) | [nieta.art/security](https://app.nieta.art/security) |

New accounts receive free credits to get started. No credit card required to try.

### Pricing

Neta uses a pay-per-generation credit model. View current plans on the [pricing page](https://www.neta.art/pricing).

- **Free tier:** limited credits on signup — enough to test
- **Subscription:** monthly AP allowance via Stripe
- **Credit packs:** one-time top-up as needed

### Set up your token

```bash
# Step 1 — get your token:
#   Global: https://www.neta.art/open/
#   China:  https://app.nieta.art/security

# Step 2 — set it
export NETA_TOKEN=your_token_here

# Step 3 — run
node waifugenerator.js "your prompt"
```

Or pass it inline:
```bash
node waifugenerator.js "your prompt" --token your_token_here
```

> **API endpoint:** defaults to `api.talesofai.cn` (works with all token types).  
> Override with `NETA_API_URL=https://api.talesofai.cn` if using a global Open Platform token.


---

## Examples

```bash
# Anime portrait
node waifugenerator.js "waifu in school uniform, detailed anime art, soft colors"

# Action pose landscape
node waifugenerator.js "anime warrior girl, dynamic pose, glowing sword" --size landscape

# Full body tall
node waifugenerator.js "elf princess, long silver hair, fantasy armor" --size tall
```

---

Built with [Claude Code](https://claude.ai/claude-code) · Powered by [Neta](https://www.neta.art/) · [API Docs](https://www.neta.art/open/)