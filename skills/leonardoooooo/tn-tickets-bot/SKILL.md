---
name: tuniu-ticket
description: 途牛门票助手 - 通过 exec + curl 调用 MCP 实现景点门票查询、订单创建。适用于用户询问某景点门票价格、票型或提交门票订单时使用。
version: 1.0.0
metadata: {"openclaw": {"emoji": "🎫", "category": "travel", "tags": ["途牛", "门票", "景点", "预订"], "requires": {"bins": ["curl"]}, "env": {"TUNIU_API_KEY": {"type": "string", "description": "途牛开放平台 API key，用于 apiKey 请求头", "required": true}}}}
---

# 途牛门票助手

当用户询问景点门票查询或预订时，使用此 skill 通过 exec 执行 curl 调用途牛门票 MCP 服务。

## 运行环境要求

本 skill 通过 **shell exec** 执行 **curl** 向 MCP endpoint 发起 HTTP POST 请求，使用 JSON-RPC 2.0 / `tools/call` 协议。**运行环境必须提供 curl 或等效的 HTTP 调用能力**，否则无法调用 MCP 服务。

## 隐私与个人信息（PII）说明

下单功能会将用户提供的**个人信息**（取票人姓名、手机号、出游人姓名、手机号、证件号等）通过 HTTP POST 发送至途牛门票 MCP 服务，以完成订单创建。使用本 skill 即表示用户知晓并同意上述 PII 被发送到外部服务。请勿在日志或回复中暴露用户个人信息。

## 适用场景

- 按景点名称查询门票（票型、价格）
- 用户确认后创建门票订单

## 配置要求

### 必需配置

- **TUNIU_API_KEY**：途牛开放平台 API key，用于 `apiKey` 请求头

用户需在[途牛开放平台](https://open.tuniu.com/mcp)注册并获取上述密钥。

### 可选配置

- **TICKET_MCP_URL**：MCP 服务地址，默认 `https://openapi.tuniu.cn/mcp/ticket`

## 调用方式

**直接调用工具**：使用以下请求头调用 `tools/call` 即可：

- `apiKey: $TUNIU_API_KEY`
- `Content-Type: application/json`
- `Accept: application/json, text/event-stream`

## 可用工具

**重要**：下方示例中的参数均为占位，调用时需**根据用户当前需求**填入实际值（景点名、日期、产品 ID、出游人信息等），勿直接照抄示例值。

### 1. 门票查询 (query_cheapest_tickets)

**入参**：`scenic_name`（必填，景点名称，如「南京中山陵」）。

**返回**：`scenic_name`、`tickets`（门票列表，含 productId、resId、价格、票型等）。**productId 和 resId 为下单必填，需保留供 create_ticket_order 使用。**

**触发词**：某景点门票、查门票、门票价格、南京中山陵多少钱

```bash
curl -s -X POST "${TICKET_MCP_URL:-https://openapi.tuniu.cn/mcp/ticket}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "apiKey: $TUNIU_API_KEY" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"query_cheapest_tickets","arguments":{"scenic_name":"<用户指定的景点名称>"}}}'
```

### 2. 创建订单 (create_ticket_order)

**前置条件**：必须先调用 `query_cheapest_tickets` 获取门票产品；从返回的 `tickets` 中选取用户要购买的产品，拿到 `productId` 和 `resId`。

**必填参数**：product_id、resource_id（来自 query_cheapest_tickets）、depart_date（YYYY-MM-DD）、adult_num、contact_name、contact_mobile、tourist_1_name、tourist_1_mobile、tourist_1_cert_type、tourist_1_cert_no，其中出游人1的姓名、手机号、证件类型、证件号码为必传项。

**出游人**：出游人总数应等于 adult_num + child_num；至少 1 位，最多 5 位。

**触发词**：预订、下单、订门票、我要订、提交订单

```bash
# product_id、resource_id 从最近一次 query_cheapest_tickets 结果取；用户信息按用户需求填
curl -s -X POST "${TICKET_MCP_URL:-https://openapi.tuniu.cn/mcp/ticket}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "apiKey: $TUNIU_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "create_ticket_order",
      "arguments": {
        "product_id": <query_cheapest_tickets 返回的 productId>,
        "resource_id": <query_cheapest_tickets 返回的 resId>,
        "depart_date": "<用户指定的出游日期 YYYY-MM-DD>",
        "adult_num": 1,
        "contact_name": "<取票人姓名>",
        "contact_mobile": "<取票人手机号>",
        "tourist_1_name": "<出游人1姓名>",
        "tourist_1_mobile": "<出游人1手机号>",
        "tourist_1_cert_type": "<出游人1证件类型，如身份证>",
        "tourist_1_cert_no": "<出游人1证件号码>"
      }
    }
  }'
```

（product_id、resource_id 必须来自最近一次 query_cheapest_tickets 的返回，不可用示例值。）

**可选参数**：child_num、contact_cert_type、contact_cert_no，以及 tourist_2～5 的姓名、手机、证件信息。

## 响应处理

### 成功响应

```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [{"type": "text", "text": "..."}]
  },
  "id": 2
}
```

- 工具结果在 **`result.content[0].text`** 中。`text` 为 **JSON 字符串**，需先 `JSON.parse(result.content[0].text)` 再使用。
- 解析后为业务对象：
  - **门票查询**（query_cheapest_tickets）：`scenic_name`、`tickets`（含 productId、resId、价格、票型等）。
  - **创建订单**（create_ticket_order）：`success`、`orderId`、`paymentUrl`、`message`。成功时 `paymentUrl` 为 `https://m.tuniu.com/u/gt/order/{orderId}?orderType=75`，**必须提醒用户点击完成支付**。
- 错误时解析后为 `{ "error": "错误信息" }` 或 `{ "success": false, "msg": "..." }`，从对应字段取提示文案。

### 错误响应

**1. 传输/会话层错误**（无 `result`，仅有顶层 `error`）：

```json
{
  "jsonrpc": "2.0",
  "error": {"code": -32000, "message": "..."},
  "id": null
}
```

**2. 工具层错误**（HTTP 200，有 `result`）：`result.content[0].text` 解析后为 `{ "success": false, "errorCode": "...", "msg": "..." }`。例如：
- `MISSING_USER_ID`：缺少用户ID信息
- `INVALID_CONTACT`：取票人姓名或手机号为空
- `INVALID_TOURISTS`：至少需要一名出游人
- `TOURIST_COUNT_MISMATCH`：出游人数量与 adult_num + child_num 不匹配

## 输出格式建议

- **门票列表**：以表格或清单展示票型、价格、productId/resId（供下单使用）；提示用户可预订
- **下单成功**：明确写出订单号、支付链接（`https://m.tuniu.com/u/gt/order/{orderId}?orderType=75`）、出游日期、景点与票型；**必须提醒用户点击支付链接完成付款**

## 使用示例

以下示例中，所有参数均从**用户表述或上一轮结果**中解析并填入，勿用固定值。

**用户**：南京中山陵门票多少钱？

**AI 执行**：scenic_name=南京中山陵，调用 query_cheapest_tickets。解析 result.content[0].text，整理门票列表（票型、价格）回复，并保留 productId、resId 供下单。

**用户**：3 月 18 号去，订一张成人票，联系人张三 13800138000，出游人李四 13900139000

**AI 执行**：从上一轮 query_cheapest_tickets 取 product_id、resource_id；depart_date=2026-03-18，adult_num=1，contact_name=张三、contact_mobile=13800138000，tourist_1_name=李四、tourist_1_mobile=13900139000。成功后回复订单号、支付链接，并提醒用户点击完成付款。

## 注意事项

1. **密钥安全**：不要在回复或日志中暴露 TUNIU_API_KEY
2. **PII 安全**：取票人、出游人姓名、手机号、证件号仅在订单创建时发送至 MCP 服务，勿在日志或回复中暴露
3. **认证**：若遇协议或认证错误，可重试或检查 TUNIU_API_KEY
4. **日期格式**：depart_date 为 YYYY-MM-DD
5. **下单前**：product_id、resource_id 必须来自最近一次 query_cheapest_tickets 的返回；若间隔较长，建议重新查询刷新
6. **出游人数量**：出游人总数必须等于 adult_num + child_num，至少 1 位，最多 5 位
7. **支付提醒**：下单成功后必须提示用户点击 paymentUrl 完成支付