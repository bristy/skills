#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测模型参数优化系统 v4.0
核心目标：通过回测找到最优参数，提高预测成功率

方法：
1. 网格搜索参数空间
2. 对每组参数进行回测
3. 选择方向正确率最高的参数组合
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# ============== 参数空间 ==============
PARAM_GRID = {
    'trend_weight': [0.4, 0.6, 0.8, 1.0],
    'momentum_weight': [0.1, 0.2, 0.3],
    'volatility_threshold': [20, 30, 40],
    'conservative_factor': [0.6, 0.8, 1.0],
}

# 默认配置
DEFAULT_CONFIG = {
    'test_days': 3,
    'sample_stocks': 20,
    'max_workers': 2,
    'timeout': 15,
    'retry_times': 3,
}

# ============== 数据获取 ==============
def fetch_with_retry(url, headers=None, retry=3):
    """带重试的 HTTP 请求"""
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0"}
    
    for i in range(retry):
        try:
            response = requests.get(url, headers=headers, timeout=DEFAULT_CONFIG['timeout'])
            if response.status_code == 200:
                return response.json()
            time.sleep(1 * (i + 1))
        except Exception as e:
            if i < retry - 1:
                time.sleep(1 * (i + 1))
    return None

def fetch_stock_history(ts_code, end_date, days=60):
    """获取历史 K 线（多数据源）"""
    try:
        # 东方财富
        market = "SH" if ts_code.startswith('6') else "SZ"
        code = f"{market}.{ts_code}"
        
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        start_dt = end_dt - timedelta(days=days*2)
        
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={code}&klt=101&fqt=1&beg={start_dt.strftime('%Y%m%d')}&end={end_date}"
        data = fetch_with_retry(url)
        
        if data and data.get('data') and data['data'].get('klines'):
            klines = data['data']['klines']
            rows = [k.split(',') for k in klines]
            df = pd.DataFrame(rows, columns=['trade_date', 'open', 'close', 'high', 'low', 'vol', 'amount', 'amplitude', 'chg', 'change', 'turnover'])
            
            for col in ['open', 'close', 'high', 'low', 'vol']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            return df.sort_values('trade_date')
    except:
        pass
    
    return None

def fetch_stock_list():
    """获取股票列表"""
    stocks_file = os.path.join(os.path.dirname(__file__), 'stocks.json')
    if os.path.exists(stocks_file):
        with open(stocks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# ============== 预测逻辑（参数化） ==============
def predict_with_params(df, params):
    """
    使用指定参数进行预测
    
    params: dict
        - trend_weight: 趋势权重
        - momentum_weight: 动量权重
        - volatility_threshold: 波动率阈值
        - conservative_factor: 保守系数
    """
    if len(df) < 20:
        return 0.0
    
    latest = df.iloc[-1]
    close = latest['close']
    ma5 = latest['ma5']
    ma20 = latest['ma20']
    ma60 = latest.get('ma60', ma20)
    rsi = latest['rsi']
    macd = latest.get('macd', 0)
    macd_signal = latest.get('macd_signal', 0)
    volatility = latest.get('volatility_20d', 20)
    vol_ratio = latest.get('vol_ratio', 1)
    
    # 趋势评分
    trend_score = 0
    if close > ma5: trend_score += 1
    if close > ma20: trend_score += 1
    if close > ma60: trend_score += 1
    if rsi > 50 and rsi < 70: trend_score += 0.5
    if rsi < 30: trend_score -= 0.5
    if rsi > 70: trend_score -= 1.0
    if macd > macd_signal: trend_score += 0.5
    
    # 近期收益率
    recent_returns = df['close'].pct_change().dropna().tail(10)
    mean_return = recent_returns.mean() * 100
    
    # 动量因子
    momentum_5d = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # 基础预测（参数化）
    base_prediction = mean_return * 1.2 + (trend_score * params['trend_weight']) + (momentum_5d * params['momentum_weight'])
    
    # 波动率调整（参数化）
    volatility_factor = 1.0
    if volatility > params['volatility_threshold'] * 1.5:
        volatility_factor = 0.5
    elif volatility > params['volatility_threshold']:
        volatility_factor = 0.7
    elif volatility > params['volatility_threshold'] * 0.8:
        volatility_factor = 0.85
    
    adjusted_prediction = base_prediction * volatility_factor
    
    # 成交量验证
    if base_prediction > 0 and vol_ratio < 0.8:
        adjusted_prediction *= 0.7
    elif base_prediction < 0 and vol_ratio < 0.8:
        adjusted_prediction *= 0.7
    
    # 保守收缩（参数化）
    max_pred = 5.0 * params['conservative_factor']
    adjusted_prediction = np.clip(adjusted_prediction, -max_pred, max_pred)
    if abs(adjusted_prediction) > 3.0:
        adjusted_prediction *= params['conservative_factor']
    
    return adjusted_prediction

def calculate_features(df):
    """计算技术指标"""
    df = df.sort_values('trade_date').reset_index(drop=True)
    
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50).clip(0, 100)
    
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    df['daily_return'] = df['close'].pct_change()
    df['volatility_20d'] = df['daily_return'].rolling(20).std() * np.sqrt(252) * 100
    
    df['vol_ma5'] = df['vol'].rolling(5).mean()
    df['vol_ratio'] = df['vol'] / df['vol_ma5']
    
    return df

# ============== 回测 ==============
def backtest_with_params(stocks, test_dates, params):
    """使用指定参数进行回测"""
    results = []
    
    for stock in stocks:
        ts_code = stock.get('ts_code', stock['code'][2:] if stock['code'].startswith('sh') or stock['code'].startswith('sz') else stock['code'])
        name = stock.get('name', '未知')
        
        stock_results = []
        
        for test_date in test_dates:
            try:
                df = fetch_stock_history(ts_code, test_date, days=60)
                
                if df is None or len(df) < 22:
                    continue
                
                df = calculate_features(df)
                
                # 预测
                historical_df = df.iloc[:-1].copy()
                historical_df = calculate_features(historical_df)
                
                predicted_change = predict_with_params(historical_df, params)
                
                # 实际
                prev_close = df.iloc[-2]['close']
                actual_close = df.iloc[-1]['close']
                actual_change = (actual_close - prev_close) / prev_close * 100
                
                # 判断
                direction_correct = (predicted_change > 0) == (actual_change > 0)
                abs_error = abs(predicted_change - actual_change)
                
                stock_results.append({
                    'trade_date': test_date,
                    'predicted_change': round(predicted_change, 2),
                    'actual_change': round(actual_change, 2),
                    'direction_correct': direction_correct,
                    'abs_error': round(abs_error, 2),
                })
                
                time.sleep(0.3)
            
            except Exception as e:
                continue
        
        if stock_results:
            df_r = pd.DataFrame(stock_results)
            results.append({
                'stock_code': ts_code,
                'stock_name': name,
                'predictions': stock_results,
                'valid_predictions': len(stock_results),
                'direction_accuracy': round(df_r['direction_correct'].mean() * 100, 1),
                'mean_absolute_error': round(df_r['abs_error'].mean(), 2),
            })
    
    return results

def get_test_dates(days=3):
    """获取测试日期"""
    test_dates = []
    current = datetime.now() - timedelta(days=1)
    
    while len(test_dates) < days:
        if current.weekday() < 5:
            test_dates.append(current.strftime('%Y%m%d'))
        current -= timedelta(days=1)
    
    return test_dates

def run_parameter_search():
    """运行参数搜索"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测模型参数优化系统 v4.0")
    print(f"测试时间：{timestamp}")
    print("="*80)
    
    # 获取测试日期
    test_dates = get_test_dates(DEFAULT_CONFIG['test_days'])
    print(f"\n📅 测试日期：{test_dates}")
    
    # 加载股票
    stocks = fetch_stock_list()
    if not stocks:
        print("❌ 无法加载股票列表")
        return
    
    # 采样
    sample_size = min(DEFAULT_CONFIG['sample_stocks'], len(stocks))
    np.random.seed(42)  # 固定随机种子保证一致性
    sample_indices = np.random.choice(len(stocks), sample_size, replace=False)
    sample_stocks = [stocks[i] for i in sample_indices]
    
    print(f"📊 测试股票：{sample_size} 只")
    print()
    
    # 参数网格搜索
    print("🔍 开始参数网格搜索...")
    print(f"   参数空间：{len(PARAM_GRID['trend_weight'])} × {len(PARAM_GRID['momentum_weight'])} × {len(PARAM_GRID['volatility_threshold'])} × {len(PARAM_GRID['conservative_factor'])} = {len(PARAM_GRID['trend_weight']) * len(PARAM_GRID['momentum_weight']) * len(PARAM_GRID['volatility_threshold']) * len(PARAM_GRID['conservative_factor'])} 种组合")
    print()
    
    all_results = []
    param_combinations = []
    
    for tw in PARAM_GRID['trend_weight']:
        for mw in PARAM_GRID['momentum_weight']:
            for vt in PARAM_GRID['volatility_threshold']:
                for cf in PARAM_GRID['conservative_factor']:
                    param_combinations.append({
                        'trend_weight': tw,
                        'momentum_weight': mw,
                        'volatility_threshold': vt,
                        'conservative_factor': cf,
                    })
    
    print(f"   共 {len(param_combinations)} 组参数，开始测试...\n")
    
    for i, params in enumerate(param_combinations):
        print(f"[{i+1}/{len(param_combinations)}] 测试参数组合:")
        print(f"   trend_weight={params['trend_weight']}, momentum_weight={params['momentum_weight']}, volatility_threshold={params['volatility_threshold']}, conservative_factor={params['conservative_factor']}")
        
        # 回测
        results = backtest_with_params(sample_stocks[:10], test_dates, params)  # 先用 10 只股票快速测试
        
        if results:
            total_preds = sum(r['valid_predictions'] for r in results)
            avg_dir_acc = np.mean([r['direction_accuracy'] for r in results])
            avg_mae = np.mean([r['mean_absolute_error'] for r in results])
            
            print(f"   结果：{len(results)}只股票，{total_preds}个预测，方向正确率={avg_dir_acc:.1f}%, 平均误差={avg_mae:.2f}%")
            
            all_results.append({
                'params': params,
                'total_stocks': len(results),
                'total_predictions': total_preds,
                'avg_direction_accuracy': round(avg_dir_acc, 1),
                'mean_absolute_error': round(avg_mae, 2),
            })
        else:
            print(f"   结果：无有效数据")
        
        print()
    
    # 找出最优参数
    if all_results:
        df_results = pd.DataFrame(all_results)
        
        # 按方向正确率排序
        df_sorted = df_results.sort_values('avg_direction_accuracy', ascending=False)
        
        print("="*80)
        print("📊 参数搜索结果")
        print("="*80)
        
        print("\n🏆 TOP 5 最优参数组合:\n")
        
        for i, (_, row) in enumerate(df_sorted.head(5).iterrows(), 1):
            params = row['params']
            print(f"{i}. 方向正确率={row['avg_direction_accuracy']:.1f}%, 平均误差={row['mean_absolute_error']:.2f}%")
            print(f"   trend_weight={params['trend_weight']}, momentum_weight={params['momentum_weight']}, volatility_threshold={params['volatility_threshold']}, conservative_factor={params['conservative_factor']}")
            print()
        
        # 保存结果
        output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
        os.makedirs(output_dir, exist_ok=True)
        
        result_file = f"{output_dir}/param_search_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'config': {
                    'test_dates': test_dates,
                    'sample_stocks': sample_size
                },
                'all_results': all_results,
                'best_params': df_sorted.iloc[0]['params'],
                'best_accuracy': df_sorted.iloc[0]['avg_direction_accuracy']
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📁 结果已保存：{result_file}")
        
        # 生成最优参数文件
        best_params = df_sorted.iloc[0]['params']
        best_params_file = '/home/admin/openclaw/workspace/stock_system/optimal_params.json'
        with open(best_params_file, 'w', encoding='utf-8') as f:
            json.dump({
                'found_at': timestamp,
                'accuracy': df_sorted.iloc[0]['avg_direction_accuracy'],
                'params': best_params
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📁 最优参数已保存：{best_params_file}")
        
        return best_params, df_sorted.iloc[0]['avg_direction_accuracy']
    
    return None, None

if __name__ == '__main__':
    best_params, accuracy = run_parameter_search()
    
    if best_params:
        print("\n" + "="*80)
        print(f"✅ 参数优化完成！")
        print(f"🏆 最优方向正确率：{accuracy:.1f}%")
        print(f"📋 最优参数:")
        for k, v in best_params.items():
            print(f"   {k}: {v}")
        print("="*80)
