#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 v19.0 - 引入成交量因子
基于回测分析改进：
1. 增加成交量确认（量价配合）
2. 增加资金流因子
3. 改进下跌趋势判断
4. 动态调整预测上限
"""

import json, numpy as np, pandas as pd
from datetime import datetime, timedelta
import requests, os, warnings
warnings.filterwarnings('ignore')

CONFIG = {
    'max_predicted_change': 5.0,
    'volume_weight': 1.5,  # 新增：成交量权重
    'trend_weight': 1.5,
    'momentum_weight': 0.3,
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

def predict_v19(df):
    """v19.0 预测逻辑 - 引入成交量因子"""
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
    
    # v19 新增：成交量分析
    df['vol_ma5'] = df['vol'].rolling(5).mean()
    df['vol_ma20'] = df['vol'].rolling(20).mean()
    df['vol_ratio'] = df['vol'] / df['vol_ma20']  # 成交量比率
    
    # v19 新增：资金流（简化版）
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['money_flow'] = df['typical_price'] * df['vol']
    df['money_flow_ma5'] = df['money_flow'].rolling(5).mean()
    
    latest = df.iloc[-1]
    close, ma5, ma20, ma60 = latest['close'], latest['ma5'], latest['ma20'], latest['ma60']
    rsi_val = rsi.iloc[-1]
    macd_val = macd.iloc[-1]
    macd_hist_val = macd_hist.iloc[-1]
    
    # 成交量确认
    vol_ratio = latest['vol_ratio'] if 'vol_ratio' in latest else 1
    vol_confirm = 0
    if vol_ratio > 1.5:  # 放量
        if close > ma5: vol_confirm = 1.5  # 放量上涨 - 强信号
        elif close < ma5: vol_confirm = -1.0  # 放量下跌 - 谨慎
    elif vol_ratio < 0.7:  # 缩量
        if close > ma5: vol_confirm = 0.5  # 缩量上涨 - 弱信号
        elif close < ma5: vol_confirm = 0.5  # 缩量下跌 - 可能反弹
    
    # 资金流确认
    money_flow_confirm = 0
    if latest['money_flow'] > latest['money_flow_ma5']:
        money_flow_confirm = 1.0  # 资金流入
    else:
        money_flow_confirm = -0.5  # 资金流出
    
    # 趋势评分（保持 v18 的 1.5）
    trend_score = 0
    if close > ma5: trend_score += 1.5
    if close > ma20: trend_score += 1.5
    if close > ma60: trend_score += 1.5
    
    # RSI（仅极端值）
    rsi_score = 0
    if rsi_val < 25: rsi_score = 1.5
    elif rsi_val > 75: rsi_score = -1.5
    elif 45 < rsi_val < 65: rsi_score = 0.5
    
    # 动量
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # v19 核心公式：增加成交量和资金流
    base = (ret * 2.0 + 
            trend_score * CONFIG['trend_weight'] + 
            mom * CONFIG['momentum_weight'] +
            vol_confirm * CONFIG['volume_weight'] +
            money_flow_confirm * 1.0)
    
    # RSI 仅在极端值时加入
    if abs(rsi_score) > 0:
        base += rsi_score * 1.0
    
    # MACD 柱状图确认
    if macd_hist_val > 0 and macd_hist_val > macd_hist.iloc[-2] if len(macd_hist) > 1 else 0:
        base += 0.5
    elif macd_hist_val < 0 and macd_hist_val < macd_hist.iloc[-2] if len(macd_hist) > 1 else 0:
        base -= 0.5
    
    # 均线偏离
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 5: base += 0.5
    elif dev > 3: base += 0.3
    
    # 波动率调整
    vol = df['close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    if CONFIG['volatility_adjustment']:
        if vol > 70:
            base *= 0.8
        elif vol > 50:
            base *= 0.9
    
    # 动态调整预测上限（v19 新增）
    # 高波动股票放宽上限，低波动收紧
    if vol > 60:
        dynamic_max = 6.0
    elif vol < 30:
        dynamic_max = 4.0
    else:
        dynamic_max = 5.0
    
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
    print(f"股票预测 v19.0 (成交量因子版) - {ts}")
    print("="*80)
    print(f"v19.0 新增:")
    print(f"  1. 成交量确认因子（量价配合）")
    print(f"  2. 资金流因子（简化版）")
    print(f"  3. 动态预测上限（4-6%）")
    print(f"  4. MACD 柱状图确认")
    print(f"  保留：趋势 1.5x, RSI 极端值，波动率调整")
    print()
    
    stocks = load_stocks()
    print(f"监控：{len(stocks)} 只股票\n")
    
    results = []
    for i, stock in enumerate(stocks):
        code = stock.get('code', '')
        ts_code = stock.get('ts_code', code[2:])
        
        df = fetch_data(code)
        if df is None or len(df) < 30:
            continue
        
        pred = predict_v19(df)
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
        vol_flag = '🔥' if r['vol_ratio'] > 1.5 else ('💧' if r['vol_ratio'] < 0.7 else '')
        flow_flag = '💰' if r['money_flow'] == 'in' else '💸'
        print(f'{i}. {r["stock_name"]} ({r["stock_code"]}): {r["current_price"]}→{r["predicted_price"]} ({r["predicted_change"]:+.2f}%) {vol_flag}{flow_flag} 趋势={r["trend_score"]:.1f} RSI={r["rsi"]:.0f}')
    
    print('\n📉 TOP 5 跌幅:')
    for i, r in enumerate(results[-5:], 1):
        print(f'{i}. {r["stock_name"]} ({r["stock_code"]}): {r["predicted_change"]:+.2f}%')
    
    # 统计
    vol_confirm_count = len([r for r in results if r['vol_ratio'] > 1.5])
    money_in_count = len([r for r in results if r['money_flow'] == 'in'])
    print(f'\n📊 统计:')
    print(f'   放量股票：{vol_confirm_count} 只')
    print(f'   资金流入：{money_in_count} 只')
    
    # 保存
    out_dir = '/home/admin/openclaw/workspace/predictions'
    os.makedirs(out_dir, exist_ok=True)
    
    with open(f'{out_dir}/{date_str}.json', 'w') as f:
        json.dump([{'timestamp': ts, 'hour': hour_str, 'predictions': results}], f, indent=2, ensure_ascii=False)
    
    with open(f'{out_dir}/{date_str}_{hour_str.replace(":", "-")}.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f'\n✅ 已保存')
    print(f'\n🎯 预期改进:')
    print(f'   方向正确率：46.7% → 52%+ (成交量确认)')
    print(f'   平均误差：3.94% → 3.5% 以下')
    return results

if __name__ == '__main__':
    run_prediction()
