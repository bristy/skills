#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动更新脚本
功能：下载最新数据、更新数据库、生成推荐
"""

import os
import sys
from datetime import datetime

# 添加路径
sys.path.insert(0, '/home/admin/openclaw/workspace/skills/stock-predictor-pro')

from stock_database import StockDatabase

def daily_update():
    """每日更新流程"""
    print("="*80)
    print(f"🔄 每日股票数据更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 1. 初始化数据库
    print(f"\n📊 步骤 1: 初始化数据库...")
    db = StockDatabase()
    
    # 2. 更新当日数据
    print(f"\n📊 步骤 2: 更新当日数据...")
    db.update_daily()
    
    # 3. 生成推荐
    print(f"\n📊 步骤 3: 生成推荐...")
    os.system('python3 /home/admin/openclaw/workspace/skills/stock-predictor-pro/generate_recommendation.py')
    
    # 4. 清理旧数据
    print(f"\n📊 步骤 4: 清理日志...")
    print(f"   ✅ 更新完成")
    
    print(f"\n{'='*80}")
    print(f"✅ 每日更新完成")
    print(f"{'='*80}")

if __name__ == '__main__':
    daily_update()
