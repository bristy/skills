# Root Cause Analysis

Systematic methods for diagnosing WHY metrics moved, systems failed, or performance changed.

---

## Table of Contents
1. RCA Principles
2. The Five Whys Framework
3. Fishbone (Ishikawa) Diagnosis
4. Change-Point Detection
5. Elimination Methodology
6. Timeline Reconstruction
7. Cross-System Dependency Tracing
8. Hypothesis Testing Workflow
9. RCA Report Template

---

## 1. RCA Principles

### The Goal
Find the ROOT cause — the deepest actionable reason something happened — not just the proximate cause.

```
PROXIMATE CAUSE: "Revenue dropped because fewer people bought"
  ↓ (why?)
INTERMEDIATE CAUSE: "Fewer people bought because conversion rate declined"
  ↓ (why?)
INTERMEDIATE CAUSE: "Conversion declined because product page views dropped"
  ↓ (why?)
ROOT CAUSE: "Product page views dropped because the Pinterest algorithm deprioritized our pin format"
  → THIS is actionable. The fix: change pin format.
```

### RCA Rules
1. **Don't stop at the first answer.** The first "because" is almost never the root cause.
2. **Follow the data, not assumptions.** Every step in the chain must be supported by evidence.
3. **Consider multiple hypotheses.** Don't tunnel-vision on the first plausible explanation.
4. **Time-box the investigation.** If you can't find the root cause in a reasonable timeframe,
   report what you know, flag what you don't, and recommend further investigation.
5. **Distinguish root cause from contributing factors.** There may be one root cause and several
   factors that made it worse.

---

## 2. The Five Whys Framework

### How to Apply
Start with the observed problem and ask "why?" five times (or until you reach a cause you can act on):

```
PROBLEM: Revenue dropped 25% this week

Why #1: Why did revenue drop?
→ Because the number of transactions decreased by 30%

Why #2: Why did transactions decrease?
→ Because product page views decreased by 35%

Why #3: Why did product page views decrease?
→ Because Pinterest referral traffic dropped by 50%

Why #4: Why did Pinterest traffic drop?
→ Because our top-performing pin stopped receiving impressions

Why #5: Why did the pin stop receiving impressions?
→ Because Pinterest's February algorithm update deprioritized our pin format (static image with text overlay)

ROOT CAUSE: Pinterest algorithm change affecting our primary pin format
RECOMMENDED FIX: Test new pin formats (video, carousel) aligned with new algorithm preferences
```

### Five Whys Pitfalls
- **Stopping too early**: "Revenue dropped because traffic dropped" is not a root cause
- **Going too deep**: "Revenue dropped because the internet exists" is too abstract to act on
- **Linear thinking**: The real cause might branch — multiple factors contributing
- **Blame attribution**: Focus on SYSTEMS and PROCESSES, not people

### The Actionability Test
The root cause is deep enough when the fix is SPECIFIC and IMPLEMENTABLE.
"Fix the pin format" = actionable. "Get more traffic" = not actionable (too vague).

---

## 3. Fishbone (Ishikawa) Diagnosis

### When to Use
When the problem could have multiple contributing causes across different categories.

### The Categories (adapted for digital business)
```
CONTENT ─────┐
PLATFORM ────┤
PRODUCT ─────┼──→ [OBSERVED PROBLEM]
SYSTEM ──────┤
EXTERNAL ────┤
DATA ────────┘
```

### Applying the Fishbone
For each category, brainstorm possible causes:

**Content causes**: Did content quality, volume, format, or timing change?
**Platform causes**: Did a platform algorithm, policy, or feature change?
**Product causes**: Did pricing, page copy, availability, or quality change?
**System causes**: Did a cron job fail, session expire, or API break?
**External causes**: Competitor action, market shift, seasonal pattern, economic factor?
**Data causes**: Is the data itself wrong? Missing data, collection error, reporting bug?

### Scoring Each Branch
For each potential cause:
```
1. Is there EVIDENCE supporting this cause? (Data, timing coincidence, known event)
2. If this cause were removed, would the problem be resolved? (Necessity test)
3. Is this cause sufficient to explain the MAGNITUDE of the problem? (Sufficiency test)
```

Rank causes by evidence strength and eliminate those that fail the necessity or sufficiency tests.

---

## 4. Change-Point Detection

### What is a Change Point?
The exact moment when a metric's behavior shifted. Identifying the change point helps narrow
the search for root cause — you look for what changed AT THAT TIME.

### Detection Methods

**Visual inspection**: Plot the metric and look for obvious breaks
**CUSUM (Cumulative Sum)**: Detect shifts in the mean
```
1. Compute the running mean up to each point
2. Track cumulative deviation from the mean
3. When cumulative deviation exceeds a threshold, a change point is detected
```

**Binary search**: For daily data with clear "before" and "after" states
```
1. Compare the first half vs second half of the period
2. If they differ significantly, the change point is in the boundary
3. Narrow the boundary by halving until you find the specific day
```

### What to Do With the Change Point
Once you know WHEN the change happened:
1. Check: What changed on that date? (Deployment, content change, price change, platform update)
2. Check: What external events occurred? (Algorithm change, competitor launch, holiday)
3. Check: What system events occurred? (Cron failure, session expiry, API error)
4. Cross-reference with ALL known events around that timestamp
5. The coinciding event is your primary hypothesis

---

## 5. Elimination Methodology

### Systematic Hypothesis Elimination
When multiple hypotheses exist, systematically eliminate them:

```
HYPOTHESES:
1. Pinterest algorithm change → CHECK: Did overall Pinterest CTR decline or just ours?
2. Content quality dropped → CHECK: Did engagement per piece decline or just volume?
3. Seasonal effect → CHECK: Did same period last year show similar pattern?
4. Product page broken → CHECK: Is conversion rate from OTHER sources also down?
5. Cron job failure → CHECK: Were all data collection jobs running clean?

ELIMINATION:
✗ Hypothesis 3 (seasonal): Last year showed no decline in same period. Eliminated.
✗ Hypothesis 5 (cron): All jobs running clean, data quality verified. Eliminated.
✗ Hypothesis 4 (page broken): Conversion from direct traffic is stable. Eliminated.
? Hypothesis 2 (content quality): Engagement per piece is slightly down. Partially supported.
✓ Hypothesis 1 (algorithm): Overall Pinterest distribution for our format type is down 40%. Strongly supported.

CONCLUSION: Primary cause is Pinterest algorithm change (H1), with possible contributing
factor from content quality (H2). Recommend: format adaptation + content quality audit.
```

### The "Control Group" Approach
When possible, find a natural control:
- If you suspect a PRODUCT page issue: Compare conversion from different traffic sources
  (if conversion is down from all sources → page issue; if only from one → source issue)
- If you suspect a PLATFORM issue: Compare your performance to general platform trends
  (if everyone's down → platform issue; if only you → your content/approach issue)
- If you suspect a SYSTEM issue: Check if other systems dependent on the same infrastructure
  are also affected

---

## 6. Timeline Reconstruction

### Building the Investigation Timeline
For any significant anomaly, reconstruct a complete timeline:

```
INVESTIGATION TIMELINE: [Problem Name]

[timestamp] — Normal state. [Metric] at [value], within expected range.
[timestamp] — [Event A] occurred. [Details]
[timestamp] — [Metric] began to deviate. [First abnormal reading]
[timestamp] — [Event B] occurred. [Details]
[timestamp] — [Metric] crossed WATCH threshold.
[timestamp] — [Event C] occurred. [Details]
[timestamp] — [Metric] crossed ALERT threshold.
[timestamp] — Anomaly detected by Analyst.
[timestamp] — Investigation initiated.
[timestamp] — Root cause identified: [description]
[timestamp] — Fix implemented: [description]
[timestamp] — [Metric] began recovering.
[timestamp] — [Metric] returned to normal range.

TOTAL TIME:
  Problem onset to detection: [duration]
  Detection to root cause: [duration]
  Root cause to fix: [duration]
  Fix to recovery: [duration]
  Total impact duration: [duration]
```

### Why Timelines Matter
- They reveal the SEQUENCE of events (critical for establishing cause-effect)
- They expose detection delays (how quickly did we catch it?)
- They measure response effectiveness (how quickly did we fix it?)
- They provide a template for preventing similar issues

---

## 7. Cross-System Dependency Tracing

### When a Problem Crosses System Boundaries
Many root causes aren't in the system where the symptom appears.

```
SYMPTOM: Revenue dropped
  └── Revenue depends on: Product page views
      └── Product page views depend on: Platform traffic
          └── Platform traffic depends on: Content distribution
              └── Content distribution depends on: Platform algorithm + Content quality
                  └── Content publishing depends on: Cron job (publishing scheduler)
                      └── Cron job depends on: AgentReach session
                          └── AgentReach session: EXPIRED 3 days ago ← ROOT CAUSE
```

### Tracing Protocol
1. Start at the SYMPTOM (the metric that triggered the investigation)
2. Identify what the symptomatic system DEPENDS ON
3. Check the health of each dependency
4. For any unhealthy dependency, repeat step 2-3 (trace further upstream)
5. Continue until you find the first broken link in the chain

---

## 8. Hypothesis Testing Workflow

### The Scientific Method Applied to Business Analysis

```
STEP 1: OBSERVE
  What anomaly was detected? What does the data show?

STEP 2: HYPOTHESIZE
  What are the 3-5 most plausible explanations?
  Rank by prior probability (how likely is each, based on experience?)

STEP 3: PREDICT
  If hypothesis X is true, what ELSE should we see in the data?
  (Each hypothesis should make at least one testable prediction)

STEP 4: TEST
  Check: Does the predicted evidence exist?
  For each hypothesis, mark as: SUPPORTED / WEAKENED / ELIMINATED

STEP 5: CONCLUDE
  Which hypothesis has the strongest evidence?
  What's the confidence level?
  What alternative explanations remain?

STEP 6: RECOMMEND
  Based on the conclusion, what specific action should be taken?
  What would DISPROVE the conclusion? (How would we know if we're wrong?)
```

---

## 9. RCA Report Template

```markdown
# Root Cause Analysis: [Problem Title]

**Date**: [investigation date]
**Trigger**: [what anomaly or incident triggered this investigation]
**Severity**: [SEV-1/2/3/4]
**Investigator**: Analyst

## Problem Statement
[One paragraph: What happened, when, magnitude, and impact]

## Investigation Summary
[2-3 paragraphs: What was examined, what was found]

## Timeline
[Chronological event sequence — see Section 6]

## Hypotheses Evaluated
| # | Hypothesis | Evidence For | Evidence Against | Verdict |
|---|-----------|-------------|-----------------|---------|
| 1 | [description] | [evidence] | [evidence] | ✓ SUPPORTED |
| 2 | [description] | [evidence] | [evidence] | ✗ ELIMINATED |
| 3 | [description] | [evidence] | [evidence] | ? INCONCLUSIVE |

## Root Cause
**Primary**: [root cause with supporting evidence]
**Contributing factors**: [factors that amplified the impact]
**Confidence**: [High / Medium / Low]

## Impact Assessment
- Revenue impact: $[amount]
- Duration: [how long the problem lasted]
- Systems affected: [list]
- Data quality impact: [any data that may be compromised]

## Recommendations
1. **Immediate**: [fix the proximate issue]
2. **Short-term**: [address the root cause]
3. **Long-term**: [prevent recurrence]

## Prevention
[What monitoring, alerting, or process change would catch this earlier or prevent it?]

## Open Questions
[What remains unknown? What further investigation is recommended?]
```
