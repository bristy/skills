---
name: meegle
description: 连接飞书项目/Meegle，查询和管理工作项、待办等。自动检测登录状态，未登录时引导 Device Code 授权。
version: 0.0.3
homepage: https://www.npmjs.com/package/@lark-project/meegle
metadata:
  openclaw:
    homepage: https://www.npmjs.com/package/@lark-project/meegle
    emoji: 📋
    requires:
      bins:
        - node
        - npx
    install:
      - kind: node
        package: "@lark-project/meegle"
        bins:
          - meegle
---

# Meegle SKILL

通过 Meegle CLI 连接飞书项目/Meegle 平台，支持查询工作项、管理待办等操作。

## 前置条件

运行环境需要 Node.js 18+。所有命令通过 `npx @lark-project/meegle@beta` 执行，无需手动安装或更新。

## Auth Guard

在执行任何 Meegle 业务命令前，必须先检查登录状态。执行以下步骤：

### 步骤 1：检查登录状态

```bash
npx @lark-project/meegle@beta auth status --format json
```

返回值示例：
- 已登录：`{ "authenticated": true, "host": "meegle.com", "source": "token_store", "expires_in_minutes": 42 }`
- 未登录且有 host：`{ "authenticated": false, "host": "meegle.com", "source": null, "expires_in_minutes": null }`
- 未登录且无 host：`{ "authenticated": false, "host": null, "source": null, "expires_in_minutes": null }`

### 步骤 2：处理结果

- **authenticated 为 true**：直接执行业务命令。
- **authenticated 为 false**：进入登录引导流程（见下方）。

## 登录引导流程

### 选择站点

如果 `host` 为 null（首次使用），询问用户：

> 你要连接哪个站点？
> 1) 飞书项目 (project.feishu.cn)
> 2) Meegle (meegle.com)
> 3) 自定义域名（请直接输入域名）

用户回复后获得 host 值。如果 `host` 已有值，跳过此步。

### 初始化授权

使用 host 值执行：

```bash
npx @lark-project/meegle@beta auth login --device-code --phase init --host <host> --format json
```

返回 JSON 包含 `verification_uri_complete`、`user_code`、`device_code`、`client_id`、`interval`、`expires_in`。

解析 JSON 后向用户发送：

> 请在浏览器中打开以下链接完成授权：
> <verification_uri_complete>

### 等待授权完成（主动轮询）

> **关键行为**：发送验证链接后，你必须**立即开始轮询**，不要等待用户回复。将 `sleep` 和 `poll` 合并为一条 Bash 命令执行，检查结果后决定下一步。

按以下循环执行（**发送验证链接后立即进入第 1 步，不要停下来等用户消息**）：

1. 执行 sleep + 单次轮询（合并为一条命令，避免中断）：

```bash
sleep <interval> && npx @lark-project/meegle@beta auth login --device-code --phase poll --once \
  --device-code-value <device_code> --client-id <client_id> --format json
```

2. 根据返回的 `status` 字段处理：
   - `"ok"`：**立即通知用户登录成功**（发送消息或更新卡片），然后再继续执行用户原始请求的业务命令。
   - `"authorization_pending"`：用户尚未完成授权，**立即回到步骤 1 继续轮询**（再次调用同样的 sleep + poll 命令）。
   - `"slow_down"`：轮询过快，将 `interval` 增加 5 秒，回到步骤 1。
   - `"expired_token"`：授权已超时，提示用户重新发起登录。

3. 最多轮询 `expires_in / interval` 次。超过后提示用户重试。

> **禁止**：不要在发送验证链接后停下来等用户说"我授权好了"。你必须主动轮询，用户在浏览器完成授权后你应当自动检测到。

> **重要**：授权成功后，必须先单独发送一条"登录成功"的消息给用户，再执行后续业务命令。不要把登录结果和业务查询结果合并到一次响应中——用户需要第一时间看到授权状态的变化。

## 业务命令调用

Auth Guard 通过后，使用以下模式调用业务命令。

### 命令结构

```bash
npx @lark-project/meegle@beta <resource> <method> [flags] --format json
```

命令采用 `resource method` 两级结构。所有输出默认 JSON 格式。

### 全局 Flag

| Flag | 说明 |
|------|------|
| `--format json\|table\|ndjson` | 输出格式，默认 json |
| `--select <props>` | 选取输出属性，逗号分隔（支持 dot path，如 `name,owner.name`） |
| `--profile <name>` | 临时切换 profile |
| `--verbose` | 显示详细日志 |

### 参数传递

三种方式，优先级从高到低：

1. **Flag 模式**（推荐）：`--project-key PROJ --work-item-type-key story`
2. **--set 模式**（设置工作项字段）：`--set priority=1 --set name="任务标题"`，value 支持 JSON
3. **--params 模式**（完整 JSON）：`--params '{"project_key":"PROJ","work_item_type_key":"story"}'`

Flag 和 --set 会覆盖 --params 中的同名字段。

### 常用命令速查

#### 查询待办

```bash
npx @lark-project/meegle@beta my todo --format json
```

#### 查询工作项

```bash
npx @lark-project/meegle@beta workitem get --project-key <project_key> --work-item-id <id> --format json
```

#### 搜索工作项（MQL）

```bash
npx @lark-project/meegle@beta workitem query --project-key <project_key> --search-mql "<MQL>" --format json
```

#### 创建工作项

```bash
npx @lark-project/meegle@beta workitem create --project-key <project_key> --work-item-type-key <type> \
  --set name="标题" --set priority=1 --format json
```

#### 更新工作项字段

```bash
npx @lark-project/meegle@beta workitem update --project-key <project_key> --work-item-id <id> \
  --set name="新标题" --format json
```

#### 查询项目信息

```bash
npx @lark-project/meegle@beta project get --project-key <project_key> --format json
```

#### 查询工作项类型和字段元数据

```bash
npx @lark-project/meegle@beta workitem meta-types --project-key <project_key> --format json
npx @lark-project/meegle@beta workitem meta-fields --project-key <project_key> --work-item-type-key <type> --format json
```

### 查看命令参数（inspect）

使用 `inspect` 查看某个命令的完整参数 schema（必填/可选、类型、描述）：

```bash
npx @lark-project/meegle@beta inspect workitem.create    # 查看 workitem create 的参数详情
npx @lark-project/meegle@beta inspect workitem.query     # 查看 workitem query 的参数详情
```

不带参数时列出所有可用命令：

```bash
npx @lark-project/meegle@beta inspect                    # 列出所有 resource 及其 method
```

> **推荐**：在调用一个不熟悉的命令前，先用 `inspect` 查看其参数 schema，确认必填字段和类型。

### 输出处理

- 始终使用 `--format json` 获取结构化输出，方便解析
- 使用 `--select` 精简返回字段，如 `--select id,name,current_nodes.name`
- 命令返回错误时，JSON 中包含 `error` 和 `message` 字段

## 触发条件

- **主动登录**：用户说"登录 Meegle"、"连接飞书项目"、"login meegle"等。
- **被动拦截**：用户请求任何 Meegle 业务操作（查询待办、查工作项、创建任务等），优先执行 Auth Guard。

## 错误处理

- 如果 bash 返回 `command not found` 或 npx 不可用，提示用户安装 Node.js 18+。
- 如果 `--phase init` 返回错误（站点不支持 Device Code），提示用户在终端中执行 `npx @lark-project/meegle@beta auth login`。
- 如果 `--phase poll` 超时，提示用户重试登录流程。
