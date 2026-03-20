---
version: "4.0.4"
name: xhs-content-creator
description: "Generate viral Xiaohongshu notes with titles, tags, and covers. Use when drafting seed posts, writing reviews, crafting tutorials, or boosting engagement."
author: BytesAgain
homepage: https://bytesagain.com
source: https://github.com/bytesagain/ai-skills
---

# xhs-viral-note-writer

Xiaohongshu (Little Red Book) content creation toolkit. Generate note titles, body text, opening hooks, closing CTAs, emoji suggestions, hashtags, cover ideas, and posting time recommendations. All content generated locally with built-in Chinese templates.

## Commands

### `note`

Generate a complete note with title, body, hashtags, and emoji for a given topic.

```bash
scripts/script.sh note "topic"
```

### `title`

Generate multiple clickable title candidates. Returns 5-10 options using built-in title formulas.

```bash
scripts/script.sh title "topic" 5
```

### `hook`

Generate 5 opening hook styles: question, data-driven, story, pain-point, suspense.

```bash
scripts/script.sh hook "topic"
```

### `body`

Generate body text structure for a specific content style (tutorial, review, recommendation, tips).

```bash
scripts/script.sh body "topic" tutorial
```

### `ending`

Generate closing paragraphs with engagement prompts for different goals.

```bash
scripts/script.sh ending engagement
```

### `emoji`

Suggest emoji combinations organized by content category (food, beauty, travel, fitness, tech).

```bash
scripts/script.sh emoji "topic"
```

### `hashtag`

Generate relevant hashtag suggestions from built-in tag database by category.

```bash
scripts/script.sh hashtag "topic" 10
```

### `timing`

Show recommended posting times by day of week and content category.

```bash
scripts/script.sh timing
```

### `cover`

Generate cover image concept suggestions with text overlay ideas for different cover types.

```bash
scripts/script.sh cover tutorial
```

### `hotspot`

Show trending topic directions and seasonal content ideas from built-in data.

```bash
scripts/script.sh hotspot
```

### `checklist`

Run a pre-publish checklist to verify note completeness before posting.

```bash
scripts/script.sh checklist
```

### `templates`

Browse available content templates organized by category.

```bash
scripts/script.sh templates
```

### `save`

Save a generated note to local library for later use.

```bash
scripts/script.sh save "note-name" "content"
```

### `list`

List all saved notes in the local library.

```bash
scripts/script.sh list
```

### `stats`

Show usage statistics — notes created, templates used, topics covered.

```bash
scripts/script.sh stats
```

### `help`

```bash
scripts/script.sh help
```

### `version`

```bash
scripts/script.sh version
```

## Examples

```bash
# Full content creation workflow
scripts/script.sh hotspot
scripts/script.sh note "coffee shop review"
scripts/script.sh title "coffee shop review" 5
scripts/script.sh hashtag "coffee" 10
scripts/script.sh checklist
scripts/script.sh save "coffee-note" "content"
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `XHS_DIR` | No | Data directory (default: `~/.local/share/xhs-viral-note-writer/`) |

## Data Storage

All data saved in `~/.local/share/xhs-viral-note-writer/`:
- `notes/` — Saved notes
- `stats.json` — Usage statistics
- `history.log` — Generation log

## Requirements

- bash 4.0+

---

*Powered by BytesAgain | bytesagain.com | hello@bytesagain.com*
