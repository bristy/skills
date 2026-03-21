#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成明日涨幅最高前十股票推荐 v25.2
使用已训练的集成模型进行预测
"""

import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
import json
import os

# 配置
CONFIG = {
    'model_path': '/home/admin/openclaw/workspace/skills/stock-predictor-pro/ml_models/ensemble_v25.pkl',
    'data_file': '/home/admin/Downloads/workspace/chinese-stock-dataset/chinese-stock-dataset.csv',
    'threshold': 0.65  # 使用推荐阈值
}

def create_features(df):
    """创建特征"""
    df = df.copy().sort_values('date').reset_index(drop=True)
    
    for period in [5, 10, 20, 60]:
        df[f'ma_{period}'] = df['close'].rolling(period).mean()
        df[f'ma_{period}_ratio'] = df['close'] / df[f'ma_{period}'] - 1
    
    df['ma_5_10'] = (df['ma_5'] > df['ma_10']).astype(int)
    df['ma_10_20'] = (df['ma_10'] > df['ma_20']).astype(int)
    df['ma_20_60'] = (df['ma_20'] > df['ma_60']).astype(int)
    df['ma_bullish'] = df['ma_5_10'] + df['ma_10_20'] + df['ma_20_60']
    
    for period in [1, 3, 5, 10, 20, 30]:
        df[f'ret_{period}d'] = df['close'].pct_change(period) * 100
    
    df['mom_accel'] = df['ret_5d'] - df['ret_10d']
    df['mom_accel_2'] = df['ret_3d'] - df['ret_5d']
    
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
        df['money_flow_change'] = df['money_flow'] / df['money_flow_ma5'].shift(5) - 1
    
    for period in [5, 10, 20]:
        df[f'volatility_{period}d'] = df['close'].pct_change().rolling(period).std() * np.sqrt(252) * 100
    
    df['high_20d'] = df['high'].rolling(20).max()
    df['low_20d'] = df['low'].rolling(20).min()
    df['breakout'] = (df['close'] > df['high_20d'].shift(1)).astype(int)
    df['breakdown'] = (df['close'] < df['low_20d'].shift(1)).astype(int)
    df['position_20d'] = (df['close'] - df['low_20d']) / (df['high_20d'] - df['low_20d'])
    df['price_momentum'] = (df['close'] - df['close'].shift(10)) / df['close'].shift(10) * 100
    df['relative_strength'] = df['close'] / df['close'].shift(20) - 1
    
    return df

def get_feature_columns():
    return [
        'ma_5_ratio', 'ma_10_ratio', 'ma_20_ratio', 'ma_60_ratio',
        'ma_bullish', 'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d', 'ret_30d',
        'mom_accel', 'mom_accel_2', 'rsi', 'macd', 'macd_signal', 'macd_hist',
        'vol_ratio', 'money_flow_change', 'volatility_5d', 'volatility_10d', 'volatility_20d',
        'breakout', 'breakdown', 'position_20d', 'price_momentum', 'relative_strength'
    ]

def generate_top10():
    """生成明日涨幅最高前十推荐"""
    print("="*80)
    print(f"📈 明日涨幅最高前十股票推荐")
    print(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模型：集成模型 v25.1 (阈值={CONFIG['threshold']})")
    print("="*80)
    
    # 加载模型
    print(f"\n📦 加载模型...")
    try:
        with open(CONFIG['model_path'], 'rb') as f:
            model_data = pickle.load(f)
        models = model_data['models']
        feature_cols = model_data['feature_cols']
        print(f"   ✅ 模型加载成功")
    except Exception as e:
        print(f"   ❌ 模型加载失败：{e}")
        print(f"   使用简化预测...")
        models = None
    
    # 加载数据
    print(f"\n📊 加载股票数据...")
    try:
        df = pd.read_csv(CONFIG['data_file'], on_bad_lines='skip')
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df = df.sort_values(['stock_code', 'date']).reset_index(drop=True)
        
        # 获取每个股票的最新数据
        latest_data = []
        for stock in df['stock_code'].unique():
            stock_df = df[df['stock_code'] == stock].iloc[-1:].copy()
            if len(stock_df) > 20:  # 至少需要 20 天数据计算指标
                latest_data.append(stock_df)
        
        df_latest = pd.concat(latest_data, ignore_index=True)
        print(f"   ✅ 获取到 {len(df_latest)} 只股票的最新数据")
        
    except Exception as e:
        print(f"   ❌ 数据加载失败：{e}")
        return
    
    # 特征工程
    print(f"\n🔧 特征工程...")
    all_stocks = []
    for _, row in df_latest.iterrows():
        stock_df = df[df['stock_code'] == row['stock_code']].tail(100).copy()
        if len(stock_df) < 60:
            continue
        stock_df = create_features(stock_df)
        all_stocks.append(stock_df.iloc[-1:])  # 取最后一行
    
    df_features = pd.concat(all_stocks, ignore_index=True)
    df_features = df_features.dropna(subset=feature_cols)
    print(f"   ✅ 有效股票：{len(df_features)} 只")
    
    # 生成预测
    print(f"\n📈 生成预测...")
    X = df_features[feature_cols].values
    
    if models:
        # 集成预测
        preds = []
        for name, model in models.items():
            pred = model.predict_proba(X)[:, 1]
            preds.append(pred)
        probabilities = np.mean(preds, axis=0)
    else:
        # 简化预测：使用动量排序
        probabilities = df_features['price_momentum'].fillna(0).values / 100
        probabilities = (probabilities - probabilities.min()) / (probabilities.max() - probabilities.min())
    
    # 添加预测结果
    df_features['probability'] = probabilities
    df_features['predicted_gain'] = probabilities * 10  # 估算涨幅
    
    # 排序取前 10
    top10 = df_features.nlargest(10, 'probability').reset_index(drop=True)
    
    # 输出结果
    print(f"\n{'='*80}")
    print(f"🏆 明日涨幅最高前十股票推荐")
    print(f"{'='*80}")
    print(f"{'排名':<4} {'代码':<10} {'名称':<15} {'现价':<10} {'预测涨幅':<10} {'概率':<10} {'行业':<15}")
    print(f"{'='*80}")
    
    results = []
    for i, row in top10.iterrows():
        stock_name = row.get('stock_name', 'N/A')
        industry = row.get('industry', 'N/A')
        
        result = {
            'rank': i + 1,
            'stock_code': row['stock_code'],
            'stock_name': stock_name,
            'current_price': round(row['close'], 2),
            'predicted_gain': round(row['predicted_gain'], 2),
            'probability': round(row['probability'] * 100, 1),
            'industry': industry
        }
        results.append(result)
        
        print(f"{i+1:<4} {row['stock_code']:<10} {stock_name:<15} {row['close']:<10.2f} {row['predicted_gain']:<10.2f}% {row['probability']*100:<10.1f}% {industry:<15}")
    
    print(f"{'='*80}")
    print(f"\n⚠️  风险提示：")
    print(f"   1. 预测基于历史数据和技术指标，不构成投资建议")
    print(f"   2. 股市有风险，投资需谨慎")
    print(f"   3. 建议结合基本面、消息面综合判断")
    print(f"   4. 设置止损位，控制仓位风险")
    
    # 保存结果
    output_dir = '/home/admin/Downloads/workspace/predictions'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f'top10_prediction_{datetime.now().strftime("%Y%m%d")}.json')
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'model': 'ensemble_v25',
            'threshold': CONFIG['threshold'],
            'top10': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存：{output_file}")
    
    return results

if __name__ == '__main__':
    generate_top10()
