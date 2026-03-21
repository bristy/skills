#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5 日趋势策略回测验证
验证：筛选出的股票是否真的在 5 天内上涨 5% 以上
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

CONFIG = {
    'test_days': 60,
    'sample_stocks': 100,
    'target_gain': 5.0,
    'hold_days': 5,
    'min_predicted': 8.0,  # v2: 提高预测门槛从 5% 到 8%
    'min_confidence': 60,  # v2: 提高置信度门槛从 50 到 60
    'data_file': '/home/admin/openclaw/workspace/chinese-stock-dataset/chinese-stock-dataset.csv'
}

def load_data():
    print("📊 加载数据集...")
    df = pd.read_csv(CONFIG['data_file'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(['stock_code', 'date'])
    print(f"   记录数：{len(df):,} 条 | 股票数：{df['stock_code'].nunique():,} 只")
    return df

def predict_5day_gain(historical_df):
    """5 日涨幅预测（与实盘一致）"""
    if len(historical_df) < 30:
        return None
    
    df = historical_df.copy().sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    latest = df.iloc[-1]
    close = latest['close']
    ma5, ma10, ma20, ma60 = latest['ma5'], latest['ma10'], latest['ma20'], latest['ma60']
    
    trend_score = 0
    if ma5 > ma10: trend_score += 1
    if ma10 > ma20: trend_score += 1
    if ma20 > ma60: trend_score += 1
    if close > ma5: trend_score += 1
    if close > ma20: trend_score += 1
    
    ret_5d = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    ret_10d = df['close'].pct_change(10).iloc[-1] * 100 if len(df) > 10 else 0
    momentum_accel = ret_5d - ret_10d if ret_10d != 0 else ret_5d
    
    if 'volume' in df.columns:
        vol_ma5 = df['volume'].rolling(5).mean().iloc[-1]
        vol_ma20 = df['volume'].rolling(20).mean().iloc[-1]
        vol_ratio = vol_ma5 / vol_ma20 if vol_ma20 > 0 else 1
        df['money_flow'] = (df['high'] + df['low'] + df['close']) / 3 * df['volume']
        money_flow_5d = df['money_flow'].iloc[-5:].sum()
        money_flow_prev = df['money_flow'].iloc[-10:-5].sum()
        money_flow_change = (money_flow_5d - money_flow_prev) / money_flow_prev if money_flow_prev > 0 else 0
    else:
        vol_ratio = 1.0
        money_flow_change = 0
    
    high_20d = df['high'].rolling(20).max().iloc[-2]
    breakout = (close - high_20d) / high_20d * 100 if high_20d > 0 else 0
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi_series = 100 - (100 / (1 + gain/loss))
    rsi = rsi_series.iloc[-1] if len(rsi_series) > 0 else 50
    if pd.isna(rsi): rsi = 50
    
    base_pred = ret_5d * 0.5 + ret_10d * 0.3
    trend_bonus = trend_score * 0.8
    momentum_bonus = momentum_accel * 0.5
    volume_bonus = (vol_ratio - 1) * 2 if vol_ratio > 1 else 0
    breakout_bonus = breakout * 0.5 if breakout > 0 else 0
    flow_bonus = money_flow_change * 3 if money_flow_change > 0 else 0
    rsi_adjust = -2 if rsi > 75 else (2 if rsi < 30 else 0)
    
    pred_5d = base_pred + trend_bonus + momentum_bonus + volume_bonus + breakout_bonus + flow_bonus + rsi_adjust
    
    confidence = 0
    if trend_score >= 4: confidence += 20
    if vol_ratio > 1.5: confidence += 20
    if breakout > 0: confidence += 15
    if money_flow_change > 0.2: confidence += 15
    if momentum_accel > 0: confidence += 10
    if rsi < 70: confidence += 20
    
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if vol > 60:
        pred_5d *= 0.8
        confidence *= 0.8
    
    return {'predicted': pred_5d, 'confidence': confidence}

def run_backtest():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"5 日趋势策略回测验证")
    print(f"时间：{ts}")
    print(f"目标：验证筛选出的股票 5 天内是否上涨 5% 以上")
    print("="*80)
    
    df = load_data()
    max_date = df['date'].max()
    min_date = max_date - timedelta(days=CONFIG['test_days'])
    
    print(f"\n📅 回测期间：{min_date.date()} - {max_date.date()} ({CONFIG['test_days']}天)")
    print(f"🎯 目标涨幅：{CONFIG['target_gain']}%+")
    print(f"📆 持有期：{CONFIG['hold_days']}天\n")
    
    stocks = df['stock_code'].unique()
    if len(stocks) > CONFIG['sample_stocks']:
        np.random.seed(42)
        stocks = np.random.choice(stocks, CONFIG['sample_stocks'], replace=False)
    print(f"   样本股票：{len(stocks)} 只\n")
    
    print(f"🔍 开始回测...\n")
    
    signals = []  # 所有信号
    actual_gains = []  # 实际涨幅
    
    for i, stock in enumerate(stocks):
        stock_df = df[df['stock_code'] == stock].sort_values('date')
        if len(stock_df) < 50:
            continue
        
        # 在回测期间内，每天检查是否发出买入信号
        test_period = stock_df[(stock_df['date'] >= min_date) & (stock_df['date'] <= max_date)]
        
        for idx, row in test_period.iterrows():
            signal_date = row['date']
            signal_idx = stock_df.index.get_loc(idx)
            
            # 确保有足够历史数据和未来数据
            if signal_idx < 30 or signal_idx >= len(stock_df) - CONFIG['hold_days']:
                continue
            
            # 用 signal_date 之前的数据做预测
            hist_df = stock_df.iloc[:signal_idx]
            pred = predict_5day_gain(hist_df)
            
            if pred is None:
                continue
            
            # v2: 提高门槛 - 预测>=8% 且置信度>=60
            if pred['predicted'] >= CONFIG['min_predicted'] and pred['confidence'] >= CONFIG['min_confidence']:
                # 计算实际 5 日后涨幅
                future_close = stock_df.iloc[signal_idx + CONFIG['hold_days']]['close']
                current_close = row['close']
                actual_gain = (future_close - current_close) / current_close * 100
                
                signals.append({
                    'stock_code': stock,
                    'signal_date': signal_date,
                    'predicted': round(pred['predicted'], 2),
                    'confidence': round(pred['confidence'], 1),
                    'actual_5d_gain': round(actual_gain, 2),
                    'success': actual_gain >= CONFIG['target_gain']
                })
        
        if (i+1) % 20 == 0:
            print(f"   进度：{i+1}/{len(stocks)}")
    
    if not signals:
        print("\n❌ 未找到有效信号")
        return
    
    df_signals = pd.DataFrame(signals)
    
    print("\n" + "="*80)
    print("📊 回测结果")
    print("="*80)
    
    total_signals = len(df_signals)
    success_count = len(df_signals[df_signals['success']])
    success_rate = success_count / total_signals * 100
    
    avg_actual_gain = df_signals['actual_5d_gain'].mean()
    avg_predicted = df_signals['predicted'].mean()
    
    # 按置信度分组
    high_conf = df_signals[df_signals['confidence'] >= 70]
    mid_conf = df_signals[(df_signals['confidence'] >= 50) & (df_signals['confidence'] < 70)]
    
    print(f"\n总信号数：{total_signals}")
    print(f"成功次数：{success_count}/{total_signals} ({success_rate:.1f}%)")
    print(f"平均预测涨幅：{avg_predicted:.2f}%")
    print(f"平均实际涨幅：{avg_actual_gain:.2f}%")
    
    print(f"\n按置信度分组:")
    if len(high_conf) > 0:
        high_success = len(high_conf[high_conf['success']]) / len(high_conf) * 100
        print(f"   高置信度 (>=70%): {len(high_conf)} 个信号，成功率 {high_success:.1f}%")
    if len(mid_conf) > 0:
        mid_success = len(mid_conf[mid_conf['success']]) / len(mid_conf) * 100
        print(f"   中置信度 (50-70%): {len(mid_conf)} 个信号，成功率 {mid_success:.1f}%")
    
    # 按股票分组
    print(f"\n个股表现 TOP 10:")
    stock_stats = df_signals.groupby('stock_code').agg({
        'success': 'mean',
        'actual_5d_gain': 'mean',
        'signal_date': 'count'
    }).rename(columns={'signal_date': 'count'}).round(2)
    
    top_stocks = stock_stats.sort_values('success', ascending=False).head(10)
    for code, row in top_stocks.iterrows():
        print(f"   {code}: 成功率={row['success']*100:.0f}%, 平均涨幅={row['actual_5d_gain']:.1f}%, 信号={int(row['count'])}")
    
    # 评估
    print("\n" + "="*80)
    print("✅ 策略评估")
    print("="*80)
    
    if success_rate >= 40:
        print(f"🎉 成功率 {success_rate:.1f}% - 优秀！策略可用")
    elif success_rate >= 30:
        print(f"✅ 成功率 {success_rate:.1f}% - 良好，可以使用")
    elif success_rate >= 20:
        print(f"⚠️  成功率 {success_rate:.1f}% - 一般，需要优化")
    else:
        print(f"❌ 成功率 {success_rate:.1f}% - 较差，需要大幅改进")
    
    if avg_actual_gain >= CONFIG['target_gain']:
        print(f"🎯 平均实际涨幅 {avg_actual_gain:.2f}% - 达到目标 ({CONFIG['target_gain']}%)")
    else:
        print(f"⚠️  平均实际涨幅 {avg_actual_gain:.2f}% - 未达目标 ({CONFIG['target_gain']}%)")
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    result_file = f"{output_dir}/backtest_5day_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': ts,
            'config': CONFIG,
            'summary': {
                'total_signals': total_signals,
                'success_count': success_count,
                'success_rate': round(success_rate, 1),
                'avg_predicted': round(avg_predicted, 2),
                'avg_actual_gain': round(avg_actual_gain, 2)
            },
            'by_confidence': {
                'high': len(high_conf),
                'mid': len(mid_conf)
            }
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 结果已保存：{result_file}")
    print("\n✅ 回测完成！")
    
    return success_rate, avg_actual_gain

if __name__ == '__main__':
    run_backtest()
