# Bottleneck Detection

How to identify where work gets stuck, which agents are slow, and what's consistently late or incomplete.

---

## Table of Contents
1. Bottleneck Theory & Principles
2. Workflow Velocity Analysis
3. Agent Performance Scoring
4. Queue & Backlog Analysis
5. Dependency Chain Analysis
6. Handoff Delay Detection
7. Resource Contention
8. Bottleneck Classification & Prioritization
9. Bottleneck Report Templates

---

## 1. Bottleneck Theory & Principles

### The Theory of Constraints (Applied)
Every system has exactly one constraint that limits its throughput. Improving anything that is NOT the
constraint is waste. The Analyst's job is to find THE constraint — not just "problems."

### Bottleneck vs Slowdown
- **Bottleneck**: A step where work ACCUMULATES (queue builds). Upstream work arrives faster than this step can process.
- **Slowdown**: A step that takes longer than ideal but isn't accumulating work. Improving it helps but isn't urgent.

The test: Is the queue GROWING at this step? If yes → bottleneck. If no → slowdown.

### Finding the Bottleneck
Look for these signals:
1. **Largest queue**: Where is the most work waiting?
2. **Longest wait time**: Where does work sit idle the longest?
3. **Highest utilization**: Which step is running at/near 100% capacity?
4. **Downstream starvation**: Which steps are idle because they're waiting on input?

The bottleneck is usually at the intersection of high utilization AND growing queue AND downstream starvation.

---

## 2. Workflow Velocity Analysis

### Measuring Workflow Velocity
For each defined workflow in the system:

```
WORKFLOW: [name]
STAGES: [stage1] → [stage2] → [stage3] → ... → [completion]

Per stage, measure:
  - Throughput: Tasks completed per time unit
  - Cycle time: Time from stage entry to stage exit
  - Wait time: Time task sits idle before processing starts
  - Processing time: Actual work time (cycle time - wait time)
  - Queue depth: Tasks waiting to enter this stage

Workflow-level metrics:
  - End-to-end cycle time: Time from workflow start to completion
  - Throughput: Completed workflows per time unit
  - WIP (Work in Progress): Tasks currently in-flight
  - Flow efficiency: Processing time / Total cycle time × 100
```

### Velocity Trend Analysis
Track weekly:
- Is end-to-end cycle time increasing? (System is getting slower)
- Is throughput decreasing? (System is producing less)
- Is WIP increasing while throughput is flat? (Work is piling up somewhere)
- Which stage's queue is growing fastest? (That's your bottleneck)

### Little's Law Application
```
WIP = Throughput × Cycle Time
```
This relationship ALWAYS holds in stable systems. Use it to:
- Predict: If throughput drops by X, WIP will increase by X (assuming cycle time stable)
- Diagnose: If WIP is higher than predicted, there's hidden rework or blocked items
- Target: To reduce cycle time, either reduce WIP or increase throughput (usually reducing WIP is easier)

---

## 3. Agent Performance Scoring

### Per-Agent Metrics
For every agent in the system:

```
AGENT: [name/identifier]
ROLE: [what this agent does]

PERFORMANCE METRICS (trailing 7 days):
  Tasks assigned: [count]
  Tasks completed: [count]
  Completion rate: [%]
  Average cycle time: [duration]
  On-time completion rate: [%] (completed before deadline or SLA)
  Error/retry rate: [%] (tasks requiring redo)
  Quality score: [if measurable — output quality rating]
  
TREND:
  Cycle time trend (4-week): [Improving / Stable / Degrading]
  Completion rate trend (4-week): [Improving / Stable / Degrading]
  Error rate trend (4-week): [Improving / Stable / Degrading]

RELATIVE PERFORMANCE:
  Cycle time vs team median: [X% faster/slower]
  Completion rate vs team median: [+/- percentage points]
  Error rate vs team median: [+/- percentage points]

STATUS: [Performing / Watch / Underperforming / Blocked]
```

### Agent Performance Classification
```
PERFORMING: Completion rate >90%, cycle time ≤ 110% of team median, error rate < team median
WATCH: Completion rate 80-90% OR cycle time 110-150% of median OR error rate 1-2x median
UNDERPERFORMING: Completion rate <80% OR cycle time >150% of median OR error rate >2x median
BLOCKED: Agent has pending tasks but cannot progress due to external dependency
```

### Identifying the Slowest Agent
Rank agents by:
1. Average cycle time (longest = potential bottleneck if they're in the critical path)
2. Queue depth (most tasks waiting = highest contention)
3. Error/retry rate (high error rate effectively reduces throughput)

Important: An agent being "slow" only matters if they're on the critical path. A slow agent doing
non-critical work is not a bottleneck.

---

## 4. Queue & Backlog Analysis

### Queue Health Metrics
For every queue in the system (task queues, job queues, approval queues):

```
QUEUE: [name]
CURRENT DEPTH: [items]
  vs 7-day average: [+/- items] ([+/-%])
  vs 30-day average: [+/- items] ([+/-%])
OLDEST ITEM: [age in hours/days]
AVERAGE WAIT TIME: [duration]
INFLOW RATE: [items per hour/day entering the queue]
DRAIN RATE: [items per hour/day leaving the queue]
NET FLOW: [inflow - drain — positive = growing, negative = shrinking]
```

### Queue Growth Detection
A growing queue is the PRIMARY signal of a bottleneck.

```
HEALTHY: Net flow ≤ 0 (queue is stable or shrinking)
GROWING: Net flow > 0 for 3+ consecutive measurement periods
CRITICAL: Queue depth > 3x historical average AND still growing
```

### Backlog Age Analysis
Classify queued items by age:
```
FRESH: < 1 hour — normal queue time
WAITING: 1-24 hours — acceptable for most workflows
STALE: 1-7 days — something may be stuck
STUCK: > 7 days — definitely blocked, needs investigation
ABANDONED: > 30 days — likely forgotten, should be cleaned up or escalated
```

Flag any STUCK or ABANDONED items in reports. These often represent forgotten work or systematic blockers.

---

## 5. Dependency Chain Analysis

### Mapping Dependencies
Every task that's blocked is blocked by something. Map the chain:

```
BLOCKED TASK → waiting on → [Dependency]
  └── [Dependency] → waiting on → [Upstream Dependency]
      └── [Upstream Dependency] → waiting on → [Root Dependency]
```

### Finding Root Blockers
The root blocker is the FIRST unresolved dependency in the chain. Everything downstream is just a symptom.

```
Algorithm:
1. For each blocked task, trace the dependency chain backward
2. Find the earliest (root) unresolved dependency
3. Count how many blocked tasks trace back to each root dependency
4. Rank root dependencies by "tasks blocked" — highest = biggest bottleneck
```

### Dependency Types
- **Sequential**: Task B cannot start until Task A completes
- **Resource**: Task B needs a resource (API key, session, tool) that's unavailable
- **Approval**: Task B needs human approval before proceeding
- **External**: Task B depends on an external system or third party
- **Data**: Task B needs data that hasn't been collected or processed yet

Each type requires a different resolution strategy.

---

## 6. Handoff Delay Detection

### What is a Handoff?
A handoff occurs when work passes from one agent/system to another. Every handoff introduces potential delay.

### Measuring Handoff Delay
```
For each handoff point:
  Handoff Delay = Time from upstream completion to downstream start
  
  CLEAN HANDOFF: Delay < 1 hour (for automated) or < 4 hours (for human-involving)
  SLOW HANDOFF: Delay 4-24 hours
  BLOCKED HANDOFF: Delay > 24 hours
```

### Common Causes of Handoff Delay
- **Notification failure**: Downstream agent doesn't know the upstream is done
- **Format mismatch**: Upstream output isn't in the format downstream needs
- **Capacity mismatch**: Downstream agent is busy with other work
- **Timezone/availability**: Agent isn't available when handoff arrives
- **Unclear ownership**: Nobody knows they're supposed to pick up the work

### Reducing Handoff Delay
For each identified slow or blocked handoff, recommend:
1. **Automate the notification**: Ensure downstream is immediately aware
2. **Standardize the format**: Define clear input/output contracts
3. **Buffer capacity**: Ensure downstream has capacity to absorb incoming work
4. **Clarify ownership**: Every handoff has a named receiver
5. **Reduce handoffs**: Can two stages be combined into one?

---

## 7. Resource Contention

### What is Resource Contention?
Multiple tasks competing for the same limited resource (API quota, human attention, compute capacity).

### Detection
```
Resource Contention = (Demand for resource / Available capacity) × 100

GREEN: <70% utilization
YELLOW: 70-85% utilization (approaching contention)
RED: >85% utilization (active contention, likely causing delays)
OVERLOADED: >100% utilization (demand exceeds capacity, queue is definitely growing)
```

### Common Contention Points
- **API rate limits**: Multiple jobs hitting the same API simultaneously
- **Agent bandwidth**: One agent assigned too many concurrent tasks
- **Session tokens**: Multiple processes sharing a limited number of sessions
- **Compute resources**: CPU, memory, or network bandwidth constraints

### Resolution Strategies
1. **Stagger**: Space out competing demands (cron jobs at different times)
2. **Prioritize**: Critical tasks get the resource first
3. **Pool**: Add more capacity to the resource
4. **Deduplicate**: Are multiple tasks requesting the same thing? Cache and share.
5. **Decouple**: Reduce dependencies on the contested resource

---

## 8. Bottleneck Classification & Prioritization

### Classification Matrix
```
| Impact | Frequency | Type | Priority |
|--------|-----------|------|----------|
| Blocks >3 downstream tasks | Daily/ongoing | Systemic | P0 — Fix immediately |
| Blocks 1-3 downstream tasks | Daily/ongoing | Recurring | P1 — Fix this week |
| Blocks >3 downstream tasks | Occasional | Intermittent | P1 — Fix this week |
| Blocks 1-3 downstream tasks | Occasional | Intermittent | P2 — Fix this month |
| Slows but doesn't block | Any frequency | Optimization | P3 — Backlog |
```

### The Bottleneck Brief
For each identified bottleneck, produce:
```
BOTTLENECK BRIEF
Location: [which stage, queue, agent, or system]
Type: [queue buildup / slow processing / dependency block / contention / handoff delay]
Impact: [what downstream effects — tasks blocked, revenue delayed, reports incomplete]
Duration: [how long has this been a bottleneck]
Root Cause: [identified or hypothesized]
Priority: [P0/P1/P2/P3]
Recommended Fix: [specific action]
Expected Improvement: [quantified if possible — e.g., "reduce cycle time by ~30%"]
Owner: [who should fix this]
```

---

## 9. Bottleneck Report Templates

### Weekly Bottleneck Section (for Signal Memo)
```
## Operational Velocity Signal

**End-to-End Cycle Time (avg, this week)**: [duration] | vs last week: [+/- change]
**Throughput (tasks completed)**: [count] | vs last week: [+/- change]
**Active Bottlenecks**: [count] (P0: [N], P1: [N], P2: [N])

### Current Bottlenecks:
1. [Location]: [brief description] — [impact] — [status: investigating/fixing/monitoring]
2. [Location]: [brief description] — [impact] — [status]

### Agent Performance:
- Fastest: [agent name] — [avg cycle time]
- Needs attention: [agent name] — [issue: slow/error-prone/blocked]

### Resolved This Week:
- [Bottleneck that was fixed] — [what was done] — [measured improvement]
```
