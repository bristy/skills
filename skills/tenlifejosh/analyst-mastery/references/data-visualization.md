# Data Visualization Standards

How to present data clearly, without clutter, in the right format for the audience and the message.

---

## Table of Contents
1. Visualization Philosophy
2. Chart Type Selection
3. Color Standards
4. Layout & Composition
5. Annotation & Labeling
6. Dashboard Design
7. Executive Summary Visualization
8. Common Mistakes to Avoid
9. Platform-Specific Visualization

---

## 1. Visualization Philosophy

### The Data-Ink Ratio
Every pixel of ink in a visualization should communicate data. Remove:
- Decorative elements (3D effects, gradients, drop shadows)
- Redundant labels (if the axis shows it, don't label each bar too)
- Chart junk (gridlines that aren't needed, unnecessary borders)
- Background color (use white/transparent unless encoding data)

### The One-Message Rule
Each visualization should communicate ONE primary message. If you're trying to show two things,
use two visualizations. A chart that tries to show everything shows nothing.

### The 5-Second Test
A reader should understand the main message of any visualization within 5 seconds.
If they can't, it needs simplification.

---

## 2. Chart Type Selection

### The Decision Tree
```
What are you showing?
├── COMPARISON (this vs that)
│   ├── Few categories (<7) → Bar chart (horizontal for long labels)
│   ├── Many categories (>7) → Bar chart (sorted by value, top N)
│   └── Two metrics per category → Grouped bar or dot plot
├── TREND OVER TIME
│   ├── Single metric → Line chart
│   ├── Multiple metrics → Multi-line chart (max 4-5 lines)
│   ├── Cumulative → Area chart
│   └── Comparison to target → Line + reference line
├── PROPORTION (part of whole)
│   ├── Few parts (<5) → Stacked bar (NOT pie chart)
│   ├── Many parts → Treemap or sorted bar
│   └── Change over time → Stacked area or 100% stacked bar
├── DISTRIBUTION
│   ├── Single variable → Histogram or box plot
│   └── Two variables → Scatter plot
├── RELATIONSHIP
│   ├── Two variables → Scatter plot
│   └── Three variables → Scatter with size encoding (bubble chart)
└── STATUS / HEALTH
    ├── Single metric → Big number with trend indicator
    ├── Multiple metrics → Traffic light table or scorecard
    └── System status → Status dashboard with indicators
```

### When to Use Specific Charts

**Line charts**: Time series. Revenue over time. Traffic trends. Always for temporal data.
**Bar charts**: Comparisons. Revenue by product. Traffic by source. Sorted by value, largest first.
**Sparklines**: Inline trend indicators in tables. Small, no axes, just the shape of the trend.
**Big numbers**: KPI dashboards. The ONE number that matters, large font, with trend arrow.
**Tables**: When exact values matter more than visual patterns. Use sparingly.
**Scatter plots**: Correlation exploration. Views vs conversion rate. Impressions vs clicks.
**Heatmaps**: Time-of-day/day-of-week patterns. Content performance grids.

### Charts to AVOID
- **Pie charts**: Human eyes are terrible at comparing angles. Use bar charts instead.
- **3D anything**: Distorts perception. Always use 2D.
- **Dual-axis charts**: Confusing and misleading. Use two separate charts.
- **Stacked area with >4 layers**: Becomes unreadable. Summarize or use small multiples.
- **Radar/spider charts**: Only useful for very specific use cases. Default to bar charts.

---

## 3. Color Standards

### The Color Palette

**Primary data colors** (use for main data series):
```
Blue:   #2563EB (primary series)
Green:  #16A34A (secondary series, positive indicators)
Orange: #EA580C (tertiary series, warning indicators)
Red:    #DC2626 (alert indicators, negative)
Purple: #7C3AED (fourth series if needed)
Gray:   #6B7280 (reference lines, secondary data, benchmarks)
```

**Status colors**:
```
Green:  #16A34A — Healthy, on target, positive
Yellow: #EAB308 — Watch, approaching threshold
Red:    #DC2626 — Alert, below threshold, negative
Blue:   #2563EB — Neutral information, benchmark reference
Gray:   #9CA3AF — Inactive, historical, reference
```

### Color Rules
1. **Never use color as the ONLY encoding.** Always pair with labels, patterns, or position.
   (Accessibility: ~8% of men are color-blind)
2. **Use color consistently.** If revenue is blue in one chart, it's blue in every chart.
3. **Limit to 4-5 colors per visualization.** More than that = too many categories. Consolidate.
4. **Use color saturation for emphasis.** Key data in saturated color, context data in muted gray.
5. **Green = good, Red = bad.** Never reverse this convention.

---

## 4. Layout & Composition

### Dashboard Layout Grid
Use a consistent grid system:
```
┌─────────────────────────────────────────┐
│        BIG NUMBER KPIS (TOP ROW)        │
│   [KPI 1]    [KPI 2]    [KPI 3]        │
├───────────────────┬─────────────────────┤
│   PRIMARY CHART   │  SECONDARY CHART    │
│   (largest,       │  (supporting detail)│
│    main message)  │                     │
├───────────────────┼─────────────────────┤
│   DETAIL TABLE    │  TREND SPARKLINES   │
│   (drill-down)    │  (quick trends)     │
└───────────────────┴─────────────────────┘
```

### Information Hierarchy
1. **Top**: The most important number or status (largest, most prominent)
2. **Middle**: Primary charts showing the main story
3. **Bottom**: Supporting details, tables, drill-down data

### Responsive Considerations
- Dashboards may be viewed on desktop or mobile
- Stack layout vertically for mobile (KPIs → Primary → Secondary → Detail)
- Minimum touch target: 44×44px for interactive elements
- Font minimum: 12px for body text, 14px for labels

---

## 5. Annotation & Labeling

### Annotation Rules
- **Annotate anomalies**: When a data point is significantly different, label it with context
  ("Price change on Nov 1" → arrow to the data point where conversion rate shifted)
- **Annotate benchmarks**: Draw a reference line at the benchmark value, label it
- **Annotate events**: If an external event affected the data, mark the date
- **Don't annotate everything**: Only annotate what adds understanding

### Labeling Standards
- **Axis labels**: Always present. Clear units ($ not "dollars", % not "percent")
- **Chart title**: States the MESSAGE, not just the topic
  - GOOD: "Revenue growing 12% WoW, led by Product A"
  - BAD: "Revenue Over Time"
- **Legend**: Only if multiple series. Place close to the data, not in a separate box.
- **Data labels**: Use sparingly. Only on the most important data points.
- **Tooltip on hover**: For interactive charts, provide exact values on hover.

### Number Formatting
```
Revenue: $1,234 (not $1234 or $1,234.00 — show cents only if relevant)
Percentages: 3.2% (one decimal place, not 3.21% or 3%)
Large numbers: $12.4K or $1.2M (abbreviate with K/M)
Dates: Jan 15 or 2025-01-15 (be consistent within a report)
Time: 2:30 PM EST (always include timezone for time-specific data)
Negative: -$500 in red (not ($500) unless accounting format requested)
```

---

## 6. Dashboard Design

### KPI Scorecard Component
```
┌──────────────────────┐
│  REVENUE TODAY        │
│  $1,247              │  ← Big number
│  ↑ 12% vs yesterday  │  ← Trend with comparison
│  ▃▄▅▆▇ (sparkline)  │  ← 7-day trend
│  Benchmark: $1,100   │  ← Context
│  🟢 ON TRACK         │  ← Status indicator
└──────────────────────┘
```

### Status Dashboard Component
```
┌──────────────────────────────────┐
│  SYSTEM STATUS                    │
│  ─────────────────────────────── │
│  🟢 Gumroad API      OK         │
│  🟢 Pinterest API    OK         │
│  🟡 Twitter/X API    Degraded   │
│  🟢 Cron Jobs        14/14      │
│  🟢 Sessions         3 active   │
│  ─────────────────────────────── │
│  Overall: 🟢 HEALTHY (92/100)   │
└──────────────────────────────────┘
```

### Interactive Dashboard Features
- **Filters**: Date range, product, traffic source (all optional, defaults to current period)
- **Drill-down**: Click a KPI to see the underlying chart
- **Comparison toggle**: Switch between WoW, MoM, vs benchmark
- **Export**: Allow data export for ad-hoc analysis

---

## 7. Executive Summary Visualization

For the Weekly Signal Memo and executive-level reports, visualizations should be:
- **Minimal**: One chart per section maximum
- **Labeled with the conclusion**: Chart title IS the insight
- **Small**: Fit alongside text, don't dominate
- **Self-contained**: Understandable without reading surrounding text

### The "Newspaper Test"
Could this chart be published in a newspaper with just its title and be understood by a general audience?
If yes, it's good executive visualization. If no, simplify.

---

## 8. Common Mistakes to Avoid

1. **Starting Y-axis at non-zero**: Makes small changes look dramatic. Always start at zero
   for bar charts. For line charts, starting at non-zero is acceptable IF the purpose is to show
   variation within a narrow range (but label the axis clearly).

2. **Using the wrong time granularity**: Daily data for a yearly trend is noise. Weekly data for
   a daily investigation is too coarse. Match granularity to the question.

3. **Too many series**: More than 5 lines on a line chart = unreadable. Use small multiples
   (one chart per series) instead.

4. **Inconsistent scales**: When comparing charts side by side, use the same Y-axis scale.
   Otherwise the visual comparison is misleading.

5. **Decorative color**: Using 7 colors for 7 bars when they're all the same category. Use
   ONE color for the series, highlight the specific bar of interest in a different color.

6. **Missing context**: A number without comparison is meaningless. Always show benchmark,
   prior period, or target alongside the current value.

7. **Overloaded dashboards**: If a dashboard has more than 6-8 components, it's trying to
   show too much. Split into multiple focused dashboards.

---

## 9. Platform-Specific Visualization

### For React/JSX Dashboards
- Use Recharts or Chart.js for standard charts
- Use Tailwind for layout and styling
- Implement responsive breakpoints
- Add loading states for data fetching
- Include error states for missing data

### For Markdown Reports
- Use ASCII tables for small datasets
- Reference external charts (link to HTML dashboard)
- Use emoji indicators (🟢🟡🔴) for status
- Use sparkline Unicode characters (▁▂▃▄▅▆▇) for inline trends

### For DOCX/PDF Reports
- Embed charts as images
- Use consistent margins and formatting
- Include chart source notes
- Ensure charts are legible in black and white (for printing)

### For HTML/Interactive
- Progressive disclosure: overview first, details on click/hover
- Keyboard navigation for accessibility
- Print-friendly CSS for when someone wants to print
- Dark mode support using CSS variables
