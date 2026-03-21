#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取全市场 A 股列表（约 5000 只）
带重试机制和进度保存
"""

import requests
import json
import time
import os

STOCKS_FILE = '/home/admin/openclaw/workspace/temp/stocks_full.json'

def load_existing():
    """加载已获取的股票"""
    if os.path.exists(STOCKS_FILE):
        try:
            with open(STOCKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def save_progress(stocks):
    """保存进度"""
    with open(STOCKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)

def fetch_from_eastmoney():
    """从东方财富分页获取（带重试）"""
    all_stocks = load_existing()
    start_page = len(all_stocks) // 80 + 1
    
    print(f"已加载 {len(all_stocks)} 只股票，从第 {start_page} 页继续...")
    
    for page in range(start_page, 100):
        success = False
        for retry in range(3):
            try:
                url = "http://push2.eastmoney.com/api/qt/clist/get"
                params = {
                    'pn': page,
                    'pz': 80,
                    'po': 1,
                    'np': 1,
                    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                    'fltt': 2,
                    'invt': 2,
                    'fid': 'f3',
                    'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',
                    'fields': 'f12,f14,f128,f140,f141'
                }
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, params=params, headers=headers, timeout=15)
                data = response.json()
                
                if not data.get('data') or not data['data'].get('diff'):
                    break
                
                stocks = data['data']['diff']
                if len(stocks) == 0:
                    print(f"  页 {page}: 无数据，结束")
                    return all_stocks
                
                new_count = 0
                for s in stocks:
                    name = s.get('f14', '')
                    if 'ST' in name:
                        continue
                    code = s.get('f12', '')
                    market = 'sh' if s.get('f13', 0) == 1 else 'sz'
                    
                    stock = {
                        "code": f"{market}{code}",
                        "name": name,
                        "ts_code": code,
                        "industry": s.get('f141', '未知'),
                        "area": s.get('f140', '未知')
                    }
                    
                    # 去重
                    if not any(x['ts_code'] == code for x in all_stocks):
                        all_stocks.append(stock)
                        new_count += 1
                
                print(f"  页 {page}: 新增 {new_count} 只，累计 {len(all_stocks)} 只")
                save_progress(all_stocks)
                success = True
                time.sleep(0.5)  # 增加延迟
                break
                
            except Exception as e:
                print(f"  页 {page}: 重试 {retry+1}/3 - {e}")
                time.sleep(2)
        
        if not success:
            print(f"  页 {page}: 失败，跳过")
            time.sleep(1)
    
    return all_stocks

if __name__ == "__main__":
    print("=" * 60)
    print("获取全市场 A 股列表（带重试）...")
    print("=" * 60)
    
    stocks = fetch_from_eastmoney()
    
    print(f"\n✅ 成功获取 {len(stocks)} 只股票")
    print(f"📁 已保存至：{STOCKS_FILE}")
    
    sh_count = sum(1 for s in stocks if s['code'].startswith('sh'))
    sz_count = sum(1 for s in stocks if s['code'].startswith('sz'))
    print(f"\n📊 市场分布:")
    print(f"   沪市 (sh): {sh_count} 只")
    print(f"   深市 (sz): {sz_count} 只")
