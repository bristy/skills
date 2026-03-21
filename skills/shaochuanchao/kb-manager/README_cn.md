# kb-manager

将文章、PDF、提示词、项目笔记整理为 OpenClaw agent 工作区中的本地结构化知识库。

`kb-manager` 提供一套轻量但可用的知识管理流程：

- 自动初始化知识库目录
- 按用途自动分类内容
- 以结构化 Markdown 保存知识条目
- 分类不确定时回落到 `00_inbox`
- 后续可继续整理，不丢信息

这是一个适合首发试用的 **v1**：足够小，足够清晰，也方便后续扩展。

---

## 为什么使用它

当知识散落在聊天记录、零散笔记和随手文件里时，后续几乎无法复用。

`kb-manager` 的目标很简单：

1. 把内容发送给 knowledge agent
2. 让 skill 判断是否值得保存
3. 自动归类到合适目录
4. 用统一 Markdown 模板保存
5. 把暂时不确定的内容放进 `00_inbox`，后面再整理

---

## 适合管理的内容

- 官方文档
- 教程与学习笔记
- 项目讨论与方案
- 调研内容
- 提示词与操作指令
- 个人总结

---

## 快速开始

### 1. 创建独立的 knowledge agent

```bash
openclaw agents add knowledge
```

### 2. 将本 skill 放入 agent 的 workspace

```text
skills/kb-manager/
```

### 3. 使用该 agent 开启新会话

### 4. 初始化知识库

```text
请使用 kb-manager 初始化知识库。

要求：
1. 在当前 workspace 下创建 `knowledge/` 目录
2. 创建标准子目录：
   - 00_inbox
   - 01_reference
   - 02_learning
   - 03_projects
   - 04_research
   - 05_playbooks
   - 06_prompts
   - 07_archive
   - _meta
3. 创建分类规则、命名规则、当前模板和入库日志文件
4. 默认使用 `templates/default-entry.md` 作为通用模板
5. 项目类内容优先使用 `templates/project-entry.md`
6. 分类不确定时统一进入 `00_inbox`
```

---

## 初始化后会生成的目录

```text
knowledge/
  00_inbox/
  01_reference/
  02_learning/
  03_projects/
  04_research/
  05_playbooks/
  06_prompts/
  07_archive/
  _meta/
```

元文件：

```text
knowledge/_meta/classification-rules.md
knowledge/_meta/naming-rules.md
knowledge/_meta/template.md
knowledge/_meta/intake-log.md
```

---

## 常见工作流

### 保存文章

```text
请把这篇文章收入知识库。

要求：
1. 先判断是否值得保存
2. 自动分类
3. 使用默认模板整理
4. 如果分类不确定，放入 `00_inbox`
5. 输出保存路径、文件名和结构化 Markdown
```

### 保存 PDF

```text
请把这份 PDF 整理成知识条目。

要求：
1. 如果是官方文档，优先归类到 `01_reference`
2. 如果是教程或学习资料，优先归类到 `02_learning`
3. 使用默认模板整理
4. 输出最终路径、文件名和结构化 Markdown
```

### 整理 inbox

```text
请整理 `knowledge/00_inbox/`。

要求：
1. 对高置信度内容重新分类
2. 补充或优化标签
3. 对低价值内容建议归档或删除
4. 仍不确定的内容继续保留在 inbox
5. 输出简短整理报告
```

---

## 模板文件

默认模板：

```text
templates/default-entry.md
```

项目模板：

```text
templates/project-entry.md
```

你可以按需要修改。

---

## 分类说明

- `01_reference`：官方文档、API、规范、产品说明
- `02_learning`：教程、文章、学习笔记
- `03_projects/<project-name>`：项目笔记、讨论、方案、设计文档
- `04_research`：调研、对比、研究
- `05_playbooks`：SOP、流程、操作方法
- `06_prompts`：提示词与可复用操作指令
- `00_inbox`：暂时无法稳定判断的内容

---

## 可修改的位置

可以根据需要调整以下文件：

- `SKILL.md` → 入库与分类行为
- `templates/default-entry.md` → 默认知识条目模板
- `templates/project-entry.md` → 项目知识模板
- `docs/classification-rules.md` → 可读的分类说明
- `docs/naming-rules.md` → 命名规则说明
- `knowledge/_meta/template.md` → 初始化后正在使用的模板

---

## 当前 v1 范围

当前版本聚焦于：

- 初始化
- 入库
- 分类
- 保存
- inbox 兜底
- 基础 inbox 整理

后续如有真实需求，再考虑扩展：

- 更强的重复检测
- 更丰富的模板体系
- 搜索与索引
- 导出与备份
- 回顾流程
