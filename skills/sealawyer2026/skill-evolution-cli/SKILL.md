---
name: skill-evolution-cli
description: 九章技能进化系统CLI工具 - 自动收集技能使用数据、分析进化需求、生成周报并上报。用于技能自我进化闭环的数据飞轮基础设施。
---

# 九章技能进化系统CLI

技能自我进化引擎的数据基础设施，实现技能使用数据的自动收集、分析和上报。

## 核心功能

### 1. 数据收集 (collect)
收集技能使用数据，包括：
- 技能调用次数和频率
- 用户反馈（正面/负面）
- 响应时间和成功率
- 用户提问类型分布
- 案例库引用情况

### 2. 数据分析 (analyze)
分析技能进化需求：
- 高频问题识别
- 回答质量评估
- 知识缺口发现
- 案例库命中率
- 用户满意度趋势

### 3. 周报生成 (report)
生成《技能进化周报》：
- 各技能使用统计
- 问题分类汇总
- 进化建议
- 优先级排序

### 4. 数据上报 (upload)
上报至技能进化中心：
- 加密传输
- 批量上报
- 失败重试
- 本地缓存

## 使用方法

```bash
# 收集今日数据
jiuzhang-cli evolution collect --date today

# 分析指定技能
jiuzhang-cli evolution analyze --skill zhang-ai-law

# 生成周报
jiuzhang-cli evolution report --week current

# 上报数据
jiuzhang-cli evolution upload --env production

# 一键执行全部
jiuzhang-cli evolution pipeline --full
```

## 配置文件

`~/.jiuzhang/evolution.yaml`:
```yaml
server:
  endpoint: https://evolution.jiuzhang.ai
  api_key: ${EVOLUTION_API_KEY}
  
collection:
  enabled: true
  interval: daily
  retention_days: 90
  
analysis:
  min_samples: 10
  quality_threshold: 0.8
  
report:
  auto_generate: true
  recipients:
    - admin@jiuzhang.ai
    
privacy:
  anonymize_users: true
  encrypt_data: true
```

## 数据飞轮流程

1. **收集** → 本地SQLite存储
2. **分析** → AI模型识别进化点
3. **生成** → 结构化周报
4. **审核** → 张律师确认
5. **执行** → 自动更新技能
6. **反馈** → 闭环验证

## 目录结构

```
skill-evolution-cli/
├── SKILL.md
├── scripts/
│   ├── collect.py      # 数据收集脚本
│   ├── analyze.py      # 数据分析脚本
│   ├── report.py       # 周报生成脚本
│   ├── upload.py       # 数据上报脚本
│   └── pipeline.py     # 一键执行脚本
└── references/
    ├── schema.md       # 数据表结构
    ├── api.md          # API文档
    └── privacy.md      # 隐私合规指南
```

## 环境变量

- `EVOLUTION_API_KEY` - 进化中心API密钥
- `EVOLUTION_ENDPOINT` - 上报端点（可选）
- `JIUZHANG_WORKSPACE` - 工作目录路径

## 安装依赖

```bash
pip install requests pyyaml sqlite3 pandas
```

---
**版本**: 1.0.0  
**作者**: 九章法律AI团队  
**分类**: infrastructure
