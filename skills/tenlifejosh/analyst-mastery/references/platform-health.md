# Platform & System Health

How to monitor, diagnose, and report on the health of all automated systems, integrations, and platform dependencies.

---

## Table of Contents
1. System Health Architecture
2. Cron Job Monitoring
3. AgentReach Session Management
4. API Integration Health
5. Silent Failure Detection
6. Dependency Health Mapping
7. System Health Scoring
8. Incident Classification
9. Health Report Templates

---

## 1. System Health Architecture

### The Three Pillars of System Health
1. **Availability**: Is the system running? (uptime, cron success rates)
2. **Correctness**: Is it producing the right output? (silent failure detection)
3. **Performance**: Is it running within acceptable parameters? (latency, throughput)

A system can fail on any pillar independently. The most dangerous failures are correctness failures
(silent failures) because they corrupt downstream analysis without triggering alarms.

### Health Monitoring Layers
```
Layer 1 — HEARTBEAT: Is the process alive and responding?
Layer 2 — EXECUTION: Did the scheduled task actually run?
Layer 3 — OUTPUT VALIDATION: Did it produce correct and complete output?
Layer 4 — DOWNSTREAM IMPACT: Are systems that depend on this output functioning correctly?
```

Most monitoring systems only cover Layers 1-2. The Analyst MUST cover all four layers.

---

## 2. Cron Job Monitoring

### Cron Job Registry
Maintain a living registry of every scheduled job:

```
JOB REGISTRY ENTRY:
  Job ID: [unique identifier]
  Job Name: [human-readable name]
  Schedule: [cron expression, human-readable equivalent]
  Criticality: [CRITICAL / HIGH / MEDIUM / LOW]
  Expected Duration: [typical runtime range]
  Expected Output: [description of what successful output looks like]
  Dependencies: [what this job depends on — APIs, sessions, other jobs]
  Dependents: [what depends on this job's output]
  Owner: [which agent or system is responsible]
  Last Known Good Run: [timestamp]
  Consecutive Failures: [count]
```

### Criticality Classification

**CRITICAL** — Business stops if this fails:
- Revenue data collection (Gumroad API pulls)
- Session refresh jobs (AgentReach)
- Core automation pipelines

**HIGH** — Significant impact within 24 hours:
- Content analytics collection
- Scheduled content publishing
- Report generation jobs

**MEDIUM** — Impact within 48-72 hours:
- Non-essential analytics
- Backup operations
- Optimization jobs

**LOW** — Can tolerate multi-day failure:
- Archival tasks
- Non-urgent data cleanup
- Experimental automations

### Monitoring Rules by Criticality

| Criticality | Check Frequency | Alert on First Failure | Max Consecutive Failures Before Escalation |
|------------|----------------|----------------------|------------------------------------------|
| CRITICAL | Every run | Yes (ALERT) | 1 |
| HIGH | Every run | No (log), Yes on 2nd consecutive | 2 |
| MEDIUM | Daily summary | No | 3 |
| LOW | Weekly summary | No | 5 |

### Cron Health Dashboard Metrics
Compute daily:
- **Overall success rate**: (Successful runs / Total scheduled runs) × 100
- **Critical job success rate**: Same, filtered to CRITICAL jobs only
- **Average failure recovery time**: Time from first failure to successful re-run
- **Job drift**: How far actual run times deviate from scheduled times (>10 min drift = WATCH)
- **Silent failure count**: Jobs that exited 0 but produced invalid output

---

## 3. AgentReach Session Management

### Session Lifecycle Tracking
For every active AgentReach session:

```
SESSION RECORD:
  Session ID: [identifier]
  Service: [what service this authenticates to]
  Created: [timestamp]
  Expires: [timestamp]
  Time Remaining: [computed — hours and minutes]
  Status: [ACTIVE / EXPIRING_SOON / EXPIRED / REFRESH_FAILED]
  Last Refresh Attempt: [timestamp]
  Last Refresh Result: [success / failure / error details]
  Refresh Schedule: [how often automated refresh runs]
  Dependent Jobs: [list of cron jobs / automations that need this session]
  Fallback Action: [what to do if session dies — manual login? backup auth?]
```

### Expiry Warning Cascade
Generate warnings at these intervals:
```
72 hours before expiry → INFO: "Session [X] expires in 3 days. Refresh scheduled."
48 hours before expiry → WATCH: "Session [X] expires in 2 days. Verify refresh is working."
24 hours before expiry → ALERT: "Session [X] expires in 24 hours. Confirm refresh or manual intervention."
12 hours before expiry → URGENT: "Session [X] expires in 12 hours. Immediate action recommended."
Expired → CRITICAL: "Session [X] has expired. [N] dependent systems affected."
```

### Refresh Failure Protocol
When a session refresh fails:
1. Immediately retry once
2. If retry fails: ALERT with error details
3. Compute impact: List all dependent systems that will break when session expires
4. Provide specific instructions for manual remediation
5. Monitor every 2 hours until resolved

### Session Health Score
```
Session Health = (
  (Active sessions / Total required sessions) × 0.50 +
  (Average remaining time / Expected session duration) × 0.30 +
  (Refresh success rate, trailing 30 days) × 0.20
) × 100
```
Scale: 0-100. Below 70 = WATCH. Below 50 = ALERT.

---

## 4. API Integration Health

### API Health Metrics (per endpoint)
For every external API the system calls:

```
API HEALTH RECORD:
  Service: [Gumroad / Pinterest / Twitter/X / Reddit / etc.]
  Endpoint: [specific API endpoint]
  Calls Today: [count]
  Success Rate (24h): [%]
  Avg Response Time (24h): [ms]
  p95 Response Time (24h): [ms]
  p99 Response Time (24h): [ms]
  Error Rate (24h): [%]
  Rate Limit Usage: [current / max, % used]
  Last Error: [timestamp, error type, details]
  Status: [HEALTHY / DEGRADED / DOWN]
```

### API Status Classification
```
HEALTHY: Success rate >99%, p95 latency <2s, rate limit usage <60%
DEGRADED: Success rate 95-99%, OR p95 latency 2-5s, OR rate limit usage 60-80%
DOWN: Success rate <95%, OR p95 latency >5s, OR rate limit usage >80%, OR consecutive 5xx errors
```

### Rate Limit Management
For each API with rate limits:
- Track current usage vs limit in real-time
- Implement backoff at 70% usage (slow down, don't stop)
- Implement pause at 85% usage (queue requests, wait for limit reset)
- ALERT at 90% usage (may need to reduce polling frequency or optimize calls)
- Calculate requests-per-minute budget and pace calls accordingly

### API Dependency Chain
Map which systems depend on which APIs:
```
Gumroad API → Revenue data collection → Daily revenue card → Weekly signal memo
Pinterest API → Content analytics → Content performance report → Weekly signal memo
Twitter/X API → Engagement data → Content performance report → Weekly signal memo
AgentReach → Session tokens → All automated operations
```

If an API goes down, immediately compute the blast radius: what downstream outputs will be affected?

---

## 5. Silent Failure Detection

Silent failures are the MOST DANGEROUS type of system failure. The job appears to succeed
but produces wrong, incomplete, or corrupt output. Standard monitoring (exit codes, uptime)
misses them entirely.

### Detection Methods

**Output Existence Check**: Did the job produce ANY output?
```
Expected: Output file exists, has >0 bytes, was modified at expected time
Failure: No output, empty file, or stale timestamp
```

**Output Size Check**: Is the output the right size?
```
Expected: Output size within 50-200% of trailing 7-day average
Failure: Output size <10% of average (probably empty or truncated)
         Output size >500% of average (probably duplicated or corrupt)
```

**Output Content Validation**: Does the output contain valid data?
```
Expected: Valid JSON/CSV/format, expected fields present, values in valid ranges
Failure: Parse errors, missing fields, impossible values (negative counts, future dates)
```

**Output Freshness Check**: Is the data in the output actually new?
```
Expected: Most recent timestamp in output is from the expected period
Failure: Most recent timestamp is older than expected (job ran but pulled stale data)
```

**Downstream Impact Check**: Are downstream consumers working?
```
Expected: Systems that consume this output are functioning normally
Failure: Downstream errors or missing data (even if this job "succeeded")
```

### Silent Failure Alert Protocol
When a silent failure is detected:
1. Classify severity: Is the affected data CRITICAL, HIGH, MEDIUM, or LOW?
2. Immediately ALERT for CRITICAL and HIGH
3. Identify the most recent KNOWN GOOD output
4. Mark all data between last good and detection as SUSPECT
5. Determine if downstream reports need correction
6. Trigger re-run of the failed job if possible
7. Add to the "Data Quality Issues" section of the next report

---

## 6. Dependency Health Mapping

### The Dependency Graph
Build and maintain a directed graph of system dependencies:
```
Nodes: Every job, session, API, and output
Edges: "depends on" relationships

Example:
  [Weekly Signal Memo] → depends on → [Revenue Data] → depends on → [Gumroad API] + [Gumroad API Key]
  [Weekly Signal Memo] → depends on → [Content Data] → depends on → [Pinterest API] + [Twitter/X API]
  [All Automated Ops] → depends on → [AgentReach Sessions]
  [Revenue Data] → depends on → [Daily Cron Job: gumroad_pull]
```

### Blast Radius Computation
When any node in the dependency graph fails, automatically compute:
- All downstream nodes affected (direct and transitive)
- Estimated time to impact (how long before downstream effects are visible)
- Criticality of affected downstream nodes
- Available fallbacks or manual workarounds

### Single Points of Failure
Identify any node in the graph where:
- A single failure cascades to multiple CRITICAL downstream systems
- There is no fallback or redundancy
- Manual intervention is the only recovery path

Flag these as architectural risks in monthly deep-dives.

---

## 7. System Health Scoring

### Overall System Health Score
```
System Health Score = (
  Cron Job Success Rate × 0.30 +
  Session Health Score × 0.25 +
  API Health Score × 0.25 +
  Silent Failure Absence Score × 0.20
) × 100
```

Where:
- Cron Job Success Rate: (Successful / Total scheduled) for all CRITICAL and HIGH jobs
- Session Health Score: From Section 3
- API Health Score: Average of all API status scores (HEALTHY=100, DEGRADED=50, DOWN=0)
- Silent Failure Absence Score: 100 - (Silent failures detected × 10), min 0

### Health Score Interpretation
- **90-100**: All green. Systems humming.
- **75-89**: Minor issues. Likely a DEGRADED API or a non-critical job failing.
- **60-74**: Attention needed. Multiple issues or a CRITICAL component degraded.
- **40-59**: Warning. Significant system problems. Manual intervention likely needed.
- **Below 40**: Critical. Major outages or cascading failures. Immediate action required.

---

## 8. Incident Classification

### Severity Levels
```
SEV-1 (CRITICAL): Revenue-impacting outage, data loss, or security incident
  Response: Immediate alert to all stakeholders. Drop everything.
  Example: Gumroad API key expired, all revenue tracking is down

SEV-2 (HIGH): Significant functionality loss, but workaround exists
  Response: Alert within 1 hour. Begin remediation.
  Example: Pinterest API returning errors, can use dashboard export temporarily

SEV-3 (MEDIUM): Partial functionality loss, limited impact
  Response: Include in daily check. Fix within 24 hours.
  Example: One non-critical cron job failing but not affecting reports yet

SEV-4 (LOW): Minor issue, no immediate impact
  Response: Log and include in weekly review.
  Example: API latency slightly elevated but within tolerance
```

### Incident Report Format
```
INCIDENT REPORT
Severity: [SEV-1/2/3/4]
Detected: [timestamp]
System: [affected system]
Impact: [what functionality is lost or degraded]
Blast Radius: [downstream effects]
Root Cause: [known or under investigation]
Status: [Investigating / Identified / Mitigating / Resolved]
ETA to Resolution: [estimate]
Workaround: [available? describe]
Action Items: [numbered list of next steps]
```

---

## 9. Health Report Templates

### Daily System Health Check (automated)
```
## System Health — [date]
**Overall Score**: [score]/100 — [GREEN/YELLOW/RED]

### Cron Jobs: [X/Y successful] ([%])
[Any failures listed with job name, time, and error summary]

### Sessions: [X/Y active] ([hours to nearest expiry])
[Any expiry warnings]

### APIs: [X/Y healthy]
[Any degraded or down APIs with status]

### Silent Failures: [count detected]
[Details if any]

### Action Required: [Yes/No]
[Specific actions if yes]
```

### Weekly System Health Section (for Signal Memo)
```
## System Health Signal

**Health Score**: [score]/100 — [trend vs last week]
**Cron Reliability (7-day)**: [%] — [trend]
**Session Status**: [all clear / {count} expiring within 72h]
**API Health**: [all healthy / {count} degraded]

### Issues this week:
- [Issue 1 — severity, impact, resolution status]
- [Issue 2]

### Upcoming risks:
- [Any sessions expiring, scheduled maintenance, known issues]
```
