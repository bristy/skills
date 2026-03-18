# Brand Voice Architect (BVA)

A Claude skill that reverse-engineers brand voice from raw copy and turns it into a deployable system.

## What it does

- **`/analyze`** — Runs a linguistic audit on any corpus: lexical density, avg sentence length, cadence variance, emotional temperature, top keywords
- **`/synthesize`** — Builds 3 voice pillars + This/Not That logic gates + LLM-ready system prompt
- **`/audit`** — Scores any piece of content against the established voice (0–100)
- **`/pivot`** — Adapts voice for specific platforms (LinkedIn, blog, Instagram, etc.) while preserving DNA

## Files

```
brand-voice-architect/
├── SKILL.md                        # Main skill instructions
├── scripts/
│   ├── voice_analyzer.py           # Linguistic metrics engine
│   └── prompt_synthesizer.py       # LLM system prompt generator
├── references/
│   └── methodology.md              # 4-Pillar Framework, Cadence Analysis, Semantic Salience
└── evals/
    └── evals.json                  # 6 benchmark scenarios with failure criteria
```

## Installation

1. Download `brand-voice-architect.skill`
2. Go to Claude.ai → Settings → Skills
3. Upload the `.skill` file

## Usage

Once installed, trigger with phrases like:
- "analyze this website's brand voice"
- "build a voice guide for [brand]"
- "audit this blog post against our brand voice"
- "adapt this copy for LinkedIn"

## Example output

Running `/analyze` on a website returns:
- Lexical density: 62.3%
- Avg sentence length: 13.5 words
- Cadence variance (σ): 8.1
- Emotional temperature: 0.33 / 1.0
- Top keywords + prohibited/preferred lexicon

Running `/audit` scores content 0–100 across 5 dimensions:
pillar adherence (30%), lexical compliance (25%), ASL accuracy (20%), cadence variance (15%), sentiment temperature (10%).

## Built with

[Claude Skills](https://claude.ai) · Python · Anthropic API
