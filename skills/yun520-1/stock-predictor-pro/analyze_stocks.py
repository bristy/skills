#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
from datetime import datetime

def analyze_stocks(data):
    """分析股票数据并选出 Top 5 推荐"""
    
    # 评分标准
    scored_stocks = []
    
    for stock in data:
        score = 0
        reasons = []
        
        # 1. 涨跌幅评分 (0-30 分)
        change_pct = stock.get('change_pct', 0)
        if change_pct > 3:
            score += 30
            reasons.append(f"涨幅优秀 (+{change_pct}%)")
        elif change_pct > 1:
            score += 20
            reasons.append(f"表现良好 (+{change_pct}%)")
        elif change_pct > 0:
            score += 10
            reasons.append(f"小幅上涨 (+{change_pct}%)")
        elif change_pct > -2:
            score += 5
            reasons.append(f"小幅调整 ({change_pct}%)")
        else:
            reasons.append(f"跌幅较大 ({change_pct}%)")
        
        # 2. 市净率 PB 评分 (0-25 分) - PB 越低越好
        pb = stock.get('pb', 0)
        if pb > 0:
            if pb < 1:
                score += 25
                reasons.append(f"PB 极低 ({pb})")
            elif pb < 2:
                score += 20
                reasons.append(f"PB 较低 ({pb})")
            elif pb < 4:
                score += 15
                reasons.append(f"PB 合理 ({pb})")
            elif pb < 8:
                score += 8
                reasons.append(f"PB 偏高 ({pb})")
            else:
                reasons.append(f"PB 过高 ({pb})")
        
        # 3. 市值评分 (0-20 分) - 大市值更稳定
        market_cap = stock.get('market_cap', 0)
        if market_cap > 1000000000000:  # >1 万亿
            score += 20
            reasons.append("超大盘龙头")
        elif market_cap > 500000000000:  # >5000 亿
            score += 15
            reasons.append("大盘蓝筹")
        elif market_cap > 100000000000:  # >1000 亿
            score += 10
            reasons.append("中大盘股")
        else:
            score += 5
            reasons.append("中小盘股")
        
        # 4. 成交额评分 (0-15 分) - 流动性好
        turnover = stock.get('turnover', 0)
        if turnover > 10000000000:  # >100 亿
            score += 15
            reasons.append("成交活跃")
        elif turnover > 5000000000:  # >50 亿
            score += 12
            reasons.append("成交良好")
        elif turnover > 1000000000:  # >10 亿
            score += 8
            reasons.append("成交一般")
        else:
            score += 3
        
        # 5. 行业龙头加分 (0-10 分)
        name = stock.get('name', '')
        industry_bonus = {
            '贵州茅台': 10, '五粮液': 8, '宁德时代': 10, '比亚迪': 8,
            '中国平安': 8, '招商银行': 8, '工商银行': 6, '中国移动': 6,
            '美的集团': 6, '恒瑞医药': 6, '紫金矿业': 6, '长江电力': 6,
            '中信证券': 5, '东方财富': 5, '药明康德': 5, '迈瑞医疗': 5,
            '隆基绿能': 5, '阳光电源': 5, '中际旭创': 5, '立讯精密': 5,
        }
        if name in industry_bonus:
            score += industry_bonus[name]
            reasons.append("行业龙头")
        
        scored_stocks.append({
            **stock,
            'score': score,
            'reasons': reasons
        })
    
    # 按分数排序
    scored_stocks.sort(key=lambda x: x['score'], reverse=True)
    
    return scored_stocks[:5]

if __name__ == '__main__':
    # 读取股票数据
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    top5 = analyze_stocks(data)
    
    # 输出结果
    result = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_analyzed': len(data),
        'top5_recommendations': top5
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
