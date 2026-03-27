# Clarity AI

<h1 align="center">
  🎯 AI Intent Parser for Crystal-Clear Instructions
</h1>

<p align="center">
  Transform messy, verbose input into structured, precise instructions that AI understands perfectly.
</p>

---

<p align="center">
  <img src="https://img.shields.io/badge/version-2.1.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/platform-OpenClaw-green?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/privacy-100%25-red?style=flat-square" alt="Privacy">
  <img src="https://img.shields.io/badge/speed-millisecond-yellow?style=flat-square" alt="Speed">
  <img src="https://img.shields.io/badge/intents-7-orange?style=flat-square" alt="Intents">
</p>

---

## ⚡ One-Command Install

```bash
curl -sL https://raw.githubusercontent.com/yjin94606-art/clarity-ai/main/install.sh | bash
```

Or:

```bash
clawhub install clarity-ai
```

---

## What It Does

| Messy Input | Clean Structured Output |
|-------------|------------------------|
| "Hi, about Python for loops, why is it running so slow?" | **Intent:** Performance<br>**Language:** Python<br>**Goal:** Analyze slow loop |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **7 Intent Types** | Debug, Performance, Create, Explain, Modify, Review, Learn |
| ⚡ **Millisecond** | Local rule engine, no waiting |
| 🔒 **Privacy** | 100% local processing |
| 🌏 **Bilingual** | Chinese & English |
| 🔧 **Optional AI** | Ollama enhancement for smarter parsing |

---

## 🎯 Supported Intents

| Intent | Keywords | Example |
|--------|----------|---------|
| Code Debug | debug, error, bug, issue | "Help me debug this code" |
| Performance | slow, performance, optimize | "Why is it running so slow?" |
| Code Creation | write, create, generate | "Write me a login feature" |
| Concept Explain | what is, explain, principle | "What is React Hooks?" |
| Code Modify | modify, refactor, change | "Convert this to TypeScript" |
| Code Review | review, check, analyze | "Review this code for me" |
| Learning | teach, learn, understand | "Explain this concept to me" |

---

## 🚀 Quick Start

### 1. Install

```bash
clawhub install clarity-ai
```

### 2. Activate

```
开启精准模式
```
or
```
Enable precision mode
```

### 3. Use

Just describe your problem naturally!

```
Can you help me check this Python code? It seems to have some issues, thanks!
```

**Output:**
```markdown
## 🎯 Precision Instruction

**📌 Intent:** Code Debug
**💻 Language:** Python

**🎯 Goal:** Find and fix code issues
```

### 4. Deactivate

```
关闭精准模式
```
or
```
Disable precision mode
```

---

## 💻 Supported Languages

**Backend:** JavaScript, TypeScript, Python, Java, C, C++, C#, Go, Rust, PHP, Ruby, Swift, Kotlin

**Frontend:** HTML, CSS, React, Vue, Next.js, Angular

**Other:** SQL, Flutter/Dart, Shell/Bash

---

## 🔧 Advanced: Ollama Enhancement

For smarter semantic understanding:

```bash
# Install Ollama
brew install ollama

# Download model
ollama pull qwen:0.5b

# Start service
brew services start ollama
```

---

## 📊 Engine vs Ollama Enhanced

| Aspect | Rule Engine | Ollama Enhanced |
|--------|-------------|-----------------|
| Speed | ⚡⚡⚡⚡ Millisecond | ⚡⚡⚡ Fast |
| Intelligence | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Dependencies | None | Ollama |
| Privacy | 100% | 100% |

---

## 🎨 Use Cases

| Scenario | Benefit |
|----------|---------|
| 💬 Chat with AI | Get better responses |
| 💻 Code Debug | Describe issues precisely |
| 📚 Learning | Ask clearer questions |
| 🔍 Problem Solving | Faster resolution |

---

## 📝 Example Transformations

### Performance Issue

**Input:**
> Hi, about Python for loops, why is it running so slow, thanks

**Output:**
```markdown
## 🎯 Precision Instruction

**📌 Intent:** Performance Optimization
**💻 Language:** Python
**🎯 Focus:** Loop Structure

**🎯 Goal:** Analyze why for loop is slow
```

### Code Creation

**Input:**
> Could you please help me write a user login function?

**Output:**
```markdown
## 🎯 Precision Instruction

**📌 Intent:** Code Creation
**💻 Language:** (not detected)

**🎯 Goal:** Create user login functionality

**💡 To help you better, please provide:**
- Specific requirements?
- Technology stack?
```

---

## 📄 License

MIT License

---

<p align="center">
  Made with ❤️ for better AI communication
</p>
