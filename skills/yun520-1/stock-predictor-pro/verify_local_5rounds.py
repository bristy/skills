#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用本地历史预测数据进行 5 轮验证
每轮 10 只股票，对比预测一致性
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
import os
from pathlib import Path

def load_all_predictions():
    """加载所有历史预测"""
    pred_dir = '/home/admin/openclaw/workspace/predictions'
    all_preds = {}  # {stock_code: [{timestamp, predicted_change, ...}]}
    
    for f in Path(pred_dir).glob('*.json'):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and 'predictions' in entry:
                        ts = entry.get('timestamp', '')
                        hour = entry.get('hour', '')
                        for pred in entry['predictions']:
                            code = pred.get('stock_code')
                            if code:
                                if code not in all_preds:
                                    all_preds[code] = []
                                all_preds[code].append({
                                    'timestamp': ts,
                                    'hour': hour,
                                    'predicted_change': pred.get('predicted_change', 0),
                                    'current_price': pred.get('current_price', 0),
                                    'file': f.name
                                })
        except Exception as e:
            pass
    
    return all_preds

def verify_round(all_preds, round_num, sample_size=10):
    """单轮验证"""
    # 找到预测次数最多的股票
    stock_counts = [(code, len(preds)) for code, preds in all_preds.items()]
    stock_counts.sort(key=lambda x: x[1], reverse=True)
    
    # 每轮使用不同的股票
    start_idx = (round_num - 1) * sample_size
    selected = stock_counts[start_idx:start_idx + sample_size]
    
    results = []
    
    for code, count in selected:
        preds = all_preds[code]
        if len(preds) < 3:
            continue
        
        # 按时间排序
        preds_sorted = sorted(preds, key=lambda x: x['timestamp'] + x['hour'])
        
        # 计算预测变化
        changes = [p['predicted_change'] for p in preds_sorted]
        variance = np.var(changes)
        std_dev = np.std(changes)
        mean_pred = np.mean(changes)
        
        # 方向一致性
        directions = [1 if c > 0 else (-1 if c < 0 else 0) for c in changes]
        direction_consistency = len([d for d in directions if d == directions[0]]) / len(directions)
        
        # 最大变化范围
        max_change = max(changes)
        min_change = min(changes)
        range_change = max_change - min_change
        
        # 稳定性评估
        is_stable = variance < 1.0
        
        results.append({
            'stock_code': code,
            'stock_name': preds[0].get('stock_name', '-'),
            'prediction_count': len(preds_sorted),
            'mean_prediction': round(mean_pred, 2),
            'variance': round(variance, 2),
            'std_dev': round(std_dev, 2),
            'direction_consistency': round(direction_consistency * 100, 1),
            'max_prediction': round(max_change, 2),
            'min_prediction': round(min_change, 2),
            'range': round(range_change, 2),
            'is_stable': is_stable,
        })
    
    return results

def run_verify():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"本地历史预测数据验证 (5 轮)")
    print(f"时间：{ts}")
    print("="*80)
    
    # 加载数据
    print("\n📊 加载历史预测数据...")
    all_preds = load_all_predictions()
    print(f"   加载成功：{len(all_preds)} 只股票")
    
    total_preds = sum(len(p) for p in all_preds.values())
    print(f"   总预测数：{total_preds} 条")
    
    # 5 轮验证
    all_results = []
    
    for round_num in range(1, 6):
        print(f"\n{'='*80}")
        print(f"🔍 第 {round_num}/5 轮验证 (10 只股票)")
        print(f"{'='*80}")
        
        results = verify_round(all_preds, round_num, sample_size=10)
        
        if results:
            df = pd.DataFrame(results)
            stable = len(df[df['is_stable']==True])
            avg_variance = df['variance'].mean()
            avg_direction = df['direction_consistency'].mean()
            
            print(f"\n✅ 验证股票：{len(results)} 只")
            print(f"📈 稳定股票：{stable} 只 ({stable/len(results)*100:.1f}%)")
            print(f"📉 平均方差：{avg_variance:.2f}")
            print(f"🎯 平均方向一致性：{avg_direction:.1f}%")
            
            print(f"\n📋 详情:")
            print(f"{'代码':<8} {'名称':<10} {'预测次数':<8} {'方差':<8} {'方向一致性':<12} {'稳定性':<8}")
            print("-"*60)
            for r in results:
                stable_flag = "✅" if r['is_stable'] else "⚠️"
                print(f"{r['stock_code']:<8} {r['stock_name']:<10} {r['prediction_count']:<8} {r['variance']:<8.2f} {r['direction_consistency']:<12.1f}% {stable_flag}")
            
            all_results.extend(results)
        else:
            print(f"❌ 第{round_num}轮验证失败")
        
        import time
        time.sleep(0.5)
    
    # 汇总
    print("\n" + "="*80)
    print("📊 5 轮验证汇总")
    print("="*80)
    
    if all_results:
        df_all = pd.DataFrame(all_results)
        total = len(all_results)
        stable_total = len(df_all[df_all['is_stable']==True])
        avg_var = df_all['variance'].mean()
        avg_dir = df_all['direction_consistency'].mean()
        
        print(f"\n总验证股票：{total} 只")
        print(f"稳定股票：{stable_total} 只 ({stable_total/total*100:.1f}%)")
        print(f"平均方差：{avg_var:.2f}")
        print(f"平均方向一致性：{avg_dir:.1f}%")
        
        # 评估
        print("\n" + "="*80)
        print("🎯 模型评估")
        print("="*80)
        
        if stable_total/total >= 0.6:
            print(f"✅ 稳定股票比例 {stable_total/total*100:.1f}% - 模型信心足（>60%）")
        else:
            print(f"⚠️  稳定股票比例 {stable_total/total*100:.1f}% - 模型犹豫（<60%）")
        
        if avg_var < 1.0:
            print(f"✅ 平均方差 {avg_var:.2f} - 预测稳定（<1.0）")
        elif avg_var < 2.0:
            print(f"⚠️  平均方差 {avg_var:.2f} - 可接受（1-2）")
        else:
            print(f"❌ 平均方差 {avg_var:.2f} - 波动大（>2）")
        
        if avg_dir >= 80:
            print(f"✅ 方向一致性 {avg_dir:.1f}% - 非常确定（>80%）")
        elif avg_dir >= 60:
            print(f"⚠️  方向一致性 {avg_dir:.1f}% - 比较确定（60-80%）")
        else:
            print(f"❌ 方向一致性 {avg_dir:.1f}% - 存在犹豫（<60%）")
        
        # 保存 (处理 numpy 类型)
        def convert(obj):
            if isinstance(obj, (np.integer, np.int64)): return int(obj)
            elif isinstance(obj, (np.floating, np.float64)): return float(obj)
            elif isinstance(obj, np.bool_): return bool(obj)
            elif isinstance(obj, dict): return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list): return [convert(i) for i in obj]
            return obj
        
        output = f'/home/admin/openclaw/workspace/stock-recommendations/backtest/verify_local_5rounds_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
        with open(output, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': ts,
                'total_stocks': len(all_preds),
                'total_predictions': total_preds,
                'rounds': 5,
                'verified': total,
                'stable': stable_total,
                'stability_rate': round(stable_total/total*100, 1),
                'avg_variance': round(avg_var, 2),
                'avg_direction_consistency': round(avg_dir, 1),
                'details': convert(all_results)
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 结果已保存：{output}")
        
        return stable_total/total*100, avg_var, avg_dir
    
    return None, None, None

if __name__ == '__main__':
    run_verify()
