# KPI Definitions & Metric Architecture

The canonical reference for every metric the Analyst tracks. Read this FIRST before any analytical task.

---

## Table of Contents
1. Metric Taxonomy & Hierarchy
2. Revenue Metrics
3. Traffic & Acquisition Metrics
4. Content Engagement Metrics
5. Product Performance Metrics
6. Platform & System Health Metrics
7. Operational Efficiency Metrics
8. Composite Scores
9. Metric Relationships Map
10. Leading vs Lagging Indicator Guide

---

## 1. Metric Taxonomy & Hierarchy

Every metric falls into one of four tiers:

### Tier 1 — North Star Metrics (Weekly Signal Memo, always included)
These are the 3-5 numbers that, if you could only see five things, would tell you whether the business is healthy.
- **Total Revenue** (daily, weekly, monthly)
- **Revenue per Product** (identifies winners and losers)
- **Conversion Rate** (traffic-to-purchase, the fundamental health metric)
- **System Uptime / Health Score** (are automated systems actually running?)
- **Content-to-Revenue Attribution** (which content efforts actually drive money?)

### Tier 2 — Diagnostic Metrics (Weekly Signal Memo when anomalous, always in monthly deep-dive)
These explain WHY Tier 1 metrics move.
- Traffic volume by source (Pinterest, Twitter/X, Reddit, direct, organic search)
- Engagement rates by platform
- Product view counts and view-to-sale ratios
- Agent task completion rates and cycle times
- Cron job success rates

### Tier 3 — Operational Metrics (Daily checks, weekly summary)
The engine-room gauges.
- Individual cron job status (pass/fail/skip)
- API response times and error rates
- Session expiry countdowns
- Queue depths
- Individual content piece performance

### Tier 4 — Deep-Dive Metrics (On-demand, forensic investigation only)
Only pulled when investigating a specific question.
- Cohort-level behavior
- Hourly traffic patterns
- Individual user session paths
- Error log line-level analysis
- A/B test segment breakdowns

### The Golden Rule of Metric Tiers
Reports should flow TOP-DOWN through tiers. Start with Tier 1. Only drill into Tier 2 when a Tier 1 metric is
anomalous. Only pull Tier 3 when Tier 2 doesn't explain the anomaly. Tier 4 is forensic — used to solve a
specific mystery, never to pad a report.

---

## 2. Revenue Metrics

### Total Revenue
- **Definition**: Gross revenue from all Gumroad sales in the measurement period, before refunds
- **Calculation**: SUM(all sale amounts) for the period
- **Comparison context**: WoW, MoM, trailing 4-week average
- **Benchmark**: See performance-benchmarks.md for target values
- **Alert threshold**: >20% decline WoW (ALERT), >10% decline WoW (WATCH)
- **Why it matters**: The ultimate output metric. Everything else is a leading indicator for this.

### Net Revenue
- **Definition**: Gross revenue minus refunds and Gumroad fees
- **Calculation**: Gross Revenue - Refunds - Platform Fees (Gumroad ~8.5% + $0.30/txn)
- **Comparison context**: Always pair with Gross Revenue to monitor refund rate
- **Alert threshold**: Refund rate >5% (ALERT), >3% (WATCH)

### Revenue by Product
- **Definition**: Revenue attributed to each individual Gumroad product/listing
- **Calculation**: SUM(sale amounts) per product_id for the period
- **Use**: Identify top performers, underperformers, and emerging products
- **Diagnostic power**: When total revenue changes, this tells you WHICH products drove the change

### Revenue by Traffic Source
- **Definition**: Revenue attributed to traffic originating from each platform
- **Calculation**: Revenue from sales where referrer matches the platform
- **Sources to track**: Pinterest, Twitter/X, Reddit, direct/bookmark, organic search, email, other
- **Why it matters**: Tells you where to invest content effort. A platform with high traffic but low
  revenue-per-visitor is less valuable than one with moderate traffic and high conversion.

### Average Order Value (AOV)
- **Definition**: Average revenue per transaction
- **Calculation**: Total Revenue / Number of Transactions
- **Comparison context**: WoW, by product category, by traffic source
- **Alert threshold**: >15% decline WoW (WATCH) — may indicate mix shift or discounting

### Daily Revenue Run Rate
- **Definition**: Projected monthly revenue based on current daily average
- **Calculation**: (Revenue this month to date / Days elapsed) × Days in month
- **Use**: Early warning system for monthly target tracking
- **Caveat**: Highly volatile early in the month. Confidence increases as month progresses.

### Revenue Concentration Index
- **Definition**: How dependent revenue is on a single product or source
- **Calculation**: (Top product revenue / Total revenue) × 100
- **Alert threshold**: >60% concentration (WATCH) — single point of failure risk
- **Why it matters**: High concentration means high vulnerability to any single product underperforming

### Price Point Conversion Matrix
- **Definition**: Conversion rate segmented by price tier
- **Calculation**: For each price tier: (Sales at that tier / Views of products at that tier) × 100
- **Price tiers**: Define based on actual product prices (e.g., $0-9, $10-29, $30-49, $50+)
- **Use**: Identifies price sensitivity and optimal price-value zones

---

## 3. Traffic & Acquisition Metrics

### Total Traffic
- **Definition**: Unique visitors/sessions to Gumroad product pages in the measurement period
- **Calculation**: SUM(unique views) across all product pages
- **Sources**: Gumroad analytics, UTM parameter tracking
- **Comparison context**: WoW, MoM, by source

### Traffic by Source
- **Definition**: Visitor volume attributed to each referral source
- **Tracked sources**:
  - **Pinterest**: Clicks from pins (track by pin → product mapping)
  - **Twitter/X**: Clicks from tweets (track by tweet → product mapping)
  - **Reddit**: Clicks from comments/posts (track by subreddit → product mapping)
  - **Organic Search**: Google/Bing referrals
  - **Direct/Bookmark**: No referrer
  - **Email**: From newsletter or email campaigns
  - **Other**: All other referrers
- **Why it matters**: Not all traffic is equal. Source quality varies enormously.

### Traffic Quality Score (per source)
- **Definition**: Composite score reflecting how likely traffic from a source is to convert
- **Calculation**: Weighted average of:
  - Conversion rate from that source (weight: 0.5)
  - Average pages per session from that source (weight: 0.2)
  - Bounce rate inverse from that source (weight: 0.15)
  - Average time on page from that source (weight: 0.15)
- **Scale**: 0-100, where 100 is the highest quality
- **Use**: Prioritize effort toward high-quality traffic sources, not just high-volume ones

### New vs Returning Visitor Ratio
- **Definition**: Proportion of traffic from first-time vs repeat visitors
- **Calculation**: New visitors / Total visitors × 100
- **Benchmark**: Healthy range varies by business model. For Gumroad digital products, 60-75% new is typical.
- **Why it matters**: Heavily new = acquisition working but no retention/repeat. Heavily returning = loyal base
  but growth channel may be drying up.

---

## 4. Content Engagement Metrics

### Pinterest Metrics
- **Pin Impressions**: How many times a pin was displayed in feeds/search
- **Pin Clicks (Outbound)**: Clicks that leave Pinterest toward your Gumroad page — THE metric that matters
- **Pin Saves**: Users saving pin to their boards — secondary indicator of resonance
- **Click-Through Rate (CTR)**: Outbound Clicks / Impressions × 100
- **Pin-to-Sale Conversion**: Sales attributed to a pin / Outbound clicks from that pin × 100
- **Top Pin Velocity**: How quickly a new pin accumulates impressions in first 48 hours (predicts performance)
- **Alert threshold**: CTR < 0.5% (WATCH for underperformance), CTR > 3% (flag as high performer to replicate)

### Twitter/X Metrics
- **Impressions**: Tweet view count
- **Replies**: THE critical metric — replies are weighted 13.5x by the X algorithm for distribution
- **Reply Rate**: Replies / Impressions × 100 — the single most important Twitter/X engagement metric
- **Retweets/Reposts**: Secondary distribution signal
- **Link Clicks**: Clicks to Gumroad from tweets
- **Engagement Rate**: (Replies + Retweets + Likes + Clicks) / Impressions × 100
- **Reply-Weighted Engagement**: Replies × 13.5 + Retweets × 1 + Likes × 0.5 (custom score reflecting algorithm weight)
- **Alert threshold**: Reply rate < 0.5% over 7-day rolling average (WATCH for declining relevance)

### Reddit Metrics
- **Upvotes**: Net upvotes on posts/comments
- **Comment Karma**: Karma earned from comments (indicator of community value)
- **Click-Through**: Profile or link clicks from Reddit posts/comments
- **Subreddit Performance**: Which subreddits generate the most engagement per post
- **Comment-to-Click Ratio**: How often engagement translates to actual profile/link visits
- **Alert threshold**: Negative karma trend over 2-week period (WATCH — could indicate content misalignment)

### Cross-Platform Content Score
- **Definition**: Normalized performance score for comparing content across platforms
- **Calculation**: For each piece of content, compute:
  - Platform-normalized engagement rate (actual / platform median × 100)
  - Revenue attribution if available
  - Decay rate (how quickly engagement falls off)
- **Scale**: 0-100, normalized per platform so a "70" on Pinterest and a "70" on Twitter/X mean
  roughly equivalent performance relative to each platform's norms
- **Use**: Identify which TOPICS resonate across platforms vs which are platform-specific

---

## 5. Product Performance Metrics

### Product View Count
- **Definition**: Unique views of a Gumroad product listing page
- **Calculation**: Gumroad analytics per product
- **Use**: First-stage diagnostic. Low views = traffic problem. High views + low sales = conversion problem.

### Product Conversion Rate
- **Definition**: Percentage of product page views that result in a purchase
- **Calculation**: (Sales / Views) × 100 per product
- **Benchmark**: See performance-benchmarks.md for range by price point
- **Diagnostic matrix**:
  - High views + High conversion = WINNER (scale traffic)
  - High views + Low conversion = CONVERSION PROBLEM (fix page, price, offer)
  - Low views + High conversion = TRAFFIC PROBLEM (content works, need more of it)
  - Low views + Low conversion = RETHINK PRODUCT (may need fundamental changes)

### Product Health Score
- **Definition**: Composite score reflecting overall product viability
- **Calculation**: Weighted composite:
  - Conversion rate vs benchmark (weight: 0.35)
  - Revenue trend (14-day slope, weight: 0.25)
  - View trend (14-day slope, weight: 0.20)
  - Refund rate inverse (weight: 0.10)
  - Review/rating quality (weight: 0.10)
- **Scale**: 0-100
  - 80-100: Star performer
  - 60-79: Healthy
  - 40-59: Needs attention
  - 20-39: Underperforming — investigate
  - 0-19: Consider sunsetting or major overhaul
- **Alert threshold**: Score drops >15 points WoW (ALERT)

### Product Lifecycle Stage
- **Classification**:
  - **Launch** (first 14 days): Evaluate against launch benchmarks, not steady-state
  - **Growth** (positive 4-week revenue trend, above break-even): Scale investment
  - **Mature** (stable revenue, minimal growth): Optimize and maintain
  - **Declining** (negative 4-week trend): Diagnose cause, decide: revive or sunset
- **Use**: Different lifecycle stages get different benchmarks and different recommendations

---

## 6. Platform & System Health Metrics

### System Uptime Score
- **Definition**: Percentage of time automated systems are running as expected
- **Calculation**: (Successful operations / Expected operations) × 100 over the period
- **Scope**: Covers all cron jobs, scheduled tasks, API integrations, agent operations
- **Benchmark**: Target 99%+ for critical systems, 95%+ for non-critical
- **Alert threshold**: <95% (ALERT for critical), <90% (ALERT for non-critical)

### Cron Job Health
- **Per-job tracking**:
  - Last successful run timestamp
  - Success rate (trailing 7 days)
  - Average execution time
  - Error frequency and error types
  - Silent failure detection (job ran but produced no output or wrong output)
- **Composite Cron Health Score**: (Jobs running clean / Total scheduled jobs) × 100
- **Alert threshold**: Any critical cron job failure = ALERT. Non-critical failure >2 consecutive = WATCH.

### AgentReach Session Health
- **Session expiry countdown**: Time remaining on active sessions
- **Session refresh success rate**: How often session refreshes succeed
- **Alert threshold**: <24 hours to expiry without scheduled refresh = ALERT
- **Pre-expiry warning**: At 72 hours, 48 hours, and 24 hours before expiry

### API Endpoint Health
- **Response time (p50, p95, p99)**: Latency distribution for each API endpoint used
- **Error rate**: 4xx and 5xx responses as percentage of total requests
- **Rate limit proximity**: How close to API rate limits (Gumroad, social platforms)
- **Alert threshold**: p95 latency >5s (WATCH), Error rate >5% (ALERT), >80% rate limit (ALERT)

### Agent Performance Metrics
- **Task completion rate**: Tasks completed / Tasks assigned × 100
- **Average cycle time**: Time from task assignment to completion
- **Error/retry rate**: How often agent tasks require retry or manual intervention
- **Queue depth**: How many tasks are waiting per agent
- **Use**: Feed into bottleneck detection (reference: bottleneck-detection.md)

---

## 7. Operational Efficiency Metrics

### Workflow Velocity
- **Definition**: Speed at which work moves through the system from initiation to completion
- **Calculation**: Completed tasks per unit time, segmented by task type
- **Comparison context**: WoW, by task type, by agent

### Effort-to-Output Ratio
- **Definition**: Input effort (time, content pieces, posts) vs output (revenue, engagement, conversions)
- **Calculation**: Output metric / Input metric (e.g., Revenue per content piece published)
- **Use**: Identifies the most and least efficient activities

### Automation Coverage
- **Definition**: Percentage of repeatable tasks that are automated vs manual
- **Calculation**: (Automated task completions / Total task completions) × 100
- **Use**: Identifies automation opportunities

---

## 8. Composite Scores

### Business Health Index (BHI)
- **Definition**: Single number representing overall business health
- **Calculation**: Weighted composite of:
  - Revenue trend score (weight: 0.30) — trailing 14-day slope, normalized 0-100
  - Conversion rate vs benchmark (weight: 0.20) — percent of benchmark, capped at 100
  - System health score (weight: 0.20) — uptime and cron health composite
  - Traffic trend score (weight: 0.15) — trailing 14-day slope, normalized 0-100
  - Content engagement trend (weight: 0.15) — cross-platform engagement trend
- **Scale**: 0-100
  - 80-100: Excellent — systems humming, revenue growing, content resonating
  - 60-79: Good — stable operations, minor areas for improvement
  - 40-59: Attention needed — one or more areas underperforming
  - 20-39: Warning — multiple systems or metrics in decline
  - 0-19: Critical — immediate investigation required
- **Use**: The one number to start every weekly signal memo with

### Channel Efficiency Score
- **Definition**: Composite efficiency of each traffic/content channel
- **Calculation**: Revenue attributed to channel / Effort invested in channel
- **Effort proxies**: Posts created, time spent, tools used
- **Use**: Rank channels by ROI to inform content allocation decisions

---

## 9. Metric Relationships Map

Understanding how metrics cause or correlate with each other prevents misdiagnosis.

### Causal Chains (proven or strong evidence)
```
Content published → Platform impressions → Clicks to Gumroad → Product views → Sales → Revenue
Cron job failure → Missed automation → Manual work increase → Cycle time increase
Product price change → Conversion rate change → Revenue change (direction depends on elasticity)
```

### Common Correlations (NOT proven causal, investigate before concluding)
```
Twitter/X reply rate ↔ Follower growth (algorithm rewards replies, but both may be caused by content quality)
Pinterest save rate ↔ Long-term click volume (saves extend content lifespan)
Reddit karma ↔ Profile clicks (high karma builds credibility → clicks, but correlation varies by subreddit)
Product view decline ↔ Revenue decline (usually causal, but could be seasonal)
```

### Common Misdiagnoses to Avoid
- "Revenue dropped because traffic dropped" — Check: did conversion rate change too? Traffic drop with stable conversion = traffic problem. Traffic drop with conversion drop = might be a different audience arriving.
- "This product isn't selling because the price is too high" — Check: is the VIEW count adequate? If nobody's seeing it, price is irrelevant.
- "Twitter/X isn't working" — Check: are you measuring the right thing? Impressions alone mean nothing. Replies and link clicks are what matter.
- "Pinterest is our best channel" — Check: best by what metric? Highest traffic ≠ highest revenue. Calculate revenue per click by channel.

---

## 10. Leading vs Lagging Indicator Guide

### Leading Indicators (predict future outcomes)
- Content engagement rates (predict future traffic)
- Pinterest pin velocity in first 48 hours (predicts pin lifetime performance)
- Twitter/X reply rate (predicts algorithm distribution → future impressions)
- Product page view trends (predict future revenue)
- Cron job error rate increase (predicts future system failures)
- Session expiry countdown (predicts future access issues)
- Queue depth increase (predicts future bottlenecks)

### Lagging Indicators (confirm past outcomes)
- Revenue (result of traffic + conversion + pricing — all lagging by the time money hits)
- Monthly active users (slow-moving aggregate)
- Refund rate (only visible after purchase)
- Cumulative content library size (grows slowly)

### The Principle
Use leading indicators for EARLY WARNING and proactive adjustment.
Use lagging indicators for CONFIRMATION and strategic assessment.
Never make urgent decisions based only on lagging indicators — by definition, you're reacting to something that already happened.
