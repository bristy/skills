#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测与验证系统 v25.0
优化版 - 目标准确率 90%+
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
    print("❌ 请安装：pip install lightgbm")

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import xgboost as xgb

# ========== 优化配置 ==========
CONFIG = {
    'data_file': '/home/admin/Downloads/workspace/chinese-stock-dataset/chinese-stock-dataset.csv',
    'predictions_dir': '/home/admin/Downloads/workspace/predictions',
    'model_dir': '/home/admin/openclaw/workspace/skills/stock-predictor-pro/ml_models',
    'target_days': 1,
    'target_gain': 5.0,
    'prob_threshold': 0.35,  # 降低阈值提高召回率
    'sample_stocks': 200,    # 增加训练股票数
    'use_ensemble': True,    # 使用集成模型
    'optimize_features': True  # 特征优化
}

def create_features(df):
    """创建优化特征"""
    df = df.copy().sort_values('date').reset_index(drop=True)
    
    # 均线系统
    for period in [5, 10, 20, 60]:
        df[f'ma_{period}'] = df['close'].rolling(period).mean()
        df[f'ma_{period}_ratio'] = df['close'] / df[f'ma_{period}'] - 1
    
    # 均线多头排列
    df['ma_5_10'] = (df['ma_5'] > df['ma_10']).astype(int)
    df['ma_10_20'] = (df['ma_10'] > df['ma_20']).astype(int)
    df['ma_20_60'] = (df['ma_20'] > df['ma_60']).astype(int)
    df['ma_bullish'] = df['ma_5_10'] + df['ma_10_20'] + df['ma_20_60']
    
    # 收益率动量
    for period in [1, 3, 5, 10, 20, 30]:
        df[f'ret_{period}d'] = df['close'].pct_change(period) * 100
    
    # 动量加速度
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
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['vol_ma5'] / df['vol_ma20']
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['money_flow'] = df['typical_price'] * df['volume']
        df['money_flow_ma5'] = df['money_flow'].rolling(5).mean()
        df['money_flow_change'] = (df['money_flow'] - df['money_flow_ma5'].shift(5))
        df['money_flow_change'] = df['money_flow_change'] / df['money_flow_ma5'].shift(5)
    
    # 波动率
    for period in [5, 10, 20]:
        df[f'volatility_{period}d'] = df['close'].pct_change().rolling(period).std() * np.sqrt(252) * 100
    
    # 突破信号
    df['high_20d'] = df['high'].rolling(20).max()
    df['low_20d'] = df['low'].rolling(20).min()
    df['breakout'] = (df['close'] > df['high_20d'].shift(1)).astype(int)
    df['breakdown'] = (df['close'] < df['low_20d'].shift(1)).astype(int)
    df['position_20d'] = (df['close'] - df['low_20d']) / (df['high_20d'] - df['low_20d'])
    
    # 新增：价格动量
    df['price_momentum'] = (df['close'] - df['close'].shift(10)) / df['close'].shift(10) * 100
    
    # 新增：相对强度
    df['relative_strength'] = df['close'] / df['close'].shift(20) - 1
    
    # 目标变量
    df['target'] = (df['close'].shift(-CONFIG['target_days']) / df['close'] - 1 >= CONFIG['target_gain'] / 100).astype(int)
    
    return df

def get_feature_columns():
    """获取特征列"""
    return [
        'ma_5_ratio', 'ma_10_ratio', 'ma_20_ratio', 'ma_60_ratio',
        'ma_bullish', 'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d', 'ret_30d',
        'mom_accel', 'mom_accel_2', 'rsi', 'macd', 'macd_signal', 'macd_hist',
        'vol_ratio', 'money_flow_change', 'volatility_5d', 'volatility_10d', 'volatility_20d',
        'breakout', 'breakdown', 'position_20d', 'price_momentum', 'relative_strength'
    ]

def train_ensemble_model(X_train, y_train, X_val, y_val):
    """训练集成模型"""
    models = {}
    predictions = {}
    
    # LightGBM
    lgb_params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'n_estimators': 500,
        'class_weight': 'balanced'
    }
    lgb_model = lgb.LGBMClassifier(**lgb_params)
    lgb_model.fit(X_train, y_train)
    models['lgb'] = lgb_model
    predictions['lgb'] = lgb_model.predict_proba(X_val)[:, 1]
    
    # XGBoost
    xgb_params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'learning_rate': 0.05,
        'n_estimators': 500,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'scale_pos_weight': sum(y_train == 0) / sum(y_train == 1)
    }
    xgb_model = xgb.XGBClassifier(**xgb_params)
    xgb_model.fit(X_train, y_train)
    models['xgb'] = xgb_model
    predictions['xgb'] = xgb_model.predict_proba(X_val)[:, 1]
    
    # Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    models['rf'] = rf_model
    predictions['rf'] = rf_model.predict_proba(X_val)[:, 1]
    
    # 集成预测 (平均)
    ensemble_pred = np.mean([predictions['lgb'], predictions['xgb'], predictions['rf']], axis=0)
    
    return models, ensemble_pred

def train_model():
    """训练模型"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"🤖 训练次日涨 5%+ 模型 v25.0 (优化版) - {ts}")
    print("="*80)
    
    print(f"\n📊 加载数据集...")
    # 使用 error_bad_lines=False 跳过错误行
    df = pd.read_csv(CONFIG['data_file'], on_bad_lines='skip')
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(['stock_code', 'date']).reset_index(drop=True)
    print(f"   记录数：{len(df):,} 条 | 股票数：{df['stock_code'].nunique():,} 只")
    
    # 采样股票
    stocks = df['stock_code'].unique()
    sample_size = min(CONFIG['sample_stocks'], len(stocks))
    np.random.seed(42)
    sampled_stocks = np.random.choice(stocks, sample_size, replace=False)
    df_sample = df[df['stock_code'].isin(sampled_stocks)].copy()
    
    print(f"\n🔧 训练配置:")
    print(f"   模型：集成 (LightGBM + XGBoost + RF)")
    print(f"   目标：次日上涨{CONFIG['target_gain']}%+")
    print(f"   训练股票：{sample_size} 只")
    print(f"   概率阈值：{CONFIG['prob_threshold']}")
    
    print(f"\n🔧 特征工程...")
    feature_cols = get_feature_columns()
    all_stocks = []
    
    for stock in sampled_stocks:
        stock_df = df_sample[df_sample['stock_code'] == stock].copy()
        if len(stock_df) < 100:
            continue
        stock_df = create_features(stock_df)
        all_stocks.append(stock_df)
    
    df_features = pd.concat(all_stocks, ignore_index=True)
    df_features = df_features.dropna(subset=feature_cols + ['target'])
    
    print(f"   有效样本：{len(df_features):,} 条")
    print(f"   正样本：{sum(df_features['target'] == 1):,} ({100*df_features['target'].mean():.1f}%)")
    print(f"   负样本：{sum(df_features['target'] == 0):,} ({100*(1-df_features['target'].mean()):.1f}%)")
    
    X = df_features[feature_cols]
    y = df_features['target']
    
    # 时间序列分割
    split_idx = int(len(df_features) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"\n📈 训练模型...")
    models, ensemble_pred = train_ensemble_model(
        X_train.values, y_train.values,
        X_test.values, y_test.values
    )
    
    # 评估
    threshold = CONFIG['prob_threshold']
    y_pred = (ensemble_pred >= threshold).astype(int)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, ensemble_pred)
    
    print(f"\n📊 模型评估 (测试集):")
    print(f"   准确率 (Accuracy): {100*accuracy:.2f}%")
    print(f"   精确率 (Precision): {100*precision:.2f}%")
    print(f"   召回率 (Recall): {100*recall:.2f}%")
    print(f"   F1 分数：{f1:.4f}")
    print(f"   AUC: {auc:.4f}")
    
    # 混淆矩阵
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n   混淆矩阵:")
    print(f"   [[TN={cm[0,0]:,}, FP={cm[0,1]:,}],")
    print(f"    [FN={cm[1,0]:,}, TP={cm[1,1]:,}]]")
    
    # 保存模型
    os.makedirs(CONFIG['model_dir'], exist_ok=True)
    model_path = os.path.join(CONFIG['model_dir'], 'ensemble_v25.pkl')
    import pickle
    with open(model_path, 'wb') as f:
        pickle.dump({'models': models, 'feature_cols': feature_cols, 'config': CONFIG}, f)
    print(f"\n💾 模型已保存：{model_path}")
    
    # 检查是否达标
    if accuracy < 0.90:
        print(f"\n⚠️  准确率 {100*accuracy:.2f}% < 90%，需要进一步优化")
        print(f"   建议：调整阈值、增加特征、使用更多数据")
    else:
        print(f"\n✅ 准确率 {100*accuracy:.2f}% ≥ 90%，达标！")
    
    return models, feature_cols, df_features

if __name__ == '__main__':
    train_model()
