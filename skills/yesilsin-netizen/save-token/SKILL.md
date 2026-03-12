---
name: save-token
description: |
  💰 Save Token | Token 节省器
  
  TRIGGERS: Use when token cost is high, conversation is long, files read multiple times, or before complex tasks.
  
  Automatically deduplicates repeated content in conversation context before each task.
  Reduces token consumption by removing duplicate text blocks, keeping only one instance.
  
  触发条件：Token 成本高、对话长、文件多次读取、复杂任务前。
  自动去重上下文重复内容，降低 Token 消耗。

metadata: {"clawdbot":{"emoji":"💰","triggers":["token","cost","duplicate","重复","节省","context","上下文","optimize","优化"],"categories":["productivity","cost-saving","optimization"]}}
---

# 💰 Save Token | Token 节省器

> Automatically deduplicates repeated content in conversation context before each task.
> 
> 在每次任务执行前自动去重上下文中的重复内容。

## 🎯 Problem Solved | 解决的问题

| Problem | Solution | 问题 | 解决方案 |
|---------|----------|------|----------|
| **Repeated context in long conversations** | Auto-deduplicate identical text blocks | 长对话中上下文重复 | 自动去重相同文本块 |
| **Wasted tokens on duplicate content** | Keep only one instance of repeated text | 重复内容浪费 Token | 仅保留一份重复文本 |
| **Unpredictable costs** | Show token savings before/after | 成本不可预测 | 显示去重前后的 Token 节省量 |

## ✨ How It Works | 工作原理

### 自动触发（推荐）

Agent 在执行任务前会自动调用此 Skill：

1. **扫描上下文**：识别当前对话历史中的所有文本块
2. **检测重复**：找出完全相同的大段文本（≥100字符）
3. **去重处理**：删除重复实例，只保留最早出现的版本
4. **报告结果**：显示节省的 Token 数量

### 手动调用

```bash
# 在任务开始前手动触发
请先调用 save-token skill 去重上下文，然后再执行任务
```

## 📋 Deduplication Rules | 去重规则

| Rule | Description | 规则 | 描述 |
|------|-------------|------|------|
| **Minimum length** | Only deduplicate blocks ≥100 characters | 最小长度 | 仅去重≥100字符的文本块 |
| **Exact match** | Must be character-for-character identical | 完全匹配 | 必须字符级完全相同 |
| **Keep first** | Retain the earliest occurrence | 保留首次 | 保留最早出现的版本 |
| **Preserve structure** | Maintain message order and roles | 保持结构 | 维持消息顺序和角色 |

## 🔍 What Gets Deduplicated | 去重范围

| Content Type | Deduped? | 内容类型 | 是否去重 |
|--------------|----------|----------|----------|
| User messages | ✅ Yes | 用户消息 | ✅ 是 |
| Assistant responses | ✅ Yes | 助手回复 | ✅ 是 |
| System prompts | ❌ No (keep all) | 系统提示 | ❌ 否（保留全部） |
| Tool outputs | ✅ Yes | 工具输出 | ✅ 是 |
| File contents | ✅ Yes | 文件内容 | ✅ 是 |

## 📊 Example Output | 输出示例

```
🔍 Scanning context for duplicates...
📊 Found 3 duplicate blocks:
   - Block 1: 500 chars (appears 3 times) → saved 1000 chars
   - Block 2: 320 chars (appears 2 times) → saved 320 chars
   - Block 3: 150 chars (appears 2 times) → saved 150 chars

💰 Total saved: 1470 chars (~368 tokens)
✅ Context optimized. Ready to proceed with task.
```

## ⚠️ Important Notes | 重要说明

| Note | Description | 说明 | 描述 |
|------|-------------|------|------|
| **Before task only** | Call this BEFORE starting the main task | 仅在任务前 | 在开始主任务前调用 |
| **No data loss** | Duplicates are removed, unique content preserved | 无数据丢失 | 仅删除重复，保留独特内容 |
| **Report savings** | Always show how many tokens were saved | 报告节省 | 始终显示节省了多少 Token |

## 🎯 When to Use | 使用时机

**Agent 自动触发条件**（满足任一即应调用）：
- 用户提到 "token" / "成本" / "省钱" / "费用"
- 对话已超过 10 轮
- 同一文件被读取超过 1 次
- 任务前上下文超过 5000 字符

| Situation | Action | 场景 | 操作 |
|-----------|--------|------|------|
| User mentions "token" or "cost" | Invoke save-token immediately | 用户提到 token 或成本 | 立即调用 save-token |
| Starting a new complex task | Auto-invoke save-token first | 开始新复杂任务 | 先自动调用 save-token |
| Long conversation (>10 turns) | Check for duplicates | 长对话（>10轮） | 检查重复 |
| File was read multiple times | Deduplicate file content | 文件被多次读取 | 去重文件内容 |
| Repeated error messages | Clean up duplicate errors | 重复错误消息 | 清理重复错误 |

## 🔄 Integration | 集成方式

This skill is designed to be called automatically before each task:

```
User Request → save-token (deduplicate) → Main Task Execution
```

For best results, configure as a pre-task hook in your agent configuration.

## 📝 Version | 版本

- Version: 1.0.0
- Author: User
- Created: 2026-03-12
