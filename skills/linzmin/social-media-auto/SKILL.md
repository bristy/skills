---
name: social-media-auto
version: 1.0.0
description: 自媒体内容生成技能 - 热点抓取 + AI 创作 + 多平台适配
author: linzmin1927
---

# 自媒体内容生成技能

> 📱 你的私人内容创作助手，让自媒体运营更高效！

---

## 🎯 功能特性

- ✅ 微博热搜 + 知乎热榜自动抓取
- ✅ AI 内容生成（支持多种语气和长度）
- ✅ 多平台格式适配（公众号/小红书/抖音）
- ✅ 草稿管理和版本控制
- ✅ 一键生成多平台版本

---

## 🚀 快速开始

### 1. 抓取热搜

```bash
./scripts/fetch-trending.js
```

### 2. 生成内容

```bash
./scripts/generate-content.js --topic "AI Agent" --save
```

### 3. 多平台适配

```bash
./scripts/format-platform.js --all
```

### 4. 查看草稿

```bash
./scripts/save-draft.js --list
```

---

## 📋 命令详解

### 抓取热搜 `fetch-trending.js`

```bash
# 抓取所有平台
./scripts/fetch-trending.js

# 只看微博
./scripts/fetch-trending.js --weibo

# 只看知乎
./scripts/fetch-trending.js --zhihu

# 查看已抓取结果
./scripts/fetch-trending.js --output
```

### 生成内容 `generate-content.js`

```bash
# 生成内容并预览
./scripts/generate-content.js --topic "AI Agent"

# 生成并保存
./scripts/generate-content.js --topic "时间管理" --save

# 指定平台和长度
./scripts/generate-content.js --topic "副业" --platform wechat --length long

# 指定语气
./scripts/generate-content.js --topic "科技" --tone humorous --save
```

**参数说明：**

| 参数 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `--topic` | 任意话题 | 必填 | 文章主题 |
| `--platform` | wechat/xiaohongshu/douyin/all | all | 目标平台 |
| `--length` | short/medium/long | medium | 文章长度 |
| `--tone` | professional/casual/humorous | professional | 文章语气 |

### 格式适配 `format-platform.js`

```bash
# 转换所有草稿
./scripts/format-platform.js --all

# 转换指定文件
./scripts/format-platform.js --input drafts/xxx.md --platform xiaohongshu
```

### 保存草稿 `save-draft.js`

```bash
# 列出所有草稿
./scripts/save-draft.js --list

# 查看指定草稿
./scripts/save-draft.js --view 2026-03-26_AI_Agent.md

# 保存新草稿
./scripts/save-draft.js --title "新话题" --platform all
```

---

## 📁 文件结构

```
social-media-auto/
├── scripts/
│   ├── fetch-trending.js      # 抓取热搜
│   ├── generate-content.js    # 生成内容
│   ├── format-platform.js     # 格式适配
│   └── save-draft.js          # 保存草稿
├── templates/
│   ├── wechat.md              # 公众号模板
│   ├── xiaohongshu.md         # 小红书模板
│   └── douyin.md              # 抖音模板
├── drafts/                    # 草稿目录
├── data/
│   └── trending.json          # 热搜数据
└── tests/
```

---

## 📊 平台特点

### 微信公众号
- **格式：** Markdown
- **长度：** 800-1500 字
- **语气：** 专业/深度
- **特点：** 结构清晰，有深度

### 小红书
- **格式：** Emoji + 短段落
- **长度：** 300-800 字
- **语气：** 轻松/分享
- **特点：** 多 emoji，多标签

### 抖音
- **格式：** 视频脚本
- **长度：** 60-180 秒
- **语气：** 口语化
- **特点：** 开场抓人，节奏快

---

## 💡 使用场景

### 场景 1：追热点

```bash
# 抓取热搜
./scripts/fetch-trending.js

# 选择热点话题生成内容
./scripts/generate-content.js --topic "AI Agent 爆发" --save

# 生成多平台版本
./scripts/format-platform.js --all
```

### 场景 2：日常更新

```bash
# 直接生成内容
./scripts/generate-content.js --topic "时间管理技巧" --platform wechat --save
```

### 场景 3：一鱼多吃

```bash
# 生成一个话题
./scripts/generate-content.js --topic "副业推荐" --platform all --save

# 自动适配三个平台格式
./scripts/format-platform.js --all
```

---

## 🔧 技术要点

### 热搜抓取
- **微博热搜：** 通过阿里云搜索 MCP 获取
- **知乎热榜：** 通过阿里云搜索 MCP 获取
- **更新频率：** 建议每小时抓取一次

### AI 生成
- **调用方式：** 阿里云 MCP
- **支持语气：** 专业/轻松/幽默
- **支持长度：** 短/中/长

### 格式适配
- **规则引擎：** 基于模板的字符串替换
- **Emoji 添加：** 关键词匹配
- **脚本转换：** 结构化分段

---

## ❓ 常见问题

### Q: 生成内容太模板化怎么办？

**A:** 可以：
1. 调整 `--tone` 参数，使用 `humorous` 语气
2. 手动修改生成的草稿
3. 自定义模板文件

### Q: 如何自定义模板？

**A:** 编辑 `templates/` 目录下的模板文件，使用 `{{变量}}` 语法。

### Q: 支持其他平台吗？

**A:** 目前支持微信/小红书/抖音。其他平台可以自定义模板。

### Q: AI 生成准确吗？

**A:** AI 生成提供初稿，建议人工审核和修改后再发布。

---

## 📝 更新日志

### v1.0.0 (2026-03-26)
- ✅ 微博热搜 + 知乎热榜抓取
- ✅ AI 内容生成
- ✅ 多平台格式适配
- ✅ 草稿管理
- ✅ 三种模板（微信/小红书/抖音）

---

## 🦆 作者

鸭鸭 (Yaya) - 你的私人内容创作助手

## 📄 许可证

MIT-0 License
