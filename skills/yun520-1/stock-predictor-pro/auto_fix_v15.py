#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v15.0 自动修复版
基于验证结果自动调整预测参数
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
import subprocess
import time

def get_latest_predictions():
    """获取最新预测"""
    with open('/home/admin/openclaw/workspace/predictions/2026-03-18.json', 'r') as f:
        data = json.load(f)
    return data[-1]['predictions']

def verify_with_mcp(codes, timeout=2):
    """使用 MCP 验证"""
    mcp = subprocess.Popen(['uvx', 'china-stock-mcp'], 
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, text=True)
    time.sleep(3)
    
    init = {'jsonrpc':'2.0','id':1,'method':'initialize',
            'params':{'protocolVersion':'2024-11-05','capabilities':{},
                     'clientInfo':{'name':'verify','version':'1.0'}}}
    mcp.stdin.write(json.dumps(init)+'\n'); mcp.stdin.flush(); mcp.stdout.readline()
    
    results = []
    for code in codes:
        call = {'jsonrpc':'2.0','method':'tools/call',
                'params':{'name':'get_hist_data','arguments':{'symbol':code,'interval':'day'}}}
        mcp.stdin.write(json.dumps(call)+'\n'); mcp.stdin.flush()
        time.sleep(timeout)
        
        try:
            resp = json.loads(mcp.stdout.readline())
            content = resp['result']['content'][0]['text'].strip().split('\n')
            if len(content) >= 2:
                latest = content[-1].split('|')[1:-1]
                prev = content[-2].split('|')[1:-1]
                if len(latest) >= 5:
                    close_now = float(latest[4].strip())
                    close_prev = float(prev[4].strip())
                    actual = (close_now - close_prev) / close_prev * 100
                    results.append({'code': code, 'actual': actual, 'close': close_now})
        except:
            pass
    
    mcp.terminate()
    return results

def calculate_adjustment_factor(predictions, verifications):
    """计算调整系数"""
    factors = []
    
    for v in verifications:
        code = v['code']
        actual = v['actual']
        
        # 找到对应预测
        for p in predictions:
            if p.get('stock_code') == code:
                pred = p.get('predicted_change', 0)
                if pred != 0:
                    factor = actual / pred
                    factors.append(min(2.0, max(0.5, factor)))  # 限制在 0.5-2.0
                break
    
    if factors:
        return np.median(factors)
    return 1.0

def run_auto_fix():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('='*80)
    print(f'v15.0 自动修复系统')
    print(f'时间：{ts}')
    print('='*80)
    
    # 获取预测
    print('\n📊 获取最新预测...')
    preds = get_latest_predictions()
    print(f'   预测数量：{len(preds)} 只')
    
    # 采样验证（前 10 只）
    codes = [p['stock_code'] for p in preds[:10]]
    print(f'\n🔍 验证股票：{len(codes)} 只')
    
    # 验证
    print('\n⏳ 获取实时数据...')
    verifications = verify_with_mcp(codes, timeout=1.5)
    print(f'   成功获取：{len(verifications)} 只')
    
    if len(verifications) < 3:
        print('\n❌ 验证样本不足，无法修复')
        return
    
    # 计算调整系数
    adj_factor = calculate_adjustment_factor(preds, verifications)
    print(f'\n📈 调整系数：{adj_factor:.2f}')
    
    # 评估
    if 0.8 <= adj_factor <= 1.2:
        print('✅ 预测准确 - 无需大幅调整')
    elif adj_factor > 1.2:
        print('⚠️  预测偏低 - 需要上调预测')
    else:
        print('⚠️  预测偏高 - 需要下调预测')
    
    # 保存配置
    config = {
        'timestamp': ts,
        'adjustment_factor': round(adj_factor, 2),
        'verified_stocks': len(verifications),
        'recommendation': 'increase' if adj_factor > 1.2 else ('decrease' if adj_factor < 0.8 else 'maintain')
    }
    
    config_file = '/home/admin/openclaw/workspace/stock_system/auto_fix_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f'\n📁 配置已保存：{config_file}')
    print(f'\n建议操作:')
    if adj_factor > 1.2:
        print(f'  - 将预测涨幅乘以 {adj_factor:.2f}')
        print(f'  - 或调整趋势权重 +20%')
    elif adj_factor < 0.8:
        print(f'  - 将预测涨幅乘以 {adj_factor:.2f}')
        print(f'  - 或调整趋势权重 -20%')
    else:
        print(f'  - 保持当前参数')
    
    return config

if __name__ == '__main__':
    run_auto_fix()
