# Revenue Analytics

Deep-dive reference for all revenue analysis: tracking, attribution, forecasting, diagnostics, and optimization signals.

---

## Table of Contents
1. Daily Revenue Analysis Protocol
2. Product-Level Revenue Diagnostics
3. Revenue Attribution by Source
4. Price Point Analysis
5. Revenue Trend Detection
6. Cohort Revenue Analysis
7. Revenue Forecasting Methods
8. Refund Analytics
9. Revenue Anomaly Investigation
10. Revenue Report Templates

---

## 1. Daily Revenue Analysis Protocol

Every day, compute and record:

### The Daily Revenue Card
```
DATE: [YYYY-MM-DD]
GROSS REVENUE: $[amount]
  vs Yesterday: [+/-$amount] ([+/-%])
  vs Same Day Last Week: [+/-$amount] ([+/-%])
  vs 7-Day Rolling Average: [+/-$amount] ([+/-%])

NET REVENUE: $[amount] (after $[refunds] refunds, $[fees] platform fees)
TRANSACTIONS: [count]
  vs 7-Day Average: [+/-count] ([+/-%])

AOV: $[amount]
  vs 7-Day Average: [+/-$amount]

TOP PRODUCT: [product_name] — $[amount] ([count] sales)
BOTTOM PRODUCT (with >0 sales): [product_name] — $[amount] ([count] sales)

REVENUE SOURCES:
  Pinterest: $[amount] ([%] of total, [count] transactions)
  Twitter/X:  $[amount] ([%] of total, [count] transactions)
  Reddit:     $[amount] ([%] of total, [count] transactions)
  Direct:     $[amount] ([%] of total, [count] transactions)
  Search:     $[amount] ([%] of total, [count] transactions)
  Other:      $[amount] ([%] of total, [count] transactions)

STATUS: [NORMAL / WATCH: {reason} / ALERT: {reason}]
```

### Daily Checks (automated, run at 00:30 UTC)
1. Pull yesterday's sales from Gumroad API
2. Compute all metrics in the Daily Revenue Card
3. Compare against rolling averages and benchmarks
4. Flag any ALERT or WATCH conditions
5. Store the card for weekly/monthly aggregation
6. If ALERT: immediately notify (format: short alert, not full card)

---

## 2. Product-Level Revenue Diagnostics

### The Product Revenue Matrix

For every active product, maintain a rolling assessment:

```
PRODUCT: [name] (ID: [gumroad_id])
PRICE: $[listed_price]
LIFECYCLE: [Launch / Growth / Mature / Declining]

REVENUE (trailing 7 days): $[amount]
  vs Prior 7 days: [+/-$amount] ([+/-%])
  vs 4-Week Average (weekly): [+/-$amount] ([+/-%])

VIEWS (trailing 7 days): [count]
  vs Prior 7 days: [+/-count] ([+/-%])

CONVERSION RATE: [%]
  vs Product's Historical Average: [+/-pp]
  vs Category Benchmark: [+/-pp]

DIAGNOSTIC:
  Views trend: [Rising / Stable / Falling]
  Conversion trend: [Rising / Stable / Falling]
  Revenue trend: [Rising / Stable / Falling]

DIAGNOSIS: [see Diagnostic Matrix below]
RECOMMENDED ACTION: [specific recommendation]
```

### The Diagnostic Matrix

| Views | Conversion | Revenue | Diagnosis | Action |
|-------|-----------|---------|-----------|--------|
| Rising | Rising | Rising | Star performer | Scale traffic investment. Double down on what's working. |
| Rising | Stable | Rising | Healthy growth | Continue current approach. Monitor conversion for softening. |
| Rising | Falling | Stable/Rising | Traffic quality issue | Audit new traffic sources. Higher volume but lower-intent visitors. |
| Rising | Falling | Falling | Conversion crisis | Urgent: page, price, or offer problem. New traffic isn't converting. |
| Stable | Rising | Rising | Conversion improvement | Something improved on the page/offer. Identify and replicate. |
| Stable | Stable | Stable | Steady state | Maintain. Consider testing a variable to drive improvement. |
| Stable | Falling | Falling | Conversion decay | Page may be stale, or audience needs shifted. Test new copy/price. |
| Falling | Rising | Stable | Traffic contraction, surviving on quality | Find new traffic sources before quality gain is exhausted. |
| Falling | Stable | Falling | Traffic problem | Content/SEO for this product needs investment. Product itself is fine. |
| Falling | Falling | Falling | Double decline | Fundamental problem. Deep investigation: is this product still viable? |

### Product Comparison (Weekly)
Rank all products by:
1. **Revenue** (absolute — who's earning?)
2. **Conversion rate** (efficiency — who converts best?)
3. **Revenue trend** (momentum — who's accelerating?)
4. **Health score** (composite — see kpi-definitions.md)

Highlight any product that moved >2 ranks in any dimension. Movement = signal.

---

## 3. Revenue Attribution by Source

### Attribution Model
Use **last-click attribution** as the primary model (Gumroad's referrer field = last click).
Acknowledge limitations: this undervalues top-of-funnel platforms that create awareness but don't get the last click.

### Revenue per Visit by Source
```
For each source:
  Revenue per Visit = Revenue from source / Total visits from source
  
Rank sources by Revenue per Visit, not by total revenue or total traffic.
```

This is THE metric for deciding where to invest content effort. Example:
- Pinterest: 10,000 visits, $500 revenue → $0.05/visit
- Twitter/X: 2,000 visits, $300 revenue → $0.15/visit
- Reddit: 500 visits, $200 revenue → $0.40/visit

In this example, Reddit has the HIGHEST quality traffic despite the lowest volume. This is the kind of
insight that changes resource allocation decisions.

### Source Trend Analysis
Track revenue per visit by source over time (weekly). A declining revenue-per-visit from a source
could mean:
- Audience saturation (you're reaching less-interested people)
- Content quality decline on that platform
- Platform algorithm change affecting who sees your content
- Competitor activity on that platform

---

## 4. Price Point Analysis

### Price Tier Performance
Group products into price tiers and compute per-tier metrics:

```
TIER: $[range]
  Products in tier: [count]
  Total views: [count]
  Total sales: [count]
  Conversion rate: [%]
  Revenue: $[amount]
  AOV: $[amount]
  Revenue share: [% of total revenue]
```

### Price Sensitivity Signals
Monitor for these patterns:
- **Price threshold effect**: Conversion drops sharply at a specific price point (common at $29, $49, $99)
- **Premium positioning**: Higher-priced products with HIGHER conversion rates (signals strong value proposition)
- **Race to bottom**: Lower-priced products cannibalizing higher-priced alternatives
- **Bundle opportunity**: Multiple low-price purchases from same buyer = bundle candidate

### Price Change Impact Assessment
When a price is changed, track:
- Conversion rate before vs after (7-day rolling average both sides)
- Revenue per day before vs after
- Revenue per VISITOR before vs after (the real test)
- Allow 7-14 days for stabilization before concluding. First 48 hours may show aberrant behavior.

---

## 5. Revenue Trend Detection

### Trend Classification
For any revenue time series, classify the trend:

```
ACCELERATING: Positive slope AND increasing rate of change (growth is speeding up)
GROWING: Positive slope, stable rate of change (steady growth)
DECELERATING: Positive slope BUT decreasing rate of change (still growing but slowing)
STABLE: Near-zero slope within normal variance
SOFTENING: Slightly negative slope but within historical variance
DECLINING: Negative slope outside normal variance
COLLAPSING: Negative slope AND increasing rate of decline (decline is accelerating)
```

### How to Compute
1. Calculate 7-day rolling average to smooth daily noise
2. Compute the slope of the rolling average over the assessment period (14 or 28 days)
3. Compute the second derivative (rate of change of the slope) to classify acceleration/deceleration
4. Compare slope magnitude to historical variance to determine if movement is significant

### Trend Break Detection
A trend break occurs when the direction changes (e.g., growing → declining):
- Confirm with at least 5 consecutive days in the new direction
- Or a single-day movement >3 standard deviations from the rolling average
- Trend breaks ALWAYS get flagged in the weekly signal memo

---

## 6. Cohort Revenue Analysis

### Monthly Cohort Definition
- A cohort = all customers who made their FIRST purchase in a given month
- Track each cohort's behavior over time

### Cohort Metrics
For each cohort, track:
- **Cohort size**: Number of first-time buyers in the month
- **First purchase AOV**: Average first-order value
- **Repeat purchase rate**: % who bought again within 30, 60, 90 days
- **LTV (to date)**: Total revenue from this cohort / Cohort size
- **Time to second purchase**: Median days between first and second purchase

### Why Cohort Analysis Matters
Aggregate revenue can mask problems:
- Revenue rising from new customer acquisition even as existing customers churn
- Revenue stable because price increases offset volume decline
- A specific acquisition channel bringing in low-LTV customers

Cohort analysis reveals the QUALITY of revenue, not just the QUANTITY.

---

## 7. Revenue Forecasting Methods

### Method 1 — Simple Run Rate
```
Monthly Forecast = (Revenue this month to date / Days elapsed) × Days in month
```
- **When to use**: Quick and dirty, early in month
- **Limitations**: Assumes uniform daily distribution. Poor if weekday/weekend patterns exist.

### Method 2 — Trailing Average Projection
```
Monthly Forecast = 30-day trailing average daily revenue × Days remaining + Revenue to date
```
- **When to use**: Standard method, works well for stable businesses
- **Limitations**: Lags behind trend changes

### Method 3 — Trend-Adjusted Projection
```
1. Compute 14-day linear regression slope
2. Project slope forward for remaining days in period
3. Monthly Forecast = Revenue to date + SUM(projected daily values)
```
- **When to use**: When there's a clear trend (growing or declining)
- **Limitations**: Over-projects if trend is temporary

### Method 4 — Scenario Modeling
```
Optimistic: Best 14-day trailing average × remaining days
Base: Median 14-day trailing average × remaining days
Conservative: Worst 14-day trailing average × remaining days
```
- **When to use**: For planning and decision-making
- **Present as**: Range with confidence indicator

### Forecast Confidence
- **Days 1-7 of month**: Low confidence. Present as wide range only.
- **Days 8-15**: Medium confidence. Present run rate and trailing average.
- **Days 16-25**: High confidence. Present trend-adjusted with scenario range.
- **Days 26+**: Very high confidence. Present near-certain figure with narrow range.

---

## 8. Refund Analytics

### Refund Metrics
- **Refund rate**: Refunds / Total sales × 100
- **Refund rate by product**: Identifies problematic products
- **Refund rate by source**: Identifies traffic sources bringing low-quality buyers
- **Time to refund**: How long after purchase refunds typically occur
- **Refund reason analysis**: If reasons are available, categorize and rank

### Refund Alert Thresholds
- Overall refund rate >5%: ALERT — investigate immediately
- Overall refund rate >3%: WATCH — include in weekly memo
- Any single product >10% refund rate: ALERT — product may have a quality or expectation issue
- Sudden spike (>2x trailing average): ALERT — could indicate broken product or mismatched traffic

### What High Refund Rates Mean
- **Product-wide**: Description doesn't match product, quality issue, or wrong audience
- **Source-specific**: Traffic source attracting tire-kickers or mismatched audience
- **Price-specific**: Buyer's remorse at certain price points
- **Time-clustered**: Something happened (bad review, misleading content) at a specific time

---

## 9. Revenue Anomaly Investigation

When revenue is anomalous (>1.5 standard deviations from rolling average), run this investigation:

### Step 1: Scope the Anomaly
- Is it total revenue or product-specific?
- Is it transaction count, AOV, or both?
- When exactly did it start? (Narrow to the hour if possible)

### Step 2: Check Traffic
- Did traffic volume change? (If yes → traffic problem, investigate content/platform)
- Did traffic SOURCE mix change? (If yes → attribution shift, check each source)
- If traffic is stable → conversion problem

### Step 3: Check Conversion
- Did conversion rate change? (If yes → something changed on the product page, price, or offer)
- Did conversion change uniformly or for specific products?
- Is the change in conversion aligned with a known action (price change, page update, etc.)?

### Step 4: Check External Factors
- Platform algorithm changes (Pinterest, Twitter/X, Reddit)
- Seasonal effects (holidays, weekends, paydays)
- Competitor actions (new competing product, price undercut)
- Media mentions or viral content (positive or negative)

### Step 5: Classify and Report
```
ANOMALY REPORT
Date detected: [date]
Metric affected: [metric]
Magnitude: [actual vs expected, +/-%, sigma deviation]
Duration: [hours/days]

ROOT CAUSE HYPOTHESIS: [most likely cause based on investigation]
CONFIDENCE: [High / Medium / Low]
SUPPORTING EVIDENCE: [what supports this hypothesis]
ALTERNATIVE HYPOTHESES: [what else could explain it]

RECOMMENDATION: [specific action to take]
MONITORING PLAN: [how to track if the anomaly resolves or worsens]
```

---

## 10. Revenue Report Templates

### Daily Revenue Summary (automated, internal)
One-paragraph summary with key numbers. Only flag ALERTs and WATCHes. No analysis unless anomalous.

### Weekly Revenue Section (for Signal Memo)
```
## Revenue Signal

**This Week**: $[amount] | **vs Last Week**: [+/-$amount] ([+/-%]) | **vs 4-Week Avg**: [+/-$amount] ([+/-%])
**Trend**: [Accelerating / Growing / Stable / Softening / Declining]
**Run Rate (Monthly)**: $[amount]

### What moved:
- [Top signal — biggest revenue driver or detractor this week]
- [Second signal]
- [Third signal if material]

### Product highlights:
- Best performer: [product] — $[amount], [conversion]% conversion
- Needs attention: [product] — [specific issue identified]

### Source performance:
- Strongest: [source] ($[RPV] revenue per visit)
- Weakest: [source] ($[RPV] revenue per visit)
```

### Monthly Revenue Deep-Dive (comprehensive)
Full analysis covering all sections in this reference. Include visualizations.
Delivered as a structured document (Markdown or DOCX).
