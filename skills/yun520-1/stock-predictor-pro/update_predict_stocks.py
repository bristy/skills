#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新预测系统的股票列表 - 基于现有 346 只股票更新最新信息
"""

import json
import os
from datetime import datetime

STOCKS_FULL = '/home/admin/openclaw/workspace/temp/stocks_full.json'
STOCKS_PREDICT = '/home/admin/openclaw/workspace/temp/stocks.json'

def main():
    print("=" * 60)
    print("更新预测系统股票列表")
    print("=" * 60)
    
    # 加载全市场股票
    if not os.path.exists(STOCKS_FULL):
        print("❌ 全市场股票文件不存在，请先运行 update_stock_info.py")
        return
    
    with open(STOCKS_FULL, 'r', encoding='utf-8') as f:
        all_stocks = json.load(f)
    
    # 创建查找字典
    stock_map = {s['ts_code']: s for s in all_stocks}
    
    # 加载现有预测股票列表
    if not os.path.exists(STOCKS_PREDICT):
        print("❌ 预测股票文件不存在")
        return
    
    with open(STOCKS_PREDICT, 'r', encoding='utf-8') as f:
        predict_stocks = json.load(f)
    
    print(f"📊 现有预测股票：{len(predict_stocks)} 只")
    print(f"📊 全市场股票：{len(all_stocks)} 只")
    
    # 更新股票信息
    updated = []
    not_found = []
    
    for stock in predict_stocks:
        ts_code = stock.get('ts_code', '')
        
        if ts_code in stock_map:
            # 保留原有行业信息（如果有）
            industry = stock.get('industry', stock_map[ts_code].get('industry', '未知'))
            area = stock.get('area', stock_map[ts_code].get('area', '未知'))
            
            updated_stock = {
                "code": stock_map[ts_code]['code'],
                "name": stock_map[ts_code]['name'],
                "ts_code": ts_code,
                "market": stock_map[ts_code].get('market', 'unknown'),
                "industry": industry,
                "area": area,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            updated.append(updated_stock)
        else:
            # 保留原有信息
            stock['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated.append(stock)
            not_found.append(ts_code)
    
    # 保存更新后的列表
    with open(STOCKS_PREDICT, 'w', encoding='utf-8') as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 更新完成：{len(updated)} 只股票")
    print(f"📁 已保存至：{STOCKS_PREDICT}")
    
    if not_found:
        print(f"\n⚠️  未在全市场列表中找到 {len(not_found)} 只股票:")
        for code in not_found[:10]:
            print(f"   - {code}")
        if len(not_found) > 10:
            print(f"   ... 还有 {len(not_found) - 10} 只")

if __name__ == "__main__":
    main()
