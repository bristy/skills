# COMPANY-INTEGRATION.md
## Analyst Mastery — Ten Life Creatives Integration Guide
### Bridges ANALYST-CHARTER.md to the analyst-mastery skill system

---

## 1. Role Mapping — Charter KPI Domains to Reference Files

| Charter KPI Domain | Reference File(s) | Notes |
|---|---|---|
| Operational KPIs (throughput, cycle time, routing) | `kpi-definitions`, `performance-benchmarks` | Task velocity, routing accuracy |
| Founder Protection KPIs (escalation load, briefing quality) | `bottleneck-detection`, `reporting-cadence` | Measure founder touch rate |
| Quality KPIs (Sentinel rejection rate, revision rate) | `anomaly-detection`, `root-cause-analysis` | Quality trend analysis |
| Revenue & Growth KPIs (pipeline, proposals, launches) | `revenue-analytics`, `product-performance` | Gumroad + pipeline signals |
| Knowledge KPIs (SOPs, prompts, templates) | `content-performance`, `performance-benchmarks` | IP compounding rate |
| Signal Memo delivery & format | `executive-communication`, `reporting-cadence` | Friday memo structure |
| Bottleneck identification | `bottleneck-detection`, `statistical-methods` | Workflow choke points |
| Monthly trend reports | `forecasting`, `statistical-methods` | Month-over-month variance |
| Data collection protocols | `data-collection` | Where to pull each metric |
| Visualization & dashboards | `data-visualization` | Chart selection for memos |
| Platform health monitoring | `platform-health` | AgentReach, cron, sessions |

---

## 2. Our Actual Metrics to Track

### Revenue — Gumroad API
- **Token:** `7Rks_AD_ZEScGX649Srnd8bnjJzmqqZ4rPUryRwFZl8`
- **Endpoint:** `GET https://api.gumroad.com/v2/products`
- **Key field:** `sales_count` per product
- **Products (live as of 2026-03-21):**
  - Reddit Master — The Complete AI Agent Playbook ($17)
  - The Social Media Agent Master Playbook — 2026 Edit ($27)
  - Legacy Letters — A Personal Letter Written Just for You ($49)
  - FamliClaw — Your Family's Complete AI Setup Kit ($47)
  - Scripture Memory Cards — 52 Verses ($4.99)
  - The Anxiety Unpack — A Practical CBT Workbook ($9.99)
  - Pray Deeper — Daily Scripture & Prayer Prompts ($6.99)
  - Budget Binder 2026 — Complete Financial Planning Kit ($7.99)
  - *(1 product unpublished — Learn to Buy a Pre-Existing QSR, $5.00)*
- **Pull command:**
```python
import requests
r = requests.get('https://api.gumroad.com/v2/products',
    headers={'Authorization': 'Bearer 7Rks_AD_ZEScGX649Srnd8bnjJzmqqZ4rPUryRwFZl8'})
for p in r.json().get('products', []):
    print(p['name'][:40], p.get('sales_count', 0), 'sales')
```

### Content — X (Twitter) Posting
- **@tenlifejosh:** `projects/content/x_posted.json` — 9 posts total (life/career content)
- **@HutchCOO:** `projects/content/hutchcoo_posted.json` — 2 posts total (AI COO brand)
- **Cron jobs:** "X Post — Daily (tenlifejosh)", "HutchCOO X Post — Daily (Social Agent)"
- Track: posts per week per account, content category mix

### Content — Pinterest
- **20 pins live** (tracked via AgentReach Pinterest session)
- AgentReach Pinterest: Healthy, 58 days remaining (as of 2026-03-21)
- Track: saves, clicks, monthly views via AgentReach harvest data

### Content — Reddit
- **Session:** AgentReach Reddit — Healthy, 28 days remaining
- **Log file:** `projects/content/reddit-log.json` (does not exist yet — begins when Reddit warm-up cron fires)
- **Cron:** "Reddit Warm-up — Daily Comment (u/HutchCOO)" — currently erroring (1 error)
- Track: comments posted, karma growth when log exists

### System — AgentReach Sessions
```bash
cd /Users/oliverhutchins1/.openclaw/workspace-main/projects/agentreach
.venv/bin/agentreach status
```
- **Current status (2026-03-21):** All 5 sessions healthy
  - Amazon KDP: 28 days
  - Etsy: 43 days
  - Gumroad: 52 days
  - Pinterest: 58 days
  - Reddit: 28 days
- **Alert threshold:** Any session < 14 days → immediate flag to Hutch

### System — Cron Health
```python
import json
with open('/Users/oliverhutchins1/.openclaw/cron/jobs.json') as f:
    jobs = json.load(f)
errors = [(j['name'], j['state'].get('consecutiveErrors', 0)) for j in jobs.get('jobs', [])
          if j['state'].get('consecutiveErrors', 0) > 0]
healthy = len([j for j in jobs.get('jobs', []) if j['state'].get('consecutiveErrors', 0) == 0])
```
- **Current:** 22/35 healthy, 13 with errors (as of 2026-03-21)
- Key erroring crons: Prayful TikTok Batch (2 errors), Revenue Trend Monitor, Revenue Product Creator, AutoImprove Revenue System, Reddit Warm-up, X Post Afternoon/Evening
- **Alert threshold:** Any cron > 3 consecutive errors → Sentinel escalation

---

## 3. Weekly Signal Memo Format

Every Friday, Analyst delivers this memo (under 200 words) to Hutch. Signal-first, no filler.

```
---
📊 ANALYST — WEEKLY SIGNAL MEMO
Week of: [DATE]
---

HEADLINE SIGNAL
[One honest sentence on what the data says this week]

---

REVENUE
Gumroad this week: $[X] ([N] sales) | Lifetime: [N] total sales
Top product: [product name] — [N] sales
Trend: [Up / Flat / Down] vs. last week

---

CONTENT
X posted: [N] tweets (@tenlifejosh) + [N] (@HutchCOO)
Pinterest: [N] pins live | [N] saves this week
Reddit: [status — log exists Y/N, posts this week]

---

SYSTEM
Cron health: [N]/[total] healthy | [N] errors
AgentReach: [N] sessions healthy | Lowest: [platform] — [N] days
Agent uptime: [any outages or issues]

---

PIPELINE
Products live: [N] published / [N] total on Gumroad
New products this week: [N]
Revenue signal: [Strong / Moderate / Weak / None]

---

ONE THING
[Single highest-leverage action the data supports this week]
---
```

---

## 4. KPI Definitions

### Revenue KPIs
| KPI | Definition | Source | Target |
|---|---|---|---|
| Weekly Gumroad revenue | Sum of sales × price this week | Gumroad API | Growing |
| Daily Gumroad sales | sales_count delta per 24h | Gumroad API | Tracked |
| Product-level sales | sales_count per product | Gumroad API | Each product > 0 |
| Revenue per product | Price × sales_count | Gumroad API | Tracked |

### Content KPIs
| KPI | Definition | Source | Target |
|---|---|---|---|
| Tweets posted/week | Count of posts in x_posted.json (7-day window) | x_posted.json | ≥5/week @tenlifejosh |
| HutchCOO posts/week | Count in hutchcoo_posted.json (7-day window) | hutchcoo_posted.json | ≥3/week |
| Pinterest pins live | Total active pins | AgentReach | Growing from 20 |
| Pinterest saves/week | Weekly saves metric | AgentReach harvest | Growing |
| Reddit posts/week | Comments + posts in reddit-log.json | reddit-log.json | ≥5/week when live |

### System KPIs
| KPI | Definition | Source | Target |
|---|---|---|---|
| Cron success rate | % of jobs with 0 consecutive errors | jobs.json | ≥85% (30/35) |
| Session health count | AgentReach sessions ≥ 14 days remaining | agentreach status | All 5 healthy |
| Min session days | Lowest days remaining across all sessions | agentreach status | > 14 days |
| Agent error rate | Consecutive errors across all cron jobs | jobs.json | Zero priority crons |

### Pipeline KPIs
| KPI | Definition | Source | Target |
|---|---|---|---|
| Products published | Count of published=True on Gumroad | Gumroad API | All products live |
| Products built vs published | Gap between total products and published | Gumroad API | Gap = 0 |
| New products this week | Products added in last 7 days | Gumroad API | ≥1/week |
| Listings updated | Products with recent metadata changes | Gumroad API | Tracked |

---

## 5. Anomaly Thresholds

### Revenue Alerts (→ Hutch immediately)
| Condition | Threshold | Action |
|---|---|---|
| Zero revenue for 7+ days | sales_count unchanged across all products | Flag to Hutch + Navigator |
| Single product sales spike | >10 sales in 24h | Positive alert — amplify signal |
| Revenue below baseline 2 weeks | 0 sales week 2 in a row | Escalate to Founder via Hutch |

### Content Alerts (→ Hutch if blocked)
| Condition | Threshold | Action |
|---|---|---|
| X posting gap | No posts in 4+ days | Flag cron failure to Sentinel |
| Zero content week | No posts on either account | Immediate Sentinel + Hutch alert |
| Pinterest session expiry | < 14 days remaining | Hutch alert to renew |

### System Alerts (→ Sentinel + Hutch)
| Condition | Threshold | Action |
|---|---|---|
| Cron success rate drops | < 70% (< 25/35 healthy) | Sentinel escalation |
| Single cron errors | > 3 consecutive errors | Sentinel review |
| AgentReach session critical | < 7 days remaining | Immediate Hutch alert |
| Revenue cron failure | Any revenue cron errors | Priority fix — blocks data |

### Normal Variance (no alert needed)
- 1–2 cron errors that clear in same week
- Gumroad API slight delays (< 1 hour)
- Pinterest impressions ±30% week over week
- X post timing variance ±2 hours from schedule

---

## 6. Handoff Protocols

### Analyst → Navigator (Weekly)
**Trigger:** Every Friday, after signal memo is generated
**Format:** Signal memo at `projects/ops/signal-memo-YYYY-MM-DD.md`
**Contents:** Revenue trend, content velocity, system health, ONE THING recommendation
**Navigator reads this for:** Monday strategic memo, weekly priority setting

### Analyst → Hutch (Anomalies)
**Trigger:** Any threshold breach (see Section 5)
**Format:** Direct Telegram alert via Hutch's main session
**Message structure:**
```
🚨 ANALYST ALERT — [CATEGORY]
Signal: [What changed]
Impact: [What it affects]
Data: [Specific numbers]
Recommended action: [One clear step]
```

### Analyst → Sentinel (Quality Issues)
**Trigger:** Recurring cron failures, data collection gaps, content quality drops
**Format:** Handoff using HANDOFF-TEMPLATES.md format
**Contents:** Specific failure, error count, affected workflow, recommended audit scope
**Sentinel owns:** Investigation, fix verification, clearance confirmation

---

*Last updated: 2026-03-21 | Version 1.0 | Owner: Analyst — Governed by Hutch (COO)*
*Bridge document: ANALYST-CHARTER.md ↔ analyst-mastery skill*
