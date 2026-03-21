#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据库管理系统 v1.0
功能：下载数据、存储到 SQLite、每日自动更新
"""

import sqlite3
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import os
import sys

class StockDatabase:
    def __init__(self, db_path='/home/admin/openclaw/workspace/stock_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建股票数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date INTEGER NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                amount REAL,
                stock_code TEXT NOT NULL,
                market TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, stock_code)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON stock_data(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_code ON stock_data(stock_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_stock ON stock_data(date, stock_code)')
        
        conn.commit()
        conn.close()
        print("✅ 数据库初始化完成")
    
    def load_csv(self, csv_path):
        """从 CSV 文件加载数据"""
        print(f"📊 加载 CSV 文件：{csv_path}")
        df = pd.read_csv(csv_path, on_bad_lines='skip')
        
        conn = sqlite3.connect(self.db_path)
        
        # 去重后写入
        df = df.drop_duplicates(subset=['date', 'stock_code'])
        df.to_sql('stock_data', conn, if_exists='append', index=False)
        
        # 统计
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM stock_data')
        count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(DISTINCT stock_code) FROM stock_data')
        stocks = cursor.fetchone()[0]
        cursor.execute('SELECT MIN(date), MAX(date) FROM stock_data')
        date_range = cursor.fetchone()
        
        conn.close()
        
        print(f"✅ 导入完成")
        print(f"   总记录数：{count:,} 条")
        print(f"   股票数量：{stocks} 只")
        print(f"   日期范围：{date_range[0]} - {date_range[1]}")
    
    def update_daily(self):
        """更新当日数据"""
        print(f"\n🔄 更新当日数据... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取最新日期
        cursor.execute('SELECT MAX(date) FROM stock_data')
        last_date = cursor.fetchone()[0]
        print(f"   数据库最新日期：{last_date}")
        
        # 获取今日数据（使用 AKShare）
        try:
            today = datetime.now().strftime('%Y%m%d')
            if last_date and int(today) <= int(last_date):
                print(f"   数据已是最新")
                return
            
            # 获取 A 股实时行情
            df = ak.stock_zh_a_spot_em()
            print(f"   获取到 {len(df)} 只股票行情")
            
            # 转换格式
            df['date'] = int(today)
            df['stock_code'] = df['代码'].astype(str)
            df['market'] = df['代码'].apply(lambda x: 'sh' if x.startswith('6') else 'sz')
            df['open'] = df['开盘']
            df['high'] = df['最高']
            df['low'] = df['最低']
            df['close'] = df['最新价']
            df['volume'] = df['成交量']
            df['amount'] = df['成交额']
            
            # 写入数据库
            for _, row in df.iterrows():
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO stock_data 
                        (date, open, high, low, close, volume, amount, stock_code, market)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        int(row['date']), row['open'], row['high'], row['low'],
                        row['close'], row['volume'], row['amount'],
                        str(row['stock_code']), row['market']
                    ))
                except:
                    continue
            
            conn.commit()
            print(f"   ✅ 更新成功")
            
        except Exception as e:
            print(f"   ❌ 更新失败：{e}")
        
        conn.close()
    
    def get_latest_data(self, limit=1000):
        """获取最新数据"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT * FROM stock_data 
            WHERE date = (SELECT MAX(date) FROM stock_data)
            ORDER BY close DESC
            LIMIT ?
        ''', conn, params=(limit,))
        conn.close()
        return df
    
    def get_stock_history(self, stock_code, days=60):
        """获取个股历史数据"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT * FROM stock_data 
            WHERE stock_code = ?
            ORDER BY date DESC
            LIMIT ?
        ''', conn, params=(stock_code, days))
        conn.close()
        return df

if __name__ == '__main__':
    db = StockDatabase()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'load':
            db.load_csv(sys.argv[2])
        elif sys.argv[1] == 'update':
            db.update_daily()
        elif sys.argv[1] == 'query':
            df = db.get_latest_data()
            print(df.head())
    else:
        print("用法：python stock_database.py [load|update|query] [args]")
