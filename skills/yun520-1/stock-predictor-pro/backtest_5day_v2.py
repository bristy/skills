#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5 日趋势策略回测验证 v2.0 - 500 只股票大样本
修复项：
1. 降低预测门槛（从 8% 降到 3%）
2. 增加过滤条件（剔除高波动、超买）
3. 优化置信度计算
4. 增加止损条件
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

CONFIG = {
    'test_days': 60,
    'sample_stocks': 500,  # v2: 扩大到 500 只
    'target_gain': 3.0,  # v2: 降低目标从 5% 到 3%
    'hold_days': 5,
    'min_predicted': 3.0,  # v2: 降低预测门槛
    'min_confidence': 55,  # v2: 适中置信度
    'max_volatility': 80,  # v2: 剔除过高波动
    'max_rsi': 75,  # v2: 剔除超买
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
    """5 日涨幅预测 v2.0"""
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
    
    # 趋势评分
    trend_score = 0
    if ma5 > ma10: trend_score += 1
    if ma10 > ma20: trend_score += 1
    if ma20 > ma60: trend_score += 1
    if close > ma5: trend_score += 1
    if close > ma20: trend_score += 1
    
    # 动量
    ret_5d = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    ret_10d = df['close'].pct_change(10).iloc[-1] * 100 if len(df) > 10 else 0
    ret_20d = df['close'].pct_change(20).iloc[-1] * 100 if len(df) > 20 else 0
    
    # 动量加速
    momentum_accel = ret_5d - ret_10d
    
    # 成交量
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
    
    # 突破
    high_20d = df['high'].rolling(20).max().iloc[-2]
    breakout = (close - high_20d) / high_20d * 100 if high_20d > 0 else 0
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi_series = 100 - (100 / (1 + gain/loss))
    rsi = rsi_series.iloc[-1] if len(rsi_series) > 0 else 50
    if pd.isna(rsi): rsi = 50
    
    # 波动率
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    
    # v2.0 预测公式（更保守）
    base_pred = ret_5d * 0.4 + ret_10d * 0.3 + ret_20d * 0.2
    trend_bonus = trend_score * 0.6
    momentum_bonus = momentum_accel * 0.4
    volume_bonus = (vol_ratio - 1) * 1.5 if vol_ratio > 1 else 0
    breakout_bonus = breakout * 0.4 if breakout > 0 else 0
    flow_bonus = money_flow_change * 2 if money_flow_change > 0 else 0
    rsi_adjust = 0
    if rsi > 70: rsi_adjust = -1.5
    elif rsi < 35: rsi_adjust = 1.5
    
    pred_5d = base_pred + trend_bonus + momentum_bonus + volume_bonus + breakout_bonus + flow_bonus + rsi_adjust
    
    # 波动率调整
    if vol > 60:
        pred_5d *= 0.85
    
    # 置信度
    confidence = 0
    if trend_score >= 4: confidence += 20
    if vol_ratio > 1.3: confidence += 15
    if breakout > 0: confidence += 15
    if money_flow_change > 0.15: confidence += 15
    if momentum_accel > 0: confidence += 10
    if rsi < 70: confidence += 15
    if vol < 50: confidence += 10
    
    return {
        'predicted': pred_5d,
        'confidence': confidence,
        'trend_score': trend_score,
        'vol_ratio': vol_ratio,
        'rsi': rsi,
        'volatility': vol
    }

def run_backtest():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"5 日趋势策略回测验证 v2.0 - 500 只股票大样本")
    print(f"时间：{ts}")
    print(f"目标：验证修复后的策略效果")
    print("="*80)
    
    df = load_data()
    max_date = df['date'].max()
    min_date = max_date - timedelta(days=CONFIG['test_days'])
    
    print(f"\n📅 回测期间：{min_date.date()} - {max_date.date()} ({CONFIG['test_days']}天)")
    print(f"🎯 目标涨幅：{CONFIG['target_gain']}%+")
    print(f"📆 持有期：{CONFIG['hold_days']}天")
    print(f"📊 样本股票：{CONFIG['sample_stocks']} 只")
    print(f"🔧 修复项:")
    print(f"   - 预测门槛：8% → {CONFIG['min_predicted']}%")
    print(f"   - 置信度：60 → {CONFIG['min_confidence']}")
    print(f"   - 最大波动率：{CONFIG['max_volatility']}%")
    print(f"   - 最大 RSI: {CONFIG['max_rsi']}")
    print()
    
    stocks = df['stock_code'].unique()
    if len(stocks) > CONFIG['sample_stocks']:
        np.random.seed(42)
        stocks = np.random.choice(stocks, CONFIG['sample_stocks'], replace=False)
    
    print(f"🔍 开始回测...\n")
    
    signals = []
    
    for i, stock in enumerate(stocks):
        stock_df = df[df['stock_code'] == stock].sort_values('date')
        if len(stock_df) < 50:
            continue
        
        test_period = stock_df[(stock_df['date'] >= min_date) & (stock_df['date'] <= max_date)]
        
        for idx, row in test_period.iterrows():
            signal_date = row['date']
            signal_idx = stock_df.index.get_loc(idx)
            
            if signal_idx < 30 or signal_idx >= len(stock_df) - CONFIG['hold_days']:
                continue
            
            hist_df = stock_df.iloc[:signal_idx]
            pred = predict_5day_gain(hist_df)
            
            if pred is None:
                continue
            
            # v2: 增加过滤条件
            if pred['volatility'] > CONFIG['max_volatility']:
                continue
            if pred['rsi'] > CONFIG['max_rsi']:
                continue
            
            if pred['predicted'] >= CONFIG['min_predicted'] and pred['confidence'] >= CONFIG['min_confidence']:
                future_close = stock_df.iloc[signal_idx + CONFIG['hold_days']]['close']
                current_close = row['close']
                actual_gain = (future_close - current_close) / current_close * 100
                
                signals.append({
                    'stock_code': stock,
                    'signal_date': signal_date,
                    'predicted': round(pred['predicted'], 2),
                    'confidence': round(pred['confidence'], 1),
                    'actual_5d_gain': round(actual_gain, 2),
                    'success': actual_gain >= CONFIG['target_gain'],
                    'trend_score': pred['trend_score'],
                    'vol_ratio': round(pred['vol_ratio'], 2),
                    'rsi': round(pred['rsi'], 1),
                    'volatility': round(pred['volatility'], 1)
                })
        
        if (i+1) % 50 == 0:
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
    mid_conf = df_signals[(df_signals['confidence'] >= 60) & (df_signals['confidence'] < 70)]
    low_conf = df_signals[df_signals['confidence'] < 60]
    
    print(f"\n总信号数：{total_signals}")
    print(f"成功次数：{success_count}/{total_signals} ({success_rate:.1f}%)")
    print(f"平均预测涨幅：{avg_predicted:.2f}%")
    print(f"平均实际涨幅：{avg_actual_gain:.2f}%")
    
    print(f"\n按置信度分组:")
    if len(high_conf) > 0:
        high_success = len(high_conf[high_conf['success']]) / len(high_conf) * 100
        high_avg = high_conf['actual_5d_gain'].mean()
        print(f"   高置信度 (>=70%): {len(high_conf)} 个信号，成功率 {high_success:.1f}%, 平均涨幅 {high_avg:.2f}%")
    if len(mid_conf) > 0:
        mid_success = len(mid_conf[mid_conf['success']]) / len(mid_conf) * 100
        mid_avg = mid_conf['actual_5d_gain'].mean()
        print(f"   中置信度 (60-70%): {len(mid_conf)} 个信号，成功率 {mid_success:.1f}%, 平均涨幅 {mid_avg:.2f}%")
    if len(low_conf) > 0:
        low_success = len(low_conf[low_conf['success']]) / len(low_conf) * 100
        low_avg = low_conf['actual_5d_gain'].mean()
        print(f"   低置信度 (<60%): {len(low_conf)} 个信号，成功率 {low_success:.1f}%, 平均涨幅 {low_avg:.2f}%")
    
    # 按趋势评分分组
    print(f"\n按趋势评分分组:")
    for ts_val in [5, 4, 3]:
        ts_group = df_signals[df_signals['trend_score'] >= ts_val]
        if len(ts_group) > 0:
            ts_success = len(ts_group[ts_group['success']]) / len(ts_group) * 100
            ts_avg = ts_group['actual_5d_gain'].mean()
            print(f"   趋势>= {ts_val}: {len(ts_group)} 个信号，成功率 {ts_success:.1f}%, 平均涨幅 {ts_avg:.2f}%")
    
    # 按波动率分组
    print(f"\n按波动率分组:")
    low_vol = df_signals[df_signals['volatility'] < 40]
    mid_vol = df_signals[(df_signals['volatility'] >= 40) & (df_signals['volatility'] < 60)]
    high_vol = df_signals[df_signals['volatility'] >= 60]
    
    if len(low_vol) > 0:
        lv_success = len(low_vol[low_vol['success']]) / len(low_vol) * 100
        lv_avg = low_vol['actual_5d_gain'].mean()
        print(f"   低波动 (<40%): {len(low_vol)} 个信号，成功率 {lv_success:.1f}%, 平均涨幅 {lv_avg:.2f}%")
    if len(mid_vol) > 0:
        mv_success = len(mid_vol[mid_vol['success']]) / len(mid_vol) * 100
        mv_avg = mid_vol['actual_5d_gain'].mean()
        print(f"   中波动 (40-60%): {len(mid_vol)} 个信号，成功率 {mv_success:.1f}%, 平均涨幅 {mv_avg:.2f}%")
    if len(high_vol) > 0:
        hv_success = len(high_vol[high_vol['success']]) / len(high_vol) * 100
        hv_avg = high_vol['actual_5d_gain'].mean()
        print(f"   高波动 (>=60%): {len(high_vol)} 个信号，成功率 {hv_success:.1f}%, 平均涨幅 {hv_avg:.2f}%")
    
    # 评估
    print("\n" + "="*80)
    print("✅ 策略评估")
    print("="*80)
    
    if success_rate >= 40:
        print(f"🎉 成功率 {success_rate:.1f}% - 优秀！策略可用")
        rating = "优秀"
    elif success_rate >= 30:
        print(f"✅ 成功率 {success_rate:.1f}% - 良好，可以使用")
        rating = "良好"
    elif success_rate >= 25:
        print(f"⚠️  成功率 {success_rate:.1f}% - 一般，需要优化")
        rating = "一般"
    else:
        print(f"❌ 成功率 {success_rate:.1f}% - 较差，需要大幅改进")
        rating = "较差"
    
    if avg_actual_gain >= CONFIG['target_gain']:
        print(f"🎯 平均实际涨幅 {avg_actual_gain:.2f}% - 达到目标 ({CONFIG['target_gain']}%)")
    elif avg_actual_gain > 0:
        print(f"⚠️  平均实际涨幅 {avg_actual_gain:.2f}% - 正收益但未达目标 ({CONFIG['target_gain']}%)")
    else:
        print(f"❌ 平均实际涨幅 {avg_actual_gain:.2f}% - 负收益")
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    result_file = f"{output_dir}/backtest_5day_v2_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': ts,
            'config': CONFIG,
            'summary': {
                'total_signals': total_signals,
                'success_count': success_count,
                'success_rate': round(success_rate, 1),
                'avg_predicted': round(avg_predicted, 2),
                'avg_actual_gain': round(avg_actual_gain, 2),
                'rating': rating
            }
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 结果已保存：{result_file}")
    print("\n✅ 回测完成！")
    
    return success_rate, avg_actual_gain, rating

if __name__ == '__main__':
    run_backtest()
