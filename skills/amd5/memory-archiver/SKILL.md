---
name: memory-archiver
description: 记忆管理技能 - 五层时间架构 + 三类记忆标签 + 最小化写入 + 压缩检测
version: 2.1.0
author: 前端 ⚡
---

# Memory Archiver Skill - 记忆归档技能

**版本**: 2.1  
**创建日期**: 2026-03-11  
**更新日期**: 2026-03-19  
**作者**: 前端 ⚡

---

## 📋 技能描述

五层时间架构（hourly → daily → weekly → monthly → yearly）+ 三类记忆标签 + 最小化写入原则 + 压缩风险检测。

---

## 🎯 功能清单

| 任务 | 频率 | 说明 |
|------|------|------|
| **记忆及时写入** | 10 分钟 | 检查并写入重要信息到 daily 文件 |
| **记忆同步 - Hourly** | 每小时 | 更新 hourly 记忆文件 |
| **记忆归档 - Daily** | 每天 23:00 | 提炼 hourly 到 daily |
| **记忆总结 - Weekly** | 每周日 22:00 | 提炼 daily 到 weekly/MEMORY.md |
| **记忆总结 - Monthly** | 每月末 22:00 | 提炼 weekly 到 monthly |
| **记忆总结 - Yearly** | 每年 12/31 21:00 | 提炼 monthly 到 yearly |

---

## 📂 文件结构

```
skills/memory-manager/
├── SKILL.md                      # 本文件
├── scripts/
│   ├── sync-hourly.sh            # 每小时同步脚本
│   ├── sync-daily.sh             # 每日归档脚本
│   ├── sync-weekly.sh            # 每周总结脚本
│   ├── sync-monthly.sh           # 每月总结脚本
│   ├── sync-yearly.sh            # 每年总结脚本
│   └── write-timely.sh           # 及时写入脚本
└── config.json                   # 配置文件 (可选)
```

---

## 🔧 安装/启用

### 方法 1: 手动注册 cron 任务

```bash
# 1. 记忆及时写入 (10 分钟)
openclaw cron add --name "记忆及时写入" \
  --schedule '{"kind":"every","everyMs":600000}' \
  --payload '{"kind":"systemEvent","text":"📝 记忆及时写入检查..."}' \
  --session-target main

# 2. 记忆同步 - Hourly (每小时)
openclaw cron add --name "记忆同步 - Hourly" \
  --schedule '{"kind":"every","everyMs":3600000}' \
  --payload '{"kind":"systemEvent","text":"🕐 每小时记忆同步时间！..."}' \
  --session-target main

# 3. 记忆归档 - Daily (每天 23:00)
openclaw cron add --name "记忆归档 - Daily" \
  --schedule '{"kind":"cron","expr":"0 23 * * *","tz":"Asia/Shanghai"}' \
  --payload '{"kind":"systemEvent","text":"🌙 每日记忆归档时间！..."}' \
  --session-target main

# 4. 记忆总结 - Weekly (每周日 22:00)
openclaw cron add --name "记忆总结 - Weekly" \
  --schedule '{"kind":"cron","expr":"0 22 * * 0","tz":"Asia/Shanghai"}' \
  --payload '{"kind":"systemEvent","text":"📅 每周记忆总结时间！..."}' \
  --session-target main

# 5. 记忆总结 - Monthly (每月末 22:00)
openclaw cron add --name "记忆总结 - Monthly" \
  --schedule '{"kind":"cron","expr":"0 22 L * *","tz":"Asia/Shanghai"}' \
  --payload '{"kind":"systemEvent","text":"📆 每月记忆总结时间！..."}' \
  --session-target main

# 6. 记忆总结 - Yearly (每年 12/31 21:00)
openclaw cron add --name "记忆总结 - Yearly" \
  --schedule '{"kind":"cron","expr":"0 21 31 12 *","tz":"Asia/Shanghai"}' \
  --payload '{"kind":"systemEvent","text":"🎆 年度记忆总结时间！..."}' \
  --session-target main
```

### 方法 2: 使用技能脚本

```bash
cd ~/.openclaw/workspace/skills/memory-manager
bash scripts/install.sh
```

---

## 📝 任务详情

### 1️⃣ 记忆及时写入 (10 分钟)

**触发**: 每 10 分钟  
**行为**:
1. 回顾最近 10 分钟的对话
2. 识别重要信息：
   - 新决策
   - 配置变更
   - 问题解决
   - 技术笔记
3. 写入 `memory/daily/YYYY-MM-DD.md`
4. 更新时间戳

**静默规则**:
- ✅ 正常 → `NO_REPLY`
- ⚠️ 异常 → 输出提醒

---

### 2️⃣ 记忆同步 - Hourly (每小时)

**触发**: 每小时整点  
**行为**:
1. 检查 `memory/hourly/YYYY-MM-DD.md` 是否存在
2. 添加新的小时段落
3. 记录：
   - 完成事项
   - 技术笔记
   - 状态
4. 更新时间戳

**输出**: 更新 hourly 文件

---

### 3️⃣ 记忆归档 - Daily (每天 23:00)

**触发**: 每天 23:00 (Asia/Shanghai)  
**行为**:
1. 回顾当天所有 hourly 记忆
2. 提炼重要内容到 daily 文件
3. 记录：
   - 今日完成
   - 重要决策
   - 技术笔记
   - 问题与解决
4. 标记值得长期保存的内容

**输出**: 更新 daily 文件

---

### 4️⃣ 记忆总结 - Weekly (每周日 22:00)

**触发**: 每周日 22:00 (Asia/Shanghai)  
**行为**:
1. 回顾本周所有 daily 记忆文件
2. 提炼核心知识、最佳实践、模式识别
3. 更新 `MEMORY.md` 长期记忆文件
4. 更新 `memory/weekly/YYYY-Www.md`
5. 记录：
   - 本周目标完成情况
   - 项目进展
   - 核心知识沉淀
6. 制定下周计划

**输出**: 更新 MEMORY.md 和 weekly 文件

---

### 5️⃣ 记忆总结 - Monthly (每月末 22:00)

**触发**: 每月最后一天 22:00 (Asia/Shanghai)  
**行为**:
1. 回顾本月所有 weekly 记忆文件 (`memory/weekly/`)
2. 提炼月度核心成果、重要决策、技术沉淀
3. 创建/更新 `memory/monthly/YYYY-MM.md`
4. 记录：
   - 本月目标完成情况
   - 重大项目进展与里程碑
   - 核心知识与技能提升
   - 问题与经验教训
   - 下月计划/展望
5. 将高价值内容同步到 `MEMORY.md`

**输出**: 更新 monthly 文件和 MEMORY.md

---

### 6️⃣ 记忆总结 - Yearly (每年 12/31 21:00)

**触发**: 每年 12月31日 21:00 (Asia/Shanghai)  
**行为**:
1. 回顾本年所有 monthly 记忆文件 (`memory/monthly/`)
2. 提炼年度核心成果、重大决策、技术演进
3. 创建/更新 `memory/yearly/YYYY.md`
4. 记录：
   - 年度目标完成情况
   - 重大项目成果与里程碑
   - 核心技能成长与知识图谱
   - 重要经验教训
   - 下年规划/展望
5. 精选最高价值内容更新到 `MEMORY.md`

**输出**: 更新 yearly 文件和 MEMORY.md

---

## 🎛️ 配置选项

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MEMORY_WORKSPACE` | `~/.openclaw/workspace` | 工作区路径 |
| `MEMORY_DAILY_PATH` | `memory/daily` | daily 文件目录 |
| `MEMORY_HOURLY_PATH` | `memory/hourly` | hourly 文件目录 |
| `MEMORY_WEEKLY_PATH` | `memory/weekly` | weekly 文件目录 |
| `MEMORY_MONTHLY_PATH` | `memory/monthly` | monthly 文件目录 |
| `MEMORY_YEARLY_PATH` | `memory/yearly` | yearly 文件目录 |
| `MEMORY_LONGTERM_FILE` | `MEMORY.md` | 长期记忆文件 |

### 静默模式配置

在 cron 任务的 `delivery` 中设置：

```json
{
  "delivery": {
    "mode": "none"
  }
}
```

或添加静默指令到 payload text。

---

## 🔍 诊断命令

```bash
# 查看所有记忆管理任务
openclaw cron list | grep -E "记忆|memory"

# 查看任务运行历史
openclaw cron runs --jobId <job-id>

# 手动触发 hourly 同步
openclaw cron run --jobId <hourly-job-id>

# 检查记忆文件
ls -la ~/.openclaw/workspace/memory/
```

---

## 📊 记忆架构

```
双维度架构: 时间分层 × 类型标签

时间维度 (纵向提炼):

  Yearly ← Monthly ← Weekly ← Daily ← Hourly ← 即时写入
  (12/31)  (月末)    (周日)   (23:00)  (每小时)  (10分钟)

类型维度 (横向标签):

  [episodic]     [semantic]      [procedural]
  发生了什么      我知道什么       怎么做
  事件/操作       知识/事实        流程/步骤
  可淘汰         优先沉淀         持续更新

提炼规则:
  episodic  → 时间越久越可淘汰（保留关键里程碑）
  semantic  → 优先进入 MEMORY.md 长期保存
  procedural → 持续更新，保持最新版本
```

---

## 🎯 记录原则

### ✅ 应该记录

- **关键决策和教训** — 做了什么选择、为什么、结果如何
- **新发现的有价值内容** — 工具、技巧、解决方案
- **重要的人际关系和偏好** — 用户习惯、沟通风格
- **技术栈的使用经验** — 踩坑、最佳实践、配置方案
- **工作习惯的调整** — 流程优化、效率改进

### ❌ 不应该记录

- **重复的上下文** — 已有记录的内容不再重复
- **毫无意义的日常** — 无事发生就不记
- **太过私密的细节** — 尊重隐私边界
- **短期、易变的想法** — 未确定的临时想法不沉淀

> 核心判断：**这条信息在未来回顾时���否有价值？** 有就记，没有就跳过。

---

## ✏️ 最小化写入原则

每条记忆遵循以下规则：

1. **最小有用笔记** — 用最少的文字传达最多的信息，不写废话
2. **具体事实 > 评论感想** — 记"Tailwind 的 @apply 在生产构建中被移除"而不是"今天学了点 CSS"
3. **区分事实与推断** — 事实直接写，推断加 `[推断]` 标记
4. **标记过时记忆** — 发现旧记忆已过时，加 `[已过时]` 标记或直接删除
5. **不承诺未写入的记忆** — 没写入文件的就不算记住了

### 写入格式参考

```markdown
## 10:30 [semantic] Tailwind 构建
- `@apply` 指令在 Tailwind v4 中需要 `@import "tailwindcss"` 才能生效
- 解决方案：postcss.config.js 添加 tailwindcss 插件

## 14:00 [episodic] 模板开发
- 完成 0004 模板首页布局，使用 UIkit grid
- 决策：导航栏采用固定定位而非粘性定位

## 16:00 [procedural] ClawHub 发布流程
- 1. 更新 version → 2. clawhub publish → 3. 验证安装
```

---

## 🏷️ 三类记忆标签

每条记忆条目用标签标注类型，与时间分层共存：

### Episodic（事件）— 发生了什么
- 时间线日志、操作记录、会话事件
- 标签：`[episodic]`
- 示例："10:02 升级了 memory-archiver 到 v2.0"

### Semantic（知识）— 我知道什么
- 技术知识、事实、规则、配置
- 标签：`[semantic]`
- 示例："UIkit slider 不会自动生成 `<li>`，需手动添加"

### Procedural（流程）— 怎么做
- 工作流程、操作步骤、最佳实践
- 标签：`[procedural]`
- 示例："ClawHub 发布：更新版本 → publish → 验证"

### 使用方式

- 写入时在条目标题后加标签：`## 10:30 [semantic] CSS Flex 溢出`
- 搜索时可按标签过滤：`memory_search("semantic CSS")`
- 提炼时按类型归类：semantic 类优先进 MEMORY.md，episodic 类可淘汰

---

## 📏 压缩风险检测

监控记忆文件总量，防止上下文窗口溢出。

### 检测方法

在 daily 归档或 weekly 总结时，检查记忆文件总大小：

```bash
# 检查所有记忆文件总大小
du -sh ~/.openclaw/workspace/memory/
find ~/.openclaw/workspace/memory/ -name "*.md" | wc -l

# 检查 MEMORY.md 大小
wc -c ~/.openclaw/workspace/MEMORY.md
```

### 阈值与动作

| 总量 | 状态 | 动作 |
|------|------|------|
| < 50KB | ✅ 安全 | 正常运行 |
| 50-100KB | ⚠️ 注意 | 建议整理，删除低价值内容 |
| > 100KB | 🚨 警告 | 立即精简，合并重复，淘汰过时记忆 |

### MEMORY.md 单独限制

| 大小 | 状态 | 动作 |
|------|------|------|
| < 5KB | ✅ 精简 | 理想状态 |
| 5-10KB | ⚠️ 偏大 | 考虑迁移细节到 weekly/monthly |
| > 10KB | 🚨 臃肿 | 必须瘦身，只保留核心知识 |

### 自动检测时机

- **Daily 归档 (23:00)**：检查当日文件增长
- **Weekly 总结 (周日 22:00)**：检查总量，输出健康报告
- 超阈值时在总结中标注 `[⚠️ 记忆膨胀]`，提醒清理

---

## 🔄 恢复技巧

当会话重启或上下文丢失时，按以下步骤恢复状态：

1. **阅读顺序**: hourly → daily → weekly → monthly → yearly（从近到远逐层回溯）
2. **记忆搜索**: 使用 `memory_search` 快速定位相关内容
3. **关联记忆**: 找到相关记忆的上下文，跨层追溯补全信息
4. **状态恢复**: 从相关记忆中恢复工作状态，继续未完成的任务

---

## ⚠️ 注意事项

1. **时区设置**: 所有 cron 任务使用 `Asia/Shanghai` 时区
2. **静默模式**: 日常任务默认静默，仅异常时提醒
3. **文件权限**: 确保 memory 目录可写
4. **时间戳**: 每次更新后同步更新时间戳

---

## 📝 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-11 | 1.0 | 初始版本，封装 4 个记忆管理任务 (三层架构) |
| 2026-03-19 | 2.0 | 新增 Monthly + Yearly 层，升级为五层记忆架构 |
| 2026-03-19 | 2.1 | 新增最小化写入原则 + 三类记忆标签 + 压缩风险检测 |

---

*技能位置：`~/.openclaw/workspace/skills/memory-archiver/`*
