#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新股票最新资料 - 使用 akshare 获取 A 股股票列表
"""

import pandas as pd
import json
import os
from datetime import datetime

OUTPUT_FILE = '/home/admin/openclaw/workspace/temp/stocks_full.json'

def fetch_stocks_akshare():
    """使用 akshare 获取 A 股股票列表"""
    try:
        import akshare as ak
        
        print("📊 正在从 akshare 获取 A 股股票列表...")
        
        # 获取 A 股股票列表
        stock_info = ak.stock_info_a_code_name()
        
        stocks = []
        for _, row in stock_info.iterrows():
            code = row['code']
            name = row['name']
            
            # 跳过 ST 股票
            if 'ST' in name:
                continue
            
            # 确定市场
            if code.startswith('6'):
                market = 'sh'
            elif code.startswith('0') or code.startswith('3'):
                market = 'sz'
            else:
                continue
            
            stock = {
                "code": f"{market}{code}",
                "name": name,
                "ts_code": code,
                "market": market,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            stocks.append(stock)
        
        return stocks
        
    except Exception as e:
        print(f"❌ akshare 获取失败：{e}")
        return None

def fetch_from_eastmoney_batch():
    """从东方财富获取（改进版，带更长延迟）"""
    import requests
    import time
    
    all_stocks = []
    
    print("📊 正在从东方财富获取 A 股股票列表...")
    
    for page in range(1, 80):
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
                    'fields': 'f12,f14,f13,f140,f141'
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "http://quote.eastmoney.com/"
                }
                response = requests.get(url, params=params, headers=headers, timeout=30)
                data = response.json()
                
                if not data.get('data') or not data['data'].get('diff'):
                    break
                
                stocks = data['data']['diff']
                if len(stocks) == 0:
                    print(f"  页 {page}: 无数据，结束")
                    return all_stocks
                
                for s in stocks:
                    name = s.get('f14', '')
                    if 'ST' in name or '*' in name:
                        continue
                    code = s.get('f12', '')
                    market_code = s.get('f13', 0)
                    market = 'sh' if market_code == 1 else 'sz'
                    
                    stock = {
                        "code": f"{market}{code}",
                        "name": name,
                        "ts_code": code,
                        "market": market,
                        "industry": s.get('f141', '未知'),
                        "area": s.get('f140', '未知'),
                        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 去重
                    if not any(x['ts_code'] == code for x in all_stocks):
                        all_stocks.append(stock)
                
                print(f"  页 {page}: 累计 {len(all_stocks)} 只")
                success = True
                time.sleep(1.5)  # 增加延迟避免被封
                break
                
            except Exception as e:
                print(f"  页 {page}: 重试 {retry+1}/3 - {e}")
                time.sleep(3)
        
        if not success:
            print(f"  页 {page}: 失败，跳过")
            time.sleep(2)
    
    return all_stocks

def main():
    print("=" * 60)
    print("更新股票最新资料")
    print("=" * 60)
    
    stocks = None
    
    # 先尝试 akshare
    if stocks is None:
        stocks = fetch_stocks_akshare()
    
    # akshare 失败则尝试东方财富
    if stocks is None or len(stocks) == 0:
        print("\nakshare 不可用，尝试东方财富...")
        stocks = fetch_from_eastmoney_batch()
    
    if stocks and len(stocks) > 0:
        # 保存
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(stocks, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 成功获取 {len(stocks)} 只股票")
        print(f"📁 已保存至：{OUTPUT_FILE}")
        
        sh_count = sum(1 for s in stocks if s['code'].startswith('sh'))
        sz_count = sum(1 for s in stocks if s['code'].startswith('sz'))
        print(f"\n📊 市场分布:")
        print(f"   沪市 (sh): {sh_count} 只")
        print(f"   深市 (sz): {sz_count} 只")
    else:
        print("\n❌ 无法获取股票数据")

if __name__ == "__main__":
    main()
