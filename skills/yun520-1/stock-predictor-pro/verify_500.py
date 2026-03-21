#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测验证脚本 - 500 只股票验证版
验证今日预测 vs 实际走势，生成详细表格报告
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import os
import sys

def fetch_stock_realtime(ts_code):
    """获取股票实时行情（包含今日涨跌幅）- 使用东方财富 API"""
    try:
        market = "SH" if ts_code.startswith('6') else "SZ"
        code = f"{market}.{ts_code}"
        
        # 东方财富实时行情 API
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={code}&fields=f43,f44,f45,f46,f47,f117,f118,f119,f120,f121,f122,f84,f85,f107,f104,f105,f106,f57,f58,f169,f170,f152,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f151,f153,f154,f155,f156,f157,f158,f159,f160,f161,f162,f163,f164,f165,f166,f167,f168"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if not data.get('data'):
            return None
        
        d = data['data']
        current_price = float(d['f43']) if d.get('f43') else 0  # 当前价
        pre_close = float(d['f60']) if d.get('f60') else 0  # 昨收
        today_change_pct = float(d['f170']) if d.get('f170') else 0  # 今日涨跌幅%
        
        if current_price == 0:
            return None
        
        return {
            'current_price': current_price / 100,  # 东方财富价格单位是分
            'pre_close': pre_close / 100,
            'today_change_pct': today_change_pct / 100  # 百分比
        }
    except Exception as e:
        return None

def fetch_stock_history(ts_code, days=10):
    """获取股票历史 K 线数据"""
    try:
        market = "SH" if ts_code.startswith('6') else "SZ"
        code = f"{market}.{ts_code}"
        
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
        
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={code}&klt=101&fqt=1&beg={start_date}&end={end_date}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if not data.get('data') or not data['data'].get('klines'):
            return None
        
        klines = data['data']['klines']
        df = pd.DataFrame([k.split(',') for k in klines])
        df.columns = ['date', 'open', 'close', 'high', 'low', 'vol', 'turn', 'amt']
        df['close'] = pd.to_numeric(df['close'])
        df['date'] = pd.to_datetime(df['date'])
        
        return df.tail(days)
    except Exception as e:
        return None

def verify_prediction(stock_code, predicted_change, predictions_dict):
    """验证单只股票预测准确率"""
    # 获取实时行情
    realtime = fetch_stock_realtime(stock_code)
    if not realtime:
        return None
    
    actual_change = realtime['today_change_pct']
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
    else:
        predictions = data[-1]['predictions'] if data else []
    
    print(f"📊 今日预测总数：{len(predictions)} 只股票")
    
    # 随机采样
    np.random.seed(int(datetime.now().timestamp()) % 1000)
    if len(predictions) >= sample_size:
        sample_indices = np.random.choice(len(predictions), sample_size, replace=False)
        sample_stocks = [predictions[i] for i in sample_indices]
    else:
        sample_stocks = predictions
    
    print(f"🔍 验证样本：{len(sample_stocks)} 只股票")
    print("\n正在获取实时行情数据...\n")
    
    # 验证
    results = []
    success = 0
    direction_success = 0
    
    for i, stock in enumerate(sample_stocks):
        ts_code = stock['stock_code']
        pred_change = stock['predicted_change']
        
        result = verify_prediction(ts_code, pred_change, predictions)
        
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
    print(f"精确命中（误差<2%）：{success}/{len(results)} ({exact_accuracy*100:.1f}%)")
    print(f"方向正确：{direction_success}/{len(results)} ({direction_accuracy*100:.1f}%)")
    print(f"平均幅度误差：{avg_error:.2f}%")
    print("="*80)
    
    # 生成详细表格
    df_results = pd.DataFrame(results)
    
    # 按误差排序
    df_sorted = df_results.sort_values('amplitude_error')
    
    print("\n📋 验证详情 TOP 20（按精确度排序）:")
    print("-"*80)
    print(df_sorted[['stock_code', 'predicted_change', 'actual_change', 'amplitude_error', 'direction_correct']].head(20).to_string(index=False))
    
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
        md += f"| {i+1} | {row['stock_code']} | - | {row['predicted_change']:+.2f} | {row['actual_change']:+.2f} | {row['amplitude_error']:.2f} | {'✅' if row['direction_correct'] else '❌'} |\n"
    
    md += f"""
---

## 📈 实际涨幅 TOP 10（验证预测准确性）

| 排名 | 代码 | 名称 | 预测涨幅% | 实际涨幅% | 误差% | 预测方向 |
|------|------|------|-----------|-----------|-------|----------|
"""
    
    for i, row in df_up.iterrows():
        pred_direction = "上涨" if row['predicted_change'] > 0 else ("下跌" if row['predicted_change'] < 0 else "盘整")
        md += f"| {i+1} | {row['stock_code']} | - | {row['predicted_change']:+.2f} | {row['actual_change']:+.2f} | {row['amplitude_error']:.2f} | {pred_direction} |\n"
    
    md += f"""
---

## 📉 实际跌幅 TOP 10（验证预测准确性）

| 排名 | 代码 | 名称 | 预测涨幅% | 实际涨幅% | 误差% | 预测方向 |
|------|------|------|-----------|-----------|-------|----------|
"""
    
    for i, row in df_down.iterrows():
        pred_direction = "上涨" if row['predicted_change'] > 0 else ("下跌" if row['predicted_change'] < 0 else "盘整")
        md += f"| {i+1} | {row['stock_code']} | - | {row['predicted_change']:+.2f} | {row['actual_change']:+.2f} | {row['amplitude_error']:.2f} | {pred_direction} |\n"
    
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
