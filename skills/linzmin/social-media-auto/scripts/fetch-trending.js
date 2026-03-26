#!/usr/bin/env node
/**
 * 抓取热搜话题
 * 用法：./fetch-trending.js [选项]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const DATA_DIR = path.join(__dirname, '..', 'data');
const DATA_FILE = path.join(DATA_DIR, 'trending.json');

function printUsage() {
  console.log(`
🔥 抓取热搜话题

用法：
  ./fetch-trending.js [选项]

选项：
  --weibo     只抓取微博热搜
  --zhihu     只抓取知乎热榜
  --all       抓取所有平台（默认）
  --output    显示结果
  --help      显示帮助
`);
}

function fetchWeibo() {
  console.log('🔍 抓取微博热搜...');
  
  try {
    // 使用阿里云搜索 MCP 获取微博热搜
    const result = execSync(
      `npx mcporter call WebSearch.bailian_web_search query="微博热搜榜 2026 年 3 月 26 日" count=15`,
      { encoding: 'utf8' }
    );
    
    const data = JSON.parse(result);
    
    if (data.pages && data.pages.length > 0) {
      const topics = data.pages.slice(0, 15).map((page, i) => ({
        rank: i + 1,
        topic: page.title.replace(/微博热搜.*?-/, '').trim(),
        hot: page.snippet.substring(0, 100),
        url: page.url,
        source: 'weibo'
      }));
      
      console.log(`✅ 获取到 ${topics.length} 个微博热搜\n`);
      return topics;
    }
  } catch (error) {
    console.log('⚠️  微博热搜获取失败，使用示例数据');
  }
  
  // 示例数据
  return [
    { rank: 1, topic: 'AI Agent 爆发', hot: '2026 年成为 Agent 元年，各大厂纷纷布局', source: 'weibo' },
    { rank: 2, topic: 'OpenClaw 技能开发', hot: '一天发布 4 个技能，生产力爆炸', source: 'weibo' },
    { rank: 3, topic: '金价波动', hot: '国际金价跌破 1000 元/克', source: 'weibo' },
    { rank: 4, topic: '伊朗美国谈判', hot: '中东局势持续紧张', source: 'weibo' },
    { rank: 5, topic: '科技创新大会', hot: '2026 科技创新大会召开', source: 'weibo' }
  ];
}

function fetchZhihu() {
  console.log('🔍 抓取知乎热榜...');
  
  try {
    const result = execSync(
      `npx mcporter call WebSearch.bailian_web_search query="知乎热榜 2026 年 3 月 26 日" count=15`,
      { encoding: 'utf8' }
    );
    
    const data = JSON.parse(result);
    
    if (data.pages && data.pages.length > 0) {
      const topics = data.pages.slice(0, 15).map((page, i) => ({
        rank: i + 1,
        topic: page.title.replace(/知乎.*?-/, '').trim(),
        hot: page.snippet.substring(0, 100),
        url: page.url,
        source: 'zhihu'
      }));
      
      console.log(`✅ 获取到 ${topics.length} 个知乎热榜\n`);
      return topics;
    }
  } catch (error) {
    console.log('⚠️  知乎热榜获取失败，使用示例数据');
  }
  
  // 示例数据
  return [
    { rank: 1, topic: '如何评价 OpenClaw？', hot: 'OpenClaw 是什么？好用吗？', source: 'zhihu' },
    { rank: 2, topic: 'AI 技能开发前景', hot: '2026 年 AI 技能开发有前途吗？', source: 'zhihu' },
    { rank: 3, topic: '自媒体运营技巧', hot: '如何做好微信公众号和小红书？', source: 'zhihu' },
    { rank: 4, topic: '时间管理方法', hot: '有哪些高效的时间管理技巧？', source: 'zhihu' },
    { rank: 5, topic: '副业推荐', hot: '2026 年有什么好的副业推荐？', source: 'zhihu' }
  ];
}

function saveData(data) {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
  
  data.fetchedAt = new Date().toISOString();
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

function displayResults(data) {
  console.log('\n🔥 热搜话题汇总\n');
  console.log('='.repeat(60));
  
  if (data.weibo && data.weibo.length > 0) {
    console.log('\n📱 微博热搜 TOP 5：\n');
    data.weibo.slice(0, 5).forEach(item => {
      console.log(`   ${item.rank}. 🔥 ${item.topic}`);
      console.log(`      ${item.hot.substring(0, 50)}...`);
    });
  }
  
  if (data.zhihu && data.zhihu.length > 0) {
    console.log('\n📖 知乎热榜 TOP 5：\n');
    data.zhihu.slice(0, 5).forEach(item => {
      console.log(`   ${item.rank}. 💡 ${item.topic}`);
      console.log(`      ${item.hot.substring(0, 50)}...`);
    });
  }
  
  console.log('\n' + '='.repeat(60));
  console.log(`\n💡 提示：运行 ./scripts/generate-content.js --topic "话题名" 生成内容`);
  console.log('');
}

function fetchAll() {
  console.log('🚀 开始抓取热搜话题...\n');
  
  const data = {
    weibo: fetchWeibo(),
    zhihu: fetchZhihu()
  };
  
  saveData(data);
  
  console.log(`✅ 数据已保存：${DATA_FILE}\n`);
  
  displayResults(data);
  
  return data;
}

// 主程序
function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('-h') || args.includes('--help')) {
    printUsage();
    process.exit(0);
  }
  
  if (args.includes('--output')) {
    if (fs.existsSync(DATA_FILE)) {
      const data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
      displayResults(data);
    } else {
      console.log('❌ 未找到数据文件，请先运行 ./fetch-trending.js');
    }
    process.exit(0);
  }
  
  const weiboOnly = args.includes('--weibo');
  const zhihuOnly = args.includes('--zhihu');
  
  if (weiboOnly) {
    const weibo = fetchWeibo();
    saveData({ weibo });
    console.log('✅ 微博热搜已保存');
  } else if (zhihuOnly) {
    const zhihu = fetchZhihu();
    saveData({ zhihu });
    console.log('✅ 知乎热榜已保存');
  } else {
    // 默认抓取所有
    fetchAll();
  }
}

main();
