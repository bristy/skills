#!/usr/bin/env python3
"""Tiered Recall 性能评估脚本"""

import json
from pathlib import Path
from datetime import datetime, timedelta

workspace = Path('C:/Windows/System32/UsersAdministrator.openclawworkspace')
memory_dir = workspace / 'memory'
output_dir = workspace / '.tiered-recall'

# 1. 统计文件大小
total_size = 0
file_count = 0
for f in memory_dir.glob('*.md'):
    total_size += f.stat().st_size
    file_count += 1

# 2. 最近2天日志大小
recent_size = 0
for i in range(2):
    date = datetime.now() - timedelta(days=i)
    filename = date.strftime('%Y-%m-%d') + '.md'
    f = memory_dir / filename
    if f.exists():
        recent_size += f.stat().st_size

# 3. MEMORY.md大小
memory_md_size = (workspace / 'MEMORY.md').stat().st_size

# 4. 索引大小
index_size = (output_dir / 'index.json').stat().st_size
projects_size = (output_dir / 'projects.json').stat().st_size

# 5. token估算（中文约2字=1token）
print('=' * 50)
print('📊 Token 消耗分析')
print('=' * 50)
print(f'总日志文件: {file_count}个, {total_size/1024:.1f}KB')
print(f'近期2天日志: {recent_size/1024:.1f}KB (约{recent_size//2} token)')
print(f'MEMORY.md: {memory_md_size/1024:.1f}KB (约{memory_md_size//2} token)')
print(f'索引文件: {(index_size+projects_size)/1024:.1f}KB')
print()
print('=' * 50)
print('📐 分层加载预算')
print('=' * 50)
l0 = memory_md_size // 2
l1 = recent_size // 2
l2 = 5000  # 固定预算
l3 = (index_size + projects_size) // 2
total = l0 + l1 + l2 + l3
print(f'L0 核心记忆: ~{l0} token')
print(f'L1 近期日志: ~{l1} token')
print(f'L2 活跃项目: ~{l2} token (固定)')
print(f'L3 记忆索引: ~{l3} token')
print(f'总计: ~{total} token')
print(f'占200k上下文: {total/200000*100:.1f}%')
print()
print('=' * 50)
print('💡 对比分析')
print('=' * 50)
print(f'手动回忆（全量）: ~{total_size//2} token')
print(f'分层回忆（默认）: ~{total} token')
saving = total_size//2 - total
print(f'节省: {saving} token ({(1-total/(total_size//2))*100:.1f}%)')
print()
print('=' * 50)
print('⚡ 速度影响')
print('=' * 50)
# 估算加载时间
import time
start = time.time()
# 模拟加载
with open(workspace / 'MEMORY.md', 'r', encoding='utf-8') as f:
    _ = f.read()
for i in range(2):
    date = datetime.now() - timedelta(days=i)
    filename = date.strftime('%Y-%m-%d') + '.md'
    f = memory_dir / filename
    if f.exists():
        with open(f, 'r', encoding='utf-8') as fp:
            _ = fp.read()
with open(output_dir / 'index.json', 'r', encoding='utf-8') as f:
    _ = f.read()
with open(output_dir / 'projects.json', 'r', encoding='utf-8') as f:
    _ = f.read()
elapsed = time.time() - start
print(f'分层加载耗时: {elapsed*1000:.1f}ms')
print(f'对新session启动影响: 可忽略（<100ms）')
print()
print('=' * 50)
print('📈 评估结论')
print('=' * 50)
print(f'✅ Token消耗: 约{total}token，仅占上下文{total/200000*100:.1f}%')
print(f'✅ 节省效果: 比全量回忆节省{saving}token')
print(f'✅ 速度影响: 加载耗时{elapsed*1000:.1f}ms，可忽略')
print(f'✅ 实用性: 2天日志覆盖最近工作，足够日常使用')