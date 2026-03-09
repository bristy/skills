# Skill Hub Gateway（简体中文）

默认 API 地址：`https://gateway-api.binaryworks.app`

英文文档：`SKILL.md`

## 首次接入（install_code）

1. 调用 `POST /agent/install-code/issue`，请求体可用 `{"channel":"local"}` 或 `{"channel":"clawhub"}`。
2. 读取 `data.install_code`。
3. 调用 `POST /agent/bootstrap`，请求体：`{"agent_uid":"<agent_uid>","install_code":"<install_code>"}`。
4. 读取 `data.api_key`，后续通过 `X-API-Key` 或 `Authorization: Bearer <api_key>` 调用。

## 运行时协议（V2）

- 提交：`POST /skill/execute`
- 轮询：`GET /skill/runs/:run_id`
- 图片类能力要求 `image_url` 为可直接下载图片的直链（返回头应为 `image/*`），不能是网页地址。
- 终态：`succeeded` / `failed`
- `succeeded` 返回 `output`
- `failed` 返回 `error.code`、`error.message`

## 能力 ID

- `human_detect`
- `image_tagging`
- `tts_report`
- `embeddings`
- `reranker`
- `asr`
- `tts_low_cost`
- `markdown_convert`
