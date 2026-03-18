---
name: wolai
description: 通过 wolai Open API 操作 wolai 笔记，支持读取页面/块内容、创建块（写入内容）、获取数据库、向数据库插入数据、获取/刷新 Token。当用户需要读取 wolai 页面、向 wolai 写入内容、操作 wolai 数据库、或与 wolai 进行任何数据交互时使用此 skill。触发场景：「读取 wolai 页面」、「在 wolai 里写入」、「查询 wolai 数据库」、「往 wolai 插入数据」、「获取 wolai token」等。
---

# wolai Skill

通过 wolai Open API（RESTful）操作 wolai 的块、页面、数据库。

Base URL：`https://openapi.wolai.com/v1`

详细接口参数见 [references/api.md](references/api.md)。

## Setup

### 1. 创建应用并获取 Token

1. 前往 https://www.wolai.com/dev 创建应用，选择所需权限（读取/插入/更新页面内容）
2. 创建后得到 `App ID` 和 `App Secret`
3. 调用 `POST /token` 换取 `app_token`（Token 永久有效，`expire_time: -1`）
4. 将 Token 存入环境变量：

```
WOLAI_TOKEN=your_app_token
```

在 QClaw/OpenClaw 中配置：
```
openclaw config set env.WOLAI_TOKEN "your_app_token"
```

### 2. 团队空间需添加应用权限

团队空间中，每个页面需单独添加应用：
页面右上角 → 页面协作 → 应用权限 → 添加应用

个人空间默认拥有全部页面权限，无需此步骤。

## 凭证预检

每次调用前先检查 Token：

```powershell
if (-not $env:WOLAI_TOKEN) {
    Write-Host "缺少 WOLAI_TOKEN，请按 Setup 步骤配置"
    exit 1
}
```

## API 调用方式

所有请求统一使用 PowerShell（Windows 环境），Token 放在 `Authorization` Header：

```powershell
function Invoke-WolaiApi {
    param(
        [string]$Method = "GET",
        [string]$Path,
        [hashtable]$Body = $null
    )
    # ⚠️ 必须强制 UTF-8，否则中文内容会变成问号
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8

    $headers = @{
        "Authorization" = $env:WOLAI_TOKEN
        "Content-Type"  = "application/json; charset=utf-8"
    }
    $uri = "https://openapi.wolai.com/v1$Path"
    if ($Body) {
        $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Depth 10))
        Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body $bodyBytes
    } else {
        Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
    }
}
```

## 接口决策表

| 用户意图 | 接口 | 说明 |
|---------|------|------|
| 读取页面/块内容 | `GET /blocks/{id}` | id 为页面 ID 或块 ID |
| 读取页面下所有子块 | `GET /blocks/{id}/children` | 支持分页 |
| 向页面写入/追加内容 | `POST /blocks` | 需指定 parent_id |
| 读取数据库 | `GET /databases/{id}` | 支持分页、筛选、排序 |
| 向数据库插入行 | `POST /databases/{id}/rows` | |
| 获取 Token | `POST /token` | 需要 appId + appSecret |
| 刷新 Token | `PUT /token` | Token 泄露时使用 |

## 常用工作流

### 读取页面内容

```powershell
# 页面 ID 从 URL 获取：wolai.com/ 后面的部分即为页面 ID
$pageId = "oaBQLqSBaMbS6S4NX4fJU7"

# 获取页面块信息
$page = Invoke-WolaiApi -Method GET -Path "/blocks/$pageId"
$page.data

# 获取页面所有子块（内容列表）
$children = Invoke-WolaiApi -Method GET -Path "/blocks/$pageId/children"
$children.data
```

### 向页面写入内容（创建块）

```powershell
# 在指定页面末尾追加一段文字
Invoke-WolaiApi -Method POST -Path "/blocks" -Body @{
    parent_id = "oaBQLqSBaMbS6S4NX4fJU7"  # 目标页面 ID
    blocks = @{
        type    = "text"
        content = "Hello from OpenClaw!"
    }
}
```

### 读取数据库

```powershell
$dbId = "your_database_id"
$db = Invoke-WolaiApi -Method GET -Path "/databases/$dbId"
$db.data
```

### 向数据库插入数据

```powershell
Invoke-WolaiApi -Method POST -Path "/databases/$dbId/rows" -Body @{
    rows = @(
        @{ "字段名" = "值1"; "另一字段" = "值2" }
    )
}
```

### 获取 Token（首次配置）

```powershell
$resp = Invoke-RestMethod -Method POST `
    -Uri "https://openapi.wolai.com/v1/token" `
    -Headers @{ "Content-Type" = "application/json" } `
    -Body (@{ appId = "your_app_id"; appSecret = "your_app_secret" } | ConvertTo-Json)
$resp.data.app_token  # 保存此值到 WOLAI_TOKEN
```

## 接口限制

- 频率：同一用户 **5次/秒**
- 批量获取：一次最多 200 条，超出用分页（`has_more` + `next_cursor`）
- 批量创建/更新：一次最多 20 条
- 删除：每次只能删除 1 条

用量限制（每小时/每月）因套餐不同，详见 references/api.md。

## 错误处理

| 错误码 | 含义 | 建议处理 |
|-------|------|---------|
| 17001 | 缺少参数 | 检查必填字段 |
| 17002 | 参数错误 | 检查参数格式 |
| 17003 | 无效 Token | 检查 WOLAI_TOKEN 是否正确 |
| 17004 | 获取资源失败 | 检查 ID 是否正确 |
| 17005 | 资源未找到 | 检查页面/块 ID |
| 17006 | 服务器内部错误 | 稍后重试 |
| 17007 | 请求过于频繁 | 降低调用频率（≤5次/秒） |
| 17008 | 请求体过大 | 拆分为多次请求 |
| 17010 | 不支持的块类型 | 检查 type 字段，见 references/api.md |
| 17011 | 权限不足 | 团队空间需在页面添加应用权限 |

## 注意事项

- 页面 ID 从 URL 获取：`wolai.com/` 后面的部分即为 ID
- Token 永久有效（`expire_time: -1`），泄露后调用 `PUT /token` 刷新
- 团队空间每个页面都需单独添加应用，个人空间无需此操作
- 块类型详见 references/api.md 的「块类型说明」章节
