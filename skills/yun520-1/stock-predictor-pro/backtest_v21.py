#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v21.0 回测验证 - 对比 v19.0（最佳版本）
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

def predict_v19(df):
    """v19.0（基准最佳）"""
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

def predict_v21(df):
    """v21.0（优化增强版）"""
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
    # v21: 趋势权重 1.5 → 1.8
    trend_score = 0
    if close > ma5: trend_score += 1.8
    if close > ma20: trend_score += 1.8
    if close > ma60: trend_score += 1.8
    vol_confirm = 0
    if vol_ratio > 1.5: vol_confirm = 2.0 if close > ma5 else -1.0
    elif vol_ratio < 0.7: vol_confirm = 0.5
    money_flow_confirm = 1.0 if df['money_flow'].iloc[-1] > df['money_flow'].rolling(5).mean().iloc[-1] else -0.5
    # v21: RSI 阈值 25/75
    rsi_score = 0
    if rsi < 25: rsi_score = 2.0
    elif rsi > 75: rsi_score = -2.0
    elif 45 < rsi < 60: rsi_score = 1.0
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    # v21: 核心公式优化
    base = ret * 2.2 + trend_score * 1.8 + mom * 0.35 + vol_confirm * 1.5 + money_flow_confirm * 1.0
    if abs(rsi_score) > 0: base += rsi_score * 1.0
    # v21: 均线偏离更敏感
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 6: base += 1.5
    elif dev > 4: base += 1.0
    elif dev > 2: base += 0.5
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    # v21: 波动率调整优化
    if vol > 80: base *= 0.75
    elif vol > 60: base *= 0.85
    dynamic_max = 6.0 if vol > 70 else (4.0 if vol < 25 else 5.0)
    return np.clip(base, -dynamic_max, dynamic_max)

def run_backtest():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"v21.0 回测验证 - 优化增强版")
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
    print(f"🔍 开始回测 (v19.0 vs v21.0)...\n")
    
    v19_results, v21_results = [], []
    
    for i, stock in enumerate(stocks):
        stock_df = df[df['stock_code'] == stock].sort_values('date')
        if len(stock_df) < 60: continue
        test_period_df = test_df[test_df['stock_code'] == stock].sort_values('date')
        for idx, row in test_period_df.iterrows():
            test_date = row['date']
            actual_close = row['close']
            prev_date = test_date - timedelta(days=1)
            hist_df = stock_df[stock_df['date'] <= prev_date]
            if len(hist_df) < 30: continue
            prev_close = hist_df.iloc[-1]['close']
            actual_change = (actual_close - prev_close) / prev_close * 100
            
            pred_v19 = predict_v19(hist_df)
            v19_results.append({'stock_code': stock, 'date': test_date, 'predicted': round(pred_v19, 2), 'actual': round(actual_change, 2), 'correct': (pred_v19 > 0) == (actual_change > 0), 'error': abs(pred_v19 - actual_change)})
            
            pred_v21 = predict_v21(hist_df)
            v21_results.append({'stock_code': stock, 'date': test_date, 'predicted': round(pred_v21, 2), 'actual': round(actual_change, 2), 'correct': (pred_v21 > 0) == (actual_change > 0), 'error': abs(pred_v21 - actual_change)})
        
        if (i+1) % 20 == 0:
            print(f"   进度：{i+1}/{len(stocks)}")
    
    df_v19 = pd.DataFrame(v19_results)
    df_v21 = pd.DataFrame(v21_results)
    
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
    
    s19 = summary(df_v19, "v19.0 (最佳)")
    s21 = summary(df_v21, "v21.0 (新版)")
    
    print("\n" + "="*80)
    print("🎯 改进对比")
    print("="*80)
    acc_improve = s21['accuracy'] - s19['accuracy']
    mae_improve = s19['mae'] - s21['mae']
    hit2_improve = s21['hit2'] - s19['hit2']
    
    print(f"\n方向正确率：{s19['accuracy']:.1f}% → {s21['accuracy']:.1f}% ({acc_improve:+.1f}%)")
    print(f"平均误差：{s19['mae']:.2f}% → {s21['mae']:.2f}% ({mae_improve:+.2f}%)")
    print(f"命中率 (<2%)：{s19['hit2']:.1f}% → {s21['hit2']:.1f}% ({hit2_improve:+.1f}%)")
    
    print("\n" + "="*80)
    print("✅ 评估")
    print("="*80)
    
    if acc_improve > 2:
        print(f"🎉 方向正确率大幅提升 {acc_improve:.1f}%！")
    elif acc_improve > 0:
        print(f"✅ 方向正确率提升 {acc_improve:.1f}%")
    elif acc_improve == 0:
        print(f"⚖️  方向正确率持平")
    else:
        print(f"⚠️  方向正确率下降 {abs(acc_improve):.1f}%")
    
    if mae_improve > 0.3:
        print(f"🎉 平均误差大幅降低 {mae_improve:.2f}%！")
    elif mae_improve > 0:
        print(f"✅ 平均误差降低 {mae_improve:.2f}%")
    elif mae_improve == 0:
        print(f"⚖️  平均误差持平")
    else:
        print(f"⚠️  平均误差增加 {abs(mae_improve):.2f}%")
    
    # 综合评估
    if acc_improve > 0 and mae_improve > 0:
        print(f"\n🏆 v21.0 全面超越 v19.0！推荐升级")
    elif acc_improve > 0 or mae_improve > 0:
        print(f"\n✅ v21.0 部分指标改善，可考虑升级")
    else:
        print(f"\n⚠️  v21.0 未超越 v19.0，建议保持 v19.0")
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    result_file = f"{output_dir}/backtest_v21_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({'timestamp': ts, 'v19': s19, 'v21': s21, 'improvement': {'accuracy': round(acc_improve, 1), 'mae': round(mae_improve, 2), 'hit2': round(hit2_improve, 1)}}, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n📁 结果已保存：{result_file}")
    print("\n✅ 回测完成！")
    
    return s19, s21

if __name__ == '__main__':
    run_backtest()
