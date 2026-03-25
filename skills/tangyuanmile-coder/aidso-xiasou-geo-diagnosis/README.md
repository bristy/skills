# geo_report_single_api_poll_v3

这是一个基于动态单一接口轮询的 OpenClaw Skill，用于：

1. 识别品牌 GEO 报告类请求
2. 先提示：本次诊断将消耗 20 积分，是否确认
3. 用户确认后，立刻先返回：
   `正在为「{brandName}」诊断中，大约需要3~10分钟，请稍后；`
4. 然后动态提取品牌名并请求接口：
   `GET https://testapi.aidso.com/openapi/skills/band_report/md?brandName=品牌名称`
5. 如果接口返回“正在处理中，请稍后”，继续轮询
6. 一旦接口返回 markdown 报告正文，则停止轮询
7. 将完整 markdown 文本内容直接返回给用户，不保存成 `.md` 文件，不作为附件返回
8. 如果接口返回文件或文件链接，仍按附件方式返回

## 文件说明
- `SKILL.md`：完整交互流程说明
- `meta.json`：skill 配置
- `run.py`：轮询动态接口获取报告
- `README.md`：说明文档

## 依赖
只依赖 Python 3 标准库，无需 pip install。

## 动态接口说明
### 获取品牌诊断报告
固定接口地址：
```bash
https://testapi.aidso.com/openapi/skills/band_report/md
```

动态请求方式：
```bash
GET "https://testapi.aidso.com/openapi/skills/band_report/md?brandName=品牌名称"
```

参数：
- `brandName`: 品牌名称（必填，最多50字符）

## 可选环境变量
- `GEO_API_TOKEN`
- `GEO_AUTH_HEADER`，默认 `Authorization`
- `GEO_AUTH_PREFIX`，默认 `Bearer `
- `GEO_BRAND_PARAM`，默认 `brandName`
- `GEO_POLL_INTERVAL_SEC`，默认 `8`
- `GEO_POLL_TIMEOUT_SEC`，默认 `900`

## 手动测试
```bash
python3 run.py poll_report 露露
python3 run.py poll_report Tesla
```

## 返回方式
脚本会按下面逻辑处理：
- 接口返回 `正在处理中，请稍后`：继续轮询
- 接口返回 markdown 文本：直接返回完整 markdown 文本
- 接口返回 JSON 且包含 `mdUrl/pdfUrl/fileUrl`：直接返回链接
- 接口返回二进制文件：保存后返回附件路径
