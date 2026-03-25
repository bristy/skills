#!/usr/bin/env python3
"""
Vocabulary Lookup - GPT4单词库查询工具
从8714词GPT4词典中查询单词详情
"""

import argparse
import json
import random
import os

DICT_PATH = "/root/.openclaw/workspace-knowledgegao/notes/resources/documents/dictionary-by-gpt4.json"


def load_dict():
    """加载词典（建立word->content的字典）"""
    word_dict = {}
    if not os.path.exists(DICT_PATH):
        print(f"错误：词典文件不存在: {DICT_PATH}")
        return None
    
    with open(DICT_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    word = obj.get('word', '').upper()
                    word_dict[word] = obj.get('content', '')
                except json.JSONDecodeError:
                    continue
    return word_dict


def lookup_word(word_dict, word):
    """查询单词"""
    result = word_dict.get(word.upper())
    if result:
        return format_output(word, result)
    else:
        return f"未找到单词: {word}"


def search_words(word_dict, query, limit=10):
    """模糊搜索"""
    query_upper = query.upper()
    matches = [w for w in word_dict.keys() if query_upper in w]
    if not matches:
        return f"未找到包含 '{query}' 的单词"
    
    results = []
    for i, word in enumerate(matches[:limit]):
        results.append(format_output(word, word_dict[word]))
    
    header = f"找到 {len(matches)} 个包含 '{query}' 的单词，显示前 {len(results)} 个：\n"
    return header + "\n---\n".join(results)


def random_words(word_dict, count=5):
    """随机抽取单词"""
    all_words = list(word_dict.keys())
    if count > len(all_words):
        count = len(all_words)
    
    selected = random.sample(all_words, count)
    results = []
    for word in selected:
        results.append(format_output(word, word_dict[word]))
    
    return f"随机抽取 {count} 个单词：\n\n" + "\n---\n".join(results)


def starts_with(word_dict, letter, limit=10):
    """按首字母筛选"""
    letter_upper = letter.upper()
    matches = [w for w in word_dict.keys() if w.startswith(letter_upper)]
    
    if not matches:
        return f"没有找到以 '{letter}' 开头的单词"
    
    results = []
    for word in matches[:limit]:
        results.append(format_output(word, word_dict[word]))
    
    header = f"以 '{letter_upper}' 开头的单词共 {len(matches)} 个，显示前 {len(results)} 个：\n"
    return header + "\n---\n".join(results)


def format_output(word, content):
    """格式化输出"""
    return f"### {word}\n\n{content}"


def main():
    parser = argparse.ArgumentParser(description='GPT4单词库查询')
    parser.add_argument('--word', '-w', action='append', help='查询的单词（可多个）')
    parser.add_argument('--search', '-s', help='模糊搜索')
    parser.add_argument('--random', '-r', type=int, help='随机抽取N个单词')
    parser.add_argument('--starts-with', '-a', help='按首字母筛选')
    parser.add_argument('--limit', '-l', type=int, default=10, help='结果显示数量')
    
    args = parser.parse_args()
    
    print("加载词典...", end=" ", flush=True)
    word_dict = load_dict()
    if not word_dict:
        return
    print(f"完成，共 {len(word_dict)} 个单词")
    
    if args.word:
        for word in args.word:
            print(f"\n{lookup_word(word_dict, word)}\n")
    
    if args.search:
        print(f"\n{search_words(word_dict, args.search, args.limit)}\n")
    
    if args.random:
        print(f"\n{random_words(word_dict, args.random)}\n")
    
    if args.starts_with:
        print(f"\n{starts_with(word_dict, args.starts_with, args.limit)}\n")
    
    if not any([args.word, args.search, args.random, args.starts_with]):
        parser.print_help()


if __name__ == "__main__":
    main()
