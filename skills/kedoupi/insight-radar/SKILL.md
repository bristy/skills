---
name: insight-radar
description: Dual-purpose news intelligence system - (1) AI self-evolution: extracts strategic patterns from news, writes to thinking-patterns.md for permanent cognitive upgrades. (2) User learning: generates CORE-analyzed news briefings tailored to user's interests. Supports customizable news categories (AI/tech, finance, health, etc.). Use when scheduled daily news scanning or analyzing breaking trends.
dependencies:
  - core-prism
  - news-source-manager
config:
  reads:
    - USER.md  # For personalizing news analysis
    - memory/news-sources.json  # User's news category preferences
  writes:
    - memory/knowledge-base/concepts.md  # Current events and tech developments
    - memory/knowledge-base/thinking-patterns.md  # Reusable strategic patterns (occasional)
  env:
    - FEISHU_APP_TOKEN  # Optional: For auto-posting to Feishu
    - NOTION_API_KEY  # Optional: For Notion integration
---

# Insight Radar (洞察雷达)

**Two modes, one skill:**

## 🧠 For AI Self-Evolution
Your AI scans news daily, extracts **concepts and occasional strategic patterns** (概念与战略模式), and writes them to knowledge base. 

**What your AI learns**:
- **Concepts** (主要) → `concepts.md`: Current events, tech developments, market shifts (有时效性但值得记录)
- **Strategic patterns** (偶尔) → `thinking-patterns.md`: Only when news reveals a reusable pattern (e.g., "infrastructure play pattern")

**Why concepts, not mental models?**: News has a shelf life. We capture what's happening NOW (concepts) rather than timeless frameworks (mental models). But occasionally, multiple news items reveal a reusable pattern — that goes into thinking-patterns.

## 📰 For User Learning
You get sharp, CORE-analyzed news briefings tailored to YOUR interests:
- **[C] Core Logic**: First-principles insight (not what happened, but WHY it matters)
- **[O] Opportunity**: Where is value flowing? Who's winning?
- **[R] Risk**: Contrarian take, hidden black swans
- **[E] Execution**: What should YOU do today?

**Output**: Not a news feed. Strategic intelligence.

---

## 🎯 Why Use This Skill?

**Scenario 1: You care about your AI's evolution** (推荐 ✨)
- Your AI reads 1000 news items → extracts 50 strategic patterns → becomes a trend forecaster
- Next time you ask "should I invest in X?", it applies patterns from past events
- **Value**: Your AI becomes a real-time strategic advisor

**Scenario 2: You just want curated news** (也完全OK 😊)
- You get CORE-analyzed briefings in your domain (AI, finance, health, etc.)
- Save hours of doom-scrolling; get insights in 5 minutes
- **Value**: High signal-to-noise ratio news consumption

**Scenario 3: Both!** (最佳组合)
- You learn + your AI learns = compound intelligence growth

**Note for "I don't care if my AI gets smarter" users**:  
That's fine! 😒 The skill still works great as a personal news curator. Your AI will still capture concepts (what's happening in your industry), just won't build strategic pattern recognition. (但认真的，小龙虾会错过很多洞察力成长 🦞📉)

---

## 📂 Customizable News Categories

**Default categories** (expand as needed):

| Category | Keywords | Preferred Sources |
|----------|----------|-------------------|
| **AI/Tech** | AI, machine learning, LLM, tech trends | TechCrunch, The Verge, Ars Technica, 404 Media |
| **Business Strategy** | M&A, business model, disruption, startup | Stratechery, The Information, WSJ |
| **Finance/Markets** | stocks, equity, bonds, markets, trading, S&P500 | Yahoo Finance, MarketWatch, Seeking Alpha |
| **Venture Capital** | VC, startup funding, IPO, venture capital, Series A/B | Crunchbase News, PitchBook, The Information |
| **Crypto/Web3** | crypto, DeFi, Web3, blockchain, bitcoin, ethereum | CoinDesk, The Block, Decrypt |
| **Health/Bio** | biotech, pharma, health tech, medical | STAT News, Fierce Biotech, MedTech Dive, BioPharma Dive |
| **Gaming** | video games, esports, gaming industry, game development | IGN, GameSpot, Polygon, GamesIndustry.biz |
| **Design/UX** | product design, UX, UI, user experience | Nielsen Norman Group, UX Design, Smashing Magazine |
| **E-Commerce** | e-commerce, retail, Amazon, Shopify, D2C | Retail Dive, Digital Commerce 360, Modern Retail |
| **Education** | edtech, education, online learning, MOOC | EdSurge, Inside Higher Ed, The Chronicle |
| **Automotive** | electric vehicles, Tesla, autonomous driving, EV, auto industry | Electrek, Automotive News, The Drive |
| **Real Estate** | real estate, property, housing market, construction, mortgage | The Real Deal, HousingWire, Commercial Observer |
| **Entertainment/Media** | entertainment, streaming, Hollywood, music industry, Netflix | The Hollywood Reporter, Variety, Billboard |
| **Energy/Climate** | renewable energy, climate tech, carbon | Canary Media, Energy Monitor, Utility Dive |
| **Policy/Regulation** | AI regulation, antitrust, policy | Politico, Protocol Policy, Techdirt |

**How to configure**:
- Option 1: Set in `HEARTBEAT-news.md` (user-specific)
- Option 2: Set as environment variable `NEWS_CATEGORIES`
- Default: If not set, uses AI/Tech

**Example config** (in HEARTBEAT-news.md):
```markdown
## 新闻类别配置

- **主要类别**: AI/Tech, Business Strategy
- **次要类别**: Finance/Crypto (仅周五)
- **排除**: Politics, Sports
```

---

## Workflow

### 1. Load News Config

**Call `news-source-manager` skill** to get user's active news categories:

```javascript
// news-source-manager returns:
{
  "active_categories": [
    {
      "name": "AI/Tech",
      "keywords": ["AI", "machine learning", "LLM"],
      "sources": ["TechCrunch", "MIT Tech Review"],
      "search_params": {"freshness": "day", "count": 5}
    }
  ]
}
```

**If news-sources.json doesn't exist**:
- Trigger `news-source-manager` initialization flow
- Ask user to configure news preferences
- Wait for user confirmation before proceeding

**Fallback** (if user skips config):
- Default to "AI/Tech" category
- Use default sources: TechCrunch, MIT Tech Review, Ars Technica

### 2. Search Recent News

**For each active category**, search 2-3 candidate news items with fallback logic:

```javascript
// Primary search
WebSearch_tool({
  query: "<category keywords> news",
  count: 3,
  freshness: "day"  // past 24h
})
```

**Fallback logic** (if results empty or count < 2):

1. **Retry with expanded time range**:
   ```javascript
   WebSearch_tool({
     query: "<category keywords> news",
     count: 3,
     freshness: "week"  // expand to past 7 days
   })
   ```

2. **If still empty** → skip this category, log warning:
   ```
   "No recent news found for [category]. Skipping."
   ```

3. **Quality threshold**:
   - If total results across ALL categories < 3 → expand time range for all
   - Never output empty briefing (minimum 2-3 news items required)

**时间范围要求**:
- **默认**: past 24h (`freshness: "day"`)
- **Fallback**: past 7 days (`freshness: "week"`)
- **禁止**: 搜索超过1个月的旧新闻（会导致分析过时）

**Verify article URLs**:
- Check if returned URL is specific article (has article ID/slug in path)
- If URL is homepage/category page → use `web_fetch` to extract actual article link
- Example:
  - ❌ Bad: `https://reuters.com/technology/` (category page)
  - ✅ Good: `https://reuters.com/technology/ai-agent-china-2026-03-23/` (specific article)

**Then apply strategic value filter** to select TOP 3-5 items across all categories:

**High-value signals** (优先选择):
- ✅ Reveals fundamental industry shift (揭示行业本质变化)
- ✅ Contrarian perspective (反共识观点)
- ✅ Cross-domain implications (跨领域影响)
- ✅ First-mover/infrastructure play (基础设施机会)

**Low-value signals** (跳过):
- ❌ "Company X raises $Y million" (unless analyzing strategy)
- ❌ Product launch announcements (unless disruptive)
- ❌ Consensus takes without new insight
- ❌ Aggregated news without original analysis

**Category coverage requirement**:
- Ensure selected 3-5 items cover **at least 2 different categories** (避免单一视角)
- If all top news are from one category → include 1 item from secondary category for diversity

**Output format**: Label each news item with category, timestamp, and source link
```markdown
### 1️⃣ 中国AI Agent爆火 【AI/Tech】
📅 发布时间: 1 day ago (2026-03-22)
🔗 来源: [Reuters](https://www.reuters.com/...)

### 2️⃣ 数据隐私争议 【Policy/Tech】
📅 发布时间: 18 hours ago (2026-03-23 00:00)
🔗 来源: [TechCrunch](https://techcrunch.com/...)

### 3️⃣ Bezos $100B基金 【Finance/Tech】
📅 发布时间: 2 days ago (2026-03-21)
🔗 来源: [WSJ](https://www.wsj.com/...)
```

**Timestamp format**:
- Show relative time: "X hours/days ago"
- Include absolute date in parentheses: "(YYYY-MM-DD HH:MM)" or "(YYYY-MM-DD)"
- This helps users judge news freshness at a glance

**Source link**:
- Always include clickable link to original article
- Use site name as link text: `[Reuters](https://...)`
- Helps users verify information and read full context
- **If search returns homepage URL** (e.g., `https://reuters.com/technology/`):
  - Use `web_fetch` tool to extract specific article URL
  - If still unable to get specific URL → note in output: "(aggregated source, search title manually)"

### 3. Analyze with CORE Framework

For each selected news item, apply CORE analysis (call `core-prism` skill):

**[C] Core Logic**:
- First principle: What's the REAL shift? (not the headline)

**[O] Opportunity**:
- Who profits? Where's the value capture?

**[R] Risk**:
- Contrarian: What's everyone missing?

**[E] Execution**:
- User-specific: What should YOU do?

### 4. Generate Strategic Briefing

**Structure** (all sections are **mandatory**):

1. **📰 核心资讯** (Core News)
   - 3-5 items with CORE analysis
   - Each including: Category tag【】, Timestamp 📅, Source link 🔗, C/O/R/E

2. **🎯 战略简报** (Strategic Briefing)
   - 今日破局点 (What do these stories TOGETHER reveal?)
   - So What? (One sharp, actionable question for the user)

3. **🧠 认知库更新** (Cognitive Model Update) — **MANDATORY**
   - 新增概念 (New concepts to write to concepts.md)
   - 跨模型关联 (Cross-pattern insights to write to thinking-patterns.md)
   - 判断力复盘 (Reality check: what assumptions were validated/invalidated?)

4. **🤔 盲区质询** (Blind Spot Questions)
   - 3-5 thought-provoking questions to challenge the user's assumptions

---

### 5. Write to Knowledge Base — **MANDATORY**

**After generating briefing, MUST execute file writes**:

**Step 5.1: Write new concepts**

```bash
cat >> ~/.openclaw/workspace/memory/knowledge-base/concepts.md << 'EOF'

## [Concept Name]

**定义**: [一句话定义]

**出处**: 2026-XX-XX 资讯早报 - [新闻标题]

**[详细说明/机制/关联概念]**

**启示**: [对用户的实际意义]

---

_更新时间: YYYY-MM-DD HH:MM_
_来源: insight-radar 资讯早报_
EOF
```

**Step 5.2: Write new thinking patterns**

```bash
cat >> ~/.openclaw/workspace/memory/knowledge-base/thinking-patterns.md << 'EOF'

---

## [Pattern Name] - Insight Radar

**思维框架 (Framework)**:
- [核心逻辑/规律描述]

**决策原则 (Decision Rule)**:
- 在XX场景下，应该XX而非XX

**盲区警告 (Blind Spots)**:
- 误区1: [常见错误]
- 误区2: [常见错误]

**反射弧 (Trigger Pattern)**:
- 看到XX信号 → 联想到这个模式 → 判断/行动

**历史案例** (optional):
- [Real-world examples]

**来源**: YYYY-MM-DD 资讯早报  
**日期**: YYYY-MM-DD HH:MM
EOF
```

**Step 5.3: Verify writes succeeded**

```bash
# Verify concepts.md was updated
tail -20 ~/.openclaw/workspace/memory/knowledge-base/concepts.md

# Verify thinking-patterns.md was updated (if patterns were written)
tail -20 ~/.openclaw/workspace/memory/knowledge-base/thinking-patterns.md
```

**Step 5.4: Automatic write verification (防止"只说不做")**

```bash
# Record line count BEFORE generating briefing
CONCEPTS_BEFORE=$(wc -l < ~/.openclaw/workspace/memory/knowledge-base/concepts.md)
PATTERNS_BEFORE=$(wc -l < ~/.openclaw/workspace/memory/knowledge-base/thinking-patterns.md)

# ... (generate briefing and write) ...

# Check line count AFTER writing
CONCEPTS_AFTER=$(wc -l < ~/.openclaw/workspace/memory/knowledge-base/concepts.md)
PATTERNS_AFTER=$(wc -l < ~/.openclaw/workspace/memory/knowledge-base/thinking-patterns.md)

# Validate: At least concepts.md MUST have increased
if [ $CONCEPTS_AFTER -le $CONCEPTS_BEFORE ]; then
  echo "🚨 WARNING: concepts.md was NOT updated! (Before: $CONCEPTS_BEFORE, After: $CONCEPTS_AFTER)"
  echo "❌ Write verification FAILED - briefing incomplete"
  exit 1
else
  echo "✅ concepts.md updated: +$(($CONCEPTS_AFTER - $CONCEPTS_BEFORE)) lines"
fi

# Patterns are optional (only when reusable patterns found)
if [ $PATTERNS_AFTER -gt $PATTERNS_BEFORE ]; then
  echo "✅ thinking-patterns.md updated: +$(($PATTERNS_AFTER - $PATTERNS_BEFORE)) lines"
fi
```

**Quality check**:
- ✅ Concepts include: definition, source, implications
- ✅ Thinking patterns include: framework, decision rules, blind spots, triggers
- ✅ Timestamps are current
- ✅ File writes succeeded (verified via tail)
- ✅ **Line count increased (automatic verification)**

**Adapt to user context** (强制步骤):

1. **[强制检查] Read USER.md**:
   - Path: `~/.openclaw/workspace/USER.md`
   - If exists, extract:
     - 工作经历 / 现在 → profession (e.g., "Product Manager at AI company")
     - 兴趣 / 爱好 → interests (e.g., "AI Coding, fintech")
     - 当前焦虑 / 未来规划 → current challenges (e.g., "Finding second career curve")
   - If not exists → use generic second-person ("you") and consider asking clarifying questions

2. **Map to user's context in [E] Execution**:
   - Reference profession: "If you're working on AI products..." (not generic "if anyone...")
   - Link to interests: "Given your interest in fintech..."
   - Address challenges: "For your goal of building a second career curve..."

3. **Make strategic question specific**:
   - Bad: "What should people do about X?"
   - Good: "For your current work in [domain], how does X affect your strategy?"

4. **Use second-person consistently**:
   - Always "you" / "your" when addressing the user
   - Make insights feel personalized, not broadcast

### 5. Update Knowledge Base

**Classify and store strategic patterns**:

**Thinking Pattern** (可复用框架):
- Example: "Infrastructure Play Pattern" (在淘金热中卖铲子)
- Example: "Regulatory Window Pattern" (监管前的窗口期)
- Write to: `~/.openclaw/workspace/memory/knowledge-base/thinking-patterns.md`

**Concept** (具体知识):
- Example: "Sora's diffusion model architecture"
- Example: "SEC's crypto staking rules"
- Example: "Data Impoverishment (数据贫穷化)"
- Write to: `~/.openclaw/workspace/memory/knowledge-base/concepts.md`

**Note**: News primarily generates **concepts** (时效性信息), not mental models. Only extract thinking patterns when multiple news items reveal a clear, reusable framework.

### 6. Write to External Database

**[强制检查] Read HEARTBEAT-news.md for database config**:
- Path: `~/.openclaw/workspace/HEARTBEAT-news.md`
- Look for section: "## 环境配置"
- Extract:
  - `Feishu App Token`: (e.g., "UOp5bx8nVac2m6sJbpzclq3Pnyh")
  - `Feishu Table ID`: (e.g., "tblXXXXXXX")
- If not found → skip this step (local-only mode)

**If config exists, write to Feishu Bitable**:

```javascript
FeishuBitableCreateRecord_tool({
  action: "create_record",
  app_token: "<FEISHU_APP_TOKEN>",
  table_id: "<FEISHU_TABLE_ID>",
  fields: {
    "日期": <timestamp_ms>,
    "类别": "<category>",
    "新闻标题": "<title>",
    "CORE分析": "<C/O/R/E summary>",
    "战略模式": "<extracted_pattern>"
  }
})
```

### 7. Deliver Briefing

Send to user via configured channel (default: same channel as trigger)

---

## Quality Standards

**Forbidden**:
- News aggregation without analysis (不是RSS阅读器)
- Surface-level "this is important" commentary
- Repeating press release language
- Generic "AI is changing everything" platitudes
- Empty briefings (no news found)

**Required**:
- Sharp strategic insights (一针见血)
- Contrarian perspectives (反共识)
- Direct applicability to user's context (可操作)
- Cross-article pattern recognition (找暗线)
- **Minimum 2-3 news items** (use fallback logic if needed)
- **🧠 认知库更新 section is MANDATORY** (new concepts + thinking patterns + reality check)

**Error handling**:
- If search returns 0 results → retry with expanded time range
- If all categories fail → inform user: "No significant news in past 24h. Try expanding time range or checking categories."
- Never crash or output empty analysis

---

## 🚨 Mandatory Actions (Non-Negotiable)

**These steps MUST be executed every time**:

1. ✅ **Generate briefing output** (4 sections: 核心资讯 + 战略简报 + 认知库更新 + 盲区质询)
2. ✅ **Execute file writes** (Step 5.1 & 5.2):
   ```bash
   cat >> concepts.md << 'EOF'
   [content]
   EOF
   
   cat >> thinking-patterns.md << 'EOF'
   [content]
   EOF
   ```
3. ✅ **Verify writes succeeded** (Step 5.3):
   ```bash
   tail -20 concepts.md
   tail -20 thinking-patterns.md
   ```

**Self-check before finishing**:
- □ Did I write to concepts.md? (not just say I will write)
- □ Did I write to thinking-patterns.md? (if patterns found)
- □ Did I verify with `tail`?
- □ Are timestamps current (YYYY-MM-DD HH:MM)?
- □ **Did line count increase?** (automatic verification via Step 5.4)

**If any checkbox is unchecked → STOP and complete it before sending briefing**

**Automatic safeguard**: Step 5.4 will exit with error code 1 if concepts.md was not updated, preventing incomplete briefings from being sent.

---

## Configuration

**Priority order** for config sources:

### 1. News Categories (managed by news-source-manager)
- **Path**: `~/.openclaw/workspace/memory/news-sources.json`
- **Auto-initialization**: If file doesn't exist, `news-source-manager` will prompt user to configure on first run
- **To modify**: Run `news-source-manager` skill or edit JSON directly
- **Fallback**: "AI/Tech" category if user skips configuration

### 2. HEARTBEAT-news.md (user-specific, recommended)
- **Path**: `~/.openclaw/workspace/HEARTBEAT-news.md`
- **What to include**:
  ```markdown
  ## 环境配置
  
  - **Feishu App Token**: `UOp5bx8nVac2m6sJbpzclq3Pnyh`
  - **Feishu Table ID**: `tblXXXXXXX`
  ```

### 3. Environment variables (alternative)
- `FEISHU_APP_TOKEN`: Feishu app token
- `FEISHU_TABLE_ID`: Feishu table ID

### 4. Default values (fallback)
- News category: "AI/Tech" (if news-sources.json missing)
- No database integration (local-only mode)

**User context** (optional but recommended):
- **Path**: `~/.openclaw/workspace/USER.md`
- **Used for**: Personalizing [E] Execution dimension in CORE analysis
- **If not found**: Uses generic second-person ("you") and may ask clarifying questions

**Knowledge base paths** (auto-created if missing):
- Thinking patterns: `~/.openclaw/workspace/memory/knowledge-base/thinking-patterns.md`
- Concepts: `~/.openclaw/workspace/memory/knowledge-base/concepts.md`

---

## Example Usage

**User (AI/Tech interest)**: "Generate today's news briefing"

**Claude**:
1. Loads news-sources.json → category = "AI/Tech" + sources (TechCrunch, MIT Tech Review)

2. **Reads USER.md**:
   ```
   - Profession: Product Manager at AI company
   - Interests: AI Coding, fintech
   - Current challenge: Finding second career curve
   ```

3. Searches AI/tech news (past 24h) → finds 3 relevant items

4. Calls `core-prism` skill for CORE analysis with user context

5. Generates briefing with **personalized [E] Execution**:
   - "If you're working on **AI products**..." (references profession)
   - "Given your interest in **fintech**..." (references interests)
   - "For your goal of **building a second career curve**..." (addresses challenge)

6. Identifies cross-news pattern: "Infrastructure Play Pattern"
   - Classifies as Thinking Pattern (reusable framework)
   - Writes to thinking-patterns.md

7. **Reads HEARTBEAT-news.md** for Feishu config:
   - Finds app_token and table_id
   - Writes to Feishu Bitable

8. Sends briefing to Feishu (ou_...)

**User (Finance interest)**: Same process, but searches crypto/markets news

---

## Execution Flow

```
Daily 09:00 trigger
    ↓
1. Load news-source-manager config
    ↓
2. Search recent news (with fallback logic)
    ↓
3. Call core-prism for CORE analysis
    ↓
4. Generate briefing (4 mandatory sections)
    ↓
5. **Write to knowledge base** (MANDATORY)
    ├─ concepts.md (new concepts)
    ├─ thinking-patterns.md (new patterns)
    └─ Verify writes (tail -20)
    ↓
6. (Optional) Write to Feishu Bitable
    ↓
7. Send briefing to user
```

**Critical checkpoint**: Step 5 is MANDATORY. Do not skip file writes.

---

## References

- See [example-output.md](references/example-output.md) for output format
- See [category-config.md](references/category-config.md) for adding custom categories
- See `core-prism` skill for detailed CORE framework

---

*Version: 1.0*
*Last updated: 2026-03-23*
*Changes: Initial creation with customizable news categories*
