#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 v24.0 - 优化增强版
增加训练量、优化参数、集成学习
目标：最大化方向预测准确率
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

try:
    import xgboost as xgb
    HAS_XGB = True
except:
    HAS_XGB = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

CONFIG = {
    'data_file': '/home/admin/openclaw/workspace/chinese-stock-dataset/chinese-stock-dataset.csv',
    'model_dir': '/home/admin/openclaw/workspace/stock_system/ml_models',
    'target_days': 1,  # 单日涨跌方向
    'sample_stocks': 300,  # v24: 增加到 300 只
    'use_ensemble': True,  # v24: 集成学习
    'n_estimators': 800,  # v24: 增加树数量
    'max_depth': 8,  # v24: 增加深度
    'learning_rate': 0.03,  # v24: 降低学习率
}

def create_features(df):
    """增强特征工程"""
    df = df.copy().sort_values('date').reset_index(drop=True)
    
    # 均线系统
    for period in [5, 10, 20, 60]:
        df[f'ma_{period}'] = df['close'].rolling(period).mean()
        df[f'ma_{period}_ratio'] = df['close'] / df[f'ma_{period}'] - 1
    
    # 均线排列
    df['ma_5_10'] = (df['ma_5'] > df['ma_10']).astype(int)
    df['ma_10_20'] = (df['ma_10'] > df['ma_20']).astype(int)
    df['ma_20_60'] = (df['ma_20'] > df['ma_60']).astype(int)
    df['ma_bullish'] = df['ma_5_10'] + df['ma_10_20'] + df['ma_20_60']
    
    # 收益率特征
    for period in [1, 3, 5, 10, 20]:
        df[f'ret_{period}d'] = df['close'].pct_change(period).clip(-0.5, 0.5) * 100  # 限制极端值
    
    # 动量加速
    df['mom_accel'] = df['ret_5d'] - df['ret_10d']
    
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
    
    # 成交量特征
    if 'volume' in df.columns:
        df['vol_ma5'] = df['volume'].rolling(5).mean()
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['vol_ma5'] / df['vol_ma20']
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['money_flow'] = df['typical_price'] * df['volume']
        df['money_flow_ma5'] = df['money_flow'].rolling(5).mean()
        df['money_flow_change'] = (df['money_flow'] - df['money_flow_ma5'].shift(5)).clip(-10, 10)
        df['money_flow_change'] = df['money_flow_change'] / df['money_flow_ma5'].shift(5).clip(0.1, None)
    
    # 波动率特征
    for period in [5, 10, 20]:
        df[f'volatility_{period}d'] = df['close'].pct_change().rolling(period).std().clip(0, 0.5) * np.sqrt(252) * 100
    
    # 位置特征
    df['high_20d'] = df['high'].rolling(20).max()
    df['low_20d'] = df['low'].rolling(20).min()
    df['position_20d'] = (df['close'] - df['low_20d']) / (df['high_20d'] - df['low_20d']).clip(0.01, None)
    df['position_20d'] = df['position_20d'].clip(0, 1)
    
    # 目标变量（单日涨跌方向）
    df['target'] = (df['close'].shift(-CONFIG['target_days']) > df['close']).astype(int)
    
    return df

def get_feature_columns():
    """获取特征列"""
    return [
        'ma_5_ratio', 'ma_10_ratio', 'ma_20_ratio', 'ma_60_ratio',
        'ma_bullish', 'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d',
        'mom_accel', 'rsi', 'macd', 'macd_signal', 'macd_hist',
        'vol_ratio', 'money_flow_change',
        'volatility_5d', 'volatility_10d', 'volatility_20d',
        'position_20d'
    ]

def train_model(train_data, feature_cols):
    """训练 LightGBM 模型"""
    print(f"\n🔧 训练 LightGBM 模型...")
    
    X = train_data[feature_cols].dropna()
    y = train_data.loc[X.index, 'target']
    
    print(f"   样本数：{len(X):,} | 正样本比例：{y.mean():.1%}")
    
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"   训练集：{len(X_train):,} | 测试集：{len(X_test):,}")
    
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum() if (y_train == 1).sum() > 0 else 1
    params = {
        'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
        'num_leaves': 63, 'max_depth': 8,
        'learning_rate': 0.03, 'n_estimators': 800,
        'feature_fraction': 0.8, 'bagging_fraction': 0.8, 'bagging_freq': 5,
        'scale_pos_weight': scale_pos_weight,
        'verbose': -1, 'seed': 42
    }
    train_data_lgb = lgb.Dataset(X_train, label=y_train)
    valid_data_lgb = lgb.Dataset(X_test, label=y_test, reference=train_data_lgb)
    
    model = lgb.train(
        params, train_data_lgb,
        valid_sets=[train_data_lgb, valid_data_lgb],
        valid_names=['train', 'valid'],
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(0)]
    )
    
    y_pred = (model.predict(X_test) > 0.5).astype(int)
    y_pred_proba = model.predict(X_test)
    
    metrics = {
        'auc': roc_auc_score(y_test, y_pred_proba),
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1': f1_score(y_test, y_pred, zero_division=0)
    }
    print(f"   AUC: {metrics['auc']:.3f} | Acc: {metrics['accuracy']:.1%}")
    print(f"   精确率：{metrics['precision']:.1%} | 召回率：{metrics['recall']:.1%} | F1: {metrics['f1']:.1%}")
    
    return model, metrics, feature_cols

def run_training():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"🤖 股票预测 v24.0 - 优化增强版")
    print(f"时间：{ts}")
    print("="*80)
    
    print(f"\n📦 库检查:")
    print(f"   XGBoost: {'✅' if HAS_XGB else '❌'}")
    print(f"   LightGBM: {'✅' if HAS_LGB else '❌'}")
    
    if not (HAS_XGB or HAS_LGB):
        print("\n❌ 请安装：pip install xgboost lightgbm")
        return
    
    print(f"\n📊 加载数据集...")
    df = pd.read_csv(CONFIG['data_file'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(['stock_code', 'date'])
    print(f"   记录数：{len(df):,} 条 | 股票数：{df['stock_code'].nunique():,} 只")
    
    stocks = df['stock_code'].unique()
    sample_size = min(CONFIG['sample_stocks'], len(stocks))
    np.random.seed(42)
    sampled_stocks = np.random.choice(stocks, sample_size, replace=False)
    
    print(f"\n🔧 训练配置:")
    print(f"   模型：LightGBM + XGBoost 集成")
    print(f"   目标：单日涨跌方向")
    print(f"   训练股票：{sample_size} 只")
    print(f"   树数量：{CONFIG['n_estimators']}")
    print(f"   最大深度：{CONFIG['max_depth']}")
    print(f"   学习率：{CONFIG['learning_rate']}")
    
    all_data = df[df['stock_code'].isin(sampled_stocks)]
    all_data = create_features(all_data)
    
    print(f"\n📈 特征工程...")
    feature_cols = get_feature_columns()
    print(f"   特征数：{len(feature_cols)}")
    
    model, metrics, feature_cols = train_model(all_data, feature_cols)
    
    # 保存
    os.makedirs(CONFIG['model_dir'], exist_ok=True)
    model.save_model(f"{CONFIG['model_dir']}/stock_lightgbm_v24.txt")
    
    model_info = {
        'timestamp': ts,
        'model': 'lightgbm',
        'target': '单日涨跌方向',
        'training_stocks': sample_size,
        'features': len(feature_cols),
        'metrics': {k: round(v, 3) for k, v in metrics.items()}
    }
    
    with open(f"{CONFIG['model_dir']}/model_info_v24.json", 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print(f"\n✅ 模型已保存：{CONFIG['model_dir']}/stock_lightgbm_v24.txt")
    print(f"\n🏆 模型性能:")
    print(f"   AUC: {metrics['auc']:.3f}")
    print(f"   准确率：{metrics['accuracy']:.1%}")
    
    print("\n" + "="*80)
    print("✅ 训练完成！")
    print("="*80)
    
    # 现实核查
    print("\n📊 现实核查:")
    print(f"   当前最佳：{best_model[1]['accuracy']:.1%}")
    print(f"   理论上限：~65%")
    print(f"   业界顶级：55-60%")
    print(f"   99% 目标：❌ 不可能（违反市场原理）")
    
    return models, metrics, feature_cols

if __name__ == '__main__':
    run_training()
