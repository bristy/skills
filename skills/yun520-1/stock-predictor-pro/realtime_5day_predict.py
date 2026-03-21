#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票实时价格更新与 5 日预测
- 获取最新实时价格
- 计算 5 天后预测价格
- 生成详细报告
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests
import pandas as pd

# ============== 配置 ==============
CONFIG = {
    'workspace': '/home/admin/openclaw/workspace',
    'predictions_dir': 'predictions',
    'reports_dir': 'stock-recommendations',
    'top_n': 20,  # 显示前 N 只股票
}

def load_latest_predictions():
    """加载最新的预测数据"""
    predictions_path = Path(CONFIG['workspace']) / CONFIG['predictions_dir']
    
    # 查找最新的小时预测文件
    hourly_files = sorted(predictions_path.glob("*_[0-9][0-9]-[0-9][0-9].json"), reverse=True)
    
    if not hourly_files:
        print("❌ 未找到预测数据文件")
        return []
    
    for latest_file in hourly_files:
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'predictions' in data:
                print(f"📊 加载预测数据：{latest_file}")
                return data['predictions']
        except:
            continue
    
    return []

def fetch_realtime_price(ts_code: str) -> dict:
    """获取股票实时价格（腾讯财经）"""
    try:
        # 转换代码格式
        if ts_code.startswith('sh') or ts_code.startswith('sz'):
            code = ts_code
        else:
            # 判断市场
            if ts_code.startswith('6') or ts_code.startswith('9'):
                code = f"sh{ts_code}"
            else:
                code = f"sz{ts_code}"
        
        url = f"http://qt.gtimg.cn/q={code}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "http://stock.gtimg.cn/"
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            text = response.content.decode('gbk')
            # 解析：v_sh600519="51~贵州茅台~600519~1460.18~...
            parts = text.split('~')
            if len(parts) >= 32:
                return {
                    'code': ts_code,
                    'name': parts[1],
                    'current_price': float(parts[3]),
                    'open': float(parts[5]),
                    'high': float(parts[32]) if len(parts) > 32 else float(parts[3]),
                    'low': float(parts[33]) if len(parts) > 33 else float(parts[3]),
                    'prev_close': float(parts[4]),
                    'change': float(parts[31]) if len(parts) > 31 else 0,
                    'change_pct': float(parts[30]) if len(parts) > 30 else 0,
                    'volume': float(parts[7]) if len(parts) > 7 else 0,
                    'turnover': float(parts[37]) if len(parts) > 37 else 0,
                }
        return None
    except Exception as e:
        return None

def calculate_5day_prices(current_price: float, predicted_change_pct: float) -> list:
    """根据预测涨幅计算 5 天内每日价格（复利增长）"""
    # 假设均匀增长，计算每日复合增长率
    daily_rate = (1 + predicted_change_pct / 100) ** (1/5) - 1
    
    prices = []
    for day in range(1, 6):
        price = current_price * ((1 + daily_rate) ** day)
        prices.append({
            'day': day,
            'date': (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
            'price': round(price, 2)
        })
    return prices

def generate_report(predictions, realtime_data):
    """生成包含实时价格和 5 日预测的报告"""
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 合并实时价格和预测数据
    merged = []
    for pred in predictions:
        code = pred.get('stock_code', '')
        realtime = realtime_data.get(code, {})
        
        current_price = realtime.get('current_price', pred.get('current_price', 0))
        predicted_change = pred.get('predicted_change', 0)
        
        # 计算 5 天后价格
        predicted_price = current_price * (1 + predicted_change / 100)
        
        # 计算 5 天内每日价格
        day_prices = calculate_5day_prices(current_price, predicted_change)
        
        merged.append({
            'code': code,
            'name': pred.get('stock_name', ''),
            'current_price': current_price,
            'predicted_change': predicted_change,
            'predicted_price_5d': round(predicted_price, 2),
            'day_prices': day_prices,
            'confidence': pred.get('confidence', ''),
            'direction': pred.get('direction', ''),
            'industry': pred.get('industry', ''),
        })
    
    # 筛选上涨股票并按涨幅排序
    rising = [x for x in merged if x['direction'] == '上涨' and x['predicted_change'] >= 5]
    rising.sort(key=lambda x: x['predicted_change'], reverse=True)
    
    # 生成报告
    report = f"""# 📈 股票 5 日预测详细报告

**生成时间**: {report_time}
**数据来源**: 实时行情 + 技术预测
**筛选条件**: 未来 5 日预测上涨 ≥ 5%

---

## 🏆 TOP {min(CONFIG['top_n'], len(rising))} 推荐股票

"""
    
    for i, stock in enumerate(rising[:CONFIG['top_n']], 1):
        report += f"### {i}. {stock['name']} ({stock['code']})\n\n"
        report += f"- **当前价格**: ¥{stock['current_price']:.2f}\n"
        report += f"- **5 天后预测**: ¥{stock['predicted_price_5d']:.2f}\n"
        report += f"- **预期涨幅**: +{stock['predicted_change']:.2f}%\n"
        report += f"- **置信度**: {stock['confidence']}\n"
        report += f"- **行业**: {stock['industry']}\n\n"
        
        report += "**5 日内价格预测**:\n"
        report += "| 日期 | 第几天 | 预测价格 |\n"
        report += "|------|--------|----------|\n"
        for dp in stock['day_prices']:
            report += f"| {dp['date']} | D+{dp['day']} | ¥{dp['price']:.2f} |\n"
        report += "\n---\n\n"
    
    # 风险提示
    report += """## ⚠️ 风险提示

1. **本预测基于历史数据和技术分析，不构成投资建议**
2. **实时价格可能存在延迟（约 15 分钟）**
3. **股市有风险，投资需谨慎**
4. **建议结合基本面、市场消息和自身风险承受能力综合判断**
5. **设置止损位，控制仓位风险**

---

**报告生成**: 小虫子 5 号 · 严谨专业版
"""
    
    return report, rising[:CONFIG['top_n']]

def main():
    print("=" * 60)
    print("股票实时价格更新与 5 日预测")
    print("=" * 60)
    
    # 加载预测数据
    predictions = load_latest_predictions()
    if not predictions:
        print("❌ 无法加载预测数据")
        return
    
    print(f"📊 加载了 {len(predictions)} 只股票的预测数据")
    
    # 获取实时价格（批量获取前 50 只）
    print("🔄 获取实时价格...")
    realtime_data = {}
    for i, pred in enumerate(predictions[:50]):
        code = pred.get('stock_code', '')
        if code:
            data = fetch_realtime_price(code)
            if data:
                realtime_data[code] = data
                if i < 10:
                    print(f"  ✓ {data['name']}: ¥{data['current_price']:.2f} ({data['change_pct']:+.2f}%)")
    
    print(f"✅ 获取到 {len(realtime_data)} 只股票的实时价格")
    
    # 生成报告
    report, top_stocks = generate_report(predictions, realtime_data)
    
    # 保存报告
    report_time = datetime.now().strftime('%Y-%m-%d_%H-%M')
    report_file = Path(CONFIG['workspace']) / CONFIG['reports_dir'] / f"realtime-5day-{report_time}.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 报告已保存：{report_file}")
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("📊 TOP 5 推荐摘要")
    print("=" * 60)
    for i, stock in enumerate(top_stocks[:5], 1):
        print(f"{i}. {stock['name']} ({stock['code']}): ¥{stock['current_price']:.2f} → ¥{stock['predicted_price_5d']:.2f} (+{stock['predicted_change']:.2f}%)")
    
    print("\n✅ 完成")

if __name__ == "__main__":
    main()
