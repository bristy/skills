# Content Performance Analytics

How to measure, compare, and diagnose content effectiveness across Pinterest, Twitter/X, and Reddit.

---

## Table of Contents
1. Cross-Platform Content Framework
2. Pinterest Performance Analysis
3. Twitter/X Performance Analysis
4. Reddit Performance Analysis
5. Content-to-Revenue Attribution
6. Content Resonance Scoring
7. Content Lifecycle Analysis
8. Content Optimization Signals
9. Content Report Templates

---

## 1. Cross-Platform Content Framework

### The Content Funnel
Every piece of content moves through stages:
```
CREATED → DISTRIBUTED → SEEN (impressions) → ENGAGED (clicks/replies/saves) → VISITED (your site) → CONVERTED (sale)
```

Measure at EVERY stage. A content piece can succeed at one stage and fail at the next. The diagnosis
depends on WHERE the funnel breaks.

### Platform-Agnostic Metrics
For every piece of content, regardless of platform, compute:
- **Reach**: How many people saw it (impressions)
- **Engagement Rate**: (All meaningful interactions / Impressions) × 100
- **Click-Through Rate**: (Outbound clicks / Impressions) × 100
- **Revenue Attribution**: Revenue from sales where this content was in the referral chain
- **Content ROI**: Revenue attributed / Estimated effort to create

### Cross-Platform Normalization
Raw numbers across platforms are NOT comparable. Normalize:
- **Percentile score**: Where does this content rank within its platform's distribution?
- **Platform-relative rate**: Metric / Platform median for that metric × 100
- A normalized score of 100 = exactly at platform median. 150 = 50% above median. 50 = 50% below.

---

## 2. Pinterest Performance Analysis

### The Pinterest Metrics Hierarchy
1. **Outbound Clicks** — THE metric. This is traffic leaving Pinterest to your Gumroad page.
2. **Click-Through Rate** — Outbound clicks / Impressions. Measures pin quality.
3. **Saves** — Users saving to their boards. Extends content lifespan dramatically.
4. **Impressions** — Distribution reach. Necessary but not sufficient.

Impressions without clicks = your pin gets seen but doesn't compel action.
Clicks without conversions = your pin promises something the product page doesn't deliver.

### Pin Performance Tiers
Based on CTR (outbound clicks / impressions):
- **Elite**: CTR >5% — Study this pin. Replicate its elements.
- **Strong**: CTR 2-5% — Performing well above average.
- **Average**: CTR 0.8-2% — Normal Pinterest performance.
- **Weak**: CTR 0.3-0.8% — Below average. Test new variations.
- **Failing**: CTR <0.3% — This pin isn't working. Stop promoting.

### Pinterest-Specific Diagnostics

**High impressions, low clicks:**
- Image doesn't communicate value clearly
- Text overlay is unclear or too small
- Pin topic is interesting to browse but not to act on
- Wrong audience seeing the pin (board/keyword targeting issue)

**High saves, low clicks:**
- Content is aspirational (people save for later but don't act)
- Missing urgency or clear call-to-action
- Pin communicates the value so well they feel they don't need to click

**Rapid initial impressions, fast decay:**
- Pinterest algorithm tested it, audience didn't engage enough
- Consider: Was the early engagement from the wrong audience segment?

**Slow start, accelerating impressions:**
- Content is being discovered organically through search
- This is the ideal evergreen pattern. These pins have long lifespans.

### Pinterest Content Velocity
Measure impressions in the first 48 hours after publishing:
- **Fast launch** (>500 impressions in 48h): Pinterest algorithm is distributing aggressively
- **Normal launch** (100-500): Standard distribution
- **Slow launch** (<100): Likely poor keyword targeting, weak image, or low-demand topic

### Board-Level Analysis
Aggregate pin performance by board to identify:
- Which TOPICS perform best on Pinterest
- Whether specific boards have higher average CTR (audience-topic fit signal)
- Board follower correlation with pin performance

---

## 3. Twitter/X Performance Analysis

### The X Algorithm Signal Hierarchy
Understanding the algorithm is ESSENTIAL for correct content analysis on X:
```
REPLIES:    13.5x weight (highest signal — this is conversational content)
RETWEETS:   1x weight (distribution signal)
LIKES:      0.5x weight (passive agreement)
BOOKMARKS:  ~1x weight (save for later)
QUOTE TWEETS: ~1x weight (engagement + distribution)
LINK CLICKS: NOT directly weighted for distribution (but critical for your business)
```

### The Reply-Weighted Engagement Score (RWES)
```
RWES = (Replies × 13.5) + (Retweets × 1) + (Likes × 0.5) + (Bookmarks × 1) + (Quote Tweets × 1)
```
This is the REAL engagement score for X content. Standard engagement rate (all interactions / impressions)
is misleading because it treats all interactions equally. RWES reflects actual algorithmic value.

### Tweet Performance Tiers (by RWES / Impressions × 100)
- **Viral**: >5% RWES rate — This tweet is getting massive distribution. Study it.
- **Strong**: 2-5% — Well above average. Content formula is working.
- **Average**: 0.5-2% — Normal performance.
- **Weak**: 0.1-0.5% — Below average. Content isn't sparking conversation.
- **Dead**: <0.1% — This isn't reaching or resonating. Rethink approach.

### X-Specific Diagnostics

**High impressions, low replies:**
- Content is statement-based, not conversation-starting
- Try: Ask questions, share controversial takes, invite disagreement
- The algorithm saw it was getting impressions but no conversation → will throttle distribution

**High replies, low link clicks:**
- Content sparks conversation but doesn't drive traffic
- This is fine for brand building but not for direct revenue
- Consider: Add link clicks as a separate campaign goal, not mixed with engagement posts

**High bookmarks relative to likes:**
- Content is VALUABLE (people save it for reference)
- This is a signal of utility content — how-tos, frameworks, tools
- These tweets may not go viral but build long-term authority

**Reply rate declining over time:**
- Audience may be fatiguing on your content style
- Or you're shifting to less conversational formats
- Check: has your tweet format changed? More links, fewer questions?

### Follower Growth Correlation
Track 7-day rolling follower growth alongside content performance:
- Strong correlation between reply rate and follower growth (algorithm shows your replies to others)
- Weak correlation between impressions alone and follower growth
- Negative follower events (unfollows spike) may indicate content misalignment with audience expectations

---

## 4. Reddit Performance Analysis

### Reddit Metrics That Matter
1. **Net Upvotes on comments with product links** — Community endorsement
2. **Profile Clicks from subreddit activity** — Interest generated
3. **Traffic to Gumroad from Reddit referrer** — Actual business impact
4. **Karma trend by subreddit** — Standing in each community

### Reddit-Specific Dynamics
Reddit is fundamentally different from Pinterest and Twitter/X:
- **Community-first**: Self-promotion is actively punished in most subreddits
- **Value-first**: You must contribute value before anyone clicks your profile or link
- **Bursty traffic**: Reddit posts spike in first 4-12 hours then die quickly
- **Long-tail via search**: High-karma posts continue to get views via Google and Reddit search
- **Subreddit fit is everything**: The same comment can get +100 in one sub and -20 in another

### Subreddit Performance Analysis
For each subreddit where content is posted:
```
SUBREDDIT: r/[name]
POSTS/COMMENTS (trailing 30d): [count]
AVG UPVOTES: [count]
TOTAL KARMA EARNED: [count]
PROFILE CLICKS ATTRIBUTED: [count] (if available)
REVENUE ATTRIBUTED: $[amount] (from Gumroad referrer matching)
KARMA PER POST: [average]
REVENUE PER POST: $[average]
ASSESSMENT: [High value / Medium value / Low value / Negative ROI]
```

### Reddit Content Type Analysis
Different content types perform differently on Reddit:
- **Helpful comments on others' posts**: Usually highest karma-per-effort
- **Original how-to posts**: High effort but can generate significant traffic
- **Link posts to your products**: Usually lowest performing (often downvoted)
- **AMA-style engagement**: High effort but builds massive credibility

Track performance by content type to optimize effort allocation.

---

## 5. Content-to-Revenue Attribution

### Attribution Chain
```
Content piece → Platform engagement → Click to site → Product view → Sale
```

At each step, measure the conversion rate and identify drop-off points.

### Attribution Methods

**Direct attribution** (highest confidence):
- Content contains a link to a specific Gumroad product
- Gumroad referrer field matches the content's platform
- Attribution: 100% of sale revenue to that content piece

**Platform attribution** (medium confidence):
- Sale's referrer matches a platform (e.g., pinterest.com) but not a specific pin
- Attribution: Revenue attributed to the platform, but cannot pinpoint which content piece
- Use: Allocate among content pieces proportional to their click volume

**Assisted attribution** (lower confidence):
- User may have seen content on one platform, then later visited directly or via search
- Detection: If a buyer previously clicked from a platform (within 7-day window) then later converted via direct
- Use: Track but present separately as "assisted" revenue

### Revenue per Content Piece
```
Content ROI = Revenue directly attributed / Estimated creation effort (in hours or equivalent cost)
```

Rank all content by Content ROI to identify:
- Content FORMATS that drive the most revenue per effort
- Content TOPICS that drive the most revenue per effort
- Content PLATFORMS that drive the most revenue per effort

---

## 6. Content Resonance Scoring

### The Resonance Score (per content piece)
A composite score that predicts whether content is "resonating" with the audience:

```
Resonance Score = (
  Engagement Rate Percentile × 0.30 +
  Velocity Percentile × 0.25 +
  Conversion Contribution Percentile × 0.25 +
  Longevity Percentile × 0.20
)
```

Where:
- **Engagement Rate Percentile**: How this content's engagement rate ranks vs all your content on that platform
- **Velocity Percentile**: How quickly it accumulated engagement (first 48h performance)
- **Conversion Contribution Percentile**: Revenue or clicks attributed, ranked vs all content
- **Longevity Percentile**: How long it continues generating impressions/clicks (14-day tail)

### Resonance Categories
- 80-100: **Breakthrough** — This is striking a nerve. Replicate the formula.
- 60-79: **Strong** — Above-average performance. Good content.
- 40-59: **Average** — Meeting baseline expectations.
- 20-39: **Weak** — Below expectations. Don't repeat this approach.
- 0-19: **Dud** — Failed to resonate. Diagnose why and avoid repeating.

### "What Resonates" Report (Weekly)
Each week, identify:
1. **Top 3 resonating content pieces** (highest resonance score) with analysis of WHY they worked
2. **Bottom 3 performers** with diagnosis of WHY they didn't
3. **Emerging patterns**: Topics, formats, or styles that are trending up or down
4. **Actionable insight**: One specific content recommendation for next week

---

## 7. Content Lifecycle Analysis

### Lifecycle Stages
Every content piece has a lifecycle:
```
LAUNCH (0-48h): Initial distribution. Algorithm testing. Velocity matters.
PEAK (2-7 days): Maximum engagement period for most content.
DECAY (7-30 days): Engagement declining. Still generating some traffic.
LONG TAIL (30+ days): Minimal ongoing engagement. Evergreen pieces still generate here.
```

### Identifying Evergreen Content
Evergreen content generates traffic long after publication. Identify by:
- Continues to receive >10% of its peak-week impressions at 30+ days
- Traffic from this content has a SEARCH component (people finding it via search)
- Revenue attribution continues beyond the initial peak period

Evergreen content is EXTREMELY valuable. It generates compounding returns.
When you find evergreen pieces, flag them prominently and recommend:
- Refresh/update the content periodically
- Create more content on the same topic
- Optimize the content's SEO and discoverability

### Identifying Viral Content
Viral content has an abnormally steep launch curve:
- >10x normal first-48-hour impressions
- Engagement rate >3x platform average during peak
- Rapid follower/subscriber growth during viral window

Viral content is valuable but unreliable. Never build strategy around expecting virality.
When it happens, capitalize by:
- Monitoring where viral traffic goes (which products benefit?)
- Quickly publishing follow-up content on the same topic
- Converting viral attention into email subscribers (owned audience)

---

## 8. Content Optimization Signals

### Format Performance Comparison
Track engagement rates by content format within each platform:

**Pinterest formats**: Standard pins, video pins, idea pins, carousel pins
**X formats**: Text-only, text + image, text + link, threads, polls
**Reddit formats**: Comments, link posts, text posts, image posts

### Timing Analysis
Compute average engagement by:
- Day of week (which days get highest engagement per platform?)
- Time of day (which hours perform best?)
- Present as a heatmap for easy interpretation

### Topic Performance
Cluster content by topic (manual tagging or keyword-based):
- Which topics consistently drive high engagement?
- Which topics drive high engagement but low conversion?
- Which topics drive low engagement but high conversion?

The ideal content strategy emphasizes topics with BOTH high engagement AND high conversion.
If forced to choose: prioritize high-conversion topics (they directly drive revenue).

---

## 9. Content Report Templates

### Weekly Content Section (for Signal Memo)
```
## Content Signal

**Content published this week**: [count] pieces ([breakdown by platform])
**Total engagement generated**: [sum across platforms, with platform breakdown]
**Content-attributed revenue**: $[amount] ([+/-%] vs last week)

### What resonated:
- [Top content piece]: [platform] — [key metric] — [why it worked]
- [Second]: [platform] — [key metric] — [brief note]

### What didn't:
- [Bottom performer]: [platform] — [key metric] — [diagnosis]

### Platform signals:
- Pinterest: [1-line summary — CTR trend, top pin, any anomalies]
- Twitter/X: [1-line summary — reply rate trend, top tweet, any anomalies]
- Reddit: [1-line summary — karma trend, any notable engagement]

### Recommendation:
[One specific, actionable content recommendation for next week]
```
