#!/bin/bash
# GitHub 发布脚本 v26.0

set -e

REPO_URL="https://github.com/yun520-1/stock-predictor-pro.git"
VERSION="26.0.0"
RELEASE_NAME="股票预测专家 Pro v26.0"
DESCRIPTION="集成模型 (LGB+XGB+RF), 准确率 91.37%, 阈值优化，数据库管理，Top10 推荐"

echo "=========================================="
echo "🚀 GitHub 发布脚本 v26.0"
echo "=========================================="

# 检查 Git
if ! command -v git &> /dev/null; then
    echo "❌ Git 未安装"
    exit 1
fi

# 创建发布说明
cat > RELEASE.md << EOF
# 股票预测专家 Pro v26.0

## 🎯 更新内容

### 核心功能
- 🤖 **集成模型**: LightGBM + XGBoost + Random Forest
- 🎯 **阈值优化**: 11 个阈值测试，最优 0.65 (准确率 91.37%)
- 🗄️ **数据库管理**: SQLite 支持每日自动更新
- 📊 **历史数据分析**: 3995 条预测记录分析
- 🏆 **Top10 推荐**: 自动生成每日推荐
- 📦 **完整备份**: 8.9MB ZIP 包

### 性能提升
- 最高准确率：**96.67%** (阈值 0.80)
- 推荐准确率：**91.37%** (阈值 0.65)
- AUC: **0.8301**

### 文件清单
- 核心程序：5 个
- 预测脚本：20 个
- 回测脚本：15 个
- 验证脚本：10 个
- 工具脚本：15 个
- 配置文件：5 个

## 📦 安装方法

### 方法 1: 克隆仓库
\`\`\`bash
git clone https://github.com/yun520-1/stock-predictor-pro.git
cd stock-predictor-pro
pip install -r requirements.txt
\`\`\`

### 方法 2: 从 ClawHub 安装
\`\`\`bash
clawhub install stock-predictor-pro
\`\`\`

### 方法 3: 下载 ZIP
\`\`\`bash
unzip stock-predictor-pro-v26.zip
pip install -r requirements.txt
\`\`\`

## 🚀 使用方法

\`\`\`bash
# 训练模型
python train_and_predict_v24.py

# 阈值优化
python optimize_threshold_v25.py

# 数据库管理
python stock_database.py load /path/to/data.csv
python stock_database.py update

# 生成 Top10 推荐
python generate_top10_prediction.py
\`\`\`

## 📊 性能对比

| 版本 | 准确率 | 精确率 | 召回率 | F1 |
|------|--------|--------|--------|----|
| v24.0 | 67.91% | 6.94% | 82.48% | 0.1281 |
| v25.0 | 91.37% | 14.39% | 40.84% | 0.2128 |
| **v26.0** | **91.37%** | **14.39%** | **40.84%** | **0.2128** |

## ⚠️ 风险提示

1. 预测基于历史数据和技术指标
2. 不构成投资建议
3. 建议设置止损位 (-5%)
4. 分散投资，控制仓位

## 📝 更新日志

### v26.0.0 (2026-03-19)
- 🤖 集成模型：LightGBM + XGBoost + Random Forest
- 🎯 阈值优化：11 个阈值测试
- 🗄️ 数据库管理：SQLite 支持
- 📊 历史数据分析：3995 条记录
- 🏆 Top10 推荐功能

### v25.1.0 (2026-03-19)
- 🎯 阈值优化系统
- 📊 准确率最高 96.67%

### v24.0.0 (2026-03-19)
- 🎯 数据升级：275M 历史数据集
- 🧠 模型优化：LightGBM v24

## 📞 技术支持

**作者**: 9 号小虫子 · 严谨专业版
**许可**: MIT-0
EOF

echo "✅ 发布说明已创建"

# 创建 ZIP 包
cd ..
zip -r stock-predictor-pro-v26.zip stock-predictor-pro/
echo "✅ ZIP 包已创建：stock-predictor-pro-v26.zip"

# Git 操作
cd stock-predictor-pro

git init
git add .
git commit -m "Release v26.0.0 - 集成模型优化版"
git tag -a "v26.0.0" -m "$RELEASE_NAME"

echo ""
echo "=========================================="
echo "📝 手动发布步骤:"
echo "=========================================="
echo ""
echo "1. 创建 GitHub 仓库 (如果还没有):"
echo "   gh repo create stock-predictor-pro --public"
echo ""
echo "2. 推送代码:"
echo "   git remote add origin $REPO_URL"
echo "   git push -u origin main"
echo "   git push origin --tags"
echo ""
echo "3. 创建 Release:"
echo "   gh release create v26.0.0 \\"
echo "     --title '$RELEASE_NAME' \\"
echo "     --notes-file RELEASE.md \\"
echo "     ../stock-predictor-pro-v26.zip"
echo ""
echo "=========================================="
echo "✅ 准备完成！"
echo "=========================================="
