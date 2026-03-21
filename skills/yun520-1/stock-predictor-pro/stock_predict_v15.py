#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 v15.0 - 自适应修复版
基于历史验证误差自动调整预测参数
"""

import json, numpy as np, pandas as pd
from datetime import datetime, timedelta
import requests, os, time, random, warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

CONFIG = {
    'max_workers': 5, 'timeout': 10, 'batch_size': 20,
    'max_predicted_change': 8.0,
    'adjustment_factor': 1.0,  # 自动调整系数
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

def predict_v15(df, adj_factor=1.0):
    if len(df) < 20: return None
    
    df = df.sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss)) if loss.mean() > 0 else 50
    
    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    macd = exp1 - exp2
    
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    
    # 趋势评分 (v15.0 增强)
    trend = 0
    if close > ma5: trend += 1.5
    if close > ma20: trend += 1.5
    if close > ma60: trend += 1.5
    if 55 < rsi.iloc[-1] < 75: trend += 1.5
    if macd.iloc[-1] > 0: trend += 1.0
    
    # 动量
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # v15.0 核心：自适应调整
    base = ret * 2.5 + trend * 1.2 + mom * 0.6
    
    # 均线偏离
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 3: base += 2.0
    elif dev > 2: base += 1.5
    elif dev > 1: base += 1.0
    
    # 应用调整系数
    base *= adj_factor
    
    # 上限
    pred = np.clip(base, -CONFIG['max_predicted_change'], CONFIG['max_predicted_change'])
    
    return {
        'current_price': round(close, 2),
        'predicted_change': round(pred, 2),
        'predicted_price': round(close * (1 + pred/100), 2),
        'trend_score': round(trend, 1),
    }

def run_prediction():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')
    hour_str = datetime.now().strftime('%H:00')
    
    # 加载调整系数
    adj_factor = 1.0
    cfg_file = '/home/admin/openclaw/workspace/stock_system/auto_fix_config.json'
    if os.path.exists(cfg_file):
        with open(cfg_file) as f:
            cfg = json.load(f)
            adj_factor = cfg.get('adjustment_factor', 1.0)
    
    print('='*80)
    print(f'股票预测 v15.0 (自适应修复版) - {ts}')
    print('='*80)
    print(f'调整系数：{adj_factor:.2f}')
    print()
    
    stocks = load_stocks()
    print(f'监控：{len(stocks)} 只股票\n')
    
    results = []
    for i, stock in enumerate(stocks):
        code = stock.get('code', '')
        ts_code = stock.get('ts_code', code[2:])
        
        df = fetch_data(code)
        if df is None or len(df) < 20:
            continue
        
        pred = predict_v15(df, adj_factor)
        if pred:
            pred['stock_code'] = ts_code
            pred['stock_name'] = stock.get('name', '-')
            pred['timestamp'] = ts
            results.append(pred)
        
        if (i+1) % 50 == 0:
            print(f'进度：{i+1}/{len(stocks)}')
    
    # 排序
    results.sort(key=lambda x: x['predicted_change'], reverse=True)
    
    print('='*80)
    print(f'成功：{len(results)} 只\n')
    
    print('📈 TOP 10:')
    for i, r in enumerate(results[:10], 1):
        print(f'{i}. {r["stock_name"]} ({r["stock_code"]}): {r["current_price"]}→{r["predicted_price"]} ({r["predicted_change"]:+.2f}%)')
    
    # 保存
    out_dir = '/home/admin/openclaw/workspace/predictions'
    os.makedirs(out_dir, exist_ok=True)
    
    with open(f'{out_dir}/{date_str}.json', 'w') as f:
        json.dump([{'timestamp': ts, 'hour': hour_str, 'predictions': results}], f, indent=2, ensure_ascii=False)
    
    with open(f'{out_dir}/{date_str}_{hour_str.replace(":", "-")}.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f'\n✅ 已保存')
    return results

if __name__ == '__main__':
    run_prediction()
