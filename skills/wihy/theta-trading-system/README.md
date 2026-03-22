# Theta量化交易系统

**基于真实A股涨停股数据的智能选股系统**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)

---

## 📖 简介

Theta System是一个基于真实A股涨停股数据的量化交易系统，- 真实数据驱动
- 机器学习模型
- 4维度评分
- 风险控制

---

## 🎯 核心功能

### 1. 数据采集
- AkShare实时获取涨停股
- SQLite持久化存储
- 每日自动更新

### 2. 模型训练
- GradientBoosting算法
- 14个特征工程
- 自动优化参数

### 3. 智能选股
- 100分制综合评分
- 技术+资金+基本+情绪
- 自动生成推荐

### 4. 风险控制
- 严格止损-5%
- 分批止盈+10%/+15%
- 仓位管理

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://clawhub.com/skills/theta-trading-system.git
cd theta-trading-system

# 安装依赖
pip install -r requirements.txt
```

### 使用

```python
# 初始化数据
python scripts/daily_data_update.py

# 训练模型
python scripts/train_with_real_data_v2.py

# 生成推荐
python scripts/theta_daily_recommendation.py
```

---

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| R²分数 | 98.18% | 模型拟合度 |
| 数据量 | 843条 | 真实涨停股数据 |
| 覆盖股票 | 538只 | A股市场覆盖 |
| 更新频率 | 每日 | 自动更新 |

---

## 📁 项目结构

```
theta-trading-system/
├── SKILL.md                      # 技能文档
├── README.md                     # 本文件
├── requirements.txt              # 依赖
├── scripts/                      # 脚本
│   ├── daily_data_update.py     # 每日数据更新
│   ├── fetch_real_stock_data.py # 数据采集
│   └── train_with_real_data_v2.py # 模型训练
├── models/                       # 模型文件
├── data/                         # 数据文件
└── docs/                         # 文档
```

---

## ⚙️ 配置

### 数据库配置
```python
DB_PATH = "/path/to/real_stock_data.db"
```

### 模型配置
```python
MODEL_PATH = "/path/to/models/theta_final/"
```

### 风险控制
```python
MAX_POSITION = 0.2      # 单只最大20%
TOTAL_POSITION = 0.6    # 总仓位60%
STOP_LOSS = 0.05        # 止损-5%
TAKE_PROFIT_1 = 0.10    # 止盈1 +10%
TAKE_PROFIT_2 = 0.15    # 止盈2 +15%
```

---

## 📈 使用示例

### 获取推荐股票

```python
from theta_trading import ThetaSystem

# 初始化
theta = ThetaSystem()

# 获取推荐
recommendations = theta.get_recommendations(top_n=10)

# 打印结果
for stock in recommendations:
    print(f"{stock['code']} {stock['name']}: {stock['score']}分")
```

### 分析单只股票

```python
# 分析股票
analysis = theta.analyze_stock('600519')

print(f"评分: {analysis['score']}/100")
print(f"建议: {analysis['recommendation']}")
print(f"止损: {analysis['stop_loss']}")
print(f"止盈: {analysis['take_profit']}")
```

---

## ⚠️ 重要提示

### 数据局限
- 当前仅16个交易日数据
- 建议积累至50+个交易日
- 模型可能存在过拟合

### 风险提示
- 所有建议仅供参考
- 不构成投资建议
- 股市有风险，投资需谨慎

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License

---

## 📞 联系方式

- **ClawHub**: https://clawhub.com/skills/theta-trading-system
- **问题反馈**: 请在ClawHub提交Issue

---

**Theta Team** - 让量化交易更简单 🚀
