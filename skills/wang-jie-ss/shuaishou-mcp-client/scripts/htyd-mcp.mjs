import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import readline from "node:readline";
import http from "node:http";
import https from "node:https";

function getMcpUrl() {
  return process.env.MCP_URL ?? "https://dz.shuaishou.com/mcp";
}

function getConfigFilePath() {
  return path.join(os.homedir(), ".htyd-mcp-client-streamable.json");
}

function safeReadJson(filePath) {
  try {
    if (!fs.existsSync(filePath)) return null;
    const raw = fs.readFileSync(filePath, "utf8");
    if (!raw.trim()) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function safeWriteJson(filePath, obj) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(obj, null, 2), "utf8");
  } catch {
    // ignore
  }
}

function envAuthorization() {
  const raw = process.env.MCP_AUTHORIZATION;
  if (raw && raw.trim()) return raw.trim();
  const appKey = process.env.MCP_APP_KEY;
  if (appKey && String(appKey).trim()) return `Bearer ${String(appKey).trim()}`;
  return "";
}

function normalizeAuthorizationInput(input) {
  const s = String(input ?? "").trim();
  if (!s) return "";
  if (/^(Bearer|Basic)\s+/i.test(s)) return s;
  return `Bearer ${s}`;
}

function isAuthError(err) {
  const msg = String(err?.message ?? "");
  return msg.startsWith("HTTP 401") || msg.startsWith("HTTP 403");
}

async function promptForAuthorization() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  try {
    const answer = await new Promise((resolve) =>
      rl.question("MCP AppKey/Authorization not set. Please input MCP_APP_KEY (or full 'Bearer xxx'):\n> ", resolve)
    );
    return normalizeAuthorizationInput(answer);
  } finally {
    rl.close();
  }
}

async function getAuthHeadersInteractive({ forcePrompt = false } = {}) {
  const fromEnv = envAuthorization();
  if (!forcePrompt && fromEnv) return { Authorization: fromEnv };

  const configPath = getConfigFilePath();
  const cfg = safeReadJson(configPath) ?? {};
  const fromFile = !forcePrompt && typeof cfg.authorization === "string" ? cfg.authorization.trim() : "";
  if (fromFile) return { Authorization: fromFile };

  const authorization = await promptForAuthorization();
  if (!authorization) return {};

  safeWriteJson(configPath, { ...cfg, authorization });
  return { Authorization: authorization };
}

function usage(exitCode = 1) {
  const msg = `
Usage:
  node htyd-mcp.mjs tools
  node htyd-mcp.mjs call <toolName> <jsonArgs>

Convenience commands (mapped to tool calls):
  node htyd-mcp.mjs login_shuashou --username <u> --password <p> [--loginType <t>]
  node htyd-mcp.mjs list_shops [--platform <p>]
  node htyd-mcp.mjs collect_goods --originList <url1> [--originList <url2> ...] [--ssuid <id>]
  node htyd-mcp.mjs list_collected_goods [--claimStatus 0|1] [--pageNo <n>] [--pageSize <n>]
  node htyd-mcp.mjs claim_goods --itemIds <id1,id2,...> --platId <n> --merchantIds <id1,id2,...>

Env:
  MCP_URL (default: ${getMcpUrl()})
  MCP_APP_KEY (optional; used as Bearer token)
  MCP_AUTHORIZATION (optional; overrides Authorization header)
`;
  // eslint-disable-next-line no-console
  console.error(msg.trim());
  process.exit(exitCode);
}

function parseFlags(argv) {
  const flags = {};
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next == null || next.startsWith("--")) {
        flags[key] = true;
      } else {
        if (flags[key] == null) flags[key] = next;
        else if (Array.isArray(flags[key])) flags[key].push(next);
        else flags[key] = [flags[key], next];
        i++;
      }
    } else {
      positional.push(a);
    }
  }
  return { flags, positional };
}

function normalizeMulti(v) {
  if (v == null) return [];
  return Array.isArray(v) ? v : [v];
}

function csvToList(v) {
  if (v == null) return [];
  return String(v)
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function tryParseJson(v) {
  if (v == null) return v;
  if (typeof v !== "string") return v;
  const s = v.trim();
  if (!s) return v;
  try {
    return JSON.parse(s);
  } catch {
    return v;
  }
}

function extractCollectedItems(payload) {
  const p = tryParseJson(payload);
  if (!p || typeof p !== "object") return [];

  // common shapes:
  // - { data: { list: [...] } }
  // - { list: [...] }
  // - { data: { records: [...] } }
  // - { records: [...] }
  // - { data: [...] }
  const candidates = [
    p?.data?.list,
    p?.list,
    p?.data?.records,
    p?.records,
    p?.data?.data?.list,
    p?.data?.data?.records,
    p?.data,
  ];
  for (const c of candidates) {
    if (Array.isArray(c)) return c;
  }
  return [];
}

function getStringField(obj, keys) {
  for (const k of keys) {
    const v = obj?.[k];
    if (v == null) continue;
    const s = String(v).trim();
    if (s) return s;
  }
  return "";
}

function getIdField(obj) {
  const v =
    obj?.itemId ??
    obj?.item_id ??
    obj?.id ??
    obj?.goodsId ??
    obj?.goods_id;
  if (v == null) return "";
  const s = String(v).trim();
  return s;
}

function isDuplicateCollectedItem(item) {
  // flags
  const boolFlags = [
    item?.duplicate,
    item?.isDuplicate,
    item?.is_duplicate,
    item?.repeat,
    item?.isRepeat,
    item?.is_repeat,
    item?.repeatCollect,
  ];
  if (boolFlags.some((x) => x === true || x === 1 || x === "1")) return true;

  // text hints
  const statusText = getStringField(item, [
    "collectStatusName",
    "collect_status_name",
    "statusName",
    "status_name",
    "message",
    "msg",
  ]);
  if (statusText.includes("重复")) return true;
  return false;
}

function isCollectingItem(item) {
  const statusText = getStringField(item, [
    "collectStatusName",
    "collect_status_name",
    "statusName",
    "status_name",
  ]);
  if (statusText.includes("采集中") || statusText.includes("处理中")) return true;

  const statusCode =
    item?.collectStatus ??
    item?.collect_status ??
    item?.status;
  if (statusCode === 0 || statusCode === "0") return true;
  return false;
}

function isCollectSuccessItem(item) {
  const statusText = getStringField(item, [
    "collectStatusName",
    "collect_status_name",
    "statusName",
    "status_name",
  ]);
  if (statusText.includes("采集成功") || statusText === "成功") return true;

  const statusCode =
    item?.collectStatus ??
    item?.collect_status ??
    item?.status;
  if (statusCode === 1 || statusCode === "1" || statusCode === "SUCCESS") return true;

  return false;
}

function matchOrigin(item, originList) {
  if (!originList?.length) return true;
  const url = getStringField(item, [
    "originUrl",
    "origin_url",
    "originLink",
    "origin_link",
    "sourceUrl",
    "source_url",
    "url",
    "link",
  ]);
  if (!url) return false;
  return originList.some((u) => String(u).trim() && url.includes(String(u).trim()));
}

// Minimal MCP client: Streamable HTTP (POST /mcp JSON-RPC)
// (imports moved to top)

class McpStreamableHttpJsonRpcClient {
  constructor(mcpUrl, headers = {}) {
    this.mcpUrl = mcpUrl;
    this.headers = headers;
    this.msgId = 0;
    this.sessionId = null;
  }

  async connect() {
    // Streamable HTTP 不需要单独建立 SSE 连接；保留接口以兼容现有调用流程
    return;
  }

  async initialize() {
    await this.sendJsonRpc("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "htyd-mcp-client", version: "0.1.0" },
    });
    await this.sendNotification("notifications/initialized");
  }

  async listTools() {
    const result = await this.sendJsonRpc("tools/list", {});
    return result?.tools ?? [];
  }

  async callTool(name, args) {
    const result = await this.sendJsonRpc("tools/call", {
      name,
      arguments: args ?? {},
    });
    if (result?.content?.length) {
      const first = result.content[0];
      if (typeof first?.text === "string") return first.text;
    }
    return result;
  }

  async sendNotification(method) {
    const body = JSON.stringify({ jsonrpc: "2.0", method });
    await this.post(body, null);
  }

  async sendJsonRpc(method, params) {
    const id = ++this.msgId;
    const body = JSON.stringify({ jsonrpc: "2.0", id, method, params });

    const msg = await this.post(body, id);
    if (msg?.error) throw new Error(JSON.stringify(msg.error));
    return msg?.result;
  }

  async post(body, expectedId) {
    const url = new URL(this.mcpUrl);
    const client = url.protocol === "https:" ? https : http;
    const acceptHeader = "application/json, text/event-stream";
    return await new Promise((resolve, reject) => {
      const req = client.request(
        url,
        {
          method: "POST",
          headers: {
            ...this.headers,
            ...(this.sessionId ? { "Mcp-Session-Id": this.sessionId } : {}),
            Accept: acceptHeader,
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(body),
          },
        },
        (res) => {
          if ((res.statusCode ?? 0) >= 400) {
            let data = "";
            res.on("data", (c) => (data += c));
            res.on("end", () =>
              reject(new Error(`HTTP ${res.statusCode}: ${data}`))
            );
            return;
          }

          // Spring AI / MCP Streamable HTTP may respond with JSON or with SSE
          // (`event: message` + `data: {...json...}`).
          const ct = String(res.headers["content-type"] ?? "").toLowerCase();
          const isSse = ct.includes("text/event-stream");

          const sid =
            res.headers["mcp-session-id"] ||
            res.headers["Mcp-Session-Id"] ||
            null;
          if (sid && typeof sid === "string") this.sessionId = sid;

          if (isSse) {
            let resolved = false;
            let buffer = "";

            res.on("data", (chunk) => {
              buffer += chunk.toString("utf8");
              const lines = buffer.split(/\r?\n/);
              buffer = lines.pop() ?? "";

              for (const line of lines) {
                if (resolved) break;
                if (!line.startsWith("data:")) continue;
                const payload = line.slice(5).trim();
                if (!payload) continue;

                try {
                  const obj = JSON.parse(payload);
                  if (expectedId != null) {
                    if (String(obj?.id) !== String(expectedId)) continue;
                  }
                  resolved = true;
                  resolve(obj);
                  res.destroy();
                  break;
                } catch {
                  // ignore non-JSON / partial data lines
                }
              }
            });

            res.on("end", () => {
              if (!resolved) resolve(null);
            });
            return;
          }

          let data = "";
          res.on("data", (c) => (data += c));
          res.on("end", () => {
            try {
              resolve(data ? JSON.parse(data) : null);
            } catch (e) {
              reject(
                new Error(
                  `Invalid JSON response: ${e?.message ?? e}; raw=${String(data).slice(0, 2000)}`
                )
              );
            }
          });
        }
      );
      req.on("error", reject);
      req.write(body);
      req.end();
    });
  }

  close() {
    // no-op
  }
}

async function withClient(fn) {
  let headers = await getAuthHeadersInteractive();
  let client = new McpStreamableHttpJsonRpcClient(getMcpUrl(), headers);
  await client.connect();
  await client.initialize();
  try {
    return await fn(client);
  } catch (e) {
    if (!envAuthorization() && isAuthError(e)) {
      headers = await getAuthHeadersInteractive({ forcePrompt: true });
      client = new McpStreamableHttpJsonRpcClient(getMcpUrl(), headers);
      await client.connect();
      await client.initialize();
      return await fn(client);
    }
    throw e;
  } finally {
    client.close();
  }
}

async function cmdTools() {
  await withClient(async (client) => {
    const tools = await client.listTools();

    // eslint-disable-next-line no-console
    console.log(
      JSON.stringify(
        tools.map((t) => ({
          name: t.name,
          description: t.description,
          inputSchema: t.inputSchema,
        })),
        null,
        2
      )
    );
  });
}

async function cmdCall(toolName, jsonArgs) {
  let args = {};
  if (jsonArgs != null && String(jsonArgs).trim() !== "") {
    try {
      args = JSON.parse(jsonArgs);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(`Invalid JSON args: ${e?.message ?? e}`);
      process.exit(2);
    }
  }

  await withClient(async (client) => {
    const res = await client.callTool(toolName, args);
    // eslint-disable-next-line no-console
    console.log(typeof res === "string" ? res : JSON.stringify(res, null, 2));
  });
}

async function cmdLogin(flags) {
  const username = flags.username;
  const password = flags.password;
  const loginType = flags.loginType;
  if (!username || !password) usage(2);

  await cmdCall(
    "login_shuashou",
    JSON.stringify({
      username,
      password,
      ...(loginType ? { loginType } : {}),
    })
  );
}

async function cmdListShops(flags) {
  const platform = flags.platform;
  await cmdCall(
    "list_shops",
    JSON.stringify(platform ? { platform } : {})
  );
}

async function cmdCollectGoods(flags) {
  const originList = normalizeMulti(flags.originList);
  const ssuid = flags.ssuid;
  if (!originList.length) usage(2);
  await cmdCall(
    "collect_goods",
    JSON.stringify({
      originList,
      ...(ssuid ? { ssuid } : {}),
    })
  );
}

async function cmdListCollectedGoods(flags) {
  const claimStatus =
    flags.claimStatus == null ? undefined : Number(flags.claimStatus);
  const pageNo = flags.pageNo == null ? undefined : Number(flags.pageNo);
  const pageSize = flags.pageSize == null ? undefined : Number(flags.pageSize);

  await cmdCall(
    "list_collected_goods",
    JSON.stringify({
      ...(Number.isFinite(claimStatus) ? { claimStatus } : {}),
      ...(Number.isFinite(pageNo) ? { pageNo } : {}),
      ...(Number.isFinite(pageSize) ? { pageSize } : {}),
    })
  );
}

async function cmdClaimGoods(flags) {
  const itemIds = csvToList(flags.itemIds);
  const originList = normalizeMulti(flags.originList);
  const platId = flags.platId == null ? undefined : Number(flags.platId);
  const merchantIds = csvToList(flags.merchantIds).map((x) => Number(x));
  if (!Number.isFinite(platId) || !merchantIds.length) usage(2);

  // If itemIds are provided explicitly, keep current behavior.
  if (itemIds.length) {
    await cmdCall(
      "claim_goods",
      JSON.stringify({
        itemIds,
        plats: [{ platId, merchantIds }],
      })
    );
    return;
  }

  // Otherwise, auto-pick itemIds from list_collected_goods
  if (!originList.length) {
    // eslint-disable-next-line no-console
    console.error(
      "claim_goods: 请传 --itemIds 或 --originList（将从 list_collected_goods 自动筛选可认领商品）"
    );
    usage(2);
  }

  await withClient(async (client) => {
    const listRes = await client.callTool("list_collected_goods", {
      claimStatus: 0,
      pageNo: 1,
      pageSize: 200,
    });

    const items = extractCollectedItems(listRes);
    const matched = items.filter((it) => matchOrigin(it, originList));
    const eligible = matched
      .filter((it) => isCollectSuccessItem(it))
      .filter((it) => !isDuplicateCollectedItem(it))
      .filter((it) => !isCollectingItem(it));

    const pickedIds = eligible
      .map((it) => getIdField(it))
      .filter(Boolean);

    // eslint-disable-next-line no-console
    console.error(
      `claim_goods auto-pick: total=${items.length}, matched=${matched.length}, eligible=${eligible.length}, pickedIds=${pickedIds.length}`
    );

    if (!pickedIds.length) {
      // eslint-disable-next-line no-console
      console.error(
        "未找到可认领商品：要求【采集成功】【非重复采集】【非采集中】且链接匹配 originList"
      );
      process.exit(3);
    }

    const res = await client.callTool("claim_goods", {
      itemIds: pickedIds,
      plats: [{ platId, merchantIds }],
    });

    // eslint-disable-next-line no-console
    console.log(typeof res === "string" ? res : JSON.stringify(res, null, 2));
  });
}

async function main() {
  const argv = process.argv.slice(2);
  const cmd = argv[0];
  if (!cmd) usage(0);

  if (cmd === "tools") return await cmdTools();
  if (cmd === "call") {
    const toolName = argv[1];
    const jsonArgs = argv[2] ?? "{}";
    if (!toolName) usage(2);
    return await cmdCall(toolName, jsonArgs);
  }

  const { flags } = parseFlags(argv.slice(1));
  if (cmd === "login_shuashou") return await cmdLogin(flags);
  if (cmd === "list_shops") return await cmdListShops(flags);
  if (cmd === "collect_goods") return await cmdCollectGoods(flags);
  if (cmd === "list_collected_goods") return await cmdListCollectedGoods(flags);
  if (cmd === "claim_goods") return await cmdClaimGoods(flags);

  usage(2);
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e);
  process.exit(1);
});

