#!/usr/bin/env node
/**
 * 保存草稿
 * 用法：./save-draft.js [内容] [选项]
 */

const fs = require('fs');
const path = require('path');

const DRAFTS_DIR = path.join(__dirname, '..', 'drafts');

function printUsage() {
  console.log(`
💾 保存草稿

用法：
  ./save-draft.js [内容] [选项]

选项：
  --title <标题>     文章标题
  --platform <平台>  目标平台：wechat/xiaohongshu/douyin/all
  --tags <标签>      文章标签
  --list             列出所有草稿
  --view <文件>      查看草稿内容
  --help             显示帮助

示例：
  ./save-draft.js --title "AI Agent" --platform all
  ./save-draft.js --list
  ./save-draft.js --view 2026-03-26_AI_Agent.md
`);
}

function saveDraft(title, content, platform = 'all', tags = '') {
  if (!fs.existsSync(DRAFTS_DIR)) {
    fs.mkdirSync(DRAFTS_DIR, { recursive: true });
  }
  
  const date = new Date().toISOString().split('T')[0];
  const time = new Date().toISOString().split('T')[1].split(':')[0];
  const safeTitle = title.replace(/\s+/g, '_').replace(/[^\w\u4e00-\u9fa5]/g, '');
  
  if (platform === 'all') {
    const platforms = ['wechat', 'xiaohongshu', 'douyin'];
    const files = [];
    
    platforms.forEach(p => {
      const filename = `${date}_${time}_${safeTitle}_${p}.md`;
      const filepath = path.join(DRAFTS_DIR, filename);
      
      const fullContent = formatForPlatform(content, p, title, tags);
      fs.writeFileSync(filepath, fullContent);
      files.push(filename);
    });
    
    return files;
  } else {
    const filename = `${date}_${time}_${safeTitle}_${platform}.md`;
    const filepath = path.join(DRAFTS_DIR, filename);
    
    const fullContent = formatForPlatform(content, platform, title, tags);
    fs.writeFileSync(filepath, fullContent);
    
    return [filename];
  }
}

function formatForPlatform(content, platform, title, tags) {
  let formatted = `# ${title}\n\n`;
  
  if (platform === 'wechat') {
    formatted += `> 深度解析，干货满满\n\n---\n\n`;
    formatted += content;
    formatted += `\n\n---\n**关注公众号，获取更多干货！**\n`;
  } else if (platform === 'xiaohongshu') {
    formatted += `🔥 ${title} | 干货分享\n\n`;
    formatted += addEmojis(content);
    formatted += `\n\n---\n#${tags.replace(/\s+/g, ' #')}\n\n💬 欢迎评论区交流～\n👍 点赞 + 收藏不迷路！`;
  } else if (platform === 'douyin') {
    formatted += `【视频脚本】${title}\n\n`;
    formatted += `【开场】你知道吗？${title}\n\n【正文】\n`;
    formatted += content;
    formatted += `\n\n【结尾】关注我，了解更多干货！\n`;
  }
  
  return formatted;
}

function addEmojis(text) {
  const emojiMap = {
    '重要': '⚠️',
    '注意': '⚠️',
    '首先': '1️⃣',
    '其次': '2️⃣',
    '最后': '3️⃣',
    '总结': '📝',
    '建议': '💡',
    '技巧': '✨',
    '推荐': '👍'
  };
  
  let result = text;
  Object.keys(emojiMap).forEach(key => {
    result = result.replace(new RegExp(key, 'g'), `${emojiMap[key]} ${key}`);
  });
  
  return result;
}

function listDrafts() {
  if (!fs.existsSync(DRAFTS_DIR)) {
    console.log('📁 草稿目录不存在');
    return;
  }
  
  const files = fs.readdirSync(DRAFTS_DIR)
    .filter(f => f.endsWith('.md'))
    .sort()
    .reverse();
  
  if (files.length === 0) {
    console.log('📁 草稿目录为空');
    return;
  }
  
  console.log(`\n📁 草稿列表（共${files.length}个）\n`);
  console.log('='.repeat(60));
  
  files.slice(0, 20).forEach((file, i) => {
    const filepath = path.join(DRAFTS_DIR, file);
    const stats = fs.statSync(filepath);
    const size = (stats.size / 1024).toFixed(1);
    const date = stats.mtime.toLocaleString('zh-CN');
    
    const platform = file.includes('wechat') ? '💬' : file.includes('xiaohongshu') ? '📕' : '🎵';
    
    console.log(`${i + 1}. ${platform} ${file}`);
    console.log(`   📏 ${size}KB | 🕐 ${date}`);
    console.log('');
  });
  
  if (files.length > 20) {
    console.log(`... 还有 ${files.length - 20} 个草稿`);
  }
  
  console.log('='.repeat(60));
  console.log('\n💡 提示:');
  console.log('  查看：./save-draft.js --view <文件名>');
  console.log('  转换：./format-platform.js --input drafts/<文件名>');
  console.log('');
}

function viewDraft(filename) {
  const filepath = path.join(DRAFTS_DIR, filename);
  
  if (!fs.existsSync(filepath)) {
    console.log(`❌ 文件不存在：${filename}`);
    return;
  }
  
  const content = fs.readFileSync(filepath, 'utf8');
  
  console.log('\n📄 草稿内容\n');
  console.log('='.repeat(60));
  console.log(content);
  console.log('='.repeat(60));
  console.log('');
}

// 主程序
function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('-h') || args.includes('--help')) {
    printUsage();
    process.exit(0);
  }
  
  if (args.includes('--list')) {
    listDrafts();
    return;
  }
  
  const viewIndex = args.indexOf('--view');
  if (viewIndex !== -1) {
    viewDraft(args[viewIndex + 1]);
    return;
  }
  
  const titleIndex = args.indexOf('--title');
  if (titleIndex === -1) {
    console.error('❌ 缺少必需参数 --title 或使用 --list/--view');
    printUsage();
    process.exit(1);
  }
  
  const title = args[titleIndex + 1];
  const platform = args.includes('--platform') ? args[args.indexOf('--platform') + 1] : 'all';
  const tags = args.includes('--tags') ? args[args.indexOf('--tags') + 1] : '';
  
  // 示例内容
  const content = `这是关于"${title}"的内容...\n\n（此处为草稿内容）`;
  
  const files = saveDraft(title, content, platform, tags);
  
  console.log(`\n✅ 已保存 ${files.length} 个草稿：\n`);
  files.forEach(f => console.log(`   📄 ${f}`));
  console.log('');
  console.log('💡 提示:');
  console.log('  查看：./save-draft.js --list');
  console.log('  转换：./format-platform.js --all');
  console.log('');
}

main();
