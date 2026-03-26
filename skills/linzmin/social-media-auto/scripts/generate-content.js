#!/usr/bin/env node
/**
 * AI 生成内容
 * 用法：./generate-content.js --topic "话题名" [选项]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const DATA_FILE = path.join(__dirname, '..', 'data', 'trending.json');
const DRAFTS_DIR = path.join(__dirname, '..', 'drafts');
const TEMPLATES_DIR = path.join(__dirname, '..', 'templates');

function printUsage() {
  console.log(`
📝 AI 生成内容

用法：
  ./generate-content.js --topic "话题名" [选项]

选项：
  --topic <话题>     话题名称（必填）
  --platform <平台>  目标平台：wechat/xiaohongshu/douyin/all（默认 all）
  --length <长度>    文章长度：short/medium/long（默认 medium）
  --tone <语气>      文章语气：professional/casual/humorous（默认 professional）
  --preview          预览生成结果
  --save             保存到草稿
  --help             显示帮助

示例：
  ./generate-content.js --topic "AI Agent" --platform all
  ./generate-content.js --topic "时间管理" --platform wechat --length long
`);
}

function loadTrending() {
  if (!fs.existsSync(DATA_FILE)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
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
    wechat: `# {{title}}

> {{subtitle}}

---

## 引言

{{intro}}

## 正文

{{content}}

## 总结

{{conclusion}}

---
**关注公众号，获取更多干货！**

---
字数：{{wordCount}} | 阅读时间：{{readTime}}分钟
`,
    
    xiaohongshu: `{{title}}

{{content}}

---
#{{tags}}

💬 欢迎评论区交流～
👍 点赞 + 收藏不迷路！
`,
    
    douyin: `【视频脚本】{{title}}

【开场】{{hook}}

【正文】
{{content}}

【结尾】{{callToAction}}

---
时长：{{duration}}秒 | 字数：{{wordCount}}
`
  };
  
  return templates[platform] || templates.wechat;
}

function generateContent(topic, platform = 'all', length = 'medium', tone = 'professional') {
  console.log(`🚀 开始生成内容...\n`);
  console.log(`📌 话题：${topic}`);
  console.log(`📱 平台：${platform}`);
  console.log(`📏 长度：${length}`);
  console.log(`🎨 语气：${tone}\n`);
  
  // 使用 AI 生成内容（调用阿里云 MCP）
  const prompt = `请为"${topic}"这个话题生成一篇${length}篇文章，语气${tone}。

要求：
1. 标题吸引人
2. 内容有深度
3. 结构清晰
4. 适合${platform === 'wechat' ? '微信公众号' : platform === 'xiaohongshu' ? '小红书' : '抖音'}平台

请生成完整内容。`;

  try {
    console.log('🤖 AI 正在创作...\n');
    
    const result = execSync(
      `npx mcporter call WebSearch.bailian_web_search query="${prompt}" count=1`,
      { encoding: 'utf8' }
    );
    
    const data = JSON.parse(result);
    
    // 解析 AI 生成的内容
    const content = parseAIResponse(data, topic, platform, length, tone);
    
    return content;
    
  } catch (error) {
    console.log('⚠️  AI 生成失败，使用模板生成示例内容\n');
    return generateExampleContent(topic, platform, length, tone);
  }
}

function parseAIResponse(data, topic, platform, length, tone) {
  // 简化处理，实际应该解析 AI 返回的内容
  return generateExampleContent(topic, platform, length, tone);
}

function generateExampleContent(topic, platform, length, tone) {
  const wordCounts = { short: 300, medium: 800, long: 1500 };
  const readTime = Math.ceil(wordCounts[length] / 500);
  
  const content = {
    title: `深度解析${topic}：2026 年你不能不知道的趋势`,
    subtitle: `一文读懂${topic}的核心要点`,
    intro: `最近，${topic}成为了热门话题。无论是社交媒体还是专业论坛，到处都能看到相关的讨论。那么，${topic}到底是什么？它为什么会如此火爆？本文将为你深度解析。`,
    
    content: `## 背景介绍

${topic}的兴起并非偶然。随着技术的发展和用户需求的变化，${topic}应运而生，并迅速成为了行业焦点。

## 核心要点

### 1. 什么是${topic}？

${topic}是指...（此处省略 500 字）

### 2. 为什么重要？

${topic}的重要性体现在以下几个方面：

- 第一，...
- 第二，...
- 第三，...

### 3. 如何应用？

在实际应用中，我们可以：

1. 首先，...
2. 其次，...
3. 最后，...

## 案例分析

让我们来看一个具体的例子...

## 未来展望

展望未来，${topic}将会...`,
    
    conclusion: `总的来说，${topic}是一个值得关注的趋势。无论你是从业者还是普通用户，都应该了解相关知识，把握时代脉搏。`,
    
    tags: `${topic.replace(/\s/g, '')} 行业趋势 深度解析 2026`,
    
    wordCount: wordCounts[length],
    readTime: readTime
  };
  
  return content;
}

function formatContent(content, platform) {
  console.log(`📱 格式化${platform}版本...\n`);
  
  const template = loadTemplate(platform);
  
  let formatted = template
    .replace(/{{title}}/g, content.title)
    .replace(/{{subtitle}}/g, content.subtitle || '')
    .replace(/{{intro}}/g, content.intro)
    .replace(/{{content}}/g, content.content)
    .replace(/{{conclusion}}/g, content.conclusion)
    .replace(/{{tags}}/g, content.tags)
    .replace(/{{wordCount}}/g, content.wordCount)
    .replace(/{{readTime}}/g, content.readTime)
    .replace(/{{hook}}/g, `你知道吗？${content.title}`)
    .replace(/{{callToAction}}/g, '关注我，了解更多干货！')
    .replace(/{{duration}}/g, '60');
  
  return formatted;
}

function saveDraft(platform, content, topic) {
  if (!fs.existsSync(DRAFTS_DIR)) {
    fs.mkdirSync(DRAFTS_DIR, { recursive: true });
  }
  
  const date = new Date().toISOString().split('T')[0];
  const time = new Date().toISOString().split('T')[1].split(':')[0];
  const filename = `${date}_${time}_${topic.replace(/\s+/g, '_')}_${platform}.md`;
  const filepath = path.join(DRAFTS_DIR, filename);
  
  fs.writeFileSync(filepath, content);
  
  console.log(`✅ 草稿已保存：${filepath}`);
  return filepath;
}

function displayPreview(contents) {
  console.log('\n📊 生成内容预览\n');
  console.log('='.repeat(60));
  
  Object.keys(contents).forEach(platform => {
    console.log(`\n📱 ${platform.toUpperCase()} 版本：\n`);
    console.log(contents[platform].substring(0, 500));
    if (contents[platform].length > 500) {
      console.log('...（内容过长，已截断）');
    }
    console.log('');
  });
  
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
  
  const topicIndex = args.indexOf('--topic');
  if (topicIndex === -1) {
    console.error('❌ 缺少必需参数 --topic');
    printUsage();
    process.exit(1);
  }
  
  const topic = args[topicIndex + 1];
  const platform = args.includes('--platform') ? args[args.indexOf('--platform') + 1] : 'all';
  const length = args.includes('--length') ? args[args.indexOf('--length') + 1] : 'medium';
  const tone = args.includes('--tone') ? args[args.indexOf('--tone') + 1] : 'professional';
  const shouldPreview = args.includes('--preview') || (!args.includes('--save') && !args.includes('--platform'));
  const shouldSave = args.includes('--save');
  
  // 生成内容
  const content = generateContent(topic, platform, length, tone);
  
  // 格式化
  const platforms = platform === 'all' ? ['wechat', 'xiaohongshu', 'douyin'] : [platform];
  const formattedContents = {};
  
  platforms.forEach(p => {
    formattedContents[p] = formatContent(content, p);
  });
  
  // 预览
  if (shouldPreview) {
    displayPreview(formattedContents);
  }
  
  // 保存
  if (shouldSave) {
    platforms.forEach(p => {
      saveDraft(p, formattedContents[p], topic);
    });
  }
  
  console.log('💡 提示:');
  console.log('  保存草稿：./generate-content.js --topic "话题" --save');
  console.log('  查看草稿：ls drafts/');
  console.log('  多平台：./generate-content.js --topic "话题" --platform all --save');
  console.log('');
}

main();
