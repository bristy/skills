# Performance Benchmarks

What "good" looks like for every metric. Internal and industry benchmarks, how to maintain them, and how to use them.

---

## Table of Contents
1. Benchmarking Philosophy
2. Revenue Benchmarks
3. Conversion Benchmarks
4. Content Engagement Benchmarks
5. System Health Benchmarks
6. Operational Efficiency Benchmarks
7. Benchmark Maintenance Protocol
8. Using Benchmarks in Reports

---

## 1. Benchmarking Philosophy

### Three Types of Benchmarks
1. **Internal Historical**: Your own past performance (the most relevant)
2. **Industry/External**: What similar businesses achieve (useful for calibration)
3. **Target/Aspirational**: What you're aiming for (set by strategy, not by Analyst)

### Benchmark Hierarchy
Always present benchmarks in this order of relevance:
1. Your own trailing 90-day average (most actionable comparison)
2. Your own trailing 12-month best (shows what you're capable of)
3. Industry benchmark (calibrates expectations)
4. Target/OKR (if set by strategy team)

### When a Metric Beats the Benchmark
Don't just celebrate — diagnose. Ask: "Why did this beat the benchmark?"
- If you can identify the cause, it's a replicable win
- If you can't identify the cause, it might be noise or a one-time event
- Update the benchmark if the improvement sustains for 4+ weeks

### When a Metric Misses the Benchmark
Don't just flag — classify:
- **Consistent miss** (4+ weeks below benchmark): Benchmark may be too high, OR systemic underperformance
- **Recent decline** (was meeting, now isn't): Something changed — investigate
- **Never met** (benchmark was always aspirational): Reset to achievable target, set aspirational separately

---

## 2. Revenue Benchmarks

### Daily Revenue
- **Benchmark source**: Trailing 28-day average daily revenue
- **Refresh**: Recalculate weekly (every Sunday for the following week)
- **WATCH threshold**: <85% of benchmark
- **ALERT threshold**: <70% of benchmark
- **Exceptional performance**: >130% of benchmark (investigate for replicability)

### Weekly Revenue
- **Benchmark source**: Trailing 4-week average weekly revenue
- **Refresh**: Recalculate monthly
- **Good**: Within 90-110% of benchmark
- **Concerning**: <80% of benchmark for 2+ consecutive weeks

### Monthly Revenue
- **Benchmark source**: Same month prior year (if available), otherwise trailing 3-month average
- **Refresh**: Annual, with quarterly checks
- **Growth target**: Month-over-month growth rate from strategy team (if set)

### Revenue Per Product
- **Benchmark**: Each product benchmarked against its own trailing 28-day average
- **New products**: Use first-14-day "launch benchmark" (typically 50-70% of mature product averages)
- **Price-adjusted**: When comparing across products, normalize to revenue per $1 of price

### Revenue Per Traffic Source
- **Benchmark**: Revenue per visit, benchmarked per source against its own 28-day average
- **Cross-source comparison**: Rank sources by RPV; the highest is the "best" source regardless of volume

---

## 3. Conversion Benchmarks

### Overall Gumroad Conversion Rate
- **Industry benchmark for digital products**: 1-5% (varies enormously by price and niche)
  - Free/low-price ($0-9): 5-15%
  - Mid-price ($10-49): 2-5%
  - High-price ($50-199): 1-3%
  - Premium ($200+): 0.5-2%
- **Internal benchmark**: Your own trailing 28-day average
- **Use internal over industry**: Industry benchmarks are wide ranges and context-dependent.
  Your own data is always more relevant.

### Per-Product Conversion Rate
- **Benchmark**: Each product against its own 28-day average
- **Cross-product comparison**: Rank products by conversion rate within price tiers (not across tiers)
- **New product benchmark**: First 14 days, expect 30-50% lower conversion than mature products

### Platform Conversion (content engagement → Gumroad visit → sale)
Full-funnel conversion by platform:
- **Pinterest → Gumroad → Sale**: Benchmark at pin CTR × page conversion rate
- **Twitter/X → Gumroad → Sale**: Benchmark at tweet link click rate × page conversion rate
- **Reddit → Gumroad → Sale**: Benchmark at comment-to-click rate × page conversion rate

These are COMPOUND rates and will be very small numbers. That's normal. Track the trend, not the absolute.

---

## 4. Content Engagement Benchmarks

### Pinterest Benchmarks
| Metric | Below Average | Average | Good | Excellent |
|--------|--------------|---------|------|-----------|
| Pin CTR (outbound) | <0.5% | 0.5-1.5% | 1.5-3% | >3% |
| Pin Save Rate | <1% | 1-3% | 3-6% | >6% |
| Pin Velocity (48h impressions) | <100 | 100-500 | 500-2000 | >2000 |

Note: These are general benchmarks. Compute your own internal benchmarks using trailing 90-day
percentile distribution of your pins. Your internal 50th percentile is your true "average."

### Twitter/X Benchmarks
| Metric | Below Average | Average | Good | Excellent |
|--------|--------------|---------|------|-----------|
| Engagement Rate | <1% | 1-3% | 3-6% | >6% |
| Reply Rate | <0.1% | 0.1-0.5% | 0.5-2% | >2% |
| RWES Rate | <0.5% | 0.5-2% | 2-5% | >5% |
| Link Click Rate | <0.5% | 0.5-1.5% | 1.5-3% | >3% |

Reply rate matters more than all other engagement metrics combined due to the 13.5x algorithm weight.

### Reddit Benchmarks
| Metric | Below Average | Average | Good | Excellent |
|--------|--------------|---------|------|-----------|
| Net Upvotes (comment) | <5 | 5-20 | 20-100 | >100 |
| Net Upvotes (post) | <10 | 10-50 | 50-500 | >500 |
| Comment-to-Click Rate | <0.1% | 0.1-0.5% | 0.5-2% | >2% |

Reddit is highly subreddit-dependent. Always benchmark against the specific subreddit's norms.

---

## 5. System Health Benchmarks

### Cron Job Success Rate
| Level | Rate | Assessment |
|-------|------|------------|
| Excellent | >99.5% | Highly reliable |
| Good | 98-99.5% | Acceptable, minor issues |
| Concerning | 95-98% | Multiple failures, investigate |
| Poor | 90-95% | Systemic issues |
| Critical | <90% | Major reliability problem |

### Session Health
| Level | Score | Assessment |
|-------|-------|------------|
| Excellent | >90 | All sessions healthy, ample time remaining |
| Good | 75-90 | Minor expiry concerns |
| Concerning | 60-75 | Sessions approaching expiry |
| Poor | 40-60 | Active expiry warnings |
| Critical | <40 | Sessions expired or imminent |

### API Reliability
| Level | Success Rate | p95 Latency | Assessment |
|-------|-------------|-------------|------------|
| Excellent | >99.9% | <500ms | Ideal |
| Good | 99-99.9% | 500ms-2s | Normal |
| Degraded | 95-99% | 2s-5s | Monitor closely |
| Poor | <95% | >5s | Investigate, consider fallback |

---

## 6. Operational Efficiency Benchmarks

### Workflow Cycle Time
- **Benchmark**: Trailing 28-day median cycle time per workflow type
- **Good**: Within 80-120% of benchmark
- **Fast**: <80% of benchmark (investigate — efficiency gain or skipped steps?)
- **Slow**: >120% of benchmark (bottleneck likely — see bottleneck-detection.md)

### Agent Performance
- **Benchmark**: Team median for each metric (cycle time, completion rate, error rate)
- **Performing**: Within ±20% of team median on all metrics
- **Outperforming**: >20% better than median on 2+ metrics
- **Underperforming**: >20% worse than median on any metric

### Queue Health
- **Benchmark**: Trailing 14-day average queue depth
- **Healthy**: Queue depth within 50-150% of benchmark
- **Growing**: Queue depth >150% of benchmark (incoming > processing)
- **Critical**: Queue depth >300% of benchmark (severe backlog)

---

## 7. Benchmark Maintenance Protocol

### When to Update Benchmarks
- **Rolling averages**: Auto-update daily/weekly (they're self-updating by definition)
- **Static benchmarks**: Review monthly, update if trailing 28-day average differs by >20%
- **Industry benchmarks**: Review quarterly against published data
- **After major changes**: If the business makes a significant change (new product, new platform,
  pricing overhaul), reset affected benchmarks after a 14-day stabilization period

### Benchmark Versioning
Track benchmark changes:
```
BENCHMARK CHANGE LOG:
Date: [when changed]
Metric: [which benchmark]
Old Value: [previous]
New Value: [updated]
Reason: [why changed — data-driven justification]
```

### The "Good Enough" Principle
Benchmarks don't need to be perfect. They need to be:
1. Based on actual data (not guesses)
2. Updated regularly (not stale)
3. Applied consistently (same methodology every time)
4. Contextually appropriate (internal > industry when available)

---

## 8. Using Benchmarks in Reports

### Benchmark Presentation Format
Always present metrics WITH their benchmark context:

```
GOOD: "Conversion rate: 3.2% (vs 2.8% benchmark, +0.4pp)"
GOOD: "Revenue: $1,240 (vs $1,100 4-week avg, +12.7%)"
BAD: "Conversion rate: 3.2%" (no context — meaningless)
BAD: "Revenue: $1,240" (no comparison — is this good or bad?)
```

### Traffic Light System
For visual reports, use a simple color system:
- 🟢 **Green**: Metric at or above benchmark
- 🟡 **Yellow**: Metric 10-20% below benchmark (WATCH zone)
- 🔴 **Red**: Metric >20% below benchmark (ALERT zone)
- 🔵 **Blue**: Metric >20% above benchmark (positive anomaly — investigate for replicability)

### Benchmark Confidence
Always disclose how much you trust the benchmark:
- **High confidence**: Based on 90+ days of stable data
- **Medium confidence**: Based on 28-60 days, or data with some quality issues
- **Low confidence**: Based on <28 days, or newly established benchmark
- **External only**: No internal data; using industry benchmark (lower relevance)
