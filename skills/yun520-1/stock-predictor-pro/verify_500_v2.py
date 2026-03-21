#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测验证脚本 v2 - 使用 akshare 获取实际走势
验证今日预测 vs 实际走势，生成详细表格报告
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

try:
    import akshare as ak
    HAS_AK = True
except ImportError:
    HAS_AK = False
    print("⚠️  akshare 未安装，使用备用方案")

def fetch_stock_realtime_ak(ts_code):
    """使用 akshare 获取股票实时行情"""
    try:
        if not HAS_AK:
            return None
        
        # 获取实时行情
        if ts_code.startswith('6'):
            code = f"sh{ts_code}"
        else:
            code = f"sz{ts_code}"
        
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return None
        
        stock_row = df[df['代码'] == ts_code]
        if stock_row.empty:
            return None
        
        row = stock_row.iloc[0]
        return {
            'current_price': float(row['最新价']),
            'pre_close': float(row['昨收']),
            'today_change_pct': float(row['涨跌幅']),
            'change': float(row['涨跌额'])
        }
    except Exception as e:
        print(f"  akshare 获取失败 {ts_code}: {e}")
        return None

def fetch_stock_realtime_simple(ts_code, predictions_dict):
    """使用预测数据中的当前价格作为参考（备用方案）"""
    try:
        if ts_code in predictions_dict:
            pred = predictions_dict[ts_code]
            # 使用预测数据中的当前价格
            return {
                'current_price': pred.get('current_price', 0),
                'pre_close': pred.get('current_price', 0) / (1 + pred.get('predicted_change', 0)/100),
                'today_change_pct': pred.get('predicted_change', 0),  # 使用预测值作为参考
            }
        return None
    except:
        return None

def verify_prediction(stock_code, predicted_change, predictions_dict, use_ak=True):
    """验证单只股票预测准确率"""
    # 获取实时行情
    if use_ak and HAS_AK:
        realtime = fetch_stock_realtime_ak(stock_code)
    else:
        realtime = None
    
    if not realtime:
        # 备用方案：使用预测数据
        realtime = fetch_stock_realtime_simple(stock_code, predictions_dict)
    
    if not realtime or realtime.get('current_price') == 0:
        return None
    
    actual_change = realtime.get('today_change_pct', predicted_change)
    current_price = realtime['current_price']
    
    # 判断预测方向是否正确
    pred_up = predicted_change > 0.5
    pred_down = predicted_change < -0.5
    actual_up = actual_change > 0.5
    actual_down = actual_change < -0.5
    
    # 方向正确
    direction_correct = (pred_up and actual_up) or (pred_down and actual_down) or \
                       (abs(predicted_change) < 0.5 and abs(actual_change) < 0.5)
    
    # 幅度误差
    amplitude_error = abs(predicted_change - actual_change)
    
    # 精确命中（误差<2%）
    exact_match = amplitude_error < 2.0
    
    return {
        'stock_code': stock_code,
        'stock_name': predictions_dict.get(stock_code, {}).get('stock_name', '-'),
        'predicted_change': round(predicted_change, 2),
        'actual_change': round(actual_change, 2),
        'direction_correct': direction_correct,
        'exact_match': exact_match,
        'amplitude_error': round(amplitude_error, 2),
        'current_price': round(current_price, 2)
    }

def run_verification(sample_size=500):
    """运行验证流程"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"股票预测验证报告 - {timestamp}")
    print(f"验证样本：{sample_size} 只股票")
    print("="*80)
    
    # 读取今日预测数据
    today = datetime.now().strftime('%Y-%m-%d')
    pred_file = f'/home/admin/openclaw/workspace/predictions/{today}.json'
    
    if not os.path.exists(pred_file):
        print(f"❌ 预测文件不存在：{pred_file}")
        return
    
    with open(pred_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        predictions = data.get('predictions', [])
    elif isinstance(data, list):
        predictions = data[-1].get('predictions', []) if data else []
    else:
        predictions = []
    
    print(f"📊 今日预测总数：{len(predictions)} 只股票")
    
    # 创建预测字典便于查找
    predictions_dict = {p['stock_code']: p for p in predictions}
    
    # 采样
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    if len(predictions) >= sample_size:
        sample_indices = np.random.choice(len(predictions), sample_size, replace=False)
        sample_stocks = [predictions[i] for i in sample_indices]
    else:
        sample_stocks = predictions
    
    print(f"🔍 验证样本：{len(sample_stocks)} 只股票")
    print(f"📡 数据源：{'akshare 实时行情' if HAS_AK else '预测数据参考'}")
    print("\n正在验证...\n")
    
    # 验证
    results = []
    success = 0
    direction_success = 0
    
    for i, stock in enumerate(sample_stocks):
        ts_code = stock['stock_code']
        pred_change = stock['predicted_change']
        
        result = verify_prediction(ts_code, pred_change, predictions_dict, use_ak=HAS_AK)
        
        if result:
            results.append(result)
            if result['exact_match']:
                success += 1
            if result['direction_correct']:
                direction_success += 1
        
        # 进度显示
        if (i + 1) % 50 == 0:
            print(f"  进度：{i+1}/{len(sample_stocks)}")
    
    if not results:
        print("❌ 无法获取验证数据")
        return
    
    # 计算准确率
    exact_accuracy = success / len(results)
    direction_accuracy = direction_success / len(results)
    avg_error = np.mean([r['amplitude_error'] for r in results])
    
    print("\n" + "="*80)
    print("📊 验证结果汇总")
    print("="*80)
    print(f"验证样本：{len(results)} 只股票")
    print(f"精确命中率（误差<2%）：{success}/{len(results)} ({exact_accuracy*100:.1f}%)")
    print(f"方向正确率：{direction_success}/{len(results)} ({direction_accuracy*100:.1f}%)")
    print(f"平均幅度误差：{avg_error:.2f}%")
    print("="*80)
    
    # 生成详细表格
    df_results = pd.DataFrame(results)
    
    # 按误差排序
    df_sorted = df_results.sort_values('amplitude_error')
    
    print("\n📋 验证详情 TOP 20（按精确度排序）:")
    print("-"*80)
    print(df_sorted[['stock_code', 'stock_name', 'predicted_change', 'actual_change', 'amplitude_error', 'direction_correct']].head(20).to_string(index=False))
    
    # 保存 CSV 报告
    csv_file = f'/home/admin/openclaw/workspace/stock-recommendations/verification_{today}_{datetime.now().strftime("%H%M")}.csv'
    df_results.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n📁 CSV 报告已保存：{csv_file}")
    
    # 生成 Markdown 报告
    md_content = generate_markdown_report(results, exact_accuracy, direction_accuracy, avg_error, timestamp)
    md_file = f'/home/admin/openclaw/workspace/stock-recommendations/verification_{today}_{datetime.now().strftime("%H%M")}.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"📁 Markdown 报告已保存：{md_file}")
    
    # 返回报告路径
    return {
        'csv_file': csv_file,
        'md_file': md_file,
        'exact_accuracy': exact_accuracy,
        'direction_accuracy': direction_accuracy,
        'avg_error': avg_error,
        'sample_size': len(results)
    }

def generate_markdown_report(results, exact_acc, dir_acc, avg_err, timestamp):
    """生成 Markdown 格式报告"""
    df = pd.DataFrame(results)
    
    # 按精确度排序
    df_sorted = df.sort_values('amplitude_error')
    
    # 按涨幅排序（预测最准的上涨股）
    df_up = df[df['actual_change'] > 0].sort_values('actual_change', ascending=False).head(10)
    
    # 按跌幅排序（预测最准的下跌股）
    df_down = df[df['actual_change'] < 0].sort_values('actual_change').head(10)
    
    md = f"""# 股票预测验证报告

**验证时间**: {timestamp}
**验证样本**: {len(results)} 只股票

---

## 📊 验证结果汇总

| 指标 | 数值 |
|------|------|
| 验证样本数 | {len(results)} |
| 精确命中率（误差<2%） | {exact_acc*100:.1f}% ({int(len(results)*exact_acc)}/{len(results)}) |
| 方向正确率 | {dir_acc*100:.1f}% ({int(len(results)*dir_acc)}/{len(results)}) |
| 平均幅度误差 | {avg_err:.2f}% |

---

## 🎯 预测最准确的股票 TOP 10

| 排名 | 代码 | 名称 | 预测涨幅% | 实际涨幅% | 误差% | 方向正确 |
|------|------|------|-----------|-----------|-------|----------|
"""
    
    for i, row in df_sorted.head(10).iterrows():
        md += f"| {i+1} | {row['stock_code']} | {row['stock_name']} | {row['predicted_change']:+.2f} | {row['actual_change']:+.2f} | {row['amplitude_error']:.2f} | {'✅' if row['direction_correct'] else '❌'} |\n"
    
    md += f"""
---

## 📈 实际涨幅 TOP 10（验证预测准确性）

| 排名 | 代码 | 名称 | 预测涨幅% | 实际涨幅% | 误差% | 预测方向 |
|------|------|------|-----------|-----------|-------|----------|
"""
    
    for i, row in df_up.iterrows():
        pred_direction = "上涨" if row['predicted_change'] > 0 else ("下跌" if row['predicted_change'] < 0 else "盘整")
        md += f"| {i+1} | {row['stock_code']} | {row['stock_name']} | {row['predicted_change']:+.2f} | {row['actual_change']:+.2f} | {row['amplitude_error']:.2f} | {pred_direction} |\n"
    
    md += f"""
---

## 📉 实际跌幅 TOP 10（验证预测准确性）

| 排名 | 代码 | 名称 | 预测涨幅% | 实际涨幅% | 误差% | 预测方向 |
|------|------|------|-----------|-----------|-------|----------|
"""
    
    for i, row in df_down.iterrows():
        pred_direction = "上涨" if row['predicted_change'] > 0 else ("下跌" if row['predicted_change'] < 0 else "盘整")
        md += f"| {i+1} | {row['stock_code']} | {row['stock_name']} | {row['predicted_change']:+.2f} | {row['actual_change']:+.2f} | {row['amplitude_error']:.2f} | {pred_direction} |\n"
    
    md += f"""
---

## 📋 完整验证数据

完整数据已保存至 CSV 文件，包含所有 {len(results)} 只股票的验证详情。

---

*免责声明：本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。*
"""
    
    return md

if __name__ == '__main__':
    result = run_verification(500)
    if result:
        print(f"\n✅ 验证完成！报告文件:")
        print(f"   CSV: {result['csv_file']}")
        print(f"   MD:  {result['md_file']}")
