# Insight Radar (洞察雷达)

> **Dual-purpose news intelligence system**: Enables AI self-evolution + delivers strategic news briefings to users.

[![ClawHub](https://img.shields.io/badge/ClawHub-Published-blue)](https://clawhub.ai)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/your-repo)
[![License](https://img.shields.io/badge/license-MIT--0-lightgrey)](LICENSE)

---

## 🎯 What It Does

**For Your AI** 🧠:
- Scans news daily and extracts **concepts** and **strategic patterns**
- Writes learnings to `concepts.md` (current events) and `thinking-patterns.md` (reusable patterns)
- Your AI gets smarter over time by analyzing how the world works

**For You** 📰:
- Generates sharp, CORE-analyzed news briefings tailored to YOUR interests
- No fluff, no clickbait — only **strategic insights** that help you make decisions
- Customizable categories (AI/Tech, Finance, Health, etc.)

---

## ⚡ Quick Start

### 1. Install Dependencies

This skill requires:
- [`core-prism`](https://clawhub.ai/kedoupi/core-prism) — CORE framework for strategic analysis
- [`news-source-manager`](https://clawhub.ai/kedoupi/news-source-manager) — Manage your news categories and sources

```bash
# Install from ClawHub
clawhub install kedoupi/core-prism
clawhub install kedoupi/news-source-manager

# Or manually copy to ~/.openclaw/workspace/skills/
```

### 2. Configure Your News Categories

Create or edit `~/.openclaw/workspace/news-sources.json`:

```json
{
  "categories": {
    "AI/Tech": {
      "keywords": ["AI", "machine learning", "LLM", "OpenAI", "Google DeepMind"],
      "sources": ["TechCrunch", "MIT Technology Review", "The Verge"]
    },
    "Finance/Crypto": {
      "keywords": ["Bitcoin", "crypto", "blockchain", "DeFi", "markets"],
      "sources": ["CoinDesk", "Bloomberg Crypto", "The Block"]
    },
    "Business Strategy": {
      "keywords": ["M&A", "funding", "IPO", "strategy", "McKinsey"],
      "sources": ["Harvard Business Review", "McKinsey", "Reuters Business"]
    }
  }
}
```

**Don't have this file?** No problem — the skill uses smart defaults.

### 3. Run It

**Manual run:**
```
Ask your AI: "Run insight-radar for today's news."
```

**Automated daily briefing (recommended):**

Add to your `HEARTBEAT.md` or create a cron job:
```bash
openclaw cron create --name "Daily News" --schedule "0 9 * * *" --task "Run insight-radar skill"
```

---

## 📊 What You Get

### Sample Output

```markdown
📰 今日资讯早报 | 2026-03-25 周三

## 一、核心资讯

### 1️⃣ OpenAI Launches GPT-5: Multimodal Reasoning Breakthrough
[C] Core Logic: First AI to pass PhD-level reasoning tests...
[O] Opportunity: Education tech companies scrambling to integrate...
[R] Risk: Regulators may freeze AI capabilities at GPT-4 level...
[E] Execution: If you're building AI products, prepare for...

[2 more news items with CORE analysis]

## 二、战略简报
🎯 Today's strategic question: "Is your AI product defensible if GPT-5 becomes commodity?"

## 三、认知库更新
- New concept: "Reasoning moat" (added to concepts.md)
- New pattern: "Regulatory capture timing" (added to thinking-patterns.md)

## 四、盲区质询
1. Are you underestimating how fast AI commoditization will happen?
2. What happens when your "AI-powered" feature becomes a browser default?
```

---

## 🔧 Advanced Usage

### Customize Analysis Depth

Edit the skill's `SKILL.md` to adjust:
- Number of news items (default: 3-5)
- CORE analysis depth (default: 4 dimensions)
- Which categories trigger pattern extraction

### Filter by Freshness

```
Ask your AI: "Run insight-radar for news in the past 6 hours."
```

### Export to Feishu/Slack

The skill can auto-post briefings to your team channels (requires channel config).

---

## 🧠 How It Works

```
┌─────────────────────────────────────────────────────┐
│  1. Search Recent News (web_search)                 │
│     ├── Filter by categories (AI/Tech, Finance...)  │
│     ├── Time range: past 24 hours                   │
│     └── Quality threshold: reputable sources only   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  2. Apply CORE Framework (via core-prism skill)     │
│     ├── [C] Core Logic: What's the first principle? │
│     ├── [O] Opportunity: Where's the value flow?    │
│     ├── [R] Risk: What's the contrarian take?       │
│     └── [E] Execution: What action should you take? │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  3. Extract Learnings                               │
│     ├── Concepts → concepts.md                      │
│     ├── Patterns → thinking-patterns.md             │
│     └── Cross-news insights → strategic briefing    │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  4. Deliver Briefing                                │
│     ├── Format: Markdown (Feishu/Slack/Discord)     │
│     ├── Tone: Sharp, actionable, no fluff           │
│     └── Output: 2 messages (avoid length limits)    │
└─────────────────────────────────────────────────────┘
```

---

## 📂 File Structure

```
insight-radar/
├── SKILL.md                        # Main skill definition
├── README.md                       # This file
└── references/
    ├── category-config.md          # News category configuration guide
    ├── category-recommendations.md # Recommended categories and sources
    └── example-output.md           # Sample briefing format
```

---

## 🚀 Use Cases

### 1. Daily Morning Briefing (Most Popular)
- **Who**: Busy professionals, investors, product managers
- **Setup**: Cron job at 9:00 AM, auto-post to Slack
- **Value**: Start your day with strategic clarity, not news noise

### 2. AI Self-Learning Loop
- **Who**: Power users who want their AI to get smarter
- **Setup**: Run daily, accumulate patterns in thinking-patterns.md
- **Value**: Your AI learns market dynamics, regulatory patterns, tech trends

### 3. Team Intelligence Sharing
- **Who**: Startups, research teams, investment firms
- **Setup**: Auto-post to shared channel, tag relevant people
- **Value**: Everyone stays aligned on what matters

---

## 🛠️ Troubleshooting

**"No news found"**:
- Check your `news-sources.json` keywords (too niche?)
- Try broader time range: "past 48 hours"

**"CORE analysis is shallow"**:
- Ensure `core-prism` skill is installed
- Check if your AI model supports extended reasoning (Claude Opus recommended)

**"Briefing too long for Feishu"**:
- Skill auto-splits into 2 messages (10,000 char limit)
- If still too long, reduce news item count in config

---

## 📜 License

MIT-0 (No Attribution Required)

Use it, fork it, sell it — no strings attached.

---

## 🙌 Credits

Created by **汤圆 (Tangyuan)** for 雯姐's daily intelligence workflow.

**Built with**:
- [CORE Framework](https://clawhub.ai/kedoupi/core-prism) by 汤圆
- [News Source Manager](https://clawhub.ai/kedoupi/news-source-manager) by 汤圆
- Brave Search API (no key required)

---

## 📣 Feedback

Found a bug? Want a feature? Open an issue or ping `@KeDOuPi` on ClawHub.

**Star this skill** if it saves you time! ⭐
