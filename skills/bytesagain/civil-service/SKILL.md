---
version: "3.0.0"
name: Civil Service Exam
description: "Prepare for Chinese civil service exams with essays and mock interviews. Use when practicing 申论, reviewing 行测 techniques, or analyzing past papers."
author: BytesAgain
homepage: https://bytesagain.com
source: https://github.com/bytesagain/ai-skills
---
# Civil Service

Developer workflow automation tool for project lifecycle management. Provides commands for initializing projects, running checks, building, testing, deploying, managing configuration, generating templates, producing documentation, and cleaning build artifacts — all from a single CLI interface.

## Commands

| Command | Description |
|---------|-------------|
| `civil-service init` | Initialize a new project in the current working directory |
| `civil-service check` | Run lint, type-check, and test passes against the project |
| `civil-service build` | Build the project artifacts |
| `civil-service test` | Execute the full test suite |
| `civil-service deploy` | Show the deployment pipeline guide (build → test → stage → prod) |
| `civil-service config` | Display or manage project configuration (`config.json`) |
| `civil-service status` | Check overall project health and status |
| `civil-service template <name>` | Generate a code template for the given component name |
| `civil-service docs` | Generate project documentation |
| `civil-service clean` | Remove build artifacts and temporary files |
| `civil-service help` | Show the built-in help message with all commands |
| `civil-service version` | Print the current version (v2.0.0) |

## Data Storage

All operational data is stored in `~/.local/share/civil-service/` by default. You can override this by setting the `CIVIL_SERVICE_DIR` environment variable. Key files inside the data directory:

- `history.log` — timestamped log of every command executed
- `config.json` — project-level configuration (managed via `config` command)

The tool respects `XDG_DATA_HOME` if set, falling back to `$HOME/.local/share`.

## Requirements

- **Bash** 4.0+ (uses `set -euo pipefail` for strict error handling)
- **coreutils** (standard `date`, `mkdir`, `echo`)
- No external dependencies or API keys required
- Works on Linux and macOS out of the box

## When to Use

1. **Bootstrapping a new project** — run `civil-service init` to set up project scaffolding quickly from the terminal without remembering per-tool init commands
2. **Pre-commit quality gates** — use `civil-service check` as part of a Git pre-commit hook to run lint + type-check + tests before every commit
3. **CI/CD pipeline steps** — chain `civil-service build` and `civil-service test` inside your continuous integration scripts for a consistent, tool-agnostic interface
4. **Deployment checklists** — run `civil-service deploy` to get a guided walkthrough of the build → test → stage → prod pipeline so nothing gets skipped
5. **Housekeeping and cleanup** — execute `civil-service clean` to wipe build artifacts after releases, freeing disk space and resetting state

## Examples

```bash
# Initialize a new project in the current directory
civil-service init

# Run all quality checks (lint + type-check + tests)
civil-service check

# Build the project
civil-service build

# Run the test suite
civil-service test

# View the deployment guide
civil-service deploy

# Generate a code template for a component called "auth"
civil-service template auth

# Generate project documentation
civil-service docs

# Check project health
civil-service status

# Clean up build artifacts
civil-service clean

# Show version
civil-service version
```

## Configuration

Set the `CIVIL_SERVICE_DIR` environment variable to change the data directory:

```bash
export CIVIL_SERVICE_DIR="$HOME/my-project/.civil-service"
```

Default location: `~/.local/share/civil-service/`

## Output

All command output goes to stdout. Redirect to a file if needed:

```bash
civil-service status > project-health.txt
```

History is automatically logged to `$DATA_DIR/history.log` with timestamps.

---
Powered by BytesAgain | bytesagain.com | hello@bytesagain.com
