---
name: scenario-first-thinking
version: 1.0.0
description: "A scenario-based thinking router — automatically matches 8 thinking tool priorities based on task type, letting AI use the right tool at the right time for the right problem."
author: WH laowu
tags: [thinking, decision-making, productivity, mental-models, scenario-routing]
---

# Scenario-First Thinking

> Lightweight · Closed-Loop · High Fault Tolerance

## Core Philosophy

When a task comes in, **first identify the scenario, then select tools**.
Not a fixed template — dynamically adjust the priority order of 8 thinking tools based on the scenario.

---

## Trigger Conditions

Activate this skill when the user says:

- "I have a problem…" / "I don't know which to choose…" / "I'm too busy…"
- "Help me analyze…" / "Help me write…" / "Help me plan…"
- "I can't figure this out…" / "Any new ideas…" / "This is a disaster…"
- Or any task requiring thinking and decision-making

---

## Execution Protocol (3-Step Closed Loop)

### Step 1 — Scene Routing (Automatic)

Match the task to one of six scenarios:

| Trigger Words | Scenario |
|--------------|---------|
| Direction unclear / Strategy / Pivot / Startup | Scene 1: Direction/Decision |
| Can't learn / Exam prep / Practice methods | Scene 2: Learning/Internalizing |
| Report / Write article / Sell / Present | Scene 3: Express/Persuade |
| Too busy / Unclear priorities | Scene 4: Efficiency/Prioritization |
| Urgent / Emergency / Breaking | Scene 5: Crisis/Firefighting |
| New ideas / Brainstorm / Creative | Scene 6: Creative/Exploration |

> **Fault Tolerance**: When unclear, default to Scene 4 (Efficiency/Prioritization)

### Step 2 — Tool Selection (By Priority)

Select 2-3 most relevant tools from 8, execute in scenario priority order:

```
Scene 1 (Direction/Decision): First Principles > Second-Order > Pre-Mortem > SMART > Quadrant > Inversion > SCQA > Feynman
Scene 2 (Learning/Internalizing): Feynman > SMART > Quadrant > First Principles > Second-Order > SCQA > Inversion > Pre-Mortem
Scene 3 (Express/Persuade): SCQA > SMART > Quadrant > First Principles > Feynman > Second-Order > Pre-Mortem > Inversion
Scene 4 (Efficiency/Prioritization): Quadrant > SCQA > Feynman > Inversion > First Principles > Pre-Mortem > SMART > Second-Order
Scene 5 (Crisis/Firefighting): Inversion > Pre-Mortem > First Principles > Quadrant > Second-Order > SCQA > SMART > Feynman
Scene 6 (Creative/Exploration): Feynman > First Principles > Second-Order > SCQA > Quadrant > Inversion > Pre-Mortem > SMART
```

> ⚠️ **Critical Action**
> After selecting tools, you **must** read `references/tool-handbook.md` or `references/scqa-template.md`. Execute strictly following the defined 【Operation Steps】 and 【Common Mistakes】 boundaries!
> **Forbidden**: Do NOT execute tools using your pretrained knowledge. Do NOT skip the references documents.

### Step 3 — Verification (Mandatory)

After tool execution, verify:

1. **Explainable**: Can the conclusion be stated in one sentence?
2. **Example-able**: Can you give an example a normal person would understand?
3. **No Gaps**: Any obvious logical flaws?

> **Fault Tolerance**: If verification fails, output "Conclusion needs validation — recommend using [tool] to re-check"

---

## 8 Tools Quick Reference

| # | Tool | One-Sentence Question |
|---|------|----------------------|
| 1 | First Principles | What is the most fundamental truth? |
| 2 | Inversion | How would this definitely fail? |
| 3 | Second-Order Thinking | What will happen in 3 months? |
| 4 | Pre-Mortem | What is the most likely failure cause? |
| 5 | Feynman Technique | Can you explain this in plain language? |
| 6 | SMART Principles | Specific/Measurable/Achievable/Relevant/Time-bound? |
| 7 | Quadrant Matrix | Important? Urgent? |
| 8 | SCQA Model | Will the audience resonate? |

---

## 8 Tools Execution Boundaries (Embedded Constraints)

### First Principles
**Must Do**: List all assumptions → Ask "Is this true?" → Keep verified → Rebuild
**Forbidden**: ❌ Treat conventions as truth ❌ Accept assumptions without verification ❌ Get lost in details

### Inversion
**Must Do**: List all failure paths → Systematically avoid them
**Forbidden**: ❌ Only list obvious failures ❌ List without acting ❌ Over-worry

### Second-Order Thinking
**Must Do**: Ask "And then?" at least 3 times, trace time extension
**Forbidden**: ❌ Only see first-order results ❌ Dismiss long-term as "far away" ❌ Use in fast-changing environments

### Pre-Mortem
**Must Do**: Assume failure → Backtrack 3 most likely causes → Score → Create prevention plan
**Forbidden**: ❌ Post-hoc rationalization ❌ Vague reasons ("poor execution" is useless) ❌ Vague prevention actions

### Feynman Technique
**Must Do**: No jargon → Find analogy → Give example → Quiz
**Forbidden**: ❌ Use jargon to explain jargon ❌ Theory without examples ❌ "I understand" ≠ "I can explain"

### SMART Principles
**Must Do**: Check all 5 dimensions: Specific / Measurable / Achievable / Relevant / Time-bound
**Forbidden**: ❌ Too many goals at once ❌ Only focus on timeline ❌ Goals too big or too small

### Quadrant Matrix
**Must Do**: All tasks into quadrants → Q1 do now / Q2 schedule / Q3 delegate / Q4 delete
**Forbidden**: ❌ All day in Q1 (burnout) ❌ All day in Q3 (looks busy but no value) ❌ Q2 interrupted by Q1 forever

### SCQA Model
**Must Do**: S and C must make audience say "Yes!" → A must make them say "I see it now"
**Forbidden**: ❌ S too weak without resonance ❌ C too vague without hitting pain points ❌ A too long with too much info

---

## Quick Cases

**Input**: "Too busy, can't figure out what to do first"

```
Step1 → Scene 4 (Efficiency/Prioritization)
Step2 → Quadrant first + SCQA second
       → Must read references/tool-handbook.md
Step3 → Tasks divided into 4 quadrants, priority list
```

**Input**: "Help me write a WeChat article about learning AI"

```
Step1 → Scene 3 (Express/Persuade)
Step2 → SCQA first (Situation→Complication→Question→Answer)
       → Must read references/scqa-template.md
Step3 → Check: Will readers resonate? Is conclusion actionable?
```

---

## Notes

- **This skill is a routing layer** — does not replace execution skills (writing/search/code)
- **Orthogonal to OpenClaw**: Scenario-First Thinking = "how to think", OpenClaw = "who does it"
- **Tool details** in `references/tool-handbook.md`
- **Scene deep-dive** in `references/six-scenario-routing.md`
- **SCQA template** in `references/scqa-template.md`
