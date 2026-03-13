---
name: giggle-generation-image
description: 支持文生图和图生图。当用户需要创建或生成图像时使用。使用场景：(1) 根据文字描述生成，(2) 使用参考图生成，(3) 自定义模型、画幅比例、分辨率。触发词：生成图片、画画、创建图片、AI 艺术图
version: "0.0.4"
license: MIT
metadata:
  {
    "openclaw":
      {
        "emoji": "📂",
        "requires": { "bins": ["python3"], "env": ["GIGGLE_API_KEY"] },
        "primaryEnv": "GIGGLE_API_KEY",
      },
  }
---

简体中文 | [English](./SKILL.md)

# Giggle 图像生成（多模型）

通过 giggle.pro 平台的 Generation API 生成 AI 图像，支持多种模型。

**API Key**：加载优先级 1) `~/.openclaw/.env`（优先）2) 系统环境变量 `GIGGLE_API_KEY`。若未配置，脚本会提示配置。

> **禁止内联 Python**：所有命令必须通过 `exec` 工具直接执行。**切勿**使用 `python3 << 'EOF'` 或 heredoc 内联代码。

## 支持的模型

| 模型 | 说明 |
|------|------|
| seedream45 | Seedream 模型，写实与创意兼备 |
| midjourney | Midjourney 风格 |
| nano-banana-2 | Nano Banana 2 模型 |
| nano-banana-2-fast | Nano Banana 2 快速版 |

---

## 执行流程（三阶段双路径）

图像生成通常需要 30–120 秒。采用「快速提交 + Cron 轮询 + 同步兜底」三阶段架构。

> **重要**：**切勿**在 exec 的 `env` 参数中传递 `GIGGLE_API_KEY`。API Key 从 `~/.openclaw/.env` 或系统环境变量自动读取。

---

### 阶段 1：提交任务（exec 在 10 秒内完成）

**先向用户发送消息**：「图像生成进行中，通常需要 30–120 秒，结果将自动发送。」

```bash
# 文生图（默认 seedream45）
python3 scripts/generation_api.py \
  --prompt "描述" --aspect-ratio 16:9 \
  --model seedream45 --resolution 2K \
  --no-wait --json

# 文生图 - Midjourney
python3 scripts/generation_api.py \
  --prompt "描述" --model midjourney \
  --aspect-ratio 16:9 --resolution 2K \
  --no-wait --json

# 图生图 - 参考图 URL
python3 scripts/generation_api.py \
  --prompt "转换为油画风格，保持构图" \
  --reference-images "https://example.com/photo.jpg" \
  --model nano-banana-2-fast \
  --no-wait --json

# 批量生成多张图
python3 scripts/generation_api.py \
  --prompt "描述" --generate-count 4 \
  --no-wait --json
```

响应示例：
```json
{"status": "started", "task_id": "xxx"}
```

**立即将 task_id 存入记忆**（`addMemory`）：
```
giggle-generation-image task_id: xxx (submitted: YYYY-MM-DD HH:mm)
```

---

### 阶段 2：注册 Cron（45 秒间隔）

使用 `cron` 工具注册轮询任务。**必须严格遵循参数格式**：

```json
{
  "action": "add",
  "job": {
    "name": "giggle-generation-image-<task_id 前 8 位>",
    "schedule": {
      "kind": "every",
      "everyMs": 45000
    },
    "payload": {
      "kind": "systemEvent",
      "text": "图像任务轮询：执行 exec python3 scripts/generation_api.py --query --task-id <完整 task_id>，按 Cron 逻辑处理 stdout。若 stdout 为非 JSON 纯文本，发送给用户并移除 Cron。若 stdout 为 JSON，不发送消息，继续等待。若 stdout 为空，立即移除 Cron。"
    },
    "sessionTarget": "main"
  }
}
```

**Cron 触发处理**（根据 exec stdout 判断）：

| stdout 模式 | 动作 |
|------------|------|
| 非空纯文本（不以 `{` 开头） | **原样转发给用户**，**移除 Cron** |
| stdout 为空 | 已推送，**立即移除 Cron，不发送消息** |
| JSON（以 `{` 开头，含 `"status"` 字段） | 不发送消息，不移除 Cron，继续等待 |

---

### 阶段 3：同步等待（乐观路径，Cron 未触发时的兜底）

**无论 Cron 是否注册成功，都必须执行此步骤。**

```bash
python3 scripts/generation_api.py --query --task-id <task_id> --poll --max-wait 180
```

**处理逻辑**：

- 返回纯文本（图像就绪/失败消息） → **原样转发给用户**，移除 Cron
- stdout 为空 → Cron 已推送，移除 Cron，不发送消息
- exec 超时 → Cron 继续轮询

---

## 新请求 vs 查询旧任务

**当用户发起新的图像生成请求**时，**必须执行阶段 1 提交新任务**，不要复用记忆中的旧 task_id。

**仅当用户明确询问之前任务的进度**时，才从记忆中查询旧 task_id。

---

## 参数速查

| 参数 | 默认值 | 说明 |
|-----|--------|------|
| `--prompt` | 必填 | 图像描述 prompt |
| `--model` | seedream45 | 模型：seedream45、midjourney、nano-banana-2、nano-banana-2-fast |
| `--aspect-ratio` | 16:9 | 16:9、9:16、1:1、3:4、4:3、2:3、3:2、21:9 |
| `--resolution` | 2K | 文生图分辨率：1K、2K、4K（图生图部分支持） |
| `--generate-count` | 1 | 生成的图像数量 |
| `--reference-images` | - | 图生图参考图，支持 URL、base64、asset_id |
| `--watermark` | false | 是否添加水印（图生图） |

---

## 图生图参考图三种传入方式

图生图 API 的 `reference_images` 为对象数组，每个元素可为以下三种格式之一（可混用）：

### 方式一：URL

```json
{
  "prompt": "一只可爱的橘猫坐在窗台上晒太阳，写实风格",
  "reference_images": [
    {
      "url": "https://assets.ggltest.com/private/test_ai_director/0ebc2ffa7512a58df5/9y91pxl0hju.thumb.jpg?Expires=1772409599000&Key-Pair-Id=K271ZF3SQS38SK&Signature=..."
    }
  ],
  "generate_count": 1,
  "model": "nano-banana-2-fast",
  "aspect_ratio": "16:9",
  "watermark": false
}
```

### 方式二：Base64

```json
{
  "prompt": "一只可爱的橘猫坐在窗台上晒太阳，写实风格",
  "reference_images": [
    {
      "base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    }
  ],
  "generate_count": 1,
  "model": "nano-banana-2-fast",
  "aspect_ratio": "16:9",
  "watermark": false
}
```

> Base64 格式：直接传递纯 Base64 编码字符串，勿添加 `data:image/xxx;base64,` 前缀。

### 方式三：asset_id

```json
{
  "prompt": "一只可爱的橘猫坐在窗台上晒太阳，写实风格",
  "reference_images": [
    {
      "asset_id": "vvsdsfsdf"
    }
  ],
  "generate_count": 1,
  "model": "nano-banana-2-fast",
  "aspect_ratio": "16:9",
  "watermark": false
}
```

> 多张参考图时，在 `reference_images` 数组中追加多个对象即可。

---

## 交互引导流程

**当用户请求较模糊时，按以下步骤引导。若用户已提供足够信息，可直接执行命令。**

### 步骤 1：模型选择

```
问题：「想使用哪个模型？」
标题：「图像模型」
选项：
- "seedream45 - 写实与创意（推荐）"
- "midjourney - 艺术风格"
- "nano-banana-2 - 高品质"
- "nano-banana-2-fast - 快速生成"
multiSelect: false
```

### 步骤 2：画幅比例

```
问题：「需要什么画幅比例？」
标题：「画幅比例」
选项：
- "16:9 - 横屏（壁纸/封面）（推荐）"
- "9:16 - 竖屏（手机）"
- "1:1 - 方形"
- "其他比例"
multiSelect: false
```

### 步骤 3：生成模式

```
问题：「需要参考图片吗？」
标题：「生成模式」
选项：
- "不需要 - 仅文生图"
- "需要 - 图生图（风格迁移）"
multiSelect: false
```

### 步骤 4：执行并展示

按执行流程：发送消息 → 阶段 1 提交 → 阶段 2 注册 Cron → 阶段 3 同步等待。

结果到达后将 exec stdout 原样转发给用户。

**链接返回规范**：结果中的图像链接必须为**完整签名 URL**（含 Policy、Key-Pair-Id、Signature 等查询参数）。正确示例：`https://assets.giggle.pro/...?Policy=...&Key-Pair-Id=...&Signature=...`。错误：不要返回仅含基础路径的未签名 URL（无查询参数）。
