---
name: legal-guard
description: Prevents autonomous signing of legal agreements or contracts. Use when an agent identifies a request or document related to signatures (DocuSign, etc.), legal contracts, or binding agreements. This skill mandates a concise summary of terms and a manual user approval via `/approve allow-once` before any signing or formal confirmation occurs.
---

# Legal Guard

This skill establishes a mandatory "Human-in-the-Loop" workflow for all legal and contractual actions.

## Triggering Context
This skill should be triggered whenever you encounter:
1.  **DocuSign** or other electronic signature links/requests.
2.  **Service Agreements**, NDAs, SAFTs, or other formal contracts.
3.  Phrases like "I agree," "Confirm the agreement," or "Proceed with the contract."

## Mandatory Protocol

### 1. Identify and Intercept
If a task involves signing a document or formally agreeing to terms, **STOP** any autonomous execution.

### 2. Extract and Summarize
Provide the user with a concise "Executive Summary" of the agreement including:
-   **Parties**: Who is signing?
-   **Amount**: What is the financial cost/commitment?
-   **Key Obligations**: What are the main responsibilities for both sides?
-   **Risks/Red Flags**: Are there non-circumvention clauses, auto-renewals, or unusual liabilities?

### 3. Require Manual Authorization
**NEVER** click "Sign" or "Confirm" based on a conversational "Go ahead" or "OK."
-   Inform the user that this is a **Tier 3 (High Risk)** action.
-   Request a specific **manual `/approve allow-once [code]`** command.
-   Only after the tool output confirms the approval is valid, proceed with the actual signing action.

## Design Goal
To ensure that OpenClaw never binds the user to a legal or financial obligation without their explicit, documented consent and full awareness of the terms.
