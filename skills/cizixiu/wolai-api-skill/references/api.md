# wolai Open API 接口参考

Base URL: `https://openapi.wolai.com/v1`

所有请求均需在 Header 中携带：
```
Authorization: <app_token>
```

---

## 目录

1. [Token 接口](#token)
2. [Block 接口](#block)
3. [Database 接口](#database)
4. [块类型说明](#block-types)
5. [分页参数](#pagination)
6. [错误码](#error-codes)
7. [用量限制](#rate-limits)

---

## Token 接口 {#token}

### 创建 Token

`POST /v1/token`

**无需 Authorization Header**

**Request Body (application/json)**

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| appId | string | ✅ | 应用 ID，创建应用后获取 |
| appSecret | string | ✅ | 应用密钥，创建应用后获取，请妥善保管 |

**示例请求：**
```json
{
  "appId": "qGPon7raLEu4nJTXCBkeAB",
  "appSecret": "e8501b4c8ed17f97961db65d438c61ba0c4d58ad894ac23c924c1a098b03b1e7"
}
```

**示例响应：**
```json
{
  "data": {
    "app_token": "2e6db3fc9bae9e4a5c004162c59c3cfa73ca5f93c61a1b009e219ed454cb37ee",
    "app_id": "qGPon7raLEu4nJTXCBkeAB",
    "create_time": 1671523112626,
    "expire_time": -1,
    "update_time": 1671523112626
  }
}
```

> `expire_time: -1` 表示 Token 永久有效。

---

### 刷新 Token

`PUT /v1/token`

Token 泄露时调用，旧 Token 立即失效。

**Header:** `Authorization: <app_token>`

**无 Body 参数**

---

## Block 接口 {#block}

### 查询块详情

`GET /v1/blocks/{id}`

获取单个块（页面或块）的详细信息。

**Path 参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | ✅ | 块 ID 或页面 ID |

**页面 ID 获取方式：** 复制 wolai 页面链接，`wolai.com/` 后面的部分即为页面 ID。

**示例：**
```powershell
Invoke-WolaiApi -Method GET -Path "/blocks/oaBQLqSBaMbS6S4NX4fJU7"
```

---

### 查询块子节点

`GET /v1/blocks/{id}/children`

获取指定块（页面）下的所有子块列表，支持分页。

**Path 参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | ✅ | 父块 ID 或页面 ID |

**Query 参数（分页）**

| 参数 | 类型 | 说明 |
|------|------|------|
| page_size | integer | 每页数量，最大 200 |
| start_cursor | string | 分页游标，首次不传，后续传上次返回的 next_cursor |

**示例：**
```powershell
Invoke-WolaiApi -Method GET -Path "/blocks/oaBQLqSBaMbS6S4NX4fJU7/children"
```

---

### 创建块

`POST /v1/blocks`

在指定页面或块下创建一个或多个块（写入内容）。

**Request Body (application/json)**

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| parent_id | string | ✅ | 父块 ID 或页面 ID，内容将插入到此位置 |
| blocks | object 或 array | ✅ | 单个块对象或块对象数组（最多 20 个） |

**单个块示例：**
```json
{
  "parent_id": "oaBQLqSBaMbS6S4NX4fJU7",
  "blocks": {
    "type": "text",
    "content": "Hello world!"
  }
}
```

**多个块示例：**
```json
{
  "parent_id": "oaBQLqSBaMbS6S4NX4fJU7",
  "blocks": [
    {
      "type": "text",
      "content": "Hello ",
      "text_alignment": "center"
    },
    {
      "type": "heading",
      "level": 1,
      "content": {
        "title": "World!",
        "front_color": "red"
      },
      "text_alignment": "center"
    }
  ]
}
```

> ⚠️ 如果提示权限错误（17011），请检查团队空间页面是否已添加该应用。

---

## Database 接口 {#database}

### 获取数据表格数据

`GET /v1/databases/{id}`

获取数据库（数据表格）的内容，支持分页。

**Path 参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | ✅ | 数据库 ID（数据表格的页面 ID） |

**示例：**
```powershell
Invoke-WolaiApi -Method GET -Path "/databases/your_database_id"
```

---

### 数据表格新增记录

`POST /v1/databases/{id}/rows`

向数据库插入一行或多行数据。

**Path 参数**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | ✅ | 数据库 ID |

**Request Body (application/json)**

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| rows | array[object] | ✅ | 行数据数组，每个对象的 key 为字段名，value 为字段值 |

**示例：**
```json
{
  "rows": [
    {
      "标题": "任务一",
      "状态": "进行中",
      "截止日期": "2024-12-31"
    }
  ]
}
```

---

## 块类型说明 {#block-types}

创建块时 `type` 字段的可用值：

| type | 说明 | 关键字段 |
|------|------|---------|
| `text` | 普通文本段落 | `content`（string） |
| `heading` | 标题 | `level`（1/2/3），`content.title` |
| `todo` | 待办事项（复选框） | `content`，`checked`（bool） |
| `bulleted_list` | 无序列表 | `content` |
| `numbered_list` | 有序列表 | `content` |
| `toggle` | 折叠块 | `content` |
| `quote` | 引用块 | `content` |
| `divider` | 分割线 | 无额外字段 |
| `code` | 代码块 | `content`，`language` |
| `image` | 图片 | `url` |
| `page` | 子页面 | `content.title` |

**文本内容格式（content 为对象时）：**

```json
{
  "title": "文字内容",
  "front_color": "red",      // 文字颜色
  "back_color": "yellow",    // 背景色
  "bold": true,
  "italic": true,
  "underline": true,
  "strikethrough": true,
  "inline_code": true
}
```

**text_alignment 可选值：** `left`、`center`、`right`

---

## 分页参数 {#pagination}

批量查询接口支持分页，响应中包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| has_more | boolean | 是否还有更多数据 |
| next_cursor | string | 下一页游标，传入 `start_cursor` 参数 |

**分页示例（PowerShell）：**
```powershell
$cursor = $null
do {
    $path = "/blocks/$pageId/children"
    if ($cursor) { $path += "?start_cursor=$cursor" }
    $resp = Invoke-WolaiApi -Method GET -Path $path
    # 处理 $resp.data
    $cursor = if ($resp.has_more) { $resp.next_cursor } else { $null }
} while ($cursor)
```

---

## 错误码 {#error-codes}

| 错误码 | HTTP 状态码 | 原因 |
|-------|------------|------|
| 17001 | 400 | 缺少参数 |
| 17002 | 400 | 参数错误 |
| 17003 | 401 | 无效的 Token |
| 17004 | 400 | 获取资源失败 |
| 17005 | 404 | 资源未找到 |
| 17006 | 500 | 服务器内部错误 |
| 17007 | 429 | 请求过于频繁（超过 5次/秒） |
| 17008 | 413 | 请求体过大 |
| 17009 | 415 | 不支持的媒体类型 |
| 17010 | 400 | 暂不支持的块类型 |
| 17011 | 403 | 权限不足（团队空间需添加应用到页面） |

**错误响应格式：**
```json
{
  "message": "错误描述及解决方案",
  "error_code": 17003,
  "status_code": 401
}
```

---

## 用量限制 {#rate-limits}

**频率限制：** 同一用户 5次/秒

**每小时 / 每月调用限制（按套餐）：**

| 套餐 | 每小时 | 每月 |
|------|--------|------|
| 个人免费版 | 10次 | 100次 |
| 个人专业版 | 500次 | 10,000次 |
| 家庭版 | 800次 | 20,000次 |
| 小组版 | 1,000次 | 30,000次 |
| 团队版 | 1,500次 | 60,000次 |
| 企业版 | 3,000次 | 200,000次 |

**其他限制：**
- 批量获取：一次最多 200 条
- 批量创建/更新：一次最多 20 条
- 删除：每次只能删除 1 条
- 单个数据表格：最多 10,000 行、100 列、10 个视图
- 资源上传：单个附件最大 1024MB
