# Reporting & Cadence

The complete reporting framework: what to report, when, to whom, and in what format.

---

## Table of Contents
1. Reporting Philosophy
2. Daily Operational Checks
3. The Weekly Signal Memo (Friday Deliverable)
4. Monthly Deep-Dive
5. Quarterly Trend Review
6. Ad-Hoc Forensic Reports
7. Escalation Triggers
8. Report Distribution

---

## 1. Reporting Philosophy

### The Anti-Dashboard-Dump Principle
Reports are NOT data dumps. A good report is SHORTER than the data it's based on because it has
filtered noise, identified signal, and translated numbers into decisions.

### The Three Laws of Reporting
1. **Every number earns its place.** If a metric doesn't change a decision, cut it.
2. **Every finding has a "so what?"** Raw observation without interpretation is noise.
3. **Every report respects the reader's time.** Shorter is better. Always.

### Audience-Appropriate Depth
```
Navigator / Hutch (decision-makers): Signal only. Top 3-5 insights. Recommendations. 1-2 pages max.
Operations team: Signal + diagnostics. Where to investigate. 2-5 pages.
Deep-dive audience: Full analysis. Methodology. Data tables. Unlimited but structured.
```

---

## 2. Daily Operational Checks

### Purpose
Catch problems early. Not a report — an automated health scan.

### Cadence
Run at 01:00 UTC daily (after all data collection jobs complete).

### What to Check
1. ✅ Revenue: Yesterday's revenue pulled. Any ALERT/WATCH conditions?
2. ✅ Cron Jobs: All CRITICAL and HIGH jobs ran successfully?
3. ✅ Sessions: All sessions active with >24h to expiry?
4. ✅ APIs: All endpoints responding with <5% error rate?
5. ✅ Silent Failures: Any detected?
6. ✅ Queue Depths: Any growing beyond threshold?

### Output: Daily Health Pulse
```
📊 DAILY HEALTH PULSE — [DATE]

Revenue: $[amount] [🟢/🟡/🔴] [vs benchmark: +/-X%]
Cron Jobs: [X/Y] passing [🟢/🟡/🔴]
Sessions: [status] [🟢/🟡/🔴] [nearest expiry: Xh]
APIs: [status] [🟢/🟡/🔴]
Silent Failures: [count] [🟢/🟡/🔴]
Queues: [status] [🟢/🟡/🔴]

⚠️ ISSUES REQUIRING ATTENTION:
[List only if any. If all green: "All systems nominal."]
```

### Distribution
- If all green: Log only. No notification needed.
- If any WATCH: Include in next scheduled report.
- If any ALERT: Immediate notification per alert protocol.

---

## 3. The Weekly Signal Memo (Friday Deliverable)

This is the Analyst's PRIMARY deliverable. Delivered every Friday. Read by Navigator and Hutch.
This is NOT a dashboard dump — it's a curated intelligence brief.

### Target Length
500-800 words. Maximum 2 pages. If it takes longer than 5 minutes to read, it's too long.

### The Signal Memo Template

```markdown
# Weekly Signal Memo — Week of [Date Range]

## Business Health Index: [SCORE]/100 — [TREND: ↑/→/↓ vs last week]

---

## Top 3 Signals This Week

### 1. [Most important signal — one sentence headline]
[2-3 sentences: What happened, why it matters, what to do about it]

### 2. [Second most important signal]
[2-3 sentences]

### 3. [Third most important signal]
[2-3 sentences]

---

## Revenue
**This Week**: $[amount] | **Last Week**: $[amount] | **Change**: [+/-$] ([+/-%])
**Trend**: [Accelerating / Growing / Stable / Softening / Declining]
**Monthly Run Rate**: $[amount]

Top mover: [what drove the biggest revenue change this week]
[One specific product or source insight]

## Content
**Published**: [count] pieces | **Best performer**: [description + metric]
**Pinterest**: [1-line signal — CTR trend, top pin]
**Twitter/X**: [1-line signal — reply rate, top tweet]
**Reddit**: [1-line signal if active]

Key insight: [What content approach is working/not working right now]

## System Health
**Score**: [X]/100 [🟢/🟡/🔴]
[1-2 lines: only if issues exist. If clean: "All systems nominal."]

## Product Health
**Stars**: [products performing well]
**Needs attention**: [products underperforming, with diagnosis]

---

## Recommended Adjustments

1. **[Specific recommendation]** — [Brief rationale based on data above]
2. **[Specific recommendation]** — [Brief rationale]
3. **[Specific recommendation]** — [Brief rationale] (if warranted)

---

## Watching (not yet actionable, monitoring)
- [Item 1: what and why monitoring]
- [Item 2]
```

### Signal Memo Principles
1. **Lead with the headline.** The Top 3 Signals are what the reader will remember. Choose them
   for IMPACT, not just magnitude. A 50% traffic spike matters less than a 10% conversion decline.

2. **Be specific in recommendations.** Not "optimize Pinterest strategy" but "Revert to editorial-style
   pins — the product-pin format has reduced CTR by 23% over 2 weeks."

3. **Distinguish what moved from what matters.** Lots of things move every week. Only include
   movements that have decision-making implications.

4. **Include what DIDN'T happen.** If something was expected and didn't materialize (a launch that
   didn't generate expected sales, a fix that didn't improve metrics), that's a signal too.

5. **End with forward-looking items.** The "Watching" section prevents surprises next week.

### Friday Memo Preparation Timeline
```
Monday: Review data from prior week. Note any anomalies flagged during the week.
Tuesday-Thursday: Monitor for additional signals. Compile context for any anomalies.
Friday AM: Compile the memo. All data should be final by now.
Friday by 2:00 PM: Deliver memo to Navigator and Hutch.
```

---

## 4. Monthly Deep-Dive

### Purpose
Zoom out from weekly signals. Identify trends, patterns, and structural issues that only become
visible at monthly scale.

### Cadence
Delivered on the 3rd business day of each month, covering the prior month.

### Structure
```markdown
# Monthly Performance Report — [Month Year]

## Executive Summary (1 paragraph)
[The single most important story of this month, in 3-4 sentences]

## Revenue Deep-Dive
- Monthly total vs prior month vs same month last year
- Revenue by product (table with trends)
- Revenue by source (table with trends)
- Price point analysis
- Cohort analysis (if applicable)
- Monthly forecast accuracy (how close was last month's forecast to actual?)

## Content Deep-Dive
- Content volume and performance by platform
- Top 10 content pieces by resonance score
- Content format analysis (what types of content work best?)
- Content-to-revenue attribution
- Platform-specific trends and algorithm observations

## System Health Summary
- Monthly uptime and reliability
- Incidents and resolutions
- Session management summary
- Any recurring system issues

## Product Portfolio Review
- Health score changes for all products
- Lifecycle stage changes
- Conversion rate trends
- Product-specific recommendations

## Bottleneck Analysis
- Workflow velocity trends
- Agent performance summary
- Identified bottlenecks and status

## Looking Ahead
- Trends to watch
- Risks on the horizon
- Opportunities identified
- Questions that need answering (data requests for next month)
```

### Delivery
As a structured Markdown document or DOCX. Include data tables and visualizations.

---

## 5. Quarterly Trend Review

### Purpose
Strategic-level assessment. Are we moving in the right direction? What structural changes are needed?

### Cadence
Delivered within the first week of each quarter, covering the prior quarter.

### Unique Content (not in monthly)
- Quarter-over-quarter revenue trajectory
- Product portfolio evolution (what's growing, what's declining over 3 months)
- Platform effectiveness evolution (which channels are becoming more/less efficient)
- Benchmark recalibration recommendations
- Strategic signals: What the data says about where the business should focus next quarter

### Important Caveat
The Analyst surfaces strategic signals but does NOT make strategic decisions. The quarterly review
presents evidence and patterns. Navigator and Hutch decide what to do with them.

---

## 6. Ad-Hoc Forensic Reports

### When to Produce
- After any SEV-1 or SEV-2 incident
- When asked to investigate a specific question
- When an anomaly is too complex for the weekly memo

### Structure
```markdown
# Investigation: [Title]
Date: [when investigation was conducted]
Requested by: [who asked, or self-initiated]
Trigger: [what prompted this investigation]

## Question
[What specific question is this investigation answering?]

## Methodology
[Data sources used, time periods examined, analytical methods applied]

## Findings
[Numbered findings, each with evidence]

## Conclusion
[What the evidence supports]

## Confidence Level
[High / Medium / Low — with explanation of what would increase confidence]

## Recommended Actions
[Specific next steps based on findings]

## Open Questions
[What this investigation couldn't answer — what further analysis is needed]
```

---

## 7. Escalation Triggers

### When to Break the Cadence
The scheduled reporting cadence (daily checks → weekly memo → monthly deep-dive) should be BROKEN
in these circumstances:

```
IMMEDIATE ESCALATION (don't wait for next scheduled report):
- Revenue drops >40% vs daily average with no known cause
- Multiple CRITICAL cron jobs failing simultaneously
- AgentReach session expires with no backup
- Data integrity issue affecting revenue tracking
- Any SEV-1 incident

SAME-DAY ESCALATION (notify within 4 hours):
- Revenue drops >20% for 2+ consecutive days
- New competitor product launched at lower price
- Platform (Pinterest, X, Reddit) announces major algorithm change
- Any SEV-2 incident

NEXT-REPORT ESCALATION (include in next scheduled report):
- New trend emerging (positive or negative) that wasn't in prior report
- Benchmark consistently missed for 3+ weeks
- System health degrading gradually
- Any SEV-3 incident
```

---

## 8. Report Distribution

### Audience Map
```
WEEKLY SIGNAL MEMO → Navigator + Hutch (decision-makers)
DAILY HEALTH PULSE → Automated log (alerts distributed per severity protocol)
MONTHLY DEEP-DIVE → Navigator + Hutch + relevant team members
QUARTERLY REVIEW → Navigator + Hutch
AD-HOC FORENSICS → Requester + relevant stakeholders
ALERTS → Per severity matrix in anomaly-detection.md
```

### Format Preferences
- Signal Memo: Markdown (quick to read, easy to scan)
- Monthly Deep-Dive: DOCX or Markdown (needs to be comprehensive)
- Alerts: Short-form structured text (glanceable)
- Dashboards: React/HTML (when interactive exploration is needed)
