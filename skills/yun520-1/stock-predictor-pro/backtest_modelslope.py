#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大规模回测验证系统 v16.0
使用 ModelScope 2200 万条历史数据进行回测
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

CONFIG = {
    'test_days': 30,  # 回测天数
    'sample_stocks': 100,  # 测试股票数
    'data_file': '/home/admin/openclaw/workspace/chinese-stock-dataset/chinese-stock-dataset.csv'
}

def load_data():
    """加载数据集"""
    print("📊 加载数据集...")
    df = pd.read_csv(CONFIG['data_file'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
    df = df.sort_values(['stock_code', 'date'])
    print(f"   ✅ 记录数：{len(df):,} 条")
    print(f"   ✅ 股票数：{df['stock_code'].nunique():,} 只")
    print(f"   ✅ 日期范围：{df['date'].min()} - {df['date'].max()}")
    return df

def predict_t1(historical_df):
    """
    使用 T-1 日及之前数据预测 T 日走势
    """
    if len(historical_df) < 20:
        return 0.0
    
    df = historical_df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # 计算技术指标
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50).clip(0, 100)
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    latest = df.iloc[-1]
    close = latest['close']
    ma5 = latest['ma5']
    ma20 = latest['ma20']
    ma60 = latest.get('ma60', ma20)
    rsi = latest['rsi']
    macd = latest.get('macd', 0)
    macd_signal = latest.get('macd_signal', 0)
    
    # 趋势评分
    trend_score = 0
    if close > ma5: trend_score += 1.5
    if close > ma20: trend_score += 1.5
    if close > ma60: trend_score += 1.5
    if 55 < rsi < 75: trend_score += 1.5
    if macd > 0: trend_score += 1.0
    
    # 动量
    ret = df['close'].pct_change().tail(10).mean() * 100
    mom = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # 预测
    base = ret * 2.5 + trend_score * 1.2 + mom * 0.6
    
    # 均线偏离
    dev = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev > 3: base += 2.0
    elif dev > 2: base += 1.5
    elif dev > 1: base += 1.0
    
    # 上限
    pred = np.clip(base, -8.0, 8.0)
    
    return pred

def run_backtest():
    """运行回测"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"大规模回测验证 v16.0")
    print(f"时间：{ts}")
    print("="*80)
    
    # 加载数据
    df = load_data()
    
    # 获取最近 N 天数据
    max_date = df['date'].max()
    min_date = max_date - timedelta(days=CONFIG['test_days'])
    test_df = df[(df['date'] >= min_date) & (df['date'] <= max_date)]
    
    print(f"\n📅 测试期间：{min_date.date()} - {max_date.date()}")
    print(f"   天数：{CONFIG['test_days']} 天")
    
    # 采样股票
    stocks = test_df['stock_code'].unique()
    if len(stocks) > CONFIG['sample_stocks']:
        np.random.seed(42)
        stocks = np.random.choice(stocks, CONFIG['sample_stocks'], replace=False)
    
    print(f"   股票：{len(stocks)} 只")
    
    # 回测
    print(f"\n🔍 开始回测...")
    all_results = []
    
    for i, stock in enumerate(stocks):
        stock_df = df[df['stock_code'] == stock].sort_values('date')
        
        if len(stock_df) < 30:
            continue
        
        # 对每个交易日进行"模拟预测"
        stock_results = []
        test_period_df = test_df[test_df['stock_code'] == stock].sort_values('date')
        
        for idx, row in test_period_df.iterrows():
            test_date = row['date']
            actual_close = row['close']
            
            # 获取前一日数据
            prev_date = test_date - timedelta(days=1)
            hist_df = stock_df[stock_df['date'] <= prev_date]
            
            if len(hist_df) < 20:
                continue
            
            # 预测
            pred_change = predict_t1(hist_df)
            
            # 实际（相对前一日涨跌幅）
            prev_close = hist_df.iloc[-1]['close']
            actual_change = (actual_close - prev_close) / prev_close * 100
            
            # 对比
            direction_correct = (pred_change > 0) == (actual_change > 0)
            abs_error = abs(pred_change - actual_change)
            
            stock_results.append({
                'stock_code': stock,
                'date': test_date,
                'predicted': round(pred_change, 2),
                'actual': round(actual_change, 2),
                'correct': direction_correct,
                'error': round(abs_error, 2)
            })
        
        if stock_results:
            all_results.extend(stock_results)
        
        if (i+1) % 20 == 0:
            print(f"   进度：{i+1}/{len(stocks)}")
    
    # 汇总
    if not all_results:
        print("\n❌ 无有效回测结果")
        return
    
    df_results = pd.DataFrame(all_results)
    
    print("\n" + "="*80)
    print("📊 回测结果汇总")
    print("="*80)
    
    total = len(df_results)
    correct = len(df_results[df_results['correct']])
    accuracy = correct / total * 100
    mae = df_results['error'].mean()
    hit_2pct = len(df_results[df_results['error'] < 2.0]) / total * 100
    
    print(f"\n验证样本：{total} 个")
    print(f"方向正确：{correct}/{total} ({accuracy:.1f}%)")
    print(f"平均误差：{mae:.2f}%")
    print(f"命中率 (<2%)：{hit_2pct:.1f}%")
    
    # 按天统计
    print(f"\n📅 每日表现:")
    daily = df_results.groupby('date').agg({
        'correct': 'mean',
        'error': 'mean'
    }).round(2)
    
    for date, row in daily.head(10).iterrows():
        print(f"   {date.date()}: 准确率={row['correct']*100:.1f}%, 误差={row['error']:.2f}%")
    
    # 按股票统计
    print(f"\n📈 个股表现 TOP 10:")
    stock_stats = df_results.groupby('stock_code').agg({
        'correct': 'mean',
        'error': 'mean',
        'date': 'count'
    }).rename(columns={'date': 'count'}).round(2)
    
    top_stocks = stock_stats.sort_values('correct', ascending=False).head(10)
    for code, row in top_stocks.iterrows():
        print(f"   {code}: 准确率={row['correct']*100:.1f}%, 误差={row['error']:.2f}%, 样本={int(row['count'])}")
    
    # 保存结果
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    
    result_file = f"{output_dir}/backtest_modelslope_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': ts,
            'config': {
                'test_days': CONFIG['test_days'],
                'sample_stocks': len(stocks),
                'data_file': CONFIG['data_file']
            },
            'summary': {
                'total_samples': total,
                'correct': correct,
                'accuracy': round(accuracy, 1),
                'mae': round(mae, 2),
                'hit_2pct': round(hit_2pct, 1)
            },
            'daily': daily.reset_index().to_dict('records'),
            'top_stocks': top_stocks.reset_index().to_dict('records')
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 结果已保存：{result_file}")
    
    # 评估与建议
    print("\n" + "="*80)
    print("🎯 模型评估与修复建议")
    print("="*80)
    
    if accuracy >= 60:
        print(f"✅ 方向正确率 {accuracy:.1f}% - 表现优秀")
    elif accuracy >= 50:
        print(f"⚠️  方向正确率 {accuracy:.1f}% - 及格，需要微调")
    else:
        print(f"❌ 方向正确率 {accuracy:.1f}% - 需要大幅改进")
    
    if mae <= 2:
        print(f"✅ 平均误差 {mae:.2f}% - 精度优秀")
    elif mae <= 4:
        print(f"⚠️  平均误差 {mae:.2f}% - 可接受")
    else:
        print(f"❌ 平均误差 {mae:.2f}% - 误差偏大")
    
    # 修复建议
    print(f"\n🔧 修复建议:")
    if accuracy < 55:
        print(f"   1. 增加趋势权重（当前预测对方向判断不准）")
        print(f"   2. 减少动量权重（可能过度依赖历史走势）")
        print(f"   3. 增加 RSI 权重（超买超卖判断不足）")
    
    if mae > 3:
        print(f"   1. 降低预测上限（当前预测幅度过大）")
        print(f"   2. 增加波动率调整（高波动股票预测不准）")
        print(f"   3. 增加成交量验证（无量预测可靠性低）")
    
    print(f"\n✅ 回测完成！")
    
    return accuracy, mae

if __name__ == '__main__':
    run_backtest()
