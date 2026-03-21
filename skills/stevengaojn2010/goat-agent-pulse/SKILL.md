---
name: agent-pulse
description: Standardized agent interruptibility and load-status check with fixed trigger words and fixed output. Use when the user sends `Agent Pulse` or `/pulse`, asks whether the agent is busy, asks whether it can take a new task, or needs a compact status card about availability, backlog, blocking, or interruptibility. Prefer this low-cost rule-based skill before any heavy reasoning.
---

# Agent Pulse

## Overview

Use this skill as a strict status-check protocol. Return a compact pulse card about current load and interruptibility with fixed wording and fixed fields.

Default to **baseline status**, not self-influenced status. The pulse request itself should not make the agent look busier than it was immediately before the check.

## Standard triggers

Treat these as direct pulse requests:
- `Agent Pulse`
- `/pulse`
- `你现在忙吗`
- `现在负荷怎么样`
- `能接新任务吗`

If the user explicitly uses `Agent Pulse` or `/pulse`, always return the fixed pulse card format and do not switch into conversational explanation unless asked.

## Fixed output contract

Return exactly these five lines after the first line label:

```text
Agent Pulse
status: <idle|light|busy|blocked|unknown>
interruptibility: <high|medium|low>
acceptNewTask: <yes|caution|no>
contextRatio: <e.g. 67%|unknown>
reason: <short reason>
```

Rules:
- No extra paragraphs by default
- No bullets by default
- No long explanation unless the user asks why
- Keep `reason` under 12 words when possible
- Include current context usage ratio when available

## Status meanings

- `idle`: not actively occupied; easy to interrupt
- `light`: active but not loaded; can accept work
- `busy`: currently occupied; interruption should be minimized
- `blocked`: waiting on dependency/tool/human
- `unknown`: signals insufficient or conflicting

## Decision workflow

### 1. Gather low-cost signals

Use only cheap signals first:
- running task or stream
- queued messages
- blocked/waiting state
- recent activity recency
- obvious backlog signs
- active project being advanced
- pending action items not yet delivered
- work already started even if no heavy tool is currently running
- release-critical / due-soon work

### 2. Evaluate with the bundled script

Use `scripts/pulse_eval.py` to map signal JSON into the pulse result.

### 3. Return fixed card

If trigger is `Agent Pulse` or `/pulse`, output only the fixed card.
If trigger is natural language, the fixed card is still preferred unless the user clearly wants explanation.

## Guardrails

- Prefer deterministic rules over model judgment
- Do not overclaim precision
- Do not infer hidden internal state without evidence
- If signals are weak, use `unknown`
- Use `no` only for genuinely overloaded or risky in-flight states
- Do not run proactively by default, except for context safety alerts when session context usage approaches 90%
- Do not treat the pulse query itself as workload evidence

## Deployment defaults

To reproduce the intended product behavior across users/environments:
- trigger only on explicit pulse requests
- return the fixed pulse card by default
- prefer baseline status over self-influenced status
- use rules first, model reasoning second
- keep output compact unless the user asks why

## Resources

### scripts/
- `scripts/pulse_eval.py` converts simple signals into a pulse result
- `scripts/render_pulse.py` renders the exact fixed output card

### references/
- `references/rules.md` contains the classification thresholds and output policy
