#!/usr/bin/env python3
"""
九章技能进化系统 - 数据收集脚本
收集技能使用数据并存储到本地SQLite数据库
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# 数据库路径
DB_PATH = Path(os.getenv('JIUZHANG_WORKSPACE', '~/.openclaw/workspace')) / 'skills' / 'evolution-data.db'

def init_db():
    """初始化数据库"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skill_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            query TEXT,
            response_time_ms INTEGER,
            success BOOLEAN,
            user_feedback INTEGER,  -- -1: 负面, 0: 中性, 1: 正面
            case_references TEXT,   -- JSON array of case IDs
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skill_stats (
            date TEXT PRIMARY KEY,
            skill_name TEXT NOT NULL,
            total_calls INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            avg_response_time_ms REAL DEFAULT 0,
            positive_feedback INTEGER DEFAULT 0,
            negative_feedback INTEGER DEFAULT 0,
            unique_cases_referenced INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")

def collect_usage(skill_name, query, response_time_ms, success=True, user_feedback=0, case_references=None):
    """记录一次技能使用"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO skill_usage 
        (timestamp, skill_name, query, response_time_ms, success, user_feedback, case_references)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        skill_name,
        query,
        response_time_ms,
        success,
        user_feedback,
        json.dumps(case_references or [])
    ))
    
    conn.commit()
    conn.close()
    print(f"✅ 已记录 {skill_name} 的使用数据")

def collect_batch(data_file):
    """批量导入历史数据"""
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    for record in data:
        cursor.execute('''
            INSERT INTO skill_usage 
            (timestamp, skill_name, query, response_time_ms, success, user_feedback, case_references)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.get('timestamp', datetime.now().isoformat()),
            record['skill_name'],
            record.get('query', ''),
            record.get('response_time_ms', 0),
            record.get('success', True),
            record.get('user_feedback', 0),
            json.dumps(record.get('case_references', []))
        ))
        count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ 批量导入完成: {count} 条记录")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python collect.py [init|record|batch]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init':
        init_db()
    elif command == 'record' and len(sys.argv) >= 5:
        collect_usage(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    elif command == 'batch' and len(sys.argv) >= 3:
        collect_batch(sys.argv[2])
    else:
        print("用法: python collect.py [init|record <skill> <query> <time>|batch <file>]")
