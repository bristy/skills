---
name: china-poster-studio
description: 社交海报生成器。一键将文字/文章生成精美海报，支持朋友圈、小红书、抖音等平台。粘贴内容即可生成，无需设计技能。适合运营人员、自媒体、普通用户。
version: 1.0.1
license: MIT-0
metadata: {"openclaw": {"emoji": "🎨", "requires": {"bins": ["python3"], "env": []}}}
dependencies: "pip install pillow"
---

# 社交海报生成器

一键将文字、文章、感悟生成精美海报，适合发朋友圈、小红书、抖音。

## 功能特点

- 🎨 **一键生成**：粘贴内容即可生成精美海报
- 📱 **多平台适配**：朋友圈(1:1)、小红书(3:4)、抖音(9:16)
- 🖼️ **精美背景**：内置10+高质量背景模板
- ✍️ **智能排版**：自动提取标题、要点、金句
- 🌏 **中文优化**：专为中文内容优化
- ⚡ **秒级生成**：无需等待，即刻出图

## 适用场景

| 场景 | 示例 |
|------|------|
| 朋友圈分享 | 新闻观点、读书笔记、生活感悟 |
| 小红书笔记 | 干货总结、产品推荐、经验分享 |
| 抖音素材 | 知识卡片、观点输出 |
| 公众号配图 | 文章摘要、金句海报 |

## 使用方式

### 方式1：粘贴内容（推荐，最稳定）

```
用户：[粘贴一篇文章或一段话]

Agent：自动生成海报
```

### 方式2：简单描述

```
用户：帮我做一个关于"坚持学习"的励志海报

Agent：AI生成内容 + 生成海报
```

### 方式3：提供URL（可选）

```
用户：https://mp.weixin.qq.com/s/xxx

Agent：尝试抓取 → 生成海报
```

---

## 生成流程

```
用户输入
    ↓
识别输入类型（URL/长文本/短描述）
    ↓
获取内容
├─ URL → 尝试抓取（可能失败）
├─ 长文本 → 直接使用
└─ 短描述 → AI扩展生成
    ↓
AI智能处理
├─ 提取标题
├─ 提炼3个核心要点
├─ 提取金句
└─ 选择背景风格
    ↓
生成海报
├─ 加载预制背景图
├─ Pillow精准压字
└─ 导出PNG图片
    ↓
输出成品海报
```

---

## 背景模板

### 内置模板

| 名称 | 风格 | 适用场景 |
|------|------|----------|
| 商务蓝 | 深蓝渐变 | 职场、商业 |
| 极简白 | 纯白底 | 清爽、通用 |
| 深色模式 | 深灰/黑 | 科技、高端 |
| 暖色橙 | 橙色渐变 | 活力、生活 |
| 渐变紫 | 紫色渐变 | 时尚、文艺 |
| 清爽灰 | 浅灰底 | 简约、通用 |
| 墨绿色 | 深绿渐变 | 自然、健康 |
| 酒红色 | 深红渐变 | 正式、庄重 |

### 背景选择

```
用户可以指定：
├─ "用蓝色背景"
├─ "深色模式"
├─ "简洁白色"
└─ 不指定 → AI根据内容自动选择
```

---

## 海报排版

### 标准布局（1:1 朋友圈）

```
┌─────────────────────────┐
│                         │
│     [背景图/渐变]        │
│                         │
│  ┌───────────────────┐  │
│  │                   │  │
│  │    标题（大字）    │  │
│  │    金句/观点      │  │
│  │                   │  │
│  └───────────────────┘  │
│                         │
│  · 要点1                │
│  · 要点2                │
│  · 要点3                │
│                         │
│  ───────────────────    │
│  来源：xxx | 日期       │
└─────────────────────────┘
```

### 竖版布局（3:4 小红书）

```
┌────────────────┐
│                │
│   [背景图]     │
│                │
│  ┌──────────┐ │
│  │  标题    │ │
│  │  金句    │ │
│  └──────────┘ │
│                │
│  · 要点1       │
│  · 要点2       │
│  · 要点3       │
│                │
│  来源 | 日期   │
└────────────────┘
```

---

## 使用示例

### 示例1：新闻观点海报

```
用户：[粘贴一篇关于AI的新闻]

输出：
┌─────────────────────────┐
│  [深蓝色科技背景]        │
│                         │
│  AI正在改变世界          │
│  ─────────────────      │
│  "未来已来，只是分布    │
│   不均匀" - 威廉·吉布森 │
│                         │
│  · 大模型能力持续突破    │
│  · Agent技术走向成熟     │
│  · 开源生态蓬勃发展      │
│                         │
│  AI研究院 | 2026.03.25  │
└─────────────────────────┘
```

### 示例2：读书笔记海报

```
用户：读完《原则》，印象最深的是"痛苦+反思=进步"

输出：
┌─────────────────────────┐
│  [简洁白色背景]          │
│                         │
│  读书笔记                │
│  《原则》                │
│  ─────────────────      │
│  "痛苦+反思=进步"        │
│                         │
│  · 拥抱现实              │
│  · 五步流程法            │
│  · 极度透明              │
│                         │
│  读书笔记 | 2026.03.25  │
└─────────────────────────┘
```

---

## Python代码示例

```python
from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np

class PosterGenerator:
    def __init__(self, assets_dir):
        self.assets_dir = assets_dir
        self.backgrounds = {
            'business_blue': 'business_blue.png',
            'minimal_white': 'minimal_white.png',
            'dark_mode': 'dark_mode.png',
            'warm_orange': 'warm_orange.png',
            'gradient_purple': 'gradient_purple.png',
            'clean_gray': 'clean_gray.png',
        }
    
    def _load_font(self, size):
        """加载中文字体"""
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
            'C:/Windows/Fonts/msyh.ttc',
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except:
                    continue
        return ImageFont.load_default()
    
    def generate_poster(self, title, points, quote, style='business_blue', size_ratio='1:1'):
        """生成海报"""
        
        # 设置尺寸
        sizes = {
            '1:1': (1080, 1080),    # 朋友圈
            '3:4': (1080, 1440),    # 小红书
            '9:16': (1080, 1920),   # 抖音
        }
        width, height = sizes.get(size_ratio, (1080, 1080))
        
        # 加载背景
        bg_path = os.path.join(self.assets_dir, 'backgrounds', 
                               self.backgrounds.get(style, 'business_blue.png'))
        if os.path.exists(bg_path):
            bg = Image.open(bg_path).resize((width, height))
        else:
            bg = Image.new('RGB', (width, height), (30, 50, 100))
        
        draw = ImageDraw.Draw(bg)
        
        # 加载字体
        font_title = self._load_font(64)
        font_normal = self._load_font(36)
        font_small = self._load_font(28)
        
        # 绘制标题
        margin = int(width * 0.08)
        y = int(height * 0.15)
        draw.text((margin, y), title, font=font_title, fill='white')
        
        # 绘制金句
        y += 100
        if quote:
            draw.text((margin, y), f'"{quote}"', font=font_normal, fill=(200, 220, 255))
        
        # 绘制要点
        y += 120
        for point in points[:3]:
            draw.text((margin + 20, y), f'● {point}', font=font_normal, fill='white')
            y += 60
        
        # 底部
        draw.rectangle([(0, height-80), (width, height)], fill=(0, 0, 0, 80))
        draw.text((margin, height-55), 'Generated by AI', font=font_small, fill=(180, 180, 180))
        
        return bg
    
    def save_poster(self, poster, output_path):
        """保存海报"""
        poster.save(output_path, 'PNG', quality=95)
        return output_path
```

---

## 注意事项

- 首次使用需要下载字体（约20MB）
- 内置背景图为预制模板
- 文字精准，无错别字
- 支持中文排版
