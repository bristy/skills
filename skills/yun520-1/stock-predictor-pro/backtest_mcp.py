#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票预测回测系统 v7.0 - 使用 china-stock-mcp
真正的历史验证：用历史预测 vs MCP 提供的实际走势
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
    """简单的 MCP 客户端"""
    
    def __init__(self):
        self.proc = None
        self.request_id = 0
    
    def start(self):
        """启动 MCP 服务器"""
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
        
        # 初始化
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "backtest-client", "version": "1.0.0"}
            }
        }
        self._send(init_request)
        response = self._receive()
        print(f"MCP 服务器已初始化")
        return response
    
    def _send(self, request):
        """发送请求"""
        self.request_id += 1
        request['id'] = self.request_id
        self.proc.stdin.write(json.dumps(request) + '\n')
        self.proc.stdin.flush()
    
    def _receive(self):
        """接收响应"""
        line = self.proc.stdout.readline()
        try:
            return json.loads(line)
        except:
            return {"error": line}
    
    def get_stock_history(self, symbol, interval='day'):
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
        """关闭服务器"""
        if self.proc:
            self.proc.terminate()

def load_predictions(pred_file):
    """加载预测文件"""
    with open(pred_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    predictions = []
    if isinstance(data, list):
        # 每小时预测文件：[{"timestamp":..., "predictions": [...]}]
        for entry in data:
            if isinstance(entry, dict) and 'predictions' in entry:
                for pred in entry['predictions']:
                    if isinstance(pred, dict) and 'stock_code' in pred:
                        pred['predict_hour'] = entry.get('hour', '-')
                        predictions.append(pred)
    elif isinstance(data, dict):
        # 每日预测文件或单小时文件
        if 'predictions' in data:
            entry = data['predictions']
            if isinstance(entry, list):
                for pred in entry:
                    if isinstance(pred, dict) and 'stock_code' in pred:
                        predictions.append(pred)
            elif isinstance(entry, dict) and 'predictions' in entry:
                for pred in entry['predictions']:
                    if isinstance(pred, dict) and 'stock_code' in pred:
                        predictions.append(pred)
    
    return predictions

def parse_mcp_history(mcp_response):
    """解析 MCP 返回的历史数据（Markdown 表格）"""
    try:
        if 'result' in mcp_response and 'content' in mcp_response['result']:
            content = mcp_response['result']['content']
            if isinstance(content, list) and len(content) > 0:
                data_str = content[0].get('text', '')
                if data_str:
                    # 解析 Markdown 表格
                    lines = data_str.strip().split('\n')
                    if len(lines) < 3:
                        return None
                    
                    # 获取表头
                    headers = [h.strip() for h in lines[0].split('|')[1:-1]]
                    
                    # 解析数据行
                    data = []
                    for line in lines[2:]:  # 跳过分隔线
                        if not line.strip():
                            continue
                        values = [v.strip() for v in line.split('|')[1:-1]]
                        if len(values) == len(headers):
                            row = {}
                            for h, v in zip(headers, values):
                                # 尝试转换为数字
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
        print(f"解析错误：{e}")
    return None

def run_backtest_with_mcp():
    """使用 MCP 进行回测"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("="*80)
    print(f"股票预测回测系统 v7.0 (MCP)")
    print(f"时间：{timestamp}")
    print("="*80)
    
    # 启动 MCP
    mcp = MCPClient()
    try:
        mcp.start()
    except Exception as e:
        print(f"❌ MCP 启动失败：{e}")
        return
    
    # 加载历史预测
    pred_dir = '/home/admin/openclaw/workspace/predictions'
    
    # 找昨天的预测
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    pred_file = f"{pred_dir}/{yesterday}.json"
    
    if not os.path.exists(pred_file):
        files = sorted(Path(pred_dir).glob('*.json'))
        if files:
            pred_file = str(files[0])
        else:
            print("❌ 无预测文件")
            mcp.close()
            return
    
    print(f"\n📁 预测文件：{pred_file}")
    predictions = load_predictions(pred_file)
    print(f"   加载预测：{len(predictions)} 条")
    
    if not predictions:
        mcp.close()
        return
    
    # 采样测试（先用 5 只股票测试）
    unique_stocks = list(set(p['stock_code'] for p in predictions if 'stock_code' in p))[:5]
    print(f"\n🔍 测试股票：{len(unique_stocks)} 只")
    print(f"   {', '.join(unique_stocks)}")
    
    # 获取历史数据
    results = []
    print("\n📊 获取历史数据...")
    
    for i, code in enumerate(unique_stocks):
        print(f"   [{i+1}/{len(unique_stocks)}] {code}...")
        
        response = mcp.get_stock_history(code)
        data = parse_mcp_history(response)
        
        if data:
            print(f"      ✅ 成功获取 {len(data) if isinstance(data, list) else 'N/A'} 条记录")
            # 这里需要进一步处理数据，对比预测和实际
            results.append({
                'stock_code': code,
                'has_data': True,
                'data_length': len(data) if isinstance(data, list) else 0
            })
        else:
            print(f"      ❌ 获取失败")
            results.append({
                'stock_code': code,
                'has_data': False
            })
        
        time.sleep(0.5)
    
    # 汇总
    print("\n" + "="*80)
    print("📊 回测结果")
    print("="*80)
    success = len([r for r in results if r['has_data']])
    print(f"成功获取：{success}/{len(results)} 只股票")
    
    for r in results:
        if r['has_data']:
            print(f"   ✅ {r['stock_code']}: {r['data_length']} 条记录")
        else:
            print(f"   ❌ {r['stock_code']}: 无数据")
    
    mcp.close()
    print("\n✅ 测试完成")
    
    return results

if __name__ == '__main__':
    run_backtest_with_mcp()
