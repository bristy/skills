#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 china-stock-mcp 服务器
"""

import subprocess
import json
import time

# 启动 MCP 服务器
print("启动 china-stock-mcp 服务器...")
proc = subprocess.Popen(
    ['uvx', 'china-stock-mcp'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

time.sleep(3)

# 发送 MCP 初始化请求
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
}

print("发送初始化请求...")
proc.stdin.write(json.dumps(init_request) + '\n')
proc.stdin.flush()

# 读取响应
response = proc.stdout.readline()
print(f"初始化响应：{response[:200]}")

# 列出可用工具
tools_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}

print("\n查询可用工具...")
proc.stdin.write(json.dumps(tools_request) + '\n')
proc.stdin.flush()

response = proc.stdout.readline()
try:
    tools_data = json.loads(response)
    print(f"可用工具：{json.dumps(tools_data, indent=2, ensure_ascii=False)[:500]}")
except:
    print(f"响应：{response[:500]}")

# 关闭
proc.terminate()
print("\n测试完成")
