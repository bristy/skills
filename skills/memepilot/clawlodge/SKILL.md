---
name: clawlodge
description: Use ClawLodge to search, inspect, download, and publish OpenClaw workspaces. Trigger when the user wants to find reusable workspaces, compare versions, fetch a workspace zip, or publish the current workspace to clawlodge.com.
---

# ClawLodge

Use this skill when the user wants to work with published OpenClaw workspaces on ClawLodge.

Prefer the `clawlodge` CLI over manual browser steps. The default origin is `https://clawlodge.com`, so you usually do not need `--origin`.

## Available commands

```bash
clawlodge --version
clawlodge login
clawlodge whoami
clawlodge search "memory"
clawlodge show openclaw-config
clawlodge get openclaw-config
clawlodge download openclaw-config --version 0.13.1 --out /tmp/openclaw-config.zip
clawlodge favorite openclaw-config
clawlodge unfavorite openclaw-config
clawlodge comment openclaw-config --content "Useful setup"
clawlodge report openclaw-config --reason "Contains broken publish output"
clawlodge pack
clawlodge publish
```

## When to use what

- Use `clawlodge search "<query>"` to find candidate workspaces.
- Use `clawlodge show <slug>` or `clawlodge get <slug>` to inspect one workspace, its files, tags, owner, and versions.
- Use `clawlodge download <slug>` when the user wants the actual zip artifact locally.
- Use `clawlodge favorite <slug>` or `clawlodge unfavorite <slug>` for like or unlike actions.
- Use `clawlodge comment <slug> --content "..."` to post a comment.
- Use `clawlodge report <slug> --reason "..."` to submit negative feedback.
- Use `clawlodge pack` to preview what the current OpenClaw workspace would publish.
- Use `clawlodge publish` only after the user clearly wants to publish.

Decision rule:

- If the user wants metadata, file lists, versions, author, tags, or source repo, use `show` or `get`.
- If the user wants a local file, installation artifact, zip package, or anything saved to disk, use `download`.
- Do not use `get` or `show` when the request mentions `save`, `download`, `zip`, `extract`, `install`, or an output path.

## Auth model

These read actions do not require login:

- `search`
- `show`
- `get`
- `download`

These write actions require a PAT:

- `favorite`
- `unfavorite`
- `comment`
- `report`
- `publish`

## Search workflow

1. Run `clawlodge search "<query>"`.
2. Read the JSON output and compare:
   - `slug`
   - `name`
   - `summary`
   - `tags`
   - `latest_version`
3. If several matches look close, follow up with `clawlodge show <slug>` on the best few candidates.

## Inspect workflow

Use `show` or `get` when the user wants details before deciding.

```bash
clawlodge show cft0808-edict
clawlodge get openclaw-config
```

Look for:

- `result.source_url` to verify the original repository
- `result.latest_version` to identify the default downloadable version
- `result.versions` to compare release history
- `result.latest.workspace_files` to understand what is actually shared

Hard rules:

- `show` and `get` are read-only metadata commands.
- `show` and `get` do not create files or directories.
- Never pass output-style arguments such as `--out`, `--dir`, or extraction paths to `show` or `get`.
- If the user asks for a local copy, switch to `download`.

## Download workflow

Use `download` when the user wants to install, inspect offline, or reuse a workspace.

```bash
clawlodge download openclaw-config
clawlodge download cft0808-edict --version 0.1.1 --out /tmp/cft0808-edict.zip
```

Notes:

- If `--version` is omitted, the CLI downloads the latest published version.
- If `--out` is omitted, the file is saved as `<slug>-<version>.zip` in the current directory.

Hard rules:

- Always use `download` for saved artifacts.
- Use `--out` only with `download`.
- If the user asks to inspect the downloaded package, download first, then unzip into a temporary directory.

## Local backup workflow

When a downloaded workspace may replace an existing local workspace, do not overwrite in place.

Preferred sequence:

1. Download to a temporary zip path.
2. Create a timestamped backup of the current workspace.
3. Extract the new workspace into a separate temporary directory.
4. Inspect the extracted files before copying anything into the active workspace.
5. Only replace files after explicit user intent.

Example shell flow:

```bash
clawlodge download openclaw-config --out /tmp/openclaw-config.zip
cp -R ~/.openclaw/workspace ~/.openclaw/workspace.backup-$(date +%Y%m%d-%H%M%S)
mkdir -p /tmp/openclaw-config
unzip -o /tmp/openclaw-config.zip -d /tmp/openclaw-config
```

Rules:

- Never unpack a downloaded workspace directly into `~/.openclaw/workspace`.
- Never delete the current workspace before the backup exists.
- Prefer side-by-side comparison over in-place replacement.

## Feedback workflow

Use write actions only after explicit user intent.

```bash
clawlodge favorite openclaw-config
clawlodge unfavorite openclaw-config
clawlodge comment openclaw-config --content "Helpful memory layout and publish flow."
clawlodge report openclaw-config --reason "README still references an outdated setup step"
```

## Publish workflow

Only publish after explicit user intent.

1. Confirm the current CLI identity:

```bash
clawlodge whoami
```

2. If needed, log in:

```bash
clawlodge login
```

3. Preview the payload:

```bash
clawlodge pack
```

4. Publish:

```bash
clawlodge publish
```

## Safety rules

- Treat `publish` as a write action. Do not run it unless the user clearly asks.
- Treat `favorite`, `comment`, and `report` as write actions. Do not run them unless the user clearly asks.
- Treat `login` as credential setup. Do not ask the user to paste tokens into shared logs.
- Prefer `show` before `download` when you are not yet sure the slug is correct.
- Prefer backup and staged extraction before any local workspace replacement.
- Never invent `get` or `show` flags for output directories or downloads.
