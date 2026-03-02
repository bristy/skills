/**
 * Literature Search - Core Module
 * 文献检索核心模块
 *
 * 提供多源文献检索能力：
 * - arXiv API
 * - Semantic Scholar API
 * - Web Search (通过统一 AI 提供商)
 */

import { createAIProvider, type AIProvider } from '../../shared/ai-provider';
import { parseArxivXml, fetchWithRetry, withTimeout, normalizeTitle } from '../../shared/utils';
import { ApiInitializationError, getErrorMessage } from '../../shared/errors';
import type { WebSearchResultItem } from '../../shared/types';
import type { SearchOptions, SearchResult, SearchResponse, SemanticScholarPaper } from './types';

// arXiv API 基础URL
const ARXIV_API_URL = 'http://export.arxiv.org/api/query';

// Semantic Scholar API 基础URL
const S2_API_URL = 'https://api.semanticscholar.org/graph/v1';

// 默认超时时间
const DEFAULT_TIMEOUT_MS = 30000;

export default class LiteratureSearch {
  private ai: AIProvider | null = null;

  /**
   * 初始化搜索器
   */
  async initialize(): Promise<void> {
    if (!this.ai) {
      try {
        this.ai = await createAIProvider();
      } catch (error) {
        throw new ApiInitializationError(
          `Failed to initialize AI provider: ${getErrorMessage(error)}`,
          error instanceof Error ? error : undefined
        );
      }
    }
  }

  /**
   * 综合搜索入口
   */
  async search(query: string, options: SearchOptions = {}): Promise<SearchResponse> {
    await this.initialize();

    const {
      sources = ['arxiv', 'semantic_scholar', 'web'],
      limit = 10,
      sortBy = 'relevance',
      filters
    } = options;

    const allResults: SearchResult[] = [];
    const usedSources: string[] = [];

    // 并行搜索多个数据源（带超时）
    const searchPromises: Promise<SearchResult[]>[] = [];

    if (sources.includes('arxiv')) {
      searchPromises.push(
        withTimeout(this.searchArxiv(query, limit), DEFAULT_TIMEOUT_MS, 'arXiv search')
          .catch(err => {
            console.error('arXiv search failed:', getErrorMessage(err));
            return [];
          })
      );
      usedSources.push('arxiv');
    }

    if (sources.includes('semantic_scholar')) {
      searchPromises.push(
        withTimeout(this.searchSemanticScholar(query, limit), DEFAULT_TIMEOUT_MS, 'Semantic Scholar search')
          .catch(err => {
            console.error('Semantic Scholar search failed:', getErrorMessage(err));
            return [];
          })
      );
      usedSources.push('semantic_scholar');
    }

    if (sources.includes('web')) {
      searchPromises.push(
        withTimeout(this.searchWeb(query, limit), DEFAULT_TIMEOUT_MS, 'Web search')
          .catch(err => {
            console.error('Web search failed:', getErrorMessage(err));
            return [];
          })
      );
      usedSources.push('web');
    }

    const results = await Promise.allSettled(searchPromises);

    // 合并结果
    results.forEach((result) => {
      if (result.status === 'fulfilled') {
        allResults.push(...result.value);
      }
    });

    // 应用过滤
    let filtered = this.applyFilters(allResults, filters);

    // 排序
    filtered = this.sortResults(filtered, sortBy);

    // 限制结果数量
    filtered = filtered.slice(0, limit * sources.length);

    // 去重（基于标题相似度）
    filtered = this.deduplicateResults(filtered);

    return {
      query,
      totalResults: filtered.length,
      results: filtered.slice(0, limit),
      sources: usedSources,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * arXiv 搜索（带重试）
   */
  private async searchArxiv(query: string, limit: number): Promise<SearchResult[]> {
    try {
      const searchQuery = encodeURIComponent(`all:${query}`);
      const url = `${ARXIV_API_URL}?search_query=${searchQuery}&max_results=${limit}&sortBy=relevance`;

      const response = await fetchWithRetry(url, undefined, { maxRetries: 3 });
      const text = await response.text();

      return this.parseArxivResponse(text);
    } catch (error) {
      console.error('arXiv search error:', getErrorMessage(error));
      return [];
    }
  }

  /**
   * 解析 arXiv API 响应（使用改进的 XML 解析器）
   */
  private parseArxivResponse(xml: string): SearchResult[] {
    const entries = parseArxivXml(xml);

    return entries.map(entry => ({
      id: entry.id,
      title: entry.title,
      authors: entry.authors,
      abstract: entry.abstract,
      publishDate: entry.published,
      source: 'arxiv',
      url: `https://arxiv.org/abs/${entry.id}`,
      pdfUrl: entry.pdfUrl,
      keywords: entry.categories
    }));
  }

  /**
   * Semantic Scholar 搜索（带重试）
   */
  private async searchSemanticScholar(query: string, limit: number): Promise<SearchResult[]> {
    try {
      const fields = 'paperId,title,abstract,authors,year,citationCount,venue,url,openAccessPdf';
      const url = `${S2_API_URL}/paper/search?query=${encodeURIComponent(query)}&limit=${limit}&fields=${fields}`;

      const response = await fetchWithRetry(url, undefined, { maxRetries: 3 });
      const data = await response.json() as { data?: SemanticScholarPaper[] };

      if (!data.data) return [];

      return data.data.map((paper) => ({
        id: paper.paperId,
        title: paper.title,
        authors: paper.authors.map(a => a.name),
        abstract: paper.abstract || '',
        publishDate: paper.year?.toString() || '',
        source: 'semantic_scholar',
        url: paper.url,
        pdfUrl: paper.openAccessPdf?.url,
        citations: paper.citationCount,
        venue: paper.venue
      }));
    } catch (error) {
      console.error('Semantic Scholar search error:', getErrorMessage(error));
      return [];
    }
  }

  /**
   * Web 搜索（通过统一 AI 提供商）
   */
  private async searchWeb(query: string, limit: number): Promise<SearchResult[]> {
    if (!this.ai) {
      await this.initialize();
    }

    try {
      // 检查 AI 提供商是否支持 web search
      if (!this.ai!.webSearch) {
        console.warn('Current AI provider does not support web search');
        return [];
      }

      // 构建学术搜索查询
      const academicQuery = `${query} research paper arxiv OR scholar OR "paper" OR "publication"`;

      const results: WebSearchResultItem[] = await this.ai!.webSearch(academicQuery, limit);

      return results.map((item, index) => ({
        id: `web_${index}`,
        title: item.name,
        authors: [],
        abstract: item.snippet || '',
        publishDate: item.date || '',
        source: 'web',
        url: item.url,
        snippet: item.snippet
      }));
    } catch (error) {
      console.error('Web search error:', getErrorMessage(error));
      return [];
    }
  }

  /**
   * 按作者搜索
   */
  async searchByAuthor(authorName: string, options: SearchOptions = {}): Promise<SearchResponse> {
    const query = `author:"${authorName}"`;
    return this.search(query, { ...options, sources: ['arxiv', 'semantic_scholar'] });
  }

  /**
   * 应用过滤条件
   */
  private applyFilters(results: SearchResult[], filters?: SearchOptions['filters']): SearchResult[] {
    if (!filters) return results;

    let filtered = [...results];

    // 年份过滤
    if (filters.yearRange) {
      const [start, end] = filters.yearRange;
      filtered = filtered.filter(r => {
        const year = parseInt(r.publishDate.split('-')[0]);
        return !isNaN(year) && year >= start && year <= end;
      });
    }

    // 最小引用数过滤
    if (filters.minCitations) {
      filtered = filtered.filter(r =>
        !r.citations || r.citations >= filters.minCitations!
      );
    }

    // 分类过滤
    if (filters.categories?.length) {
      filtered = filtered.filter(r =>
        r.keywords?.some(k => filters.categories!.includes(k))
      );
    }

    return filtered;
  }

  /**
   * 排序结果
   */
  private sortResults(results: SearchResult[], sortBy: string): SearchResult[] {
    const sorted = [...results];

    switch (sortBy) {
      case 'citations':
        return sorted.sort((a, b) => (b.citations || 0) - (a.citations || 0));
      case 'date':
        return sorted.sort((a, b) =>
          new Date(b.publishDate).getTime() - new Date(a.publishDate).getTime()
        );
      default:
        return sorted; // 按相关性（API默认顺序）
    }
  }

  /**
   * 去重（基于标题相似度）
   */
  private deduplicateResults(results: SearchResult[]): SearchResult[] {
    const seen = new Set<string>();
    const deduped: SearchResult[] = [];

    for (const result of results) {
      const normalizedTitle = normalizeTitle(result.title);

      if (!seen.has(normalizedTitle)) {
        seen.add(normalizedTitle);
        deduped.push(result);
      }
    }

    return deduped;
  }
}

// CLI 支持
if (import.meta.main) {
  const args = process.argv.slice(2);
  const query = args[0];

  if (!query) {
    console.error('Usage: bun run search.ts <query> [--limit N] [--source <arxiv|semantic_scholar|web>]');
    process.exit(1);
  }

  const limitIndex = args.indexOf('--limit');
  const limit = limitIndex > -1 ? parseInt(args[limitIndex + 1]) || 10 : 10;

  const sourceIndex = args.indexOf('--source');
  const source = sourceIndex > -1 ? args[sourceIndex + 1] as 'arxiv' | 'semantic_scholar' | 'web' : undefined;

  const searcher = new LiteratureSearch();

  searcher.search(query, {
    limit,
    sources: source ? [source] : undefined
  }).then(response => {
    console.log(JSON.stringify(response, null, 2));
  }).catch(err => {
    console.error('Search failed:', getErrorMessage(err));
    process.exit(1);
  });
}
