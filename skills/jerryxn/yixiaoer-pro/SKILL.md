# yixiaoer-pro Skill

蚁小二专业版发布技能：上传 → 发布 → 查询状态，全流程自动化。支持按账号/分组/平台批量发布。

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `YIXIAOER_TOKEN` | **必填**。蚁小二 API Token，优先读取系统环境变量 |
| `YIXIAOER_BASE_URL` | 可选，默认 `https://www.yixiaoer.cn/api` |

> ⚠️ **首次使用：** 如果 `YIXIAOER_TOKEN` 未配置，skill 会返回引导提示，请在 OpenClaw 配置界面添加系统环境变量：变量名填 `YIXIAOER_TOKEN`，值填你的蚁小二 API Token（登录蚁小二 → 个人设置 → API Token）

---

## Token 检查机制

**每次执行任意命令时，skill 会自动检查 token：**

| 状态 | 效果 |
|------|------|
| ✅ `YIXIAOER_TOKEN` 已配置 | 正常执行命令 |
| ❌ `YIXIAOER_TOKEN` 未配置 | 返回错误码 `TOKEN_NOT_CONFIGURED` + 引导提示，告知用户在平台配置界面写入系统环境变量 |

```json
// 未配置时运行任何命令，都会收到：
{
  "error": true,
  "code": "TOKEN_NOT_CONFIGURED",
  "message": "YIXIAOER_TOKEN 未配置",
  "hint": "请在 OpenClaw 配置界面添加系统环境变量：\n  变量名：YIXIAOER_TOKEN\n  值：你的蚁小二 API Token"
}
```

---

## 自然语言触发映射

> 当用户说以下类似的话时，Agent 自动执行对应命令：

| 用户意图 | Agent 执行 |
|---------|----------|
| "帮我发视频" / "上传发布" | `python3 yixiaoer_pro.py publish_full <文件> <封面> <目标> <平台> <标题> <描述> <标签>` |
| "帮我发布到 XX 组/账号" | 同上，自动解析目标 |
| "查一下我的账号" / "有哪些分组" | `python3 yixiaoer_pro.py accounts` |
| "这个任务发布成功了吗" | `python3 yixiaoer_pro.py status <taskSetId>` |
| "先存草稿" / "预览一下" | `python3 yixiaoer_pro.py draft ...` |
| "批量发到XX组" | `python3 yixiaoer_pro.py publish_batch <分组> <平台> ...` |

---

## 快速上手（三句话）

**第一句：** "帮我把视频发到抖音小桃犟账号"
→ Agent 自动完成：查询账号 → 上传视频+封面 → 发布 → 确认

**第二句：** "先存草稿看看效果"
→ Agent 执行 draft 模式，不正式发布

**第三句：** "确认发布"
→ Agent 查询草稿状态，确认后正式发布

---

## 四阶段流程详解

### 阶段一：验证（自动执行）
Agent 收到发布指令后，**自动**执行验证：
```bash
python3 yixiaoer_pro.py validate
```
- 验证 TOKEN 是否有效
- 查询所有分组（`GET /groups`）
- 查询所有账号（`GET /platform-accounts`），含 `groups` 字段
- **自动匹配目标**：用户说"小桃犟" → 找到对应 `platformAccountId`

### 阶段二：上传
```bash
python3 yixiaoer_pro.py upload <视频路径> <封面路径>
```
- 识别文件类型（ffprobe）
- 获取 OSS 上传地址
- 上传到 OSS（自动重试1次）
- **返回**：`videoKey`、`coverKey`

### 阶段三：发布
```bash
# 立即发布
python3 yixiaoer_pro.py publish_full <视频> <封面> <目标> <平台> <标题> <描述> <标签>

# 存草稿（推荐先试）
python3 yixiaoer_pro.py draft <vk> <ck> <目标> <平台> <标题> <描述> <标签>

# 批量发布（同一分组多账号）
python3 yixiaoer_pro.py publish_batch <分组> <平台> <标题> <描述> <标签>
```

**发布目标匹配优先级：**
1. `platformAccountId`（直接匹配）
2. `groups` 数组（按分组查所有账号）
3. `platformAccountName`（按账号名精确匹配）
4. `platformName`（按平台名模糊匹配）

**描述字段特殊处理：** 标签自动追加到描述末尾，无需手动拼接。

### 阶段四：确认
```bash
python3 yixiaoer_pro.py status <taskSetId>
```
- 自动轮询最多 5 次（每次间隔 10 秒）
- 返回最终状态：`allsuccessful` / `partialsuccessful` / `pending`

---

## 命令行接口

```bash
# 推荐：一条命令完成全部
python3 yixiaoer_pro.py publish_full <视频> <封面> <目标> <平台> <标题> <描述> [标签JSON]
python3 yixiaoer_pro.py publish_full video.mp4 cover.jpg 小桃犟 抖音 "标题" "描述" '["标签1","标签2"]'

# 分步执行
python3 yixiaoer_pro.py upload <视频> <封面>          # 上传，返回 videoKey/coverKey
python3 yixiaoer_pro.py publish <vk> <ck> <目标> <平台> <标题> <描述> <标签JSON>

# 批量发布
python3 yixiaoer_pro.py publish_batch <分组> <平台> <标题> <描述> <标签JSON>

# 查询
python3 yixiaoer_pro.py validate                          # 验证+查账号+查分组
python3 yixiaoer_pro.py accounts                          # 查所有账号（含分组）
python3 yixiaoer_pro.py groups                            # 查所有分组
python3 yixiaoer_pro.py status <taskSetId>               # 查任务状态
python3 yixiaoer_pro.py status_all                        # 查所有pending任务
```

---

## API 参考（Fallback）

### 基础
- **Base URL:** `https://www.yixiaoer.cn/api`
- **鉴权:** `Authorization: YOUR_YIXIAOER_TOKEN`

### 分组
```
GET /groups
```

### 账号
```
GET /platform-accounts?page=1&size=50
```
关键字段：`id`（platformAccountId）、`platformName`、`platformAccountName`、`groups`（分组ID数组）、`isOperate`、`proxyId`

### 上传
```
GET /storages/cloud-publish/upload-url?contentType={type}&size={字节数}

PUT {serviceUrl}
Headers: Content-Type: video/mp4 或 image/jpeg
Body: binary
```
返回：`{"Status":"Ok"}`

### 发布
```
POST /taskSets/v2
Body: {
  "coverKey": "...", "desc": "",
  "platforms": ["抖音"], "publishType": "video",
  "isDraft": false, "isAppContent": false,
  "publishArgs": {
    "accountForms": [{
      "cover": { "width": 1920, "height": 1080, "size": 字节, "key": "...", "path": "https://oss-v2.yixiaoer.cn/..." },
      "coverKey": "...", "platformAccountId": "账号ID",
      "video": { "duration": 秒, "width": 1920, "height": 1080, "size": 字节, "key": "...", "path": "..." },
      "contentPublishForm": {
        "formType": "task", "title": "标题",
        "description": "描述#标签1#标签2",
        "tags": ["标签1","标签2"], "category": [], "type": 1
      }
    }], "content": ""
  }, "publishChannel": "cloud"
}
```

### 状态
```
GET /v2/taskSets?page=1&size=5&taskSetStatus=pending
GET /v2/taskSets/{taskSetId}
```

---

## 错误排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `获取视频资源失败` (403) | 视频 OSS key 无效或 size=0 | 重新上传，确认 `Status:Ok` |
| `获取视频资源失败` (403) | 账号 `proxyId=null` | 在蚁小二后台绑定代理 |
| `获取视频资源失败` (403) | `publishChannel=local` | 改用 `cloud` |
| `pending` 不动 | 草稿模式未解除 | 改为 `isDraft:false` + `type:1` |
| `data: ""` 空返回 | 账号无权限 | 确认账号属于同一团队 |
| `statusCode: 400` | TOKEN 无效 | 确认 `YIXIAOER_TOKEN` 环境变量 |
