#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
50 只股票历史数据验证
使用 MCP 获取真实历史数据，对比预测 vs 实际
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import time

class MCPClient:
    def __init__(self):
        self.proc = None
        self.request_id = 0
    
    def start(self):
        print("启动 MCP 服务器...")
        self.proc = subprocess.Popen(
            ['uvx', 'china-stock-mcp'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(3)
        init = {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'verify','version':'1.0'}}}
        self._send(init)
        self._receive()
        print("✅ MCP 已初始化")
    
    def _send(self, req):
        self.request_id += 1
        req['id'] = self.request_id
        self.proc.stdin.write(json.dumps(req) + '\n')
        self.proc.stdin.flush()
    
    def _receive(self):
        return json.loads(self.proc.stdout.readline())
    
    def get_hist(self, symbol):
        req = {'jsonrpc':'2.0','method':'tools/call','params':{'name':'get_hist_data','arguments':{'symbol':symbol,'interval':'day'}}}
        self._send(req)
        return self._receive()
    
    def close(self):
        if self.proc:
            self.proc.terminate()

def parse_table(resp):
    try:
        content = resp['result']['content'][0]['text']
        lines = content.strip().split('\n')
        if len(lines) < 3:
            return None
        headers = [h.strip() for h in lines[0].split('|')[1:-1]]
        data = []
        for line in lines[2:]:
            if not line.strip():
                continue
            vals = [v.strip() for v in line.split('|')[1:-1]]
            if len(vals) == len(headers):
                row = {}
                for h, v in zip(headers, vals):
                    try:
                        row[h] = float(v) if '.' in v else int(v)
                    except:
                        row[h] = v
                data.append(row)
        return data
    except:
        return None

def run_verify():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("="*80)
    print(f"50 只股票历史验证")
    print(f"时间：{ts}")
    print("="*80)
    
    # 加载预测
    with open('/home/admin/openclaw/workspace/predictions/2026-03-18.json', 'r') as f:
        data = json.load(f)
    
    preds = []
    for entry in data:
        if isinstance(entry, dict) and 'predictions' in entry:
            preds.extend(entry['predictions'])
    
    # 采样 50 只
    unique = list(set(p['stock_code'] for p in preds if 'stock_code' in p))[:50]
    pred_dict = {p['stock_code']: p for p in preds}
    
    print(f"\n📊 验证股票：{len(unique)} 只")
    print(f"📈 数据来源：MCP china-stock-mcp")
    print()
    
    # 启动 MCP
    mcp = MCPClient()
    try:
        mcp.start()
    except Exception as e:
        print(f"❌ MCP 启动失败：{e}")
        return
    
    # 验证
    results = []
    print("🔍 开始验证...\n")
    
    for i, code in enumerate(unique):
        pred = pred_dict.get(code, {})
        pred_change = pred.get('predicted_change', 0)
        pred_price = pred.get('predicted_price', 0)
        current = pred.get('current_price', 0)
        
        # 获取历史数据
        resp = mcp.get_hist(code)
        hist = parse_table(resp)
        
        if not hist or len(hist) < 2:
            print(f"[{i+1:2d}/50] {code} {pred.get('stock_name','-'):10s} ❌ 数据不足")
            continue
        
        # 计算实际（最后一日相对前一日）
        latest = hist[-1]
        prev = hist[-2]
        actual_change = ((latest.get('close',0) - prev.get('close',0)) / prev.get('close',1)) * 100
        
        # 对比
        direction_correct = (pred_change > 0) == (actual_change > 0)
        abs_error = abs(pred_change - actual_change)
        hit_2pct = abs_error < 2.0
        hit_1pct = abs_error < 1.0
        
        results.append({
            'stock_code': code,
            'stock_name': pred.get('stock_name', '-'),
            'predicted': round(pred_change, 2),
            'actual': round(actual_change, 2),
            'correct': direction_correct,
            'error': round(abs_error, 2),
            'hit_2pct': hit_2pct,
            'hit_1pct': hit_1pct,
        })
        
        status = "✅" if direction_correct else "❌"
        print(f"[{i+1:2d}/50] {code} {pred.get('stock_name','-'):10s} 预测{pred_change:+6.2f}% 实际{actual_change:+6.2f}% 误差{abs_error:5.2f}% {status}")
        
        time.sleep(0.3)
    
    mcp.close()
    
    # 汇总
    if results:
        df = pd.DataFrame(results)
        total = len(results)
        correct = len(df[df['correct']==True])
        acc = correct / total * 100
        mae = df['error'].mean()
        hit_2pct = df['hit_2pct'].mean() * 100
        hit_1pct = df['hit_1pct'].mean() * 100
        
        print("\n" + "="*80)
        print("📊 验证结果汇总")
        print("="*80)
        print(f"\n验证样本：{total} 只")
        print(f"方向正确：{correct}/{total} ({acc:.1f}%)")
        print(f"平均误差：{mae:.2f}%")
        print(f"命中率 (<2%)：{hit_2pct:.1f}%")
        print(f"命中率 (<1%)：{hit_1pct:.1f}%")
        
        # 按正确率
        print(f"\n✅ 正确 ({correct}只):")
        correct_df = df[df['correct']==True].sort_values('error')
        for _, row in correct_df.head(10).iterrows():
            print(f"   {row['stock_code']} {row['stock_name']}: 预测{row['predicted']:+.2f}% 实际{row['actual']:+.2f}% 误差{row['error']:.2f}%")
        
        print(f"\n❌ 错误 ({total-correct}只):")
        wrong_df = df[df['correct']==False].sort_values('error')
        for _, row in wrong_df.head(10).iterrows():
            print(f"   {row['stock_code']} {row['stock_name']}: 预测{row['predicted']:+.2f}% 实际{row['actual']:+.2f}% 误差{row['error']:.2f}%")
        
        # 保存
        output = f'/home/admin/openclaw/workspace/stock-recommendations/backtest/verify_50stocks_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
        with open(output, 'w') as f:
            json.dump({
                'timestamp': ts,
                'total': total,
                'correct': correct,
                'accuracy': round(acc, 1),
                'mae': round(mae, 2),
                'hit_2pct': round(hit_2pct, 1),
                'hit_1pct': round(hit_1pct, 1),
                'details': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 结果已保存：{output}")
        
        # 评估
        print("\n" + "="*80)
        print("🎯 模型评估")
        print("="*80)
        if acc >= 60:
            print(f"✅ 方向正确率 {acc:.1f}% - 表现良好（>60% 合格）")
        elif acc >= 50:
            print(f"⚠️  方向正确率 {acc:.1f}% - 勉强及格（50-60%）")
        else:
            print(f"❌ 方向正确率 {acc:.1f}% - 需要改进（<50%）")
        
        if mae <= 2:
            print(f"✅ 平均误差 {mae:.2f}% - 精度优秀（<2%）")
        elif mae <= 4:
            print(f"⚠️  平均误差 {mae:.2f}% - 可接受（2-4%）")
        else:
            print(f"❌ 平均误差 {mae:.2f}% - 误差偏大（>4%）")
        
        return acc, mae
    
    mcp.close()
    return None, None

if __name__ == '__main__':
    run_verify()
