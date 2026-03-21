#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v19.0 回测验证 - 引入成交量因子
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

def predict_v18(historical_df):
    """v18.0（对比基准）"""
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

def predict_v19(historical_df):
    """v19.0（成交量因子）"""
    if len(historical_df) < 30: return 0.0
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
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 成交量因子（ModelScope 数据集字段名是 'volume'）
    if 'volume' in df.columns:
        df['vol_ma5'] = df['volume'].rolling(5).mean()
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['volume'] / df['vol_ma20']
        # 资金流
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['money_flow'] = df['typical_price'] * df['volume']
        df['money_flow_ma5'] = df['money_flow'].rolling(5).mean()
    else:
        df['vol_ratio'] = 1.0
        df['money_flow'] = 0
        df['money_flow_ma5'] = 0
    
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi = latest['rsi']
    macd_hist = latest.get('macd_hist', 0)
    
    # 成交量确认
    vol_ratio = latest.get('vol_ratio', 1)
    vol_confirm = 0
    if vol_ratio > 1.5:
        vol_confirm = 1.5 if close > ma5 else -1.0
    elif vol_ratio < 0.7:
        vol_confirm = 0.5
    
    # 资金流确认
    money_flow_confirm = 1.0 if latest.get('money_flow', 0) > latest.get('money_flow_ma5', 0) else -0.5
    
    # 趋势
    trend_score = 0
    if close > ma5: trend_score += 1.5
    if close > ma20: trend_score += 1.5
    if close > ma60: trend_score += 1.5
    
    # RSI
    rsi_score = 0
    if rsi < 25: rsi_score = 1.5
    elif rsi > 75: rsi_score = -1.5
    elif 45 < rsi < 65: rsi_score = 0.5
    
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # v19 核心公式
    base = (ret * 2.0 + trend_score * 1.5 + mom * 0.3 + 
            vol_confirm * 1.5 + money_flow_confirm * 1.0)
    
    if abs(rsi_score) > 0: base += rsi_score * 1.0
    
    # MACD 柱状图
    if len(df) > 1:
        prev_macd_hist = df.iloc[-2].get('macd_hist', 0)
        if macd_hist > 0 and macd_hist > prev_macd_hist: base += 0.5
        elif macd_hist < 0 and macd_hist < prev_macd_hist: base -= 0.5
    
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 5: base += 0.5
    elif dev > 3: base += 0.3
    
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if vol > 70: base *= 0.8
    elif vol > 50: base *= 0.9
    
    # 动态上限
    dynamic_max = 6.0 if vol > 60 else (4.0 if vol < 30 else 5.0)
    return np.clip(base, -dynamic_max, dynamic_max)

def run_backtest():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"v19.0 回测验证（成交量因子）")
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
    print(f"🔍 开始回测 (v18.0 vs v19.0)...\n")
    
    v18_results, v19_results = [], []
    
    for i, stock in enumerate(stocks):
        stock_df = df[df['stock_code'] == stock].sort_values('date')
        if len(stock_df) < 40: continue
        test_period_df = test_df[test_df['stock_code'] == stock].sort_values('date')
        for idx, row in test_period_df.iterrows():
            test_date = row['date']
            actual_close = row['close']
            prev_date = test_date - timedelta(days=1)
            hist_df = stock_df[stock_df['date'] <= prev_date]
            if len(hist_df) < 30: continue
            prev_close = hist_df.iloc[-1]['close']
            actual_change = (actual_close - prev_close) / prev_close * 100
            
            pred_v18 = predict_v18(hist_df)
            v18_results.append({'stock_code': stock, 'date': test_date, 'predicted': round(pred_v18, 2), 'actual': round(actual_change, 2), 'correct': (pred_v18 > 0) == (actual_change > 0), 'error': abs(pred_v18 - actual_change)})
            
            pred_v19 = predict_v19(hist_df)
            v19_results.append({'stock_code': stock, 'date': test_date, 'predicted': round(pred_v19, 2), 'actual': round(actual_change, 2), 'correct': (pred_v19 > 0) == (actual_change > 0), 'error': abs(pred_v19 - actual_change)})
        
        if (i+1) % 20 == 0:
            print(f"   进度：{i+1}/{len(stocks)}")
    
    df_v18 = pd.DataFrame(v18_results)
    df_v19 = pd.DataFrame(v19_results)
    
    print("\n" + "="*80)
    print("📊 回测结果对比")
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
    
    s18 = summary(df_v18, "v18.0")
    s19 = summary(df_v19, "v19.0")
    
    print("\n" + "="*80)
    print("🎯 改进对比")
    print("="*80)
    acc_improve = s19['accuracy'] - s18['accuracy']
    mae_improve = s18['mae'] - s19['mae']
    hit2_improve = s19['hit2'] - s18['hit2']
    
    print(f"\n方向正确率：{s18['accuracy']:.1f}% → {s19['accuracy']:.1f}% ({acc_improve:+.1f}%)")
    print(f"平均误差：{s18['mae']:.2f}% → {s19['mae']:.2f}% ({mae_improve:+.2f}%)")
    print(f"命中率 (<2%)：{s18['hit2']:.1f}% → {s19['hit2']:.1f}% ({hit2_improve:+.1f}%)")
    
    print("\n" + "="*80)
    print("✅ 评估")
    print("="*80)
    
    if acc_improve > 5:
        print(f"🎉 方向正确率大幅提升 {acc_improve:.1f}%！")
    elif acc_improve > 0:
        print(f"✅ 方向正确率提升 {acc_improve:.1f}%")
    else:
        print(f"⚠️  方向正确率下降 {abs(acc_improve):.1f}%")
    
    if mae_improve > 0.5:
        print(f"🎉 平均误差大幅降低 {mae_improve:.2f}%！")
    elif mae_improve > 0:
        print(f"✅ 平均误差降低 {mae_improve:.2f}%")
    else:
        print(f"⚠️  平均误差增加 {abs(mae_improve):.2f}%")
    
    if s19['accuracy'] >= 52:
        print(f"\n🎯 达到目标！方向正确率 >= 52%")
    elif s19['accuracy'] >= 50:
        print(f"\n✅ 接近目标！方向正确率 >= 50%")
    else:
        print(f"\n⚠️  仍需改进，目标 52%+")
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    result_file = f"{output_dir}/backtest_v19_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({'timestamp': ts, 'v18': s18, 'v19': s19, 'improvement': {'accuracy': round(acc_improve, 1), 'mae': round(mae_improve, 2), 'hit2': round(hit2_improve, 1)}}, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n📁 结果已保存：{result_file}")
    print("\n✅ 回测完成！")
    
    return s18, s19

if __name__ == '__main__':
    run_backtest()
