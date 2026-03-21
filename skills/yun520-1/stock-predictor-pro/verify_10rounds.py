#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测 10 轮回测验证系统 v8.0
目标：对比预测 vs 实际，反复验证 10 次，计算准确率，找到最优参数
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import time
import os
from pathlib import Path

class MCPClient:
    """MCP 客户端"""
    
    def __init__(self):
        self.proc = None
        self.request_id = 0
    
    def start(self):
        print("启动 china-stock-mcp 服务器...")
        self.proc = subprocess.Popen(
            ['uvx', 'china-stock-mcp'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        time.sleep(3)
        
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "verify-client", "version": "1.0.0"}
            }
        }
        self._send(init_request)
        response = self._receive()
        print("✅ MCP 服务器已初始化")
        return response
    
    def _send(self, request):
        self.request_id += 1
        request['id'] = self.request_id
        self.proc.stdin.write(json.dumps(request) + '\n')
        self.proc.stdin.flush()
    
    def _receive(self):
        line = self.proc.stdout.readline()
        try:
            return json.loads(line)
        except:
            return {"error": line}
    
    def get_hist_data(self, symbol, interval='day'):
        """获取股票历史数据"""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_hist_data",
                "arguments": {
                    "symbol": symbol,
                    "interval": interval
                }
            }
        }
        self._send(request)
        return self._receive()
    
    def close(self):
        if self.proc:
            self.proc.terminate()

def parse_mcp_table(mcp_response):
    """解析 MCP 返回的 Markdown 表格"""
    try:
        if 'result' in mcp_response and 'content' in mcp_response['result']:
            content = mcp_response['result']['content']
            if isinstance(content, list) and len(content) > 0:
                data_str = content[0].get('text', '')
                if data_str:
                    lines = data_str.strip().split('\n')
                    if len(lines) < 3:
                        return None
                    
                    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
                    data = []
                    for line in lines[2:]:
                        if not line.strip():
                            continue
                        values = [v.strip() for v in line.split('|')[1:-1]]
                        if len(values) == len(headers):
                            row = {}
                            for h, v in zip(headers, values):
                                try:
                                    if '.' in v:
                                        row[h] = float(v)
                                    else:
                                        row[h] = int(v)
                                except:
                                    row[h] = v
                            data.append(row)
                    return data if data else None
    except Exception as e:
        pass
    return None

def load_predictions(pred_file):
    """加载预测文件"""
    with open(pred_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = []
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and 'predictions' in entry:
                for pred in entry['predictions']:
                    if isinstance(pred, dict) and 'stock_code' in pred:
                        pred['predict_hour'] = entry.get('hour', '-')
                        predictions.append(pred)
    return predictions

def verify_single_round(mcp, pred_file, sample_size=20):
    """单轮验证"""
    predictions = load_predictions(pred_file)
    if not predictions:
        return None
    
    # 随机采样
    unique_stocks = list(set(p['stock_code'] for p in predictions if 'stock_code' in p))
    if len(unique_stocks) < sample_size:
        sample_stocks = unique_stocks
    else:
        np.random.seed(int(datetime.now().timestamp()) % 1000)
        sample_stocks = np.random.choice(unique_stocks, sample_size, replace=False).tolist()
    
    results = []
    
    for code in sample_stocks:
        # 获取预测
        preds = [p for p in predictions if p.get('stock_code') == code]
        if not preds:
            continue
        
        # 取最新预测
        latest_pred = preds[-1]
        predicted_change = latest_pred.get('predicted_change', 0)
        
        # 获取实际数据（用 MCP）
        response = mcp.get_hist_data(code, 'day')
        hist_data = parse_mcp_table(response)
        
        if not hist_data or len(hist_data) < 2:
            continue
        
        # 计算实际涨跌幅（最新一日相对前一日）
        latest = hist_data[-1]
        prev = hist_data[-2]
        
        actual_change = ((latest.get('close', 0) - prev.get('close', 0)) / prev.get('close', 1)) * 100
        
        # 对比
        direction_correct = (predicted_change > 0) == (actual_change > 0)
        abs_error = abs(predicted_change - actual_change)
        
        results.append({
            'stock_code': code,
            'stock_name': latest_pred.get('stock_name', '-'),
            'predicted_change': round(predicted_change, 2),
            'actual_change': round(actual_change, 2),
            'direction_correct': direction_correct,
            'abs_error': round(abs_error, 2),
            'hit_2pct': abs_error < 2.0,
            'hit_1pct': abs_error < 1.0,
        })
        
        time.sleep(0.3)
    
    return results

def run_10_rounds():
    """运行 10 轮验证"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测 10 轮回测验证系统 v8.0")
    print(f"时间：{timestamp}")
    print("="*80)
    
    # 启动 MCP
    mcp = MCPClient()
    try:
        mcp.start()
    except Exception as e:
        print(f"❌ MCP 启动失败：{e}")
        return
    
    # 预测文件
    pred_dir = '/home/admin/openclaw/workspace/predictions'
    pred_file = f"{pred_dir}/2026-03-17.json"
    
    if not os.path.exists(pred_file):
        files = sorted(Path(pred_dir).glob('*.json'))
        if files:
            pred_file = str(files[0])
        else:
            print("❌ 无预测文件")
            mcp.close()
            return
    
    print(f"\n📁 预测文件：{pred_file}")
    
    # 10 轮验证
    all_round_results = []
    
    for round_num in range(1, 11):
        print(f"\n{'='*80}")
        print(f"🔍 第 {round_num}/10 轮验证")
        print(f"{'='*80}")
        
        # 每轮使用不同的随机种子
        np.random.seed(round_num * 1000)
        
        results = verify_single_round(mcp, pred_file, sample_size=10)
        
        if results:
            df_r = pd.DataFrame(results)
            
            total = len(results)
            direction_acc = df_r['direction_correct'].mean() * 100
            mae = df_r['abs_error'].mean()
            hit_2pct = df_r['hit_2pct'].mean() * 100
            
            print(f"\n✅ 验证样本：{total} 个")
            print(f"📈 方向正确率：{direction_acc:.1f}%")
            print(f"📉 平均误差：{mae:.2f}%")
            print(f"🎯 命中率 (<2%)：{hit_2pct:.1f}%")
            
            all_round_results.append({
                'round': round_num,
                'total': total,
                'direction_accuracy': round(direction_acc, 1),
                'mae': round(mae, 2),
                'hit_2pct': round(hit_2pct, 1),
                'details': results
            })
        else:
            print(f"❌ 第{round_num}轮验证失败")
            all_round_results.append({
                'round': round_num,
                'total': 0,
                'direction_accuracy': 0,
                'mae': 0,
                'hit_2pct': 0,
                'details': []
            })
        
        time.sleep(1)
    
    # 汇总统计
    print("\n" + "="*80)
    print("📊 10 轮验证汇总")
    print("="*80)
    
    valid_rounds = [r for r in all_round_results if r['total'] > 0]
    
    if not valid_rounds:
        print("❌ 无有效验证结果")
        mcp.close()
        return
    
    avg_direction_acc = np.mean([r['direction_accuracy'] for r in valid_rounds])
    avg_mae = np.mean([r['mae'] for r in valid_rounds])
    avg_hit_2pct = np.mean([r['hit_2pct'] for r in valid_rounds])
    total_samples = sum([r['total'] for r in valid_rounds])
    
    print(f"\n📈 平均方向正确率：{avg_direction_acc:.1f}%")
    print(f"📉 平均误差：{avg_mae:.2f}%")
    print(f"🎯 平均命中率 (<2%)：{avg_hit_2pct:.1f}%")
    print(f"📝 总验证样本：{total_samples} 个")
    print()
    
    # 每轮详情
    print("📋 每轮详情:")
    print(f"{'轮次':<6} {'样本数':<8} {'方向正确率':<12} {'平均误差':<10} {'命中率 (<2%)':<12}")
    print("-"*60)
    for r in all_round_results:
        print(f"{r['round']:<6} {r['total']:<8} {r['direction_accuracy']:<12.1f}% {r['mae']:<10.2f}% {r['hit_2pct']:<12.1f}%")
    
    # 保存结果
    output_dir = '/home/admin/openclaw/workspace/stock-recommendations/backtest'
    os.makedirs(output_dir, exist_ok=True)
    
    result_file = f"{output_dir}/verify_10rounds_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'pred_file': pred_file,
            'rounds': all_round_results,
            'summary': {
                'total_rounds': len(valid_rounds),
                'total_samples': total_samples,
                'avg_direction_accuracy': round(avg_direction_acc, 1),
                'avg_mae': round(avg_mae, 2),
                'avg_hit_2pct': round(avg_hit_2pct, 1)
            }
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📁 结果已保存：{result_file}")
    
    # 评估
    print("\n" + "="*80)
    print("🎯 模型评估")
    print("="*80)
    
    if avg_direction_acc >= 60:
        print(f"✅ 方向正确率 {avg_direction_acc:.1f}% - 模型表现良好（>60% 为合格）")
    elif avg_direction_acc >= 50:
        print(f"⚠️  方向正确率 {avg_direction_acc:.1f}% - 勉强及格（50-60%）")
    else:
        print(f"❌ 方向正确率 {avg_direction_acc:.1f}% - 需要改进（<50%）")
    
    if avg_mae <= 2.0:
        print(f"✅ 平均误差 {avg_mae:.2f}% - 预测精度优秀（<2%）")
    elif avg_mae <= 3.0:
        print(f"⚠️  平均误差 {avg_mae:.2f}% - 预测精度可接受（2-3%）")
    else:
        print(f"❌ 平均误差 {avg_mae:.2f}% - 误差偏大（>3%）")
    
    mcp.close()
    print("\n" + "="*80)
    print("✅ 10 轮验证完成")
    print("="*80)
    
    return avg_direction_acc, avg_mae, avg_hit_2pct

if __name__ == '__main__':
    run_10_rounds()
