#!/bin/bash
# 自媒体技能安装脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🦆 自媒体技能安装脚本"
echo "========================"
echo ""

# 检查前置条件
echo "检查前置条件..."

if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js"
    exit 1
fi
echo "  ✅ Node.js 已安装"

# 设置脚本权限
echo "设置脚本权限..."
chmod +x "$SCRIPT_DIR/scripts/"*.js
chmod +x "$SCRIPT_DIR/tests/"*.sh
echo "  ✅ 脚本已设置为可执行"

# 创建必要目录
echo "创建目录..."
mkdir -p "$SCRIPT_DIR/drafts"
mkdir -p "$SCRIPT_DIR/data"
echo "  ✅ 目录已创建"

echo ""
echo "========================"
echo "✅ 安装完成！"
echo ""
echo "使用说明："
echo "  1. 抓取热搜：$SCRIPT_DIR/scripts/fetch-trending.js"
echo "  2. 生成内容：$SCRIPT_DIR/scripts/generate-content.js --topic \"话题\""
echo "  3. 格式适配：$SCRIPT_DIR/scripts/format-platform.js --all"
echo "  4. 查看草稿：$SCRIPT_DIR/scripts/save-draft.js --list"
echo ""
echo "示例："
echo "  ./scripts/fetch-trending.js"
echo "  ./scripts/generate-content.js --topic \"AI Agent\" --save"
echo "  ./scripts/format-platform.js --all"
echo ""
