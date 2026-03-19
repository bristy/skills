---
name: ai-task-hub
description: AI task hub for image analysis, background removal, speech-to-text, text-to-speech, markdown conversion, points balance/ledger lookup, and async execute/poll/presentation orchestration. Use when users need hosted AI outcomes while host runtime manages identity, credits, payment, and risk control.
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

# AI Task Hub

Formerly `skill-hub-gateway`.

Public package boundary:

- Only orchestrates `portal.skill.execute`, `portal.skill.poll`, `portal.skill.presentation`, `portal.account.balance`, and `portal.account.ledger`.
- Does not exchange `api_key` or `userToken` inside this package.
- Does not handle recharge or payment flows inside this package.
- Prefers attachment URLs, and when host runtime explicitly exposes attachment bytes or an explicit attachment path, auto-uploads through the public bridge and injects the returned URL.
- Third-party agent entry uses `POST /agent/public-bridge/invoke`.

## User-Facing Response Policy

- When users upload images, audio, documents, or video and ask for a capability, treat the input as ready to process and prefer executing immediately, then return results, progress, or the smallest necessary next step.
- Do not explain `image_url`, `attachment.url`, storage URLs, bridge layers, host uploads, input normalization, or controlled media domain details to end users unless they explicitly ask for technical debugging.
- Do not ask end users to provide manual URLs, JSON field names, or upload-chain instructions; those are internal host-to-skill mechanics.
- If the runtime supports attachment handling, complete upload, transfer, URL injection, and execute/poll/presentation orchestration silently.
- Only when execution actually fails and the user must intervene should you mention missing processable files, incomplete authorization, or retry guidance, using user-oriented language without exposing internal layering.

Chinese documentation: `SKILL.zh-CN.md`

## When to Use This Skill

Use this skill when the user asks to:

- detect faces, human presence, body keypoints, image tags, or facial emotion from images
- generate person/product segmentation, mask, cutout, or matting outputs that this public package explicitly exposes
- transcribe uploaded audio into text (`speech to text`, `audio transcription`)
- generate speech from text input (`text to speech`, `voice generation`)
- convert uploaded files into markdown (`document to markdown`)
- start async jobs and check status later (`poll`, `check job status`)
- fetch rendered visual outputs such as `overlay`, `mask`, and `cutout`
- run embedding or reranking tasks for retrieval workflows
- check current account points balance or recent points ledger rows

## Common Requests

Example requests that should trigger this skill:

- "Detect faces in this image and return bounding boxes."
- "Tag this image and summarize the main objects."
- "Remove the background from this product photo."
- "Create a clean cutout from this portrait image."
- "Transcribe this meeting audio into text."
- "Generate speech from this paragraph."
- "Convert this PDF file into markdown."
- "Start this job now and let me poll the run status later."
- "Fetch overlay and mask files for run_456."
- "Generate embeddings for this text list and rerank the candidates."
- "Check my current points balance."
- "Show my recent points ledger from 2026-03-01 to 2026-03-15."

## Search-Friendly Capability Aliases

- `vision` aliases: face detection, human detection, person detection, image tagging
- `background` aliases: remove background, background removal, cutout, matting, product-cutout
- `asr` aliases: speech to text, audio transcription, transcribe audio
- `tts` aliases: text to speech, voice generation, speech synthesis
- `markdown_convert` aliases: document to markdown, file to markdown, markdown conversion
- `poll` aliases: check job status, poll long-running task, async run status
- `presentation` aliases: rendered output, overlay, mask, cutout files
- `account.balance` aliases: points balance, credits balance, remaining points
- `account.ledger` aliases: points ledger, credits history, points statement
- `embeddings/reranker` aliases: vectorization, semantic vectors, relevance reranking

Public discovery boundary for visual capabilities:

- This published skill only advertises visual capabilities whose backing services are currently enabled for public delivery.
- Disabled or internally retained legacy routes are intentionally omitted from discovery references and capability manifests even if related backend code still exists.

## Runtime Contract

Default API base URL: `https://gateway-api.binaryworks.app`
Published package policy: outbound base URL is locked to the default API base URL to reduce token exfiltration risk.

Action to endpoint mapping:

- `portal.skill.execute` -> `POST /agent/skill/execute`
- `portal.skill.poll` -> `GET /agent/skill/runs/:run_id`
- `portal.skill.presentation` -> `GET /agent/skill/runs/:run_id/presentation`
- `portal.account.balance` -> `GET /agent/skill/account/balance`
- `portal.account.ledger` -> `GET /agent/skill/account/ledger`

## Install Mechanism & Runtime Requirements

- This skill is instruction-first and does not define a remote installer flow.
- Runtime execution is limited to bundled local scripts under `scripts/*.mjs`.
- Required runtime binary is `node` (as declared in `metadata.openclaw.requires.bins`).
- No remote download-to-exec install chain is used (`curl|wget ... | sh|bash|python|node` is not part of this package).

## Auth Contract

Third-party agent entry mode (recommended):

- Use `POST /agent/public-bridge/invoke` as the first entrypoint for OpenClaw / Codex / Claude style runtimes.
- Do not require end users to provide any credential.
- On first use without an existing binding, gateway returns `AUTHORIZATION_REQUIRED` with `authorization_url` and `entry_user_key`.
- The returned `authorization_url` may include `gateway_api_base_url`; preserve it when completing browser authorization so `/agent-auth/complete` is posted back to the same API environment that created the auth session.
- Host/runtime should show `authorization_url` to the user, persist `entry_user_key`, then retry the same action with that same `entry_user_key`.
- If gateway later returns `AUTHORIZATION_REQUIRED` with `details.likely_cause=ENTRY_USER_KEY_NOT_REUSED`, `details.recovery_action=REUSE_ENTRY_USER_KEY`, and `details.reauthorization_required=false`, host should restore the previously persisted `entry_user_key` and retry without sending the user through browser authorization again.

Identifier format constraints used by gateway auth:

- `agent_uid` must match `^agent_[a-z0-9][a-z0-9_-]{5,63}$`.
- `conversation_id` must match `^[A-Za-z0-9._:-]{8,128}$`.
- In deployed bridge mode, host may pass its own stable runtime agent identifier and the gateway bridge will canonicalize it server-side.

Host-side token bridge (outside published package):

- To keep this package compliant and low-privilege, this published runtime does not issue or accept caller-managed task tokens.
- Preferred deployed bridge endpoint for third-party agent entry: `POST /agent/public-bridge/invoke`.
- Trusted host runtime that can safely hold bridge assertion secret may continue to use `POST /agent/skill/bridge/invoke`.
- These bridge endpoints are served by gateway runtime, not bundled into this published package, and do not require caller-managed credentials.
- Bridge request body should include `action`, `agent_uid`, `conversation_id`, and optional `payload`.
- `conversation_id` should be a host-generated opaque session/install identifier, not a public chat ID, raw thread ID, or PII.
- Public bridge should resolve a stable external user binding when available; if the binding is missing, gateway returns a host-owned authorization URL plus `entry_user_key` so user can complete first-time binding in browser.
- Cross-conversation account continuity requires reusing the same `entry_user_key`; public bridge intentionally does not accept owner overrides.
- Gateway bridge will canonicalize `agent_uid`, repair binding when missing, issue short-lived internal task token, and run the action server-side.
- `portal.skill.execute` through public bridge is write-capable and should send `options.confirm_write=true` after user confirmation; otherwise gateway may return `ACTION_CONFIRMATION_REQUIRED`.
- `base_url`, `gateway_api_key`, `api_key`, `user_token`, `agent_task_token`, `owner_uid_hint`, and `install_channel` overrides are rejected by the deployed bridge endpoint.
- Recommended host behavior: persist `entry_user_key`, normalize `agent_uid`, and re-run the same bridge action after authorization completes.

Host integration modes:

- `interactive` (recommended): host calls `POST /agent/public-bridge/invoke`, surfaces the returned host-owned authorization URL to the user when needed, persists returned `entry_user_key`, and retries after authorization completes.
- `trusted host bridge` (secondary): a trusted backend you control may call `POST /agent/skill/bridge/invoke` with its own bridge assertion secret.
- Published skill package itself does not open browser, persist credentials, or perform OAuth/token exchange flows.
- The authorization URL above is owned by deployed gateway/admin-web pages, not by this skill package runtime.

## Agent Invocation Quickstart

Preferred invocation mode for third-party agent entry (recommended):

- Deployed bridge API:
```json
{
  "entry_host": "openclaw",
  "action": "portal.account.balance",
  "agent_uid": "support_assistant",
  "conversation_id": "host_session_20260316_opaque_001",
  "payload": {}
}
```

- Send that body to `POST /agent/public-bridge/invoke`.
- This is the recommended production entrypoint for third-party agent-friendly integration.
- On first use, gateway may return `AUTHORIZATION_REQUIRED` with `authorization_url` and `entry_user_key`.
- Persist `entry_user_key` and retry with the same value after user authorization completes.
- Preserve any `gateway_api_base_url` embedded in the authorization flow so the completion request lands on the same gateway API environment.
- `agent_uid` should be your host-defined stable runtime agent identifier.
- `conversation_id` should be your host-generated opaque session/install identifier; it is not tied to Telegram or any single tool and does not determine account ownership.
- Use the same `entry_user_key` across conversations when those conversations should share one account.

Trusted host runtime secondary mode:

- If you control the upstream backend and it can safely hold bridge assertion secret, use `POST /agent/skill/bridge/invoke`.
- This path is for trusted host runtime only, not OpenClaw / Codex / Claude style third-party entry.

Action payload templates (same for public bridge and trusted host bridge mode):

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

Agent-side decision flow:

- Always prefer `POST /agent/public-bridge/invoke` for third-party agent entry so first-time authorization can return `authorization_url` plus `entry_user_key`.
- New task: call `portal.skill.execute`, then poll with `portal.skill.poll` until `data.terminal=true`, then fetch `portal.skill.presentation`.
- Account query: call `portal.account.balance` or `portal.account.ledger` directly.
- Keep `conversation_id` as session context only; do not use it as the account key.
- For cross-conversation continuity in third-party entry mode, persist and reuse the same `entry_user_key`; do not pass `owner_uid_hint` to the public bridge endpoint.
- If `AUTHORIZATION_REQUIRED` is returned, show `authorization_url`, persist `entry_user_key`, then retry the same action after user authorization completes.
- If `AUTHORIZATION_REQUIRED` includes `details.likely_cause=ENTRY_USER_KEY_NOT_REUSED`, do not open a new auth flow yet; first restore the previously persisted `entry_user_key` and retry the same bridge call.
- Treat `details.reauthorization_required=false` as a recovery hint that browser re-login is unnecessary for this failure mode.
- If `AUTH_UNAUTHORIZED` + `agent_uid claim format is invalid`: use canonical `agent_uid` (`agent_...`) instead of a short host alias (`assistant`, `planner`).
- If `SYSTEM_NOT_FOUND` + `agent binding not found`: restart the same bridge flow once and let gateway repair binding.

Output parsing contract:

- Always parse standard gateway envelope: `request_id`, `data`, `error`.
- Treat non-empty `error` as failure even when HTTP tooling hides status code.

## Visualization Playbooks (Agent Guidance)

- For successful visual actions (`portal.skill.execute`, `portal.skill.poll`, `portal.skill.presentation`), the script enriches responses with `data.agent_guidance.visualization.playbook`.
- Playbook mapping covers the visual capabilities currently exposed by this published skill (detection/classification/keypoints/segmentation/matting families).
- Global rendering guardrail for all visual capabilities:
- Must use skill-native rendered assets first (`overlay`/`mask`/`cutout`/`view_url`) when available.
- Manual local drawing fallback is disabled by default (`allow_manual_draw=false`) to avoid inconsistent agent-side rendering.
- If rendered assets are missing, fallback is summary-only from structured output (`raw`/`visual.spec`), not local drawing.
- Example special rule:
- `body-contour-63pt` -> when both rendered assets and geometry are absent, playbook marks `status=degraded` and recommends fallback capability `body-keypoints-2d`.

## Payload Contract

- `portal.skill.execute`: payload requires `capability` and `input`.
- `payload.request_id` is optional and passed through.
- `portal.skill.poll` and `portal.skill.presentation`: payload requires `run_id`.
- `portal.skill.presentation` supports `include_files` (defaults to `true`).
- `portal.account.balance`: payload is optional and ignored.
- `portal.account.ledger`: payload may include `date_from` + `date_to` (`YYYY-MM-DD`, must be provided together).

Attachment normalization:

- Prefer explicit `image_url` / `audio_url` / `file_url` / `video_url`.
- `attachment.url` is mapped to target media field by capability.
- When host runtime exposes attachment bytes or an explicit attachment path, this published package auto-uploads through the public bridge and injects the returned URL before execute.
- There is no separate `portal.upload` action in this package; for third-party agent entry, callers should keep using `portal.skill.execute`, and the bundled runtime will auto-upload explicit bytes/path inputs when available.
- If a host bypasses the bundled auto-upload helper and implements upload itself, use `POST /agent/public-bridge/upload-file` for third-party/public entry, not `POST /agent/skill/bridge/upload-file`.
- Arbitrary unmanaged local filesystem access remains unsupported.
- Example host upload endpoint: `/agent/public-bridge/upload-file`.
- `tencent-video-face-fusion` requires 2 uploaded files from the user before execution:
  - source video -> `input.video_url`
  - merge face image -> `input.merge_infos[0].merge_face_image.url`
- If either Tencent face fusion file is missing, agent should ask the user to upload both files first.
- Prefer a short source video for testing or smoke runs because Tencent legacy facefusion jobs are asynchronous and slower than image-only tasks.
- Do not rely on a single `attachment.url` auto-mapping for `tencent-video-face-fusion`; host must pass both structured URL fields explicitly.

## Error Contract

- Preserve gateway envelope: `request_id`, `data`, `error`.
- Preserve `POINTS_INSUFFICIENT` and pass through `error.details.recharge_url`.

## Bundled Files

- `scripts/skill.mjs`
- `scripts/agent-task-auth.mjs`
- `scripts/base-url.mjs`
- `scripts/attachment-normalize.mjs`
- `scripts/telemetry.mjs` (compatibility shim)
- `references/capabilities.json`
- `references/openapi.json`
- `SKILL.zh-CN.md`
