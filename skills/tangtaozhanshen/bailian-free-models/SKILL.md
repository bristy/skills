# 阿里百炼免费模型 Skill 使用指南

## 概述

本 Skill 提供阿里百炼 (通义千问) 免费模型的接入能力，支持通过 OpenClaw 网关调用阿里百炼平台的免费模型资源。

## API 配置

- **服务商**: Alibaba Bailian (通义千问)
- **API 端点**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **认证方式**: Bearer Token
- **配置路径**: `/root/.openclaw/workspace/it-ops/bailian-free-pool/bailian-api-config.json`

## 可用免费模型列表

### 文本对话模型

| 模型 ID | 模型名称 | 免费额度 | 适用场景 |
|--------|----------|----------|----------|
| qwen-turbo | 通义千问 Turbo | 100 万 tokens/月 | 快速响应、简单任务 |
| qwen-plus | 通义千问 Plus | 100 万 tokens/月 | 平衡性能与成本 |
| qwen-max | 通义千问 Max | 100 万 tokens/月 | 复杂推理、高质量输出 |
| qwen2.5-72b-instruct | Qwen2.5-72B | 100 万 tokens/月 | 超大规模语言理解 |
| qwen2.5-coder-32b-instruct | Qwen2.5-Coder-32B | 100 万 tokens/月 | 代码生成与理解 |

### 视觉模型

| 模型 ID | 模型名称 | 免费额度 | 适用场景 |
|--------|----------|----------|----------|
| qwen-vl-max | 通义千问视觉 Max | 100 万 tokens/月 | 复杂视觉理解 |
| qwen-vl-plus | 通义千问视觉 Plus | 100 万 tokens/月 | 通用视觉任务 |
| qwen-vl-ocr | 通义千问 OCR | 100 万 tokens/月 | 文字识别 |

### 嵌入模型

| 模型 ID | 模型名称 | 免费额度 | 适用场景 |
|--------|----------|----------|----------|
| text-embedding-v3 | 文本嵌入 V3 | 100 万 tokens/月 | 语义搜索、向量检索 |

## 使用方式

### 1. 在 OpenClaw 中调用

在 OpenClaw 配置中添加模型前缀 `bailian/`:

```bash
# 示例：使用 qwen-turbo 模型
/model bailian/qwen-turbo
```

### 2. 通过 Python 脚本调用

```python
import requests

API_KEY = "sk-5f4e6734b31b40f39dc4f9c96c8aeb5c"
API_ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "qwen-turbo",
    "messages": [
        {"role": "user", "content": "你好"}
    ]
}

response = requests.post(
    f"{API_ENDPOINT}/chat/completions",
    headers=headers,
    json=payload
)

print(response.json())
```

### 3. 通过 curl 调用

```bash
curl -X POST "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  -H "Authorization: Bearer sk-5f4e6734b31b40f39dc4f39dc4f9c96c8aeb5c" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-turbo",
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

## 模型池自动切换

本 Skill 已集成到阿里百炼免费模型池管理系统，支持:

- **自动轮询**: 按优先级自动选择可用模型
- **错误切换**: 遇到 429/404 错误时自动切换到下一个模型
- **配额监控**: 实时监控配额使用情况
- **状态报告**: 定期生成模型可用性报告

### 查看可用模型列表

```bash
cd /root/.openclaw/workspace/it-ops/bailian-free-pool
python bailian_free_pool.py
```

### 获取下一个可用模型

```python
from bailian_free_pool import BailianFreePool

pool = BailianFreePool()
next_model = pool.get_current_default()
print(f"下一个可用模型：{next_model}")
```

## 配额管理

### 配额查询

登录阿里百炼控制台查看配额使用情况:
https://bailian.console.aliyun.com/

### 配额预警

当配额使用超过 90% 时，系统会自动记录并告警:

```json
{
  "model_id": "qwen-turbo",
  "threshold_pct": 0.9,
  "has_free_quota": true,
  "is_sufficient": true
}
```

## 故障排查

### 常见问题

#### 1. 认证失败 (401)
- 检查 API Key 是否正确
- 确认 API Key 未过期
- 验证账户状态正常

#### 2. 速率限制 (429)
- 等待 1 分钟后重试
- 切换到其他可用模型
- 考虑升级配额

#### 3. 模型不存在 (404)
- 检查模型 ID 是否正确
- 确认模型在免费额度范围内
- 使用 `bailian_free_pool.py` 查看可用模型列表

### 日志位置

- **API 调用日志**: `/root/.openclaw/workspace/it-ops/bailian-free-pool/check_log.jsonl`
- **配额使用记录**: `/root/.openclaw/workspace/it-ops/bailian-free-pool/quota-usage.json`
- **模型状态**: `/root/.openclaw/workspace/it-ops/bailian-free-pool/model_state.json`

## 最佳实践

1. **优先使用轻量模型**: 简单任务使用 `qwen-turbo`，复杂任务使用 `qwen-max`
2. **合理分配配额**: 开发测试使用低优先级模型，生产环境使用高优先级模型
3. **定期监控配额**: 每周检查配额使用情况，避免超额
4. **利用自动切换**: 启用模型池自动切换功能，提高可用性

## 更新记录

- **2026-03-20**: 初始版本，接入阿里百炼免费模型池
- **API Key**: sk-5f4e6734b31b40f39dc4f9c96c8aeb5c
- **配置人**: OpenClaw 运维团队

## 相关文档

- [阿里百炼官方文档](https://help.aliyun.com/zh/dashscope/)
- [OpenClaw 免费模型池管理](./README.md)
- [模型池配置](./available-models.json)
