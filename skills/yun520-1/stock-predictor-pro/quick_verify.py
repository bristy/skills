#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测快速验证 - 5 轮测试
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import time
import os

def run_quick_verify():
    """快速验证"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测快速验证")
    print(f"时间：{timestamp}")
    print("="*80)
    
    # 启动 MCP
    print("\n启动 MCP 服务器...")
    proc = subprocess.Popen(
        ['uvx', 'china-stock-mcp'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(3)
    
    # 初始化
    init = {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'test','version':'1.0'}}}
    proc.stdin.write(json.dumps(init) + '\n')
    proc.stdin.flush()
    proc.stdout.readline()
    print("✅ MCP 已初始化")
    
    # 测试股票（从预测文件中提取）
    pred_file = '/home/admin/openclaw/workspace/predictions/2026-03-17.json'
    with open(pred_file, 'r') as f:
        data = json.load(f)
    
    predictions = []
    for entry in data:
        if isinstance(entry, dict) and 'predictions' in entry:
            predictions.extend(entry['predictions'])
    
    # 采样 10 只股票
    unique_codes = list(set(p['stock_code'] for p in predictions if 'stock_code' in p))[:10]
    pred_dict = {p['stock_code']: p for p in predictions}
    
    print(f"\n📊 测试股票：{len(unique_codes)} 只")
    
    results = []
    
    for i, code in enumerate(unique_codes):
        print(f"[{i+1}/{len(unique_codes)}] {code}...", end=' ')
        
        # 获取预测
        pred = pred_dict.get(code, {})
        predicted_change = pred.get('predicted_change', 0)
        
        # 获取实际数据
        call = {'jsonrpc':'2.0','id':i+2,'method':'tools/call','params':{'name':'get_hist_data','arguments':{'symbol':code,'interval':'day'}}}
        proc.stdin.write(json.dumps(call) + '\n')
        proc.stdin.flush()
        time.sleep(2)
        
        response = proc.stdout.readline()
        
        # 解析
        try:
            resp_data = json.loads(response)
            if 'result' in resp_data and 'content' in resp_data['result']:
                content = resp_data['result']['content'][0].get('text', '')
                lines = content.strip().split('\n')
                if len(lines) >= 3:
                    # 解析最后两行
                    latest = lines[-1].split('|')[1:-1]
                    prev = lines[-2].split('|')[1:-1]
                    
                    if len(latest) >= 5 and len(prev) >= 5:
                        close_latest = float(latest[4].strip())
                        close_prev = float(prev[4].strip())
                        
                        actual_change = ((close_latest - close_prev) / close_prev) * 100
                        
                        direction_correct = (predicted_change > 0) == (actual_change > 0)
                        abs_error = abs(predicted_change - actual_change)
                        
                        results.append({
                            'stock_code': code,
                            'stock_name': pred.get('stock_name', '-'),
                            'predicted': round(predicted_change, 2),
                            'actual': round(actual_change, 2),
                            'correct': direction_correct,
                            'error': round(abs_error, 2)
                        })
                        
                        status = "✅" if direction_correct else "❌"
                        print(f"预测{predicted_change:+.2f}%, 实际{actual_change:+.2f}%, 误差{abs_error:.2f}% {status}")
                    else:
                        print("❌ 数据解析失败")
                else:
                    print("❌ 数据不足")
            else:
                print("❌ 无响应")
        except Exception as e:
            print(f"❌ 错误：{e}")
        
        time.sleep(0.5)
    
    proc.terminate()
    
    # 汇总
    if results:
        df = pd.DataFrame(results)
        total = len(results)
        correct = len(df[df['correct']==True])
        acc = correct / total * 100
        mae = df['error'].mean()
        
        print("\n" + "="*80)
        print("📊 验证结果")
        print("="*80)
        print(f"验证样本：{total} 个")
        print(f"方向正确：{correct}/{total} ({acc:.1f}%)")
        print(f"平均误差：{mae:.2f}%")
        print()
        
        print("📋 详细结果:")
        print(df.to_string(index=False))
        
        # 保存
        output_file = f'/home/admin/openclaw/workspace/stock-recommendations/backtest/quick_verify_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'total': total,
                'correct': correct,
                'accuracy': round(acc, 1),
                'mae': round(mae, 2),
                'details': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 结果已保存：{output_file}")
        
        return acc, mae
    
    return None, None

if __name__ == '__main__':
    run_quick_verify()
