# AlphaLens API Skill Package

This folder contains a publishable skill package for the AlphaLens API.

**Note:** This skill requires an active [AlphaLens subscription](https://alphalens.ai) with API access. Contact sales@alphalens.ai for pricing.

## Contents

- `SKILL.md`: Main skill definition used by agent runtimes
- `references/REFERENCE.md`: Endpoint mapping and workflow rules
- `references/EXAMPLES.md`: Example prompts and request shapes

## Local Use

To make this skill available locally in a supported agent runtime, copy this folder to one of:

- `~/.cursor/skills/alphalens-api/`
- `.cursor/skills/alphalens-api/`

The final path must contain `SKILL.md` directly inside the `alphalens-api` directory.

## Publish For Installer Use

If you want to install this with a repo-based installer such as:

```bash
npx skills add your-org/your-skills-repo
```

publish a repository that includes this `alphalens-api/` directory with `SKILL.md` inside it.

The safest layout for a dedicated skills repo is:

```text
your-skills-repo/
└── alphalens-api/
    ├── SKILL.md
    └── references/
        ├── REFERENCE.md
        └── EXAMPLES.md
```

## Claude Code

For Claude Code, follow that tool's skill/plugin install flow against the published repo. The exact commands can differ by runtime version, but the skill package content in this folder is the part you need to publish.
