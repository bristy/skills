# agent-memory-system-guide

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

GitHub repository: [cjke84/agent-memory-system-guide](https://github.com/cjke84/agent-memory-system-guide)

English overview: This repository provides a practical Agent long-term memory workflow for OpenClaw and Codex. It combines a compact `MEMORY.md`, daily notes, session recovery files, and Obsidian archiving, with OpenViking as an optional enhancement rather than a hard dependency.

Canonical OpenClaw skill id: `memory-system`

## Start Here

- [English README](README_EN.md)
- [中文介绍](README_CN.md)
- [Install Skill for Agent](INSTALL.md)
- GitHub release archive: [v0.1.0](https://github.com/cjke84/agent-memory-system-guide/releases/tag/v0.1.0)
- Current published skill version: `1.0.10`

## What it is

An Agent long-term memory guide for OpenClaw and Obsidian workflows.
OpenViking is an optional enhancement for semantic recall and summary support.

## Optional enhancement

OpenViking can be added later if you want semantic recall and summary support, but it is not required for the core workflow.

## Who it is for

- Agents that need persistent memory
- Agents that should keep daily notes and distill stable facts
- Users who want Obsidian as the long-term archive

## Quick start

1. Install the skill.
2. Copy `templates/SESSION-STATE.md` and `templates/working-buffer.md`, then use them together with `MEMORY.md` and daily notes.
3. Distill stable facts into long-term memory and keep raw notes in daily files.
4. Archive stable knowledge into Obsidian.

## Memory Capture Upgrade

- Use `templates/memory-capture.md` as a low-friction end-of-task capture sheet.
- During the task, write rough notes into `working-buffer.md` under `临时决策`, `新坑`, and `待蒸馏`.
- After the task, spend 30 seconds turning those rough notes into candidate memory instead of forcing a full `MEMORY.md` rewrite.
- To bootstrap those files in a real workspace, run `python3 scripts/memory_capture.py --workspace /path/to/workspace`.

## Files

- `SKILL.md`: skill contract and workflow
- `manifest.toml`: publish metadata for OpenClaw / ClawHub style release workflows
- `INSTALL.md`: a copy-paste installation prompt for agents
- `README_EN.md` / `README_CN.md`: bilingual introductions
- `templates/SESSION-STATE.md` and `templates/working-buffer.md`: recovery templates
- `templates/memory-capture.md`: end-of-task candidate-memory template
- `templates/OBSIDIAN-NOTE.md`: Obsidian note template (frontmatter, links, embeds)
- `scripts/memory_capture.py`: bootstrap helper for memory capture files

Publish note: `manifest.toml` is the source of truth for skill versioning and the Xiaping skill id used for updates.
