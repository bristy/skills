# Executive Communication

How to write for decision-makers: concise, structured, actionable, and honest about uncertainty.

---

## Table of Contents
1. Writing for Decision-Makers
2. The Pyramid Principle
3. BLUF (Bottom Line Up Front)
4. Insight Density Optimization
5. Uncertainty Communication
6. Bad News Delivery
7. The "So What?" Discipline
8. Recommendation Framing
9. Anti-Patterns to Avoid

---

## 1. Writing for Decision-Makers

### Know Your Audience
Navigator and Hutch are the primary consumers of Analyst output. They need:
- **Speed**: Can they get the key message in 30 seconds?
- **Clarity**: Is the message unambiguous?
- **Actionability**: Do they know what to do (or decide) after reading?
- **Trust**: Is the data reliable and honestly presented?

They do NOT need:
- Methodology details (unless they ask)
- Raw data (that's what dashboards are for)
- Hedging without substance ("it's complex" — everything is complex)
- Jargon or statistical terminology without plain-language translation

### The Executive Reading Pattern
Executives read in an F-pattern:
1. **First line** of each section (they skim headers and opening sentences)
2. **Bold text** and highlighted items
3. **Numbers** (they scan for specific figures)
4. **The rest** only if the first three caught their attention

Structure your writing to front-load the most important information at each level.

---

## 2. The Pyramid Principle

### Structure: Answer First, Then Support

```
WRONG (narrative structure):
  "We looked at Pinterest data. We noticed pins were down.
   We checked the algorithm. It changed. Therefore revenue might decline."

RIGHT (pyramid structure):
  "Revenue is at risk because Pinterest changed its algorithm, reducing our pin distribution by 35%.
   Evidence: [supporting point 1] [supporting point 2] [supporting point 3]
   Recommendation: [specific action]"
```

### The Pyramid
```
        [MAIN MESSAGE]          ← State this first. The single most important thing.
       /      |       \
   [Support] [Support] [Support]  ← Evidence and reasoning that supports the main message.
   /  \      /  \      /  \
 [Detail] [Detail] [Detail]       ← Granular data. Only if the reader wants to go deeper.
```

### Applying the Pyramid to Reports
- **Signal Memo**: Pyramid at every level. Main message = BHI + top 3 signals. Each signal section
  leads with the conclusion, follows with evidence.
- **Monthly Deep-Dive**: Main message = executive summary paragraph. Each section follows the pyramid.
- **Alerts**: Main message = what's happening and what to do. Details follow.

---

## 3. BLUF (Bottom Line Up Front)

### The BLUF Rule
Every piece of communication starts with the conclusion or recommendation, not the analysis
that led to it.

```
BLUF: "Conversion rate dropped 18% this week. Root cause: the product page update on Tuesday
broke the mobile layout. Recommend: revert to previous page version immediately."

THEN (if needed): Supporting analysis, methodology, alternative explanations, data tables.
```

### BLUF Templates

**For alerts**:
"[METRIC] is [STATE]. [ROOT CAUSE or hypothesis]. Recommend: [ACTION]."

**For weekly findings**:
"[WHAT HAPPENED] because [WHY]. This means [IMPLICATION]. Suggest [ACTION]."

**For forecasts**:
"[METRIC] is projected to reach [VALUE] by [DATE] (range: [LOW]-[HIGH]). Key driver: [FACTOR]."

**For status updates**:
"[SYSTEM/METRIC] is [STATUS]. [One sentence on any issues]. [One sentence on next steps if needed]."

---

## 4. Insight Density Optimization

### What is Insight Density?
Insight density = Useful information per word. Higher is better.

### Low Density (avoid):
"We took a look at the revenue numbers for this past week and noticed that they seem to have
gone down somewhat compared to where they were the previous week, which could potentially
indicate that there might be some issues worth looking into."
(40 words, 1 vague insight)

### High Density (target):
"Revenue dropped 22% WoW ($1,240 → $968). Primary driver: Pinterest traffic fell 35% after
the algorithm update. Conversion rate held steady at 3.1%, confirming this is a traffic problem,
not a product problem."
(35 words, 4 specific insights)

### Density Techniques
1. **Cut throat-clearing**: Remove "We noticed that..." and "It appears that..." — just state the finding.
2. **Use numbers**: "$968" is denser than "revenue decreased somewhat."
3. **Combine what + why**: "Revenue dropped 22% because Pinterest traffic fell" = two insights in one sentence.
4. **Kill adverbs**: "Significantly decreased" → "Dropped 22%." The number IS the significance.
5. **One idea per sentence**: Complex sentences dilute density. Break them up.

---

## 5. Uncertainty Communication

### How to Express Confidence
Never present uncertain findings as certain. But also don't drown in caveats.

```
HIGH CONFIDENCE:
  "Revenue dropped 22% WoW, driven by a 35% decline in Pinterest traffic."
  (State directly. No hedging needed when evidence is strong.)

MEDIUM CONFIDENCE:
  "Revenue dropped 22% WoW, likely driven by a Pinterest algorithm change that reduced our
  pin distribution. The timing aligns, though we can't fully confirm the causal link."
  (State the finding + the uncertainty in ONE sentence.)

LOW CONFIDENCE:
  "Revenue dropped 22% WoW. The cause is unclear. Leading hypotheses: Pinterest algorithm change
  (some supporting evidence), seasonal pattern (inconclusive), or traffic source shift (under investigation).
  More data needed — recommend monitoring through next week before concluding."
  (Be explicit about what you DON'T know.)
```

### The Confidence Spectrum
```
CERTAIN:    "X caused Y" (only with controlled evidence)
LIKELY:     "X most likely caused Y" (strong correlation + plausible mechanism)
POSSIBLE:   "X may have contributed to Y" (some evidence, not conclusive)
SPECULATIVE: "X could be related to Y" (hypothesis without strong evidence)
UNKNOWN:    "We don't know what caused Y" (honest admission)
```

Use the precise word. Don't say "likely" when you mean "possible."

### Presenting Ranges vs Points
```
WRONG: "Next month's revenue will be $5,000."
RIGHT: "Next month's revenue: $4,200-$5,800 (base case: $5,000)."
BETTER: "Next month's revenue: $4,200-$5,800. The base case of $5,000 assumes current Pinterest 
traffic stabilizes. If traffic continues declining, the conservative scenario ($4,200) is more likely."
```

---

## 6. Bad News Delivery

### The Bad News Framework
When delivering negative findings:

1. **State it clearly**: Don't bury bad news. Lead with it.
2. **Quantify it**: "Revenue is down" is scary-vague. "Revenue is down 15%" is manageable.
3. **Contextualize it**: Is this a catastrophe or a blip? Compare to historical variance.
4. **Diagnose it**: Why did it happen? (Even a hypothesis is better than silence.)
5. **Recommend**: What should be done about it?
6. **Scope the risk**: What happens if we do nothing? What's the downside scenario?

```
BAD: "Things aren't looking great this week."
GOOD: "Revenue declined 15% WoW ($1,400 → $1,190). This is the steepest single-week drop in 3 months.
Root cause: Product A conversion rate fell from 3.2% to 1.8% after the Tuesday pricing change.
Recommendation: Revert to the original price and re-test with a smaller increment."
```

### The Honest Broker Standard
The Analyst's credibility depends on delivering bad news as clearly and promptly as good news.
If you sugarcoat, hedge, or delay bad news, decision-makers will lose trust in ALL your reporting.

Rules:
- Never minimize a real problem to avoid discomfort
- Never inflate a minor issue to create drama
- Present the magnitude honestly and let the decision-makers decide how to feel about it
- Pair bad news with diagnosis and recommendation — problems without paths forward are demoralizing

---

## 7. The "So What?" Discipline

### The Test
After writing any sentence in a report, ask: "So what?" If you can't answer that question,
the sentence shouldn't be in the report.

```
"Pinterest impressions were 14,200 this week."
SO WHAT? → "That's a 23% decline from last week, breaking a 4-week growth trend."
SO WHAT? → "If this continues, monthly traffic will fall below the level needed to hit revenue targets."
SO WHAT? → "Recommend testing new pin formats aligned with Pinterest's updated algorithm."

FINAL VERSION: "Pinterest impressions dropped 23% WoW (14,200 vs 18,400), breaking a 4-week growth trend. 
At this rate, monthly traffic will fall below revenue-target thresholds. Recommend testing new pin formats."
```

Every finding in a report should survive at least TWO rounds of "So What?" before inclusion.

---

## 8. Recommendation Framing

### The SPECIFIC Standard
Every recommendation must be:
- **S**pecific: What exactly should be done?
- **P**rioritized: Is this urgent or can it wait?
- **E**vidence-based: What data supports this recommendation?
- **C**lear on ownership: Who should do this?
- **I**mpact-estimated: What's the expected effect?
- **F**easible: Can it actually be done with available resources?
- **I**nvestigable: How will we know if it worked?
- **C**oncise: Stated in 1-2 sentences

```
BAD: "We should improve our Pinterest strategy."
GOOD: "Revert to editorial-style pins this week (PIN team). The product-pin format reduced CTR by 23%
over 2 weeks. Expected recovery: CTR back to 1.8% within 7 days if format was the cause."
```

### Recommendation vs Decision
The Analyst RECOMMENDS. Navigator and Hutch DECIDE.
Frame recommendations as recommendations, not directives:
- "Recommend: [action]" or "Suggest: [action]" — not "We need to [action]"
- Always provide the reasoning so the decision-maker can disagree with informed context

---

## 9. Anti-Patterns to Avoid

### The Dashboard Dump
"Here are all 47 metrics from this week." Nobody reads this. Select the 5-7 that matter.

### The Hedging Spiral
"It could possibly be the case that there might potentially be a decline." Just say "Revenue declined 15%."

### The Methodology Dissertation
"We computed a 14-day exponentially weighted moving average with a half-life of 7 days, applied
a Hodrick-Prescott filter with lambda 1600, and..." Save this for the appendix. Decision-makers
need findings, not process.

### The Vanity Parade
"Great news! Impressions are up 40%!" Impressions are vanity. What happened to revenue?

### The Opinion-as-Data
"I think the product is pricing too high." Where's the data? The Analyst doesn't "think" — the Analyst
measures, analyzes, and concludes based on evidence.

### The Recommendation-Free Report
"Revenue is down. Conversion is down. Traffic is down." ...And? What should be done? A report
without recommendations is a problem statement, not analysis.

### The Emotional Forecast
"Things are looking really concerning and we should be worried." Quantify the concern.
"Revenue trend projects a 25% monthly decline at current trajectory. Conservative scenario: $3,200 
(vs $5,000 target). This gap requires intervention." Same message, but useful.
