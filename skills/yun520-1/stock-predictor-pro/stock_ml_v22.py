#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 v22.0 - 机器学习版 (XGBoost/LightGBM)
基于 2200 万条历史数据训练
特征：技术指标 + 动量 + 成交量 + 波动率
目标：5 日上涨 3%+ 分类预测
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import warnings
warnings.filterwarnings('ignore')

# 尝试导入机器学习库
try:
    import xgboost as xgb
    HAS_XGB = True
except:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGB = True
except:
    HAS_LGB = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

CONFIG = {
    'data_file': '/home/admin/openclaw/workspace/chinese-stock-dataset/chinese-stock-dataset.csv',
    'model_dir': '/home/admin/openclaw/workspace/stock_system/ml_models',
    'target_days': 1,  # v23: 改为次日 (1 日)
    'target_gain': 5.0,  # v23: 目标涨幅 5%
    'lookback_days': 30,
    'test_size': 0.2,
    'model_type': 'lightgbm'
}

def create_features(df):
    """
    创建特征工程
    """
    df = df.copy().sort_values('date').reset_index(drop=True)
    
    # 基础均线
    for period in [5, 10, 20, 60]:
        df[f'ma_{period}'] = df['close'].rolling(period).mean()
        df[f'ma_{period}_ratio'] = df['close'] / df[f'ma_{period}'] - 1
    
    # 均线排列
    df['ma_5_10'] = (df['ma_5'] > df['ma_10']).astype(int)
    df['ma_10_20'] = (df['ma_10'] > df['ma_20']).astype(int)
    df['ma_20_60'] = (df['ma_20'] > df['ma_60']).astype(int)
    df['ma_bullish'] = df['ma_5_10'] + df['ma_10_20'] + df['ma_20_60']  # 0-3
    
    # 收益率特征
    for period in [1, 3, 5, 10, 20]:
        df[f'ret_{period}d'] = df['close'].pct_change(period) * 100
    
    # 动量加速
    df['mom_accel'] = df['ret_5d'] - df['ret_10d']
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50).clip(0, 100)
    
    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    df['macd_cross'] = (df['macd'] > df['macd_signal']).astype(int)
    
    # 成交量特征
    if 'volume' in df.columns:
        df['vol_ma5'] = df['volume'].rolling(5).mean()
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['vol_ma5'] / df['vol_ma20']
        
        # 资金流
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['money_flow'] = df['typical_price'] * df['volume']
        df['money_flow_ma5'] = df['money_flow'].rolling(5).mean()
        df['money_flow_change'] = (df['money_flow'] - df['money_flow_ma5'].shift(5)) / df['money_flow_ma5'].shift(5)
    
    # 波动率特征
    for period in [5, 10, 20]:
        df[f'volatility_{period}d'] = df['close'].pct_change().rolling(period).std() * np.sqrt(252) * 100
    
    # 突破特征
    df['high_20d'] = df['high'].rolling(20).max()
    df['low_20d'] = df['low'].rolling(20).min()
    df['breakout'] = (df['close'] > df['high_20d'].shift(1)).astype(int)
    df['breakdown'] = (df['close'] < df['low_20d'].shift(1)).astype(int)
    
    # 位置特征
    df['position_20d'] = (df['close'] - df['low_20d']) / (df['high_20d'] - df['low_20d'])
    
    # 目标变量（5 日后是否涨 3%+）
    df['target'] = (df['close'].shift(-CONFIG['target_days']) / df['close'] - 1 >= CONFIG['target_gain'] / 100).astype(int)
    
    return df

def get_feature_columns():
    """获取特征列名"""
    return [
        'ma_5_ratio', 'ma_10_ratio', 'ma_20_ratio', 'ma_60_ratio',
        'ma_bullish',
        'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d',
        'mom_accel',
        'rsi',
        'macd', 'macd_signal', 'macd_hist', 'macd_cross',
        'vol_ratio', 'money_flow_change',
        'volatility_5d', 'volatility_10d', 'volatility_20d',
        'breakout', 'breakdown',
        'position_20d'
    ]

def train_model(stock_data, model_type='lightgbm'):
    """
    训练模型
    """
    print(f"\n🔧 训练 {model_type.upper()} 模型...")
    
    # 创建特征
    df = create_features(stock_data)
    
    # 删除 NaN
    df = df.dropna()
    
    if len(df) < 1000:
        print(f"   ⚠️  数据量不足 ({len(df)} 条)，跳过")
        return None
    
    feature_cols = get_feature_columns()
    X = df[feature_cols]
    y = df['target']
    
    # 检查类别平衡
    positive_rate = y.mean()
    print(f"   样本数：{len(X)} | 正样本比例：{positive_rate:.1%}")
    
    # 划分训练测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=CONFIG['test_size'], random_state=42, shuffle=False)
    
    # 处理类别不平衡
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum() if (y_train == 1).sum() > 0 else 1
    
    if model_type == 'lightgbm' and HAS_LGB:
        # LightGBM 参数
        params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'scale_pos_weight': scale_pos_weight,
            'verbose': -1,
            'seed': 42
        }
        
        train_data = lgb.Dataset(X_train, label=y_train)
        valid_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[train_data, valid_data],
            valid_names=['train', 'valid'],
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(0)]
        )
        
    elif model_type == 'xgboost' and HAS_XGB:
        # XGBoost 参数
        model = xgb.XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            eval_metric='auc',
            early_stopping_rounds=50,
            random_state=42,
            verbosity=0
        )
        
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    else:
        print(f"   ❌ 未安装 {model_type} 库")
        return None
    
    # 评估
    if model_type == 'lightgbm':
        y_pred = (model.predict(X_test) > 0.5).astype(int)
        y_pred_proba = model.predict(X_test)
    else:
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_test, y_pred_proba)
    except:
        auc = 0.5
    
    print(f"   准确率：{accuracy:.1%} | 精确率：{precision:.1%} | 召回率：{recall:.1%} | F1: {f1:.1%} | AUC: {auc:.3f}")
    
    return {
        'model': model,
        'model_type': model_type,
        'feature_cols': feature_cols,
        'metrics': {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': auc
        }
    }

def predict_with_model(df, model_info):
    """使用模型预测"""
    model = model_info['model']
    model_type = model_info['model_type']
    feature_cols = model_info['feature_cols']
    
    # 创建特征
    df_feat = create_features(df)
    
    # 取最后一行
    latest = df_feat.iloc[-1:]
    X = latest[feature_cols]
    
    if X.isnull().any().any():
        return None
    
    if model_type == 'lightgbm':
        prob_up = model.predict(X)[0]
    else:
        prob_up = model.predict_proba(X)[0, 1]
    
    return {
        'prob_up': round(prob_up, 3),
        'prediction': 'up' if prob_up > 0.5 else 'down'
    }

def run_training():
    """运行训练流程"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测 v22.0 - 机器学习训练")
    print(f"时间：{ts}")
    print("="*80)
    
    # 检查库
    print(f"\n📦 库检查:")
    print(f"   XGBoost: {'✅' if HAS_XGB else '❌'}")
    print(f"   LightGBM: {'✅' if HAS_LGB else '❌'}")
    print(f"   Scikit-learn: ✅")
    
    if not (HAS_XGB or HAS_LGB):
        print("\n❌ 请安装机器学习库:")
        print("   pip install xgboost lightgbm scikit-learn")
        return
    
    # 加载数据
    print(f"\n📊 加载数据集...")
    df = pd.read_csv(CONFIG['data_file'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(['stock_code', 'date'])
    print(f"   记录数：{len(df):,} 条 | 股票数：{df['stock_code'].nunique():,} 只")
    
    # 采样股票（加速训练）
    stocks = df['stock_code'].unique()
    sample_size = min(50, len(stocks))
    np.random.seed(42)
    sampled_stocks = np.random.choice(stocks, sample_size, replace=False)
    
    print(f"\n🔧 训练配置:")
    print(f"   模型类型：{CONFIG['model_type']}")
    print(f"   预测目标：{CONFIG['target_days']}日上涨{CONFIG['target_gain']}%+")
    print(f"   回看天数：{CONFIG['lookback_days']}天")
    print(f"   训练股票：{sample_size} 只")
    
    # 合并所有股票数据
    all_stock_data = df[df['stock_code'].isin(sampled_stocks)]
    
    # 训练模型
    model_info = train_model(all_stock_data, CONFIG['model_type'])
    
    if model_info is None:
        print("\n❌ 训练失败")
        return
    
    # 保存模型
    os.makedirs(CONFIG['model_dir'], exist_ok=True)
    model_file = f"{CONFIG['model_dir']}/stock_ml_{CONFIG['model_type']}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    
    # 保存模型信息（实际项目中应保存模型文件）
    model_save_info = {
        'timestamp': ts,
        'model_type': CONFIG['model_type'],
        'target_days': CONFIG['target_days'],
        'target_gain': CONFIG['target_gain'],
        'feature_cols': model_info['feature_cols'],
        'metrics': model_info['metrics'],
        'training_stocks': len(sampled_stocks)
    }
    
    with open(model_file, 'w') as f:
        json.dump(model_save_info, f, indent=2)
    
    print(f"\n✅ 模型信息已保存：{model_file}")
    print(f"\n📊 特征重要性:")
    
    # 显示特征重要性
    if CONFIG['model_type'] == 'lightgbm' and HAS_LGB:
        importance = pd.DataFrame({
            'feature': model_info['feature_cols'],
            'importance': model_info['model'].feature_importance(importance_type='gain')
        }).sort_values('importance', ascending=False)
    else:
        importance = pd.DataFrame({
            'feature': model_info['feature_cols'],
            'importance': model_info['model'].feature_importances_
        }).sort_values('importance', ascending=False)
    
    for idx, row in importance.head(10).iterrows():
        print(f"   {row['feature']}: {row['importance']:.2f}")
    
    print("\n" + "="*80)
    print("✅ 训练完成！")
    print("="*80)
    
    return model_info

if __name__ == '__main__':
    run_training()
