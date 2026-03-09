# Perplexica Search Skill 🔍

AI-powered search using your local Perplexica instance. Combines web search with LLM reasoning for accurate answers with cited sources.

## Installation

```bash
# Using ClawHub (when published)
clawhub install perplexica-search

# Manual install
git clone <repo> ~/.openclaw/skills/perplexica-search
```

## Prerequisites

- Perplexica running locally (default: `http://localhost:3000`)
- At least one chat model provider configured in Perplexica
- Python 3.8+

## Quick Start

```bash
# Basic search
python3 scripts/perplexica_search.py "What is quantum computing?"

# Quality mode with academic sources
python3 scripts/perplexica_search.py "Transformer architecture 2024" --mode quality --sources academic

# JSON output for programmatic use
python3 scripts/perplexica_search.py "Python async best practices" --json
```

## Usage

```
usage: perplexica_search.py [-h] [-u URL] [-m {speed,balanced,quality}]
                            [-s SOURCES] [--chat-model CHAT_MODEL]
                            [--embedding-model EMBEDDING_MODEL]
                            [-i INSTRUCTIONS] [--history HISTORY] [-j]
                            [--stream]
                            query

AI-powered search using local Perplexica instance

positional arguments:
  query                 Search query

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     Perplexica instance URL (default: http://localhost:3000)
  -m {speed,balanced,quality}, --mode {speed,balanced,quality}
                        Optimization mode
  -s SOURCES, --sources SOURCES
                        Search sources: web,academic,discussions
  --chat-model CHAT_MODEL
                        Chat model key (e.g., gpt-4o-mini)
  --embedding-model EMBEDDING_MODEL
                        Embedding model key
  -i INSTRUCTIONS, --instructions INSTRUCTIONS
                        Custom system instructions
  --history HISTORY     Conversation history as JSON array
  -j, --json            Output raw JSON
  --stream              Enable streaming
```

## Examples

### Quick Fact Check
```bash
python3 scripts/perplexica_search.py "Who won the 2024 Nobel Prize in Physics?"
```

### Academic Research
```bash
python3 scripts/perplexica_search.py "CRISPR gene editing advances" --sources academic --mode quality
```

### Technical Deep Dive
```bash
python3 scripts/perplexica_search.py "Rust memory safety vs C++" \
  --instructions "Focus on practical examples and performance comparisons"
```

### Multi-Turn Conversation
```bash
python3 scripts/perplexica_search.py "Explain more about that" \
  --history '[["human", "What is quantum entanglement?"], ["assistant", "Quantum entanglement is..."]]'
```

## Configuration

Create `config.json` in the skill directory:

```json
{
  "perplexica_url": "http://localhost:3000",
  "default_chat_model": "llama3.1:latest",
  "default_embedding_model": "nomic-embed-text",
  "default_mode": "balanced",
  "default_sources": ["web"]
}
```

## Publishing

```bash
# Login to ClawHub
clawhub login

# Publish
clawhub publish . --slug perplexica-search --name "Perplexica Search" --version 1.0.0 --changelog "Initial release"
```

## License

MIT

## Links

- [Perplexica GitHub](https://github.com/ItzCrazyKns/Perplexica)
- [ClawHub](https://clawhub.com)
