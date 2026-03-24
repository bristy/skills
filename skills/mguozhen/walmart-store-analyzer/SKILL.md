---
name: walmart-store-analyzer
description: "Walmart marketplace store traffic and performance analysis agent. Auto-analyze Walmart seller traffic reports, item performance, search analytics, and competitive positioning to grow your Walmart business. Triggers: walmart analyzer, walmart traffic, walmart seller, walmart marketplace, walmart store analysis, walmart performance, walmart search ranking, walmart item rank, walmart analytics, walmart seo, walmart competitor, walmart listing"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/walmart-store-analyzer
---

# Walmart Store Analyzer

Deep analysis of your Walmart marketplace performance — traffic sources, item rankings, conversion rates, and competitive positioning. Turn your Walmart seller data into growth actions.

Paste your Walmart seller data or traffic reports. The agent analyzes performance, identifies opportunities, and outputs a prioritized action plan.

## Commands

```
walmart traffic <data>            # analyze traffic report data
walmart rank <item-id>            # analyze item search ranking
walmart compete <query>           # competitive analysis for a search term
walmart listing grade <item>      # score and improve a Walmart listing
walmart keyword <term>            # Walmart-specific keyword research
walmart buybox <item>             # Buy Box win rate analysis
walmart ads <data>                # Walmart Connect ad performance analysis
walmart report <period>           # full store performance report
walmart compare <item1> <item2>   # compare two item performances
walmart optimize <item>           # listing optimization recommendations
```

## What Data to Provide

- **Traffic reports** — views, clicks, add-to-carts, purchases by item
- **Item IDs / WMT IDs** — specific items to analyze
- **Search terms** — keywords you want to rank for
- **Competitor data** — competing items on same search results
- **Ad data** — Walmart Connect campaign metrics
- **Sales data** — units sold, revenue, return rates

## Walmart Marketplace Framework

### Walmart vs Amazon Key Differences

| Factor | Walmart | Amazon |
|--------|---------|--------|
| Commission | 6-15% (category) | 6-20% (category) |
| Monthly fee | None | $39.99 |
| Fulfillment | WFS or seller | FBA or FBM |
| Traffic | Growing, less saturated | Very high, very competitive |
| Review barrier | Lower (fewer sellers) | High in most categories |
| Ads | Walmart Connect | Amazon Ads |
| Algorithm | Relevance + conversion | A9 (similar) |

### Walmart Search Ranking Algorithm

Key ranking factors:
1. **Relevance** — title, description keyword match
2. **Performance signals** — click-through rate, conversion rate
3. **Price** — competitive pricing vs. category
4. **In-stock status** — out-of-stock = ranking penalty
5. **Customer ratings** — star rating and review count
6. **Fulfillment method** — WFS items get priority (similar to FBA)
7. **Listing completeness** — content score from Walmart

### Traffic Report Analysis

When given Walmart traffic data, analyze:

```
Metric                 Benchmark      Action if below
Views/week             >100           SEO optimization needed
CTR (views→clicks)     >3%            Improve title/image
Add-to-cart rate       >5% of views   Improve images, price
Purchase rate          >2% of views   Address price/reviews
Return rate            <5%            Product quality issue
```

**Traffic source breakdown:**
- Search traffic: Main driver — keyword optimization focus
- Browse traffic: Category placement — content score matters
- Paid traffic: Walmart Connect ads
- External traffic: Affiliate and off-site

### Walmart Listing Optimization

**Content Score** (Walmart grades your listing):
- Items with 100% content score rank higher
- Check: title, short description, long description, key features, images, specs

**Title Best Practices:**
- Format: `[Brand] [Product Type] [Key Feature] [Size/Color] [Use Case]`
- Character limit: 75 characters recommended (200 max)
- Lead with strongest keyword
- Include size, material, or key differentiator

**Image Requirements:**
- Main image: white background, product fills 85% of frame
- Minimum 4 images (aim for 8+)
- Lifestyle shots: product in use context
- Infographic: key features callouts
- Minimum 2000×2000 pixels

**Short Description** (Key Features):
- 6 bullet points, 80 chars each
- Lead each bullet with the benefit, support with feature
- Include primary keywords naturally

### Walmart Buy Box Analysis

Walmart Buy Box rules:
- Lowest price (among fulfilled, available sellers) typically wins
- WFS sellers get advantage at similar prices
- Seller rating impacts eligibility
- In-stock required

**Buy Box win rate formula:**
```
If you're winning:      Item price ≤ market price, good metrics
If you're losing:       Check price competitiveness first
                        Then check seller metrics (>98% on-time ship, <2% cancel)
                        Then check fulfillment method (WFS advantage)
```

### Walmart Connect (Ad) Metrics

Key ad performance metrics:
```
ROAS:          Revenue / Ad spend (target >4x)
CPC:           Cost per click (benchmark $0.30-$1.50)
CTR:           Ad clicks / impressions (target >0.5%)
CVR:           Purchases / clicks (target >2%)
ACOS:          Ad cost / revenue × 100 (target <25%)
```

**Ad campaign types:**
- Sponsored Products: Item-level targeting, most common
- Sponsored Brands: Brand banner + 3 products
- Video Ads: High impact, higher CPM

### Competitive Positioning on Walmart

Search for your category on Walmart:
```
Position 1-3: Premium placement, highest traffic share
Position 4-8: Good visibility, competitive zone
Position 9-16: Second page (mobile), less visible
Position 17+: Low visibility, need ranking improvement
```

**Competitive gaps on Walmart vs Amazon:**
- Many Amazon sellers haven't expanded to Walmart
- Lower review counts needed to rank
- Less sophisticated ads competition
- WFS (Walmart Fulfillment Services) gives strong advantage

## Workspace

Creates `~/walmart-tracker/` containing:
- `traffic/` — traffic report analyses
- `keywords/` — Walmart keyword research
- `listings/` — listing scores and optimization notes
- `ads/` — Walmart Connect performance data
- `reports/` — full store performance reports

## Output Format

Every analysis outputs:
1. **Store Performance Summary** — top metrics vs. benchmarks with trend arrows
2. **Traffic Source Breakdown** — where traffic comes from and conversion by source
3. **Item Ranking Report** — search position for key terms
4. **Listing Score Card** — content score with specific improvement actions
5. **Ad Performance** — ROAS, ACOS, top performing keywords
6. **Opportunity Items** — items with traffic but low conversion (quick wins)
7. **Weekly Action Plan** — prioritized optimization tasks
