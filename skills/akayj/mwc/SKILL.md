---
name: mac-wallpaper-changer
description: 自动更换 Mac 壁纸并智能推荐。当用户提到换壁纸、更新桌面、Mac 壁纸、自动壁纸、壁纸推荐时使用此技能。支持定时任务、喜好学习、智能推荐。
compatibility: macOS, uv
---

# Mac 壁纸随心换

自动为 macOS 更换高质量壁纸，通过评分学习偏好并智能推荐。

## Available scripts

- `scripts/change-wallpaper.py` — 下载并设置壁纸（Bing/Unsplash/Picsum 多源支持）
- `scripts/analyze-preferences.py` — 分析历史评分，统计偏好分布
- `scripts/recommend-wallpaper.py` — 基于偏好数据智能推荐壁纸
- `scripts/my-location.py` — 获取/设置位置，支持时间色调建议

## Workflow

```bash
# 立即换壁纸
uv run scripts/change-wallpaper.py

# 指定分类/色调/源
uv run scripts/change-wallpaper.py --category mountain --color-tone dark
uv run scripts/change-wallpaper.py --source bing

# 换壁纸并评分（用于学习偏好）
uv run scripts/change-wallpaper.py --ask-rating

# 查看偏好统计
uv run scripts/analyze-preferences.py

# 获取智能推荐
uv run scripts/recommend-wallpaper.py

# 查看参数帮助
uv run scripts/change-wallpaper.py --help
```

## Data storage

所有数据存储在 `~/wallpaper-daily/`：

- `YYYY-MM-DD/` — 按日期存放的壁纸文件
- `preferences.parquet` — 评分和偏好数据
- `logs/` — 运行日志

## Cron setup

```bash
crontab -e
# 添加（每天 10:30 自动换壁纸）
30 10 * * * cd ~/.agents/skills/mac-wallpaper-changer && uv run scripts/change-wallpaper.py
```

## Troubleshooting

**壁纸不生效（macOS Tahoe 26+）**：脚本已自动处理，使用 PyObjC + killall WallpaperAgent 方案。

**某些 Spaces 未刷新**：系统设置 > 墙纸 > 开启"在所有空间中显示"

**权限问题**：系统设置 > 隐私与安全性 > 自动化 > 终端/Finder

**查看日志**：`tail -f ~/wallpaper-daily/logs/change-wallpaper-*.log`

## References

- `references/wallpaper-sources.md` — 壁纸源配置详情
