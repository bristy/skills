#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习股票预测系统 v22.0
基于 LightGBM/XGBoost
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

CONFIG = {
    'data_file': '/home/admin/openclaw/workspace/chinese-stock-dataset/chinese-stock-dataset.csv',
    'model_dir': '/home/admin/openclaw/workspace/stock_system/ml_models',
    'target_days': 1,  # v23: 次日
    'target_gain': 5.0,  # v23: 5%
    'prob_threshold': 0.45  # v23: 降低阈值提高召回
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
    return [
        'ma_5_ratio', 'ma_10_ratio', 'ma_20_ratio', 'ma_60_ratio',
        'ma_bullish', 'ret_1d', 'ret_3d', 'ret_5d', 'ret_10d', 'ret_20d',
        'mom_accel', 'rsi', 'macd', 'macd_signal', 'macd_hist',
        'vol_ratio', 'money_flow_change', 'volatility_5d', 'volatility_10d',
        'volatility_20d', 'breakout', 'breakdown', 'position_20d'
    ]

def load_stocks():
    stock_file = os.path.join(os.path.dirname(__file__), 'stocks.json')
    if os.path.exists(stock_file):
        with open(stock_file, 'r') as f:
            return json.load(f)
    return []

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

def train_universal_model():
    """训练通用模型（使用所有历史数据）"""
    print("="*80)
    print("🤖 训练机器学习模型")
    print("="*80)
    
    if not (HAS_LGB or HAS_XGB):
        print("\n❌ 请安装机器学习库：pip install lightgbm xgboost")
        return None
    
    print(f"\n📊 加载数据集...")
    df = pd.read_csv(CONFIG['data_file'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(['stock_code', 'date'])
    print(f"   记录数：{len(df):,} 条 | 股票数：{df['stock_code'].nunique():,} 只")
    
    # 采样股票加速训练
    stocks = df['stock_code'].unique()
    sample_size = min(100, len(stocks))
    np.random.seed(42)
    sampled_stocks = np.random.choice(stocks, sample_size, replace=False)
    
    print(f"\n🔧 训练配置:")
    print(f"   模型：LightGBM")
    print(f"   目标：{CONFIG['target_days']}日上涨{CONFIG['target_gain']}%+")
    print(f"   训练股票：{sample_size} 只")
    
    # 合并数据
    all_data = df[df['stock_code'].isin(sampled_stocks)]
    all_data = create_features(all_data).dropna()
    
    feature_cols = get_feature_columns()
    X = all_data[feature_cols]
    y = all_data['target'] = (all_data['close'].shift(-CONFIG['target_days']) / all_data['close'] - 1 >= CONFIG['target_gain'] / 100).astype(int)
    
    # 划分训练集
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # 训练
    params = {
        'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
        'num_leaves': 31, 'learning_rate': 0.05, 'verbose': -1, 'seed': 42,
        'scale_pos_weight': (y_train == 0).sum() / (y_train == 1).sum() if (y_train == 1).sum() > 0 else 1
    }
    
    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    model = lgb.train(
        params, train_data, num_boost_round=500,
        valid_sets=[train_data, valid_data],
        valid_names=['train', 'valid'],
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(0)]
    )
    
    # 评估
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    y_pred = (model.predict(X_test) > 0.5).astype(int)
    y_pred_proba = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_pred_proba)
    
    print(f"\n✅ 模型评估:")
    print(f"   准确率：{accuracy:.1%} | 精确率：{precision:.1%} | 召回率：{recall:.1%} | F1: {f1:.1%} | AUC: {auc:.3f}")
    
    # 特征重要性
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importance(importance_type='gain')
    }).sort_values('importance', ascending=False)
    
    print(f"\n📊 TOP 10 特征:")
    for idx, row in importance.head(10).iterrows():
        print(f"   {row['feature']}: {row['importance']:.0f}")
    
    # 保存模型
    os.makedirs(CONFIG['model_dir'], exist_ok=True)
    model.save_model(f"{CONFIG['model_dir']}/stock_lightgbm_v22.txt")
    
    model_info = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model_type': 'lightgbm',
        'target_days': CONFIG['target_days'],
        'target_gain': CONFIG['target_gain'],
        'feature_cols': feature_cols,
        'metrics': {
            'accuracy': round(accuracy, 3),
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1': round(f1, 3),
            'auc': round(auc, 3)
        },
        'training_stocks': sample_size
    }
    
    with open(f"{CONFIG['model_dir']}/model_info.json", 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print(f"\n✅ 模型已保存：{CONFIG['model_dir']}/stock_lightgbm_v22.txt")
    
    return model

def run_prediction(model=None):
    """运行预测"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"🤖 机器学习股票预测 v22.0 - {ts}")
    print("="*80)
    
    if model is None:
        # 加载模型
        model_file = f"{CONFIG['model_dir']}/stock_lightgbm_v22.txt"
        if os.path.exists(model_file):
            model = lgb.Booster(model_file=model_file)
            print(f"\n✅ 加载模型：{model_file}")
        else:
            print(f"\n⚠️  模型不存在，先训练...")
            model = train_universal_model()
            if model is None:
                return
    
    feature_cols = get_feature_columns()
    stocks = load_stocks()
    
    if not stocks:
        print("\n❌ 未找到股票列表")
        return
    
    print(f"\n监控：{len(stocks)} 只股票\n")
    
    results = []
    for i, stock in enumerate(stocks):
        code = stock.get('code', '')
        ts_code = stock.get('ts_code', code[2:])
        name = stock.get('name', '-')
        
        df = fetch_data(code, days=90)
        if df is None or len(df) < 60:
            continue
        
        # 创建特征
        df_feat = create_features(df)
        latest = df_feat.iloc[-1:]
        X = latest[feature_cols]
        
        if X.isnull().any().any():
            continue
        
        # 预测
        prob_up = model.predict(X)[0]
        
        results.append({
            'stock_code': ts_code,
            'stock_name': name,
            'current_price': round(df['close'].iloc[-1], 2),
            'prob_up': round(prob_up, 3),
            'prediction': 'up' if prob_up > CONFIG['prob_threshold'] else 'hold',
            'timestamp': ts
        })
        
        if (i+1) % 50 == 0:
            print(f'进度：{i+1}/{len(stocks)}')
    
    # 筛选并排序
    qualified = [r for r in results if r['prob_up'] >= CONFIG['prob_threshold']]
    qualified.sort(key=lambda x: x['prob_up'], reverse=True)
    
    print('='*80)
    print(f'筛选结果：{len(qualified)} 只股票符合 5 日涨{CONFIG["target_gain"]}%+ 条件\n')
    
    print('📈 TOP 20 推荐:')
    print('-'*80)
    for i, r in enumerate(qualified[:20], 1):
        stars = '⭐' * int(r['prob_up'] * 5)
        print(f'{i:2}. {r["stock_name"]} ({r["stock_code"]})')
        print(f'    现价：{r["current_price"]:.2f} | 上涨概率：{r["prob_up"]:.1%} {stars}')
        print(f'    预测：5 日涨幅 {CONFIG["target_gain"]}%+')
        print()
    
    # 保存
    out_dir = '/home/admin/openclaw/workspace/stock-recommendations'
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    with open(f'{out_dir}/ml_prediction_{date_str}.json', 'w') as f:
        json.dump({
            'timestamp': ts,
            'model': 'LightGBM',
            'target': f'{CONFIG["target_days"]}日上涨{CONFIG["target_gain"]}%+',
            'prob_threshold': CONFIG['prob_threshold'],
            'total_screened': len(results),
            'qualified': len(qualified),
            'top_20': qualified[:20]
        }, f, indent=2, ensure_ascii=False)
    
    print(f'✅ 推荐已保存：{out_dir}/ml_prediction_{date_str}.json')
    
    return qualified[:20]

if __name__ == '__main__':
    import requests
    if not HAS_LGB and not HAS_XGB:
        print("❌ 请先安装机器学习库：pip install lightgbm xgboost scikit-learn")
    else:
        # 先训练（如果模型不存在）
        model_file = f"{CONFIG['model_dir']}/stock_lightgbm_v22.txt"
        if not os.path.exists(model_file):
            model = train_universal_model()
        else:
            model = lgb.Booster(model_file=model_file)
        
        # 运行预测
        run_prediction(model)
