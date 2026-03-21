# 股票预测系统 - 使用指南

## 📦 安装

```bash
# 1. 安装依赖
pip install pandas numpy lightgbm xgboost scikit-learn akshare tqdm

# 2. 技能已安装在
~/.openclaw/skills/stock-predictor-pro/
```

## 🚀 快速开始

### 1. 初始化数据库

```bash
# 从 CSV 加载历史数据
python3 stock_database.py load /path/to/chinese-stock-dataset.csv
```

### 2. 每日自动更新

```bash
# 下载最新数据并更新数据库
python3 daily_update_cron.py
```

### 3. 生成推荐

```bash
# 生成今日和明日推荐
python3 generate_recommendation.py
```

### 4. 训练模型

```bash
# 重新训练模型
python3 predict_and_verify_v25.py
```

### 5. 阈值优化

```bash
# 测试不同阈值效果
python3 optimize_threshold_v25.py
```

## 📁 文件说明

| 文件 | 功能 |
|------|------|
| `stock_database.py` | 数据库管理（加载/更新/查询） |
| `generate_recommendation.py` | 生成股票推荐 |
| `daily_update_cron.py` | 每日自动更新 |
| `predict_and_verify_v25.py` | 模型训练与验证 |
| `optimize_threshold_v25.py` | 阈值优化 |

## 📊 输出位置

- **数据库**: `/home/admin/openclaw/workspace/stock_data.db`
- **推荐报告**: `/home/admin/openclaw/workspace/stock-recommendations/`
- **模型文件**: `/home/admin/openclaw/workspace/skills/stock-predictor-pro/ml_models/`

## ⏰ 定时任务

添加 cron 任务实现每日自动更新：

```bash
# 每天收盘后 (15:30) 自动更新
crontab -e

# 添加以下行
30 15 * * 1-5 python3 /home/admin/openclaw/workspace/skills/stock-predictor-pro/daily_update_cron.py >> /var/log/stock_update.log 2>&1
```

## 📈 模型性能

| 指标 | 数值 |
|------|------|
| 准确率 | 91.37% (阈值 0.65) |
| AUC | 0.8301 |
| 训练股票 | 200 只 |
| 特征数 | 26 个 |

## ⚠️ 风险提示

1. 股市有风险，投资需谨慎
2. 模型基于历史数据，无法预测突发事件
3. 建议结合其他分析方法
4. 做好止损和仓位管理

## 📞 技术支持

如有问题，请查看：
- SKILL.md - 技能定义
- analysis_report.md - 性能分析报告
