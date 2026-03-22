# Statistical Methods & Rigor

The statistical toolkit for rigorous analysis. When to use each method, how to apply it correctly, and how to communicate results honestly.

---

## Table of Contents
1. Statistical Thinking for Analysts
2. Descriptive Statistics
3. Significance Testing
4. Confidence Intervals
5. Regression Analysis
6. Correlation Analysis
7. A/B Test Evaluation
8. Cohort Analysis Methods
9. Time Series Methods
10. Small Sample Strategies

---

## 1. Statistical Thinking for Analysts

### The Three Questions Before Any Analysis
1. **What am I trying to learn?** (The question must be specific and answerable with data)
2. **Is my data adequate?** (Sample size, quality, relevance, time period)
3. **What are the limitations?** (Always identify before concluding, not after)

### Signal vs Noise
Every metric has natural variation (noise). The Analyst's job is to determine whether observed
changes are SIGNAL (real, meaningful) or NOISE (random, meaningless).

Rules of thumb:
- Single data point: Almost certainly noise unless extreme (>3 sigma)
- 3-5 data points in same direction: Possibly signal. Monitor.
- 7+ data points in same direction: Almost certainly signal. Investigate.
- Magnitude matters: A 50% change is more likely signal than a 2% change
- Context matters: A change coinciding with a known action is more likely signal

---

## 2. Descriptive Statistics

### Core Measures
For any metric, compute and report:
- **Mean**: Average value. Sensitive to outliers.
- **Median**: Middle value. Robust to outliers. Prefer for skewed data.
- **Standard deviation**: Spread of values. Defines "normal range."
- **Min/Max**: Extreme values. Flags data quality issues.
- **Percentiles** (25th, 75th, 90th, 95th): Full distribution picture.

### When to Use Mean vs Median
```
Symmetric data (roughly bell-shaped): Mean and median are similar. Use mean.
Skewed data (long tail on one side): Mean is pulled toward the tail. Use median.
Revenue data: Often skewed (a few big sales). Use median for "typical" day, mean for totals.
Latency data: Always skewed. Use median and p95/p99 for performance.
```

### Rolling Statistics
For time-series data, compute rolling (moving) versions:
- **7-day rolling average**: Smooths daily noise, preserves weekly patterns
- **28-day rolling average**: Smooths weekly noise, reveals monthly trends
- **Rolling standard deviation**: Tracks whether variability itself is changing

---

## 3. Significance Testing

### When to Use
Use significance testing when answering: "Is this change REAL or could it be random chance?"

Common scenarios:
- Revenue changed after a price adjustment — is the change real?
- Conversion rate differs between two products — is the difference meaningful?
- Content engagement changed after a format shift — signal or noise?

### The Basics
```
Null hypothesis (H₀): There is no real change. The observed difference is due to random variation.
Alternative hypothesis (H₁): There IS a real change.

p-value: The probability of seeing this result (or more extreme) if H₀ is true.
  p < 0.05: Statistically significant (conventionally). Reject H₀.
  p < 0.01: Highly significant.
  p > 0.05: Not statistically significant. Cannot reject H₀. (This does NOT mean H₀ is true.)
```

### Practical Significance vs Statistical Significance
A change can be statistically significant but practically meaningless:
- "Conversion rate changed from 2.50% to 2.52% (p=0.03)" — statistically significant but
  irrelevant for business decisions.

A change can be practically important but not yet statistically significant:
- "Conversion rate changed from 2.5% to 3.5% but we only have 100 observations (p=0.12)" —
  probably real, need more data.

**Always report both statistical significance AND practical significance (effect size).**

### Effect Size
```
For percentage changes: Report the absolute and relative change
  "Conversion rate increased from 2.5% to 3.1% (+0.6 percentage points, +24% relative)"

For continuous metrics: Report Cohen's d or similar
  Small effect: d = 0.2
  Medium effect: d = 0.5
  Large effect: d = 0.8
```

---

## 4. Confidence Intervals

### What They Are
A confidence interval gives a RANGE of plausible values for the true metric, given the data.
"Our conversion rate is 3.2% (95% CI: 2.8%-3.6%)" means we're 95% confident the true rate
is between 2.8% and 3.6%.

### When to Use
- Reporting metrics where precision matters
- Comparing two metrics (do their CIs overlap? If not, they're likely different)
- Forecasting (present forecasts as ranges, not point estimates)

### Practical Guidelines
- **Wide CI**: Not enough data to be precise. Communicate this uncertainty.
- **Narrow CI**: High precision. Can be confident in the point estimate.
- **Overlapping CIs**: Metrics might not be truly different. Don't conclude they are.
- **Non-overlapping CIs**: Strong evidence of a real difference.

---

## 5. Regression Analysis

### When to Use
- Modeling how one metric affects another (price → conversion rate)
- Trend lines (revenue over time)
- Forecasting (projecting trends forward)

### Simple Linear Regression
```
y = mx + b

Where:
  y = dependent variable (what you're predicting)
  x = independent variable (what you're using to predict)
  m = slope (how much y changes per unit change in x)
  b = intercept

For trend analysis: x = time, y = metric value
Slope m tells you the rate of change per time period
```

### What to Report
- **Slope**: The rate of change (and its direction)
- **R²**: How much of the variation is explained (0-1, higher = better fit)
- **p-value of slope**: Is the trend statistically significant?
- **Residuals**: Are the prediction errors random? If not, the model may be wrong.

### Caution
Regression shows ASSOCIATION, not causation. "Revenue increases with Pinterest clicks" does not
mean Pinterest clicks CAUSE revenue. Both might be driven by a third factor.

---

## 6. Correlation Analysis

### Computing Correlation
```
Pearson's r: Measures linear relationship between two variables
  Range: -1 to +1
  +1 = perfect positive correlation
   0 = no linear relationship
  -1 = perfect negative correlation

Interpretation:
  |r| > 0.7: Strong correlation
  |r| 0.4-0.7: Moderate correlation
  |r| 0.2-0.4: Weak correlation
  |r| < 0.2: Negligible correlation
```

### The Causation Firewall (Restated for Emphasis)
Finding a correlation between X and Y can mean:
1. X causes Y
2. Y causes X
3. Z causes both X and Y
4. Coincidence

NEVER leap to interpretation 1 without strong evidence. The Analyst reports correlations
as correlations, period. Causal claims require controlled experiments or clear mechanisms.

### Useful Correlations to Track
- Pinterest click volume ↔ Revenue (should be positive, strength indicates channel quality)
- Twitter/X reply rate ↔ Follower growth (algorithm-mediated relationship)
- Content volume ↔ Traffic (more content → more traffic, but with diminishing returns)
- Price ↔ Conversion rate (usually negative, strength indicates price sensitivity)

---

## 7. A/B Test Evaluation

### Framework for Evaluating Tests
When a change is tested (new price, new page copy, new content format):

```
BEFORE:
  Sample size: [N observations]
  Metric value: [value ± standard error]
  Time period: [dates]

AFTER:
  Sample size: [N observations]
  Metric value: [value ± standard error]
  Time period: [dates]

COMPARISON:
  Absolute change: [difference in metric]
  Relative change: [% change]
  Statistical significance: [p-value]
  Practical significance: [effect size interpretation]
  Confidence interval for difference: [range]
  
CONCLUSION:
  [Significant improvement / No significant change / Significant decline]
  Confidence: [High/Medium/Low based on sample size and effect clarity]
```

### Minimum Sample Sizes
Rule of thumb: To detect a 10% relative change with 80% power:
- For proportions (conversion rates): ~400 observations per group
- For means (revenue): ~200 observations per group, depending on variance
- Smaller changes need larger samples

If you don't have enough data: SAY SO. "The change appears positive (+15%) but with only 50
observations, we cannot rule out random variation. Recommend continuing the test for 2 more weeks."

---

## 8. Cohort Analysis Methods

### Building Cohort Tables
```
Cohort: Customers grouped by first-purchase month

         Month 0  Month 1  Month 2  Month 3
Jan 2025   100      12       8        5
Feb 2025    85      10       6        —
Mar 2025    92      11       —        —
Apr 2025   110       —       —        —

Cells show: repeat purchase count (or revenue, or any metric)
```

### Retention Curve Analysis
```
Retention Rate = Cohort members active in month N / Original cohort size × 100

Healthy pattern: Initial drop-off (Month 0→1), then stabilizing
Concerning: Continuous decline with no stabilization
Strong: Stabilization above industry average retention
```

### Cohort Comparison
Compare cohorts to identify:
- Is customer QUALITY improving or declining over time?
- Did a specific change (price, platform, content) produce better/worse customers?
- Are newer cohorts more or less likely to repeat-purchase?

---

## 9. Time Series Methods

### Decomposition
Every time series can be decomposed into:
```
Observed = Trend + Seasonality + Residual

Trend: The long-term direction (growth, decline, stable)
Seasonality: Repeating patterns (day-of-week, monthly, annual)
Residual: What's left after removing trend and seasonality (random noise + anomalies)
```

Anomaly detection should be applied to RESIDUALS, not the raw series. This prevents
seasonal patterns from being flagged as anomalies.

### Moving Averages
```
Simple Moving Average (SMA): Equal weight to all points in window
  Use: General smoothing. 7-day SMA for daily data.

Exponential Moving Average (EMA): More weight to recent points
  Use: When recent data matters more. Better for detecting recent trend changes.
  
Weighted Moving Average (WMA): Custom weights
  Use: When specific time periods are more relevant
```

### Trend Detection
```
1. Compute 7-day or 14-day SMA
2. Fit linear regression to the SMA
3. Slope sign = trend direction
4. Slope magnitude = trend strength
5. p-value of slope = trend significance
6. Second derivative = acceleration/deceleration
```

---

## 10. Small Sample Strategies

When data is limited (common for new products, new channels, or niche segments):

### Bayesian Reasoning
Instead of "is this significant?", think "how should this update my beliefs?"
```
Prior: What I expected before seeing the data
Evidence: What the data shows
Posterior: Updated belief combining prior and evidence

With small samples, the prior has more influence (appropriate — we shouldn't overreact to limited data)
With large samples, the evidence dominates (appropriate — the data speaks for itself)
```

### Practical Small-Sample Rules
- **N < 20**: Report descriptives only. DO NOT compute significance tests. They're meaningless.
- **N = 20-50**: Report with heavy caveats. Compute significance but note low power.
- **N = 50-100**: Standard analysis is becoming reliable. Report with moderate caveats.
- **N > 100**: Standard analysis is reliable. Report normally.

### Combining Evidence
When individual data points are too few, combine:
- Multiple weeks of data (aggregate to get larger N)
- Similar products (pool data with appropriate adjustments)
- Cross-platform data (if measuring the same underlying behavior)

Always disclose the aggregation and its assumptions.
