# 小宿智能搜索 V2 API 文档

## 请求

- **方法**: GET
- **URL**: `https://searchapi.xiaosuai.com/search/{Endpoint}/smart`
- **Headers**:
  - `Authorization: Bearer {AK}`
  - `Pragma: no-cache`（可选，禁用10分钟结果缓存）

## 请求参数（Query String）

| 参数 | 必填 | 类型 | 描述 |
|------|------|------|------|
| q | Y | String | 搜索查询词，不能为空 |
| count | N | Short | 返回结果数量，默认10，最大50（枚举：10/20/30/40/50） |
| freshness | N | String | 时间过滤：Day/Week/Month |
| offset | N | Short | 分页偏移量，默认0 |
| enableContent | N | bool | true=返回长摘要，默认false |
| contentType | N | String | 长摘要格式：HTML/MARKDOWN/TEXT（默认TEXT） |
| contentTimeout | N | Float | 长摘要超时秒数，默认0，最大10s |
| mainText | N | bool | true=返回动态摘要关键片段，默认false |
| sites | N | String | 限定站点（host格式，如 baijiahao.baidu.com） |
| blockWebsites | N | String | 排除站点（host格式） |

## 返回结构

```json
{
  "queryContext": { "originalQuery": "..." },
  "webPages": {
    "value": [
      {
        "name": "标题",
        "url": "链接",
        "datePublished": "2025-07-14T01:15:00.0000000",
        "snippet": "短摘要",
        "mainText": "动态摘要片段",
        "siteName": "站点名",
        "content": "长摘要正文",
        "contentCrawled": true,
        "logo": "站点logo",
        "imageList": [],
        "score": 0.67
      }
    ]
  }
}
```

## 状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 401 | 认证失败 |
| 429 | QPS超限 |
