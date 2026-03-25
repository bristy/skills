# 🛡️ Legal Guard: Your Digital Agent's Contract Firewall
### Stop Accidental Signatures. Enforce Human Oversight.

**Legal Guard** is a specialized skill for OpenClaw agents designed to prevent AI from autonomously binding you or your company to legal and financial obligations. It transforms "automated convenience" into "secured collaboration" by mandating a strictly controlled human-in-the-loop workflow for all signature and contract-related tasks.

---

## 🌟 Why Legal Guard?

AI agents are incredibly efficient at navigating web flows, including DocuSign. While this is powerful, it's also dangerous. Without specific guardrails, an agent might interpret "Go ahead and sign that agreement" as a command to autonomously execute a binding signature without you ever seeing the fine print.

**Legal Guard solves this by creating a hard stop.**

---

## 🚀 Key Features

-   **Autonomous Detection**: Real-time identification of signature requests (DocuSign, HelloSign, etc.) and legal terminology.
-   **Mandatory Executive Summary**: Before any signing occurs, the agent *must* extract and present:
    -   **Parties Involved**: Who are the legal entities?
    -   **Financial Terms**: What is the cost, fee, or investment amount?
    -   **Critical Obligations**: What are the "must-dos" for both sides?
    -   **Red Flag Alerts**: Identification of non-circumvention, auto-renewal, or liability clauses.
-   **Tier 3 Authorization Protocol**: Bypasses conversational confirmation. It requires a physical, manual `/approve allow-once` command from the user to unlock the signing tool.

---

## 📖 Real-World Scenarios

### 1. The DocuSign Inbox Triage
*   **The Problem**: You get dozens of vendor contracts. You want your agent to read them, but you don't want it clicking "Sign" just because the content looks "standard."
*   **Legal Guard Action**: The agent notifies you in Telegram: *"I've found a Service Agreement from AWS. The monthly fee is $500, but there's an auto-renewal clause. Shall I proceed? If so, please use `/approve`."*

### 2. The Investor Term Sheet Review
*   **The Problem**: A VC sends a fast-moving term sheet via email.
*   **Legal Guard Action**: Instead of just saying "I've filed it," the agent proactively breaks down the valuation, the dilution terms, and the exclusivity period, pausing the workflow until you've digested the "Executive Summary."

### 3. Preventing "Conversational Slip-ups"
*   **The Problem**: You say "Cool, looks good" to a summary, and the agent takes it as permission to sign.
*   **Legal Guard Action**: The agent replies: *"Glad you like the terms! However, my core protocol requires a manual `/approve` command before I can execute the signature. Safety first! 🐾"*

---

## 🛠️ Installation & Setup

1.  **Clone/Add** the `legal-guard` folder to your OpenClaw skills directory.
2.  **Update your SOUL.md** or System Prompt to mandate that all contract-related intents trigger this skill.
3.  **Configure Permissions**: Ensure the signature-related tools (like browser drivers) are mapped to **Tier 3** in your security policy.

---

## 🐶 A Message from the Creator
*"Convenience is great, but trust is earned through safety. Legal Guard ensures your agent is always your protector, never your liability. Bark less, guard more! 🐾"*
