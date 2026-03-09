---
name: perplexica-search
description: AI-powered search using your local Perplexica instance. Combines web search with LLM reasoning for accurate answers with cited sources. Use when user asks to "search with Perplexica", "ask Perplexica", "deep search", "research with sources", or wants AI search with citations.
version: 1.0.0
homepage: https://github.com/ItzCrazyKns/Perplexica
metadata:
  openclaw:
    emoji: "🔍"
    requires:
      bins:
        - curl
        - jq
    install: []
    files:
      - "scripts/*"

---

# Perplexica Search Skill

AI-powered search using your local Perplexica instance. This skill wraps Perplexica's search API to provide intelligent search results with cited sources.

## When to Use

Use this skill when the user wants to:

- Search the web with AI-powered reasoning
- Get answers with cited sources
- Perform deep research on a topic
- Search academic papers or discussions
- Use a local, privacy-focused search engine
- Get structured search results with metadata

## Prerequisites

- Perplexica running locally (default: `http://localhost:3000`)
- At least one chat model provider configured in Perplexica
- At least one embedding model configured

## Usage

```bash
# Basic search
python3 {baseDir}/scripts/perplexica_search.py "What is quantum computing?"

# Specify optimization mode
python3 {baseDir}/scripts/perplexica_search.py "Latest AI developments" --mode quality

# Search specific sources
python3 {baseDir}/scripts/perplexica_search.py "Machine learning papers" --sources academic

# Custom Perplexica URL
python3 {baseDir}/scripts/perplexica_search.py "Climate change research" --url http://localhost:3000

# JSON output for programmatic use
python3 {baseDir}/scripts/perplexica_search.py "Python best practices" --json

# With conversation history
python3 {baseDir}/scripts/perplexica_search.py "Explain more" --history '[["human", "What is Python?"], ["assistant", "Python is a programming language..."]]'

# Custom system instructions
python3 {baseDir}/scripts/perplexica_search.py "Explain Rust" --instructions "Focus on memory safety and performance"
```

### CLI Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `query` | | *(required)* | The search query |
| `--url` | `-u` | `http://localhost:3000` | Perplexica instance URL |
| `--mode` | `-m` | `balanced` | Optimization mode: `speed`, `balanced`, `quality` |
| `--sources` | `-s` | `web` | Search sources: `web`, `academic`, `discussions` (comma-separated) |
| `--chat-model` | | `auto` | Chat model key (e.g., `gpt-4o-mini`, `llama3.1:latest`) |
| `--embedding-model` | | `auto` | Embedding model key (e.g., `text-embedding-3-large`) |
| `--instructions` | `-i` | `None` | Custom system instructions |
| `--history` | | `None` | Conversation history as JSON array |
| `--json` | `-j` | `off` | Output raw JSON instead of formatted summary |
| `--stream` | | `off` | Enable streaming response |

## How It Works

1. **Fetch Providers**: Calls `/api/providers` to get available chat and embedding models
2. **Auto-Select Models**: If not specified, selects the first available chat and embedding models
3. **Execute Search**: POSTs to `/api/search` with query, models, and options
4. **Format Results**: Displays answer with sources, citations, and metadata

## Output Structure

### Human-Readable Summary

```
🔍 Query: What is Perplexica?
⚡ Mode: balanced | Sources: web

📄 Answer:
Perplexica is an AI-powered search engine that...

📚 Sources:
[1] Title - https://example.com/page1
[2] Title - https://example.com/page2
```

### JSON Output

```json
{
  "query": "What is Perplexica?",
  "mode": "balanced",
  "sources": ["web"],
  "answer": "Perplexica is...",
  "sources_used": [
    {
      "title": "Page Title",
      "url": "https://example.com",
      "content": "Snippet..."
    }
  ],
  "model_used": "gpt-4o-mini",
  "took_ms": 1234
}
```

## Configuration

Create a `config.json` in the skill directory:

```json
{
  "perplexica_url": "http://localhost:3000",
  "default_chat_model": "llama3.1:latest",
  "default_embedding_model": "nomic-embed-text",
  "default_mode": "balanced",
  "default_sources": ["web"]
}
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/providers` | GET | List available model providers |
| `/api/search` | POST | Execute search query |

## Error Handling

- **Connection Error**: Perplexica instance unreachable — check URL and that it's running
- **No Providers**: No chat models configured — configure at least one provider in Perplexica settings
- **Invalid Model**: Specified model not found — use `--json` to see available models
- **Timeout**: Search took too long — try `--mode speed` or reduce query complexity

## Examples

### Quick Fact Check
```bash
python3 scripts/perplexica_search.py "Who won the 2024 Nobel Prize in Physics?"
```

### Research with Academic Sources
```bash
python3 scripts/perplexica_search.py "Transformer architecture improvements 2024" --sources academic --mode quality
```

### Technical Documentation Search
```bash
python3 scripts/perplexica_search.py "Python async await best practices" --instructions "Focus on Python 3.10+ examples"
```

## Publishing to ClawHub

To publish this skill to ClawHub:

```bash
cd ~/.openclaw/skills/perplexica-search
clawhub publish . --slug perplexica-search --name "Perplexica Search" --version 1.0.0 --changelog "Initial release"
```

## Security & Privacy

- **Local First**: All requests go to your local Perplexica instance
- **No Data Exfiltration**: Search queries stay on your machine
- **Configurable Models**: Use local LLMs (Ollama) or cloud providers — your choice
- **No API Keys**: Uses Perplexica's configured providers

## Limitations

- Requires Perplexica to be running locally
- Search quality depends on configured models and SearXNG setup
- Streaming mode requires additional client-side handling

## External Endpoints

| Endpoint | Data Sent | Purpose |
|----------|-----------|---------|
| `http://localhost:3000/api/providers` | None | Fetch available model providers |
| `http://localhost:3000/api/search` | Query, model selections, sources | Execute AI-powered search |

All requests go to your local Perplexica instance. Perplexica itself may make external requests to search engines (SearXNG, Tavily, Exa) and LLM providers based on your configuration.

## Trust Statement

By installing this skill, you trust that: (1) the skill will make HTTP requests to your local Perplexica instance at the configured URL, and (2) Perplexica will handle search and LLM requests according to its own configuration. No data is sent to third parties by this skill directly. Only install if you are running Perplexica locally.
