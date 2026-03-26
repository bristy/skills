---
name: jiuwu-agent
description: 调用久吾智能体API进行文本或文件分析处理。支持两种调用方式：(1) 文本内容分析 - 传入name(智能体名称)、docno(文档编号)、content(文本内容)；(2) 文件分析 - 传入name、docno和files(文件列表)进行智能评审。适用于合同评审、需求评审、文档审查等场景。
---

# 久吾智能体调用

调用久吾智能体API进行文本或文件分析。

## API 基础信息

- **Base URL**: `http://192.168.1.213:5000`
- **认证**: Bearer Token (Authorization header)

## Token 配置

Token 已配置在 OpenClaw 环境中，优先级：

1. **OpenClaw 环境变量** `JIUWU_CORE_TOKEN` - 通过 `openclaw.json` 的 `env.vars` 配置
2. **workspace/.env** 文件 - 在 `~/.openclaw/workspace/.env`
3. **OpenClaw根目录 .env** 文件 - 在 `~/.openclaw/.env`

> 注：如需修改 Token，请编辑 `openclaw.json` 中的 `env.vars.JIUWU_CORE_TOKEN`

## 调用方式

### 1. 文本分析 (GET)

适用于短文本、合同条款、评审意见等内容的分析。

> **注**: Token 可通过环境变量或 .env 文件配置（见上文）

```bash
curl -X 'GET' \
  'http://192.168.1.213:5000/api/AiReview/AgentAnswer?name={name}&docno={docno}&content={content}' \
  -H 'accept: text/plain' \
  -H 'Authorization: Bearer %JIUWU_CORE_TOKEN%'
```

**参数说明**:
| 参数 | 必填 | 说明 |
|-----|-----|------|
| name | 是 | 智能体名称，如：合同评审、需求评审 |
| docno | 是 | 文档编号，如：JWSO20260001 |
| content | 是 | 要分析的文本内容 |

**成功响应**:
```json
{
  "success": true,
  "data": {
    "reviewOpinion": "分析结果文本",
    "modelId": "MiniMax-M2.7",
    "provider": 2
  },
  "message": "请求成功"
}
```

**失败响应**:
```json
{
  "success": false,
  "data": null,
  "message": "程序发生业务异常:\n匹配到多个智能体，请确认名称"
}
```

### 2. 文件分析 (POST)

适用于长文档、合同文件、需求文档等需要上传文件进行分析的场景。

> **注**: Token 可通过环境变量或 .env 文件配置（见上文）

```bash
curl -X 'POST' \
  'http://192.168.1.213:5000/api/AiReview/AgentAnswerByFiles' \
  -H 'accept: text/plain' \
  -H 'Authorization: Bearer %JIUWU_CORE_TOKEN%' \
  -H 'Content-Type: multipart/form-data' \
  -F 'code=' \
  -F 'name={name}' \
  -F 'docno={docno}' \
  -F 'files=@{file1}' \
  -F 'files=@{file2}'
```

**参数说明**:
| 参数 | 必填 | 说明 |
|-----|-----|------|
| code | 否 | 预留参数，可为空 |
| name | 是 | 智能体名称 |
| docno | 是 | 文档编号 |
| files | 是 | 要上传的文件（支持多个） |

**支持的文件格式**:
- Word: `.doc`, `.docx`
- PDF: `.pdf`
- Excel: `.xls`, `.xlsx`
- 文本: `.txt`

## 响应字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| success | bool | 请求是否成功 |
| data.reviewOpinion | string | 智能体分析结果 |
| data.modelId | string | 使用的模型ID |
| data.provider | number | 服务商编号 |
| message | string | 响应消息 |

## 常见错误处理

1. **匹配到多个智能体**: name 参数需更精确，如"信息化需求评审"而非"信息化"
2. **未获取到智能体**: 检查 name 是否正确，确认智能体是否存在
3. **文件过大**: 建议将大文件拆分或压缩后上传

## 使用示例

### 示例1: 文本分析

```
用户: 请帮我评审这份合同条款："合同金额：10万元，付款方式：先款后货"
操作: 调用文本分析API，name="合同评审"，docno="JWSO20260001"
```

### 示例2: 文件分析

```
用户: 请评审这两个需求文档
操作: 调用文件分析API，name="信息化需求评审"，docno="JWBG20260001"，上传doc1.docx和doc2.docx
```
