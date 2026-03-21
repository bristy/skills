#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据获取脚本 - 使用 akshare 获取真实行情数据
"""

import akshare as ak
import pandas as pd
import json
from datetime import datetime

# 重点监控股票
FOCUS_STOCKS = [
    {"code": "600519", "name": "贵州茅台", "industry": "白酒"},
    {"code": "000858", "name": "五粮液", "industry": "白酒"},
    {"code": "601318", "name": "中国平安", "industry": "保险"},
    {"code": "600036", "name": "招商银行", "industry": "银行"},
    {"code": "300750", "name": "宁德时代", "industry": "电池"},
    {"code": "000333", "name": "美的集团", "industry": "家电"},
    {"code": "600276", "name": "恒瑞医药", "industry": "医药"},
    {"code": "002415", "name": "海康威视", "industry": "安防"},
    {"code": "601888", "name": "中国中免", "industry": "免税"},
    {"code": "600030", "name": "中信证券", "industry": "券商"},
    {"code": "002594", "name": "比亚迪", "industry": "汽车"},
    {"code": "002230", "name": "科大讯飞", "industry": "AI"},
    {"code": "300274", "name": "阳光电源", "industry": "光伏"},
    {"code": "300308", "name": "中际旭创", "industry": "光模块"},
    {"code": "601088", "name": "中国神华", "industry": "煤炭"},
    {"code": "600900", "name": "长江电力", "industry": "电力"},
    {"code": "601899", "name": "紫金矿业", "industry": "矿业"},
    {"code": "600028", "name": "中国石化", "industry": "石油"},
    {"code": "601857", "name": "中国石油", "industry": "石油"},
    {"code": "000651", "name": "格力电器", "industry": "家电"},
    {"code": "300760", "name": "迈瑞医疗", "industry": "医疗器械"},
    {"code": "300059", "name": "东方财富", "industry": "券商"},
    {"code": "600570", "name": "恒生电子", "industry": "金融科技"},
    {"code": "002475", "name": "立讯精密", "industry": "消费电子"},
    {"code": "600809", "name": "山西汾酒", "industry": "白酒"},
]

def get_stock_data():
    """获取股票实时行情数据"""
    all_data = []
    
    print("开始获取股票行情数据...")
    
    for stock in FOCUS_STOCKS:
        try:
            # 使用 akshare 获取实时行情
            code = stock["code"]
            if code.startswith("6"):
                symbol = f"sh{code}"
            else:
                symbol = f"sz{code}"
            
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == code]
            
            if not stock_data.empty:
                row = stock_data.iloc[0]
                data = {
                    "ts_code": code,
                    "name": row.get('名称', stock["name"]),
                    "industry": stock["industry"],
                    "close": float(row.get('最新价', 0)),
                    "pct_chg": float(row.get('涨跌幅', 0)),
                    "pe": float(row.get('市盈率 - 动态', 0)) if row.get('市盈率 - 动态') else 0,
                    "pb": float(row.get('市净率', 0)) if row.get('市净率') else 0,
                    "vol": int(row.get('成交量', 0)) if row.get('成交量') else 0,
                    "amount": float(row.get('成交额', 0)) if row.get('成交额') else 0,
                    "total_mv": float(row.get('总市值', 0)) if row.get('总市值') else 0,
                    "trade_date": datetime.now().strftime("%Y%m%d")
                }
                all_data.append(data)
                print(f"✓ {code} {data['name']}: ¥{data['close']} ({data['pct_chg']}%)")
            else:
                print(f"✗ {code} 未找到数据")
                
        except Exception as e:
            print(f"✗ {code} 获取失败：{str(e)}")
    
    return all_data

def calculate_score(stock):
    """计算综合评分"""
    score = 0
    
    # 涨跌幅评分（0-30 分）
    change_score = min(30, max(0, stock["pct_chg"] * 5 + 15))
    score += change_score
    
    # PE 评分（越低越好，0-25 分）
    pe = stock["pe"]
    if pe <= 0:
        pe_score = 10  # 无 PE 数据给中等分
    elif pe < 15:
        pe_score = 25
    elif pe < 25:
        pe_score = 18
    elif pe < 35:
        pe_score = 10
    else:
        pe_score = 5
    score += pe_score
    
    # PB 评分（越低越好，0-20 分）
    pb = stock["pb"]
    if pb <= 0:
        pb_score = 10
    elif pb < 2:
        pb_score = 20
    elif pb < 4:
        pb_score = 14
    elif pb < 6:
        pb_score = 8
    else:
        pb_score = 4
    score += pb_score
    
    # 成交量评分（0-15 分）
    vol = stock["vol"]
    if vol > 5000000:
        vol_score = 15
    elif vol > 2000000:
        vol_score = 10
    else:
        vol_score = 5
    score += vol_score
    
    # 市值评分（0-10 分）
    mv = stock["total_mv"]
    if 1000 < mv < 3000:
        mv_score = 10
    else:
        mv_score = 6
    score += mv_score
    
    stock["total_score"] = round(score, 2)
    return stock

def generate_reason(stock):
    """生成推荐理由"""
    reasons = []
    
    if stock["pct_chg"] > 3:
        reasons.append(f"今日涨幅{stock['pct_chg']}%，表现强势")
    elif stock["pct_chg"] > 0:
        reasons.append(f"今日上涨{stock['pct_chg']}%，走势稳健")
    elif stock["pct_chg"] > -2:
        reasons.append(f"今日微跌{stock['pct_chg']}%，相对抗跌")
    
    pe = stock["pe"]
    if pe > 0:
        if pe < 15:
            reasons.append(f"PE 仅{pe}，估值较低")
        elif pe < 25:
            reasons.append(f"PE{pe}，估值合理")
    
    pb = stock["pb"]
    if pb > 0 and pb < 3:
        reasons.append(f"PB{pb}，资产价格有吸引力")
    
    if stock["vol"] > 5000000:
        reasons.append("成交活跃，资金关注度高")
    
    if stock["industry"] in ["AI", "光模块", "电池", "光伏", "金融科技"]:
        reasons.append(f"所属{stock['industry']}为热门赛道")
    
    return "；".join(reasons) if reasons else "综合指标良好"

def main():
    # 获取数据
    stock_data = get_stock_data()
    
    if not stock_data:
        print("未能获取到股票数据，使用模拟数据...")
        # 使用 Node.js 脚本的模拟数据
        import subprocess
        result = subprocess.run(
            ["node", "/home/admin/openclaw/workspace/stock_system/analyze_stocks.js"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return
    
    print(f"\n成功获取 {len(stock_data)} 只股票数据")
    
    # 计算评分
    scored_stocks = [calculate_score(s) for s in stock_data]
    
    # 排序
    scored_stocks.sort(key=lambda x: x["total_score"], reverse=True)
    
    # 获取 Top 5
    top5 = scored_stocks[:5]
    
    # 生成推荐结果
    recommendations = []
    for i, stock in enumerate(top5):
        rec = {
            "rank": i + 1,
            "code": stock["ts_code"],
            "name": stock["name"],
            "industry": stock["industry"],
            "price": stock["close"],
            "change": stock["pct_chg"],
            "pe": stock["pe"],
            "pb": stock["pb"],
            "volume": stock["vol"],
            "total_score": stock["total_score"],
            "reason": generate_reason(stock)
        }
        recommendations.append(rec)
    
    # 保存结果
    import os
    output_dir = "/home/admin/openclaw/workspace/stock-recommendations"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    output_file = os.path.join(output_dir, f"recommendation-{timestamp}.json")
    
    result = {
        "generated_at": datetime.now().isoformat(),
        "market_date": datetime.now().strftime("%Y-%m-%d"),
        "total_analyzed": len(stock_data),
        "top_recommendations": recommendations
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n推荐结果已保存到：{output_file}")
    
    # 输出 Top 5
    print("\n" + "="*50)
    print("📈 Top 5 推荐股票")
    print("="*50)
    
    for rec in recommendations:
        print(f"\n{rec['rank']}. {rec['name']}({rec['code']}) - {rec['industry']}")
        print(f"   价格：¥{rec['price']} | 涨跌：{rec['change']}% | PE: {rec['pe']} | PB: {rec['pb']}")
        print(f"   评分：{rec['total_score']}")
        print(f"   💡 {rec['reason']}")
    
    # 生成消息文本
    message_lines = [f"📈 股票推荐 Top 5 ({datetime.now().strftime('%Y/%m/%d %H:%M')})\n"]
    
    for rec in recommendations:
        change_sign = "+" if rec["change"] > 0 else ""
        message_lines.append(f"{rec['rank']}. *{rec['name']}* ({rec['code']})")
        message_lines.append(f"   行业：{rec['industry']} | 价格：¥{rec['price']}")
        message_lines.append(f"   涨跌：{change_sign}{rec['change']}% | PE: {rec['pe']} | PB: {rec['pb']}")
        message_lines.append(f"   💡 {rec['reason']}")
        message_lines.append("")
    
    message_lines.append("⚠️ 以上仅供参考，不构成投资建议。")
    
    message_text = "\n".join(message_lines)
    
    # 保存消息
    with open(os.path.join(output_dir, "latest-message.txt"), "w", encoding="utf-8") as f:
        f.write(message_text)
    
    print("\n" + "="*50)
    print("📩 消息格式")
    print("="*50)
    print(message_text)
    
    # 输出 JSON 供后续使用
    print("\n" + "="*50)
    print("📄 JSON 输出")
    print("="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
