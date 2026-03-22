# Forecasting & Trend Analysis

How to detect trends, project trajectories, model scenarios, and communicate forecasts with appropriate uncertainty.

---

## Table of Contents
1. Forecasting Principles
2. Trend Detection Methods
3. Growth Rate Calculations
4. Run-Rate Projections
5. Scenario Modeling
6. Leading Indicator Tracking
7. Inflection Point Detection
8. Momentum Scoring
9. Forecast Accuracy Tracking
10. Forecast Report Templates

---

## 1. Forecasting Principles

### What Forecasting IS
- An informed estimate of future values based on current data and patterns
- A range of possibilities with associated probabilities
- A tool for planning, not a promise

### What Forecasting is NOT
- A prediction of what WILL happen (uncertainty is inherent)
- A commitment or target (those are set by strategy, not by analysis)
- Reliable far into the future (confidence degrades rapidly with time horizon)

### The Forecast Confidence Horizon
```
1-7 days out:   HIGH confidence (unless major disruption)
8-14 days out:  MEDIUM confidence (trends may shift)
15-30 days out: LOW-MEDIUM confidence (increasing uncertainty)
31-90 days out: LOW confidence (directional only, not precise)
90+ days out:   VERY LOW confidence (scenario-based only, not point estimates)
```

Always disclose the time horizon and confidence level with every forecast.

### The Cardinal Rule
**Never present a point forecast without a range.** A forecast of "$5,000 monthly revenue" is less
honest and less useful than "$4,200-$5,800 monthly revenue (80% confidence interval)."

---

## 2. Trend Detection Methods

### Method 1: Linear Regression Trend
```
1. Collect metric values over assessment period (minimum 14 days, prefer 28)
2. Fit linear regression: value = slope × day + intercept
3. Slope = trend rate (units per day)
4. R² = how well the line fits (>0.7 = strong trend, <0.3 = no clear trend)
5. p-value of slope = statistical significance of the trend
```

Use when: Trends appear roughly linear (steady growth or decline).

### Method 2: Moving Average Crossover
```
Short-term MA: 7-day moving average
Long-term MA: 28-day moving average

Bullish crossover: Short MA crosses ABOVE long MA → uptrend beginning
Bearish crossover: Short MA crosses BELOW long MA → downtrend beginning
```

Use when: Looking for trend CHANGES rather than steady trends.

### Method 3: Rate of Change
```
ROC = (Current value - Value N periods ago) / Value N periods ago × 100

7-day ROC: Short-term momentum
14-day ROC: Medium-term trend
28-day ROC: Established trend
```

Use when: You want to quantify how fast things are changing.

### Trend Classification System
Based on analysis, classify each metric's trend:

```
ACCELERATING GROWTH:  Positive slope AND ROC increasing
                      The metric is growing and the growth rate is increasing.

STEADY GROWTH:        Positive slope AND ROC stable
                      Growing at a consistent rate.

DECELERATING GROWTH:  Positive slope AND ROC decreasing
                      Still growing but the growth rate is slowing.

PLATEAUING:           Near-zero slope, ROC near zero
                      Stable. Neither growing nor declining meaningfully.

SOFTENING:            Slightly negative slope, within 1 sigma of normal variance
                      Trending down but could be noise. Monitor.

DECLINING:            Negative slope outside normal variance
                      Real decline. Investigate cause.

ACCELERATING DECLINE: Negative slope AND ROC becoming more negative
                      Declining and the decline is getting worse. Urgent.
```

---

## 3. Growth Rate Calculations

### Week-over-Week (WoW) Growth
```
WoW = (This week's value - Last week's value) / Last week's value × 100
```
Use for: Short-term momentum tracking. Include in weekly signal memo.

### Month-over-Month (MoM) Growth
```
MoM = (This month's value - Last month's value) / Last month's value × 100
```
Use for: Monthly reports and trend assessment.

### Compound Weekly Growth Rate (CWGR)
```
CWGR = (End value / Start value)^(1/N weeks) - 1
```
Use for: Smoothed growth rate over a multi-week period. Better than single-week WoW
which can be noisy.

### Year-over-Year (YoY) Growth
```
YoY = (This period's value - Same period last year) / Same period last year × 100
```
Use for: Removing seasonal effects. Only available after 12+ months of data.

### Growth Rate Red Flags
- Growth rate declining for 4+ consecutive weeks → DECELERATION signal
- Growth rate turned negative after being positive → TREND REVERSAL (ALERT)
- Growth rate is high but base is tiny → "Growing 200%!" means less when it's $10 to $30
- Growth rate is inconsistent (jumping between +30% and -20%) → VOLATILE, don't over-interpret

---

## 4. Run-Rate Projections

### Daily Run Rate
```
Daily Run Rate = Trailing 7-day total / 7
Monthly Projection = Daily Run Rate × Days in month
Annual Projection = Daily Run Rate × 365
```

### Adjusted Run Rate (incorporating trend)
```
1. Compute 14-day linear regression slope (daily change)
2. For each remaining day in the projection period, estimate:
   Projected daily value = Current daily run rate + (slope × days forward)
3. Sum all projected daily values = Adjusted projection
```

This is more accurate than flat run rate when there's a clear trend.

### Run Rate Confidence
```
EARLY MONTH (days 1-7):    Low confidence. Wide range. Present as "on pace for $X-$Y."
MID MONTH (days 8-20):     Medium confidence. Narrower range. "Tracking toward $X (±15%)."
LATE MONTH (days 21+):     High confidence. Tight range. "Expected: $X (±5%)."
```

### Seasonal Adjustment for Run Rate
If there are known seasonal patterns (weekday vs weekend, beginning vs end of month):
```
Adjusted Run Rate = (Revenue to date) + SUM(expected daily revenue for remaining days)
Where expected daily revenue = historical average for that day-of-week or day-of-month
```

---

## 5. Scenario Modeling

### Three-Scenario Framework
For any forecast, present three scenarios:

```
OPTIMISTIC (P20 — 20% probability of being this good or better):
  Assumptions: Best-case trends continue, no disruptions, key initiatives succeed
  Method: Use the best 7-day period from the trailing 28 days as the run rate
  
BASE CASE (P50 — median expectation):
  Assumptions: Current trends continue with normal variance
  Method: Use trailing 14-day average as the run rate, adjusted for trend
  
CONSERVATIVE (P80 — 80% probability of being this good or better):
  Assumptions: Slight underperformance, minor disruptions
  Method: Use the worst 7-day period from the trailing 28 days as the run rate
```

### When to Use Scenario Modeling
- Monthly and quarterly revenue projections
- Impact assessment of proposed changes (price change, new product launch)
- Risk assessment (what happens if Pinterest traffic drops 30%?)
- Resource planning (how many content pieces needed to hit revenue targets?)

### Scenario Sensitivity Analysis
Identify which INPUT variables have the biggest impact on outcomes:
```
If Pinterest traffic drops 20%, revenue impact = -$X (sensitive)
If conversion rate drops 10%, revenue impact = -$Y (very sensitive)
If Twitter/X engagement drops 30%, revenue impact = -$Z (moderate sensitivity)

CONCLUSION: Conversion rate is the highest-leverage variable. Protect it above all else.
```

---

## 6. Leading Indicator Tracking

### Identifying Leading Indicators
A leading indicator predicts future changes in a lagging indicator BEFORE they happen.

```
PROVEN LEADING INDICATORS:
  Pinterest pin velocity (48h) → Future pin lifetime traffic (7-14 day lead)
  Twitter/X reply rate → Future impression volume (3-7 day lead)
  Content engagement rate → Future traffic volume (7-14 day lead)
  Product page view trend → Future revenue trend (3-7 day lead)
  Cron job error rate increase → Future system failure (hours to days lead)
  Session expiry countdown → Future access loss (exact countdown)
  Queue depth increase → Future bottleneck (hours to days lead)
```

### Leading Indicator Dashboard
Track all leading indicators with their current status:
```
LEADING INDICATOR STATUS:
  Pinterest pin velocity:  🟢 Normal (on pace for typical distribution)
  Twitter/X reply rate:    🟡 Declining (down 15% over 7 days — watch)
  Content engagement:      🟢 Normal
  Product view trend:      🟢 Growing (+8% WoW)
  Cron error rate:         🟢 Low (0.2%)
  Session health:          🟢 All sessions >72h to expiry
  Queue depths:            🟢 Normal

  FORWARD OUTLOOK: Mostly positive. Twitter/X reply rate decline bears watching — 
  if it continues, expect impression decline in 3-7 days.
```

---

## 7. Inflection Point Detection

### What is an Inflection Point?
A moment where a metric's trajectory FUNDAMENTALLY changes. Not a blip — a regime change.

### Detection Criteria
An inflection point is confirmed when:
1. The metric's moving average changes direction (crosses its longer-term MA)
2. The change persists for at least 5 data points
3. The magnitude of change exceeds 1.5 standard deviations from the prior trend
4. No known temporary cause explains it (not a holiday, not a one-time event)

### Inflection Point Alert
```
📍 INFLECTION POINT DETECTED

Metric: [name]
Previous trajectory: [description, e.g., "Growing at ~3% WoW for 8 weeks"]
New trajectory: [description, e.g., "Declining at ~2% WoW for 2 weeks"]
Change detected: [date]
Confidence: [High/Medium — based on data points since the change]
Possible causes: [hypotheses based on coincident events]
Impact: [what this means for downstream metrics and business outcomes]
Recommended action: [investigate, adjust, monitor]
```

---

## 8. Momentum Scoring

### Computing Momentum
Momentum captures both the DIRECTION and STRENGTH of a metric's movement:

```
Momentum Score = (
  ROC_7day × 0.50 +     (recent movement, heavily weighted)
  ROC_14day × 0.30 +    (medium-term trend)
  ROC_28day × 0.20      (established trend)
)

Scale: -100 to +100
  +50 to +100: Strong positive momentum (accelerating growth)
  +10 to +50:  Moderate positive momentum (growing)
  -10 to +10:  Neutral (stable or no clear direction)
  -50 to -10:  Moderate negative momentum (declining)
  -100 to -50: Strong negative momentum (accelerating decline)
```

### Momentum Divergence
When momentum DIVERGES from the absolute level, it's an early warning:
- Metric is high but momentum is negative → Currently good but deteriorating. Early warning.
- Metric is low but momentum is positive → Currently bad but improving. Recovery signal.
- Metric and momentum aligned → Situation is what it appears to be.

Report divergences prominently — they're the most actionable forecasting signals.

---

## 9. Forecast Accuracy Tracking

### Measuring Forecast Quality
After each forecast period completes, compute:
```
Forecast Error = (Actual - Forecast) / Actual × 100

MAPE (Mean Absolute Percentage Error): Average of |Forecast Error| over multiple periods
  Excellent: MAPE < 10%
  Good: MAPE 10-20%
  Fair: MAPE 20-30%
  Poor: MAPE > 30%
```

### Bias Detection
```
If forecasts are consistently HIGH → Optimistic bias. Reduce by X%.
If forecasts are consistently LOW → Pessimistic bias. Increase by X%.
If forecasts are unbiased (average error near zero) but high MAPE → High variance. Widen confidence intervals.
```

### Monthly Forecast Accuracy Report
```
FORECAST ACCURACY — [Month]
  Revenue forecast: $[forecast]
  Revenue actual: $[actual]
  Error: [+/-$] ([+/-%])
  Direction correct: [Yes/No]
  Within confidence interval: [Yes/No]
  
  Trailing 6-month MAPE: [%]
  Bias: [Optimistic / Pessimistic / Unbiased]
  
  Recommendation: [Adjust methodology? Widen intervals? Current approach is working?]
```

---

## 10. Forecast Report Templates

### Weekly Forecast Section (for Signal Memo)
```
## Forward Outlook

**Monthly revenue projection**: $[base case] (range: $[conservative]-$[optimistic])
**Confidence**: [High/Medium/Low based on days remaining and data stability]
**Trend trajectory**: [Accelerating/Steady/Decelerating/Declining]

### Leading indicators:
- [Indicator 1]: [status] → implies [future expectation]
- [Indicator 2]: [status] → implies [future expectation]

### Key risk: [one sentence — the biggest downside risk based on data]
### Key opportunity: [one sentence — the biggest upside signal]
```
