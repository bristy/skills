#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测模型回溯测试系统 v1.0
核心思路：用历史数据进行"模拟预测"，然后与实际走势对比

方法：
1. 选取过去 N 个交易日
2. 对每个交易日 T，只用 T 日之前的数据预测 T+1 日走势
3. 用 T+1 日的实际涨跌幅验证预测准确性
4. 统计准确率、平均误差、方向正确率等指标

这样可以快速验证模型在历史数据上的表现，无需等待实际走势！
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

# ============== 配置 ==============
CONFIG = {
    'test_days': 10,  # 回溯测试天数
    'sample_stocks': 50,  # 测试股票数量
    'max_workers': 5,  # 并发数
    'timeout': 10,  # 请求超时
}

# ============== 数据获取 ==============
def fetch_stock_history_eastmoney(ts_code: str, end_date: str = None, days: int = 90) -> pd.DataFrame:
    """
    获取股票历史 K 线数据（东方财富）
    end_date: 截止日期（模拟"当时"的视角）
    """
    try:
        market = "SH" if ts_code.startswith('6') else "SZ"
        code = f"{market}.{ts_code}"
        
        # 如果不指定 end_date，默认使用最近数据
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
        else:
            # 计算 start_date（end_date 前推 days 天）
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            start_dt = end_dt - timedelta(days=days*2)
            start_date = start_dt.strftime('%Y%m%d')
        
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={code}&klt=101&fqt=1&beg={start_date}&end={end_date}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=CONFIG['timeout'])
        data = response.json()
        
        if not data.get('data') or not data['data'].get('klines'):
            return None
        
        klines = data['data']['klines']
        rows = [k.split(',') for k in klines]
        df = pd.DataFrame(rows, columns=['trade_date', 'open', 'close', 'high', 'low', 'vol', 'amount', 'amplitude', 'chg', 'change', 'turnover'])
        
        for col in ['open', 'close', 'high', 'low', 'vol']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        return df.sort_values('trade_date')
    
    except Exception as e:
        return None

def fetch_stock_list() -> list:
    """获取股票列表（使用本地缓存）"""
    stocks_file = os.path.join(os.path.dirname(__file__), 'stocks.json')
    if os.path.exists(stocks_file):
        with open(stocks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# ============== 预测逻辑（与 v13 一致） ==============
def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    df = df.sort_values('trade_date').reset_index(drop=True)
    
    # 均线
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50).clip(0, 100)
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # 波动率
    df['daily_return'] = df['close'].pct_change()
    df['volatility_20d'] = df['daily_return'].rolling(20).std() * np.sqrt(252) * 100
    
    # 成交量
    df['vol_ma5'] = df['vol'].rolling(5).mean()
    df['vol_ratio'] = df['vol'] / df['vol_ma5']
    
    return df

def predict_single_day(df: pd.DataFrame) -> float:
    """
    基于给定数据预测次日涨跌幅
    返回预测的涨跌幅百分比
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
    
    # 基础预测
    base_prediction = mean_return * 1.2 + (trend_score * 0.6) + (momentum_5d * 0.2)
    
    # 波动率调整
    volatility_factor = 1.0
    if volatility > 50:
        volatility_factor = 0.5
    elif volatility > 30:
        volatility_factor = 0.7
    elif volatility > 20:
        volatility_factor = 0.85
    
    adjusted_prediction = base_prediction * volatility_factor
    
    # 成交量验证
    if base_prediction > 0 and vol_ratio < 0.8:
        adjusted_prediction *= 0.7
    elif base_prediction < 0 and vol_ratio < 0.8:
        adjusted_prediction *= 0.7
    
    # 保守收缩
    adjusted_prediction = np.clip(adjusted_prediction, -5.0, 5.0)
    if abs(adjusted_prediction) > 3.0:
        adjusted_prediction *= 0.8
    
    return adjusted_prediction

# ============== 回溯测试核心 ==============
def backtest_single_stock(ts_code: str, stock_name: str, test_days: int = 10) -> dict:
    """
    对单只股票进行回溯测试
    
    方法：
    1. 获取最近 N+test_days 天的数据
    2. 对每个测试日 T：
       - 只用 T 日之前的数据预测 T 日走势
       - 用 T 日实际涨跌幅验证
    """
    try:
        # 获取数据（多获取 test_days 天用于验证）
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=60 + test_days*2)).strftime('%Y%m%d')
        
        df = fetch_stock_history_eastmoney(ts_code, end_date=end_date, days=60+test_days*2)
        
        if df is None or len(df) < 20 + test_days:
            return {
                'stock_code': ts_code,
                'stock_name': stock_name,
                'error': '数据不足',
                'valid_predictions': 0
            }
        
        # 计算特征
        df = calculate_features(df)
        
        predictions = []
        
        # 对最近 test_days 个交易日进行"模拟预测"
        for i in range(test_days):
            # 测试日索引（从后往前）
            test_idx = len(df) - 1 - i
            
            if test_idx < 20:
                break
            
            test_date = df.iloc[test_idx]['trade_date']
            actual_close = df.iloc[test_idx]['close']
            
            # 获取前一日数据
            prev_idx = test_idx - 1
            prev_close = df.iloc[prev_idx]['close']
            
            # 实际涨跌幅（测试日相对前一日的变化）
            actual_change = (actual_close - prev_close) / prev_close * 100
            
            # "模拟预测"：只用 prev_idx 及之前的数据
            historical_df = df.iloc[:prev_idx + 1].copy()
            
            # 重新计算特征（确保只用历史数据）
            historical_df = calculate_features(historical_df)
            
            # 预测
            predicted_change = predict_single_day(historical_df)
            
            predictions.append({
                'trade_date': test_date.strftime('%Y-%m-%d'),
                'predicted_change': round(predicted_change, 2),
                'actual_change': round(actual_change, 2),
                'direction_correct': (predicted_change > 0) == (actual_change > 0),
                'error': round(predicted_change - actual_change, 2),
                'abs_error': round(abs(predicted_change - actual_change), 2)
            })
        
        if not predictions:
            return {
                'stock_code': ts_code,
                'stock_name': stock_name,
                'error': '无法生成预测',
                'valid_predictions': 0
            }
        
        # 统计指标
        df_pred = pd.DataFrame(predictions)
        
        return {
            'stock_code': ts_code,
            'stock_name': stock_name,
            'predictions': predictions,
            'valid_predictions': len(predictions),
            'direction_accuracy': round(df_pred['direction_correct'].mean() * 100, 1),
            'mean_absolute_error': round(df_pred['abs_error'].mean(), 2),
            'mean_error': round(df_pred['error'].mean(), 2),
            'hit_rate_2pct': round((df_pred['abs_error'] < 2.0).mean() * 100, 1),
            'hit_rate_1pct': round((df_pred['abs_error'] < 1.0).mean() * 100, 1),
        }
    
    except Exception as e:
        return {
            'stock_code': ts_code,
            'stock_name': stock_name,
            'error': str(e),
            'valid_predictions': 0
        }

def run_backtest():
    """运行回溯测试"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测模型回溯测试系统 v1.0")
    print(f"测试时间：{timestamp}")
    print("="*80)
    
    # 加载股票列表
    stocks = fetch_stock_list()
    if not stocks:
        print("❌ 无法加载股票列表")
        return
    
    # 采样
    sample_size = min(CONFIG['sample_stocks'], len(stocks))
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    sample_indices = np.random.choice(len(stocks), sample_size, replace=False)
    sample_stocks = [stocks[i] for i in sample_indices]
    
    print(f"\n📊 测试配置:")
    print(f"   回溯天数：{CONFIG['test_days']} 个交易日")
    print(f"   测试股票：{sample_size} 只（随机采样）")
    print(f"   总测试样本：{CONFIG['test_days'] * sample_size} 个预测")
    print()
    
    # 执行回溯测试
    results = []
    print(f"🔍 开始回溯测试...")
    
    with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        futures = {}
        for stock in sample_stocks:
            ts_code = stock.get('ts_code', stock['code'][2:] if stock['code'].startswith('sh') or stock['code'].startswith('sz') else stock['code'])
            name = stock.get('name', '未知')
            future = executor.submit(backtest_single_stock, ts_code, name, CONFIG['test_days'])
            futures[future] = ts_code
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            if completed % 10 == 0:
                print(f"   进度：{completed}/{sample_size}")
    
    # 汇总统计
    print("\n" + "="*80)
    print("📊 回溯测试结果汇总")
    print("="*80)
    
    valid_results = [r for r in results if r.get('valid_predictions', 0) > 0]
    
    if not valid_results:
        print("❌ 没有有效的测试结果")
        return
    
    total_predictions = sum(r['valid_predictions'] for r in valid_results)
    avg_direction_accuracy = np.mean([r['direction_accuracy'] for r in valid_results])
    avg_mae = np.mean([r['mean_absolute_error'] for r in valid_results])
    avg_hit_rate_2pct = np.mean([r['hit_rate_2pct'] for r in valid_results])
    avg_hit_rate_1pct = np.mean([r['hit_rate_1pct'] for r in valid_results])
    
    print(f"\n✅ 有效股票：{len(valid_results)}/{sample_size}")
    print(f"📝 总预测样本：{total_predictions} 个")
    print()
    print("📈 核心指标:")
    print(f"   方向正确率：{avg_direction_accuracy:.1f}%")
    print(f"   平均绝对误差：{avg_mae:.2f}%")
    print(f"   命中率（误差<2%）：{avg_hit_rate_2pct:.1f}%")
    print(f"   命中率（误差<1%）：{avg_hit_rate_1pct:.1f}%")
    print()
    
    # 按方向正确率排序
    df_results = pd.DataFrame(valid_results)
    df_sorted = df_results.sort_values('direction_accuracy', ascending=False)
    
    print("🎯 方向正确率 TOP 10:")
    print("-"*80)
    for i, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
        print(f"{i}. {row['stock_name']} ({row['stock_code']}): "
              f"方向正确率 {row['direction_accuracy']:.1f}%, "
              f"平均误差 {row['mean_absolute_error']:.2f}%, "
              f"测试样本 {row['valid_predictions']} 个")
    print()
    
    print("⚠️  方向正确率 BOTTOM 10:")
    print("-"*80)
    for i, (_, row) in enumerate(df_sorted.tail(10).iterrows(), 1):
        print(f"{i}. {row['stock_name']} ({row['stock_code']}): "
              f"方向正确率 {row['direction_accuracy']:.1f}%, "
              f"平均误差 {row['mean_absolute_error']:.2f}%")
    print()
    
    # 保存结果
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    
    result_file = f"{output_dir}/backtest_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'config': CONFIG,
            'summary': {
                'total_stocks': len(valid_results),
                'total_predictions': total_predictions,
                'avg_direction_accuracy': avg_direction_accuracy,
                'avg_mae': avg_mae,
                'avg_hit_rate_2pct': avg_hit_rate_2pct,
                'avg_hit_rate_1pct': avg_hit_rate_1pct
            },
            'details': valid_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"📁 结果已保存：{result_file}")
    
    # 生成 Markdown 报告
    md_report = generate_md_report(valid_results, avg_direction_accuracy, avg_mae, 
                                   avg_hit_rate_2pct, avg_hit_rate_1pct, total_predictions, timestamp)
    md_file = f"{output_dir}/backtest_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"📁 报告已保存：{md_file}")
    print("\n" + "="*80)
    print("✅ 回溯测试完成")
    print("="*80)
    
    return {
        'total_stocks': len(valid_results),
        'total_predictions': total_predictions,
        'avg_direction_accuracy': avg_direction_accuracy,
        'avg_mae': avg_mae,
        'avg_hit_rate_2pct': avg_hit_rate_2pct,
        'avg_hit_rate_1pct': avg_hit_rate_1pct
    }

def generate_md_report(results, avg_dir_acc, avg_mae, avg_hit_2pct, avg_hit_1pct, total_preds, timestamp):
    """生成 Markdown 报告"""
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('direction_accuracy', ascending=False)
    
    md = f"""# 📊 股票预测模型回溯测试报告

**测试时间**: {timestamp}
**测试方法**: 使用历史数据进行"模拟预测"，然后与实际走势对比

---

## 📈 测试配置

| 配置项 | 值 |
|--------|-----|
| 回溯天数 | {CONFIG['test_days']} 个交易日 |
| 测试股票 | {len(results)} 只（随机采样） |
| 总预测样本 | {total_preds} 个 |

---

## 🎯 核心指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 方向正确率 | {avg_dir_acc:.1f}% | 预测涨跌方向正确的比例 |
| 平均绝对误差 | {avg_mae:.2f}% | 预测涨幅与实际涨幅的平均差距 |
| 命中率（误差<2%） | {avg_hit_2pct:.1f}% | 预测误差在 2% 以内的比例 |
| 命中率（误差<1%） | {avg_hit_1pct:.1f}% | 预测误差在 1% 以内的比例 |

---

## 📊 方向正确率 TOP 10

| 排名 | 代码 | 名称 | 方向正确率 | 平均误差 | 测试样本 |
|------|------|------|------------|----------|----------|
"""
    
    for i, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
        md += f"| {i} | {row['stock_code']} | {row['stock_name']} | {row['direction_accuracy']:.1f}% | {row['mean_absolute_error']:.2f}% | {row['valid_predictions']} |\n"
    
    md += f"""
---

## ⚠️  方向正确率 BOTTOM 10

| 排名 | 代码 | 名称 | 方向正确率 | 平均误差 |
|------|------|------|------------|----------|
"""
    
    for i, (_, row) in enumerate(df_sorted.tail(10).iterrows(), 1):
        md += f"| {i} | {row['stock_code']} | {row['stock_name']} | {row['direction_accuracy']:.1f}% | {row['mean_absolute_error']:.2f}% |\n"
    
    md += f"""
---

## 📋 测试方法说明

### 回溯测试原理

1. **选取测试期间**: 最近 {CONFIG['test_days']} 个交易日
2. **模拟"当时"视角**: 对每个交易日 T，只用 T 日之前的数据进行预测
3. **验证**: 用 T 日的实际涨跌幅验证预测准确性
4. **统计**: 汇总所有预测的准确率

### 为什么这样做？

- ✅ **快速验证**: 不需要等待实际走势，立即得到结果
- ✅ **大样本**: 可以测试数百个预测样本
- ✅ **可重复**: 可以调整参数反复测试
- ✅ **客观**: 基于真实历史数据，不是模拟数据

### 局限性

- ⚠️ 历史表现不代表未来
- ⚠️ 回测期间可能包含特殊市场环境
- ⚠️ 需要结合前瞻性测试（实际预测）

---

## 🔧 模型优化建议

基于回测结果，可以考虑：

1. **如果方向正确率<50%**: 模型可能需要大幅调整
2. **如果平均误差>3%**: 预测幅度过大，需要保守收缩
3. **如果命中率（误差<2%）<30%**: 模型精度需要提升

---

*免责声明：回测结果仅供参考，不构成投资建议。股市有风险，投资需谨慎。*
"""
    
    return md

if __name__ == '__main__':
    run_backtest()
