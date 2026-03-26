# Furry Art Generator

Generate stunning **furry art generator ai** images from a text prompt — powered by the Neta talesofai API. Get back a direct image URL in seconds.

---

## Install

```bash
# Via npx skills
npx skills add omactiengartelle/furry-art-skill

# Via ClawHub
clawhub install furry-art-skill
```

---

## Usage

```bash
# Basic — uses built-in default prompt
node furryart.js

# Custom prompt
node furryart.js "red fox warrior in armor, fantasy setting, detailed fur"

# Specify size
node furryart.js "wolf mage casting spells" --size portrait

# Reference an existing image for style inheritance
node furryart.js "same character, different pose" --ref <picture_uuid>
```

The script prints the final image URL to stdout and progress info to stderr.

---

## Options

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--size` | `square`, `portrait`, `landscape`, `tall` | `square` | Output image dimensions |
| `--token` | string | — | Override the API token for this run |
| `--ref` | picture_uuid | — | Inherit style/params from an existing image |

### Size dimensions

| Name | Width | Height |
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
node furryart.js "your prompt"
```

Or pass it inline:
```bash
node furryart.js "your prompt" --token your_token_here
```

> **API endpoint:** defaults to `api.talesofai.com` (Open Platform tokens).  
> China users: set `NETA_API_BASE_URL=https://api.talesofai.com` to use the China endpoint.


---

## Default prompt

When no prompt is provided, the skill uses:

> anthropomorphic animal character, furry art style, detailed fur texture, expressive eyes, vibrant colors, clean linework, digital illustration

---

## Example output

```
Submitting: "red fox knight in enchanted forest" [square 1024×1024]
Task: abc123-def456-...
Waiting… attempt 3/90 [PENDING]
https://cdn.talesofai.cn/artifacts/abc123.png
```

---

Built with [Claude Code](https://claude.ai/claude-code) · Powered by [Neta](https://www.neta.art/) · [Open Portal](https://www.neta.art/open/)