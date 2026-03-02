/**
 * Shared Utils - 公共工具函数
 * 提供 XML 解析、JSON 提取、重试机制、超时控制等
 */

import type { ParsedArxivEntry, RetryOptions, JsonExtractionResult } from './types';
import { TimeoutError, ParseError, ApiCallError, isRetryableError, getErrorMessage } from './errors';

// 默认重试配置
const DEFAULT_RETRY_OPTIONS: Required<RetryOptions> = {
  maxRetries: 3,
  initialDelayMs: 1000,
  maxDelayMs: 10000,
  backoffMultiplier: 2,
  retryableErrors: ['ECONNRESET', 'ETIMEDOUT', 'ECONNREFUSED', 'rate limit', '429', '503']
};

// 默认超时时间
const DEFAULT_TIMEOUT_MS = 30000;

/**
 * 解析 arXiv XML 响应
 * 使用 DOMParser 替代正则表达式，更安全可靠
 */
export function parseArxivXml(xml: string): ParsedArxivEntry[] {
  const results: ParsedArxivEntry[] = [];

  try {
    // 在 Node/Bun 环境中使用简单的 XML 解析
    // 由于 DOMParser 在 Node 中不可用，使用改进的正则解析
    const entries = xml.split('<entry>').slice(1);

    for (const entry of entries) {
      try {
        const id = extractXmlTag(entry, 'id');
        const title = extractXmlTag(entry, 'title').replace(/\s+/g, ' ').trim();
        const abstract = extractXmlTag(entry, 'summary').replace(/\s+/g, ' ').trim();
        const published = extractXmlTag(entry, 'published');
        const updated = extractXmlTag(entry, 'updated');

        // 提取作者 - 改进的解析
        const authors: string[] = [];
        const authorRegex = /<author>[\s\S]*?<name>([^<]+)<\/name>[\s\S]*?<\/author>/g;
        let authorMatch;
        while ((authorMatch = authorRegex.exec(entry)) !== null) {
          const name = authorMatch[1].trim();
          if (name) {
            authors.push(name);
          }
        }

        // 提取分类
        const categories: string[] = [];
        const categoryRegex = /category\s+term="([^"]+)"/g;
        let categoryMatch;
        while ((categoryMatch = categoryRegex.exec(entry)) !== null) {
          categories.push(categoryMatch[1]);
        }

        // 提取 PDF URL
        const pdfLinkMatch = entry.match(/<link[^>]*title="pdf"[^>]*href="([^"]+)"/);
        const pdfUrl = pdfLinkMatch ? pdfLinkMatch[1] : id.replace('/abs/', '/pdf/') + '.pdf';

        // 提取 arXiv ID
        const arxivId = id.split('/abs/')[1] || id;

        results.push({
          id: arxivId,
          title,
          authors,
          abstract,
          published: published.split('T')[0],
          updated: updated ? updated.split('T')[0] : undefined,
          categories,
          pdfUrl
        });
      } catch (e) {
        // 跳过解析失败的条目
        continue;
      }
    }
  } catch (error) {
    throw new ParseError('Failed to parse arXiv XML response', {
      format: 'xml',
      cause: error instanceof Error ? error : undefined
    });
  }

  return results;
}

/**
 * 提取 XML 标签内容
 */
function extractXmlTag(xml: string, tag: string): string {
  const regex = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, 'i');
  const match = xml.match(regex);
  return match ? match[1].trim() : '';
}

/**
 * 安全提取 JSON
 * 使用平衡括号匹配，支持嵌套 JSON
 */
export function extractJson<T = unknown>(text: string): JsonExtractionResult<T> {
  // 首先尝试从 markdown 代码块中提取
  const codeBlockMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (codeBlockMatch) {
    text = codeBlockMatch[1].trim();
  }

  // 查找 JSON 对象或数组的起始位置
  const objectStart = text.indexOf('{');
  const arrayStart = text.indexOf('[');

  let startIndex: number;
  let openChar: string;
  let closeChar: string;

  if (objectStart === -1 && arrayStart === -1) {
    return {
      success: false,
      error: 'No JSON object or array found in text'
    };
  }

  if (objectStart === -1) {
    startIndex = arrayStart;
    openChar = '[';
    closeChar = ']';
  } else if (arrayStart === -1) {
    startIndex = objectStart;
    openChar = '{';
    closeChar = '}';
  } else {
    // 选择先出现的
    if (objectStart < arrayStart) {
      startIndex = objectStart;
      openChar = '{';
      closeChar = '}';
    } else {
      startIndex = arrayStart;
      openChar = '[';
      closeChar = ']';
    }
  }

  // 使用平衡括号匹配找到完整的 JSON
  let depth = 0;
  let inString = false;
  let escapeNext = false;
  let endIndex = -1;

  for (let i = startIndex; i < text.length; i++) {
    const char = text[i];

    if (escapeNext) {
      escapeNext = false;
      continue;
    }

    if (char === '\\' && inString) {
      escapeNext = true;
      continue;
    }

    if (char === '"') {
      inString = !inString;
      continue;
    }

    if (inString) {
      continue;
    }

    if (char === openChar || (openChar === '{' && char === '{') || (openChar === '[' && char === '[')) {
      if (char === openChar) depth++;
    } else if (char === closeChar || (closeChar === '}' && char === '}') || (closeChar === ']' && char === ']')) {
      if (char === closeChar) depth--;
      if (depth === 0) {
        endIndex = i;
        break;
      }
    }
  }

  if (endIndex === -1) {
    return {
      success: false,
      error: 'Unbalanced brackets in JSON'
    };
  }

  const jsonStr = text.substring(startIndex, endIndex + 1);

  try {
    const data = JSON.parse(jsonStr) as T;
    return {
      success: true,
      data,
      rawMatch: jsonStr
    };
  } catch (error) {
    return {
      success: false,
      error: `JSON parse error: ${getErrorMessage(error)}`,
      rawMatch: jsonStr
    };
  }
}

/**
 * 带重试的异步函数执行
 * 使用指数退避策略
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...DEFAULT_RETRY_OPTIONS, ...options };
  let lastError: Error | undefined;
  let delay = opts.initialDelayMs;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(getErrorMessage(error));

      // 检查是否应该重试
      if (attempt >= opts.maxRetries || !isRetryableError(error)) {
        throw lastError;
      }

      // 等待后重试
      await sleep(delay);
      delay = Math.min(delay * opts.backoffMultiplier, opts.maxDelayMs);
    }
  }

  throw lastError || new Error('Retry failed');
}

/**
 * 带重试的 fetch
 */
export async function fetchWithRetry(
  url: string,
  init?: RequestInit,
  options: RetryOptions = {}
): Promise<Response> {
  return withRetry(async () => {
    const response = await fetch(url, init);

    // 检查是否需要重试的状态码
    if (response.status === 429 || response.status >= 500) {
      throw new ApiCallError(`HTTP ${response.status}`, {
        endpoint: url,
        responseStatus: response.status,
        retryable: true
      });
    }

    if (!response.ok) {
      throw new ApiCallError(`HTTP ${response.status}: ${response.statusText}`, {
        endpoint: url,
        responseStatus: response.status,
        retryable: false
      });
    }

    return response;
  }, options);
}

/**
 * 带超时的 Promise
 */
export async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
  operation?: string
): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout>;

  const timeoutPromise = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => {
      reject(new TimeoutError(
        `Operation timed out after ${timeoutMs}ms${operation ? `: ${operation}` : ''}`,
        { timeoutMs, operation }
      ));
    }, timeoutMs);
  });

  try {
    const result = await Promise.race([promise, timeoutPromise]);
    clearTimeout(timeoutId!);
    return result;
  } catch (error) {
    clearTimeout(timeoutId!);
    throw error;
  }
}

/**
 * 带超时的 Promise.allSettled
 */
export async function promiseAllWithTimeout<T>(
  promises: Promise<T>[],
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<PromiseSettledResult<T>[]> {
  const wrappedPromises = promises.map(p =>
    withTimeout(p, timeoutMs).then(
      value => ({ status: 'fulfilled' as const, value }),
      reason => ({ status: 'rejected' as const, reason })
    )
  );

  return Promise.all(wrappedPromises);
}

/**
 * 睡眠函数
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 安全的字符串截断
 */
export function truncate(str: string, maxLength: number, suffix: string = '...'): string {
  if (str.length <= maxLength) {
    return str;
  }
  return str.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * 标准化标题用于去重
 */
export function normalizeTitle(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]/g, '') // 保留字母、数字和中文
    .substring(0, 50);
}
