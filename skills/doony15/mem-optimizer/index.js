/**
 * MemOptimizer - 记忆优化器
 * 整合 self-improving 机制，自动统计、压缩和优化记忆文件
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Token 估算：1 token ≈ 4 个字符（英文）或 2 个字符（中文）
const CHARS_PER_TOKEN_ZH = 2;
const CHARS_PER_TOKEN_EN = 4;

/**
 * 估算文本的 token 数量
 */
function estimateTokens(text) {
  const zhCount = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
  const enCount = text.length - zhCount;
  return Math.round(zhCount / CHARS_PER_TOKEN_ZH + enCount / CHARS_PER_TOKEN_EN);
}

/**
 * 扫描 memory 目录，获取文件信息
 */
async function scanMemoryFiles(workspacePath) {
  const memoryDir = path.join(workspacePath, 'memory');
  const files = [];
  let totalTokens = 0;
  
  try {
    // 检查 memory 目录是否存在
    if (!fsSync.existsSync(memoryDir)) {
      return { files, totalTokens };
    }
    
    // 读取 memory 目录下的所有 .md 文件
    const entries = await fs.readdir(memoryDir, { withFileTypes: true });
    
    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith('.md')) {
        const filePath = path.join(memoryDir, entry.name);
        const content = await fs.readFile(filePath, 'utf-8');
        const lines = content.split('\n').length;
        const tokens = estimateTokens(content);
        
        files.push({
          name: entry.name,
          path: filePath,
          lines,
          tokens
        });
        
        totalTokens += tokens;
      }
    }
    
    // 按修改时间排序（最新的在前）
    files.sort((a, b) => {
      try {
        const statA = fsSync.statSync(a.path);
        const statB = fsSync.statSync(b.path);
        return statB.mtimeMs - statA.mtimeMs;
      } catch (e) {
        return 0;
      }
    });
    
  } catch (error) {
    console.error('Error scanning memory files:', error);
  }
  
  return { files, totalTokens };
}

/**
 * 读取 self-improving 的偏好和学习记录
 */
async function loadSelfImprovingPreferences() {
  const workspacePath = process.cwd();
  const preferencesPath = path.join(workspacePath, 'self-improving', 'preferences.md');
  const correctionsPath = path.join(workspacePath, 'self-improving', 'corrections.md');
  const reflectionsPath = path.join(workspacePath, 'self-improving', 'reflections.md');
  
  const preferences = {
    compressionThreshold: 50,
    maxSummaryLines: 20,
    defaultCompressionRatio: 0.4,
    learnedPatterns: []
  };
  
  try {
    // 读取已确认的偏好
    if (fsSync.existsSync(preferencesPath)) {
      const content = await fs.readFile(preferencesPath, 'utf-8');
      // 解析偏好设置
      const thresholdMatch = content.match(/compressionThreshold[:\s]+(\d+)/i);
      if (thresholdMatch) preferences.compressionThreshold = parseInt(thresholdMatch[1]);
      
      const linesMatch = content.match(/maxSummaryLines[:\s]+(\d+)/i);
      if (linesMatch) preferences.maxSummaryLines = parseInt(linesMatch[1]);
      
      // 读取确认的学习模式
      if (fsSync.existsSync(reflectionsPath)) {
        const reflections = await fs.readFile(reflectionsPath, 'utf-8');
        const patterns = reflections.match(/```json[\s\S]*?```/g);
        if (patterns) {
          patterns.forEach(p => {
            try {
              const jsonMatch = p.match(/\{[\s\S]*\}/);
              if (jsonMatch) {
                const obj = JSON.parse(jsonMatch[0]);
                if (obj.status === 'Confirmed') {
                  preferences.learnedPatterns.push(obj);
                }
              }
            } catch (e) {}
          });
        }
      }
    }
  } catch (err) {
    console.error('Error loading self-improving preferences:', err);
  }
  
  return preferences;
}

/**
 * 记录优化反思到 self-improving
 */
async function logReflection(optimizeResult, userFeedback = null) {
  const workspacePath = process.cwd();
  const reflectionsPath = path.join(workspacePath, 'self-improving', 'reflections.md');
  const correctionsPath = path.join(workspacePath, 'self-improving', 'corrections.md');
  
  const date = new Date().toISOString().split('T')[0];
  const timestamp = new Date().toISOString();
  
  const reflection = {
    date,
    timestamp,
    type: 'memory_optimization',
    stats: {
      freedTokens: optimizeResult.stats?.freedTokens || 0,
      summarizedTokens: optimizeResult.stats?.summarizedTokens || 0,
      filesProcessed: optimizeResult.stats?.filesProcessed || 0
    },
    userFeedback,
    status: 'Tentative', // Tentative, Emerging, Pending, Confirmed, Archived
    confidence: 'low'
  };
  
  const reflectionText = `
## [${date}] - Memory Optimization

**What I did:** Compressed ${optimizeResult.stats?.filesProcessed} memory files, freed ${optimizeResult.stats?.freedTokens} tokens
**Outcome:** ${userFeedback || 'Pending user feedback'}
**Reflection:** Compression ratio of ${(optimizeResult.stats?.compressionRatio || 0).toFixed(2)*100}% was applied
**Lesson:** ${userFeedback === 'approved' ? 'Compression was acceptable' : 'Need to adjust strategy'}
**Status:** ${reflection.status}
\`\`\`json
${JSON.stringify(reflection, null, 2)}
\`\`\`
`;
  
  try {
    // 记录到 reflections.md
    await fs.appendFile(reflectionsPath, reflectionText, 'utf-8');
    
    // 如果有负面反馈，记录到 corrections.md
    if (userFeedback === 'negative' || userFeedback === 'too aggressive') {
      const correction = `
- **Date:** ${timestamp}
- **Type:** Over-compression warning
- **Action:** Increase compression threshold
- **Current threshold:** ${reflection.stats.freedTokens} tokens freed
- **Note:** User requested more details retained
`;
      await fs.appendFile(correctionsPath, correction, 'utf-8');
    }
  } catch (err) {
    console.error('Error logging reflection:', err);
  }
  
  return reflection;
}

/**
 * 压缩记忆内容（简单摘要生成）
 */
function summarizeContent(content, maxLines = 20, compressionRatio = 0.4) {
  const lines = content.split('\n');
  if (lines.length <= maxLines) return content;
  
  const result = [];
  let summaryAdded = false;
  const keepLines = Math.floor(lines.length * compressionRatio);
  
  for (let i = 0; i < lines.length; i++) {
    if (i === 0) {
      result.push(lines[i]); // 标题
      continue;
    }
    
    if (i === 1 && lines[i].trim() === '') {
      // 在标题后的空行添加压缩信息
      result.push(lines[i]);
      continue;
    }
    
    if (summaryAdded) {
      break;
    }
    
    // 保留关键行（标题附近）
    if (i < 5) {
      result.push(lines[i]);
      continue;
    }
    
    // 压缩模式：保留前 40% 的内容
    if (i <= keepLines) {
      result.push(lines[i]);
    } else if (i === keepLines) {
      // 添加压缩摘要
      result.push('');
      result.push(`> 📝 **已压缩**: 原内容 ${lines.length} 行，保留 ${keepLines} 行关键信息`);
      result.push('');
      result.push('... [内容已压缩，可通过 mem_optimize({dryRun: false}) 查看完整日志]');
      summaryAdded = true;
      break;
    }
  }
  
  return result.join('\n');
}

/**
 * 获取服务器状态
 */
async function getServerStatus() {
  return new Promise((resolve) => {
    const commands = {
      cpu: 'top -bn1 | grep "Cpu(s)" | awk \'{print $2 + $4}\'',
      memory: 'free -h | grep Mem | awk \'{print $3 "/" $2}\'',
      disk: 'df -h / | tail -1 | awk \'{print $3 "/" $2}\'',
      uptime: 'uptime -p'
    };
    
    const results = {};
    let completed = 0;
    
    Object.keys(commands).forEach(key => {
      exec(commands[key], (err, stdout, stderr) => {
        if (err) {
          results[key] = 'N/A';
        } else {
          results[key] = stdout.trim();
        }
        completed++;
        if (completed === Object.keys(commands).length) {
          resolve(results);
        }
      });
    });
  });
}

/**
 * 获取多智能体状态
 */
async function getAgentStatus() {
  return new Promise((resolve) => {
    exec('ls -1 ~/.openclaw/agents/ 2>/dev/null | head -10', (err, stdout, stderr) => {
      if (err || !stdout.trim()) {
        resolve({ agents: [], total: 0 });
        return;
      }
      
      const agents = stdout.trim().split('\n').filter(a => a.trim() && a !== 'main');
      resolve({ agents, total: agents.length });
    });
  });
}

/**
 * 执行优化
 */
async function optimizeMemory(workspacePath, dryRun = true, includeReflection = true, compressionRatio = 0.4) {
  // 加载 self-improving 偏好
  const preferences = await loadSelfImprovingPreferences();
  
  const scanResult = await scanMemoryFiles(workspacePath);
  const { files, totalTokens } = scanResult;
  
  if (files.length === 0) {
    return {
      success: true,
      freedTokens: 0,
      summarizedTokens: 0,
      filesProcessed: 0,
      message: '未找到 memory 文件',
      details: [],
      dryRun,
      compressionRatio
    };
  }
  
  let freedTokens = 0;
  let summarizedTokens = 0;
  const details = [];
  
  for (const file of files) {
    const originalTokens = file.tokens;
    
    // 读取文件内容
    const content = await fs.readFile(file.path, 'utf-8');
    
    // 根据 preferences 决定是否压缩
    if (file.lines > preferences.compressionThreshold) {
      const newContent = summarizeContent(content, preferences.maxSummaryLines, compressionRatio);
      const newTokens = estimateTokens(newContent);
      
      if (newTokens < originalTokens) {
        const saved = originalTokens - newTokens;
        summarizedTokens += newTokens;
        freedTokens += saved;
        
        if (!dryRun) {
          await fs.writeFile(file.path, newContent, 'utf-8');
        }
        
        details.push({
          file: file.name,
          originalTokens,
          newTokens,
          freed: saved,
          lines: file.lines,
          action: '压缩'
        });
      }
    }
  }
  
  const reflection = includeReflection && !dryRun ? 
    await logReflection({ stats: { freedTokens, summarizedTokens, filesProcessed: details.length } }, null) : null;
  
  return {
    success: true,
    freedTokens,
    summarizedTokens,
    filesProcessed: details.length,
    totalTokens,
    message: `已释放 ${freedTokens} tokens，总结了 ${summarizedTokens} tokens 记忆`,
    details,
    reflection,
    preferences,
    compressionRatio,
    dryRun
  };
}

/**
 * 执行每日优化并生成完整报告
 */
async function optimizeMemoryDaily() {
  const workspacePath = process.cwd();
  
  // 执行优化
  const optimizeResult = await optimizeMemory(workspacePath, false, true, 0.4);
  
  // 获取服务器状态
  const serverStatus = await getServerStatus();
  
  // 获取多智能体状态
  const agentStatus = await getAgentStatus();
  
  // 获取最近 24 小时的记忆文件
  const memoryDir = path.join(workspacePath, 'memory');
  let recentFiles = [];
  try {
    const entries = await fs.readdir(memoryDir);
    recentFiles = entries.filter(f => f.endsWith('.md')).slice(0, 7);
  } catch (e) {}
  
  const date = new Date().toISOString().split('T')[0];
  
  const report = {
    date,
    memory: {
      freedTokens: optimizeResult.freedTokens,
      summarizedTokens: optimizeResult.summarizedTokens,
      filesProcessed: optimizeResult.filesProcessed,
      totalTokens: optimizeResult.totalTokens,
      compressionRatio: optimizeResult.compressionRatio,
      files: recentFiles
    },
    server: serverStatus,
    agents: agentStatus,
    reflection: optimizeResult.reflection
  };
  
  return report;
}

module.exports = {
  mem_optimize: async (params = {}) => {
    const workspacePath = process.cwd();
    const dryRun = params.dryRun !== false; // 默认 dryRun
    
    const result = await optimizeMemory(workspacePath, dryRun);
    
    if (result.success) {
      return {
        status: 'success',
        message: result.message,
        stats: {
          freedTokens: result.freedTokens,
          summarizedTokens: result.summarizedTokens,
          filesProcessed: result.filesProcessed,
          totalTokens: result.totalTokens
        },
        details: result.details,
        dryRun: result.dryRun,
        note: result.dryRun ? '🔍 预览模式，未实际修改文件' : '✅ 已执行优化'
      };
    }
    
    return {
      status: 'error',
      message: result.message || '优化失败'
    };
  },
  
  mem_stats: async () => {
    const workspacePath = process.cwd();
    const { files, totalTokens } = await scanMemoryFiles(workspacePath);
    
    return {
      status: 'success',
      totalFiles: files.length,
      totalTokens,
      files: files.map(f => ({
        name: f.name,
        tokens: f.tokens,
        lines: f.lines
      }))
    };
  }
};
