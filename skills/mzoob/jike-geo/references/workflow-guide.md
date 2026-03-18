# 极义GEO 工作流指南

## 核心概念

### 什么是 GEO？
GEO（Generative Engine Optimization）= 生成式搜索引擎优化。
与传统 SEO 优化搜索引擎排名不同，GEO 优化的是品牌在 AI 搜索引擎回答中的可见度和引用率。

### 数据依赖链（重要）

```
products create → company save → keywords add → questions generate → articles generate
                                                      ↑ 需要 keyword_ids    ↑ 需要 question_id
```

- `questions generate` 必须先有关键词（`keywords add` 返回的 ID）
- `articles generate` 必须先有问题（`questions generate` 返回的 ID）
- `search create` 是**独立的**，只需要问题文本和品牌名，不依赖上述链路
- 依赖链中任何一步失败，后续步骤都无法执行，不要尝试绕过

### 数据层级
```
用户 → 产品(多个) → 公司信息(每产品一份)
                   → 核心词(多个) → 问题(多个) → 文章(多个) → 发布记录
                   → 图片素材库
```

### 问题阶段（L1-L4）
| 阶段 | 英文 | 含义 | 示例 |
|------|------|------|------|
| L1 | inquiry | 认知层 | "什么是GEO优化？" |
| L2 | understanding | 探索层 | "GEO优化有哪些方法？" |
| L3 | consideration | 评估层 | "GEO优化工具哪个好？" |
| L4 | purchase | 决策层 | "极义GEO怎么样？值得用吗？" |

### 支持的 AI 平台
| 平台 | ID 标识 | 说明 |
|------|---------|------|
| DeepSeek | deepseek | 深度求索 |
| Kimi | kimi | 月之暗面 |
| 通义千问 | qianwen | 阿里云 |
| 豆包 | doubao | 字节跳动 |
| 文心一言 | wenxin | 百度 |
| 智谱清言 | zhipu | 智谱AI |
| 腾讯元宝 | yuanbao | 腾讯 |

---

## 典型工作流

### 流程一：品牌 AI 可见度诊断（最常用）

```
1. 查看产品列表 → products list
2. 创建搜索任务 → search create --question "品牌名怎么样" --brand "品牌名" --platforms deepseek,kimi,qianwen,doubao
3. 查看结果 → search status --task-id xxx
```

注意：`search create` 不需要先创建关键词或问题，直接传文本即可。这是最快的诊断路径。

### 流程二：内容优化与分发（完整链路）

```
1. 创建产品 → products create（如果还没有）
2. 填写公司信息 → company save（提升文章质量）
3. 添加核心词 → keywords add
4. AI 生成问题 → questions generate --keyword-ids 1,2,3
5. 查看问题 → questions list
6. 生成文章 → articles generate --question-id xxx
7. 分发到自媒体 → publish record
```

**⚠️ 步骤 6 必须有步骤 4 的 question_id。如果步骤 4 失败，步骤 6 无法执行。**

### 流程三：批量监控

```
1. 确保已有问题（questions list 查看）
2. 批量搜索 → search batch --question-ids 1,2,3 --platforms deepseek,kimi,qianwen,doubao
3. 查看批量进度 → search batch-status --batch-id xxx
```

---

## 搜索结果解读

### 单平台结果结构
```json
{
  "platform": "deepseek",
  "answer": "AI 生成的回答全文...",
  "brand_mentioned": true,
  "brand_rank": 2,
  "sentiment": "positive",
  "citations": [
    {
      "position": 1,
      "title": "引用来源标题",
      "url": "https://...",
      "domain": "example.com"
    }
  ]
}
```

### 关键指标
- **brand_mentioned**: 品牌是否被提及
- **brand_rank**: 品牌在回答中的排名位置（0=未排名）
- **sentiment**: 情感倾向（positive/neutral/negative）
- **citations**: 引用来源列表，可分析哪些内容被 AI 引用

---

## 错误处理

### 原则
- 同一接口最多重试 1 次，连续失败 2 次后停止
- 不要反复尝试不同的绕过方式
- 明确告知用户失败原因和替代方案

### 常见错误

| 错误场景 | 处理方式 |
|---------|---------|
| 401 认证失败 | 引导用户前往 https://jike-geo.100.city 获取 API Key |
| 403 权限不足 | 检查产品归属或账号状态 |
| 500 / 服务过载 | 重试 1 次，仍失败则告知"服务暂时不可用，建议稍后再试" |
| questions generate 失败 | 告知用户原因，说明文章生成暂不可用。可直接为用户撰写 GEO 优化文章样稿作为参考 |
| articles generate 缺少 question_id | 引导用户先完成 keywords add → questions generate 流程，不要尝试绕过 |
