#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 v18.0 - 参数微调版
基于 v17.0 回测结果优化：
- 降低趋势权重（2.0 → 1.5）
- 调整 RSI 权重（仅极端值使用）
- 保留波动率调整（但降低收缩幅度）
- 保留预测上限 5%
"""

import json, numpy as np, pandas as pd
from datetime import datetime, timedelta
import requests, os, time, random, warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

CONFIG = {
    'max_workers': 5,
    'timeout': 10,
    'batch_size': 20,
    'max_predicted_change': 5.0,
    'trend_weight': 1.5,  # v18: 从 2.0 降到 1.5
    'momentum_weight': 0.3,
    'rsi_weight': 1.0,  # v18: 从 1.5 降到 1.0
    'volatility_adjustment': True,
    'volatility_factor': 0.8,  # v18: 从 0.6 提升到 0.8（减少收缩）
}

def load_stocks():
    with open(os.path.join(os.path.dirname(__file__), 'stocks.json'), 'r') as f:
        return json.load(f)

def fetch_data(code, days=60):
    try:
        market = "SH" if code.startswith("sh") else "SZ"
        symbol = code[2:]
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market}.{symbol}&klt=101&fqt=1&beg=19900101&end=20991231"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=CONFIG['timeout'])
        d = r.json()
        if d.get('data') and d['data'].get('klines'):
            klines = d['data']['klines'][-days:]
            df = pd.DataFrame([k.split(',') for k in klines], 
                            columns=['date','open','close','high','low','vol','amount'])
            for c in ['open','close','high','low','vol']:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            return df
    except: pass
    return None

def predict_v18(df):
    """v18.0 预测逻辑"""
    if len(df) < 20:
        return None
    
    df = df.sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss)) if loss.mean() > 0 else 50
    rsi = rsi.fillna(50).clip(0, 100)
    
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    macd = exp1 - exp2
    
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi_val = rsi.iloc[-1]
    macd_val = macd.iloc[-1]
    
    # v18: 降低趋势权重（2.0 → 1.5）
    trend_score = 0
    if close > ma5: trend_score += 1.5
    if close > ma20: trend_score += 1.5
    if close > ma60: trend_score += 1.5
    
    # v18: 调整 RSI 权重（仅极端值使用，1.5 → 1.0）
    rsi_score = 0
    if rsi_val < 25: rsi_score = 1.5  # 超卖加分
    elif rsi_val > 75: rsi_score = -1.5  # 超买减分
    elif 45 < rsi_val < 65: rsi_score = 0.5  # 中性区域轻微加分
    
    # v18: 保留动量权重 0.3
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # v18 核心公式
    base = ret * 2.0 + trend_score * CONFIG['trend_weight'] + mom * CONFIG['momentum_weight']
    
    # 仅在极端 RSI 时加入
    if abs(rsi_score) > 0:
        base += rsi_score * CONFIG['rsi_weight']
    
    # MACD 加分
    if macd_val > 0 and macd_val > (exp1 - exp2).iloc[-2] if len(macd) > 1 else 0:
        base += 0.5
    
    # 均线偏离（保守）
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 5: base += 0.5
    elif dev > 3: base += 0.3
    
    # v18: 波动率调整（降低收缩幅度）
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if CONFIG['volatility_adjustment']:
        if vol > 70:
            base *= CONFIG['volatility_factor']  # v18: 0.8（从 0.6 提升）
        elif vol > 50:
            base *= 0.9
    
    # 保留预测上限 5%
    pred = np.clip(base, -CONFIG['max_predicted_change'], CONFIG['max_predicted_change'])
    
    return {
        'current_price': round(close, 2),
        'predicted_change': round(pred, 2),
        'predicted_price': round(close * (1 + pred/100), 2),
        'trend_score': round(trend_score, 1),
        'rsi': round(rsi_val, 1),
        'volatility': round(vol, 1)
    }

def run_prediction():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')
    hour_str = datetime.now().strftime('%H:00')
    
    print("="*80)
    print(f"股票预测 v18.0 (参数微调版) - {ts}")
    print("="*80)
    print(f"v18.0 调整:")
    print(f"  1. 趋势权重：2.0 → 1.5")
    print(f"  2. RSI 权重：1.5 → 1.0（仅极端值）")
    print(f"  3. 波动率收缩：0.6 → 0.8")
    print(f"  4. 预测上限：保持 5%")
    print(f"  5. 新增：MACD 加分")
    print()
    
    stocks = load_stocks()
    print(f"监控：{len(stocks)} 只股票\n")
    
    results = []
    for i, stock in enumerate(stocks):
        code = stock.get('code', '')
        ts_code = stock.get('ts_code', code[2:])
        
        df = fetch_data(code)
        if df is None or len(df) < 20:
            continue
        
        pred = predict_v18(df)
        if pred:
            pred['stock_code'] = ts_code
            pred['stock_name'] = stock.get('name', '-')
            pred['timestamp'] = ts
            results.append(pred)
        
        if (i+1) % 50 == 0:
            print(f'进度：{i+1}/{len(stocks)}')
    
    results.sort(key=lambda x: x['predicted_change'], reverse=True)
    
    print('='*80)
    print(f'成功：{len(results)} 只\n')
    
    print('📈 TOP 10:')
    for i, r in enumerate(results[:10], 1):
        print(f'{i}. {r["stock_name"]} ({r["stock_code"]}): {r["current_price"]}→{r["predicted_price"]} ({r["predicted_change"]:+.2f}%) 趋势={r["trend_score"]:.1f} RSI={r["rsi"]:.0f}')
    
    print('\n📉 TOP 5 跌幅:')
    for i, r in enumerate(results[-5:], 1):
        print(f'{i}. {r["stock_name"]} ({r["stock_code"]}): {r["predicted_change"]:+.2f}%')
    
    # 保存
    out_dir = '/home/admin/openclaw/workspace/predictions'
    os.makedirs(out_dir, exist_ok=True)
    
    with open(f'{out_dir}/{date_str}.json', 'w') as f:
        json.dump([{'timestamp': ts, 'hour': hour_str, 'predictions': results}], f, indent=2, ensure_ascii=False)
    
    with open(f'{out_dir}/{date_str}_{hour_str.replace(":", "-")}.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f'\n✅ 已保存')
    print(f'\n🎯 预期改进:')
    print(f'   方向正确率：46.3% → 52%+')
    print(f'   平均误差：4.40% → 3.5% 以下')
    return results

if __name__ == '__main__':
    run_prediction()
