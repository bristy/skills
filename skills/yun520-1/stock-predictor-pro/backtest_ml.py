#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习策略回测验证
对比：传统方法 vs 机器学习
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import warnings
warnings.filterwarnings('ignore')

try:
    import lightgbm as lgb
    HAS_LGB = True
except:
    HAS_LGB = False

try:
    import xgboost as xgb
    HAS_XGB = True
except:
    HAS_XGB = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

CONFIG = {
    'data_file': '/home/admin/openclaw/workspace/chinese-stock-dataset/chinese-stock-dataset.csv',
    'test_days': 30,
    'sample_stocks': 100,
    'target_days': 5,
    'target_gain': 3.0,
    'lookback_days': 30
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
    df['macd_cross'] = (df['macd'] > df['macd_signal']).astype(int)
    
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
    
    df['target'] = (df['close'].shift(-CONFIG['target_days']) / df['close'] - 1 >= CONFIG['target_gain'] / 100).astype(int)
    
    return df

def get_feature_columns():
    return [
        'ma_5_ratio', 'ma_10_ratio', 'ma_20_ratio', 'ma_60_ratio',
        'ma_bullish', 'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d',
        'mom_accel', 'rsi', 'macd', 'macd_signal', 'macd_hist', 'macd_cross',
        'vol_ratio', 'money_flow_change', 'volatility_5d', 'volatility_10d',
        'volatility_20d', 'breakout', 'breakdown', 'position_20d'
    ]

def predict_traditional(df):
    """传统方法预测"""
    if len(df) < 30:
        return {'prob_up': 0.5, 'prediction': 'down'}
    
    df_feat = create_features(df)
    latest = df_feat.iloc[-1]
    
    # 简化版传统策略
    score = 0
    if latest['ma_bullish'] >= 3: score += 2
    if latest['rsi'] < 30: score += 2
    elif latest['rsi'] > 70: score -= 2
    if latest['vol_ratio'] > 1.5: score += 1
    if latest['breakout'] == 1: score += 2
    if latest['money_flow_change'] > 0.2: score += 1
    
    prob_up = 1 / (1 + np.exp(-score))  # sigmoid
    
    return {
        'prob_up': round(prob_up, 3),
        'prediction': 'up' if prob_up > 0.5 else 'down'
    }

def run_backtest():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"机器学习 vs 传统方法 回测对比")
    print(f"时间：{ts}")
    print("="*80)
    
    print(f"\n📊 加载数据集...")
    df = pd.read_csv(CONFIG['data_file'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(['stock_code', 'date'])
    print(f"   记录数：{len(df):,} 条 | 股票数：{df['stock_code'].nunique():,} 只")
    
    max_date = df['date'].max()
    min_date = max_date - timedelta(days=CONFIG['test_days'])
    
    print(f"\n📅 回测期间：{min_date.date()} - {max_date.date()} ({CONFIG['test_days']}天)")
    print(f"🎯 目标：{CONFIG['target_days']}日上涨{CONFIG['target_gain']}%+")
    
    stocks = df['stock_code'].unique()
    if len(stocks) > CONFIG['sample_stocks']:
        np.random.seed(42)
        stocks = np.random.choice(stocks, CONFIG['sample_stocks'], replace=False)
    print(f"   样本股票：{len(stocks)} 只\n")
    
    # 准备训练数据（回测期间之前的数据）
    train_end = min_date - timedelta(days=30)
    train_df = df[(df['date'] <= train_end)]
    
    print(f"🔧 训练机器学习模型...")
    train_stocks = np.random.choice(stocks, min(50, len(stocks)), replace=False)
    train_data = train_df[train_df['stock_code'].isin(train_stocks)]
    train_data = create_features(train_data).dropna()
    
    feature_cols = get_feature_columns()
    X_train = train_data[feature_cols]
    y_train = train_data['target']
    
    if HAS_LGB:
        params = {
            'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
            'num_leaves': 31, 'learning_rate': 0.05, 'verbose': -1, 'seed': 42
        }
        train_dataset = lgb.Dataset(X_train, label=y_train)
        model = lgb.train(params, train_dataset, num_boost_round=200)
        print(f"   ✅ LightGBM 模型训练完成")
    else:
        model = None
        print(f"   ⚠️  LightGBM 不可用，仅测试传统方法")
    
    print(f"\n🔍 开始回测...\n")
    
    ml_signals = []
    traditional_signals = []
    
    for i, stock in enumerate(stocks):
        stock_df = df[df['stock_code'] == stock].sort_values('date')
        if len(stock_df) < 60:
            continue
        
        test_period = stock_df[(stock_df['date'] >= min_date) & (stock_df['date'] <= max_date)]
        
        for idx, row in test_period.iterrows():
            signal_date = row['date']
            signal_idx = stock_df.index.get_loc(idx)
            
            if signal_idx < 30 or signal_idx >= len(stock_df) - CONFIG['target_days']:
                continue
            
            hist_df = stock_df.iloc[:signal_idx]
            
            # 机器学习预测
            if model:
                df_feat = create_features(hist_df)
                latest = df_feat.iloc[-1:]
                X = latest[feature_cols]
                if not X.isnull().any().any():
                    prob_up = model.predict(X)[0]
                    ml_pred = 'up' if prob_up > 0.5 else 'down'
                else:
                    continue
            else:
                continue
            
            # 传统方法预测
            trad_pred = predict_traditional(hist_df)
            
            # 实际结果
            future_close = stock_df.iloc[signal_idx + CONFIG['target_days']]['close']
            current_close = row['close']
            actual_gain = (future_close - current_close) / current_close * 100
            actual_up = 1 if actual_gain >= CONFIG['target_gain'] else 0
            
            if ml_pred == 'up' and trad_pred['prediction'] == 'up':
                ml_signals.append({
                    'stock_code': stock, 'date': signal_date,
                    'prob_up': round(prob_up, 3),
                    'actual_gain': round(actual_gain, 2),
                    'actual_up': actual_up
                })
                traditional_signals.append({
                    'stock_code': stock, 'date': signal_date,
                    'prob_up': trad_pred['prob_up'],
                    'actual_gain': round(actual_gain, 2),
                    'actual_up': actual_up
                })
        
        if (i+1) % 20 == 0:
            print(f"   进度：{i+1}/{len(stocks)}")
    
    print("\n" + "="*80)
    print("📊 回测结果对比")
    print("="*80)
    
    def evaluate(signals, name):
        if not signals:
            print(f"\n{name}: 无信号")
            return None
        
        df_sig = pd.DataFrame(signals)
        total = len(df_sig)
        
        # 按概率分组
        high_prob = df_sig[df_sig['prob_up'] >= 0.7]
        mid_prob = df_sig[(df_sig['prob_up'] >= 0.5) & (df_sig['prob_up'] < 0.7)]
        
        success = len(df_sig[df_sig['actual_up'] == 1])
        success_rate = success / total * 100
        avg_gain = df_sig['actual_gain'].mean()
        
        print(f"\n{name}:")
        print(f"   总信号：{total}")
        print(f"   成功率：{success_rate:.1f}% ({success}/{total})")
        print(f"   平均涨幅：{avg_gain:.2f}%")
        
        if len(high_prob) > 0:
            hp_success = len(high_prob[high_prob['actual_up'] == 1]) / len(high_prob) * 100
            hp_avg = high_prob['actual_gain'].mean()
            print(f"   高概率 (>=70%): {len(high_prob)} 个，成功率 {hp_success:.1f}%, 平均涨幅 {hp_avg:.2f}%")
        
        return {
            'total': total, 'success': success, 'success_rate': success_rate,
            'avg_gain': avg_gain
        }
    
    ml_stats = evaluate(ml_signals, "🤖 机器学习 (LightGBM)")
    trad_stats = evaluate(traditional_signals, "📐 传统方法")
    
    if ml_stats and trad_stats:
        print("\n" + "="*80)
        print("🎯 对比结论")
        print("="*80)
        
        improve = ml_stats['success_rate'] - trad_stats['success_rate']
        gain_improve = ml_stats['avg_gain'] - trad_stats['avg_gain']
        
        print(f"\n成功率提升：{trad_stats['success_rate']:.1f}% → {ml_stats['success_rate']:.1f}% ({improve:+.1f}%)")
        print(f"平均涨幅提升：{trad_stats['avg_gain']:.2f}% → {ml_stats['avg_gain']:.2f}% ({gain_improve:+.2f}%)")
        
        if improve > 10:
            print(f"\n🎉 机器学习大幅超越传统方法！")
        elif improve > 5:
            print(f"\n✅ 机器学习优于传统方法")
        elif improve > 0:
            print(f"\n⚖️  机器学习略有优势")
        else:
            print(f"\n⚠️  机器学习未展现优势")
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    result_file = f"{output_dir}/backtest_ml_vs_traditional_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': ts,
            'config': CONFIG,
            'ml': ml_stats,
            'traditional': trad_stats
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 结果已保存：{result_file}")
    print("\n✅ 回测完成！")

if __name__ == '__main__':
    run_backtest()
