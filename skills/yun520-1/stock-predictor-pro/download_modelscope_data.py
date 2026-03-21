#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 ModelScope 下载 A 股历史数据
数据集：huskyhong/chinese-stock-dataset
"""

import json
import os
from datetime import datetime

def load_and_process_data():
    """加载并处理 ModelScope 数据"""
    
    # 检查 Git 仓库
    repo_path = '/home/admin/openclaw/workspace/chinese-stock-dataset'
    
    if not os.path.exists(repo_path):
        print('❌ 数据集仓库不存在')
        print('请先运行：git clone https://www.modelscope.cn/datasets/huskyhong/chinese-stock-dataset.git')
        return None
    
    # 检查数据文件
    data_file = os.path.join(repo_path, 'chinese-stock-dataset.csv')
    
    if not os.path.exists(data_file):
        print('⚠️  数据文件是 Git LFS 指针，需要下载实际数据')
        print('方法 1: 安装 git-lfs 后运行 git lfs pull')
        print('方法 2: 从 ModelScope 网站手动下载')
        
        # 读取指针文件查看实际大小
        with open(data_file, 'r') as f:
            content = f.read()
            if 'version https://git-lfs.github.com/spec/v1' in content:
                print(f'\n指针文件内容：{content[:200]}')
        return None
    
    # 加载 CSV
    import pandas as pd
    print(f'📊 加载数据：{data_file}')
    
    try:
        df = pd.read_csv(data_file)
        print(f'✅ 加载成功！')
        print(f'   记录数：{len(df)}')
        print(f'   字段：{list(df.columns)}')
        print(f'\n前 5 条数据:')
        print(df.head())
        
        # 保存为 JSON 格式供预测系统使用
        output_file = '/home/admin/openclaw/workspace/stock_system/modelscope_stocks.json'
        
        # 转换为股票列表
        stocks = []
        for _, row in df.iterrows():
            stock = {
                'code': row.get('stock_code', ''),
                'trade_date': row.get('date', ''),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'close': float(row.get('close', 0)),
                'volume': float(row.get('volume', 0)),
                'amount': float(row.get('amount', 0))
            }
            stocks.append(stock)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stocks, f, ensure_ascii=False, indent=2)
        
        print(f'\n📁 已保存：{output_file}')
        print(f'   股票数：{len(stocks)}')
        
        return df
    
    except Exception as e:
        print(f'❌ 加载失败：{e}')
        return None

if __name__ == '__main__':
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('='*80)
    print(f'ModelScope 数据下载工具')
    print(f'时间：{ts}')
    print('='*80)
    print()
    
    load_and_process_data()
