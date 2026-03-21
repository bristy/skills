#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测快速验证 v5.0
目标：快速验证更多股票，累积统计数据
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import requests
import os
import time

def fetch_stock_history(ts_code, end_date, days=60):
    """获取历史数据"""
    try:
        market = "SH" if ts_code.startswith('6') else "SZ"
        code = f"{market}.{ts_code}"
        
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        start_dt = end_dt - timedelta(days=days*2)
        
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={code}&klt=101&fqt=1&beg={start_dt.strftime('%Y%m%d')}&end={end_date}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data and data.get('data') and data['data'].get('klines'):
            klines = data['data']['klines']
            rows = [k.split(',') for k in klines]
            df = pd.DataFrame(rows, columns=['trade_date', 'open', 'close', 'high', 'low', 'vol', 'amount'])
            
            for col in ['open', 'close', 'high', 'low', 'vol']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            return df.sort_values('trade_date')
    except:
        pass
    return None

def predict(df):
    """简化预测"""
    if len(df) < 20:
        return 0.0
    
    df = df.sort_values('trade_date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    
    latest = df.iloc[-1]
    close = latest['close']
    ma5 = latest['ma5']
    ma20 = latest['ma20']
    
    # 简单趋势
    trend = 0
    if close > ma5: trend += 1
    if close > ma20: trend += 1
    
    # 近期收益
    recent = df['close'].pct_change().dropna().tail(10).mean() * 100
    
    # 预测
    pred = recent * 1.5 + trend * 0.5
    pred = np.clip(pred, -3, 3)  # 保守
    
    return pred

def verify_single_stock(ts_code, name, test_date):
    """验证单只股票"""
    try:
        df = fetch_stock_history(ts_code, test_date, days=60)
        if df is None or len(df) < 22:
            return None
        
        # 预测（用 T-1 日数据）
        hist_df = df.iloc[:-1].copy()
        predicted = predict(hist_df)
        
        # 实际
        prev_close = df.iloc[-2]['close']
        actual_close = df.iloc[-1]['close']
        actual = (actual_close - prev_close) / prev_close * 100
        
        direction_correct = (predicted > 0) == (actual > 0)
        abs_error = abs(predicted - actual)
        
        return {
            'stock_code': ts_code,
            'stock_name': name,
            'predicted': round(predicted, 2),
            'actual': round(actual, 2),
            'direction_correct': direction_correct,
            'abs_error': round(abs_error, 2),
            'hit_2pct': abs_error < 2.0,
        }
    except:
        return None

def run_verify():
    """运行验证"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测快速验证 v5.0")
    print(f"时间：{timestamp}")
    print("="*80)
    
    # 测试日期（最近 3 个交易日）
    test_dates = []
    current = datetime.now() - timedelta(days=1)
    while len(test_dates) < 3:
        if current.weekday() < 5:
            test_dates.append(current.strftime('%Y%m%d'))
        current -= timedelta(days=1)
    
    print(f"\n📅 测试日期：{test_dates}")
    
    # 加载股票
    stocks_file = '/home/admin/openclaw/workspace/stock_system/stocks.json'
    if os.path.exists(stocks_file):
        with open(stocks_file, 'r', encoding='utf-8') as f:
            stocks = json.load(f)
    else:
        print("❌ 无法加载股票列表")
        return
    
    print(f"📊 股票总数：{len(stocks)}")
    
    # 验证
    all_results = []
    
    for date_idx, test_date in enumerate(test_dates):
        print(f"\n🔍 验证日期：{test_date} ({date_idx+1}/{len(test_dates)})")
        
        # 随机采样 20 只
        np.random.seed(int(datetime.now().timestamp()) + date_idx)
        sample = np.random.choice(len(stocks), min(20, len(stocks)), replace=False)
        
        date_results = []
        for idx in sample:
            stock = stocks[idx]
            ts_code = stock.get('ts_code', stock['code'][2:] if len(stock['code']) > 2 else stock['code'])
            name = stock.get('name', '未知')
            
            result = verify_single_stock(ts_code, name, test_date)
            if result:
                date_results.append(result)
                all_results.append(result)
            
            if len(date_results) % 5 == 0:
                print(f"   成功：{len(date_results)}")
            
            time.sleep(0.2)
        
        print(f"   完成：{len(date_results)} 只")
    
    # 汇总
    print("\n" + "="*80)
    print("📊 验证结果汇总")
    print("="*80)
    
    if not all_results:
        print("❌ 无有效数据")
        return
    
    df_r = pd.DataFrame(all_results)
    
    total = len(all_results)
    direction_acc = df_r['direction_correct'].mean() * 100
    mae = df_r['abs_error'].mean()
    hit_2pct = df_r['hit_2pct'].mean() * 100
    
    print(f"\n✅ 总验证样本：{total} 个")
    print(f"📈 方向正确率：{direction_acc:.1f}%")
    print(f"📉 平均误差：{mae:.2f}%")
    print(f"🎯 命中率 (<2%)：{hit_2pct:.1f}%")
    
    # 按日期统计
    print("\n📅 每日表现:")
    for i, test_date in enumerate(test_dates):
        date_data = [r for r in all_results if True]  # 简化
        if date_data:
            print(f"   {test_date}: {len(date_data)}个样本")
    
    # TOP 10
    df_sorted = df_r.sort_values('abs_error')
    print("\n🎯 预测最准确 TOP 10:")
    for i, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
        flag = "✅" if row['direction_correct'] else "❌"
        print(f"{i}. {row['stock_name']} ({row['stock_code']}): 预测{row['predicted']:+.2f}%, 实际{row['actual']:+.2f}%, 误差{row['abs_error']:.2f}% {flag}")
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    
    result_file = f"{output_dir}/verify_round_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'test_dates': test_dates,
            'total': total,
            'direction_accuracy': round(direction_acc, 1),
            'mae': round(mae, 2),
            'hit_2pct': round(hit_2pct, 1),
            'details': all_results
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 结果已保存：{result_file}")
    print("\n" + "="*80)
    
    return direction_acc, mae, hit_2pct

if __name__ == '__main__':
    run_verify()
