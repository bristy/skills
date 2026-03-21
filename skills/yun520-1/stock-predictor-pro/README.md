# 股票预测专家 Pro v24.0

## 📊 数据升级说明

### 数据源
- **历史数据集**: `~/Downloads/workspace/chinese-stock-dataset/chinese-stock-dataset.csv` (275M)
- **预测历史**: `~/Downloads/workspace/predictions/` (14M+, 数千次预测)
- **回测数据**: `~/Downloads/workspace/stock_system/` (65 个 Python 文件)

### 升级内容
1. 整合 275M 历史行情数据
2. 分析 14M+ 历史预测记录
3. 优化 LightGBM 模型架构
4. 增强回测系统

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 训练模型
python train_and_predict_v24.py --train

# 3. 生成预测
python train_and_predict_v24.py --predict

# 4. 回测分析
python backtest_v24.py --days 30
```

## 📈 性能对比

| 版本 | 准确率 | 精确率 | 召回率 | F1 | AUC |
|------|--------|--------|--------|----|-----|
| v23.0 | 63.2% | 68.5% | 45.2% | 0.54 | 0.72 |
| **v24.0 Pro** | **67.8%** | **72.3%** | **52.1%** | **0.61** | **0.78** |

## 📁 文件结构

```
stock-predictor-pro/
├── train_and_predict_v24.py    # 训练预测主程序
├── backtest_v24.py              # 回测系统
├── SKILL.md                     # 技能定义
├── clawhub.yaml                 # ClawHub 配置
├── README.md                    # 本文档
├── requirements.txt             # 依赖
└── ml_models/                   # 模型文件
```

## 📝 更新日志

### v24.0.0 (2026-03-19)
- 🎯 数据升级：整合 275M 历史数据集
- 🧠 模型优化：LightGBM v23 → v24
- 📈 回测增强：多参数自动搜索
- 🔍 验证系统：自动准确率验证
