---
name: htyd-mcp-client-streamable
description: Builds and uses an MCP client (Streamable HTTP transport) to connect to the htyd MCP server and invoke all available tools (including login). Use when connecting to a Streamable HTTP MCP endpoint like https://dz.shuaishou.com/mcp.
---

# HTYD MCP Client (Streamable HTTP)

## Goal

Provide an **MCP client-first** wrapper for MCP servers exposed via **Streamable HTTP** transport (`/mcp`). This is intended for hosts (e.g. OpenClaw) that **do not support MCP connections natively**: install a tiny Node client and use it to **list/call all MCP tools**, including **login**.

Default endpoint:

- `MCP_URL=https://dz.shuaishou.com/mcp`
- `MCP_APP_KEY=<your_app_key>` (sent as `Authorization: Bearer ...`)

## Quick start (OpenClaw / any shell)

1) Ensure the MCP server is reachable (it must expose Streamable HTTP at `https://dz.shuaishou.com/mcp`).

2) Install the client dependencies once:

```bash
cd "%USERPROFILE%\.agents\skills\htyd-mcp-client-streamable-0.1.0\scripts"
npm install
```

3) List tools:

```bash
node htyd-mcp.mjs tools
```

4) Call any tool (raw JSON arguments):

```bash
node htyd-mcp.mjs call list_shops "{}"
node htyd-mcp.mjs call list_collected_goods "{\"claimStatus\":0,\"pageNo\":1,\"pageSize\":50}"
```

5) Login (required by some flows):

```bash
node htyd-mcp.mjs login_shuashou --username "YOUR_USER" --password "YOUR_PASS" --loginType "pd"
```

6) Collect goods:

```bash
node htyd-mcp.mjs collect_goods --originList "https://detail.1688.com/offer/xxx.html"
```

7) Claim goods to a shop:

```bash
node htyd-mcp.mjs claim_goods --itemIds 35476703,35476704 --platId 68 --merchantIds 2025050918
```

Notes:

- `collect_goods` can be called repeatedly for the same URL(s).
- For claiming, it is recommended to use `--originList` instead of `--itemIds`.
  - The client will call `list_collected_goods` and auto-pick `itemIds` that are:
    - collected successfully (采集成功)
    - NOT duplicate collection (非重复采集)
    - NOT collecting/in progress (非采集中)

Example (recommended):

```bash
node htyd-mcp.mjs claim_goods --originList "https://detail.1688.com/offer/xxx.html" --platId 68 --merchantIds 2025050918
```

## Tool coverage (current `user-htyd-mcp`)

This wrapper is expected to expose **all current tools**:

- `login_shuashou` (required)
- `list_shops`
- `collect_goods`
- `list_collected_goods`
- `claim_goods`

If new tools are added server-side later, use `tools` to discover them and call them via `call`.

## Configuration

Environment variables:

- `MCP_URL` (optional): MCP endpoint URL. Default `https://dz.shuaishou.com/mcp`.
- `MCP_APP_KEY` (optional): AppKey (sent as `Authorization: Bearer ...`).
- `MCP_AUTHORIZATION` (optional): Full Authorization header value; overrides `MCP_APP_KEY`.

First run / missing API key:

- If `MCP_APP_KEY`/`MCP_AUTHORIZATION` is not provided (or loading fails with 401/403), the client will prompt you to input it.
- The value will be saved to: `~/.htyd-mcp-client-streamable.json` and reused automatically next time.

## Operational checklist

When OpenClaw needs to use the MCP tools:

1. Run `tools` once to verify connectivity.
2. If tool needs authentication, call `login_shuashou` first.
3. Then call domain tools (`list_shops`, `collect_goods`, `list_collected_goods`, `claim_goods`).

