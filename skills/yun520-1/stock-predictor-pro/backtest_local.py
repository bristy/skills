#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测模型回溯测试 v2.0 - 本地数据版
使用本地保存的历史预测数据进行验证，不需要外部 API

方法：
1. 读取 predictions/ 目录中历史预测文件
2. 对比同一股票在不同时间的预测变化
3. 分析预测一致性和稳定性
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def load_predictions(pred_dir: str = '/home/admin/openclaw/workspace/predictions') -> list:
    """加载所有预测文件"""
    predictions = []
    
    if not os.path.exists(pred_dir):
        print(f"❌ 预测目录不存在：{pred_dir}")
        return predictions
    
    for f in sorted(Path(pred_dir).glob('*.json')):
        if '_0' in f.name or f.name.endswith('.json'):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                if isinstance(data, list):
                    # 每小时预测文件
                    for pred in data:
                        pred['source_file'] = f.name
                        pred['load_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    predictions.extend(data)
                elif isinstance(data, dict) and 'predictions' in data:
                    # 每日预测文件（包含多个时段）
                    for entry in data.get('predictions', []):
                        if isinstance(entry, dict) and 'predictions' in entry:
                            for pred in entry['predictions']:
                                pred['source_file'] = f.name
                                pred['timestamp'] = entry.get('timestamp', '')
                                pred['hour'] = entry.get('hour', '')
                            predictions.append(entry)
                        elif isinstance(entry, dict) and 'stock_code' in entry:
                            # 直接是预测列表
                            entry['source_file'] = f.name
                            predictions.append(entry)
            except Exception as e:
                pass
    
    return predictions

def analyze_prediction_stability(predictions: list) -> dict:
    """分析预测稳定性"""
    # 按股票代码分组
    stock_preds = {}
    for pred in predictions:
        code = pred.get('stock_code')
        if not code:
            continue
        
        if code not in stock_preds:
            stock_preds[code] = {
                'name': pred.get('stock_name', '-'),
                'predictions': []
            }
        
        stock_preds[code]['predictions'].append({
            'timestamp': pred.get('timestamp', ''),
            'hour': pred.get('hour', ''),
            'predicted_change': pred.get('predicted_change', 0),
            'current_price': pred.get('current_price', 0),
            'source_file': pred.get('source_file', '')
        })
    
    # 分析每只股票的预测变化
    stability_results = []
    
    for code, data in stock_preds.items():
        preds = data['predictions']
        if len(preds) < 2:
            continue
        
        # 按时间排序
        preds_sorted = sorted(preds, key=lambda x: x['timestamp'] + x['hour'])
        
        # 计算预测变化
        changes = [p['predicted_change'] for p in preds_sorted]
        
        if len(changes) < 2:
            continue
        
        variance = np.var(changes)
        std_dev = np.std(changes)
        mean_pred = np.mean(changes)
        
        # 判断方向一致性
        directions = [1 if c > 0 else (-1 if c < 0 else 0) for c in changes]
        direction_consistency = len([d for d in directions if d == directions[0]]) / len(directions)
        
        # 最大变化幅度
        max_change = max(changes)
        min_change = min(changes)
        range_change = max_change - min_change
        
        stability_results.append({
            'stock_code': code,
            'stock_name': data['name'],
            'prediction_count': len(preds_sorted),
            'mean_prediction': round(mean_pred, 2),
            'variance': round(variance, 2),
            'std_dev': round(std_dev, 2),
            'direction_consistency': round(direction_consistency * 100, 1),
            'max_prediction': round(max_change, 2),
            'min_prediction': round(min_change, 2),
            'range': round(range_change, 2),
            'is_stable': variance < 1.0,
            'first_timestamp': preds_sorted[0]['timestamp'],
            'last_timestamp': preds_sorted[-1]['timestamp']
        })
    
    return stability_results

def analyze_accuracy_by_time(predictions: list) -> dict:
    """分析不同时间段的预测准确性（基于预测变化）"""
    # 按小时分组
    hourly_preds = {}
    
    for pred in predictions:
        hour = pred.get('hour', 'unknown')
        if hour not in hourly_preds:
            hourly_preds[hour] = []
        hourly_preds[hour].append(pred.get('predicted_change', 0))
    
    hourly_stats = {}
    for hour, preds in hourly_preds.items():
        if not preds:
            continue
        
        hourly_stats[hour] = {
            'count': len(preds),
            'mean': round(np.mean(preds), 2),
            'std': round(np.std(preds), 2),
            'max': round(max(preds), 2),
            'min': round(min(preds), 2)
        }
    
    return hourly_stats

def generate_report(stability_results: list, hourly_stats: dict, timestamp: str) -> str:
    """生成 Markdown 报告"""
    df = pd.DataFrame(stability_results)
    
    if df.empty:
        return "❌ 没有足够的预测数据进行分析"
    
    # 按稳定性排序
    df_sorted = df.sort_values('variance')
    
    # 统计
    total_stocks = len(df)
    stable_stocks = len(df[df['is_stable'] == True])
    avg_variance = df['variance'].mean()
    avg_direction_consistency = df['direction_consistency'].mean()
    
    md = f"""# 📊 股票预测稳定性分析报告

**分析时间**: {timestamp}
**分析方法**: 基于历史预测数据，分析同一股票在不同时段的预测变化

---

## 📈 总体统计

| 指标 | 数值 |
|------|------|
| 分析股票数量 | {total_stocks} |
| 预测稳定股票 | {stable_stocks} ({stable_stocks/total_stocks*100:.1f}%) |
| 平均预测方差 | {avg_variance:.2f} |
| 平均方向一致性 | {avg_direction_consistency:.1f}% |

---

## 🎯 预测最稳定的股票 TOP 20

| 排名 | 代码 | 名称 | 预测次数 | 方差 | 方向一致性 | 平均预测 |
|------|------|------|----------|------|------------|----------|
"""
    
    for i, (_, row) in enumerate(df_sorted.head(20).iterrows(), 1):
        md += f"| {i} | {row['stock_code']} | {row['stock_name']} | {row['prediction_count']} | {row['variance']:.2f} | {row['direction_consistency']:.1f}% | {row['mean_prediction']:+.2f}% |\n"
    
    md += f"""
---

## ⚠️  预测波动最大的股票 TOP 10

| 排名 | 代码 | 名称 | 预测次数 | 方差 | 预测范围 | 平均预测 |
|------|------|------|----------|------|----------|----------|
"""
    
    df_volatile = df_sorted.sort_values('variance', ascending=False)
    for i, (_, row) in enumerate(df_volatile.head(10).iterrows(), 1):
        md += f"| {i} | {row['stock_code']} | {row['stock_name']} | {row['prediction_count']} | {row['variance']:.2f} | {row['min_prediction']:+.2f}% ~ {row['max_prediction']:+.2f}% | {row['mean_prediction']:+.2f}% |\n"
    
    md += f"""
---

## 📊 预测方向一致性分析

| 一致性区间 | 股票数量 | 占比 |
|------------|----------|------|
"""
    
    consistency_bins = [
    (90, 100, "90-100%"),
    (70, 90, "70-90%"),
    (50, 70, "50-70%"),
    (0, 50, "0-50%")
    ]
    
    for low, high, label in consistency_bins:
        count = len(df[(df['direction_consistency'] >= low) & (df['direction_consistency'] < high)])
        pct = count / total_stocks * 100 if total_stocks > 0 else 0
        md += f"| {label} | {count} | {pct:.1f}% |\n"
    
    md += f"""
---

## 📋 分析结论

### 预测稳定性评估

1. **稳定股票比例**: {stable_stocks/total_stocks*100:.1f}% 的股票预测方差<1.0
   - 方差<1.0：预测相对稳定，模型信心足
   - 方差>2.0：预测波动大，模型犹豫不决

2. **方向一致性**: 平均 {avg_direction_consistency:.1f}% 的预测方向保持一致
   - >90%：模型非常确定
   - 70-90%：模型比较确定
   - <70%：模型存在犹豫

3. **预测范围**: 波动大的股票预测范围可达 {df['range'].max():.2f}%

### 模型问题诊断

- **如果稳定股票比例<50%**: 模型对大部分股票缺乏信心
- **如果方向一致性<70%**: 模型预测方向频繁变化，需要调整
- **如果平均方差>2.0**: 预测幅度过大，需要保守收缩

---

## 🔧 优化建议

基于稳定性分析，建议：

1. **对波动大的股票**: 降低预测权重，增加波动率惩罚
2. **对方向不一致的股票**: 检查技术指标是否冲突
3. **整体保守化**: 如果平均预测幅度>3%，进一步收缩

---

*免责声明：本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。*
"""
    
    return md

def run_analysis():
    """运行分析"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测稳定性分析 v2.0")
    print(f"分析时间：{timestamp}")
    print("="*80)
    
    # 加载预测数据
    print("\n📊 加载历史预测数据...")
    predictions = load_predictions()
    print(f"   加载成功：{len(predictions)} 条预测记录")
    
    if not predictions:
        print("❌ 没有预测数据")
        return
    
    # 分析稳定性
    print("\n🔍 分析预测稳定性...")
    stability_results = analyze_prediction_stability(predictions)
    print(f"   分析股票：{len(stability_results)} 只")
    
    # 分析时段准确性
    print("\n🔍 分析时段差异...")
    hourly_stats = analyze_accuracy_by_time(predictions)
    print(f"   时段数量：{len(hourly_stats)}")
    
    # 生成报告
    print("\n📝 生成分析报告...")
    md_report = generate_report(stability_results, hourly_stats, timestamp)
    
    # 保存
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    
    md_file = f"{output_dir}/stability_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    # 保存 JSON 数据（处理 numpy 类型）
    json_file = f"{output_dir}/stability_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    
    # 转换 numpy 类型为 Python 原生类型
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
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'stability_results': convert_numpy(stability_results),
            'hourly_stats': convert_numpy(hourly_stats)
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✅ 分析完成！")
    print(f"📁 Markdown 报告：{md_file}")
    print(f"📁 JSON 数据：{json_file}")
    
    # 打印摘要
    if stability_results:
        df = pd.DataFrame(stability_results)
        print(f"\n📊 关键指标:")
        print(f"   分析股票：{len(df)} 只")
        print(f"   稳定股票：{len(df[df['is_stable']==True])} 只 ({len(df[df['is_stable']==True])/len(df)*100:.1f}%)")
        print(f"   平均方差：{df['variance'].mean():.2f}")
        print(f"   平均方向一致性：{df['direction_consistency'].mean():.1f}%")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    run_analysis()
