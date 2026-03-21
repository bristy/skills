#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日股票推荐系统
- 筛选条件：未来 5 日预测上涨 > 5%
- 生成推荐报告并发送给用户
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# ============== 配置 ==============
CONFIG = {
    'min_rise_threshold': 5.0,  # 最小涨幅阈值 (%)
    'prediction_days': 5,  # 预测天数
    'max_recommendations': 10,  # 最大推荐数量
    'workspace': '/home/admin/openclaw/workspace',
    'predictions_dir': 'predictions',
    'recommendations_dir': 'stock-recommendations',
}

def load_latest_predictions():
    """加载最新的预测数据"""
    predictions_path = Path(CONFIG['workspace']) / CONFIG['predictions_dir']
    
    # 查找所有小时预测文件（优先）和每日预测文件
    hourly_files = sorted(predictions_path.glob("*_[0-9][0-9]-[0-9][0-9].json"), reverse=True)
    daily_files = sorted(predictions_path.glob("*.json"), reverse=True)
    
    # 优先使用小时预测文件（更新）
    prediction_files = hourly_files if hourly_files else daily_files
    
    if not prediction_files:
        print("❌ 未找到预测数据文件")
        return []
    
    # 找到第一个包含 predictions 的文件
    for latest_file in prediction_files:
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'predictions' in data:
                print(f"📊 加载预测数据：{latest_file}")
                return data['predictions']
            elif isinstance(data, list):
                print(f"📊 加载预测数据：{latest_file}")
                return data
        except:
            continue
    
    print("❌ 无法解析预测数据文件")
    return []

def filter_high_confidence_rising(predictions):
    """筛选高置信度上涨股票（未来 5 日涨幅 > 5%）"""
    qualified = []
    
    for pred in predictions:
        # 获取预测涨幅 (字段名：predicted_change)
        rise_pct = pred.get('predicted_change', 0)
        confidence = pred.get('confidence', '')
        direction = pred.get('direction', '')
        
        # 筛选条件：上涨且涨幅 > 5% 且高置信度
        if (direction == '上涨' and 
            rise_pct >= CONFIG['min_rise_threshold'] and 
            confidence in ['高', '中']):
            
            qualified.append({
                'code': pred.get('stock_code', ''),
                'name': pred.get('stock_name', ''),
                'current_price': pred.get('current_price', 0),
                'predicted_price': pred.get('predicted_price', 0),
                'rise_pct': rise_pct,
                'confidence': confidence,
                'direction': direction
            })
    
    # 按涨幅排序
    qualified.sort(key=lambda x: x['rise_pct'], reverse=True)
    
    return qualified[:CONFIG['max_recommendations']]

def generate_report(qualified_stocks):
    """生成推荐报告"""
    today = datetime.now()
    report_date = today.strftime('%Y-%m-%d')
    report_time = today.strftime('%H:%M')
    
    report = f"""# 📈 每日股票推荐报告

**生成时间**: {report_date} {report_time}
**筛选条件**: 未来 5 日预测上涨 ≥ {CONFIG['min_rise_threshold']}%
**置信度要求**: 高/中

---

## 🏆 推荐股票列表

"""
    
    if not qualified_stocks:
        report += "⚠️ 今日暂无符合筛选条件的股票推荐。\n\n"
        report += "可能原因：\n"
        report += "- 市场整体表现平淡\n"
        report += "- 高置信度上涨股票较少\n"
        report += "- 建议关注明日推荐\n"
    else:
        report += f"**共推荐 {len(qualified_stocks)} 只股票**\n\n"
        report += "| 序号 | 股票 | 代码 | 当前价 | 预测价 | 预期涨幅 | 置信度 |\n"
        report += "|------|------|------|--------|--------|----------|--------|\n"
        
        for i, stock in enumerate(qualified_stocks, 1):
            report += f"| {i} | {stock['name']} | {stock['code']} | "
            report += f"{stock['current_price']:.2f} | {stock['predicted_price']:.2f} | "
            report += f"+{stock['rise_pct']:.2f}% | {stock['confidence']} |\n"
        
        report += "\n---\n\n"
        report += "## 📊 推荐摘要\n\n"
        
        # 统计信息
        avg_rise = sum(s['rise_pct'] for s in qualified_stocks) / len(qualified_stocks)
        high_conf_count = sum(1 for s in qualified_stocks if s['confidence'] == '高')
        
        report += f"- **平均预期涨幅**: +{avg_rise:.2f}%\n"
        report += f"- **高置信度股票**: {high_conf_count} 只\n"
        report += f"- **最高预期涨幅**: +{qualified_stocks[0]['rise_pct']:.2f}% ({qualified_stocks[0]['name']})\n"
        
        report += "\n---\n\n"
        report += "## ⚠️ 风险提示\n\n"
        report += "1. 本推荐基于历史数据和技术分析，不构成投资建议\n"
        report += "2. 股市有风险，投资需谨慎\n"
        report += "3. 建议结合基本面和市场消息综合判断\n"
        report += "4. 设置止损位，控制仓位风险\n"
    
    return report

def send_to_user(report, qualified_stocks):
    """发送推荐信息给用户"""
    # 生成简要消息
    if not qualified_stocks:
        brief_msg = "📈 **今日股票推荐**\n\n暂无符合筛选条件（5 日涨幅≥5%）的股票推荐。\n\n建议关注明日推荐。"
    else:
        brief_msg = "📈 **今日股票推荐** (未来 5 日预期上涨≥5%)\n\n"
        brief_msg += f"**共推荐 {len(qualified_stocks)} 只股票**\n\n"
        brief_msg += "**TOP 5 推荐**:\n"
        
        for i, stock in enumerate(qualified_stocks[:5], 1):
            brief_msg += f"{i}. 🟢 {stock['name']} ({stock['code']}): "
            brief_msg += f"预期涨幅 +{stock['rise_pct']:.2f}% [{stock['confidence']}置信度]\n"
        
        brief_msg += "\n完整报告已保存至 `stock-recommendations/` 目录"
    
    print(f"\n📬 推荐摘要:\n{brief_msg}")
    
    # 返回简要消息供 cron 任务使用
    return brief_msg

def main():
    print("=" * 60)
    print("每日股票推荐系统")
    print("=" * 60)
    
    # 加载预测数据
    predictions = load_latest_predictions()
    if not predictions:
        print("❌ 无法加载预测数据，请先运行 stock_predict_hourly.py")
        return
    
    print(f"📊 加载了 {len(predictions)} 只股票的预测数据")
    
    # 筛选符合条件的股票
    qualified = filter_high_confidence_rising(predictions)
    print(f"✅ 筛选出 {len(qualified)} 只符合条件的股票")
    
    # 生成报告
    report = generate_report(qualified)
    
    # 保存报告
    today = datetime.now().strftime('%Y-%m-%d')
    report_file = Path(CONFIG['workspace']) / CONFIG['recommendations_dir'] / f"daily-recommend-{today}.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 报告已保存：{report_file}")
    
    # 发送给用户
    brief_msg = send_to_user(report, qualified)
    
    print("\n" + "=" * 60)
    print("✅ 推荐完成")
    print("=" * 60)
    
    # 输出简要消息供 cron 使用
    print(f"\n[MESSAGE]\n{brief_msg}")

if __name__ == "__main__":
    main()
