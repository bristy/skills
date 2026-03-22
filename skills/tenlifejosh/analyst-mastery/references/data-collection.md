# Data Collection & Integration

How to pull, validate, normalize, and maintain data from every source the Analyst depends on.

---

## Table of Contents
1. Data Source Registry
2. Gumroad API Data Collection
3. Pinterest Analytics Collection
4. Twitter/X Analytics Collection
5. Reddit Analytics Collection
6. Cron Job & System Log Collection
7. AgentReach Session Monitoring
8. Cross-Source Data Normalization
9. Data Quality Validation Framework
10. Collection Scheduling & Automation
11. Error Handling & Recovery
12. Data Freshness Standards

---

## 1. Data Source Registry

Every data source has a reliability tier and a freshness requirement:

| Source | Type | Reliability | Freshness Requirement | Auth Method |
|--------|------|------------|----------------------|-------------|
| Gumroad API | REST API | High | Daily (revenue), Real-time (alerts) | API key / OAuth |
| Gumroad Dashboard | Web scrape fallback | Medium | Daily | Session auth |
| Pinterest Analytics | API / Dashboard | Medium | Daily | OAuth 2.0 |
| Twitter/X Analytics | API / Dashboard | Medium | Daily | OAuth 2.0 / API key |
| Reddit | API / Manual | Medium-Low | Weekly | OAuth 2.0 |
| Cron logs | Local filesystem | High | Real-time | System access |
| AgentReach | Session monitoring | High | Every 6 hours | Session tokens |
| Google Analytics | API | High | Daily | OAuth 2.0 |

---

## 2. Gumroad API Data Collection

Gumroad is the PRIMARY revenue data source. Treat it with the highest rigor.

### Key Endpoints

**Sales Data** — `/api/v2/sales`
```
GET https://api.gumroad.com/v2/sales
Parameters:
  - after: date (ISO 8601) — start of range
  - before: date (ISO 8601) — end of range
  - page: integer — for pagination
  - access_token: string — your Gumroad API key

Response fields to extract:
  - id: unique sale ID
  - product_id: which product was purchased
  - product_name: human-readable product name
  - price: sale price in cents
  - currency: currency code
  - created_at: timestamp of sale
  - refunded: boolean — whether this sale was later refunded
  - referrer: traffic source URL (CRITICAL for attribution)
  - variants: any product variants selected
  - email: buyer email (handle with privacy care)
  - quantity: number purchased
```

**Product Data** — `/api/v2/products`
```
GET https://api.gumroad.com/v2/products
Parameters:
  - access_token: string

Response fields to extract per product:
  - id: product ID
  - name: product name
  - price: listed price in cents
  - sales_count: total historical sales
  - sales_usd_cents: total historical revenue
  - views_count: total product page views
  - published: boolean — is it live?
  - url: product URL
```

### Collection Protocol
1. **Daily revenue pull**: Run at 00:15 UTC daily. Pull all sales from previous day (00:00-23:59 UTC).
2. **Pagination**: Gumroad paginates at 10 results. Loop through all pages until empty response.
3. **Deduplication**: Track sale IDs to prevent double-counting if a pull overlaps.
4. **Refund reconciliation**: On each pull, also check for refund status changes on previous sales.
5. **Store raw responses**: Always store the raw API response before processing. Enables re-processing if logic changes.

### Referrer Attribution Mapping
Map Gumroad's `referrer` field to standardized source names:
```
pinterest.com, pin.it → "Pinterest"
twitter.com, t.co, x.com → "Twitter/X"
reddit.com, old.reddit.com → "Reddit"
google.com, google.co.* → "Organic Search"
(empty or direct) → "Direct"
any email service domain → "Email"
everything else → "Other: {domain}"
```

### Rate Limits & Error Handling
- Gumroad API rate limit: ~240 requests per minute. Stay below 200/min for safety.
- On 429 (rate limited): Back off exponentially — wait 30s, 60s, 120s, then alert.
- On 5xx: Retry 3 times with 10-second intervals. If still failing, log and alert.
- On 401: Authentication issue. Alert immediately — likely API key rotation needed.

---

## 3. Pinterest Analytics Collection

### Data Points to Collect
- **Pin-level metrics**: Impressions, outbound clicks, saves, close-ups, CTR
- **Board-level metrics**: Aggregate engagement by board (identifies topic performance)
- **Time-series data**: Daily performance per pin over trailing 30 days
- **Top performers**: Pins ranked by outbound clicks (the metric that drives revenue)

### Collection Methods
**Method 1 — Pinterest Analytics API (preferred)**
- Use Pinterest API v5 for pin analytics
- Endpoint: `GET /v5/pins/{pin_id}/analytics`
- Parameters: start_date, end_date, metric_types (IMPRESSION, OUTBOUND_CLICK, SAVE, PIN_CLICK)
- Rate limit: 1000 requests per minute. Paginate cleanly.

**Method 2 — Pinterest Analytics Dashboard (fallback)**
- Navigate to analytics.pinterest.com
- Export "Overview" and "Top Pins" data as CSV
- Parse and normalize into standard format
- Use when API is unavailable or for metrics not in API

### Key Derivations
- **Pin CTR**: Outbound clicks / Impressions × 100
- **Pin Efficiency**: Outbound clicks / (Saves + Close-ups) — measures conversion from interest to action
- **Content Velocity**: Impressions in first 48 hours post-publish (leading indicator of pin success)
- **Pin-to-Revenue**: Cross-reference with Gumroad referrer data to attribute sales to specific pins

---

## 4. Twitter/X Analytics Collection

### Data Points to Collect
- **Tweet-level metrics**: Impressions, replies, retweets, likes, quote tweets, bookmark, link clicks
- **Reply-weighted engagement**: Replies × 13.5 + other engagement (reflects actual algorithm weighting)
- **Profile metrics**: Follower count, profile visits, mention count
- **Time-series**: Daily metrics over trailing 28 days

### Collection Methods
**Method 1 — X API v2 (preferred)**
- Endpoint: `GET /2/tweets/{id}` with `tweet.fields=public_metrics`
- Returns: impression_count, reply_count, retweet_count, like_count, quote_count, bookmark_count
- For link clicks: Use `GET /2/tweets/{id}` with `tweet.fields=organic_metrics` (requires elevated access)
- Rate limits vary by tier. Track remaining quota in response headers.

**Method 2 — X Analytics Dashboard (fallback)**
- Navigate to analytics.x.com
- Export tweet activity data
- Parse CSV into standard format

### Critical: The Reply Signal
Replies are THE dominant algorithmic signal on X. The algorithm weights replies approximately 13.5x compared
to likes for distribution decisions. This means:
- A tweet with 10 replies and 50 likes gets MORE distribution than a tweet with 2 replies and 500 likes
- ALWAYS compute reply-weighted engagement: `(replies × 13.5) + retweets + (likes × 0.5) + (bookmarks × 1)`
- Rank content by reply-weighted engagement, NOT by impressions or likes alone
- If reply rate drops, distribution will follow. This is a LEADING indicator.

---

## 5. Reddit Analytics Collection

### Data Points to Collect
- **Post/comment-level**: Upvotes (net), comment count, karma earned
- **Profile-level**: Total karma, karma by subreddit
- **Referral tracking**: Clicks from Reddit to Gumroad (via referrer matching)
- **Subreddit performance**: Which subreddits generate the most engagement per contribution

### Collection Methods
**Method 1 — Reddit API (preferred)**
- Use Reddit's OAuth2 API
- Endpoint: `GET /user/{username}/overview` for all posts and comments
- Extract: score, subreddit, created_utc, permalink, num_comments
- Rate limit: 60 requests per minute. Use `User-Agent` header properly.

**Method 2 — Manual Tracking (supplement)**
- Maintain a log of posts/comments with links to Gumroad products
- Cross-reference with Gumroad referrer data for attribution
- Reddit doesn't provide link click data — attribution relies on Gumroad's referrer field

### Reddit-Specific Considerations
- Karma is a LAGGING indicator — it reflects value already delivered
- Subreddit fit matters enormously — same content can get +50 or -10 depending on subreddit
- Self-promotion rules vary by subreddit. Track which subreddits allow product links.
- Reddit traffic tends to be BURSTY — spikes then drops quickly. Don't over-index on single-day Reddit numbers.

---

## 6. Cron Job & System Log Collection

### What to Collect
For every scheduled job in the system:
- **Job name/identifier**
- **Scheduled time**: When it should have run
- **Actual run time**: When it actually started
- **Completion time**: When it finished
- **Exit status**: Success (0), error (non-zero), timeout, skipped
- **Output/logs**: Stdout and stderr captured
- **Output validation**: Did the job produce the EXPECTED output, not just exit code 0?

### Collection Protocol
```
Parse cron logs from:
- /var/log/cron (or systemd journal for systemd-based systems)
- Application-level job logs
- CI/CD pipeline logs
- Custom job runners

For each job execution, create a record:
{
  "job_id": "string",
  "job_name": "string",
  "scheduled_at": "ISO 8601",
  "started_at": "ISO 8601 or null",
  "completed_at": "ISO 8601 or null",
  "exit_code": "integer or null",
  "status": "success | failure | timeout | skipped | silent_failure",
  "output_valid": "boolean — did it produce expected output?",
  "error_message": "string or null",
  "duration_seconds": "float"
}
```

### Silent Failure Detection
A silent failure is a job that exits successfully (code 0) but produces incorrect or empty output.
Detection rules:
- Job produces no output when output is expected → SILENT FAILURE
- Job output size is <10% of typical size → POTENTIAL SILENT FAILURE (investigate)
- Job completes in <1% of typical duration → SUSPICIOUS (may have skipped actual work)
- Job output contains error strings despite exit code 0 → SILENT FAILURE

SILENT FAILURES ARE MORE DANGEROUS THAN LOUD FAILURES. Loud failures are noticed. Silent failures
corrupt downstream data without anyone knowing. Flag them as ALERT severity.

---

## 7. AgentReach Session Monitoring

### What to Monitor
- **Active session count**: How many sessions are currently valid
- **Session expiry timestamps**: When each session will expire
- **Time to expiry**: For each session, how much time remains
- **Refresh history**: When sessions were last refreshed, success/failure
- **Dependent systems**: Which automated processes depend on each session

### Monitoring Protocol
1. Check session status every 6 hours
2. Calculate time-to-expiry for each active session
3. Generate pre-expiry warnings at 72h, 48h, 24h, 12h
4. On failed refresh: ALERT immediately — manual intervention likely required
5. Track session refresh success rate over trailing 30 days

### Expiry Countdown Format
```
SESSION: [session_name]
STATUS: Active / Expiring Soon / Expired
EXPIRY: [timestamp]
TIME REMAINING: [hours]h [minutes]m
DEPENDENT SYSTEMS: [list of systems that will break if this expires]
LAST REFRESH: [timestamp] — [success/failure]
ACTION: None / Monitor / Refresh Now / URGENT: Manual intervention required
```

---

## 8. Cross-Source Data Normalization

When combining data from multiple sources, normalize on these dimensions:

### Time Normalization
- **Standard timezone**: All timestamps converted to UTC for storage, displayed in user's local timezone
- **Period alignment**: When comparing across sources, ensure periods match exactly
- **Granularity alignment**: If one source has daily data and another has hourly, aggregate hourly to daily before comparing

### Currency Normalization
- Gumroad reports in USD by default. Verify currency field on international sales.
- All revenue figures stored in USD cents (integer) to avoid floating-point errors.
- Convert at the exchange rate on the transaction date, not the reporting date.

### Naming Normalization
- Product names: Use Gumroad product_id as canonical identifier, not name (names can change)
- Traffic sources: Use the standard source mapping from Section 2 (Gumroad referrer attribution)
- Platform names: "Twitter/X" not "Twitter" or "X" alone (consistency)

### Metric Normalization for Cross-Platform Comparison
Raw numbers across platforms are NOT comparable (100 Pinterest impressions ≠ 100 Twitter/X impressions).
Always normalize to platform-relative scores when comparing:
- Compute each metric as a percentile within that platform's historical distribution
- Or compute as a ratio to the platform's median/average
- The Cross-Platform Content Score in kpi-definitions.md uses this approach

---

## 9. Data Quality Validation Framework

Run these checks on EVERY data pull:

### Completeness Checks
- [ ] Expected number of records received (compare to prior periods)
- [ ] No gaps in time series (every expected time bucket has data)
- [ ] All expected data fields populated (no unexpected nulls)
- [ ] All expected data sources responded (no silent API failures)

### Consistency Checks
- [ ] Revenue totals match between API pull and dashboard (within 1% tolerance)
- [ ] Record counts don't have implausible jumps (>3x prior period = investigate)
- [ ] Timestamps are within expected range (no future dates, no dates before last pull)
- [ ] No duplicate records (check unique IDs)

### Freshness Checks
- [ ] Data is from the expected period (not stale from a failed prior pull)
- [ ] Timestamps of most recent records are within expected freshness window
- [ ] No data source is more than 2x its freshness requirement behind

### Validity Checks
- [ ] Monetary values are positive (or explicitly flagged as refunds)
- [ ] Percentages are 0-100 (or 0-1 depending on format — be consistent)
- [ ] Counts are non-negative integers
- [ ] URLs and emails pass format validation
- [ ] No impossible metric values (e.g., conversion rate > 100%)

### When Data Quality Fails
1. Log the failure with specific details (which check, which source, what was expected vs found)
2. If the affected data is critical (revenue, system health): ALERT
3. If non-critical: WATCH, include in next report with quality caveat
4. NEVER use data that fails quality checks without flagging the issue
5. In reports, always note: "Data quality: [CLEAN / {N} issues found — see notes]"

---

## 10. Collection Scheduling & Automation

### Daily Schedule (all times UTC)

| Time | Task | Sources | Priority |
|------|------|---------|----------|
| 00:15 | Revenue pull | Gumroad API | CRITICAL |
| 00:30 | Product metrics refresh | Gumroad API | HIGH |
| 01:00 | Content engagement pull | Pinterest, Twitter/X | HIGH |
| 01:30 | System health snapshot | Cron logs, AgentReach | CRITICAL |
| 06:00 | Session expiry check | AgentReach | HIGH |
| 12:00 | Midday session expiry check | AgentReach | MEDIUM |
| 18:00 | Evening session expiry check | AgentReach | HIGH |
| 23:45 | Pre-close day summary | All sources | MEDIUM |

### Weekly Schedule

| Day | Task | Output |
|-----|------|--------|
| Monday | Full data quality audit | Data Quality Report |
| Wednesday | Mid-week trend check | Mid-Week Signal Note (internal) |
| Friday | Weekly Signal Memo generation | Weekly Signal Memo → Navigator + Hutch |
| Sunday | Benchmark recalculation | Updated benchmark values |

### Monthly Schedule

| When | Task | Output |
|------|------|--------|
| 1st | Monthly deep-dive compilation | Monthly Performance Report |
| 1st | Benchmark refresh | Updated benchmark thresholds |
| 15th | Mid-month trend assessment | Mid-Month Check-in |

---

## 11. Error Handling & Recovery

### Retry Logic
```
For all API calls:
  Attempt 1: Immediate
  Attempt 2: Wait 10 seconds
  Attempt 3: Wait 30 seconds
  Attempt 4: Wait 120 seconds
  After 4 failures: Log error, use cached data (if <24h old), alert operator

For file/log reads:
  Attempt 1: Immediate
  Attempt 2: Wait 5 seconds
  After 2 failures: Alert — likely filesystem or access issue
```

### Fallback Data Hierarchy
When primary data is unavailable:
1. Use cached data from last successful pull (flag as stale with age)
2. Use dashboard/manual export as fallback (flag as lower confidence)
3. If no data available, report the gap explicitly — NEVER interpolate or guess

### Recovery After Outage
When a data source recovers after an outage:
1. Pull ALL data from the gap period (not just the latest)
2. Re-run quality validation on backfilled data
3. Re-compute any derived metrics affected by the gap
4. Note the gap in the next report: "Data from [start]-[end] was backfilled after [source] outage"

---

## 12. Data Freshness Standards

| Data Type | Maximum Acceptable Staleness | Action If Exceeded |
|-----------|-----------------------------|--------------------|
| Revenue (daily) | 2 hours after scheduled pull | ALERT |
| System health | 12 hours | ALERT |
| Content engagement | 24 hours | WATCH |
| Session expiry | 12 hours | ALERT |
| Product metrics | 24 hours | WATCH |
| Reddit analytics | 48 hours | Log only |
| Benchmarks | 7 days | Recalculate |

Every data point in every report should have an implicit freshness guarantee. If data is stale beyond
these thresholds, the report MUST disclose it.
