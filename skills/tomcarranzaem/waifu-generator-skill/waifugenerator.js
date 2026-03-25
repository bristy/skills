#!/usr/bin/env node
import { readFileSync } from "fs";
import { homedir } from "os";
import { join } from "path";

// --- CLI args ---
const args = process.argv.slice(2);
let prompt = null;
let size = "portrait";
let tokenFlag = null;
let refPictureUuid = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--size" && args[i + 1]) {
    size = args[++i];
  } else if (args[i] === "--token" && args[i + 1]) {
    tokenFlag = args[++i];
  } else if (args[i] === "--ref" && args[i + 1]) {
    refPictureUuid = args[++i];
  } else if (!args[i].startsWith("--") && prompt === null) {
    prompt = args[i];
  }
}

if (!prompt) {
  prompt = "waifu generator, high quality AI art, detailed illustration";
}

// --- Token resolution ---
function readEnvFile(filePath) {
  try {
    const expanded = filePath.replace(/^~/, homedir());
    const content = readFileSync(expanded, "utf8");
    const match = content.match(/NETA_TOKEN=(.+)/);
    return match ? match[1].trim() : null;
  } catch {
    return null;
  }
}

function resolveToken() {
  if (tokenFlag) return tokenFlag;
  if (process.env.NETA_TOKEN) return process.env.NETA_TOKEN;
  const fromWorkspace = readEnvFile("~/.openclaw/workspace/.env");
  if (fromWorkspace) return fromWorkspace;
  const fromClawhouse = readEnvFile("~/developer/clawhouse/.env");
  if (fromClawhouse) return fromClawhouse;
  return null;
}

const TOKEN = resolveToken();
if (!TOKEN) {
  console.error('\n✗ NETA_TOKEN not found.');
  console.error('  Global: sign up at https://www.neta.art/ → get token at https://www.neta.art/open/');
  console.error('  China:  sign up at https://app.nieta.art/ → get token at https://app.nieta.art/security');
  console.error('  Then:   export NETA_TOKEN=your_token_here');
  process.exit(1);
}

// --- Size map ---
const SIZE_MAP = {
  square:    { width: 1024, height: 1024 },
  portrait:  { width: 832,  height: 1216 },
  landscape: { width: 1216, height: 832  },
  tall:      { width: 704,  height: 1408 },
};

const dimensions = SIZE_MAP[size] ?? SIZE_MAP.portrait;

// --- Headers ---
const HEADERS = {
  "x-token": TOKEN,
  "x-platform": "nieta-app/web",
  "content-type": "application/json",
};

// --- Build request body ---
const body = {
  storyId: "DO_NOT_USE",
  jobType: "universal",
  rawPrompt: [{ type: "freetext", value: prompt, weight: 1 }],
  width: dimensions.width,
  height: dimensions.height,
  meta: { entrance: "PICTURE,CLI" },
};

if (refPictureUuid) {
  body.inherit_params = {
    collection_uuid: refPictureUuid,
    picture_uuid: refPictureUuid,
  };
}

// --- Submit job ---
async function submitJob() {
  const res = await fetch(`${process.env.NETA_API_URL || 'https://api.talesofai.cn'}/v3/make_image`, {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to submit job (${res.status}): ${text}`);
  }

  const data = await res.json();
  if (typeof data === "string") return data;
  if (data.task_uuid) return data.task_uuid;
  throw new Error(`Unexpected response: ${JSON.stringify(data)}`);
}

// --- Poll for result ---
async function pollTask(taskUuid) {
  const url = `${process.env.NETA_API_URL || 'https://api.talesofai.cn'}/v1/artifact/task/${taskUuid}`;
  const MAX_ATTEMPTS = 90;
  const INTERVAL_MS = 2000;

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    await new Promise((r) => setTimeout(r, INTERVAL_MS));

    const res = await fetch(url, { headers: HEADERS });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Poll failed (${res.status}): ${text}`);
    }

    const data = await res.json();
    const status = data.task_status;

    if (['PENDING', 'MODERATION'].includes(status)) { continue; }
  if (['FAILURE', 'TIMEOUT', 'DELETED', 'ILLEGAL_IMAGE'].includes(status)) {
    console.error('Error: generation failed with status ' + status + (pollData.err_msg ? ' — ' + pollData.err_msg : ''));
    process.exit(1);
  }

    // Done — extract image URL
    const imageUrl =
      data.artifacts?.[0]?.url ?? data.result_image_url ?? null;

    if (!imageUrl) {
      throw new Error(`Task finished but no image URL found: ${JSON.stringify(data)}`);
    }

    return imageUrl;
  }

  throw new Error("Timed out waiting for image generation after 90 attempts.");
}

// --- Main ---
(async () => {
  try {
    const taskUuid = await submitJob();
    const imageUrl = await pollTask(taskUuid);
    console.log(imageUrl);
    process.exit(0);
  } catch (err) {
    console.error("Error:", err.message);
    process.exit(1);
  }
})();
