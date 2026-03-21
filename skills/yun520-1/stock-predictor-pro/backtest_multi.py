#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测模型多轮回溯测试系统 v3.0
真正的历史回测：用历史数据预测，用实际走势验证

方法：
1. 选取过去 N 个交易日作为测试集
2. 对每个交易日 T：
   - 只用 T-1 日及之前的数据预测 T 日走势
   - 用 T 日实际涨跌幅验证
3. 统计多轮验证的准确率、命中率、方向正确率

关键：确保"当时"视角，不使用未来数据！
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
    'test_days': 5,  # 回溯测试天数
    'sample_stocks': 30,  # 测试股票数量
    'max_workers': 3,  # 并发数（降低避免被封）
    'timeout': 15,  # 请求超时
    'retry_times': 2,  # 重试次数
}

# ============== 数据获取（多数据源 + 重试） ==============
def fetch_with_retry(url: str, headers: dict = None, retry: int = 3) -> dict:
    """带重试的 HTTP 请求"""
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0"}
    
    for i in range(retry):
        try:
            response = requests.get(url, headers=headers, timeout=CONFIG['timeout'])
            if response.status_code == 200:
                return response.json()
            time.sleep(1 * (i + 1))  # 递增延迟
        except Exception as e:
            if i < retry - 1:
                time.sleep(1 * (i + 1))
            else:
                return None
    return None

def fetch_stock_history_eastmoney(ts_code: str, end_date: str, days: int = 60) -> pd.DataFrame:
    """获取历史 K 线（东方财富）"""
    try:
        market = "SH" if ts_code.startswith('6') else "SZ"
        code = f"{market}.{ts_code}"
        
        end_dt = datetime.strptime(end_date, '%Y%m%d')
        start_dt = end_dt - timedelta(days=days*2)
        start_date = start_dt.strftime('%Y%m%d')
        
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={code}&klt=101&fqt=1&beg={start_date}&end={end_date}"
        data = fetch_with_retry(url)
        
        if not data or not data.get('data') or not data['data'].get('klines'):
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

def fetch_stock_history_tencent(ts_code: str, end_date: str, days: int = 60) -> pd.DataFrame:
    """获取历史 K 线（腾讯）"""
    try:
        market = "sh" if ts_code.startswith('6') else "sz"
        code = f"{market}{ts_code}"
        
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{days},qfq"
        data = fetch_with_retry(url)
        
        if not data or data.get('code') != 0 or 'data' not in data:
            return None
        
        stock_data = data['data'].get(code, {})
        klines = stock_data.get('qfqday', [])
        
        if not klines:
            return None
        
        df = pd.DataFrame(klines)
        if df.shape[1] < 7:
            return None
        
        df = df.rename(columns={0: 'trade_date', 1: 'open', 2: 'close', 3: 'high', 4: 'low', 5: 'vol', 6: 'amount'})
        
        for col in ['open', 'close', 'high', 'low', 'vol', 'amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        return df.sort_values('trade_date')
    
    except Exception as e:
        return None

def fetch_stock_history(ts_code: str, end_date: str, days: int = 60) -> pd.DataFrame:
    """多数据源获取历史数据"""
    # 尝试 东方财富
    df = fetch_stock_history_eastmoney(ts_code, end_date, days)
    if df is not None and len(df) >= 20:
        return df
    
    # 尝试 腾讯
    df = fetch_stock_history_tencent(ts_code, end_date, days)
    if df is not None and len(df) >= 20:
        return df
    
    return None

def fetch_stock_list() -> list:
    """获取股票列表"""
    stocks_file = os.path.join(os.path.dirname(__file__), 'stocks.json')
    if os.path.exists(stocks_file):
        with open(stocks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# ============== 预测逻辑 ==============
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
    """基于给定数据预测次日涨跌幅"""
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

# ============== 回测核心 ==============
def backtest_single_stock(ts_code: str, stock_name: str, test_dates: list) -> dict:
    """
    对单只股票进行多轮回溯测试
    
    test_dates: 测试日期列表 ['20260315', '20260316', ...]
    对每个日期 T：
    - 用 T-1 日及之前的数据预测 T 日
    - 用 T 日实际走势验证
    """
    results = []
    
    for test_date in test_dates:
        try:
            # 获取数据（截止到 test_date）
            df = fetch_stock_history(ts_code, test_date, days=60)
            
            if df is None or len(df) < 20:
                results.append({
                    'trade_date': test_date,
                    'error': '数据不足',
                    'valid': False
                })
                continue
            
            # 计算特征
            df = calculate_features(df)
            
            # 预测（用 last-1 日数据预测 last 日）
            # df 的最后一行是 test_date 的数据
            # 我们需要用 test_date-1 的数据预测 test_date
            if len(df) < 2:
                results.append({
                    'trade_date': test_date,
                    'error': '数据不足',
                    'valid': False
                })
                continue
            
            # 用前 N-1 行数据预测第 N 行
            historical_df = df.iloc[:-1].copy()
            historical_df = calculate_features(historical_df)
            
            predicted_change = predict_single_day(historical_df)
            
            # 实际涨跌幅（test_date 相对前一日的变化）
            prev_close = df.iloc[-2]['close']
            actual_close = df.iloc[-1]['close']
            actual_change = (actual_close - prev_close) / prev_close * 100
            
            # 判断
            direction_correct = (predicted_change > 0) == (actual_change > 0)
            error = predicted_change - actual_change
            abs_error = abs(error)
            hit_2pct = abs_error < 2.0
            hit_1pct = abs_error < 1.0
            
            results.append({
                'trade_date': test_date,
                'predicted_change': round(predicted_change, 2),
                'actual_change': round(actual_change, 2),
                'direction_correct': direction_correct,
                'error': round(error, 2),
                'abs_error': round(abs_error, 2),
                'hit_2pct': hit_2pct,
                'hit_1pct': hit_1pct,
                'valid': True
            })
            
            # 延迟避免请求过快
            time.sleep(0.5)
        
        except Exception as e:
            results.append({
                'trade_date': test_date,
                'error': str(e),
                'valid': False
            })
    
    # 统计
    valid_results = [r for r in results if r.get('valid', False)]
    
    if not valid_results:
        return {
            'stock_code': ts_code,
            'stock_name': stock_name,
            'valid_predictions': 0,
            'error': '无有效预测'
        }
    
    df_r = pd.DataFrame(valid_results)
    
    return {
        'stock_code': ts_code,
        'stock_name': stock_name,
        'predictions': valid_results,
        'valid_predictions': len(valid_results),
        'direction_accuracy': round(df_r['direction_correct'].mean() * 100, 1),
        'mean_absolute_error': round(df_r['abs_error'].mean(), 2),
        'mean_error': round(df_r['error'].mean(), 2),
        'hit_rate_2pct': round(df_r['hit_2pct'].mean() * 100, 1),
        'hit_rate_1pct': round(df_r['hit_1pct'].mean() * 100, 1),
    }

def get_test_dates(days: int = 5) -> list:
    """获取测试日期列表（过去 N 个交易日）"""
    # 从昨天开始往前推（今天可能还没收盘）
    test_dates = []
    current = datetime.now() - timedelta(days=1)
    
    while len(test_dates) < days:
        # 跳过周末
        if current.weekday() < 5:  # 周一到周五
            test_dates.append(current.strftime('%Y%m%d'))
        current -= timedelta(days=1)
    
    return test_dates

def run_backtest():
    """运行回测"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测模型多轮回溯测试系统 v3.0")
    print(f"测试时间：{timestamp}")
    print("="*80)
    
    # 获取测试日期
    test_dates = get_test_dates(CONFIG['test_days'])
    print(f"\n📅 测试日期：{test_dates}")
    print(f"   回溯天数：{len(test_dates)} 个交易日")
    
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
    print(f"   测试股票：{sample_size} 只（随机采样）")
    print(f"   总测试样本：{len(test_dates) * sample_size} 个预测")
    print()
    
    # 执行回测
    results = []
    print(f"🔍 开始多轮回溯测试...")
    print(f"   每只股票测试 {len(test_dates)} 个交易日")
    print()
    
    with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        futures = {}
        for stock in sample_stocks:
            ts_code = stock.get('ts_code', stock['code'][2:] if stock['code'].startswith('sh') or stock['code'].startswith('sz') else stock['code'])
            name = stock.get('name', '未知')
            future = executor.submit(backtest_single_stock, ts_code, name, test_dates)
            futures[future] = ts_code
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            if completed % 5 == 0:
                print(f"   进度：{completed}/{sample_size}")
    
    # 汇总统计
    print("\n" + "="*80)
    print("📊 回测结果汇总")
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
    
    # 转换 numpy 类型
    def convert_numpy(obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(i) for i in obj]
        return obj
    
    result_file = f"{output_dir}/backtest_multi_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'config': {
                'test_days': len(test_dates),
                'test_dates': test_dates,
                'sample_stocks': sample_size
            },
            'summary': {
                'total_stocks': len(valid_results),
                'total_predictions': total_predictions,
                'avg_direction_accuracy': convert_numpy(avg_direction_accuracy),
                'avg_mae': convert_numpy(avg_mae),
                'avg_hit_rate_2pct': convert_numpy(avg_hit_rate_2pct),
                'avg_hit_rate_1pct': convert_numpy(avg_hit_rate_1pct)
            },
            'details': convert_numpy(valid_results)
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"📁 结果已保存：{result_file}")
    
    # 生成 Markdown 报告
    md_report = generate_md_report(valid_results, avg_direction_accuracy, avg_mae, 
                                   avg_hit_rate_2pct, avg_hit_rate_1pct, 
                                   total_predictions, test_dates, timestamp)
    md_file = f"{output_dir}/backtest_multi_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"📁 报告已保存：{md_file}")
    print("\n" + "="*80)
    print("✅ 多轮回溯测试完成")
    print("="*80)
    
    return {
        'total_stocks': len(valid_results),
        'total_predictions': total_predictions,
        'avg_direction_accuracy': avg_direction_accuracy,
        'avg_mae': avg_mae,
        'avg_hit_rate_2pct': avg_hit_rate_2pct,
        'avg_hit_rate_1pct': avg_hit_rate_1pct
    }

def generate_md_report(results, avg_dir_acc, avg_mae, avg_hit_2pct, avg_hit_1pct, total_preds, test_dates, timestamp):
    """生成 Markdown 报告"""
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('direction_accuracy', ascending=False)
    
    md = f"""# 📊 股票预测模型多轮回溯测试报告

**测试时间**: {timestamp}
**测试方法**: 用历史数据进行"模拟预测"，然后与实际走势对比（真正的回测）

---

## 📅 测试配置

| 配置项 | 值 |
|--------|-----|
| 测试日期 | {', '.join(test_dates)} |
| 回溯天数 | {len(test_dates)} 个交易日 |
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
    
    # 按日期汇总
    all_predictions = []
    for r in results:
        if 'predictions' in r:
            for p in r['predictions']:
                p['stock_code'] = r['stock_code']
                p['stock_name'] = r['stock_name']
                all_predictions.append(p)
    
    if all_predictions:
        df_all = pd.DataFrame(all_predictions)
        daily_stats = df_all.groupby('trade_date').agg({
            'direction_correct': 'mean',
            'abs_error': 'mean',
            'hit_2pct': 'mean'
        }).round(3)
        
        md += f"""
---

## 📅 每日表现

| 日期 | 方向正确率 | 平均误差 | 命中率 (<2%) |
|------|------------|----------|-------------|
"""
        for date, row in daily_stats.iterrows():
            md += f"| {date} | {row['direction_correct']*100:.1f}% | {row['abs_error']:.2f}% | {row['hit_2pct']*100:.1f}% |\n"
    
    md += f"""
---

## 📋 测试方法说明

### 回测原理

1. **选取测试日期**: 过去 {len(test_dates)} 个交易日 ({', '.join(test_dates)})
2. **模拟"当时"视角**: 对每个交易日 T，只用 T-1 日及之前的数据进行预测
3. **验证**: 用 T 日的实际涨跌幅验证预测准确性
4. **统计**: 汇总所有预测的准确率

### 为什么这样做？

- ✅ **真实验证**: 用真实历史数据，不是模拟数据
- ✅ **避免未来函数**: 确保只用"当时"可见的数据
- ✅ **大样本**: 可以测试数百个预测样本
- ✅ **可重复**: 可以调整参数反复测试

### 局限性

- ⚠️ 历史表现不代表未来
- ⚠️ 回测期间可能包含特殊市场环境
- ⚠️ 数据获取可能受网络影响

---

## 🔧 模型评估

基于回测结果：

"""
    
    if avg_dir_acc >= 60:
        md += f"- ✅ **方向正确率 {avg_dir_acc:.1f}%**: 模型方向判断能力较好（>60% 为合格）\n"
    elif avg_dir_acc >= 50:
        md += f"- ⚠️ **方向正确率 {avg_dir_acc:.1f}%**: 模型方向判断勉强及格（50-60%）\n"
    else:
        md += f"- ❌ **方向正确率 {avg_dir_acc:.1f}%**: 模型方向判断需要改进（<50%）\n"
    
    if avg_mae <= 2.0:
        md += f"- ✅ **平均误差 {avg_mae:.2f}%**: 预测精度较高（<2% 为优秀）\n"
    elif avg_mae <= 3.0:
        md += f"- ⚠️ **平均误差 {avg_mae:.2f}%**: 预测精度可接受（2-3%）\n"
    else:
        md += f"- ❌ **平均误差 {avg_mae:.2f}%**: 预测误差偏大（>3%）\n"
    
    if avg_hit_2pct >= 50:
        md += f"- ✅ **命中率 {avg_hit_2pct:.1f}%**: 超过半数预测误差<2%\n"
    else:
        md += f"- ⚠️ **命中率 {avg_hit_2pct:.1f}%**: 需要提高预测精度\n"
    
    md += """
---

*免责声明：回测结果仅供参考，不构成投资建议。股市有风险，投资需谨慎。*
"""
    
    return md

if __name__ == '__main__':
    run_backtest()
