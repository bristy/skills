---
name: amazon-hot-products
description: "Scout Amazon trending products, hot searches, new releases, and rising categories to find blue ocean opportunities early. Triggers: hot products, hot search, hot new releases, hot movers, hot seasonal, hot compare, hot report, hot save"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-hot-products
---

# Amazon Hot Products & Trending Scout

Track Amazon's real-time hot searches, new releases, and rising categories. Spot trending products before they become saturated — find blue ocean opportunities early.

## Commands

```
hot products                    # scan trending products across categories
hot search [category]           # analyze hot search terms in category
hot new releases [category]     # find new releases with early traction
hot movers [category]           # find products with rapid BSR improvement
hot seasonal                    # identify upcoming seasonal trends
hot compare [cat1] [cat2]       # compare trend momentum between categories
hot report                      # generate weekly trend report
hot save [opportunity]          # save a trend opportunity to memory
```

## What Data to Provide

- **Category** — broad (Electronics) or specific (Wireless Earbuds)
- **BSR data** — paste BSR rankings if you have them
- **Search term data** — trending search terms from Seller Central
- **Time period** — last 7/30/90 days
- **Market** — US, UK, DE, JP, etc.

No API key needed. Provide data verbally or paste raw numbers.

## Trend Identification Framework

### Signal 1: Search Volume Surge
- Search term appears in Amazon's "Hot New Keywords" (from Seller Central Brand Analytics)
- Week-over-week search volume growth >20%
- Low current competition (fewer than 1,000 results for exact match)

### Signal 2: BSR Velocity
| BSR Movement | Signal Strength |
|---|---|
| BSR improved >50% in 30 days | 🔥 Strong |
| BSR improved 20–50% in 30 days | ✅ Moderate |
| BSR stable | ⚪ Neutral |
| BSR declining | ❌ Avoid |

### Signal 3: Review Accumulation Rate
- New products getting 50+ reviews in first 60 days = high demand signal
- Multiple competitors launching simultaneously = category heating up

### Signal 4: Seasonal Calendar
| Month | Trending Categories |
|---|---|
| Jan–Feb | Fitness, Organization, New Year |
| Mar–Apr | Outdoor, Garden, Spring Cleaning |
| May–Jun | Graduation, Father's Day, Summer |
| Jul–Aug | Back to School, Pool/Beach |
| Sep–Oct | Halloween, Fall Home |
| Nov–Dec | Holiday Gifts, Holiday Decor |

## Blue Ocean Score (1–10)

Score each trending product opportunity:
- **Demand** (1–3): Search volume trend direction
- **Competition** (1–3): # of sellers, review counts, listing quality
- **Margin** (1–2): Estimated price point vs. likely COGS
- **Differentiation** (1–2): Can you improve on existing products?

**Score 7+** = Enter aggressively
**Score 5–6** = Enter cautiously with differentiation
**Score <5** = Skip or monitor

## Output Format

1. **Trending Opportunities** — ranked list with Blue Ocean Score
2. **Category Heat Map** — which categories are rising vs. cooling
3. **Early Entry Windows** — products with <200 reviews but rising BSR
4. **Avoid List** — saturated trends (too late to enter profitably)
5. **30-Day Watch List** — opportunities to monitor for next scan

## Rules

1. Always check review count before calling a trend "early" — >500 reviews = not early
2. Flag categories with known high return rates (electronics, clothing)
3. Distinguish between fad (short spike) and trend (sustained growth)
4. Note when seasonal peaks are approaching — timing matters
5. Always pair trend data with estimated margin — demand means nothing if margins are thin
