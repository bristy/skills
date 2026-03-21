#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 v21.0 - 优化增强版
基于 v19.0 最佳实践 + v20.0 教训
优化点：
1. 保留 v19.0 核心因子（最简洁有效）
2. 优化趋势权重（1.5 → 1.8）
3. 优化 RSI 阈值（30/70 → 25/75）
4. 增加均线偏离敏感度
5. 改进波动率调整
"""

import json, numpy as np, pandas as pd
from datetime import datetime, timedelta
import requests, os, warnings
warnings.filterwarnings('ignore')

CONFIG = {
    'max_predicted_change': 5.0,
    'volume_weight': 1.5,
    'trend_weight': 1.8,  # v21: 从 1.5 提升到 1.8
    'momentum_weight': 0.35,  # v21: 从 0.3 提升到 0.35
    'rsi_low': 25,  # v21: 从 30 降到 25（更极端）
    'rsi_high': 75,  # v21: 从 70 升到 75（更极端）
    'volatility_adjustment': True,
}

def load_stocks():
    with open(os.path.join(os.path.dirname(__file__), 'stocks.json'), 'r') as f:
        return json.load(f)

def fetch_data(code, days=90):
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

def predict_v21(df):
    """v21.0 优化增强版预测"""
    if len(df) < 30:
        return None
    
    df = df.sort_values('date').reset_index(drop=True)
    
    # 均线系统
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
    macd_signal = macd.ewm(span=9).mean()
    macd_hist = macd - macd_signal
    
    # 成交量
    if 'volume' in df.columns:
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        vol_ratio = df['volume'].iloc[-1] / df['vol_ma20'].iloc[-1] if df['vol_ma20'].iloc[-1] > 0 else 1
        df['money_flow'] = (df['high'] + df['low'] + df['close']) / 3 * df['volume']
    else:
        vol_ratio = 1.0
        df['money_flow'] = 0
    
    # 资金流
    money_flow_confirm = 1.0 if df['money_flow'].iloc[-1] > df['money_flow'].rolling(5).mean().iloc[-1] else -0.5
    
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi_val = rsi.iloc[-1]
    
    # ===== v21.0 核心因子 =====
    
    # 1. 趋势因子（v21: 权重 1.5 → 1.8）
    trend_score = 0
    if close > ma5: trend_score += CONFIG['trend_weight']
    if close > ma20: trend_score += CONFIG['trend_weight']
    if close > ma60: trend_score += CONFIG['trend_weight']
    
    # 2. 成交量因子
    vol_confirm = 0
    if vol_ratio > 1.5:
        vol_confirm = 2.0 if close > ma5 else -1.0
    elif vol_ratio < 0.7:
        vol_confirm = 0.5
    
    # 3. RSI 因子（v21: 阈值优化 30/70 → 25/75）
    rsi_score = 0
    if rsi_val < CONFIG['rsi_low']: rsi_score = 2.0  # 超卖
    elif rsi_val > CONFIG['rsi_high']: rsi_score = -2.0  # 超买
    elif 45 < rsi_val < 60: rsi_score = 1.0  # 中性偏多
    
    # 4. 动量因子（v21: 权重 0.3 → 0.35）
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # 5. MACD 确认
    macd_confirm = 0.5 if macd_hist.iloc[-1] > 0 else -0.5
    
    # v21.0 综合公式
    base = (ret * 2.2 +  # v21: 从 2.0 提升到 2.2
            trend_score * CONFIG['trend_weight'] + 
            mom * CONFIG['momentum_weight'] +
            vol_confirm * CONFIG['volume_weight'] +
            money_flow_confirm * 1.0 +
            rsi_score * 1.0 +
            macd_confirm)
    
    # v21: 均线偏离更敏感
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 6: base += 1.5  # v21: 从 5/1.0 提升到 6/1.5
    elif dev > 4: base += 1.0  # v21: 从 3/0.5 提升到 4/1.0
    elif dev > 2: base += 0.5  # v21: 新增
    
    # v21: 改进波动率调整
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if CONFIG['volatility_adjustment']:
        if vol > 80:
            base *= 0.75  # v21: 从 70/0.8 调整到 80/0.75
        elif vol > 60:
            base *= 0.85  # v21: 从 50/0.9 调整到 60/0.85
    
    # 动态上限
    dynamic_max = 6.0 if vol > 70 else (4.0 if vol < 25 else 5.0)
    pred = np.clip(base, -dynamic_max, dynamic_max)
    
    return {
        'current_price': round(close, 2),
        'predicted_change': round(pred, 2),
        'predicted_price': round(close * (1 + pred/100), 2),
        'trend_score': round(trend_score, 1),
        'rsi': round(rsi_val, 1),
        'vol_ratio': round(vol_ratio, 2),
        'money_flow': 'in' if money_flow_confirm > 0 else 'out',
        'volatility': round(vol, 1)
    }

def run_prediction():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')
    hour_str = datetime.now().strftime('%H:00')
    
    print("="*80)
    print(f"股票预测 v21.0 (优化增强版) - {ts}")
    print("="*80)
    print(f"v21.0 优化项:")
    print(f"  1. 趋势权重：1.5 → 1.8")
    print(f"  2. 动量权重：0.3 → 0.35")
    print(f"  3. RSI 阈值：30/70 → 25/75（更极端）")
    print(f"  4. 均线偏离：更敏感（6%/1.5, 4%/1.0, 2%/0.5）")
    print(f"  5. 波动率调整：80/0.75, 60/0.85")
    print(f"  6. 动量系数：2.0 → 2.2")
    print(f"  保留：v19.0 核心因子（成交量、资金流、MACD）")
    print()
    
    stocks = load_stocks()
    print(f"监控：{len(stocks)} 只股票\n")
    
    results = []
    for i, stock in enumerate(stocks):
        code = stock.get('code', '')
        ts_code = stock.get('ts_code', code[2:])
        name = stock.get('name', '-')
        
        df = fetch_data(code, days=90)
        if df is None or len(df) < 30:
            continue
        
        pred = predict_v21(df)
        if pred:
            pred['stock_code'] = ts_code
            pred['stock_name'] = name
            pred['timestamp'] = ts
            results.append(pred)
        
        if (i+1) % 50 == 0:
            print(f'进度：{i+1}/{len(stocks)}')
    
    results.sort(key=lambda x: x['predicted_change'], reverse=True)
    
    print('='*80)
    print(f'成功：{len(results)} 只\n')
    
    print('📈 TOP 10:')
    for i, r in enumerate(results[:10], 1):
        flags = ''
        if r['vol_ratio'] > 1.5: flags += '💰'
        if r['money_flow'] == 'in': flags += '📈'
        print(f'{i}. {r["stock_name"]} ({r["stock_code"]}): {r["current_price"]}→{r["predicted_price"]} ({r["predicted_change"]:+.2f}%) {flags} 趋势={r["trend_score"]:.1f} RSI={r["rsi"]:.0f}')
    
    print('\n📉 TOP 5 跌幅:')
    for i, r in enumerate(results[-5:], 1):
        print(f'{i}. {r["stock_name"]} ({r["stock_code"]}): {r["predicted_change"]:+.2f}%')
    
    # 统计
    vol_up = len([r for r in results if r['vol_ratio'] > 1.5])
    money_in = len([r for r in results if r['money_flow'] == 'in'])
    trend_up = len([r for r in results if r['trend_score'] > 0])
    
    print(f'\n📊 统计:')
    print(f'   放量股票：{vol_up} 只')
    print(f'   资金流入：{money_in} 只')
    print(f'   趋势向上：{trend_up} 只')
    
    # 保存
    out_dir = '/home/admin/openclaw/workspace/predictions'
    os.makedirs(out_dir, exist_ok=True)
    
    with open(f'{out_dir}/{date_str}.json', 'w') as f:
        json.dump([{'timestamp': ts, 'hour': hour_str, 'predictions': results}], f, indent=2, ensure_ascii=False)
    
    with open(f'{out_dir}/{date_str}_{hour_str.replace(":", "-")}.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f'\n✅ 已保存')
    print(f'\n🎯 预期改进:')
    print(f'   方向正确率：46.9% → 50%+')
    print(f'   平均误差：3.74% → 3.5% 以下')
    return results

if __name__ == '__main__':
    run_prediction()
