#!/usr/bin/env node
import { readFileSync } from "fs";
import { homedir } from "os";
import { join } from "path";

// --- Argument parsing ---
const args = process.argv.slice(2);
let prompt = null;
let size = "portrait";
let tokenFlag = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--size" && args[i + 1]) {
    size = args[++i];
  } else if (args[i] === "--token" && args[i + 1]) {
    tokenFlag = args[++i];
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

const TOKEN =
  tokenFlag ||
  process.env.NETA_TOKEN ||
  readEnvFile("~/.openclaw/workspace/.env") ||
  readEnvFile("~/developer/clawhouse/.env");

if (!TOKEN) {
  console.error("Error: NETA_TOKEN not found. Set via --token, NETA_TOKEN env var, ~/.openclaw/workspace/.env, or ~/developer/clawhouse/.env");
  process.exit(1);
}

// --- Size map ---
const SIZES = {
  square:    { width: 1024, height: 1024 },
  portrait:  { width: 832,  height: 1216 },
  landscape: { width: 1216, height: 832  },
  tall:      { width: 704,  height: 1408 },
};

const { width, height } = SIZES[size] ?? SIZES.portrait;

// --- Headers ---
const HEADERS = {
  "x-token": TOKEN,
  "x-platform": "nieta-app/web",
  "content-type": "application/json",
};

// --- Submit image generation job ---
async function submitJob() {
  const body = {
    storyId: "DO_NOT_USE",
    jobType: "universal",
    rawPrompt: [{ type: "freetext", value: prompt, weight: 1 }],
    width,
    height,
    meta: { entrance: "PICTURE,VERSE" },
  };

  const res = await fetch("https://api.talesofai.cn/v3/make_image", {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error(`Error submitting job (${res.status}): ${text}`);
    process.exit(1);
  }

  const data = await res.json();
  if (typeof data === "string") return data;
  if (data.task_uuid) return data.task_uuid;
  console.error("Unexpected response:", JSON.stringify(data));
  process.exit(1);
}

// --- Poll for result ---
async function pollTask(taskUuid) {
  const url = `https://api.talesofai.cn/v1/artifact/task/${taskUuid}`;
  const PENDING_STATUSES = new Set(["PENDING", "MODERATION"]);
  const MAX_ATTEMPTS = 90;
  const INTERVAL_MS = 2000;

  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    await new Promise((r) => setTimeout(r, INTERVAL_MS));

    const res = await fetch(url, { headers: HEADERS });
    if (!res.ok) {
      const text = await res.text();
      console.error(`Poll error (${res.status}): ${text}`);
      process.exit(1);
    }

    const data = await res.json();
    const status = data.task_status;

    if (PENDING_STATUSES.has(status)) continue;

    // Done — extract image URL
    const imageUrl =
      data.artifacts?.[0]?.url ||
      data.result_image_url;

    if (!imageUrl) {
      console.error("Job finished but no image URL found:", JSON.stringify(data));
      process.exit(1);
    }

    console.log(imageUrl);
    process.exit(0);
  }

  console.error("Timed out waiting for image generation.");
  process.exit(1);
}

// --- Main ---
const taskUuid = await submitJob();
await pollTask(taskUuid);
