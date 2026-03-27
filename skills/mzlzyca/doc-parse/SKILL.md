---
name: doc-parse
description: "Doc Parse - parse Word (.doc/.docx) documents into structured Markdown using MinerU. Preserves document hierarchy: headings, lists, tables, and paragraphs."
homepage: https://mineru.net
metadata: {"openclaw": {"emoji": "📄", "requires": {"bins": ["mineru-open-api"], "env": ["MINERU_TOKEN"]}, "primaryEnv": "MINERU_TOKEN", "install": [{"id": "npm", "kind": "node", "package": "mineru-open-api", "bins": ["mineru-open-api"], "label": "Install via npm"}, {"id": "go", "kind": "go", "package": "github.com/opendatalab/MinerU-Ecosystem/cli/mineru-open-api", "bins": ["mineru-open-api"], "label": "Install via go install", "os": ["darwin", "linux"]}]}}
---

# Doc Parse

Parse Word (.doc/.docx) documents into structured Markdown using MinerU. Preserves document hierarchy including headings, lists, tables, and paragraphs.

## Install

```bash
npm install -g mineru-open-api
# or via Go (macOS/Linux):
go install github.com/opendatalab/MinerU-Ecosystem/cli/mineru-open-api@latest
```

## Quick Start

```bash
# Quick parse from .docx (no token required)
mineru-open-api flash-extract report.docx

# Save structured Markdown to directory
mineru-open-api flash-extract report.docx -o ./out/

# Parse .doc file (requires token)
mineru-open-api extract report.doc -o ./out/

# With language hint
mineru-open-api extract report.docx --language en -o ./out/
```

## Authentication

No token needed for `flash-extract` on `.docx`. Token required for `.doc`:

```bash
mineru-open-api auth             # Interactive token setup
export MINERU_TOKEN="your-token" # Or via environment variable
```

Create token at: https://mineru.net/apiManage/token

## Capabilities

- Supported input: .doc, .docx (local file or URL)
- `.docx`: supports `flash-extract` (no token, max 10 MB / 20 pages) and `extract`
- `.doc`: requires `extract` with token
- Output preserves document structure as Markdown hierarchy
- Language hint with `--language` (default: `ch`, use `en` for English)

## Notes

- `.doc` requires `extract` with token; `.docx` supports `flash-extract` for quick parsing
- Output goes to stdout by default; use `-o <dir>` to save to a file or directory
- All progress/status messages go to stderr; document content goes to stdout
- MinerU is open-source by OpenDataLab (Shanghai AI Lab): https://github.com/opendatalab/MinerU
