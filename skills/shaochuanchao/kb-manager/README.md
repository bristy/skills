# kb-manager

A lightweight OpenClaw skill for creating and managing a local knowledge base inside an agent workspace.

It helps you:

- initialize a standard knowledge base structure
- decide whether content is worth saving
- classify content automatically
- save knowledge as structured Markdown
- use `00_inbox` as a fallback when classification is uncertain
- organize inbox items later

This version is designed as a **publishable v1**: small enough to use, clear enough to teach, and easy to extend later.

---

## Directory structure

```text
kb-manager/
  SKILL.md
  templates/
    default-entry.md
    project-entry.md
  docs/
    classification-rules.md
    naming-rules.md
  examples/
    init.txt
    intake-article.txt
    intake-pdf.txt
    organize-inbox.txt
```

---

## What this skill does

`kb-manager` is meant to work inside a dedicated `knowledge` agent workspace.

Its main responsibilities are:

- initialize a `knowledge/` directory
- create standard subdirectories and meta files
- evaluate whether incoming content should be saved
- classify content by purpose
- format saved content with Markdown templates
- send uncertain items to `knowledge/00_inbox/`
- help organize inbox items when asked

---

## Recommended usage

Use a dedicated OpenClaw agent for knowledge management.

Example:

```bash
openclaw agents add knowledge
```

Then place this skill in the agent workspace:

```text
skills/
  kb-manager/
    SKILL.md
    templates/
    docs/
    examples/
```

---

## Standard knowledge base structure

When initialized, the skill should create:

```text
knowledge/
  00_inbox/
  01_reference/
  02_learning/
  03_projects/
  04_research/
  05_playbooks/
  06_prompts/
  07_archive/
  _meta/
```

And these meta files:

```text
knowledge/_meta/classification-rules.md
knowledge/_meta/naming-rules.md
knowledge/_meta/template.md
knowledge/_meta/intake-log.md
```

---

## Install options

### Option A: install an existing skill

If a suitable knowledge-base skill exists in ClawHub, install it there.

```bash
clawhub search "knowledge base"
clawhub install <skill-slug>
```

### Option B: add this skill manually

Copy the `kb-manager/` directory into your agent workspace:

```text
skills/kb-manager/
```

This is the simplest way to try the current version.

---

## Quick start

### 1. Create a knowledge agent

```bash
openclaw agents add knowledge
```

### 2. Add the skill

Put the `kb-manager` folder into the agent's `skills/` directory.

### 3. Start a new session with the knowledge agent

Make sure the skill is loaded in the new session.

### 4. Initialize the knowledge base

Use the example prompt from `examples/init.txt`, or send something like:

```text
Please use kb-manager to initialize a knowledge base.

Requirements:
1. Create a `knowledge/` directory in the current workspace
2. Create standard subdirectories:
   - 00_inbox
   - 01_reference
   - 02_learning
   - 03_projects
   - 04_research
   - 05_playbooks
   - 06_prompts
   - 07_archive
   - _meta
3. Create meta files for classification rules, naming rules, active template, and intake log
4. Use `templates/default-entry.md` as the default template
5. Use `templates/project-entry.md` for project-related content
6. Put uncertain items into `00_inbox`
```

---

## Common usage examples

### Save an article

Use `examples/intake-article.txt`, or:

```text
Please save this article to the knowledge base.

Requirements:
1. Decide whether it is worth saving
2. Classify it automatically
3. Use the default entry template
4. If classification is uncertain, put it into `00_inbox`
5. Output the save path, filename, and structured Markdown
```

### Save a PDF

Use `examples/intake-pdf.txt`, or:

```text
Please turn this PDF into a knowledge entry.

Requirements:
1. If it is an official document, prefer `01_reference`
2. If it is a tutorial or study material, prefer `02_learning`
3. Use the default entry template
4. Output the final path, filename, and structured Markdown
```

### Organize inbox

Use `examples/organize-inbox.txt`, or:

```text
Please organize `knowledge/00_inbox/`.

Requirements:
1. Reclassify items when confidence is high
2. Add or improve tags
3. Suggest archive or deletion for low-value items
4. Keep uncertain items in inbox
5. Output a short organization report
```

---

## Templates

### Default entry template

File:

```text
templates/default-entry.md
```

Used for most articles, documents, notes, research, prompts, and playbooks.

### Project entry template

File:

```text
templates/project-entry.md
```

Used for project-related discussions, plans, meeting notes, and design decisions.

---

## Editable files

If you want to customize behavior:

### Change intake and classification behavior

Edit:

```text
SKILL.md
```

### Change default entry structure

Edit:

```text
templates/default-entry.md
```

### Change project entry structure

Edit:

```text
templates/project-entry.md
```

### Change readable rule docs

Edit:

```text
docs/classification-rules.md
docs/naming-rules.md
```

### Change the active template after initialization

Edit:

```text
knowledge/_meta/template.md
```

---

## Classification summary

- `01_reference`: official docs, APIs, specs, product docs
- `02_learning`: tutorials, articles, learning notes
- `03_projects/<project-name>`: project notes, discussions, plans, design docs
- `04_research`: research, comparisons, investigations
- `05_playbooks`: SOPs, workflows, procedures
- `06_prompts`: prompts and reusable operating instructions
- `00_inbox`: uncertain items

---

## Notes

This release focuses on the core workflow:

- initialize
- intake
- classify
- save
- inbox fallback
- basic organization

It does **not** try to implement everything at once.

Later versions can expand into:

- stronger duplicate detection
- richer templates
- search and indexing
- exports
- reviews and maintenance flows

---

## Included files

```text
SKILL.md
templates/default-entry.md
templates/project-entry.md
docs/classification-rules.md
docs/naming-rules.md
examples/init.txt
examples/intake-article.txt
examples/intake-pdf.txt
examples/organize-inbox.txt
```
