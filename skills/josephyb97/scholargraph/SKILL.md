---
name: scholargraph
description: Academic literature intelligence toolkit with AI-powered search, analysis, and knowledge management. Features literature search, concept learning, gap detection, progress tracking, paper analysis, and knowledge graph building across 15+ AI providers.
metadata:
  {
    "openclaw": {
      "emoji": "📚",
      "requires": {
        "bins": ["bun"],
        "env": ["AI_PROVIDER"]
      }
    }
  }
---

# ScholarGraph - Academic Literature Intelligence Toolkit

## Overview

ScholarGraph is a comprehensive academic literature intelligence toolkit that helps researchers efficiently search, analyze, and manage academic papers using AI-powered tools.

## Features

### Core Modules (6)

1. **Literature Search** - Multi-source academic paper discovery
   - Search across arXiv, Semantic Scholar, and web sources
   - Filter by relevance, date, or citations
   - Support for multiple search sources

2. **Concept Learner** - Rapid knowledge framework construction
   - Generate structured learning cards
   - Include code examples and related papers
   - Support beginner/intermediate/advanced depth levels

3. **Knowledge Gap Detector** - Proactive blind spot identification
   - Analyze knowledge coverage in specific domains
   - Identify critical, recommended, and optional gaps
   - Provide learning recommendations and time estimates

4. **Progress Tracker** - Real-time field monitoring
   - Track research topics and keywords
   - Generate daily/weekly/monthly reports
   - Monitor trending papers and topics

5. **Paper Analyzer** - Deep paper analysis
   - Extract key contributions and insights
   - Support quick/standard/deep analysis modes
   - Generate structured analysis reports

6. **Knowledge Graph Builder** - Concept relationship visualization
   - Build interactive knowledge graphs
   - Support Mermaid and JSON output formats
   - Find learning paths between concepts

### Advanced Features (4)

7. **Compare Concepts** - Compare two concepts
   - Identify similarities and differences
   - Provide use case recommendations

8. **Compare Papers** - Compare multiple papers
   - Find common themes and differences
   - Generate synthesis analysis

9. **Critique** - Critical paper analysis
   - Identify strengths and weaknesses
   - Find research gaps and improvement suggestions
   - Support custom focus areas

10. **Learning Path** - Find optimal learning paths
    - Discover paths between concepts
    - Generate topological learning order
    - Visualize with Mermaid diagrams

## Technical Features

- **Multi-AI Provider Support**: 15+ AI providers including OpenAI, Anthropic, DeepSeek, Qwen, Zhipu AI, etc.
- **Rate Limiting**: Automatic retry and delay for API calls
- **Multiple Output Formats**: Markdown, JSON, Mermaid
- **TypeScript + Bun**: Fast and type-safe runtime
- **CLI + API**: Both command-line and programmatic interfaces

## Installation

```bash
# Clone repository
git clone https://github.com/Josephyb97/ScholarGraph.git
cd ScholarGraph

# Install dependencies
bun install

# Initialize configuration
bun run cli.ts config init
```

## Configuration

Set up your AI provider:

```bash
# Using OpenAI
export AI_PROVIDER=openai
export OPENAI_API_KEY="your-api-key"

# Using DeepSeek
export AI_PROVIDER=deepseek
export DEEPSEEK_API_KEY="your-api-key"

# Using Qwen (通义千问)
export AI_PROVIDER=qwen
export QWEN_API_KEY="your-api-key"
```

## Usage Examples

### Search Literature
```bash
lit search "transformer attention" --limit 20 --source arxiv
```

### Learn Concepts
```bash
lit learn "BERT" --depth advanced --papers --code --output bert-card.md
```

### Detect Knowledge Gaps
```bash
lit detect --domain "Deep Learning" --known "CNN,RNN" --output gaps.md
```

### Analyze Papers
```bash
lit analyze "https://arxiv.org/abs/1706.03762" --mode deep --output analysis.md
```

### Build Knowledge Graph
```bash
lit graph transformer attention BERT GPT --format mermaid --output graph.md
```

### Compare Concepts
```bash
lit compare concepts CNN RNN --output comparison.md
```

### Compare Papers
```bash
lit compare papers "url1" "url2" "url3" --output comparison.md
```

### Critical Analysis
```bash
lit critique "paper-url" --focus "novelty,scalability" --output critique.md
```

### Find Learning Path
```bash
lit path "Machine Learning" "Deep Learning" --concepts "Neural Networks" --output path.md
```

## Use Cases

### 1. Quick Field Onboarding
- Learn core concepts
- Detect prerequisite gaps
- Build knowledge graph
- Plan learning path

### 2. Deep Paper Understanding
- Analyze paper in depth
- Perform critical analysis
- Learn new concepts from paper
- Compare with related papers

### 3. Research Progress Tracking
- Monitor research topics
- Track latest papers
- Generate progress reports

### 4. Concept Comparison
- Compare technical approaches
- Evaluate different models
- Build comparison graphs

## Project Structure

```
ScholarGraph/
├── cli.ts                      # Unified CLI entry
├── config.ts                   # Configuration management
├── README.md                   # Project documentation
├── CHANGELOG.md                # Version history
├── SKILL.md                    # This file
│
├── shared/                     # Shared modules
│   ├── ai-provider.ts          # AI provider abstraction
│   ├── types.ts                # Type definitions
│   ├── validators.ts           # Parameter validation
│   ├── errors.ts               # Error handling
│   └── utils.ts                # Utility functions
│
├── literature-search/          # Literature search module
├── concept-learner/            # Concept learning module
├── knowledge-gap-detector/     # Gap detection module
├── progress-tracker/           # Progress tracking module
├── paper-analyzer/             # Paper analysis module
├── knowledge-graph/            # Knowledge graph module
│
└── test/                       # Tests and documentation
    ├── ADVANCED_FEATURES.md
    ├── TEST_RESULTS.md
    └── scripts/
```

## Supported AI Providers

### International
- OpenAI
- Anthropic (Claude)
- Azure OpenAI
- Groq
- Together AI
- Ollama (local)

### China
- 通义千问 (Qwen/DashScope)
- DeepSeek
- 智谱 AI (GLM)
- MiniMax
- Moonshot (Kimi)
- 百川 AI (Baichuan)
- 零一万物 (Yi)
- 豆包 (Doubao)

## Output Formats

### Markdown Reports
- Concept cards with definitions, components, history, applications
- Gap reports with analysis and recommendations
- Progress reports with trending topics
- Paper analyses with methods, experiments, contributions
- Comparison analyses with similarities and differences
- Critical analyses with strengths, weaknesses, and suggestions

### JSON Data
Structured data for programmatic processing

### Mermaid Diagrams
Interactive knowledge graphs and learning paths

## Requirements

- Bun 1.3+ or Node.js 18+
- AI provider API key
- Internet connection for paper search

## License

MIT License

## Links

- GitHub: https://github.com/Josephyb97/ScholarGraph
- Issues: https://github.com/Josephyb97/ScholarGraph/issues
- Discussions: https://github.com/Josephyb97/ScholarGraph/discussions

## Version

Current version: 1.0.0

## Author

ScholarGraph Team

---

*For detailed documentation, see README.md*
*For advanced features, see test/ADVANCED_FEATURES.md*
*For test results, see test/TEST_RESULTS.md*
