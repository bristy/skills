---
name: "memory-palace"
description: "为 AI Agent 提供持久化记忆管理，支持语义搜索、时间推理、经验积累和智能遗忘。"
allowed-tools: Bash(npx memory-palace:*)
---

# Memory Palace

Agent 的持久化记忆系统。让 AI Agent 能够**记住**用户偏好、对话上下文、项目状态、经验教训，并在需要时**主动检索**。

## 🚀 快速开始

**首次使用：** 无需配置，向量模型未安装时自动降级到文本搜索。

**推荐：安装向量模型以获得更好的搜索体验**
```bash
cd /path/to/memory-palace
bash scripts/install-vector-dependencies.sh
```
向量模型（BGE-small-zh-v1.5）能让语义搜索更准确，比如搜"用户喜欢什么"能找到"我一般用深色模式"这类表述，而不只是关键词匹配。

**立即可用：**
```json
// 记住用户说的话
memory_palace_write: { "content": "用户叫盘古，喜欢简洁的回复", "tags": ["用户", "偏好"], "importance": 0.9 }

// 下次想知道用户叫什么
memory_palace_search: { "query": "用户名字" }

// 记住项目的关键决策
memory_palace_write: { "content": "决定使用 PostgreSQL 作为主数据库", "tags": ["项目决策", "数据库"], "importance": 0.8 }
```

---

## 📋 工具选择指南

### 场景 1：用户告诉了我一些信息 → 写入记忆

```
用户说：「我叫张三」
→ memory_palace_write: { "content": "用户名叫张三", "tags": ["用户信息"], "importance": 0.7 }
```

### 场景 2：需要回忆某件事 → 搜索记忆

```
用户问：「我上次说叫什么名字？」
→ memory_palace_search: { "query": "用户名字" }
```

### 场景 3：完成了一个任务，学到了经验 → 记录经验

```
用户完成了一个 API 设计任务
→ memory_palace_record_experience: { "content": "REST API 设计时用名词而非动词命名端点", "category": "development", "applicability": "设计新的 API 端点时", "source": "task-xxx" }
```

### 场景 4：需要判断某个经验是否有用 → 验证经验

```
之前记录过一条经验，现在在类似场景下
→ memory_palace_verify_experience: { "id": "经验ID", "effective": true }  // 或 false
```

### 场景 5：长记忆需要提炼 → 智能总结

```
用户分享了一段很长的需求描述
→ memory_palace_summarize: { "id": "记忆ID" }
```

### 场景 6：记忆太多太杂，需要整理 → 压缩或提取经验

```
项目进行了很久，积累了很多对话记录
→ memory_palace_extract_experience: { "category": "development" }  // 提取开发经验
→ memory_palace_compress: { "memory_ids": ["id1", "id2", ...] }  // 压缩多条记忆
```

---

## 工具列表

### 基础操作（最常用）

| 工具 | 功能 | 何时用 |
|------|------|--------|
| `memory_palace_write` | 写入记忆 | 用户告诉你任何重要信息时 |
| `memory_palace_get` | 获取记忆 | 知道 ID，要查看完整内容 |
| `memory_palace_update` | 更新记忆 | 发现记忆有误或需要补充 |
| `memory_palace_delete` | 删除记忆 | 记忆过时或错误时 |
| `memory_palace_search` | 搜索记忆 | 需要找某件事但不确定 ID |
| `memory_palace_list` | 列出记忆 | 想看看记忆库里都有什么 |

### 经验管理（进阶）

| 工具 | 功能 | 何时用 |
|------|------|--------|
| `memory_palace_record_experience` | 记录可复用经验 | 完成重要任务、学到教训时 |
| `memory_palace_get_experiences` | 查询经验 | 想参考过去的经验 |
| `memory_palace_verify_experience` | 验证经验有效性 | 在类似场景验证经验是否正确 |
| `memory_palace_get_relevant_experiences` | 查找相关经验 | 当前任务需要过去的经验指导 |
| `memory_palace_experience_stats` | 经验统计 | 查看经验库健康度 |

### LLM 增强（智能处理）

| 工具 | 功能 | 何时用 | 超时 |
|------|------|--------|------|
| `memory_palace_summarize` | 智能总结长记忆 | 记忆内容太长时提炼要点 | 60s |
| `memory_palace_parse_time` | 解析时间表达 | 用户提到"明天"、"下周三"等 | 10s |
| `memory_palace_extract_experience` | 从记忆提取经验 | 从对话中自动抽取可复用经验 | 60s |
| `memory_palace_expand_concepts` | 语义扩展搜索 | 普通搜索找不到时扩展概念 | 15s |
| `memory_palace_compress` | 智能压缩记忆 | 记忆太多需要精简 | 60s |

### 回收站

| 工具 | 功能 |
|------|------|
| `memory_palace_restore` | 从回收站恢复记忆 |
| `memory_palace_link` | 将两条记忆关联起来 |
| `memory_palace_get_related` | 获取某条记忆的所有关联记忆 |

---

## 参数详解

### memory_palace_write

**必填：**
- `content`: 记忆内容（你想记住什么）

**可选：**
- `tags`: 标签数组，方便分类检索，如 `["用户", "偏好", "重要"]`
- `importance`: 重要性 0-1，建议 0.7+ 表示重要记忆
- `location`: 存储位置，默认 "default"，如 "用户"、"项目A"、"日程"
- `type`: 类型
  - `fact` - 事实（默认）
  - `experience` - 经验
  - `lesson` - 教训
  - `preference` - 偏好
  - `decision` - 决策

### memory_palace_search

**必填：**
- `query`: 搜索关键词（可以是自然语言描述）

**可选：**
- `tags`: 只搜索特定标签
- `topK`: 返回数量，默认 10

### memory_palace_record_experience

**必填：**
- `content`: 经验内容
- `applicability`: 这个经验在什么场景下有用
- `source`: 来源标识（如任务 ID）

**可选：**
- `category`: 类别
  - `development` - 开发
  - `operations` - 运维
  - `product` - 产品
  - `communication` - 沟通
  - `general` - 一般

### 经验有效性 (effectivenessScore)

经验按 `effectivenessScore`（0-1 分）排序，分数越高越靠前：

| 操作 | 分数变化 | 说明 |
|------|---------|------|
| 记录新经验 | 初始 0.1 分 | 新经验不会被完全遗忘 |
| 每次查询使用 | +0.1 分 | 被调用时自动累加 |
| 每次验证有效 | +0.3 分 | 调用 `verify_experience(effective=true)` |
| 每次验证无效 | -0.1 分 | 调用 `verify_experience(effective=false)` |

**验证规则：** 需要 2+ 次验证才标记为"已验证"

**示例：**
```
经验被查询3次、验证2次有效：
effectivenessScore = min(1, 2*0.3 + 3*0.1) = min(1, 0.9) = 0.9
```

### memory_palace_link

将两条记忆关联起来。

**必填：**
- `sourceId`: 源记忆 ID
- `targetId`: 目标记忆 ID
- `type`: 关系类型
  - `relates_to` - 相关
  - `refines` - 细化
  - `contradicts` - 矛盾

**可选：**
- `note`: 说明

### memory_palace_get_related

获取某条记忆的所有关联记忆。

**必填：**
- `id`: 记忆 ID

**可选：**
- `type`: 只返回特定类型的关系（`relates_to` / `refines` / `contradicts`）

---

## 使用示例

### 记住用户偏好
```
memory_palace_write: { 
  "content": "用户偏好深色模式，喜欢简洁的回复风格",
  "tags": ["偏好", "UI"],
  "importance": 0.9,
  "type": "preference"
}
```

### 记住项目状态
```
memory_palace_write: { 
  "content": "MiroFish 项目已完成 MVP 开发，正在准备上线",
  "location": "MiroFish",
  "tags": ["项目", "状态"],
  "importance": 0.8,
  "type": "fact"
}
```

### 记录技术决策
```
memory_palace_record_experience: { 
  "content": "TypeScript 的 as const 可以让类型推断更精确",
  "category": "development",
  "applicability": "需要精确类型推断的场景，如配置对象、常量定义",
  "source": "MiroFish-dev"
}
```

### 查找相关经验
```
memory_palace_get_relevant_experiences: { 
  "context": "需要为新项目选择数据库",
  "limit": 3
}
```

### 智能总结
```
memory_palace_summarize: { 
  "id": "memory-id",
  "save_summary": true
}
```

---

## 工作原理

### 记忆写入流程
1. Agent 调用 `write`
2. 记忆存储到本地文件系统（Markdown 格式）
3. 如果有向量模型，同时建立语义索引
4. 返回记忆 ID，可用于后续检索

### 记忆搜索流程
1. Agent 调用 `search` 或 `recall`
2. 如果有向量模型，进行语义相似度匹配
3. 同时进行关键词匹配和过滤
4. 结合 `importance` 和 `decayScore` 排序
5. 返回最相关的记忆

### 遗忘机制（艾宾浩斯遗忘曲线）

记忆宫殿内置**艾宾浩斯遗忘曲线**机制，模拟人类记忆的自然衰减：

**核心机制：**
- 每条记忆有 `decayScore`（0-1），初始为 1.0
- 每次访问记忆，`decayScore = min(1, decayScore × 0.9 + 0.2)`
- `decayScore < 0.1` 时，记忆自动归档（可恢复）
- 归档记忆仍可搜索到，但权重降低

**环境变量配置：**
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MEMORY_DECAY_ENABLED` | `true` | 启用衰减 |
| `MEMORY_DECAY_ARCHIVE_THRESHOLD` | `0.1` | 归档阈值 |
| `MEMORY_DECAY_RECOVERY_FACTOR` | `0.2` | 恢复因子 |

**向后兼容：** 已有的记忆自动初始化 `decayScore = 1.0`

---

## 注意事项

1. **向量模型可选** — 未安装时自动降级到文本搜索，不影响基本功能
2. **记忆是持久化的** — 写入后即使重启也保留
3. **经验需要验证** — 记录的经验需要 2+ 次验证才标记为"已验证"
4. **标签很重要** — 好的标签能大幅提升检索精度
5. **重要性建议** — 真正重要的记忆设置 0.7+，便于后续优先检索

---

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| 搜索找不到 | 用 `expand_concepts` 扩展搜索词 |
| 记忆太多 | 用 `compress` 压缩或 `extract_experience` 提炼 |
| 不确定记忆是否正确 | 用 `verify_experience` 验证 |
| 想不起某件事 | 用 `search` 配合关键词搜索 |
