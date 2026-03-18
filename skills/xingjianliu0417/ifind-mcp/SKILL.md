---
name: ifind-mcp
description: 同花顺iFinD金融数据MCP工具。用于查询A股股票、公募基金、宏观经济和新闻资讯数据。
---

# iFind MCP Skill

同花顺 iFinD MCP 服务，提供专业金融数据查询。

## 配置

### 配置文件位置
`~/.config/mcporter.json`

### MCP 服务器

| 服务器 | 用途 |
|--------|------|
| hexin-ifind-stock | A股股票数据 |
| hexin-ifind-fund | 公募基金数据 |
| hexin-ifind-edb | 宏观经济数据 |
| hexin-ifind-news | 公告资讯 |

### 调用方式

```bash
mcporter call <server>.<tool>
```

## 股票工具 (hexin-ifind-stock)

| 工具 | 说明 |
|------|------|
| get_stock_summary | 股票信息摘要（基本面、行情、估值、行业） |
| search_stocks | 智能选股（按行业、市值、指标筛选） |
| get_stock_perfomance | 历史行情与技术指标 |
| get_stock_info | 基本资料查询 |
| get_stock_shareholders | 股本结构与股东数据 |
| get_stock_financials | 财务数据与指标 |
| get_risk_indicators | 风险指标（alpha、beta、波动率） |
| get_stock_events | 公开披露事件 |
| get_esg_data | ESG评级与报告 |

### 使用示例

```bash
# 查询股票概况
mcporter call hexin-ifind-stock.get_stock_summary query:"贵州茅台财务状况"

# 智能选股
mcporter call hexin-ifind-stock.search_stocks query:"新能源汽车行业市值大于1000亿的股票"

# 历史行情
mcporter call hexin-ifind-stock.get_stock_perfomance query:"宁德时代最近5日涨跌幅"

# 财务数据
mcporter call hexin-ifind-stock.get_stock_financials query:"比亚迪2025年ROE和净利润"
```

## 基金工具 (hexin-ifind-fund)

| 工具 | 说明 |
|------|------|
| search_funds | 模糊基金名称匹配 |
| get_fund_profile | 基金基本资料 |
| get_fund_market_performance | 行情与业绩 |
| get_fund_ownership | 份额与持有人结构 |
| get_fund_portfolio | 投资标的与资产配置 |
| get_fund_financials | 基金财务指标 |
| get_fund_company_info | 基金公司信息 |

### 使用示例

```bash
# 查询基金
mcporter call hexin-ifind-fund.search_funds query:"易方达的科技ETF"

# 基金业绩
mcporter call hexin-ifind-fund.get_fund_market_performance query:"富国天惠近一年收益率"

# 持仓明细
mcporter call hexin-ifind-fund.get_fund_portfolio query:"中欧医疗健康混合A2025年Q2前十大持仓"
```

## 宏观/新闻工具

### hexin-ifind-edb (宏观经济)
```bash
mcporter call hexin-ifind-edb.get_macro_data query:"中国GDP增速"
```

### hexin-ifind-news (新闻资讯)
```bash
mcporter call hexin-ifind-news.get_company_news query:"华为最新公告"
```

## 自然语言查询

iFind MCP 支持自然语言，直接描述你的需求即可：

```bash
# 查股票
"帮我查一下宁德时代的最新市值和PE"
"找出半导体行业ROE最高的前10只股票"

# 查基金
"近一年收益最好的主动权益基金有哪些"
"查询规模超过100亿的货币基金"

# 查宏观
"最近三年的M2增速"
```

## 配置检查

```bash
mcporter list
# 应该显示 4 个服务器健康状态
```
