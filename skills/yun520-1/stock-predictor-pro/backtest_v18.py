#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v18.0 大规模回测验证 - 对比 v16.0/v17.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

CONFIG = {
    'test_days': 30,
    'sample_stocks': 100,
    'data_file': '/home/admin/openclaw/workspace/chinese-stock-dataset/chinese-stock-dataset.csv'
}

def load_data():
    print("📊 加载数据集...")
    df = pd.read_csv(CONFIG['data_file'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(['stock_code', 'date'])
    print(f"   记录数：{len(df):,} 条 | 股票数：{df['stock_code'].nunique():,} 只")
    return df

def predict_v16(historical_df):
    """v16.0（基准）"""
    if len(historical_df) < 20: return 0.0
    df = historical_df.copy().sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = (100 - (100 / (1 + rs))).fillna(50).clip(0, 100)
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi = latest['rsi']
    macd = latest.get('macd', 0)
    trend_score = 0
    if close > ma5: trend_score += 1.5
    if close > ma20: trend_score += 1.5
    if close > ma60: trend_score += 1.5
    if 55 < rsi < 75: trend_score += 1.5
    if macd > 0: trend_score += 1.0
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    base = ret * 2.5 + trend_score * 1.2 + mom * 0.6
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 3: base += 2.0
    elif dev > 2: base += 1.5
    elif dev > 1: base += 1.0
    return np.clip(base, -8.0, 8.0)

def predict_v17(historical_df):
    """v17.0"""
    if len(historical_df) < 20: return 0.0
    df = historical_df.copy().sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = (100 - (100 / (1 + rs))).fillna(50).clip(0, 100)
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi = latest['rsi']
    trend_score = 0
    if close > ma5: trend_score += 2.0
    if close > ma20: trend_score += 2.0
    if close > ma60: trend_score += 2.0
    rsi_score = 0
    if 50 < rsi < 70: rsi_score = 2.0
    elif 30 < rsi <= 50: rsi_score = 1.0
    elif rsi <= 30: rsi_score = -1.0
    elif rsi >= 70: rsi_score = -1.0
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    base = ret * 2.0 + trend_score * 2.0 + mom * 0.3 + rsi_score * 1.5
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 5: base += 1.0
    elif dev > 3: base += 0.5
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if vol > 60: base *= 0.6
    elif vol > 40: base *= 0.8
    return np.clip(base, -5.0, 5.0)

def predict_v18(historical_df):
    """v18.0（参数微调）"""
    if len(historical_df) < 20: return 0.0
    df = historical_df.copy().sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = (100 - (100 / (1 + rs))).fillna(50).clip(0, 100)
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi = latest['rsi']
    macd = latest.get('macd', 0)
    # v18: 降低趋势权重
    trend_score = 0
    if close > ma5: trend_score += 1.5
    if close > ma20: trend_score += 1.5
    if close > ma60: trend_score += 1.5
    # v18: 仅极端 RSI
    rsi_score = 0
    if rsi < 25: rsi_score = 1.5
    elif rsi > 75: rsi_score = -1.5
    elif 45 < rsi < 65: rsi_score = 0.5
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    # v18 核心公式
    base = ret * 2.0 + trend_score * 1.5 + mom * 0.3
    if abs(rsi_score) > 0:
        base += rsi_score * 1.0
    # MACD 加分
    if macd > 0:
        base += 0.5
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 5: base += 0.5
    elif dev > 3: base += 0.3
    # v18: 降低波动率收缩
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if vol > 70:
        base *= 0.8
    elif vol > 50:
        base *= 0.9
    return np.clip(base, -5.0, 5.0)

def run_backtest():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"v18.0 大规模回测验证")
    print(f"时间：{ts}")
    print("="*80)
    
    df = load_data()
    max_date = df['date'].max()
    min_date = max_date - timedelta(days=CONFIG['test_days'])
    test_df = df[(df['date'] >= min_date) & (df['date'] <= max_date)]
    print(f"\n📅 测试期间：{min_date.date()} - {max_date.date()} ({CONFIG['test_days']}天)")
    
    stocks = test_df['stock_code'].unique()
    if len(stocks) > CONFIG['sample_stocks']:
        np.random.seed(42)
        stocks = np.random.choice(stocks, CONFIG['sample_stocks'], replace=False)
    print(f"   股票：{len(stocks)} 只\n")
    print(f"🔍 开始回测 (v16.0 / v17.0 / v18.0)...\n")
    
    v16_results, v17_results, v18_results = [], [], []
    
    for i, stock in enumerate(stocks):
        stock_df = df[df['stock_code'] == stock].sort_values('date')
        if len(stock_df) < 30: continue
        test_period_df = test_df[test_df['stock_code'] == stock].sort_values('date')
        for idx, row in test_period_df.iterrows():
            test_date = row['date']
            actual_close = row['close']
            prev_date = test_date - timedelta(days=1)
            hist_df = stock_df[stock_df['date'] <= prev_date]
            if len(hist_df) < 20: continue
            prev_close = hist_df.iloc[-1]['close']
            actual_change = (actual_close - prev_close) / prev_close * 100
            
            pred_v16 = predict_v16(hist_df)
            v16_results.append({'stock_code': stock, 'date': test_date, 'predicted': round(pred_v16, 2), 'actual': round(actual_change, 2), 'correct': (pred_v16 > 0) == (actual_change > 0), 'error': abs(pred_v16 - actual_change)})
            
            pred_v17 = predict_v17(hist_df)
            v17_results.append({'stock_code': stock, 'date': test_date, 'predicted': round(pred_v17, 2), 'actual': round(actual_change, 2), 'correct': (pred_v17 > 0) == (actual_change > 0), 'error': abs(pred_v17 - actual_change)})
            
            pred_v18 = predict_v18(hist_df)
            v18_results.append({'stock_code': stock, 'date': test_date, 'predicted': round(pred_v18, 2), 'actual': round(actual_change, 2), 'correct': (pred_v18 > 0) == (actual_change > 0), 'error': abs(pred_v18 - actual_change)})
        
        if (i+1) % 20 == 0:
            print(f"   进度：{i+1}/{len(stocks)}")
    
    df_v16 = pd.DataFrame(v16_results)
    df_v17 = pd.DataFrame(v17_results)
    df_v18 = pd.DataFrame(v18_results)
    
    print("\n" + "="*80)
    print("📊 三版本对比")
    print("="*80)
    
    def summary(df, version):
        total = len(df)
        correct = len(df[df['correct']])
        acc = correct/total*100
        mae = df['error'].mean()
        hit2 = len(df[df['error']<2.0])/total*100
        hit1 = len(df[df['error']<1.0])/total*100
        print(f"\n{version}:")
        print(f"   样本：{total} | 正确率：{acc:.1f}% | 误差：{mae:.2f}% | 命中<2%：{hit2:.1f}% | 命中<1%：{hit1:.1f}%")
        return {'total': total, 'correct': correct, 'accuracy': acc, 'mae': mae, 'hit2': hit2, 'hit1': hit1}
    
    s16 = summary(df_v16, "v16.0")
    s17 = summary(df_v17, "v17.0")
    s18 = summary(df_v18, "v18.0")
    
    print("\n" + "="*80)
    print("🎯 改进对比")
    print("="*80)
    print(f"\nvs v16.0:")
    print(f"   v17.0: 正确率 {s16['accuracy']:.1f}%→{s17['accuracy']:.1f}% ({s17['accuracy']-s16['accuracy']:+.1f}%) | 误差 {s16['mae']:.2f}%→{s17['mae']:.2f}% ({s16['mae']-s17['mae']:+.2f}%)")
    print(f"   v18.0: 正确率 {s16['accuracy']:.1f}%→{s18['accuracy']:.1f}% ({s18['accuracy']-s16['accuracy']:+.1f}%) | 误差 {s16['mae']:.2f}%→{s18['mae']:.2f}% ({s16['mae']-s18['mae']:+.2f}%)")
    
    print(f"\nvs v17.0:")
    print(f"   v18.0: 正确率 {s17['accuracy']:.1f}%→{s18['accuracy']:.1f}% ({s18['accuracy']-s17['accuracy']:+.1f}%) | 误差 {s17['mae']:.2f}%→{s18['mae']:.2f}% ({s17['mae']-s18['mae']:+.2f}%)")
    
    print("\n" + "="*80)
    print("✅ 最佳版本评估")
    print("="*80)
    
    best_acc = max(s16['accuracy'], s17['accuracy'], s18['accuracy'])
    best_mae = min(s16['mae'], s17['mae'], s18['mae'])
    
    if s18['accuracy'] == best_acc and s18['mae'] == best_mae:
        print(f"🎉 v18.0 最佳！正确率={best_acc:.1f}%, 误差={best_mae:.2f}%")
    elif s17['accuracy'] == best_acc and s17['mae'] == best_mae:
        print(f"🏆 v17.0 最佳！正确率={best_acc:.1f}%, 误差={best_mae:.2f}%")
    elif s16['accuracy'] == best_acc and s16['mae'] == best_mae:
        print(f"📌 v16.0 最佳！正确率={best_acc:.1f}%, 误差={best_mae:.2f}%")
    else:
        print(f"⚖️  需要权衡：v18.0 正确率={s18['accuracy']:.1f}% 误差={s18['mae']:.2f}%")
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    result_file = f"{output_dir}/backtest_v18_final_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({'timestamp': ts, 'v16': s16, 'v17': s17, 'v18': s18, 'best': {'accuracy': best_acc, 'mae': best_mae}}, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n📁 结果已保存：{result_file}")
    print("\n✅ 回测完成！")
    
    return s16, s17, s18

if __name__ == '__main__':
    run_backtest()
