# Waifu Generator

Generate stunning waifu generator ai image generator images from any text description using AI. Powered by the Neta talesofai API — get a direct image URL back in seconds.

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
node waifugenerator.js "cute anime girl with silver hair, cherry blossoms"

# With size option
node waifugenerator.js "warrior princess, epic pose" --size landscape

# With explicit token
node waifugenerator.js "magical fox spirit" --token YOUR_NETA_TOKEN
```

The script prints the image URL to stdout when generation completes.

---

## Options

| Option    | Values                                      | Default    | Description               |
|-----------|---------------------------------------------|------------|---------------------------|
| `--size`  | `portrait`, `landscape`, `square`, `tall`   | `portrait` | Output image dimensions   |
| `--token` | string                                      | _(auto)_   | Neta API token (optional) |

### Size dimensions

| Size        | Width | Height |
|-------------|-------|--------|
| `portrait`  | 832   | 1216   |
| `landscape` | 1216  | 832    |
| `square`    | 1024  | 1024   |
| `tall`      | 704   | 1408   |

---

## Token Setup

The script resolves your `NETA_TOKEN` in this order:

1. `--token` CLI flag
2. `NETA_TOKEN` environment variable
3. `~/.openclaw/workspace/.env` file
4. `~/developer/clawhouse/.env` file

**Recommended:** add to your shell profile or `.env` file:
```bash
export NETA_TOKEN=your_token_here
```

Or place in `~/.openclaw/workspace/.env`:
```
NETA_TOKEN=your_token_here
```

---

## Examples

```bash
# Portrait waifu (default)
node waifugenerator.js "elegant maid, soft lighting, pastel colors"

# Landscape scene
node waifugenerator.js "samurai girl at sunset" --size landscape

# Square avatar
node waifugenerator.js "chibi dragon girl, big eyes" --size square

# Tall full-body
node waifugenerator.js "tall elf ranger, forest background" --size tall
```

---

Built with Claude Code · Powered by Neta
