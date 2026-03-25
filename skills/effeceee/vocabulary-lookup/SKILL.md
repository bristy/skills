---
name: vocabulary-lookup
description: 从GPT4词典库查询单词详情，支持词义、例句、词根、记忆技巧等功能
author:
  name: Maosi English Team
  github: https://github.com/effecE
homepage: https://clawhub.com
metadata:
  {
    "openclaw":
      {
        "version": "1.0.0",
        "emoji": "📚",
        "tags": ["english", "vocabulary", "learning", "gpt4"],
        "requires": { "bins": ["python3"] },
        "install":
          [
            {
              "id": "pip",
              "kind": "pip",
              "package": "edge-tts",
              "label": "Install edge-tts (optional, for audio)",
            },
          ],
      },
  }
---

# Vocabulary Lookup - GPT4单词库查询

从8714词GPT4词典中查询单词详细信息。

## 数据来源
- 路径：`/root/.openclaw/workspace-knowledgegao/notes/resources/documents/dictionary-by-gpt4.json`
- 格式：NDJSON，每行一个JSON
- 词数：8,714个单词
- 数据内容：词义、例句、词根、词缀、文化背景、记忆技巧、小故事

## 作者
**Maosi English Team**

## 使用方法

```bash
# 查询单个单词
python3 vocabulary_lookup.py --word camel

# 查询多个单词
python3 vocabulary_lookup.py --word apple --word banana

# 模糊搜索（部分匹配）
python3 vocabulary_lookup.py --search "app"

# 随机抽取N个单词
python3 vocabulary_lookup.py --random 5

# 按首字母筛选
python3 vocabulary_lookup.py --starts-with a --limit 10
```

## 输出内容
每个单词包含：
- 分析词义
- 3+个例句（附中文翻译）
- 词根分析
- 词缀分析
- 发展历史和文化背景
- 单词变形
- 记忆辅助
- 小故事（中英文）

## 技术实现
- 使用 ndjson 库逐行读取（不加载整个17MB文件到内存）
- 哈希表快速查找
- 支持模糊匹配和随机抽取

## 安全设置
- ✅ 只读操作：仅读取本地JSON文件
- ✅ 无网络请求
- ✅ 无外部API调用
- ✅ 无文件写入操作
- ✅ 命令行参数验证
