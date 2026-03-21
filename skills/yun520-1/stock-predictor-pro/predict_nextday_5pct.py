#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
次日涨 5%+ 预测 v23.0
使用已训练的 LightGBM 模型
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import warnings
warnings.filterwarnings('ignore')

try:
    import lightgbm as lgb
    HAS_LGB = True
except:
    HAS_LGB = False

CONFIG = {
    'target_days': 1,
    'target_gain': 5.0,
    'prob_threshold': 0.40,  # 降低到 40% 以提高召回
    'model_file': '/home/admin/openclaw/workspace/stock_system/ml_models/stock_lightgbm_v22.txt'
}

def create_features(df):
    df = df.copy().sort_values('date').reset_index(drop=True)
    for period in [5, 10, 20, 60]:
        df[f'ma_{period}'] = df['close'].rolling(period).mean()
        df[f'ma_{period}_ratio'] = df['close'] / df[f'ma_{period}'] - 1
    df['ma_5_10'] = (df['ma_5'] > df['ma_10']).astype(int)
    df['ma_10_20'] = (df['ma_10'] > df['ma_20']).astype(int)
    df['ma_20_60'] = (df['ma_20'] > df['ma_60']).astype(int)
    df['ma_bullish'] = df['ma_5_10'] + df['ma_10_20'] + df['ma_20_60']
    for period in [1, 3, 5, 10, 20]:
        df[f'ret_{period}d'] = df['close'].pct_change(period) * 100
    df['mom_accel'] = df['ret_5d'] - df['ret_10d']
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = (100 - (100 / (1 + rs))).fillna(50).clip(0, 100)
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    if 'volume' in df.columns:
        df['vol_ma5'] = df['volume'].rolling(5).mean()
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['vol_ma5'] / df['vol_ma20']
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['money_flow'] = df['typical_price'] * df['volume']
        df['money_flow_ma5'] = df['money_flow'].rolling(5).mean()
        df['money_flow_change'] = (df['money_flow'] - df['money_flow_ma5'].shift(5)) / df['money_flow_ma5'].shift(5)
    for period in [5, 10, 20]:
        df[f'volatility_{period}d'] = df['close'].pct_change().rolling(period).std() * np.sqrt(252) * 100
    df['high_20d'] = df['high'].rolling(20).max()
    df['low_20d'] = df['low'].rolling(20).min()
    df['breakout'] = (df['close'] > df['high_20d'].shift(1)).astype(int)
    df['breakdown'] = (df['close'] < df['low_20d'].shift(1)).astype(int)
    df['position_20d'] = (df['close'] - df['low_20d']) / (df['high_20d'] - df['low_20d'])
    return df

def get_feature_columns():
    return ['ma_5_ratio', 'ma_10_ratio', 'ma_20_ratio', 'ma_60_ratio', 'ma_bullish', 'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d', 'mom_accel', 'rsi', 'macd', 'macd_signal', 'macd_hist', 'vol_ratio', 'money_flow_change', 'volatility_5d', 'volatility_10d', 'volatility_20d', 'breakout', 'breakdown', 'position_20d']

def load_stocks():
    stock_file = os.path.join(os.path.dirname(__file__), 'stocks.json')
    if os.path.exists(stock_file):
        with open(stock_file, 'r') as f:
            return json.load(f)
    return []

def fetch_data(code, days=90):
    try:
        import requests
        market = "SH" if code.startswith("sh") else "SZ"
        symbol = code[2:]
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market}.{symbol}&klt=101&fqt=1&beg=19900101&end=20991231"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        d = r.json()
        if d.get('data') and d['data'].get('klines'):
            klines = d['data']['klines'][-days:]
            df = pd.DataFrame([k.split(',') for k in klines], columns=['date','open','close','high','low','vol','amount'])
            for c in ['open','close','high','low','vol','amount']:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            return df
    except: pass
    return None

def run_prediction():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"🚀 次日涨 5%+ 预测 v23.0 - {ts}")
    print("="*80)
    
    if not os.path.exists(CONFIG['model_file']):
        print(f"\n❌ 模型不存在：{CONFIG['model_file']}")
        print("请先运行：python3 stock_ml_v22.py")
        return
    
    model = lgb.Booster(model_file=CONFIG['model_file'])
    print(f"\n✅ 加载模型：{CONFIG['model_file']}")
    
    feature_cols = get_feature_columns()
    stocks = load_stocks()
    if not stocks:
        print("\n❌ 未找到股票列表")
        return
    
    print(f"\n监控：{len(stocks)} 只股票")
    print(f"目标：次日上涨 {CONFIG['target_gain']}%+")
    print(f"概率阈值：{CONFIG['prob_threshold']:.0%}\n")
    
    results = []
    for i, stock in enumerate(stocks):
        code = stock.get('code', '')
        ts_code = stock.get('ts_code', code[2:])
        name = stock.get('name', '-')
        df = fetch_data(code, days=90)
        if df is None or len(df) < 60:
            continue
        df_feat = create_features(df)
        latest = df_feat.iloc[-1:]
        X = latest[feature_cols]
        if X.isnull().any().any():
            continue
        prob_up = model.predict(X)[0]
        results.append({
            'stock_code': ts_code,
            'stock_name': name,
            'current_price': round(df['close'].iloc[-1], 2),
            'prob_up': round(prob_up, 3),
            'prediction': 'up' if prob_up >= CONFIG['prob_threshold'] else 'hold',
            'timestamp': ts
        })
        if (i+1) % 50 == 0:
            print(f'进度：{i+1}/{len(stocks)}')
    
    qualified = [r for r in results if r['prob_up'] >= CONFIG['prob_threshold']]
    qualified.sort(key=lambda x: x['prob_up'], reverse=True)
    
    print('='*80)
    print(f'筛选结果：{len(qualified)} 只股票符合 次日涨{CONFIG["target_gain"]}%+ 条件\n')
    
    if qualified:
        print('📈 TOP 20 推荐 (次日涨 5%+):')
        print('-'*80)
        for i, r in enumerate(qualified[:20], 1):
            stars = '⭐' * min(5, int(r['prob_up'] * 5))
            print(f'{i:2}. {r["stock_name"]} ({r["stock_code"]})')
            print(f'    现价：{r["current_price"]:.2f} | 上涨概率：{r["prob_up"]:.1%} {stars}')
            print(f'    预测：次日涨幅 {CONFIG["target_gain"]}%+')
            print()
    else:
        print('⚠️  无符合股票的，可能市场整体走弱')
    
    out_dir = '/home/admin/openclaw/workspace/stock-recommendations'
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    with open(f'{out_dir}/ml_prediction_nextday_{date_str}.json', 'w') as f:
        json.dump({
            'timestamp': ts,
            'model': 'LightGBM v23.0',
            'target': f'次日上涨{CONFIG["target_gain"]}%+',
            'prob_threshold': CONFIG['prob_threshold'],
            'total_screened': len(results),
            'qualified': len(qualified),
            'top_20': qualified[:20]
        }, f, indent=2, ensure_ascii=False)
    
    print(f'✅ 推荐已保存：{out_dir}/ml_prediction_nextday_{date_str}.json')
    print("\n" + "="*80)
    print("⚠️ 风险提示：预测仅供参考，不构成投资建议")
    print("="*80)
    
    return qualified[:20]

if __name__ == '__main__':
    run_prediction()
