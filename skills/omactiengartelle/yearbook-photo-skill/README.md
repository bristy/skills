# AI Yearbook Photo Generator

Generate classic ai yearbook photo generator images from a text description using AI. Powered by the Neta talesofai API, this skill returns a direct image URL in seconds — no setup beyond a token required.

---

## Install

**Via npx skills:**
```bash
npx skills add omactiengartelle/yearbook-photo-skill
```

**Via ClawHub:**
```bash
clawhub install yearbook-photo-skill
```

---

## Usage

```bash
# Default prompt (classic 1990s yearbook portrait)
node yearbookphoto.js

# Custom subject/description
node yearbookphoto.js "1990s high school yearbook portrait photo of Emma, soft studio lighting, formal attire"

# With size option
node yearbookphoto.js "senior portrait of a student" --size square

# With a reference image UUID
node yearbookphoto.js "yearbook portrait of Alex" --ref <picture_uuid>

# Pass token directly
node yearbookphoto.js "yearbook photo" --token YOUR_NETA_TOKEN
```

The script prints a single image URL to stdout on success.

---

## Options

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--size` | `portrait`, `landscape`, `square`, `tall` | `portrait` | Output image dimensions |
| `--token` | string | — | Neta API token (overrides env/file) |
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
node yearbookphoto.js "your prompt"
```

Or pass it inline:
```bash
node yearbookphoto.js "your prompt" --token your_token_here
```

> **API endpoint:** defaults to `api.talesofai.com` (Open Platform tokens).  
> China users: set `NETA_API_BASE_URL=https://api.talesofai.com` to use the China endpoint.


---

## Default prompt

```
1990s high school yearbook portrait photo of {subject}, professional school photography studio, neutral background, soft studio lighting, formal attire, genuine smile, film grain texture, classic yearbook aesthetic
```

---

Built with [Claude Code](https://claude.ai/claude-code) · Powered by [Neta](https://www.neta.art/) · [Open Portal](https://www.neta.art/open/)