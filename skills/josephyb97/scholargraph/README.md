# 📚 ScholarGraph - 学术文献智能工具包

<div align="center">

**高效、系统化的学术文献分析与知识管理工具**

[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![Bun](https://img.shields.io/badge/Bun-1.3+-orange.svg)](https://bun.sh/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](#) | [中文文档](#)

</div>

---

## 🎯 项目目标

本工具包解决学术研究和知识获取中的核心挑战：

| 问题 | 解决方案 |
|------|----------|
| 📚 信息过载 | AI 驱动的多源智能过滤 |
| 🧩 知识碎片化 | 自动化知识图谱构建 |
| 🔄 进展难追踪 | 实时监控与智能报告 |
| 🙈 知识盲区不可见 | 主动式盲区检测 |
| 🆕 概念学习复杂 | 一键生成学习卡片 |
| 📄 论文分析耗时 | 深度智能分析与对比 |

---

## ✨ 核心功能

### 基础功能

#### 1. 🔍 文献检索 (Literature Search)

跨 arXiv、Semantic Scholar 和 Web 的多源学术论文检索。

```bash
# CLI 使用
lit search "transformer attention" --limit 20 --source arxiv --sort citations

# 编程 API
import LiteratureSearch from './literature-search/scripts/search';

const searcher = new LiteratureSearch();
const results = await searcher.search("large language models", {
  sources: ['arxiv', 'semantic_scholar'],
  limit: 10,
  sortBy: 'citations'
});
```

#### 2. 📖 概念学习 (Concept Learner)

快速构建知识框架，生成结构化学习卡片。

```bash
# CLI 使用
lit learn "BERT" --depth advanced --papers --code --output bert-card.md

# 编程 API
import ConceptLearner from './concept-learner/scripts/learn';

const learner = new ConceptLearner();
const card = await learner.learn("Transformer", {
  depth: 'advanced',
  includePapers: true,
  includeCode: true
});
```

**输出内容**：
- 📖 定义与核心概念
- 🔧 核心组成部分
- 📜 历史演进时间线
- 🎯 应用场景与案例
- 🔗 相关概念关系图
- 📚 学习路径规划
- 💻 代码示例（可选）
- 📄 相关论文（可选）

#### 3. 🔎 知识盲区检测 (Knowledge Gap Detector)

主动识别知识体系中的盲点和薄弱环节。

```bash
# CLI 使用
lit detect --domain "Deep Learning" --known "CNN,RNN" --output dl-gaps.md

# 编程 API
import KnowledgeGapDetector from './knowledge-gap-detector/scripts/detect';

const detector = new KnowledgeGapDetector();
const report = await detector.detect({
  domain: 'Machine Learning',
  knownConcepts: ['Python', 'NumPy', 'Pandas'],
  targetLevel: 'advanced'
});
```

**输出内容**：
- 🚨 关键缺口（必须掌握）
- 📚 建议学习（推荐掌握）
- 🔗 跨学科机会
- 📈 新兴主题
- 🎯 建议学习顺序
- ⏱️ 预计学习工作量

#### 4. 📊 进展追踪 (Progress Tracker)

实时监控研究领域动态，自动生成进展报告。

```bash
# CLI 使用
lit track report --type weekly --topic "large language model" --output weekly-report.md

# 编程 API
import ProgressTracker from './progress-tracker/scripts/track';

const tracker = new ProgressTracker();
await tracker.addWatch({
  type: 'keyword',
  value: 'large language model',
  frequency: 'daily'
});
const report = await tracker.generateReport({ type: 'weekly' });
```

#### 5. 📄 论文分析 (Paper Analyzer)

深度论文分析，提取关键贡献和洞察。

```bash
# CLI 使用
lit analyze "https://arxiv.org/abs/1706.03762" --mode deep --output analysis.md

# 编程 API
import PaperAnalyzer from './paper-analyzer/scripts/analyze';

const analyzer = new PaperAnalyzer();
const analysis = await analyzer.analyze({
  url: 'https://arxiv.org/abs/1706.03762',
  mode: 'deep'
});
```

**分析模式**：
- `quick`: 快速分析（摘要、关键点）
- `standard`: 标准分析（方法、实验、贡献）
- `deep`: 深度分析（完整分析、局限性、未来工作）

#### 6. 🔗 知识图谱 (Knowledge Graph Builder)

可视化概念关系，构建交互式知识图谱。

```bash
# CLI 使用
lit graph transformer attention BERT GPT --format mermaid --output graph.md

# 编程 API
import KnowledgeGraphBuilder from './knowledge-graph/scripts/graph';

const builder = new KnowledgeGraphBuilder();
const graph = await builder.build(['transformer', 'attention', 'BERT']);
console.log(builder.toMermaid(graph));
```

**输出格式**：
- `mermaid`: Mermaid 图表格式
- `json`: JSON 数据格式

---

### 高级功能

#### 7. 🔄 概念对比 (Compare Concepts)

对比两个概念的相似点、差异点和使用场景。

```bash
# CLI 使用
lit compare concepts CNN RNN --output cnn-vs-rnn.md

# 编程 API
const comparison = await learner.compare('CNN', 'RNN');
```

**输出内容**：
- 📊 相似点
- 🔀 差异点
- 🎯 使用场景（何时优先使用哪个）

#### 8. 📑 论文对比 (Compare Papers)

对比多篇论文的共同主题、主要差异和综合分析。

```bash
# CLI 使用 - 对比两篇论文
lit compare papers \
  "https://arxiv.org/abs/1706.03762" \
  "https://arxiv.org/abs/1810.04805" \
  --output transformer-vs-bert.md

# 对比三篇或更多论文
lit compare papers \
  "https://arxiv.org/abs/1706.03762" \
  "https://arxiv.org/abs/1810.04805" \
  "https://arxiv.org/abs/2005.14165" \
  --output three-papers.md

# 编程 API
const comparison = await analyzer.compare([url1, url2, url3]);
```

**输出内容**：
- 📚 对比论文列表
- 🔗 共同主题
- 🔀 主要差异
- 💡 综合分析

#### 9. 🔍 批判性分析 (Critique)

对论文进行批判性分析，识别优点、缺点、研究空白和改进建议。

```bash
# CLI 使用
lit critique "https://arxiv.org/abs/1706.03762" \
  --focus "novelty,scalability,efficiency" \
  --output critique.md

# 编程 API
const critique = await analyzer.critique({
  url: 'https://arxiv.org/abs/1706.03762',
  focusAreas: ['novelty', 'scalability']
});
```

**输出内容**：
- 📄 论文信息
- 🎯 关注领域（可选）
- ✅ 优点
- ⚠️ 缺点
- 🔍 研究空白
- 💡 改进建议
- 📊 总体评价

#### 10. 🗺️ 学习路径 (Learning Path)

查找从一个概念到另一个概念的最优学习路径。

```bash
# CLI 使用
lit path "Machine Learning" "Deep Learning" \
  --concepts "Neural Networks,Backpropagation" \
  --output ml-to-dl-path.md

# 编程 API
const graph = await builder.build(concepts);
const path = builder.findPath(graph, 'Machine Learning', 'Deep Learning');
const order = builder.getTopologicalOrder(graph);
```

**输出内容**：
- 🗺️ 推荐学习路径
- 📊 Mermaid 可视化
- 📚 学习建议

---

## 📦 安装

### 前置要求

- [Bun](https://bun.sh/) 1.3 或更高版本
- Node.js 18+ (可选，如果不使用 Bun)

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/your-username/ScholarGraph.git
cd ScholarGraph

# 安装依赖
bun install

# 初始化配置
bun run cli.ts config init
```

---

## 🚀 快速开始

### 配置 AI 提供商

本工具支持 15+ AI 提供商，需要配置相应的 API 密钥：

```bash
# 使用 OpenAI
export AI_PROVIDER=openai
export OPENAI_API_KEY="your-api-key"

# 使用 DeepSeek
export AI_PROVIDER=deepseek
export DEEPSEEK_API_KEY="your-api-key"

# 使用 OpenRouter
export AI_PROVIDER=openai
export OPENAI_API_KEY="your-openrouter-key"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_MODEL="deepseek/deepseek-chat"

# 使用智谱 AI
export AI_PROVIDER=zhipu
export ZHIPU_API_KEY="your-api-key"
```

**支持的 AI 提供商**：
- 🌍 国际: OpenAI, Anthropic, Azure OpenAI, Groq, Together AI, Ollama
- 🇨🇳 国内: 通义千问 (Qwen), DeepSeek, 智谱 AI (GLM), MiniMax, Moonshot (Kimi), 百川 AI, 零一万物 (Yi), 豆包 (Doubao)

### 基础使用示例

```bash
# 1. 检索文献
lit search "transformer attention" --limit 20

# 2. 学习概念
lit learn "Transformer" --depth advanced --output transformer.md

# 3. 检测知识盲区
lit detect --domain "Deep Learning" --known "CNN,RNN"

# 4. 分析论文
lit analyze "https://arxiv.org/abs/1706.03762" --output analysis.md

# 5. 构建知识图谱
lit graph transformer attention BERT GPT --format mermaid

# 6. 对比概念
lit compare concepts CNN RNN

# 7. 对比论文
lit compare papers "https://arxiv.org/abs/1706.03762" "https://arxiv.org/abs/1810.04805"

# 8. 批判性分析
lit critique "https://arxiv.org/abs/1706.03762" --focus "novelty,scalability"

# 9. 查找学习路径
lit path "Machine Learning" "Deep Learning" --concepts "Neural Networks"
```

---

## 💡 使用场景

### 场景 1: 快速入门新领域

```bash
# 1. 学习核心概念
lit learn "Large Language Model" --depth beginner --code --output llm-basics.md

# 2. 检测前置知识盲区
lit detect --domain "LLM" --known "transformer,attention" --output llm-gaps.md

# 3. 构建知识图谱
lit graph LLM transformer attention GPT BERT --format mermaid --output llm-graph.md

# 4. 规划学习路径
lit path "Transformer" "Large Language Model" --concepts "attention,BERT,GPT"
```

### 场景 2: 深度理解论文

```bash
# 1. 分析论文
lit analyze "https://arxiv.org/abs/1706.03762" --mode deep --output transformer-paper.md

# 2. 批判性分析
lit critique "https://arxiv.org/abs/1706.03762" --focus "novelty,limitations" --output critique.md

# 3. 学习论文中的新概念
lit learn "Self-Attention" --depth advanced --papers --output self-attention.md

# 4. 对比相关论文
lit compare papers \
  "https://arxiv.org/abs/1706.03762" \
  "https://arxiv.org/abs/1810.04805" \
  --output transformer-vs-bert.md
```

### 场景 3: 研究进展追踪

```bash
# 1. 添加监控主题
lit track report --type weekly --topic "prompt engineering" --output weekly-report.md

# 2. 检索最新论文
lit search "prompt engineering" --sort date --limit 10

# 3. 分析热门论文
lit analyze "latest-paper-url" --mode quick
```

### 场景 4: 概念对比与选择

```bash
# 1. 对比两个技术方案
lit compare concepts "CNN" "RNN" --output cnn-vs-rnn.md

# 2. 对比多个模型
lit compare concepts "Transformer" "LSTM"

# 3. 构建对比图谱
lit graph CNN RNN LSTM Transformer --format mermaid
```

---

## 📁 项目结构

```
ScholarGraph/
├── cli.ts                      # 统一 CLI 入口
├── config.ts                   # 配置管理
├── README.md                   # 项目文档
├── ADVANCED_FEATURES.md        # 高级功能指南
├── TEST_RESULTS.md             # 测试结果报告
│
├── shared/                     # 共享模块
│   ├── ai-provider.ts          # AI 提供商抽象层
│   ├── types.ts                # 共享类型定义
│   ├── validators.ts           # 参数验证
│   └── errors.ts               # 错误处理
│
├── literature-search/          # 文献检索
│   ├── skill.md
│   └── scripts/
│       ├── search.ts
│       └── types.ts
│
├── concept-learner/            # 概念学习
│   ├── skill.md
│   └── scripts/
│       ├── learn.ts
│       └── types.ts
│
├── knowledge-gap-detector/     # 知识盲区检测
│   ├── skill.md
│   └── scripts/
│       ├── detect.ts
│       └── types.ts
│
├── progress-tracker/           # 进展追踪
│   ├── skill.md
│   └── scripts/
│       ├── track.ts
│       └── types.ts
│
├── paper-analyzer/             # 论文分析
│   ├── skill.md
│   └── scripts/
│       ├── analyze.ts
│       └── types.ts
│
└── knowledge-graph/            # 知识图谱
    ├── skill.md
    └── scripts/
        ├── graph.ts
        └── types.ts
```

---

## 🔧 配置

### 配置文件

配置文件 `scholargraph-config.json`：

```json
{
  "user": {
    "interests": ["Machine Learning", "NLP"],
    "level": "intermediate",
    "primaryLanguage": "zh-CN"
  },
  "search": {
    "defaultSources": ["arxiv", "semantic_scholar"],
    "maxResults": 20,
    "sortBy": "relevance"
  },
  "learning": {
    "depth": "standard",
    "includePapers": true,
    "includeCode": false
  },
  "tracking": {
    "enabled": true,
    "frequency": "weekly",
    "keywords": ["transformer", "large language model"]
  }
}
```

### 配置管理命令

```bash
# 初始化配置文件
lit config init

# 显示当前配置
lit config show

# 设置配置项
lit config set user.level "advanced"
lit config set learning.depth "deep"

# 重置为默认配置
lit config reset
```

---

## 🌐 环境变量

### AI 提供商配置

```bash
# 选择 AI 提供商
export AI_PROVIDER=openai  # zai, openai, anthropic, azure, ollama, qwen, deepseek, zhipu, minimax, moonshot, baichuan, yi, doubao, groq, together

# 国际厂商
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_API_KEY="your-key"
export GROQ_API_KEY="your-key"
export TOGETHER_API_KEY="your-key"
export OLLAMA_BASE_URL="http://localhost:11434"

# 国内厂商
export QWEN_API_KEY="your-key"           # 或 DASHSCOPE_API_KEY
export DEEPSEEK_API_KEY="your-key"
export ZHIPU_API_KEY="your-key"
export MINIMAX_API_KEY="your-key"
export MOONSHOT_API_KEY="your-key"
export BAICHUAN_API_KEY="your-key"
export YI_API_KEY="your-key"
export DOUBAO_API_KEY="your-key"

# 搜索 API（可选）
export SERPER_API_KEY="your-key"  # 用于 web 搜索功能
```

---

## 📊 输出格式

### Markdown 报告

所有工具都支持 Markdown 输出，便于阅读和分享：

- **概念卡片**: 定义、组成、历史、应用、学习路径、代码示例
- **知识盲区报告**: 盲区分析、学习建议、工作量估算
- **进展报告**: 新论文、热门主题、推荐阅读
- **论文分析**: 方法、实验、贡献、局限性
- **对比分析**: 相似点、差异点、使用场景
- **批判性分析**: 优点、缺点、研究空白、改进建议

### JSON 数据

结构化 JSON 输出，便于程序化处理：

```typescript
interface SearchResult {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  publishDate: string;
  citationCount: number;
  url: string;
  source: string;
}

interface ConceptCard {
  concept: string;
  definition: string;
  coreComponents: Component[];
  applications: Application[];
  relatedConcepts: RelatedConcept[];
  learningPath: LearningPhase[];
  codeExamples?: CodeExample[];
  papers?: Paper[];
}
```

---

## 🧪 测试

项目已通过全面测试，所有功能正常工作。

### 运行测试

```bash
# 测试基础功能
bun run cli.ts search "transformer" --limit 5
bun run cli.ts learn "BERT" --depth intermediate
bun run cli.ts detect --domain "NLP" --known "transformer"

# 测试高级功能
bun run cli.ts compare concepts CNN RNN
bun run cli.ts compare papers "url1" "url2"
bun run cli.ts critique "paper-url" --focus "novelty"
bun run cli.ts path "ML" "DL" --concepts "NN"

# 测试编程 API
bun run test-advanced-features.ts
```

### 测试结果

查看 [TEST_RESULTS.md](TEST_RESULTS.md) 了解详细的测试结果和覆盖范围。

---

## 📝 命令行参考

### 完整命令列表

```bash
lit <command> [options]

命令:
  search <query>              检索相关文献
  learn <concept>             学习概念并生成知识卡片
  detect --domain <d>         检测知识盲区
  track <action>              进展追踪
  analyze <url>               分析论文
  graph <concepts...>         构建知识图谱
  compare <type> <items...>   对比分析
  critique <url>              批判性分析论文
  path <from> <to>            查找学习路径
  config <action>             配置管理

选项:
  --help, -h                  显示帮助信息
  --output <file>             输出文件路径
  --limit <n>                 结果数量限制
  --depth <d>                 学习深度 (beginner|intermediate|advanced)
  --mode <m>                  分析模式 (quick|standard|deep)
  --format <f>                输出格式 (mermaid|json)
  --focus <areas>             关注领域 (逗号分隔)
```

详细使用说明请参考 [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md)。

---

## 🛠️ 开发指南

### 添加新功能

1. 创建目录结构：
```bash
mkdir -p my-feature/scripts
```

2. 编写功能描述 (`skill.md`)

3. 实现核心脚本 (`scripts/main.ts`)

4. 定义类型 (`scripts/types.ts`)

5. 在 `cli.ts` 中注册命令

### 代码规范

- 使用 TypeScript 严格模式
- 遵循 ESLint 规则
- 编写单元测试
- 添加 JSDoc 注释

---

## ⚠️ 注意事项

### API 速率限制

- **Semantic Scholar API**: 有速率限制，已实现自动重试和延迟
- **arXiv API**: 相对宽松，推荐用于批量操作
- **建议**: 使用 arXiv URL 进行论文分析和对比

### 最佳实践

1. **使用 arXiv URL**: 比 Semantic Scholar URL 更稳定
2. **配置 SERPER_API_KEY**: 提供 web 搜索降级能力
3. **选择合适的分析模式**: quick 用于快速浏览，deep 用于深度研究
4. **批量操作间隔**: 避免短时间内大量请求

---

## 🤝 贡献指南

欢迎贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [arXiv](https://arxiv.org/) - 开放获取的论文仓库
- [Semantic Scholar](https://www.semanticscholar.org/) - 学术搜索引擎
- [Bun](https://bun.sh/) - 快速的 JavaScript 运行时
- 所有 AI 提供商 - 提供强大的语言模型支持

---

## 📞 联系方式

- 问题反馈: [GitHub Issues](https://github.com/your-username/ScholarGraph/issues)
- 功能建议: [GitHub Discussions](https://github.com/your-username/ScholarGraph/discussions)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个 Star！⭐**

Made with ❤️ by the ScholarGraph Team

</div>
