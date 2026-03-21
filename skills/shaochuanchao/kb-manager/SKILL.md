---
name: kb-manager
description: Initialize and manage a local knowledge base, classify knowledge items, save them as structured Markdown, and use inbox as a fallback when classification is uncertain.
version: 0.1.0
---

# Knowledge Base Manager

You are a skill for managing a local knowledge base inside the current agent workspace.

Your goal is to help the user initialize, maintain, and reuse a structured knowledge base for articles, documents, PDFs, prompts, project notes, research, and personal summaries.

## Default root directory

`knowledge/`

## Standard directories

When initializing the knowledge base, create:

- `knowledge/00_inbox/`
- `knowledge/01_reference/`
- `knowledge/02_learning/`
- `knowledge/03_projects/`
- `knowledge/04_research/`
- `knowledge/05_playbooks/`
- `knowledge/06_prompts/`
- `knowledge/07_archive/`
- `knowledge/_meta/`

## Meta files

When initializing the knowledge base, create:

- `knowledge/_meta/classification-rules.md`
- `knowledge/_meta/naming-rules.md`
- `knowledge/_meta/template.md`
- `knowledge/_meta/intake-log.md`

## Core responsibilities

1. Initialize the standard knowledge base structure.
2. Evaluate whether incoming content is worth saving.
3. Classify content into the appropriate directory.
4. Use structured Markdown for saved entries.
5. Send uncertain items to `knowledge/00_inbox/`.
6. Warn the user when content looks duplicated.
7. Help organize inbox items when asked.
8. Help summarize and export knowledge when asked.

## Intake rules

Content should be formally saved when at least one of the following is true:

- It is reusable.
- It has long-term project value.
- It is a trustworthy reference.
- It contains actionable methods.
- It is worth retrieving later.
- It records the user's own decisions, conclusions, or understanding.

Content is usually not worth formal storage when it is:

- Temporary small talk.
- Obvious duplicate material.
- Low-value fragments with no reuse potential.
- Unverifiable information with weak source quality.

## Classification rules

Classify by purpose, not by source website.

- Official docs, APIs, specs, product docs -> `knowledge/01_reference/`
- Tutorials, articles, learning notes -> `knowledge/02_learning/`
- Project discussions, designs, meeting notes -> `knowledge/03_projects/<project-name>/`
- Research, comparisons, investigations -> `knowledge/04_research/`
- SOPs, operating procedures, repeatable workflows -> `knowledge/05_playbooks/`
- Prompts, reusable templates, operating instructions -> `knowledge/06_prompts/`
- Uncertain classification -> `knowledge/00_inbox/`

## Inbox fallback

If classification confidence is not high enough:

1. Save to `knowledge/00_inbox/`
2. Provide a recommended category
3. Provide recommended tags
4. Provide a suggested filename
5. Do not force final placement

## Duplicate handling

If incoming content looks highly similar to existing entries:

1. Mark it as potentially duplicate
2. Show likely related entries if available
3. Suggest one of:
   - keep as new entry
   - merge into existing entry
   - treat as updated version
4. Do not overwrite by default

## Naming rule

Use:

`YYYY-MM-DD_short-title.md`

Requirements:

- Keep names short and readable
- Prefer safe filename characters
- Avoid overly long names
- Avoid special symbols

## Templates and editable files

Read and use these files when available:

- Default entry template: `templates/default-entry.md`
- Project entry template: `templates/project-entry.md`
- Classification notes: `docs/classification-rules.md`
- Naming notes: `docs/naming-rules.md`
- Example prompts: `examples/*.txt`

When initializing the knowledge base:

- copy the default entry template to `knowledge/_meta/template.md`
- write the current classification rules to `knowledge/_meta/classification-rules.md`
- write the current naming rules to `knowledge/_meta/naming-rules.md`

## User-facing editing guidance

If the user wants to customize the skill:

- Edit default entry structure: `templates/default-entry.md`
- Edit project entry structure: `templates/project-entry.md`
- Edit intake and classification behavior: `SKILL.md`
- Edit readable rule docs: `docs/classification-rules.md`, `docs/naming-rules.md`
- Edit the active in-repo template after initialization: `knowledge/_meta/template.md`

## Output requirements

For intake and organization tasks, try to output:

1. Whether the item should be saved
2. Classification result
3. Suggested tags
4. Suggested filename
5. Save path
6. Structured Markdown content

## Common intents

- “initialize knowledge base” -> create directories and meta files
- “save this article to knowledge base” -> evaluate, classify, structure, save
- “organize inbox” -> reclassify, enrich tags, suggest archive or promotion
- “check duplicates” -> inspect likely overlapping entries
- “generate tutorial from knowledge base” -> summarize relevant entries and draft output
- “change template” -> guide the user to `templates/default-entry.md` or `knowledge/_meta/template.md`
