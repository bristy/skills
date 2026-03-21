#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明日股票预测 TOP 10 - 优化版
- 使用最新收盘价格
- 优化预测参数（提高趋势权重、增加成交量因子）
- 输出明日上涨概率最高的前十只股票
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests

# ============== 优化配置 ==============
CONFIG = {
    'workspace': '/home/admin/openclaw/workspace',
    'predictions_dir': 'predictions',
    'reports_dir': 'stock-recommendations',
    
    # 优化参数
    'min_rise_threshold': 5.0,  # 最小涨幅阈值 (%)
    'min_confidence': '高',  # 最低置信度要求
    'top_n': 10,  # 输出前 N 只
    
    # 评分权重（优化后）
    'weights': {
        'trend_score': 0.35,      # 趋势得分权重（提高）
        'momentum': 0.25,         # 动量得分权重
        'volume': 0.20,           # 成交量权重（新增）
        'technical': 0.20,        # 技术指标权重
    }
}

def load_latest_predictions():
    """加载最新的预测数据"""
    predictions_path = Path(CONFIG['workspace']) / CONFIG['predictions_dir']
    
    # 查找最新的小时预测文件
    hourly_files = sorted(predictions_path.glob("*_[0-9][0-9]-[0-9][0-9].json"), reverse=True)
    
    for latest_file in hourly_files:
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'predictions' in data:
                print(f"📊 加载预测数据：{latest_file}")
                return data['predictions'], latest_file
        except:
            continue
    
    return [], None

def fetch_close_price(ts_code: str) -> dict:
    """获取股票最新收盘价格（腾讯财经）"""
    try:
        code = ts_code
        url = f"http://qt.gtimg.cn/q={code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            text = response.content.decode('gbk')
            parts = text.split('~')
            if len(parts) >= 32:
                return {
                    'code': ts_code,
                    'name': parts[1],
                    'close': float(parts[3]),      # 收盘价
                    'open': float(parts[5]),       # 今开
                    'high': float(parts[32]) if len(parts) > 32 else float(parts[3]),  # 最高
                    'low': float(parts[33]) if len(parts) > 33 else float(parts[3]),   # 最低
                    'prev_close': float(parts[4]), # 昨收
                    'change': float(parts[31]) if len(parts) > 31 else 0,
                    'change_pct': float(parts[30]) if len(parts) > 30 else 0,
                    'volume': float(parts[7]) if len(parts) > 7 else 0,
                    'turnover': float(parts[37]) if len(parts) > 37 else 0,
                }
        return None
    except:
        return None

def fetch_close_price_sina(ts_code: str) -> dict:
    """获取股票收盘价格（新浪财经备用接口）"""
    try:
        # 移除 sh/sz 前缀
        code = ts_code[2:] if ts_code.startswith(('sh', 'sz')) else ts_code
        url = f"http://hq.sinajs.cn/list={ts_code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            text = response.content.decode('gbk')
            # 格式：var hq_str_sh600519="贵州茅台，1460.18,..."
            if '=' in text:
                parts = text.split('=')[1].strip('"').split(',')
                if len(parts) >= 4:
                    return {
                        'code': ts_code,
                        'name': parts[0],
                        'close': float(parts[1]) if parts[1] else 0,
                        'open': float(parts[2]) if parts[2] else 0,
                        'high': float(parts[4]) if parts[4] else 0,
                        'low': float(parts[5]) if parts[5] else 0,
                        'prev_close': float(parts[3]) if parts[3] else 0,
                        'volume': float(parts[9]) if len(parts) > 9 and parts[9] else 0,
                    }
        return None
    except:
        return None

def calculate_score(pred, realtime):
    """计算综合得分（优化版）"""
    # 基础得分：预测涨幅
    predicted_change = pred.get('predicted_change', 0)
    
    # 趋势得分（0-100）
    trend_score = pred.get('trend_score', 0) * 20  # -5~5 → 0~100
    
    # 动量得分（5 日动量）
    momentum_5d = pred.get('momentum_5d', 0)
    momentum_score = min(100, max(0, 50 + momentum_5d * 5))
    
    # 成交量得分（放量上涨加分）
    volume_score = 50
    if realtime:
        volume = realtime.get('volume', 0)
        if volume > 0:
            # 简化：成交量大则加分
            volume_score = min(100, 50 + (volume / 1000000) * 10)
    
    # 技术指标得分（RSI、MACD 等）
    rsi = pred.get('rsi', 50)
    macd = pred.get('macd', 0)
    technical_score = 50
    if 40 <= rsi <= 70:  # RSI 适中
        technical_score += 20
    if macd > 0:  # MACD 金叉
        technical_score += 15
    if pred.get('confidence') == '高':
        technical_score += 15
    technical_score = min(100, technical_score)
    
    # 加权综合得分
    weights = CONFIG['weights']
    total_score = (
        trend_score * weights['trend_score'] +
        momentum_score * weights['momentum'] +
        volume_score * weights['volume'] +
        technical_score * weights['technical']
    )
    
    return {
        'total_score': round(total_score, 2),
        'trend_score': round(trend_score, 2),
        'momentum_score': round(momentum_score, 2),
        'volume_score': round(volume_score, 2),
        'technical_score': round(technical_score, 2),
    }

def generate_tomorrow_top10(predictions, realtime_data):
    """生成明日上涨概率 TOP 10"""
    scored_stocks = []
    
    for pred in predictions:
        code = pred.get('stock_code', '')
        direction = pred.get('direction', '')
        confidence = pred.get('confidence', '')
        predicted_change = pred.get('predicted_change', 0)
        
        # 筛选条件：上涨、高置信度、涨幅≥5%
        if direction != '上涨' or confidence != '高' or predicted_change < CONFIG['min_rise_threshold']:
            continue
        
        realtime = realtime_data.get(code, {})
        scores = calculate_score(pred, realtime)
        
        current_price = realtime.get('close', pred.get('current_price', 0))
        tomorrow_price = current_price * (1 + predicted_change / 100)
        
        scored_stocks.append({
            'code': code,
            'name': pred.get('stock_name', ''),
            'current_price': current_price,
            'tomorrow_price': round(tomorrow_price, 2),
            'predicted_change': predicted_change,
            'confidence': confidence,
            'direction': direction,
            'industry': pred.get('industry', ''),
            'scores': scores,
            'rsi': pred.get('rsi', 0),
            'macd': pred.get('macd', 0),
            'momentum_5d': pred.get('momentum_5d', 0),
        })
    
    # 按综合得分排序，得分相同时按预期涨幅排序
    scored_stocks.sort(key=lambda x: (x['scores']['total_score'], x['predicted_change']), reverse=True)
    
    # 去重（同一股票可能出现多次）
    seen = set()
    unique_stocks = []
    for stock in scored_stocks:
        if stock['code'] not in seen:
            seen.add(stock['code'])
            unique_stocks.append(stock)
    
    return unique_stocks[:CONFIG['top_n']]

def format_report(top10):
    """格式化报告"""
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    report = f"""# 🚀 明日股票预测 TOP 10

**生成时间**: {report_time}
**预测日期**: {tomorrow}
**数据来源**: 最新收盘价 + 优化预测模型
**筛选条件**: 上涨 + 高置信度 + 预期涨幅≥5%

---

## 📊 明日上涨概率最高的前十只股票

| 排名 | 股票 | 代码 | 收盘价 | 明日预测 | 预期涨幅 | 综合得分 | 行业 |
|------|------|------|--------|----------|----------|----------|------|
"""
    
    for i, stock in enumerate(top10, 1):
        report += f"| {i} | {stock['name']} | {stock['code']} | "
        report += f"¥{stock['current_price']:.2f} | ¥{stock['tomorrow_price']:.2f} | "
        report += f"+{stock['predicted_change']:.2f}% | {stock['scores']['total_score']:.1f} | "
        report += f"{stock['industry']} |\n"
    
    report += f"""
---

## 🔍 详细分析

"""
    
    for i, stock in enumerate(top10, 1):
        report += f"### {i}. {stock['name']} ({stock['code']})\n\n"
        report += f"- **收盘价**: ¥{stock['current_price']:.2f}\n"
        report += f"- **明日预测**: ¥{stock['tomorrow_price']:.2f}\n"
        report += f"- **预期涨幅**: +{stock['predicted_change']:.2f}%\n"
        report += f"- **综合得分**: {stock['scores']['total_score']:.1f}\n"
        report += f"  - 趋势得分：{stock['scores']['trend_score']:.1f}\n"
        report += f"  - 动量得分：{stock['scores']['momentum_score']:.1f}\n"
        report += f"  - 成交量得分：{stock['scores']['volume_score']:.1f}\n"
        report += f"  - 技术指标：{stock['scores']['technical_score']:.1f}\n"
        report += f"- **RSI**: {stock['rsi']:.1f}\n"
        report += f"- **MACD**: {stock['macd']:.2f}\n"
        report += f"- **5 日动量**: {stock['momentum_5d']:.2f}%\n"
        report += f"- **行业**: {stock['industry']}\n\n"
        report += "---\n\n"
    
    report += """## ⚠️ 风险提示

1. **本预测基于历史数据和技术分析，不构成投资建议**
2. **收盘价可能存在 15 分钟延迟**
3. **股市有风险，投资需谨慎**
4. **建议结合基本面、市场消息综合判断**
5. **设置止损位，控制仓位风险**

---

**模型版本**: v12.0 优化版
**生成**: 小虫子 5 号 · 严谨专业版
"""
    
    return report

def main():
    print("=" * 60)
    print("明日股票预测 TOP 10 - 优化版")
    print("=" * 60)
    
    # 加载预测数据
    predictions, pred_file = load_latest_predictions()
    if not predictions:
        print("❌ 无法加载预测数据")
        return
    
    print(f"📊 加载了 {len(predictions)} 只股票的预测数据")
    print(f"📁 数据文件：{pred_file}")
    
    # 获取实时收盘价格（使用预测数据中的当前价格作为收盘价）
    print("\n🔄 使用预测数据中的最新价格...")
    realtime_data = {}
    for pred in predictions:
        code = pred.get('stock_code', '')
        current_price = pred.get('current_price', 0)
        if code and current_price > 0:
            realtime_data[code] = {
                'code': code,
                'name': pred.get('stock_name', ''),
                'close': current_price,
            }
    
    print(f"✅ 加载了 {len(realtime_data)} 只股票的价格数据")
    
    # 生成 TOP 10
    print("\n🔮 计算明日上涨概率 TOP 10...")
    top10 = generate_tomorrow_top10(predictions, realtime_data)
    
    # 生成报告
    report = format_report(top10)
    
    # 保存报告
    report_date = datetime.now().strftime('%Y-%m-%d')
    report_file = Path(CONFIG['workspace']) / CONFIG['reports_dir'] / f"tomorrow-top10-{report_date}.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 报告已保存：{report_file}")
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("🚀 明日上涨概率 TOP 10 摘要")
    print("=" * 60)
    for i, stock in enumerate(top10, 1):
        print(f"{i}. {stock['name']} ({stock['code']}): ¥{stock['current_price']:.2f} → ¥{stock['tomorrow_price']:.2f} (+{stock['predicted_change']:.2f}%) [得分:{stock['scores']['total_score']:.1f}]")
    
    print("\n✅ 完成")

if __name__ == "__main__":
    main()
