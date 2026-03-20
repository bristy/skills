---
name: stock-select
description: 智能选股技能，类似同花顺问财。使用自然语言查询符合条件的股票，如"涨停的股票"、"市盈率小于20"、"连续3天上涨"等。触发词：选股、问财、股票查询、动态选股、筛选股票、符合条件的股票。
---

# 智能选股技能

基于自然语言的智能选股工具，类似同花顺问财。

## API 基础地址

- **Base URL**: `http://39.108.127.26:9998/api`

---

## 一、行情接口 (/quote)

### 1.1 获取单只股票行情
- **接口**: `GET /quote/{stockCode}`
- **说明**: 获取股票实时行情，包括五档买卖
- **示例**: `GET /api/quote/600519`

### 1.2 批量获取股票行情
- **接口**: `POST /quote/batch`
- **说明**: 批量获取多只股票实时行情
- **Body**: `["600519", "000001", "300750"]`

### 1.3 搜索股票
- **接口**: `GET /quote/search?keyword=xxx`
- **说明**: 根据股票代码、简称或名称搜索股票

### 1.4 获取分时数据
- **接口**: `GET /quote/minute/{stockCode}?tradeDate=xxx`
- **说明**: 获取股票分时行情数据，不指定日期则获取当天

### 1.5 获取分时数据（优化传输）
- **接口**: `GET /quote/minute/{stockCode}/optimized?tradeDate=xxx`
- **说明**: 获取分时数据，字段名和数据分离，减少网络传输量

### 1.6 获取集合竞价数据
- **接口**: `GET /quote/call-auction/{stockCode}?tradeDate=xxx`
- **说明**: 获取早盘集合竞价数据（9:15-9:25）

### 1.7 获取集合竞价数据（优化传输）
- **接口**: `GET /quote/call-auction/{stockCode}/optimized?tradeDate=xxx`
- **说明**: 获取集合竞价数据，字段名和数据分离，减少网络传输量

### 1.8 获取股票基础数据
- **接口**: `GET /quote/basic-data/{stockCode}`
- **说明**: 获取融资融券、次新、市盈率、市净率、板块、概念等基础数据

### 1.9 获取历史K线数据
- **接口**: `GET /quote/kline/{stockCode}?interval=D&startDate=xxx&endDate=xxx&appendToday=false`
- **参数**:
  - `interval`: K线周期 (D=日, W=周, M=月, Q=季, Y=年)
  - `startDate`: 开始日期
  - `endDate`: 结束日期
  - `appendToday`: 是否包含今天

### 1.10 获取历史K线数据（优化传输）
- **接口**: `GET /quote/kline/{stockCode}/optimized?interval=D&startDate=xxx&endDate=xxx&appendToday=false`
- **说明**: 获取历史K线数据，字段名和数据分离，减少网络传输量

---

## 二、动态选股接口 (/dynamic-select)

- **接口地址**: `GET /api/dynamic-select/execute`
- **方法**: GET
- **参数**: `sentence` - 自然语言选股条件
- **POST版本**: `POST /api/dynamic-select/execute`，Body: `{"sentence": "xxx"}`

---

## 三、动态选股使用方式

当用户提出选股需求时，将用户的自然语言转换为查询条件，调用 API 并返回结果。

### 查询语法示例

从日志中已知支持的查询模式：

1. **涨跌停类**:
   - `涨停` - 今日涨停的股票
   - `跌停` - 今日跌停的股票
   - `涨幅大于8%未涨停非ST` - 涨幅大但未涨停
   - `非一字涨停非ST` - 非一字板涨停

2. **涨幅类**:
   - `涨幅大于5%`
   - `涨幅小于-3%`
   - `连续3天上涨`
   - `前5日平均涨幅大于20%`

3. **财务指标**:
   - `市盈率小于20`
   - `市净率小于2`
   - `流通市值小于50亿`

4. **组合条件** (用分号分隔):
   - `涨幅大于5%;非ST`
   - `前5日平均涨幅大于20%;前10日涨停次数大于1`
   - `连续5日净买入且主力净流入占比大于10%非ST`

5. **排除条件**:
   - `非ST` - 排除ST股票
   - `非新股` - 排除新股

## 执行流程

1. 解析用户的选股意图
2. 构建查询条件字符串
3. 调用 API: `curl "http://39.108.127.26:9998/api/dynamic-select/execute?sentence=<URL编码的条件>"`
4. 格式化返回结果

## 返回格式

API 返回 JSON，包含：
- `sentence`: 查询条件
- `stocks`: 股票列表（code, name, marketType）
- `totalCount`: 符合条件的股票数量
- `costTime`: 查询耗时(ms)

## 示例对话

**用户**: 帮我找今天涨停的股票
**助手**: 调用接口查询"涨停"，返回涨停股票列表

**用户**: 有没有市盈率低的小盘股？
**助手**: 调用接口查询"市盈率小于20;流通市值小于50亿"

**用户**: 最近3天连续上涨的非ST股票
**助手**: 调用接口查询"连续3天上涨非ST"