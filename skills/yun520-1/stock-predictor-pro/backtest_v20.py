#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v20.0 大规模回测验证 - 综合强化版
对比：v16.0 → v17.0 → v18.0 → v19.0 → v20.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

CONFIG = {'test_days': 30, 'sample_stocks': 100, 'data_file': '/home/admin/openclaw/workspace/chinese-stock-dataset/chinese-stock-dataset.csv'}

def load_data():
    print("📊 加载数据集...")
    df = pd.read_csv(CONFIG['data_file'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(['stock_code', 'date'])
    print(f"   记录数：{len(df):,} 条 | 股票数：{df['stock_code'].nunique():,} 只")
    return df

def predict_v16(df):
    if len(df) < 20: return 0.0
    df = df.copy().sort_values('date').reset_index(drop=True)
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
    if close > ma5: trend_score += 1.5
    if close > ma20: trend_score += 1.5
    if close > ma60: trend_score += 1.5
    if 55 < rsi < 75: trend_score += 1.5
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    base = ret * 2.5 + trend_score * 1.2 + mom * 0.6
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 3: base += 2.0
    elif dev > 2: base += 1.5
    elif dev > 1: base += 1.0
    return np.clip(base, -8.0, 8.0)

def predict_v18(df):
    if len(df) < 20: return 0.0
    df = df.copy().sort_values('date').reset_index(drop=True)
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
    rsi_score = 0
    if rsi < 25: rsi_score = 1.5
    elif rsi > 75: rsi_score = -1.5
    elif 45 < rsi < 65: rsi_score = 0.5
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    base = ret * 2.0 + trend_score * 1.5 + mom * 0.3
    if abs(rsi_score) > 0: base += rsi_score * 1.0
    if macd > 0: base += 0.5
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 5: base += 0.5
    elif dev > 3: base += 0.3
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if vol > 70: base *= 0.8
    elif vol > 50: base *= 0.9
    return np.clip(base, -5.0, 5.0)

def predict_v19(df):
    if len(df) < 30: return 0.0
    df = df.copy().sort_values('date').reset_index(drop=True)
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
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    if 'volume' in df.columns:
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        vol_ratio = df['volume'].iloc[-1] / df['vol_ma20'].iloc[-1] if df['vol_ma20'].iloc[-1] > 0 else 1
        df['money_flow'] = (df['high'] + df['low'] + df['close']) / 3 * df['volume']
    else:
        vol_ratio = 1.0
        df['money_flow'] = 0
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi = latest['rsi']
    vol_confirm = 0
    if vol_ratio > 1.5: vol_confirm = 1.5 if close > ma5 else -1.0
    elif vol_ratio < 0.7: vol_confirm = 0.5
    money_flow_confirm = 1.0 if df['money_flow'].iloc[-1] > df['money_flow'].rolling(5).mean().iloc[-1] else -0.5
    trend_score = 0
    if close > ma5: trend_score += 1.5
    if close > ma20: trend_score += 1.5
    if close > ma60: trend_score += 1.5
    rsi_score = 0
    if rsi < 25: rsi_score = 1.5
    elif rsi > 75: rsi_score = -1.5
    elif 45 < rsi < 65: rsi_score = 0.5
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    base = ret * 2.0 + trend_score * 1.5 + mom * 0.3 + vol_confirm * 1.5 + money_flow_confirm * 1.0
    if abs(rsi_score) > 0: base += rsi_score * 1.0
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 5: base += 0.5
    elif dev > 3: base += 0.3
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if vol > 70: base *= 0.8
    elif vol > 50: base *= 0.9
    dynamic_max = 6.0 if vol > 60 else (4.0 if vol < 30 else 5.0)
    return np.clip(base, -dynamic_max, dynamic_max)

def predict_v20(df):
    """v20.0 综合强化版"""
    if len(df) < 60: return 0.0
    df = df.copy().sort_values('date').reset_index(drop=True)
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
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 成交量
    if 'volume' in df.columns:
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        vol_ratio = df['volume'].iloc[-1] / df['vol_ma20'].iloc[-1] if df['vol_ma20'].iloc[-1] > 0 else 1
        df['money_flow'] = (df['high'] + df['low'] + df['close']) / 3 * df['volume']
    else:
        vol_ratio = 1.0
        df['money_flow'] = 0
    
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi = latest['rsi']
    
    # v20.0 核心因子
    # 1. 趋势（权重提升到 2.0）
    trend_score = 0
    if close > ma5: trend_score += 2.0
    if close > ma20: trend_score += 2.0
    if close > ma60: trend_score += 2.0
    
    # 2. 成交量
    vol_confirm = 0
    if vol_ratio > 1.5: vol_confirm = 2.0 if close > ma5 else -1.0
    elif vol_ratio < 0.7: vol_confirm = 0.5
    
    # 3. RSI（优化阈值 30/70）
    rsi_score = 0
    if rsi < 30: rsi_score = 2.0
    elif rsi > 70: rsi_score = -2.0
    elif 45 < rsi < 60: rsi_score = 1.0
    
    # 4. 动量
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # 5. 历史模式匹配（简化版）
    pattern_signal = 0
    if len(df) >= 80:
        recent_trend = df['close'].iloc[-20:].iloc[-1] / df['close'].iloc[-20:].iloc[0] - 1
        for i in range(40, len(df) - 20):
            hist_trend = df['close'].iloc[i:i+20].iloc[-1] / df['close'].iloc[i:i+20].iloc[0] - 1
            if abs(recent_trend - hist_trend) < 0.03:
                next_5 = df['close'].iloc[i+20:i+25]
                if len(next_5) > 0:
                    pattern_signal = (next_5.iloc[-1] / next_5.iloc[0] - 1) * 100
                    break
    
    # 6. MACD
    macd_confirm = 0.5 if df['macd_hist'].iloc[-1] > 0 else -0.5
    
    # 7. 资金流
    money_flow_confirm = 1.0 if df['money_flow'].iloc[-1] > df['money_flow'].rolling(5).mean().iloc[-1] else -0.5
    
    # v20.0 综合公式
    base = (ret * 2.5 + 
            trend_score * 2.0 + 
            mom * 0.4 +
            vol_confirm * 1.5 +
            money_flow_confirm * 1.0 +
            rsi_score * 1.0 +
            pattern_signal * 2.0 / 10 +
            macd_confirm)
    
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 5: base += 1.0
    elif dev > 3: base += 0.5
    
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if vol > 70: base *= 0.85
    elif vol > 50: base *= 0.95
    
    dynamic_max = 6.0 if vol > 60 else (4.0 if vol < 30 else 5.0)
    return np.clip(base, -dynamic_max, dynamic_max)

def run_backtest():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"v20.0 大规模回测验证 - 综合强化版")
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
    print(f"🔍 开始回测 (v16.0 / v18.0 / v19.0 / v20.0)...\n")
    
    results = {'v16': [], 'v18': [], 'v19': [], 'v20': []}
    
    for i, stock in enumerate(stocks):
        stock_df = df[df['stock_code'] == stock].sort_values('date')
        if len(stock_df) < 80: continue
        test_period_df = test_df[test_df['stock_code'] == stock].sort_values('date')
        for idx, row in test_period_df.iterrows():
            test_date = row['date']
            actual_close = row['close']
            prev_date = test_date - timedelta(days=1)
            hist_df = stock_df[stock_df['date'] <= prev_date]
            if len(hist_df) < 60: continue
            prev_close = hist_df.iloc[-1]['close']
            actual_change = (actual_close - prev_close) / prev_close * 100
            
            for ver, predict_fn in [('v16', predict_v16), ('v18', predict_v18), ('v19', predict_v19), ('v20', predict_v20)]:
                pred = predict_fn(hist_df)
                results[ver].append({
                    'stock_code': stock, 'date': test_date,
                    'predicted': round(pred, 2), 'actual': round(actual_change, 2),
                    'correct': (pred > 0) == (actual_change > 0),
                    'error': abs(pred - actual_change)
                })
        
        if (i+1) % 20 == 0:
            print(f"   进度：{i+1}/{len(stocks)}")
    
    print("\n" + "="*80)
    print("📊 四版本对比")
    print("="*80)
    
    stats = {}
    for ver in ['v16', 'v18', 'v19', 'v20']:
        df_ver = pd.DataFrame(results[ver])
        total = len(df_ver)
        correct = len(df_ver[df_ver['correct']])
        acc = correct/total*100
        mae = df_ver['error'].mean()
        hit2 = len(df_ver[df_ver['error']<2.0])/total*100
        hit1 = len(df_ver[df_ver['error']<1.0])/total*100
        stats[ver] = {'total': total, 'correct': correct, 'accuracy': acc, 'mae': mae, 'hit2': hit2, 'hit1': hit1}
        print(f"\n{ver}:")
        print(f"   样本：{total} | 正确率：{acc:.1f}% | 误差：{mae:.2f}% | 命中<2%：{hit2:.1f}% | 命中<1%：{hit1:.1f}%")
    
    print("\n" + "="*80)
    print("🎯 进化历程")
    print("="*80)
    
    print(f"\n方向正确率:")
    for ver in ['v16', 'v18', 'v19', 'v20']:
        bar = '█' * int(stats[ver]['accuracy'] / 2)
        print(f"   {ver}: {bar} {stats[ver]['accuracy']:.1f}%")
    
    print(f"\n平均误差:")
    for ver in ['v16', 'v18', 'v19', 'v20']:
        bar = '█' * int(stats[ver]['mae'])
        print(f"   {ver}: {bar} {stats[ver]['mae']:.2f}%")
    
    print("\n" + "="*80)
    print("✅ 最佳版本")
    print("="*80)
    
    best_acc = max(stats.values(), key=lambda x: x['accuracy'])
    best_mae = min(stats.values(), key=lambda x: x['mae'])
    
    for ver in ['v16', 'v18', 'v19', 'v20']:
        if stats[ver] == best_acc:
            print(f"🏆 方向正确率最佳：{ver} ({best_acc['accuracy']:.1f}%)")
        if stats[ver] == best_mae:
            print(f"🎯 平均误差最佳：{ver} ({best_mae['mae']:.2f}%)")
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    result_file = f"{output_dir}/backtest_v20_final_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({'timestamp': ts, 'stats': stats, 'best': {'accuracy': best_acc, 'mae': best_mae}}, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n📁 结果已保存：{result_file}")
    print("\n✅ 回测完成！")
    
    return stats

if __name__ == '__main__':
    run_backtest()
