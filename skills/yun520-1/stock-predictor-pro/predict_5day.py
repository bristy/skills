#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5 日趋势预测系统 v1.0
目标：筛选 5 天内上涨 5% 以上的股票
策略：
1. 趋势强度（均线多头排列）
2. 动量加速（近期涨幅扩大）
3. 成交量确认（放量上涨）
4. 突破形态（突破关键位置）
5. 资金流入（连续流入）
"""

import json, numpy as np, pandas as pd
from datetime import datetime, timedelta
import requests, os, warnings
warnings.filterwarnings('ignore')

CONFIG = {
    'min_trend_score': 3.0,  # 最低趋势评分
    'min_momentum': 2.0,  # 最低动量（%）
    'min_volume_ratio': 1.2,  # 最低成交量比率
    'min_breakout': 0.0,  # 突破要求
    'lookback_days': 20,  # 回看天数
}

def load_stocks():
    with open(os.path.join(os.path.dirname(__file__), 'stocks.json'), 'r') as f:
        return json.load(f)

def fetch_data(code, days=60):
    try:
        market = "SH" if code.startswith("sh") else "SZ"
        symbol = code[2:]
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market}.{symbol}&klt=101&fqt=1&beg=19900101&end=20991231"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        d = r.json()
        if d.get('data') and d['data'].get('klines'):
            klines = d['data']['klines'][-days:]
            df = pd.DataFrame([k.split(',') for k in klines], 
                            columns=['date','open','close','high','low','vol','amount'])
            for c in ['open','close','high','low','vol','amount']:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            return df
    except: pass
    return None

def predict_5day_gain(df):
    """
    预测 5 日涨幅
    返回：预测涨幅、置信度、关键指标
    """
    if len(df) < 30:
        return None
    
    df = df.sort_values('date').reset_index(drop=True)
    
    # 均线系统
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    # 均线多头排列评分
    latest = df.iloc[-1]
    close = latest['close']
    ma5, ma10, ma20, ma60 = latest['ma5'], latest['ma10'], latest['ma20'], latest['ma60']
    
    trend_score = 0
    if ma5 > ma10: trend_score += 1
    if ma10 > ma20: trend_score += 1
    if ma20 > ma60: trend_score += 1
    if close > ma5: trend_score += 1
    if close > ma20: trend_score += 1
    
    # 动量指标
    ret_5d = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    ret_10d = df['close'].pct_change(10).iloc[-1] * 100 if len(df) > 10 else 0
    ret_20d = df['close'].pct_change(20).iloc[-1] * 100 if len(df) > 20 else 0
    
    # 动量加速（近期涨幅扩大）
    momentum_accel = ret_5d - ret_10d if ret_10d != 0 else ret_5d
    
    # 成交量分析
    if 'volume' in df.columns:
        vol_ma5 = df['vol'].rolling(5).mean().iloc[-1]
        vol_ma20 = df['vol'].rolling(20).mean().iloc[-1]
        vol_ratio = vol_ma5 / vol_ma20 if vol_ma20 > 0 else 1
        
        # 资金流
        df['money_flow'] = (df['high'] + df['low'] + df['close']) / 3 * df['vol']
        money_flow_5d = df['money_flow'].iloc[-5:].sum()
        money_flow_prev = df['money_flow'].iloc[-10:-5].sum()
        money_flow_change = (money_flow_5d - money_flow_prev) / money_flow_prev if money_flow_prev > 0 else 0
    else:
        vol_ratio = 1.0
        money_flow_change = 0
    
    # 突破形态（是否突破 20 日高点）
    high_20d = df['high'].rolling(20).max().iloc[-2]  # 前一日 20 日高点
    breakout = (close - high_20d) / high_20d * 100 if high_20d > 0 else 0
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss)) if loss.mean() > 0 else 50
    
    # ===== 5 日涨幅预测公式 =====
    # 基础：近期动量
    base_pred = ret_5d * 0.5 + ret_10d * 0.3
    
    # 趋势加分
    trend_bonus = trend_score * 0.8
    
    # 动量加速加分
    momentum_bonus = momentum_accel * 0.5
    
    # 成交量确认
    volume_bonus = (vol_ratio - 1) * 2 if vol_ratio > 1 else 0
    
    # 突破加分
    breakout_bonus = breakout * 0.5 if breakout > 0 else 0
    
    # 资金流加分
    flow_bonus = money_flow_change * 3 if money_flow_change > 0 else 0
    
    # RSI 调整（避免超买）
    rsi_adjust = 0
    if rsi > 75: rsi_adjust = -2
    elif rsi < 30: rsi_adjust = 2
    
    # 综合预测
    pred_5d = base_pred + trend_bonus + momentum_bonus + volume_bonus + breakout_bonus + flow_bonus + rsi_adjust
    
    # 置信度（基于信号强度）
    confidence = 0
    if trend_score >= 4: confidence += 20
    if vol_ratio > 1.5: confidence += 20
    if breakout > 0: confidence += 15
    if money_flow_change > 0.2: confidence += 15
    if momentum_accel > 0: confidence += 10
    if rsi < 70: confidence += 20
    
    # 波动率调整
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if vol > 60:
        pred_5d *= 0.8
        confidence *= 0.8
    
    return {
        'predicted_5d_gain': round(pred_5d, 2),
        'confidence': round(confidence, 1),
        'trend_score': trend_score,
        'ret_5d': round(ret_5d, 2),
        'ret_10d': round(ret_10d, 2),
        'momentum_accel': round(momentum_accel, 2),
        'vol_ratio': round(vol_ratio, 2),
        'breakout': round(breakout, 2),
        'money_flow_change': round(money_flow_change, 2),
        'rsi': round(rsi, 1),
        'volatility': round(vol, 1)
    }

def run_screening():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"5 日趋势选股系统 v1.0 - {ts}")
    print(f"目标：筛选 5 天内上涨 5% 以上的股票")
    print("="*80)
    
    stocks = load_stocks()
    print(f"\n监控：{len(stocks)} 只股票\n")
    
    results = []
    for i, stock in enumerate(stocks):
        code = stock.get('code', '')
        ts_code = stock.get('ts_code', code[2:])
        name = stock.get('name', '-')
        
        df = fetch_data(code, days=60)
        if df is None or len(df) < 30:
            continue
        
        pred = predict_5day_gain(df)
        if pred:
            pred['stock_code'] = ts_code
            pred['stock_name'] = name
            pred['current_price'] = round(df['close'].iloc[-1], 2)
            pred['timestamp'] = ts
            results.append(pred)
        
        if (i+1) % 50 == 0:
            print(f'进度：{i+1}/{len(stocks)}')
    
    # 筛选：预测 5 日涨幅 >= 5% 且 置信度 >= 50
    filtered = [r for r in results if r['predicted_5d_gain'] >= 5.0 and r['confidence'] >= 50]
    filtered.sort(key=lambda x: x['predicted_5d_gain'], reverse=True)
    
    print('\n' + '='*80)
    print(f'筛选结果：{len(filtered)} 只股票符合 5 日涨 5%+ 条件\n')
    
    print('📈 TOP 20 推荐（5 日涨幅预测）:')
    print('-'*80)
    for i, r in enumerate(filtered[:20], 1):
        flags = ''
        if r['trend_score'] >= 4: flags += '📈'
        if r['vol_ratio'] > 1.5: flags += '💰'
        if r['breakout'] > 0: flags += '🚀'
        if r['money_flow_change'] > 0.2: flags += '💵'
        
        print(f'{i:2}. {r["stock_name"]} ({r["stock_code"]})')
        print(f'    现价：{r["current_price"]:.2f} | 预测 5 日：+{r["predicted_5d_gain"]:.1f}% | 置信度：{r["confidence"]:.0f}%')
        print(f'    趋势：{r["trend_score"]}/5 | 5 日涨：{r["ret_5d"]:.1f}% | 10 日涨：{r["ret_10d"]:.1f}%')
        print(f'    量能：{r["vol_ratio"]:.2f}x | 突破：{r["breakout"]:+.1f}% | 资金：{r["money_flow_change"]:+.1f}% | RSI: {r["rsi"]:.0f}{flags}')
        print()
    
    # 保存
    out_dir = '/home/admin/openclaw/workspace/stock-recommendations'
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    with open(f'{out_dir}/5day_prediction_{date_str}.json', 'w') as f:
        json.dump({
            'timestamp': ts,
            'target': '5 日上涨 5%+',
            'total_screened': len(results),
            'qualified': len(filtered),
            'top_20': filtered[:20]
        }, f, indent=2, ensure_ascii=False)
    
    print(f'✅ 推荐已保存：{out_dir}/5day_prediction_{date_str}.json')
    
    return filtered[:20]

if __name__ == '__main__':
    run_screening()
