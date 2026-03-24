---
name: pi-ppt
description: 使用PI(Presentation Intelligence)提供的服务生成PPT.
---

# Pi PPT 生成

## 功能
1. 生成PPT.

## Setup
使用 PI 的服务前，须先从 PI 平台获取 `PIPPT_APP_ID` 与 `PIPPT_APP_SECRET`,并设置为环境变量。

```bash
export PIPPT_APP_ID="your_app_id"
export PIPPT_APP_SECRET="your_api_secret"
```

> 建议将上述 export 语句写入 `~/.zshrc` 或 `~/.bashrc`，避免每次重开终端失效。

## 凭证预检

每次调用 API 前，先确认凭证可用。如果环境变量未设置，停止操作并提示用户按 Setup 步骤配置。

```bash
if [ -z "$PIPPT_APP_ID" ] || [ -z "$PIPPT_APP_SECRET" ]; then
  echo "缺少PIPPT_APP_ID或PIPPT_APP_SECRET，请按 Setup 步骤配置环境变量 PIPPT_APP_ID 和 PIPPT_APP_SECRET"
  exit 1
fi
```

## 生成PPT
执行以下脚本
```bash
python <skill-dir>/scripts/generate_pi_ppt.py --content  --language --cards --file
```
其中输入参数:
   content(str, 必填): 主题和描述，比如"生成一个关于中国GPU厂商介绍的PPT，商务严肃风格"。
   cards(int, 非必填): 期望的PPT页数，比如 10, 默认为8。如果要根据上传的文档生成PPT，则不能指定PPT页数，因为PPT页数根据上传的文档内容决定。
   language(str, 比填): 期望的PPT的语言，'zh': 中文，'en': 英文，默认为'zh'.
   file(str, 可填): 要上传的文档的路径，比如："/Users/jack/download/weekly_report_20250304.doc", 支持的文档类型包括: .doc/.docx/.txt/.md/.pdf/.pptx/.ppt, 不支持其他类型的文件类型，且仅限于上传一个文档。 

完整的命令举例:

**根据上传文档生成**（页数由文档内容决定，不要传 `--cards`）：

```bash
python "<skill-dir>/scripts/generate_pi_ppt.py" \
  --pippt_app_id $PIPPT_APP_ID \
  --pippt_app_secret $PIPPT_APP_SECRET \
  --content "根据附件内容生成一份结构清晰的商务汇报PPT" \
  --language zh \
  --file "/Users/you/Documents/quarterly_review.docx"
```

**根据一句话 / 主题生成**（可指定页数）：

```bash
python "<skill-dir>/scripts/generate_pi_ppt.py" \
  --pippt_app_id $PIPPT_APP_ID \
  --pippt_app_secret $PIPPT_APP_SECRET \
  --content "生成一个关于中国GPU厂商介绍的PPT，商务严肃风格" \
  --language zh \
  --cards 10
```
## 注意
- 生成一个PPT大概要耗时2-3分钟，需要提醒用户耐心等待。
