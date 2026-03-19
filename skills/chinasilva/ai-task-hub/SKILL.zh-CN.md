---
name: ai-task-hub
description: AI Task Hub 用于图像检测与分析、去背景与抠图、语音转文字、文本转语音、文档转 Markdown、积分余额/流水查询和异步任务编排。适用于用户需要通过 execute/poll/presentation 与账户积分查询完成结果交付，且由宿主统一管理身份、积分、支付和风控的场景。
version: 3.2.23
metadata:
  openclaw:
    skillKey: ai-task-hub
    emoji: "🧩"
    homepage: https://gateway.binaryworks.app
    transport:
      preferredEntrypoint: /agent/public-bridge/invoke
      trustedHostEntrypoint: /agent/skill/bridge/invoke
    requires:
      bins:
        - node
---

# AI Task Hub（公开包）

原名：`skill-hub-gateway`。

公开包能力边界：

- 只保留 `portal.skill.execute`、`portal.skill.poll`、`portal.skill.presentation`、`portal.account.balance`、`portal.account.ledger`。
- 不在公开包内交换 `api_key` 或 `userToken`。
- 不在公开包内处理支付、充值与积分 UI 闭环。
- 优先使用附件 URL；当宿主运行时显式暴露附件 bytes 或显式附件路径时，会通过 public bridge 自动上传并注入返回的 URL。
- 第三方 agent 入口统一走 `POST /agent/public-bridge/invoke`。

## 用户侧输出原则

- 当用户上传图片、音频、文档或视频并请求执行能力时，默认把这些输入视为可直接处理，优先直接执行并返回结果、进度或必要的最小化下一步。
- 不要向最终用户解释 `image_url`、`attachment.url`、对象存储 URL、bridge、宿主上传、输入归一化、受控媒体域名等内部实现细节，除非用户明确要求排查技术问题。
- 不要要求用户手工提供 URL、JSON 字段名或上传链路说明；这些属于宿主与 skill 之间的内部处理。
- 若运行时已具备附件处理能力，应静默完成上传、转存、URL 注入和 execute/poll/presentation 编排。
- 只有在执行确实失败且用户必须介入时，才用面向用户的语言说明缺少可处理文件、授权未完成或稍后重试；不要泄漏内部链路分层。

## 适用场景

当用户提出以下需求时，优先触发本 skill：

- 检测图片中的人脸、人体存在、人体关键点、图像标签或人脸情绪
- 执行当前公开包明确对外暴露的人像/商品分割、蒙版、抠图或 matting
- 将音频转写为文本（语音转文字、音频转写）
- 将文本生成语音（文本转语音、语音合成）
- 将上传文档转换为 Markdown 文本
- 发起异步任务并在稍后查询任务状态（轮询）
- 获取 run 的渲染结果（叠加图、蒙版、抠图文件）
- 执行向量化或重排序任务（embeddings / reranker）
- 查询当前积分余额或积分流水

## 示例请求

可触发本 skill 的用户表达示例：

- "检测这张图片里的人脸并返回框坐标。"
- "给这张图做标签并总结主要对象。"
- "帮我把这张商品图去背景。"
- "把这张人像图做成干净抠图。"
- "把这段会议录音转成文字。"
- "把这段文本生成语音。"
- "把这个 PDF 文件转成 Markdown。"
- "先发起任务，稍后我再查任务状态。"
- "帮我拉取 run_456 的叠加图和蒙版文件。"
- "为这组文本生成向量并做重排序。"
- "帮我查一下当前积分余额。"
- "帮我查 2026-03-01 到 2026-03-15 的积分流水。"

## 能力别名（便于检索）

- `vision` 别名：人脸检测 / 人体检测 / 图像标签 / 图像识别
- `background` 别名：去背景 / 抠图 / 人像分割 / 商品抠图 / 蒙版
- `asr` 别名：语音转文字 / 音频转写 / 语音识别
- `tts` 别名：文本转语音 / 语音合成 / 语音生成
- `markdown_convert` 别名：文档转 Markdown / 文件转 Markdown
- `poll` 别名：轮询 / 查询任务状态 / 异步任务状态
- `presentation` 别名：结果渲染 / 叠加图 / 蒙版 / 抠图文件
- `account.balance` 别名：积分余额 / 剩余积分 / credits 余额
- `account.ledger` 别名：积分流水 / 积分明细 / credits 历史
- `embeddings/reranker` 别名：向量化 / 语义向量 / 重排序

视觉能力公开发现边界：

- 当前公开 skill 只对外宣告后端已启用、且适合公开交付的视觉能力。
- 已下线、仅内部保留或仍属 legacy fallback 的视觉路由，不会继续出现在 discovery references 和 capability manifest 中。

## 运行时契约

默认 API 基址：`https://gateway-api.binaryworks.app`
发布包策略：对外请求基址锁定为默认 API 基址，以降低 token 被重定向外发的风险。

Action 与接口映射：

- `portal.skill.execute` -> `POST /agent/skill/execute`
- `portal.skill.poll` -> `GET /agent/skill/runs/:run_id`
- `portal.skill.presentation` -> `GET /agent/skill/runs/:run_id/presentation`
- `portal.account.balance` -> `GET /agent/skill/account/balance`
- `portal.account.ledger` -> `GET /agent/skill/account/ledger`

## 安装机制与运行要求

- 本 skill 为说明优先（instruction-first）包，不定义远程安装器流程。
- 运行时仅执行包内自带脚本（`scripts/*.mjs`）。
- 运行依赖仅为 `node`（与 `metadata.openclaw.requires.bins` 声明一致）。
- 本包不包含远程下载后执行链路（不使用 `curl|wget ... | sh|bash|python|node`）。

## 鉴权契约

第三方 agent 入口模式（推荐）：

- OpenClaw / Codex / Claude 这类运行时应优先调用 `POST /agent/public-bridge/invoke`。
- 不应要求最终用户手工提供任何凭证。
- 首次调用且尚无绑定时，gateway 会返回 `AUTHORIZATION_REQUIRED`，并在 details 中给出 `authorization_url` 与 `entry_user_key`。
- 返回的 `authorization_url` 里可能带有 `gateway_api_base_url`；宿主在浏览器授权完成时应保留这个参数，确保 `/agent-auth/complete` 回到创建该授权会话的同一 API 环境。
- 宿主/运行时应把 `authorization_url` 展示给用户，保存 `entry_user_key`，待授权完成后用同一个 `entry_user_key` 重试。
- 如果后续又收到 `AUTHORIZATION_REQUIRED`，且 `details.likely_cause=ENTRY_USER_KEY_NOT_REUSED`、`details.recovery_action=REUSE_ENTRY_USER_KEY`、`details.reauthorization_required=false`，宿主应优先恢复之前保存的 `entry_user_key` 并直接重试，而不是再次让用户走浏览器授权。

网关鉴权使用的标识格式约束：

- `agent_uid` 必须匹配 `^agent_[a-z0-9][a-z0-9_-]{5,63}$`。
- `conversation_id` 必须匹配 `^[A-Za-z0-9._:-]{8,128}$`。
- 在已部署 bridge 模式下，宿主可以传入自己的稳定运行时 agent 标识，由网关 bridge 在服务端完成规范化。

宿主侧 token 桥接（不属于公开发布包）：

- 为保持公开包低权限与合规，本公开运行时不签发也不接受调用方自管 task token。
- 面向第三方 agent 入口的推荐桥接入口：`POST /agent/public-bridge/invoke`。
- 若宿主是你自己控制、且能安全持有 bridge secret 的服务端，仍可继续使用 `POST /agent/skill/bridge/invoke`。
- 这些桥接入口都由网关运行时提供，不打包在本公开 skill 包里，也不要求调用方自己管理任何凭证。
- bridge 请求体应包含 `action`、`agent_uid`、`conversation_id` 以及可选 `payload`。
- `conversation_id` 应是宿主生成的 opaque 会话/安装标识，不应直接使用公开 chat id、原始 thread id 或任何 PII。
- 公开 bridge 在可用时会直接复用稳定外部用户绑定；若绑定缺失，网关会返回宿主自有授权 URL（host-owned 授权 URL）和 `entry_user_key`，让用户在浏览器完成首次绑定。
- 若需要跨多个会话/线程复用同一账户，应复用同一个 `entry_user_key`；公开 bridge 不接受 owner 覆盖。
- 网关 bridge 会在服务端完成 `agent_uid` 规范化、缺失绑定修复、短期 task token 签发和 action 执行。
- `portal.skill.execute` 属于写操作；通过 public bridge 调用时，建议在用户确认后再发送 `options.confirm_write=true`，否则网关可能返回 `ACTION_CONFIRMATION_REQUIRED`。
- 已部署 bridge 会拒绝 `base_url`、`gateway_api_key`、`api_key`、`user_token`、`agent_task_token`、`owner_uid_hint`、`install_channel` 这类覆盖字段。
- 建议宿主保存 `entry_user_key`、规范化 `agent_uid`，并在授权完成后重放同一 bridge action。

宿主接入模式：

- `交互模式`（推荐）：宿主调用 `POST /agent/public-bridge/invoke`，在需要时把返回的宿主自有授权 URL（host-owned 授权 URL）展示给用户，保存 `entry_user_key`，待授权完成后重试。
- `可信宿主 bridge`（次级）：若你控制上游后端且可安全持有 bridge assertion secret，可调用 `POST /agent/skill/bridge/invoke`。
- 公开 skill 包本身不会拉起浏览器、持久化凭证或执行 OAuth/token 交换。
- 上述授权 URL 由已部署的 gateway/admin-web 页面承载，不属于本 skill 包运行时。

## Agent 调用速查

第三方 agent 入口推荐单入口（推荐）：

- 已部署 bridge API 请求体：
```json
{
  "entry_host": "openclaw",
  "action": "portal.account.balance",
  "agent_uid": "support_assistant",
  "conversation_id": "host_session_20260316_opaque_001",
  "payload": {}
}
```

- 将该请求体发送到 `POST /agent/public-bridge/invoke`。
- 这是面向第三方 agent 友好接入的推荐生产入口。
- 首次使用时，gateway 可能返回带 `authorization_url` 和 `entry_user_key` 的 `AUTHORIZATION_REQUIRED`。
- 宿主应保存 `entry_user_key`，用户授权完成后继续携带同一个值重试。
- 若授权流程中带有 `gateway_api_base_url`，宿主应原样保留，确保授权完成请求回到同一 gateway API 环境。
- `agent_uid` 应表示宿主侧稳定的运行时 agent 标识。
- `conversation_id` 应表示宿主生成的 opaque 会话/安装标识，不绑定 Telegram 或任一单一工具，也不决定账户归属。
- 若需要跨多个会话保持同一账户，应复用同一个 `entry_user_key`。

可信宿主服务端次级模式：

- 若上游是你自己控制且可安全持有 bridge assertion secret 的后端，可继续使用 `POST /agent/skill/bridge/invoke`。
- 该路径仅适用于可信宿主服务端，不适用于 OpenClaw / Codex / Claude 这类第三方入口。

Action payload 模板（public bridge 与可信宿主 bridge 一致）：

- `portal.skill.execute`
```json
{
  "capability": "human_detect",
  "input": { "image_url": "https://files.example.com/demo.png" },
  "request_id": "optional_request_id"
}
```
- `portal.skill.poll`
```json
{ "run_id": "run_123" }
```
- `portal.skill.presentation`
```json
{ "run_id": "run_123", "channel": "web", "include_files": true }
```
- `portal.account.balance`
```json
{}
```
- `portal.account.ledger`
```json
{ "date_from": "2026-03-01", "date_to": "2026-03-15" }
```

agent 侧决策流程：

- 对第三方 agent 入口，优先走 `POST /agent/public-bridge/invoke`，让首次授权直接返回 `authorization_url` 与 `entry_user_key`。
- 新任务：先调 `portal.skill.execute`，再轮询 `portal.skill.poll` 到 `data.terminal=true`，最后调 `portal.skill.presentation`。
- 账户查询：直接调 `portal.account.balance` 或 `portal.account.ledger`。
- `conversation_id` 只做上下文，不是账户主身份。
- 若需要跨多个会话保持同一账户，在第三方入口模式下应复用同一个 `entry_user_key`；不要向公开 bridge 传 `owner_uid_hint`。
- 若返回 `AUTHORIZATION_REQUIRED`，应展示 `authorization_url`，保存 `entry_user_key`，待用户授权后重试同一 action。
- 若 `AUTHORIZATION_REQUIRED` 同时给出 `details.likely_cause=ENTRY_USER_KEY_NOT_REUSED`，不要立即重新拉起授权页；先恢复之前保存的 `entry_user_key`，再重试同一 bridge 调用。
- 若 `details.reauthorization_required=false`，表示该错误优先按“恢复旧 key”处理，而不是要求用户重新登录。
- 若报 `AUTH_UNAUTHORIZED` 且消息是 `agent_uid claim format is invalid`：使用规范化 `agent_uid`（`agent_...`），不要用宿主短别名（如 `assistant`、`planner`）。
- 若报 `SYSTEM_NOT_FOUND` 且消息是 `agent binding not found`：重走同一 bridge 流程一次，让 gateway 自动修复绑定。

输出解析约定：

- 始终按网关 envelope 解析：`request_id`、`data`、`error`。
- 即使 HTTP 工具没有透出状态码，只要 `error` 非空就按失败处理。

## 可视化 Playbook（agent 引导）

- 在视觉类 action 成功返回时（`portal.skill.execute`、`portal.skill.poll`、`portal.skill.presentation`），脚本会在 `data.agent_guidance.visualization.playbook` 注入展示引导。
- 目前已覆盖本公开 skill 对外暴露的视觉能力（检测/分类/关键点/分割/抠图各族）。
- 全局渲染约束（对所有视觉能力生效）：
- 有原生渲染产物时，必须优先使用 skill 返回的 `overlay`/`mask`/`cutout`/`view_url`。
- 默认禁用本地手动画图兜底（`allow_manual_draw=false`），避免 agent 侧绘制差异和未知错误。
- 若缺少渲染产物，只允许基于结构化结果做摘要（`raw`/`visual.spec`），不允许本地补画。
- 特殊规则示例：
- `body-contour-63pt` 在“无渲染产物 + 无几何数据”时，playbook 会标记 `status=degraded` 并推荐 fallback 到 `body-keypoints-2d`。

## Payload 约定

- `portal.skill.execute`：`payload` 必须含 `capability` 和 `input`。
- 可选 `payload.request_id` 会透传给后端。
- `portal.skill.poll`、`portal.skill.presentation`：`payload` 必须含 `run_id`。
- `portal.skill.presentation` 支持 `include_files`（默认 `true`）。
- `portal.account.balance`：`payload` 可省略，传入内容会被忽略。
- `portal.account.ledger`：`payload` 可带 `date_from` + `date_to`（`YYYY-MM-DD`，需成对出现）。

附件归一化：

- 优先使用 `image_url` / `audio_url` / `file_url` / `video_url`。
- 若存在 `attachment.url`，脚本会按 capability 自动映射到目标字段。
- 当宿主显式提供附件 bytes 或显式附件路径时，公开包会先通过 public bridge 自动上传，再把返回的 URL 注入到目标字段。
- 本包没有单独的 `portal.upload` action；对第三方 agent 入口，调用方应继续走 `portal.skill.execute`，只要运行时拿到了显式 bytes/路径，包内脚本会在 execute 前自动上传。
- 如果宿主绕过包内自动上传逻辑而要自己实现上传，第三方/公开入口应使用 `POST /agent/public-bridge/upload-file`，不要使用 `POST /agent/skill/bridge/upload-file`。
- 不支持任意未受控的本地文件系统访问。
- 宿主可使用上传接口（示例）：`/agent/public-bridge/upload-file`。
- `tencent-video-face-fusion` 在执行前必须拿到用户上传的 2 个文件：
  - 源视频 -> `input.video_url`
  - 融合人脸图 -> `input.merge_infos[0].merge_face_image.url`
- 如果腾讯视频换脸缺少任意一个文件，agent 应先提醒用户把视频和人脸图都上传完成，再发起执行。
- 由于腾讯旧版 facefusion 为异步任务且耗时相对更长，测试或冒烟验证时应优先使用较短的源视频。
- 对 `tencent-video-face-fusion` 不要依赖单个 `attachment.url` 自动映射；宿主必须显式传入这两个结构化 URL 字段。

## 错误约定

- 保持网关 envelope：`request_id`、`data`、`error`。
- `POINTS_INSUFFICIENT` 错误会透传 `error.details.recharge_url`。

## 发布包文件

- `scripts/skill.mjs`
- `scripts/agent-task-auth.mjs`
- `scripts/base-url.mjs`
- `scripts/attachment-normalize.mjs`
- `scripts/telemetry.mjs`（兼容占位）
- `references/capabilities.json`
- `references/openapi.json`
- `SKILL.md`
