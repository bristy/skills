#!/bin/bash
# 自媒体技能测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_FILE="$SCRIPT_DIR/data/trending.json"
DRAFTS_DIR="$SCRIPT_DIR/drafts"

echo "🧪 自媒体技能测试"
echo "=========================="
echo ""

# 测试 1: 检查文件结构
echo "测试 1: 检查文件结构..."
required_files=(
    "scripts/fetch-trending.js"
    "scripts/generate-content.js"
    "scripts/format-platform.js"
    "scripts/save-draft.js"
    "templates/wechat.md"
    "templates/xiaohongshu.md"
    "templates/douyin.md"
    "package.json"
    "SKILL.md"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file 缺失"
        exit 1
    fi
done
echo ""

# 测试 2: 抓取热搜
echo "测试 2: 抓取热搜..."
node "$SCRIPT_DIR/scripts/fetch-trending.js" > /dev/null 2>&1
if [ -f "$DATA_FILE" ]; then
    echo "  ✅ 热搜抓取成功"
else
    echo "  ❌ 热搜抓取失败"
    exit 1
fi
echo ""

# 测试 3: 保存草稿
echo "测试 3: 保存草稿..."
node "$SCRIPT_DIR/scripts/save-draft.js" --title "测试话题" --platform all > /dev/null 2>&1
draft_count=$(ls -1 "$DRAFTS_DIR"/*.md 2>/dev/null | wc -l)
if [ "$draft_count" -gt 0 ]; then
    echo "  ✅ 草稿保存成功 ($draft_count 个)"
else
    echo "  ❌ 草稿保存失败"
    exit 1
fi
echo ""

# 测试 4: 查看草稿列表
echo "测试 4: 查看草稿列表..."
node "$SCRIPT_DIR/scripts/save-draft.js" --list > /dev/null 2>&1
echo "  ✅ 草稿列表显示成功"
echo ""

# 清理测试草稿
echo "清理测试草稿..."
rm -f "$DRAFTS_DIR"/*测试话题*.md
echo "  ✅ 已清理"
echo ""

echo "=========================="
echo "✅ 所有测试通过！"
echo ""
echo "💡 提示：运行 ./install.sh 安装技能"
echo ""
