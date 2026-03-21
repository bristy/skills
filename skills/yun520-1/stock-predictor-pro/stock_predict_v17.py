#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 v17.0 - 回测修复版
基于 2149 个样本回测结果优化：
- 方向正确率从 47% 提升到目标 55%+
- 平均误差从 5.35% 降低到目标 3% 以下
"""

import json, numpy as np, pandas as pd
from datetime import datetime, timedelta
import requests, os, time, random, warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

# ============== v17.0 核心修复配置 ==============
CONFIG = {
    'max_workers': 5,
    'timeout': 10,
    'batch_size': 20,
    
    # 修复 1: 降低预测上限（从 8% 降到 5%）
    'max_predicted_change': 5.0,
    
    # 修复 2: 增加趋势权重
    'trend_weight': 2.0,  # 从 1.2 提升到 2.0
    
    # 修复 3: 减少动量权重
    'momentum_weight': 0.3,  # 从 0.6 降低到 0.3
    
    # 修复 4: 增加 RSI 权重
    'rsi_weight': 1.5,  # 新增
    
    # 修复 5: 增加波动率调整
    'volatility_adjustment': True,
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

def predict_v17(df):
    """
    v17.0 修复版预测逻辑
    """
    if len(df) < 20:
        return None
    
    df = df.sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss)) if loss.mean() > 0 else 50
    rsi = rsi.fillna(50).clip(0, 100)
    
    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    macd = exp1 - exp2
    
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi_val = rsi.iloc[-1]
    macd_val = macd.iloc[-1]
    
    # ===== v17.0 核心修复 =====
    
    # 修复 2: 增加趋势权重（从 1.2 提升到 2.0）
    trend_score = 0
    if close > ma5: trend_score += 2.0  # 从 1.5 提升到 2.0
    if close > ma20: trend_score += 2.0  # 从 1.5 提升到 2.0
    if close > ma60: trend_score += 2.0  # 从 1.5 提升到 2.0
    
    # 修复 4: 增加 RSI 权重（新增）
    rsi_score = 0
    if 50 < rsi_val < 70: rsi_score = 2.0  # 强势区间
    elif 30 < rsi_val <= 50: rsi_score = 1.0  # 中性
    elif rsi_val <= 30: rsi_score = -1.0  # 超卖
    elif rsi_val >= 70: rsi_score = -1.0  # 超买
    
    # 修复 3: 减少动量权重（从 0.6 降到 0.3）
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # 基础预测
    base = ret * 2.0 + trend_score * CONFIG['trend_weight'] + mom * CONFIG['momentum_weight'] + rsi_score * CONFIG['rsi_weight']
    
    # 均线偏离（适度）
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 5: base += 1.0  # 只有大幅偏离才加分
    elif dev > 3: base += 0.5
    
    # 修复 5: 增加波动率调整
    if CONFIG['volatility_adjustment']:
        vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
        if vol > 60:
            base *= 0.6  # 高波动大幅收缩
        elif vol > 40:
            base *= 0.8  # 中高波动收缩
    
    # 修复 1: 降低预测上限（从 8% 降到 5%）
    pred = np.clip(base, -CONFIG['max_predicted_change'], CONFIG['max_predicted_change'])
    
    return {
        'current_price': round(close, 2),
        'predicted_change': round(pred, 2),
        'predicted_price': round(close * (1 + pred/100), 2),
        'trend_score': round(trend_score, 1),
        'rsi': round(rsi_val, 1),
        'volatility': round(vol, 1) if CONFIG['volatility_adjustment'] else None
    }

def run_prediction():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')
    hour_str = datetime.now().strftime('%H:00')
    
    print("="*80)
    print(f"股票预测 v17.0 (回测修复版) - {ts}")
    print("="*80)
    print(f"修复项:")
    print(f"  1. 预测上限：8% → 5%")
    print(f"  2. 趋势权重：1.2 → 2.0")
    print(f"  3. 动量权重：0.6 → 0.3")
    print(f"  4. RSI 权重：新增 1.5")
    print(f"  5. 波动率调整：启用")
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
        
        pred = predict_v17(df)
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
        vol_flag = '' if r.get('volatility') is None else f' (波动率{r["volatility"]}%)'
        print(f'{i}. {r["stock_name"]} ({r["stock_code"]}): {r["current_price"]}→{r["predicted_price"]} ({r["predicted_change"]:+.2f}%) 趋势={r["trend_score"]:.1f}{vol_flag}')
    
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
    print(f'   方向正确率：47% → 55%+')
    print(f'   平均误差：5.35% → 3% 以下')
    return results

if __name__ == '__main__':
    run_prediction()
