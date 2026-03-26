---
name: gws
description: "Google Workspace CLI. Use when the user mentions Gmail, Google Drive, Calendar, Sheets, Docs, Tasks, People, Keep, sending email, checking inbox, managing files, reading/writing spreadsheets, viewing schedules, standup reports, or any Google Workspace operation — even if they don't explicitly say 'gws'."
metadata:
  {
    "requires":
      {
        "env": ["GOOGLE_WORKSPACE_PROJECT_ID", "GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE", "GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"],
        "bins": ["gws", "jq", "base64"]
      }
  }
---

# GWS — Google Workspace CLI

Google's official Workspace CLI (`@googleworkspace/cli`). One tool for Gmail, Drive, Calendar, Sheets, Docs, Tasks, People, Slides, Forms, Meet, Classroom, and more.

GitHub: https://github.com/googleworkspace/cli

## Setup

Each session, set these before using `gws`:

```bash
export GOOGLE_WORKSPACE_PROJECT_ID=<your-project-id>
export GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=~/.config/gws/credentials.json
export GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file
```

Auth once with `gws auth login`. Enable required APIs in GCP Console first.

## Usage Philosophy

**不确定参数时，查 schema 而不是猜。** `gws schema <api.method>` 返回完整参数说明，比盲目尝试快得多。

**批量操作优先。** 每次 `gws` 调用有 ~2-3s 启动延迟。批量标记已读/加星用 `batchModify`（每批 ≤100 条），避免逐条循环。

**JSON + jq 是默认输出模式。** 程序化处理用 JSON 输出配合 jq 提取字段。`--format table` 仅用于给人类看的展示场景。

**并行加速 I/O bound 操作。** 逐条 get 邮件等操作可用 `&` 后台并行 + `wait`，从 N×3s 降到 ~3s。

**所有 `--upload` 和 `--output` 路径仅支持相对路径。** 必须先 `cd` 到目标目录再操作，这是 CLI 的硬性限制。

## Known API Quirks

- **Gmail header 顺序不固定。** API 按内部存储顺序返回 headers，而非请求顺序。**必须按 header name 匹配，不能按数组 index 取值。**
- **Drive upload 的 name 参数无效。** `files create` 的 `"name"` 被忽略，上传后文件名始终为 "Untitled"，需先 upload 再 `update` 重命名。但 `files copy` 的 name 参数有效。
- **Drive delete 返回 HTML 而非 JSON。** 成功时返回 `{"status":"success","saved_file":"download.html"}`，忽略即可。
- **Sheets 的 sheet 名称不一定是 "Sheet1"。** `+read` 的 range 必须用实际 sheet 名，先 `get` 获取 `.sheets[].properties.title`。
- **Gmail `messages list` 仅返回 ID。** 需逐条 `get`。用 `format=metadata` 比 `format=full` 更快更省 token，只在需要正文时用 `full`。
- **Gmail 邮件 parts 结构不固定。** 有些邮件是单层 `.payload.parts[]`，有些是嵌套 `.payload.parts[].parts[]`。两种写法都要准备好。
- **People `searchContacts` 必须指定 `readMask`。** 不传会报 400。`connections list` 不需要。

## Service Availability

| 服务 | 状态 | 前置条件 |
|------|------|----------|
| Gmail | ✅ | Gmail API 已启用 |
| Drive | ✅ | Drive API 已启用 |
| Calendar | ✅ | Calendar API 已启用 |
| Sheets | ✅ | Sheets API 已启用 |
| Docs | ✅ | Docs API 已启用 |
| Tasks | ✅ | Tasks API 已启用 |
| People | ✅ | People API 已启用 |
| Slides | ✅ | Slides API 已启用 |
| Forms | ✅ | Forms API 已启用 |
| Meet | ✅ | Meet API 已启用 |
| Classroom | ✅ | Classroom API 已启用 |
| Keep | ⚠️ | 需额外 scope，重新授权时勾选 Keep 权限 |
| Workflow | ✅ | 内置 helper，无需额外 API |
| Chat | ❌ | 需要在 Google Workspace Admin 开启 Google Chat |
| Admin Reports | ❌ | 需超级管理员权限 |

## Troubleshooting

- **`insufficient authentication scopes`** → `gws auth login` 重新授权，确保勾选所需权限
- **`File not found`** → 检查是否使用了绝对路径，改用相对路径
- **上传后文件名为 "Untitled"** → 这是已知行为，用 `files update` 重命名
- **参数不确定** → `gws schema <api.method>` 查询任意 API 的完整参数结构
- **API 未启用** → 前往 GCP Console → APIs & Services → 启用对应 API

---

## Gmail

Gmail 是最常用的服务，支持完整的邮件 CRUD、搜索、标签、附件、线程、批量操作和设置管理。

### 搜索与列表

Gmail 搜索语法通过 `q` 参数传递，功能强大：`newer_than:1d`、`is:starred`、`is:unread`、`from:xxx`、`subject:keyword`、`label:xxx`、`has:attachment`、`after:YYYY/MM/DD`、`before:YYYY/MM/DD`、`category:primary`（primary/promotions/social/updates/forums）等。

```bash
gws gmail users messages list --params '{"userId":"me","q":"is:unread","maxResults":20}'
gws gmail users messages list --params '{"userId":"me","q":"is:unread"}' --page-all
```

### 读取邮件

**决策原则**：只需要摘要（发件人/主题/时间）用 `metadata`，需要正文用 `full`，只要预览用 `snippet` 字段。

```bash
# 提取 headers（按 name 匹配，不要按 index）
gws gmail users messages get --params '{"userId":"me","id":"MSG_ID","format":"metadata","metadataHeaders":["From","Subject","Date"]}'
# → jq '.payload.headers | map({(.name): .value}) | add'

# 纯文本正文（先试单层，为空再试嵌套）
gws gmail users messages get --params '{"userId":"me","id":"MSG_ID","format":"full"}' | jq -r '.payload.parts[] | select(.mimeType == "text/plain") | .body.data' | base64 -d
# 嵌套备选: jq -r '.payload.parts[].parts[]? | select(.mimeType == "text/plain") | .body.data' | base64 -d

# 快速预览（无需 base64，但有长度限制）
gws gmail users messages get --params '{"userId":"me","id":"MSG_ID","format":"metadata"}' | jq -r '.snippet'
```

### 并行批量读取

利用 `&` 后台并行将 N×3s 降到 ~3s：

```bash
IDS=$(gws gmail users messages list --params '{"userId":"me","q":"is:unread","maxResults":10}' 2>/dev/null | jq -r '.messages[].id')
for id in $IDS; do
  gws gmail users messages get --params "{\"userId\":\"me\",\"id\":\"$id\",\"format\":\"metadata\",\"metadataHeaders\":[\"From\",\"Subject\",\"Date\"]}" 2>/dev/null | jq -r '.payload.headers | map({(.name): .value}) | add | "\(.From[:30]) | \(.Subject) — \(.Date)"' &
done; wait
```

### 批量操作

`batchModify` 一次处理最多 100 条，避免逐条循环的延迟开销：

```bash
IDS=$(gws gmail users messages list --params '{"userId":"me","q":"is:unread","maxResults":100}' 2>/dev/null | jq -c '[.messages[].id]')
gws gmail users messages batchModify --params '{"userId":"me"}' --json "{\"ids\":$IDS,\"removeLabelIds\":[\"UNREAD\"]}"
gws gmail users messages batchModify --params '{"userId":"me"}' --json "{\"ids\":$IDS,\"addLabelIds\":[\"STARRED\"]}"
```

### 发送邮件

构造 RFC 2822 格式邮件，Base64 编码后发送。支持 HTML 和附件：

```bash
# 纯文本
RAW=$(printf "To: recipient@example.com\r\nSubject: Hello\r\nFrom: me@gmail.com\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nBody text here" | base64 -w0)
gws gmail users messages send --json "{\"raw\":\"$RAW\"}" --params '{"userId":"me"}'
```

### 附件下载

先从 `format=full` 响应中提取 `attachmentId`，再用 `attachments get` 下载（同样受相对路径限制）：

```bash
# 1. 获取附件列表
gws gmail users messages get --params '{"userId":"me","id":"MSG_ID","format":"full"}' | jq '[.payload.parts[] | select(.filename != "") | {filename, body: .body.attachmentId}]'

# 2. 下载（cd 到目标目录）
cd /path/to/target/dir
gws gmail users messages attachments get --params '{"userId":"me","messageId":"MSG_ID","id":"ATTACHMENT_ID"}' --output filename.pdf
```

### 线程 / 回复链

按对话线程查看邮件，避免重复同一封邮件的多个副本：

```bash
gws gmail users threads list --params '{"userId":"me","q":"is:unread","maxResults":10}'
gws gmail users threads get --params '{"userId":"me","id":"THREAD_ID","format":"metadata"}'
```

### 标签管理

```bash
gws gmail users labels list --params '{"userId":"me"}' | jq '.labels[] | {id, name, type}'
gws gmail users labels create --json '{"name":"Projects/AI","labelListVisibility":"labelShow","messageListVisibility":"show"}' --params '{"userId":"me"}'
gws gmail users messages batchModify --params '{"userId":"me"}' --json '{"ids":["MSG_ID"],"addLabelIds":["LABEL_ID"]}'
```

### Trash

```bash
gws gmail users messages trash --params '{"userId":"me","id":"MSG_ID"}'
gws gmail users messages untrash --params '{"userId":"me","id":"MSG_ID"}'
```

### 设置

```bash
gws gmail users settings getVacation --params '{"userId":"me"}'
gws gmail users settings sendAs list --params '{"userId":"me"}'
```

---

## Drive

Drive 支持文件和文件夹的完整生命周期管理：创建、上传、下载、复制、移动、删除、权限、共享盘。

### 浏览与搜索

```bash
gws drive files list --params '{"pageSize":10,"orderBy":"modifiedTime desc"}'
gws drive files list --params '{"q":"mimeType=\"application/vnd.google-apps.spreadsheet\""}'
gws drive files list --params '{"q":"'\''FOLDER_ID'\'' in parents"}'
```

### 上传（两步命名）

`files create` 的 name 参数无效，必须先上传再 rename：

```bash
cd /path/to/target/dir
gws drive files create --params '{}' --upload file.txt --upload-content-type text/plain
gws drive files update --params '{"fileId":"FILE_ID"}' --json '{"name":"real_name.txt"}'
```

### 创建文件夹

```bash
gws drive files create --params '{}' --json '{"name":"Folder Name","mimeType":"application/vnd.google-apps.folder"}'
```

### 复制与移动

`files copy` 的 name 参数有效（与 upload 不同），可一步完成：

```bash
# 复制（可同时重命名）
gws drive files copy --params '{"fileId":"ID"}' --json '{"name":"Copy of file"}'

# 移动到文件夹
gws drive files update --params '{"fileId":"ID","addParents":"FOLDER_ID","removeParents":"root"}' --json '{}'
```

### 下载与导出

**决策原则**：原生文件（txt, pdf, docx 等）用 `get --alt media`；Google 原生格式（Sheets, Docs, Slides）用 `export` 转换。

```bash
gws drive files get --params '{"fileId":"ID","alt":"media"}' --output file.txt
gws drive files export --params '{"fileId":"ID","mimeType":"application/pdf"}' --output doc.pdf
gws drive files export --params '{"fileId":"ID","mimeType":"text/csv"}' --output data.csv
```

### 权限与存储

```bash
gws drive permissions list --params '{"fileId":"ID","pageSize":10}'
gws drive about get --params '{"fields":"storageQuota"}' | jq '.storageQuota'
```

### 删除

```bash
gws drive files delete --params '{"fileId":"ID"}'
```

---

## Calendar

支持完整的事件 CRUD、日历管理、忙碌查询和权限控制。所有时间参数使用 RFC 3339 格式。

### 事件管理

```bash
# 查询事件
gws calendar events list --params '{"calendarId":"primary","timeMin":"START_DATETIME","timeMax":"END_DATETIME","maxResults":20}'

# 创建事件
gws calendar events insert --json '{"summary":"Meeting","start":{"dateTime":"DATETIME_START","timeZone":"Asia/Shanghai"},"end":{"dateTime":"DATETIME_END","timeZone":"Asia/Shanghai"}}' --params '{"calendarId":"primary"}'

# 更新/删除事件
gws calendar events update --params '{"calendarId":"primary","eventId":"EVENT_ID"}' --json '{"summary":"Updated"}'
gws calendar events delete --params '{"calendarId":"primary","eventId":"EVENT_ID"}'

# 查看重复事件的所有实例
gws calendar events instances --params '{"calendarId":"primary","eventId":"RECURRING_EVENT_ID"}'
```

### 忙碌查询与权限

```bash
# 查看忙碌/空闲时段
gws calendar freebusy query --json '{"timeMin":"START_DT","timeMax":"END_DT","items":[{"id":"primary"}]}'

# 日历权限
gws calendar acl list --params '{"calendarId":"primary"}'
```

### 日历管理

```bash
# 创建/删除二级日历
gws calendar calendars insert --json '{"summary":"My Calendar"}' --params '{}'
gws calendar calendars delete --params '{"calendarId":"CALENDAR_ID"}'

# 日历列表管理
gws calendar calendarList list --params '{"maxResults":10}'
```

---

## Sheets

先获取真实 sheet 名称再操作。支持创建、读写、更新、清空和批量操作。

```bash
# 创建 Spreadsheet
gws sheets spreadsheets create --json '{"properties":{"title":"My Sheet"}}' --params '{}'

# 获取 sheet 名称
SHEET=$(gws sheets spreadsheets get --params '{"spreadsheetId":"ID"}' 2>/dev/null | jq -r '.sheets[0].properties.title')

# 读写
gws sheets +read --spreadsheet "ID" --range "${SHEET}!A1:C10"
gws sheets +append --spreadsheet "ID" --range "${SHEET}!A:A" --values '[["col1","col2"]]'

# 更新单元格
gws sheets spreadsheets values update --params '{"spreadsheetId":"ID","range":"Sheet1!A1","valueInputOption":"RAW"}' --json '{"values":[["New Value"]]}'

# 清空单元格（保留格式）
gws sheets spreadsheets values clear --params '{"spreadsheetId":"ID","range":"Sheet1!A1:C10"}'
```

---

## Docs

支持创建文档和提取纯文本内容。文档编辑通过 `batchUpdate` 实现。

```bash
# 创建
gws docs documents create --json '{"title":"My Doc"}' --params '{}'

# 提取纯文本
gws docs documents get --params '{"documentId":"ID"}' | jq '[.body.content[]|select(.paragraph)|.paragraph.elements[]?|select(.textRun)|.textRun.content]|join("")'
```

---

## Slides

```bash
# 创建
gws slides presentations create --json '{"title":"My Slides"}' --params '{}'

# 获取元数据
gws slides presentations get --params '{"presentationId":"ID"}' | jq '{title, slideCount: (.slides | length)}'
```

---

## Forms

```bash
# 创建表单
gws forms forms create --json '{"info":{"title":"Survey"}}' --params '{}'

# 查看回复
gws forms forms responses list --params '{"formId":"FORM_ID"}'
```

---

## Tasks

支持任务列表 CRUD 和完成状态管理。

```bash
gws tasks tasklists list | jq '.items[]|{title,id}'
gws tasks tasks list --params '{"tasklist":"@default"}' | jq '.items[]|{title,status,due}'
gws tasks tasks insert --json '{"title":"Task","notes":"Details"}' --params '{"tasklist":"@default"}'
gws tasks tasks patch --params '{"tasklist":"@default","task":"TASK_ID"}' --json '{"status":"completed"}'
gws tasks tasks delete --params '{"tasklist":"@default","task":"TASK_ID"}'
gws tasks tasks clear --params '{"tasklist":"@default"}'  # 清除所有已完成任务
```

---

## People

支持联系人搜索、创建、分组和个人资料查询。

```bash
# 个人资料
gws people people get --params '{"resourceName":"people/me","personFields":"names,emailAddresses"}'

# 搜索联系人（必须指定 readMask）
gws people people searchContacts --params '{"query":"keyword","pageSize":10,"readMask":"names,emailAddresses,phoneNumbers"}'

# 联系人列表
gws people connections list --params '{"resourceName":"people/me","personFields":"names,emailAddresses,phoneNumbers","pageSize":10}'

# 创建联系人
gws people people createContact --json '{"names":[{"givenName":"First","familyName":"Last"}],"emailAddresses":[{"value":"email@example.com"}]}' --params '{"readMask":"names,emailAddresses"}'

# 联系人分组
gws people contactGroups list --params '{"pageSize":10}'
```

---

## Meet / Classroom

基础查询可用，详细操作通过 `gws schema` 查参数。

```bash
# Meet: 会议记录
gws meet conferenceRecords list --params '{"pageSize":10}'
gws meet conferenceRecords get --params '{"name":"RECORD_ID"}'

# Classroom: 课程、学生、作业
gws classroom courses list --params '{"pageSize":10}'
gws classroom courses students list --params '{"courseId":"COURSE_ID"}'
gws classroom courses.courseWork list --params '{"courseId":"COURSE_ID"}'
```

## Keep

报 `insufficient authentication scopes` 时重新授权：

```bash
gws auth login  # 确保勾选 Keep 权限
```

## Workflow Helpers

```bash
gws workflow +standup-report        # 今日会议 + 待办任务
gws workflow +meeting-prep          # 下一个会议准备
gws workflow +weekly-digest         # 本周会议 + 未读邮件数
gws workflow +email-to-task --message-id "MSG_ID"  # Gmail → Tasks
```

## General

```bash
gws schema <api.method>            # 查询任意 API 的参数结构
gws <service> <method> --params '{}' --format table   # 表格输出（给人类看）
gws <service> <method> --params '{}' --page-all       # 自动翻页
```
