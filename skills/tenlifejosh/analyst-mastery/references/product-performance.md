# Product Performance Analytics

How to diagnose product health, identify conversion vs traffic problems, and optimize product listings.

---

## Table of Contents
1. Product Diagnostic Framework
2. The View-to-Sale Funnel
3. Conversion Problem Diagnosis
4. Traffic Problem Diagnosis
5. Product Health Scoring
6. Product Lifecycle Management
7. Listing Optimization Scoring
8. Product Comparison Framework
9. Product Report Templates

---

## 1. Product Diagnostic Framework

### The First Question: Traffic or Conversion?
Every underperforming product has one of two fundamental problems (sometimes both):
- **Traffic Problem**: Not enough people are seeing the product page
- **Conversion Problem**: People see the page but don't buy

These require COMPLETELY DIFFERENT fixes. Misdiagnosing leads to wasted effort.

### The Diagnostic Decision Tree
```
Is the product getting adequate views?
├── YES (views >= benchmark for its category/price)
│   ├── Is the conversion rate adequate?
│   │   ├── YES → Product is healthy. Scale traffic to grow revenue.
│   │   └── NO → CONVERSION PROBLEM. Fix: page copy, price, offer, social proof.
│   └── Is the conversion rate declining?
│       ├── YES → CONVERSION DECAY. Investigate: staleness, competition, audience shift.
│       └── NO → Stable but low. Test: price change, page redesign, offer restructure.
└── NO (views < benchmark)
    ├── Is there content pointing to this product?
    │   ├── YES → CONTENT EFFECTIVENESS problem. Content exists but isn't driving clicks.
    │   └── NO → CONTENT GAP. No content is promoting this product. Create it.
    └── Is the product findable via search?
        ├── YES → SEO working but volume is low. Supplement with social distribution.
        └── NO → DISCOVERABILITY problem. Optimize title, description, keywords.
```

---

## 2. The View-to-Sale Funnel

### Funnel Stages for Gumroad Products
```
Stage 1: AWARENESS — User encounters content about the product (Pinterest pin, tweet, Reddit post)
  Metric: Content impressions mentioning this product
  
Stage 2: CLICK — User clicks through to the Gumroad product page
  Metric: Outbound clicks / Product page views
  Conversion: Click-through rate from content to page

Stage 3: EVALUATION — User reads the product page
  Metric: Time on page, scroll depth (if available)
  Signal: If available from analytics, otherwise infer from views-to-cart data

Stage 4: PURCHASE — User completes the purchase
  Metric: Sales / Views = Conversion Rate
  
Stage 5: RETENTION — User doesn't request a refund
  Metric: Refund rate for this product
```

### Funnel Drop-Off Diagnosis
Measure the conversion rate at each stage. The stage with the biggest drop-off is where to focus.

**Stage 1→2 drop-off (content doesn't drive clicks):**
- Content isn't compelling enough to spark curiosity
- Call-to-action is weak or missing
- Content reaches wrong audience (platform targeting issue)
- Fix: Better hooks, clearer value proposition in content, stronger CTAs

**Stage 2→4 drop-off (views but no sales):**
- Product page doesn't convert — this is the classic conversion problem
- Could be: price, copy, social proof, product-market fit, or design
- See Section 3 for detailed diagnosis

**Stage 4→5 drop-off (sales but high refunds):**
- Product doesn't match expectations set by the page
- Quality issue with the product itself
- Buyer's remorse at the price point
- See revenue-analytics.md for refund investigation protocol

---

## 3. Conversion Problem Diagnosis

When a product has adequate views but low conversion rate, investigate these factors in order:

### Factor 1: Price-Value Perception
- Is the price appropriate for the perceived value?
- Compare conversion rate to similar-priced products in your catalog
- Check: Does the product page clearly communicate WHY it's worth the price?
- Signal: If conversion drops sharply above a price threshold, price is likely the issue

### Factor 2: Product Page Copy
- Does the headline clearly state the benefit (not just the feature)?
- Is the description written for the buyer's problem, not the creator's achievement?
- Are there bullet points or clear value propositions?
- Is there a clear call-to-action?
- Signal: If views are high (people are interested) but conversion is low, copy may be failing to close

### Factor 3: Social Proof
- Are there ratings/reviews visible?
- Is the sales count displayed? (Gumroad shows "X sales" — low numbers can deter buyers)
- Are there testimonials or use cases?
- Signal: New products without social proof often have lower conversion. This improves over time.

### Factor 4: Product-Market Fit
- Is the product solving a problem people actually have?
- Is the target audience the one actually visiting the page?
- Compare: Which traffic source has the highest conversion? That source's audience is the best fit.
- Signal: If NO traffic source converts well, the product-market fit may be off

### Factor 5: Competition
- Are there free alternatives available?
- Has a competitor launched a similar product at a lower price?
- Signal: Sudden conversion rate drops without internal changes suggest external factors

### Conversion Improvement Tracking
When a change is made to improve conversion:
```
CONVERSION TEST LOG:
Product: [name]
Change Made: [description]
Date Implemented: [date]
Baseline Conversion Rate: [rate, measured over prior 14 days]
Post-Change Conversion Rate: [rate, measured starting 48h after change, over 14 days]
Change in Rate: [+/- percentage points]
Statistical Significance: [Yes/No — computed using chi-square or similar]
Revenue Impact: [estimated $ change per month at current traffic levels]
Conclusion: [Keep / Revert / Test further]
```

---

## 4. Traffic Problem Diagnosis

When a product has low views:

### Traffic Source Audit
For the product in question:
- How many content pieces (pins, tweets, posts) point to this product?
- What's the engagement rate on that content?
- What's the click-through rate from that content?
- Is the product linked in the Gumroad profile/store page?

### Content Gap Analysis
```
For each product, compute:
  Content Coverage = Number of content pieces promoting this product
  Content Freshness = Average age of content pieces
  Content Quality = Average engagement rate of content pieces

UNDER-COVERED: Content Coverage < median across all products
STALE CONTENT: Content Freshness > 30 days with no new content
LOW-QUALITY CONTENT: Content Quality < 50th percentile for the platform
```

### SEO and Discoverability
- Is the product title keyword-optimized for Gumroad search?
- Is the description keyword-rich for what buyers would search?
- Does the product appear in Gumroad's category/discovery pages?
- Is the product URL structured cleanly?

### Traffic Building Recommendations
Based on diagnosis:
```
IF under-covered → "Create [N] new content pieces for [product] on [best platform]"
IF stale content → "Refresh or republish content for [product] — last piece is [N] days old"
IF low-quality content → "Rework content strategy for [product] — current content underperforms"
IF SEO issue → "Optimize [product] title and description for keywords: [suggested keywords]"
IF platform mismatch → "[Product] may perform better on [alternative platform] based on topic fit"
```

---

## 5. Product Health Scoring

### Computing the Product Health Score
(Full definition in kpi-definitions.md, detailed methodology here)

```python
def compute_product_health(product):
    # Conversion component (0-100)
    conversion_score = min(100, (product.conversion_rate / benchmark_conversion_rate) * 100)
    
    # Revenue trend component (0-100)
    # Based on 14-day linear regression slope of daily revenue
    revenue_slope = compute_slope(product.daily_revenue, days=14)
    revenue_score = normalize_slope(revenue_slope, 0, 100)
    
    # View trend component (0-100)
    view_slope = compute_slope(product.daily_views, days=14)
    view_score = normalize_slope(view_slope, 0, 100)
    
    # Refund component (0-100, inverted — lower refund = higher score)
    refund_score = max(0, 100 - (product.refund_rate * 20))  # 5% refund = 0 score
    
    # Review component (0-100)
    review_score = (product.avg_rating / 5) * 100 if product.has_reviews else 50  # neutral if no reviews
    
    # Weighted composite
    health = (
        conversion_score * 0.35 +
        revenue_score * 0.25 +
        view_score * 0.20 +
        refund_score * 0.10 +
        review_score * 0.10
    )
    
    return round(health, 1)
```

### Health Score Triggers
- Score drops >15 points WoW → ALERT: Investigate immediately
- Score drops >5 points for 3 consecutive weeks → WATCH: Persistent decline
- Score rises >10 points WoW → Flag as positive: What changed? Can we replicate?
- Score consistently <40 for 4+ weeks → Recommend: Evaluate for sunset or major overhaul

---

## 6. Product Lifecycle Management

### Lifecycle Stage Detection
Automatically classify each product's lifecycle stage:

```
LAUNCH (first 14 days after creation):
  Criteria: product.created_at > (now - 14 days)
  Benchmarks: Use launch-specific benchmarks (lower bar)
  Focus: Initial traction, early conversion signal, content creation

GROWTH (positive trajectory, above minimum revenue):
  Criteria: 4-week revenue trend is positive AND weekly revenue > $[minimum threshold]
  Benchmarks: Compare to growth-stage products
  Focus: Scale traffic, optimize conversion, expand content

MATURE (stable revenue, minimal growth):
  Criteria: 4-week revenue variance < 20% AND revenue > $[minimum threshold]
  Benchmarks: Compare to steady-state averages
  Focus: Maintain, minor optimizations, protect market position

DECLINING (negative trajectory):
  Criteria: 4-week revenue trend is negative beyond normal variance
  Benchmarks: Focus on rate of decline
  Focus: Diagnose cause → decide: revive (new content, price change) or sunset

DORMANT (near-zero activity):
  Criteria: <$[very low threshold] revenue AND <[very few] views in trailing 30 days
  Decision: Keep listed (no cost) or remove to declutter store
```

### Lifecycle Transitions
When a product transitions between stages:
- Flag the transition in the weekly signal memo
- Include the evidence (metrics that triggered the reclassification)
- Include a recommended action based on the new stage

---

## 7. Listing Optimization Scoring

Rate each product listing on these dimensions (1-10 each):

### Title Quality (1-10)
- Contains primary keyword? (+2)
- States a clear benefit? (+3)
- Under 60 characters? (+1)
- Compelling/curiosity-inducing? (+2)
- Grammatically clean? (+2)

### Description Quality (1-10)
- Opens with the buyer's problem, not the product features? (+2)
- Clear value propositions? (+2)
- Includes bullet points or scannable formatting? (+2)
- Has a compelling call-to-action? (+2)
- Appropriate length (150-500 words)? (+2)

### Visual Quality (1-10)
- Product cover image is professional? (+3)
- Preview images show the actual product? (+3)
- Images are appropriately sized and not blurry? (+2)
- Brand-consistent? (+2)

### Pricing Positioning (1-10)
- Price matches perceived value? (+3)
- Competitive with alternatives? (+3)
- Price is a clean number (psychological pricing)? (+2)
- Tiered options available if appropriate? (+2)

### Listing Score = Average of all four dimensions
- 8-10: Excellent listing
- 6-8: Good, minor improvements possible
- 4-6: Needs work
- Below 4: Major overhaul recommended

---

## 8. Product Comparison Framework

### Head-to-Head Comparison Table
When comparing products:

```
| Metric | Product A | Product B | Product C | Best |
|--------|-----------|-----------|-----------|------|
| Revenue (7d) | $X | $Y | $Z | [name] |
| Views (7d) | N | N | N | [name] |
| Conversion Rate | X% | Y% | Z% | [name] |
| Revenue Trend | ↑/→/↓ | ↑/→/↓ | ↑/→/↓ | [name] |
| Health Score | X | Y | Z | [name] |
| Lifecycle Stage | X | Y | Z | — |
| Refund Rate | X% | Y% | Z% | [name] |
| Listing Score | X | Y | Z | [name] |
```

### Portfolio Analysis
Classify all products into a 2×2 matrix:
```
                    HIGH CONVERSION
                    │
    CASH COW        │    STAR
    (mature,        │    (growing,
     stable)        │     high converting)
                    │
   ─────────────────┼─────────────────
                    │
    QUESTION MARK   │    DOG
    (low conversion,│    (low conversion,
     but has views) │     low views)
                    │
                    LOW CONVERSION
    LOW VIEWS ──────────────── HIGH VIEWS
```

Stars: Invest heavily.
Cash Cows: Maintain efficiently.
Question Marks: Fix conversion or kill.
Dogs: Diagnose → revive or sunset.

---

## 9. Product Report Templates

### Weekly Product Section (for Signal Memo)
```
## Product Signal

### Portfolio Overview
Products tracked: [N]
Stars: [list] | Cash Cows: [list] | Question Marks: [list] | Dogs: [list]

### Movement This Week:
- [Product X] — Health score [old] → [new] ([+/- change]). [Brief reason].
- [Product Y] — Lifecycle: [old stage] → [new stage]. [What triggered transition].

### Conversion Highlights:
- Highest converting: [product] at [rate]% (vs [benchmark]% benchmark)
- Needs attention: [product] at [rate]% — [diagnosis: traffic or conversion problem]

### Recommended Actions:
1. [Product]: [specific action] — [expected impact]
2. [Product]: [specific action] — [expected impact]
```
