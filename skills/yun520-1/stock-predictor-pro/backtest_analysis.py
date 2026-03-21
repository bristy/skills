#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度分析回测结果 - 找出方向判断失败的原因
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

DATA_FILE = '/home/admin/openclaw/workspace/chinese-stock-dataset/chinese-stock-dataset.csv'

def load_data():
    print("📊 加载数据集...")
    df = pd.read_csv(DATA_FILE)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    return df.sort_values(['stock_code', 'date'])

def analyze_failures():
    print("="*80)
    print("深度分析：方向判断失败原因")
    print("="*80)
    
    df = load_data()
    
    # 采样分析
    stocks = df['stock_code'].unique()[:50]
    max_date = df['date'].max()
    
    print(f"\n分析股票：{len(stocks)} 只")
    print(f"最新日期：{max_date.date()}\n")
    
    # 分类统计
    stats = {
        'uptrend_correct': 0, 'uptrend_wrong': 0,
        'downtrend_correct': 0, 'downtrend_wrong': 0,
        'sideways_correct': 0, 'sideways_wrong': 0,
        'high_vol_correct': 0, 'high_vol_wrong': 0,
        'low_vol_correct': 0, 'low_vol_wrong': 0,
    }
    
    total = 0
    
    for stock in stocks:
        stock_df = df[df['stock_code'] == stock].sort_values('date')
        if len(stock_df) < 40:
            continue
        
        # 计算指标
        stock_df = stock_df.copy()
        stock_df['ma20'] = stock_df['close'].rolling(20).mean()
        stock_df['vol_ma20'] = stock_df['vol'].rolling(20).mean()
        stock_df['return'] = stock_df['close'].pct_change() * 100
        stock_df['volatility'] = stock_df['return'].rolling(20).std()
        
        # 回测最近 20 天
        recent = stock_df[stock_df['date'] > (max_date - pd.Timedelta(days=30))].iloc[-20:]
        
        for idx, row in recent.iterrows():
            if pd.isna(row['return']) or idx == stock_df.index[0]:
                continue
            
            prev_idx = stock_df.index.get_loc(idx) - 1
            if prev_idx < 0:
                continue
            
            prev_row = stock_df.iloc[prev_idx]
            
            # 实际方向
            actual = row['return']
            actual_dir = 'up' if actual > 0.5 else ('down' if actual < -0.5 else 'sideways')
            
            # 预测（简单 MA 交叉）
            if row['close'] > row['ma20']:
                pred_dir = 'up'
            elif row['close'] < row['ma20']:
                pred_dir = 'down'
            else:
                pred_dir = 'sideways'
            
            # 波动率分类
            vol = row['volatility'] if not pd.isna(row['volatility']) else 0
            is_high_vol = vol > 3
            
            # 统计
            correct = (pred_dir == actual_dir) or (abs(actual) < 0.5 and pred_dir in ['up', 'down'])
            
            if actual_dir == 'up':
                if correct: stats['uptrend_correct'] += 1
                else: stats['uptrend_wrong'] += 1
            elif actual_dir == 'down':
                if correct: stats['downtrend_correct'] += 1
                else: stats['downtrend_wrong'] += 1
            else:
                if correct: stats['sideways_correct'] += 1
                else: stats['sideways_wrong'] += 1
            
            if is_high_vol:
                if correct: stats['high_vol_correct'] += 1
                else: stats['high_vol_wrong'] += 1
            else:
                if correct: stats['low_vol_correct'] += 1
                else: stats['low_vol_wrong'] += 1
            
            total += 1
    
    # 汇总
    print("="*80)
    print("📊 分析结果")
    print("="*80)
    
    print(f"\n总样本：{total}\n")
    
    print("按趋势分类:")
    up_total = stats['uptrend_correct'] + stats['uptrend_wrong']
    down_total = stats['downtrend_correct'] + stats['downtrend_wrong']
    side_total = stats['sideways_correct'] + stats['sideways_wrong']
    
    if up_total > 0:
        print(f"  上涨趋势：{stats['uptrend_correct']}/{up_total} ({stats['uptrend_correct']/up_total*100:.1f}%)")
    if down_total > 0:
        print(f"  下跌趋势：{stats['downtrend_correct']}/{down_total} ({stats['downtrend_correct']/down_total*100:.1f}%)")
    if side_total > 0:
        print(f"  横盘震荡：{stats['sideways_correct']}/{side_total} ({stats['sideways_correct']/side_total*100:.1f}%)")
    
    print("\n按波动率分类:")
    high_vol_total = stats['high_vol_correct'] + stats['high_vol_wrong']
    low_vol_total = stats['low_vol_correct'] + stats['low_vol_wrong']
    
    if high_vol_total > 0:
        print(f"  高波动：{stats['high_vol_correct']}/{high_vol_total} ({stats['high_vol_correct']/high_vol_total*100:.1f}%)")
    if low_vol_total > 0:
        print(f"  低波动：{stats['low_vol_correct']}/{low_vol_total} ({stats['low_vol_correct']/low_vol_total*100:.1f}%)")
    
    # 结论
    print("\n" + "="*80)
    print("💡 结论")
    print("="*80)
    
    if up_total > 0 and down_total > 0:
        up_acc = stats['uptrend_correct']/up_total*100
        down_acc = stats['downtrend_correct']/down_total*100
        if up_acc > down_acc + 10:
            print("⚠️  上涨趋势预测准确，下跌趋势判断差 - 需加强下跌信号")
        elif down_acc > up_acc + 10:
            print("⚠️  下跌趋势预测准确，上涨趋势判断差 - 需加强上涨信号")
    
    if high_vol_total > 0 and low_vol_total > 0:
        high_acc = stats['high_vol_correct']/high_vol_total*100
        low_acc = stats['low_vol_correct']/low_vol_total*100
        if high_acc < low_acc - 10:
            print("⚠️  高波动股票预测准确率显著较低 - 需加强波动率调整")
    
    print("\n✅ 分析完成！")

if __name__ == '__main__':
    analyze_failures()
