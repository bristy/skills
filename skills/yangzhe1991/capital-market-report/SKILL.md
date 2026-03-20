---
name: capital-market-report
description: Generate high-signal, impact-driven capital market anomaly and rumor reports. Focuses on actionable business signals, expectation-breaking news, and deep logical deduction rather than routine index reading. Uses local scanners to digest Chinese and global financial media, Reddit, and Twitter. Features strict market-isolation rules to prevent cross-border misattribution and requires real source URLs.
---

# Capital Market Report (High-Signal Anomaly Edition)

Generates forward-looking business deduction reports based on an "Absolute Impact Threshold." This skill abandons traditional macroeconomic index reading (e.g., "Nasdaq down 1%"), shifting instead to deep scraping of domestic and international forums, news, and social media to lock in supply-chain anomalies and earnings explosion points with extreme expectation gaps.

## Core Philosophy (Absolute Impact Threshold)

1. **Zero Routine Data**: No longer reports routine market data like index points or daily percentage changes. Focuses entirely on nuclear-level anomalies in the business world.
2. **Dynamic Capacity**: Abolishes mechanical rules like "must have 3-5 items." If only 2 events meet the threshold today, report 2; if 8 major global supply-chain-shaking news break, report all 8.
3. **Core on Selected Assets, Inclusive of Global Leaders**: While deeply scanning specific target assets (e.g., Chinese ADRs, A/HK tech stocks, AI/consumer/EV supply chains), it absolutely must not miss strategic turning points from global tech giants (e.g., the "Magnificent Seven" or core global AI leaders).

## Execution Pipeline & Toolchain

### Step 1: Launch Underlying Scanners

You must run the following information scraping tools:

**1. Chinese Financial Core News Scraper** (Scraping domestic sources like Cailianshe, Wall Street CN, Sina Finance):
```bash
cd ~/.openclaw/skills/capital-market-report; uv run scripts/news-processor.py --delta --delta
```

**2. Overseas Anomaly & Rumor Radar** (Monitoring Reddit WSB, CoinGecko, Yahoo Finance movers, Google News rumors):
*(Note: Requires the `stock-analysis` skill to be installed)*
```bash
uv run ~/.openclaw/skills/stock-analysis/scripts/hot_scanner.py
uv run ~/.openclaw/skills/stock-analysis/scripts/rumor_scanner.py
```

### Step 2: Comprehensive Inclusion of Major Market Events

From the scraped results, retain news based on the following rules:
- **Include All High-Attention Events**: Any news heavily discussed by the market (e.g., major AI model releases like Claude/GPT updates, big tech earnings, macro data, geopolitical shifts) **MUST** be included, even if they perfectly meet market expectations. Do not filter out highly focused topics.
- **Retain Anomalies**: Keep extremely strong earnings reversals, supply-chain-level product delays, or major rumors.
- **Red Line**: Do not aggressively filter out major news just because it lacks a "shock" factor. If the market cares, it goes in the report.

### Step 3: Mandatory Source Tracking (Real URL Verification)

**Red Line**: Every piece of news reported must include a real source URL `[Read Original](URL)`. 
- The URL is natively extracted and provided by the underlying `news-processor.py` script from the original RSS or HTML feeds.
- Do not invent URLs or use generic domain homepages. Rely on the exact link returned by the scripts.

### Step 4: Isolated Deduction & Localization

Perform strict logical deduction on the selected events:
- **Market Isolation Red Line**: Rigorously distinguish the "country/market" where the anomaly occurred. For example, a surge in US domestic airfares can only be deduced as bullish for US airlines and US OTAs; it **absolutely cannot be forcefully applied** to Chinese companies like Trip.com.
- If the event is a shock to an overseas giant (e.g., Honda taking a massive loss), the deduction must clarify whether the logical link to its global competitors genuinely holds up.
- **Language Localization**: Although this skill description is in English, the final report generated **MUST** be written in the user's primary conversational language (e.g., if the user communicates in Chinese, the report must be in Chinese).

### Step 5: Rolling Updates & Delta Extraction (Temporal Event Tracking)

For multi-source concurrency or rolling reports on the same market event, **DO NOT simply discard duplicate news items**. Instead, apply strict "Delta Extraction" tracking based on time:
- **Definition of Delta**: "Delta" means **new information added since the last generated report** (temporal delta), NOT whether the news broke market expectations.
- **Baseline Comparison**: You MUST read the previous report from `~/.openclaw/workspace-group/memory/last_capital_market_report.md` before generating the new report. Use it to compare newly scraped news against the *previous report's* coverage of the same event.
- **Extract Delta (New Information)**: Specifically pull out any new data, new official statements, or new market reactions that weren't in the previous report.
- **Visual Labeling**: Use tiered labeling for event tracking updates. For example:
  - `🔴 [增量更新 - 关键细节/市场反应]` for news containing substantial new facts since the last report.
  - `⚪ [跟进报道 - 与上次相比无新增]` for news that merely repeats facts already covered in the previous report.
- **Save State**: After generating the new report, you MUST overwrite `~/.openclaw/workspace-group/memory/last_capital_market_report.md` with the exact text of the new report so it is available for the next run.

## Report Output Format

The output must be minimalist, sharp, and deduction-driven:

```markdown
📊 **Capital Market Absolute Impact Report | YYYY-MM-DD HH:MM**

⚠️ **Core Anomaly Alerts (Potential Expectation Gaps & Strategic Inflection Points)**

- **[Category/Theme] Core Event Title (Marked with Country/Market)**
  **Source & Link**: News Source Name ([Read Original](Real_Article_URL))
  **Core**: A single sentence highlighting the crux of the anomaly.
  **Rigorous Deduction**: 1-2 sentences pointing out the bullish/bearish impact and specific stock tickers or supply chains. The logic must be airtight.

- **[Category/Theme] Core Event Title (Marked with Country/Market)**
  **Source & Link**: News Source Name ([Read Original](Real_Article_URL))
  **Core**: ...
  **Rigorous Deduction**: ...
```