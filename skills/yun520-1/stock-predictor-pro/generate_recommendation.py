#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票推荐生成系统 v26.0
生成今日和明日推荐股票（前 10 只）
"""

import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime, timedelta
import os
import sqlite3

# 配置
CONFIG = {
    'db_path': '/home/admin/openclaw/workspace/stock_data.db',
    'model_path': '/home/admin/openclaw/workspace/skills/stock-predictor-pro/ml_models/ensemble_v25.pkl',
    'output_dir': '/home/admin/openclaw/workspace/stock-recommendations',
    'threshold': 0.65  # 最优阈值
}

def create_features(df):
    """创建技术特征"""
    df = df.copy().sort_index().reset_index(drop=True)
    
    # 均线
    for period in [5, 10, 20, 60]:
        df[f'ma_{period}'] = df['close'].rolling(period).mean()
        df[f'ma_{period}_ratio'] = df['close'] / df[f'ma_{period}'] - 1
    
    # 均线排列
    df['ma_5_10'] = (df['ma_5'] > df['ma_10']).astype(int)
    df['ma_10_20'] = (df['ma_10'] > df['ma_20']).astype(int)
    df['ma_20_60'] = (df['ma_20'] > df['ma_60']).astype(int)
    df['ma_bullish'] = df['ma_5_10'] + df['ma_10_20'] + df['ma_20_60']
    
    # 收益率
    for period in [1, 3, 5, 10, 20, 30]:
        df[f'ret_{period}d'] = df['close'].pct_change(period) * 100
    
    # 动量
    df['mom_accel'] = df['ret_5d'] - df['ret_10d']
    df['mom_accel_2'] = df['ret_3d'] - df['ret_5d']
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = (100 - (100 / (1 + rs))).fillna(50).clip(0, 100)
    
    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 成交量
    if 'volume' in df.columns:
        df['vol_ma5'] = df['volume'].rolling(5).mean()
        df['vol_ratio'] = df['vol_ma5'] / df['volume'].rolling(20).mean()
    
    # 波动率
    df['volatility_20d'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252) * 100
    
    # 突破
    df['high_20d'] = df['high'].rolling(20).max()
    df['low_20d'] = df['low'].rolling(20).min()
    df['breakout'] = (df['close'] > df['high_20d'].shift(1)).astype(int)
    df['position_20d'] = (df['close'] - df['low_20d']) / (df['high_20d'] - df['low_20d'])
    
    # 动量
    df['price_momentum'] = (df['close'] - df['close'].shift(10)) / df['close'].shift(10) * 100
    df['relative_strength'] = df['close'] / df['close'].shift(20) - 1
    
    return df

def get_feature_columns():
    return [
        'ma_5_ratio', 'ma_10_ratio', 'ma_20_ratio', 'ma_60_ratio',
        'ma_bullish', 'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d', 'ret_30d',
        'mom_accel', 'mom_accel_2', 'rsi', 'macd', 'macd_signal', 'macd_hist',
        'vol_ratio', 'volatility_20d', 'breakout', 'breakdown', 'position_20d',
        'price_momentum', 'relative_strength'
    ]

def get_stocks_from_db():
    """从数据库获取股票数据"""
    if not os.path.exists(CONFIG['db_path']):
        print("❌ 数据库不存在，使用 CSV 文件")
        return None
    
    conn = sqlite3.connect(CONFIG['db_path'])
    
    # 获取最新日期的所有股票
    df = pd.read_sql_query('''
        SELECT * FROM stock_data 
        WHERE date = (SELECT MAX(date) FROM stock_data)
    ''', conn)
    conn.close()
    
    return df

def predict_stocks(df_stocks, models, feature_cols):
    """预测所有股票"""
    predictions = []
    
    for _, row in df_stocks.iterrows():
        stock_code = str(row['stock_code'])
        
        # 获取历史数据
        conn = sqlite3.connect(CONFIG['db_path'])
        history = pd.read_sql_query('''
            SELECT date, open, high, low, close, volume, amount 
            FROM stock_data 
            WHERE stock_code = ?
            ORDER BY date DESC
            LIMIT 100
        ''', conn, params=(stock_code,))
        conn.close()
        
        if len(history) < 60:
            continue
        
        # 计算特征
        history = history.sort_values('date').reset_index(drop=True)
        history = create_features(history)
        
        # 获取最新特征
        latest = history.iloc[-1]
        
        # 提取特征
        try:
            X = latest[feature_cols].values.reshape(1, -1)
            
            if np.any(np.isnan(X)) or np.any(np.isinf(X)):
                continue
            
            # 集成预测
            preds = []
            for model in models.values():
                pred = model.predict_proba(X)[0, 1]
                preds.append(pred)
            
            prob = np.mean(preds)
            
            # 计算其他指标
            current_price = latest['close']
            ma5 = latest.get('ma_5', current_price)
            ma20 = latest.get('ma_20', current_price)
            rsi = latest.get('rsi', 50)
            macd = latest.get('macd', 0)
            
            # 风险评分
            risk_score = 0
            if latest.get('volatility_20d', 0) > 50:
                risk_score += 2
            if latest.get('position_20d', 0.5) > 0.8:
                risk_score += 1
            if abs(rsi - 50) > 30:
                risk_score += 1
            
            predictions.append({
                'stock_code': stock_code,
                'stock_name': row.get('stock_name', 'Unknown'),
                'current_price': current_price,
                'probability': prob,
                'predicted_change': (prob - 0.5) * 20,  # 简化估算
                'ma5': ma5,
                'ma20': ma20,
                'rsi': rsi,
                'macd': macd,
                'risk_score': risk_score,
                'signal': '🟢' if prob > CONFIG['threshold'] else '🟡' if prob > 0.5 else '🔴',
                'confidence': '高' if prob > 0.7 else '中' if prob > 0.5 else '低'
            })
            
        except Exception as e:
            continue
    
    return predictions

def generate_recommendation():
    """生成推荐"""
    print("="*80)
    print(f"📈 股票推荐生成系统 v26.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 加载模型
    print(f"\n📦 加载模型...")
    with open(CONFIG['model_path'], 'rb') as f:
        model_data = pickle.load(f)
    models = model_data['models']
    feature_cols = model_data['feature_cols']
    print(f"   模型：集成 (LGB + XGB + RF)")
    
    # 获取股票数据
    print(f"\n📊 获取股票数据...")
    df_stocks = get_stocks_from_db()
    
    if df_stocks is None or len(df_stocks) == 0:
        print("   使用 CSV 数据...")
        df_stocks = pd.read_csv('/home/admin/Downloads/workspace/chinese-stock-dataset/chinese-stock-dataset.csv', 
                               on_bad_lines='skip', nrows=10000)
    
    print(f"   股票数量：{len(df_stocks)}")
    
    # 预测
    print(f"\n🔮 生成预测...")
    predictions = predict_stocks(df_stocks, models, feature_cols)
    print(f"   完成预测：{len(predictions)} 只股票")
    
    # 排序
    predictions.sort(key=lambda x: x['probability'], reverse=True)
    
    # 生成今日推荐
    print(f"\n📋 生成今日推荐...")
    today_rec = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'type': '今日推荐',
        'threshold': CONFIG['threshold'],
        'total_stocks': len(predictions),
        'top10': predictions[:10]
    }
    
    # 生成明日推荐（使用相同预测，标注为明日）
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_rec = {
        'date': tomorrow.strftime('%Y-%m-%d'),
        'type': '明日预测',
        'threshold': CONFIG['threshold'],
        'total_stocks': len(predictions),
        'top10': predictions[:10]
    }
    
    # 保存
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    
    today_file = os.path.join(CONFIG['output_dir'], f'recommendation_{datetime.now().strftime("%Y%m%d")}_today.json')
    with open(today_file, 'w', encoding='utf-8') as f:
        json.dump(today_rec, f, indent=2, ensure_ascii=False)
    
    tomorrow_file = os.path.join(CONFIG['output_dir'], f'recommendation_{tomorrow.strftime("%Y%m%d")}_tomorrow.json')
    with open(tomorrow_file, 'w', encoding='utf-8') as f:
        json.dump(tomorrow_rec, f, indent=2, ensure_ascii=False)
    
    # 打印结果
    print(f"\n{'='*80}")
    print(f"🏆 今日推荐 TOP 10")
    print(f"{'='*80}")
    print(f"{'排名':<4} {'代码':<10} {'名称':<15} {'价格':<10} {'概率':<8} {'信号':<6} {'置信度':<8}")
    print(f"{'-'*80}")
    
    for i, pred in enumerate(predictions[:10], 1):
        print(f"{i:<4} {pred['stock_code']:<10} {pred.get('stock_name', 'Unknown'):<15} "
              f"{pred['current_price']:<10.2f} {100*pred['probability']:<8.1f}% "
              f"{pred['signal']:<6} {pred['confidence']:<8}")
    
    print(f"\n💾 推荐已保存:")
    print(f"   今日：{today_file}")
    print(f"   明日：{tomorrow_file}")
    print(f"{'='*80}")
    
    return predictions[:10]

if __name__ == '__main__':
    generate_recommendation()
