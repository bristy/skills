# Anomaly Detection & Alerting

How to detect meaningful anomalies, calibrate alert thresholds, and avoid alert fatigue.

---

## Table of Contents
1. Anomaly Detection Philosophy
2. Statistical Methods for Anomaly Detection
3. Alert Threshold Calibration
4. Severity Classification
5. Contextual Anomaly Assessment
6. Multi-Signal Correlation
7. False Positive Management
8. Alert Templates

---

## 1. Anomaly Detection Philosophy

### The Two Sins of Anomaly Detection
- **False Negative** (missing a real anomaly): Dangerous — problems go undetected
- **False Positive** (alerting on noise): Expensive — causes alert fatigue, erodes trust in the system

The Analyst must balance both. The goal: catch every anomaly that warrants action, suppress every
fluctuation that doesn't.

### The Action Test
Before generating any alert, ask: "If the right person saw this alert right now, would they DO something
different than they would otherwise?" If the answer is no, it's not an alert — it's a note for the next
scheduled report.

### Two-Tier System
- **ALERT**: Immediate attention required. Would interrupt someone's work. Sent in real-time.
- **WATCH**: Notable but not urgent. Include in next scheduled report. Monitor for escalation.

---

## 2. Statistical Methods for Anomaly Detection

### Method 1: Z-Score (Standard Deviation from Mean)
```
Z = (Current Value - Rolling Mean) / Rolling Standard Deviation

Use: General-purpose anomaly detection for normally distributed metrics
Window: 28-day rolling mean and standard deviation (smooths weekly cycles)
Threshold: |Z| > 2.0 → WATCH, |Z| > 3.0 → ALERT

When to use: Revenue, traffic, engagement rates — metrics with roughly stable variance
When NOT to use: Metrics with strong trends (use detrended version) or extreme skew
```

### Method 2: IQR (Interquartile Range)
```
IQR = Q3 - Q1 (where Q1 = 25th percentile, Q3 = 75th percentile)
Lower fence = Q1 - 1.5 × IQR
Upper fence = Q3 + 1.5 × IQR

Any value outside the fences is an anomaly.
Use: 2.0 × IQR for WATCH, 3.0 × IQR for ALERT

When to use: Metrics that may not be normally distributed, or have outliers in historical data
When NOT to use: Very small datasets (need at least 20 data points for reliable IQR)
```

### Method 3: Rolling Average Deviation
```
Deviation = |Current Value - 7-Day Rolling Average| / 7-Day Rolling Average × 100

>20% deviation → WATCH
>40% deviation → ALERT

When to use: Simple and intuitive. Good for metrics where percentage change matters more than absolute.
When NOT to use: Metrics near zero (small absolute changes create huge percentage swings)
```

### Method 4: Trend Break Detection
```
1. Fit a linear regression to the trailing 14-day data
2. Predict today's value based on the trend
3. If actual value deviates from prediction by >2 standard errors → anomaly

When to use: Detecting when a trend CHANGES DIRECTION (e.g., growing metric suddenly declines)
Advantage: Doesn't flag normal growth/decline as anomalous — only flags unexpected direction changes
```

### Method 5: Seasonal Adjustment
```
1. Compute the average value for this day-of-week over trailing 4 weeks
2. Compare current value to the day-of-week average
3. Apply Z-score or percentage deviation to the seasonally-adjusted value

When to use: Metrics with strong day-of-week patterns (e.g., traffic higher on weekdays)
Why: Without seasonal adjustment, every Saturday looks like a "decline" compared to Friday
```

### Choosing the Right Method
```
Is the metric trending (consistently going up or down)?
├── YES → Use Trend Break Detection (Method 4)
└── NO → Does the metric have day-of-week seasonality?
    ├── YES → Use Seasonal Adjustment (Method 5) + Z-Score or IQR
    └── NO → Is the metric normally distributed?
        ├── YES → Use Z-Score (Method 1)
        ├── UNKNOWN → Use IQR (Method 2) — more robust to non-normality
        └── NO → Use IQR (Method 2)

For quick checks: Rolling Average Deviation (Method 3) works everywhere as a simple sanity check
```

---

## 3. Alert Threshold Calibration

### Initial Threshold Setting
When setting thresholds for a new metric:
1. Collect at least 28 days of baseline data before enabling alerts
2. During baseline period, compute all anomaly detection statistics
3. Set WATCH threshold at the level that would have triggered 2-4 times in the baseline period
4. Set ALERT threshold at the level that would have triggered 0-1 times in the baseline period
5. Adjust based on first month of live operation

### Threshold Tuning
Review alert accuracy monthly:
```
True Positives: Alerts that led to a real finding or action → GOOD
False Positives: Alerts that turned out to be noise → BAD (need to widen threshold)
True Negatives: Normal periods correctly not alerted → GOOD
False Negatives: Real problems that were NOT alerted → BAD (need to tighten threshold)

If False Positive rate > 20%: Widen thresholds by ~30%
If any False Negative on a CRITICAL metric: Tighten threshold immediately
```

### Metric-Specific Thresholds
(Canonical thresholds — adjust based on observed variance)

| Metric | WATCH Threshold | ALERT Threshold |
|--------|----------------|-----------------|
| Daily Revenue | >15% below 7-day avg | >30% below 7-day avg |
| Conversion Rate | >10% below 14-day avg | >25% below 14-day avg |
| Traffic Volume | >20% below 7-day avg | >40% below 7-day avg |
| Cron Job Failure | Any CRITICAL job failure | 2+ consecutive CRITICAL failures |
| Session Expiry | <48h remaining | <24h remaining |
| API Error Rate | >3% | >5% |
| Product Refund Rate | >3% | >5% |
| Pinterest CTR | >30% below 14-day avg | >50% below 14-day avg |
| Twitter/X Reply Rate | >25% below 14-day avg | >50% below 14-day avg |
| Agent Cycle Time | >50% above team median | >100% above team median |
| Queue Depth | >2x 7-day avg | >3x 7-day avg |

---

## 4. Severity Classification

### The Severity Matrix

```
              CRITICAL METRIC            NON-CRITICAL METRIC
LARGE
DEVIATION     SEV-1: IMMEDIATE           SEV-2: SAME-DAY
(>ALERT       Action: Alert now.         Action: Alert within 4h.
 threshold)   Who: Navigator + Hutch     Who: Relevant owner

MODERATE
DEVIATION     SEV-2: SAME-DAY            SEV-3: NEXT REPORT
(>WATCH       Action: Alert within 4h.   Action: Include in weekly memo.
 threshold)   Who: Relevant owner        Who: General audience

SMALL
DEVIATION     SEV-3: NEXT REPORT         SEV-4: LOG ONLY
(<WATCH       Action: Note in report.    Action: Log, no action needed.
 threshold)   Who: General audience      Who: No one unless pattern emerges
```

### Critical Metrics List
These metrics get the highest severity treatment:
- Total daily revenue
- Cron job health (CRITICAL-tier jobs)
- AgentReach session status
- Any metric where failure means revenue stops flowing

### Non-Critical Metrics List
These are important but not urgent:
- Individual content piece performance
- Platform-specific engagement rates
- Non-critical cron jobs
- Optimization metrics

---

## 5. Contextual Anomaly Assessment

Not every statistical anomaly is a real-world anomaly. Apply context:

### Known Context Filters
Before alerting, check if the anomaly has a known explanation:
- **Day of week**: Is this a normal weekend pattern?
- **Holiday/event**: Is today a holiday, event, or known quiet period?
- **Known change**: Was a price, page, or product changed recently? (Expected impact)
- **Platform outage**: Is the source platform experiencing issues? (Not our problem)
- **Seasonal pattern**: Is this consistent with the same period last year/month?

If a known context fully explains the anomaly: Downgrade to LOG ONLY, note the context.
If a known context partially explains it: Keep the alert but include the context.
If no known context: Full alert.

### The "Both Sides" Rule
Always check both directions:
- Anomalous DECLINE → investigate (something may be broken)
- Anomalous SPIKE → also investigate (could be a one-time event, not sustainable growth)
- Unexpected improvements deserve the same scrutiny as unexpected declines. If you don't understand
  why something got better, you can't reproduce it or protect it.

---

## 6. Multi-Signal Correlation

### Correlated Anomalies
When multiple metrics are anomalous simultaneously, they often share a root cause.
Group correlated anomalies into a single alert with a common hypothesis.

Example:
```
Instead of 3 separate alerts:
  ALERT: Pinterest click volume down 30%
  ALERT: Gumroad product page views down 25%
  ALERT: Revenue down 20%

Generate one correlated alert:
  ALERT: Revenue Decline Cascade
  - Revenue down 20%, product views down 25%, Pinterest clicks down 30%
  - Pattern: Upstream traffic decline is cascading through the funnel
  - Most likely root cause: Pinterest distribution issue (investigate algorithm change or pin performance)
```

### Correlation Detection
When an anomaly fires:
1. Check all related metrics within ±24 hours
2. If >2 related metrics are simultaneously anomalous, group them
3. Identify the most upstream anomaly (likely root cause)
4. Present as a single correlated alert with the full cascade

### Independence Verification
If anomalies appear correlated but shouldn't be (unrelated systems), flag as especially noteworthy.
Independent simultaneous anomalies suggest a COMMON external cause (infrastructure issue, environment change).

---

## 7. False Positive Management

### Tracking Alert Accuracy
For every alert generated, log the outcome:
```
ALERT LOG:
  Alert ID: [unique]
  Timestamp: [when fired]
  Metric: [what was anomalous]
  Severity: [SEV-1/2/3/4]
  Outcome: [TRUE_POSITIVE / FALSE_POSITIVE / INCONCLUSIVE]
  Action Taken: [what was done]
  Notes: [any context]
```

### Monthly Alert Quality Report
```
Total alerts: [count]
True positives: [count] ([%])
False positives: [count] ([%])
Inconclusive: [count] ([%])
Mean time to resolution: [duration]

False positive rate by metric:
- [Metric A]: [rate] — [action: widen threshold / add context filter / no change]
- [Metric B]: [rate] — [action]

Recommendations:
- [Specific threshold adjustments]
- [New context filters to add]
- [Metrics to start/stop monitoring]
```

### Alert Fatigue Prevention
- If a metric generates >3 false positives in a month: Widen threshold or add context filters
- If a metric is consistently noisy: Move from ALERT to WATCH tier
- Combine related alerts (per Section 6) to reduce alert volume
- Every alert must pass the Action Test: would someone DO something?
- Review and prune alert rules quarterly

---

## 8. Alert Templates

### Immediate Alert (SEV-1 / SEV-2)
```
🔴 ALERT: [Brief description]

METRIC: [metric name]
CURRENT VALUE: [value]
EXPECTED RANGE: [lower] - [upper]
DEVIATION: [magnitude, e.g., "2.5 standard deviations below mean"]

CONTEXT: [Any known factors that might explain this]
RELATED SIGNALS: [Other metrics that moved with this one]

LIKELY CAUSE: [Best hypothesis]
RECOMMENDED ACTION: [Specific next step]
IMPACT IF UNRESOLVED: [What happens if this continues]
```

### Watch Notice (SEV-3)
```
🟡 WATCH: [Brief description]

[Metric] is [X%] [above/below] [baseline].
This is [description of deviation] but [not yet at alert threshold / within seasonal norms / etc.]
Monitoring for [what would escalate this to an ALERT].
Will report in next scheduled [daily check / weekly memo].
```

### Anomaly Resolution
```
✅ RESOLVED: [Original alert description]

Resolution: [What happened — root cause and fix]
Duration: [How long the anomaly lasted]
Impact: [What was affected and to what degree]
Prevention: [What will prevent recurrence, if anything]
```
