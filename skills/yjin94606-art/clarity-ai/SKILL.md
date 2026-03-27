---
name: clarity-ai
description: AI-Powered Intent Parser - Transform messy input into crystal-clear instructions. Converts verbose Chinese/English input into structured intent. Supports 7 intent types + 20+ programming languages. Privacy-first, millisecond response.
version: 2.1.0
author: Boss
---

# Clarity AI

**Transform messy input into crystal-clear instructions**

---

## What It Does

| Messy Input | Clean Output |
|-------------|--------------|
| "Hi, about Python for loops, why is it running so slow?" | **Intent:** Performance<br>**Language:** Python<br>**Goal:** Analyze slow loop |

---

## Features

| Feature | Description |
|---------|-------------|
| 🎯 **7 Intent Types** | Debug, Performance, Create, Explain, Modify, Review, Learn |
| ⚡ **Millisecond** | Local rule engine, no waiting |
| 🔒 **Privacy** | 100% local processing |
| 🌏 **Bilingual** | Chinese & English |

---

## Supported Intents

| Intent | Keywords |
|--------|----------|
| Code Debug | debug, error, bug, issue |
| Performance | slow, performance, optimize |
| Code Creation | write, create, generate |
| Concept Explain | what is, explain, principle |
| Code Modify | modify, refactor |
| Code Review | review, check |
| Learning | teach, learn |

---

## Usage

**Activate:** "开启精准模式" or "Enable precision mode"

**Input:** "Can you help me check this Python code?"

**Output:**
```markdown
## 🎯 Precision Instruction

**📌 Intent:** Code Debug
**💻 Language:** Python

**🎯 Goal:** Find and fix code issues
```

**Deactivate:** "关闭精准模式" or "Disable precision mode"

---

## Installation

```bash
clawhub install clarity-ai
```

---

## Optional: Ollama Enhancement

```bash
brew install ollama
ollama pull qwen:0.5b
brew services start ollama
```

---

## Technical Details

- **Speed:** Millisecond response (rule engine)
- **Privacy:** 100% local
- **Languages:** 20+ programming languages
- **Intelligence:** 7 intent types

---

## Author

**Boss** - Built for better AI communication
