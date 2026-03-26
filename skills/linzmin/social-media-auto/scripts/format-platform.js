#!/usr/bin/env node
/**
 * 多平台格式适配
 * 用法：./format-platform.js [草稿文件] [选项]
 */

const fs = require('fs');
const path = require('path');

const DRAFTS_DIR = path.join(__dirname, '..', 'drafts');
const TEMPLATES_DIR = path.join(__dirname, '..', 'templates');

function printUsage() {
  console.log(`
📱 多平台格式适配

用法：
  ./format-platform.js [草稿文件] [选项]

选项：
  --all             转换所有草稿
  --platform <平台>  目标平台：wechat/xiaohongshu/douyin
  --input <文件>     输入文件
  --output <目录>    输出目录
  --help            显示帮助

示例：
  ./format-platform.js --all
  ./format-platform.js --input drafts/2026-03-26_AI_Agent_wechat.md --platform xiaohongshu
`);
}

function loadTemplate(platform) {
  const templateFile = path.join(TEMPLATES_DIR, `${platform}.md`);
  
  if (!fs.existsSync(templateFile)) {
    return getDefaultTemplate(platform);
  }
  
  return fs.readFileSync(templateFile, 'utf8');
}

function getDefaultTemplate(platform) {
  const templates = {
    wechat: {
      titlePrefix: '',
      titleSuffix: '',
      contentFormat: 'markdown',
      addTags: false,
      addCTA: true,
      ctaText: '**关注公众号，获取更多干货！**'
    },
    xiaohongshu: {
      titlePrefix: '🔥',
      titleSuffix: '| 干货分享',
      contentFormat: 'emoji',
      addTags: true,
      addCTA: true,
      ctaText: '💬 欢迎评论区交流～\n👍 点赞 + 收藏不迷路！'
    },
    douyin: {
      titlePrefix: '【视频脚本】',
      titleSuffix: '',
      contentFormat: 'script',
      addTags: false,
      addCTA: true,
      ctaText: '关注我，了解更多干货！'
    }
  };
  
  return templates[platform] || templates.wechat;
}

function convertToPlatform(content, platform) {
  const template = getDefaultTemplate(platform);
  
  let title = content.title || '';
  let body = content.body || '';
  
  // 添加标题前缀后缀
  title = `${template.titlePrefix}${title}${template.titleSuffix}`;
  
  // 转换内容格式
  if (template.contentFormat === 'emoji') {
    body = addEmojis(body);
  } else if (template.contentFormat === 'script') {
    body = convertToScript(body);
  }
  
  // 添加标签
  if (template.addTags && content.tags) {
    body += `\n\n#${content.tags.replace(/\s+/g, ' #')}`;
  }
  
  // 添加 CTA
  if (template.addCTA) {
    body += `\n\n${template.ctaText}`;
  }
  
  return {
    title,
    body,
    platform
  };
}

function addEmojis(text) {
  // 简单 emoji 添加规则
  const emojiMap = {
    '重要': '⚠️',
    '注意': '⚠️',
    '首先': '1️⃣',
    '其次': '2️⃣',
    '最后': '3️⃣',
    '总结': '📝',
    '案例': '📊',
    '分析': '🔍',
    '建议': '💡',
    '方法': '🛠️',
    '技巧': '✨',
    '推荐': '👍',
    '关注': '👀',
    '收藏': '⭐',
    '点赞': '❤️'
  };
  
  let result = text;
  Object.keys(emojiMap).forEach(key => {
    result = result.replace(new RegExp(key, 'g'), `${emojiMap[key]} ${key}`);
  });
  
  return result;
}

function convertToScript(text) {
  // 转换为视频脚本格式
  const sections = text.split(/\n##\s+/);
  
  let script = '';
  sections.forEach((section, i) => {
    if (i === 0) {
      script += `【开场】\n${section.trim()}\n\n`;
    } else {
      const lines = section.split('\n');
      const title = lines[0].trim();
      const content = lines.slice(1).join('\n').trim();
      script += `【${title}】\n${content}\n\n`;
    }
  });
  
  return script;
}

function parseDraft(filepath) {
  const content = fs.readFileSync(filepath, 'utf8');
  
  // 简单解析 Markdown
  const titleMatch = content.match(/^#\s+(.+)/m);
  const title = titleMatch ? titleMatch[1].trim() : '无标题';
  
  const body = content.replace(/^#\s+.+\n+/m, '').trim();
  
  // 提取标签
  const tagsMatch = content.match(/#(\w+)/g);
  const tags = tagsMatch ? tagsMatch.join(' ').replace(/#/g, '') : '';
  
  return { title, body, tags };
}

function formatAll() {
  console.log('🔄 开始批量转换草稿...\n');
  
  if (!fs.existsSync(DRAFTS_DIR)) {
    console.log('❌ 草稿目录不存在');
    return;
  }
  
  const files = fs.readdirSync(DRAFTS_DIR).filter(f => f.endsWith('.md'));
  
  if (files.length === 0) {
    console.log('ℹ️  草稿目录为空');
    return;
  }
  
  console.log(`📁 找到 ${files.length} 个草稿文件\n`);
  
  files.forEach(file => {
    const filepath = path.join(DRAFTS_DIR, file);
    const content = parseDraft(filepath);
    
    console.log(`📝 处理：${file}`);
    
    // 转换为其他平台
    const platforms = ['wechat', 'xiaohongshu', 'douyin'];
    platforms.forEach(platform => {
      const formatted = convertToPlatform(content, platform);
      const outputDir = path.join(DRAFTS_DIR, 'formatted');
      
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      
      const outputFile = path.join(outputDir, `${file.replace('.md', '')}_${platform}.md`);
      fs.writeFileSync(outputFile, `# ${formatted.title}\n\n${formatted.body}`);
      
      console.log(`   ✅ ${platform}: ${path.basename(outputFile)}`);
    });
    
    console.log('');
  });
  
  console.log('✅ 批量转换完成！\n');
}

function formatSingle(inputFile, platform) {
  console.log(`🔄 开始转换：${inputFile}\n`);
  
  if (!fs.existsSync(inputFile)) {
    console.log(`❌ 文件不存在：${inputFile}`);
    return;
  }
  
  const content = parseDraft(inputFile);
  const formatted = convertToPlatform(content, platform);
  
  const outputDir = path.join(DRAFTS_DIR, 'formatted');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  const inputFileBase = path.basename(inputFile, '.md');
  const outputFile = path.join(outputDir, `${inputFileBase}_${platform}.md`);
  
  fs.writeFileSync(outputFile, `# ${formatted.title}\n\n${formatted.body}`);
  
  console.log(`✅ 转换完成：${outputFile}\n`);
  console.log(`📱 平台：${platform}`);
  console.log(`📝 标题：${formatted.title}`);
  console.log(`📏 字数：${formatted.body.length}`);
  console.log('');
}

// 主程序
function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('-h') || args.includes('--help')) {
    printUsage();
    process.exit(0);
  }
  
  if (args.includes('--all')) {
    formatAll();
    return;
  }
  
  const inputIndex = args.indexOf('--input');
  const platformIndex = args.indexOf('--platform');
  
  if (inputIndex === -1) {
    console.error('❌ 缺少必需参数 --input 或使用 --all');
    printUsage();
    process.exit(1);
  }
  
  const inputFile = args[inputIndex + 1];
  const platform = platformIndex !== -1 ? args[platformIndex + 1] : 'wechat';
  
  formatSingle(inputFile, platform);
}

main();
