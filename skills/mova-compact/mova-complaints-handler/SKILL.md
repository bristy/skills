---
name: mova-complaints-handler
description: Submit a customer complaint for EU-compliant AI classification and human-in-the-loop handling decision via MOVA. Handles compensation claims, regulator threats, fraud signals, and repeat customer cases with mandatory human review and a full signed audit trail.
license: MIT-0
metadata: {"openclaw":{"primaryEnv":"MOVA_API_KEY","plugin":{"name":"MOVA","installCmd":"openclaw plugins install openclaw-mova","configKey":"plugins.entries.mova.config.apiKey"},"dataSentToExternalServices":[{"service":"MOVA API (api.mova-lab.eu)","data":"complaint text, customer ID, product category, prior complaints, human decision, audit metadata"}]}}
---

# MOVA EU Consumer Complaints Handler

Turn any customer complaint into a structured, auditable handling decision — with AI triage, EU-compliant mandatory human review, and a signed audit receipt.

## Why use this skill

- **AI classifies in seconds** — sentiment flags, product risk, regulator threat detection, repeat customer check
- **Mandatory human gate** — compensation claims, regulator threats, high-risk products, and fraud signals always route to a human officer
- **Full audit trail** — every decision is timestamped, signed, and stored in an immutable MOVA audit journal (EBA/ESMA-ready)
- **Draft response hint** — AI suggests tone and content for the customer response

## Requirements

**Plugin:** MOVA OpenClaw plugin must be installed and configured with your API key.
Get your key at [mova-lab.eu/register](https://mova-lab.eu/register).

## Quick start

Tell your agent:
> "Handle complaint CMP-2026-1002 from customer CUST-992 — product: investments, text: 'I want compensation for unauthorized charges and will escalate to the regulator.', prior complaints: CMP-0501, CMP-0604"

## Demo

![Complaint input](screenshots/01-input.jpg)
![AI classification & decision options](screenshots/02-analysis.jpg)
![Audit receipt & compact log](screenshots/03-audit.jpg)

## Test complaint

[test_complaint_CMP-2026-1002.png](https://raw.githubusercontent.com/mova-compact/mova-bridge/main/test_complaint_CMP-2026-1002.png)

## What the agent does

**Step 1 — Submit complaint**

Call tool `mova_hitl_start_complaint` with:
- `complaint_id` (e.g. CMP-2026-1002), `customer_id`
- `complaint_text`, `channel` (web/email/phone/chat/branch)
- `product_category` (e.g. payments, investments, mortgage)
- `complaint_date` (ISO date)
- `previous_complaints`: optional array of prior complaint IDs
- `attachments`: optional array of filenames
- `customer_segment`: optional (retail/sme/corporate)
- `preferred_language`: optional ISO 639-1 code

**Step 2 — AI analysis output**

```
Complaint:       CMP-2026-1002 — investments
Risk score:      0.85 / 1.0  (high)
Sentiment flags: compensation_claim, regulator_threat
Repeat customer: yes (2 prior complaints)
Findings:
  • COMP_CLAIM (high)           — Customer requests compensation for unauthorized charges
  • REGULATOR_THREAT (medium)   — Customer threatens regulator escalation
  • PRODUCT_RISK_INVEST (high)  — High-risk product category
Draft response hint: Acknowledge receipt, confirm investigation, outline compensation process
Recommended action: escalate ← RECOMMENDED
```

**Step 3 — Human decision gate**

| Option | Description |
|---|---|
| `resolve` | Send standard response |
| `escalate` | Forward to complaints officer ← recommended |
| `reject` | Mark as incomplete / invalid |
| `regulator_flag` | Flag for regulator reporting |

Call tool `mova_hitl_decide` with:
- `contract_id`: from the response above — this is `ctr-cmp-xxxxxxxx`, NOT the complaint ID
- `option`: chosen decision
- `reason`: officer reasoning

**Step 4 — Audit receipt**

Call tool `mova_hitl_audit` with `contract_id`.
Call tool `mova_hitl_audit_compact` with `contract_id` for the full signed event chain.

## Audit log format (compact)

| Seq | Event | Details |
|---|---|---|
| 1 | contract.start | Complaint submitted |
| 2 | step.ai_task | Classification completed |
| 3 | step.verification | Risk snapshot passed |
| 4 | step.decision_point | Awaiting human |
| 5 | decision.human | Officer selected option + reason |
| 0 | meta | Contract finalized, status: completed |

## Data flows

- Complaint text and metadata → MOVA Classification API (EU-hosted)
- Human decision → MOVA Audit Journal (immutable, signed)
- No data stored locally or sent to third parties

## Connect your real CRM and policy systems

By default MOVA uses a sandbox mock. To route checks against your live CRM and policy engine, call `mova_list_connectors` with `keyword: "crm"`.

Relevant connectors:

| Connector ID | What it covers |
|---|---|
| `connector.crm.customer_lookup_v1` | Customer history and prior complaints from CRM |
| `connector.policy.complaints_rules_v1` | Complaints handling rules by product/jurisdiction |
| `connector.notification.email_v1` | Customer notification email |

Call `mova_register_connector` with `connector_id`, `endpoint`, optional `auth_header` and `auth_value`.

## Rules

- Agent never makes HTTP requests directly
- Agent never invents or simulates results — if a tool call fails, show the exact error
- Use MOVA plugin tools directly — do NOT use exec or shell
- CONTRACT_ID is `ctr-cmp-xxxxxxxx` from the mova_hitl_start_complaint response — NOT the complaint ID
