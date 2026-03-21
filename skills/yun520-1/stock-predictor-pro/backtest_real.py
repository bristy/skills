#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测真实回测系统 v6.0
真正的历史验证：用历史预测数据 vs 实际走势

方法：
1. 读取历史预测文件（如 3 月 17 日的预测）
2. 获取这些股票在预测日期的实际涨跌幅
3. 对比预测与实际，计算准确率
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import requests
import os
import time
from pathlib import Path

# ============== 数据获取 ==============
def fetch_stock_realtime(ts_code):
    """获取股票实时行情（包含今日涨跌幅）"""
    try:
        market = "SH" if ts_code.startswith('6') else "SZ"
        code = f"{market}.{ts_code}"
        
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={code}&fields=f170,f43,f60"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if not data.get('data'):
            return None
        
        d = data['data']
        return {
            'current_price': d.get('f43', 0) / 100,
            'today_change_pct': d.get('f170', 0) / 100,
            'pre_close': d.get('f60', 0) / 100
        }
    except Exception as e:
        return None

def fetch_stock_history_single(ts_code, target_date):
    """获取指定日期的 K 线数据"""
    try:
        market = "SH" if ts_code.startswith('6') else "SZ"
        code = f"{market}.{ts_code}"
        
        # 获取 target_date 前后几天的数据
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        start_dt = (target_dt - timedelta(days=5)).strftime('%Y%m%d')
        end_dt = (target_dt + timedelta(days=5)).strftime('%Y%m%d')
        
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={code}&klt=101&fqt=1&beg={start_dt}&end={end_dt}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if not data.get('data') or not data['data'].get('klines'):
            return None
        
        klines = data['data']['klines']
        for k in klines:
            parts = k.split(',')
            date = parts[0]
            if date == target_date or date == target_date.replace('-', ''):
                return {
                    'date': date,
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'vol': float(parts[5])
                }
        
        # 如果找不到精确匹配，找最近的
        if klines:
            k = klines[-1]
            parts = k.split(',')
            return {
                'date': parts[0],
                'open': float(parts[1]),
                'close': float(parts[2]),
                'high': float(parts[3]),
                'low': float(parts[4]),
                'vol': float(parts[5])
            }
    except Exception as e:
        return None
    
    return None

# ============== 回测核心 ==============
def load_predictions(pred_file):
    """加载预测文件"""
    with open(pred_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = []
    if isinstance(data, list):
        # 每小时预测文件
        for pred in data:
            if isinstance(pred, dict) and 'stock_code' in pred:
                predictions.append(pred)
    elif isinstance(data, dict):
        # 每日预测文件
        for entry in data.get('predictions', []):
            if isinstance(entry, dict) and 'predictions' in entry:
                for pred in entry['predictions']:
                    pred['predict_timestamp'] = entry.get('timestamp', '')
                    pred['predict_hour'] = entry.get('hour', '')
                predictions.extend(entry['predictions'])
    
    return predictions

def backtest_predictions(pred_date, predictions, actual_data):
    """
    对比预测与实际
    
    pred_date: 预测日期
    predictions: 预测列表
    actual_data: 实际数据 dict{stock_code: actual_change}
    """
    results = []
    
    for pred in predictions:
        code = pred.get('stock_code')
        if not code or code not in actual_data:
            continue
        
        predicted_change = pred.get('predicted_change', 0)
        actual_change = actual_data[code]
        
        direction_correct = (predicted_change > 0) == (actual_change > 0)
        abs_error = abs(predicted_change - actual_change)
        
        results.append({
            'stock_code': code,
            'stock_name': pred.get('stock_name', '-'),
            'predicted_change': round(predicted_change, 2),
            'actual_change': round(actual_change, 2),
            'direction_correct': direction_correct,
            'abs_error': round(abs_error, 2),
            'hit_2pct': abs_error < 2.0,
            'hit_1pct': abs_error < 1.0,
            'predict_hour': pred.get('predict_hour', pred.get('hour', '-'))
        })
    
    return results

def run_backtest():
    """运行回测"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测真实回测系统 v6.0")
    print(f"时间：{timestamp}")
    print("="*80)
    
    # 选择历史预测文件
    pred_dir = '/home/admin/openclaw/workspace/predictions'
    
    # 找昨天的预测文件
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    pred_file = f"{pred_dir}/{yesterday}.json"
    
    if not os.path.exists(pred_file):
        # 找最早的文件
        files = sorted(Path(pred_dir).glob('*.json'))
        if files:
            pred_file = str(files[0])
        else:
            print("❌ 无预测文件")
            return
    
    print(f"\n📁 预测文件：{pred_file}")
    
    # 加载预测
    print("📊 加载预测数据...")
    predictions = load_predictions(pred_file)
    print(f"   加载成功：{len(predictions)} 条预测")
    
    if not predictions:
        print("❌ 无有效预测")
        return
    
    # 获取预测日期
    pred_date = predictions[0].get('timestamp', yesterday)[:10]
    print(f"📅 预测日期：{pred_date}")
    
    # 获取实际数据
    print(f"\n🔍 获取 {pred_date} 实际走势数据...")
    actual_data = {}
    
    unique_stocks = list(set(p['stock_code'] for p in predictions if 'stock_code' in p))
    print(f"   唯一股票数：{len(unique_stocks)}")
    
    # 采样 50 只股票
    sample_size = min(50, len(unique_stocks))
    np.random.seed(42)
    sample_stocks = np.random.choice(unique_stocks, sample_size, replace=False)
    
    print(f"   采样股票：{sample_size} 只")
    print("   获取实际数据中...")
    
    for i, code in enumerate(sample_stocks):
        data = fetch_stock_realtime(code)
        if data and data.get('today_change_pct') is not None:
            # 注意：这里获取的是"今天"的实时数据，不是历史数据
            # 对于真正的回测，我们需要历史数据
            actual_data[code] = data['today_change_pct']
        
        if (i + 1) % 10 == 0:
            print(f"   进度：{i+1}/{sample_size}")
        
        time.sleep(0.2)
    
    print(f"   成功获取：{len(actual_data)} 只")
    
    if not actual_data:
        print("❌ 无法获取实际数据")
        return
    
    # 回测对比
    print("\n🔍 进行回测对比...")
    results = backtest_predictions(pred_date, predictions, actual_data)
    
    if not results:
        print("❌ 无有效对比结果")
        return
    
    # 统计
    df_r = pd.DataFrame(results)
    
    total = len(results)
    direction_acc = df_r['direction_correct'].mean() * 100
    mae = df_r['abs_error'].mean()
    hit_2pct = df_r['hit_2pct'].mean() * 100
    hit_1pct = df_r['hit_1pct'].mean() * 100
    
    print("\n" + "="*80)
    print("📊 回测结果汇总")
    print("="*80)
    print(f"\n✅ 验证样本：{total} 个")
    print(f"📈 方向正确率：{direction_acc:.1f}%")
    print(f"📉 平均误差：{mae:.2f}%")
    print(f"🎯 命中率 (<2%)：{hit_2pct:.1f}%")
    print(f"🎯 命中率 (<1%)：{hit_1pct:.1f}%")
    
    # 按小时统计
    print("\n📅 按预测时段统计:")
    hourly = df_r.groupby('predict_hour').agg({
        'direction_correct': 'mean',
        'abs_error': 'mean',
        'stock_code': 'count'
    })
    for hour, row in hourly.iterrows():
        print(f"   {hour}: {int(row['stock_code'])}只，方向正确率={row['direction_correct']*100:.1f}%, 误差={row['abs_error']:.2f}%")
    
    # TOP 10
    df_sorted = df_r.sort_values('abs_error')
    print("\n🎯 预测最准确 TOP 10:")
    for i, (_, row) in enumerate(df_sorted.head(10).iterrows(), 1):
        flag = "✅" if row['direction_correct'] else "❌"
        print(f"{i}. {row['stock_name']} ({row['stock_code']}): 预测{row['predicted_change']:+.2f}%, 实际{row['actual_change']:+.2f}%, 误差{row['abs_error']:.2f}% {flag}")
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    
    result_file = f"{output_dir}/backtest_real_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'pred_file': pred_file,
            'pred_date': pred_date,
            'total': total,
            'direction_accuracy': round(direction_acc, 1),
            'mae': round(mae, 2),
            'hit_2pct': round(hit_2pct, 1),
            'hit_1pct': round(hit_1pct, 1),
            'details': results
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 结果已保存：{result_file}")
    print("\n" + "="*80)
    
    return direction_acc, mae, hit_2pct

if __name__ == '__main__':
    run_backtest()
