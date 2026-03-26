#!/usr/bin/env node
/**
 * yixiaoer-pro skill 入口
 *
 * 启动检查：自动检测 YIXIAOER_TOKEN 是否已配置
 * - 已配置：正常执行
 * - 未配置：返回引导提示，让用户在平台配置界面写入系统环境变量
 *
 * 环境变量:
 *   YIXIAOER_TOKEN   - API Token（必填，优先读取系统环境变量）
 *   YIXIAOER_BASE_URL - API Base URL（默认: https://www.yixiaoer.cn/api）
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const TOKEN = process.env.YIXIAOER_TOKEN;
const BASE = process.env.YIXIAOER_BASE_URL || 'https://www.yixiaoer.cn/api';
const PY = 'python3';
const SCRIPT_DIR = path.dirname(require.resolve(__filename));

// ─────────────────────────────────────────
// Token 检查（核心：未配置时引导用户）
// ─────────────────────────────────────────
function checkToken() {
    if (!TOKEN) {
        return {
            error: true,
            code: 'TOKEN_NOT_CONFIGURED',
            message: 'YIXIAOER_TOKEN 未配置',
            hint: '请在 OpenClaw 配置界面添加系统环境变量：\n' +
                  '  变量名：YIXIAOER_TOKEN\n' +
                  '  值：你的蚁小二 API Token\n' +
                  '获取方式：蚁小二官网 → 个人设置 → API Token'
        };
    }
    return null;
}

// ─────────────────────────────────────────
// 通用：执行 Python 脚本并返回 JSON
// ─────────────────────────────────────────
function runPy(scriptName, args = []) {
    return new Promise((resolve, reject) => {
        const scriptPath = path.join(SCRIPT_DIR, 'scripts', scriptName);
        const child = spawn(PY, [scriptPath, ...args], {
            timeout: 120000,
            env: { ...process.env, YIXIAOER_TOKEN: TOKEN, YIXIAOER_BASE_URL: BASE }
        });
        let out = '', err = '';
        child.stdout.on('data', d => out += d.toString());
        child.stderr.on('data', d => err += d.toString());
        child.on('close', code => {
            if (code !== 0) return reject(new Error(err || `exit ${code}`));
            try { resolve(JSON.parse(out)); }
            catch { resolve(out.trim()); }
        });
        child.on('error', reject);
    });
}

// ─────────────────────────────────────────
// 命令: upload
// ─────────────────────────────────────────
async function cmdUpload(videoPath, coverPath) {
    const check = checkToken();
    if (check) return check;

    if (!videoPath || !coverPath) {
        return { error: true, message: '需要提供 videoPath 和 coverPath 两个参数' };
    }
    return runPy('upload_and_publish.py', ['upload', videoPath, coverPath]);
}

// ─────────────────────────────────────────
// 命令: publish
// ─────────────────────────────────────────
async function cmdPublish(videoKey, coverKey, platformAccountId, platform, title, description, tagsJson) {
    const check = checkToken();
    if (check) return check;

    return runPy('upload_and_publish.py', ['publish',
        videoKey, coverKey, platformAccountId, platform,
        title, description, tagsJson
    ]);
}

// ─────────────────────────────────────────
// 命令: status
// ─────────────────────────────────────────
async function cmdStatus(taskSetId) {
    const check = checkToken();
    if (check) return check;

    const args = taskSetId ? ['status', taskSetId] : ['status'];
    return runPy('upload_and_publish.py', args);
}

// ─────────────────────────────────────────
// 命令: accounts（含 token 检查）
// ─────────────────────────────────────────
async function cmdAccounts() {
    const check = checkToken();
    if (check) return check;

    return runPy('upload_and_publish.py', ['accounts']);
}

// ─────────────────────────────────────────
// 命令: validate
// ─────────────────────────────────────────
async function cmdValidate() {
    const check = checkToken();
    if (check) return check;

    return runPy('upload_and_publish.py', ['validate']);
}

// ─────────────────────────────────────────
// 命令: groups
// ─────────────────────────────────────────
async function cmdGroups() {
    const check = checkToken();
    if (check) return check;

    return runPy('upload_and_publish.py', ['groups']);
}

// ─────────────────────────────────────────
// 命令: publish_full
// ─────────────────────────────────────────
async function cmdPublishFull(args) {
    const check = checkToken();
    if (check) return check;

    return runPy('upload_and_publish.py', ['publish_full', ...args]);
}

// ─────────────────────────────────────────
// 命令: publish_batch
// ─────────────────────────────────────────
async function cmdPublishBatch(args) {
    const check = checkToken();
    if (check) return check;

    return runPy('upload_and_publish.py', ['publish_batch', ...args]);
}

// ─────────────────────────────────────────
// 命令: draft
// ─────────────────────────────────────────
async function cmdDraft(args) {
    const check = checkToken();
    if (check) return check;

    return runPy('upload_and_publish.py', ['draft', ...args]);
}

// ─────────────────────────────────────────
// CLI 入口
// ─────────────────────────────────────────
const [, , cmd, ...args] = process.argv;

(async () => {
    // 无命令时显示使用说明（含 token 配置引导）
    if (!cmd) {
        console.log(JSON.stringify({
            usage: `yixiaoer-pro skill

命令:
  upload <videoPath> <coverPath>       上传视频+封面到OSS
  publish <vk> <ck> <目标> <平台> <标题> <描述> <tags>  发布
  publish_full <视频> <封面> <目标> <平台> <标题> <描述> [tags]  完整流程
  publish_batch <分组> <平台> <标题> <描述> <tags>          批量发布
  draft <vk> <ck> <目标> <平台> <标题> <描述> <tags>        存草稿
  validate                                       验证+查账号+查分组
  accounts                                       查询所有账号
  groups                                         查询所有分组
  status [taskSetId]                            查询任务状态

⚠️  首次使用请先配置 YIXIAOER_TOKEN：
    在 OpenClaw 配置界面添加系统环境变量
    变量名：YIXIAOER_TOKEN
    值：你的蚁小二 API Token（登录 yixiaoer.cn → 个人设置 → API Token）
`, tokenStatus: TOKEN ? '已配置' : '未配置'
        }, null, 2));
        return;
    }

    try {
        let result;
        switch (cmd) {
            case 'upload':         result = await cmdUpload(args[0], args[1]); break;
            case 'publish':        result = await cmdPublish(args[0], args[1], args[2], args[3], args[4], args[5], args[6]); break;
            case 'publish_full':  result = await cmdPublishFull(args); break;
            case 'publish_batch': result = await cmdPublishBatch(args); break;
            case 'draft':         result = await cmdDraft(args); break;
            case 'status':       result = await cmdStatus(args[0]); break;
            case 'accounts':     result = await cmdAccounts(); break;
            case 'groups':       result = await cmdGroups(); break;
            case 'validate':     result = await cmdValidate(); break;
            default:
                result = { error: true, message: `未知命令: ${cmd}` };
        }
        console.log(JSON.stringify(result, null, 2));
    } catch (e) {
        console.error(JSON.stringify({ error: true, message: e.message }, null, 2));
        process.exit(1);
    }
})();
