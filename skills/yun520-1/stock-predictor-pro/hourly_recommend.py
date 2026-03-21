#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每小时股票推荐任务
- 基于预测数据筛选 Top 5 推荐股票
- 保存推荐结果到 stock-recommendations 目录
- 输出简要推荐信息
"""

import json
import os
from datetime import datetime
from pathlib import Path

# ============== 配置 ==============
CONFIG = {
    'workspace': '/home/admin/openclaw/workspace',
    'predictions_dir': 'predictions',
    'recommendations_dir': 'stock-recommendations',
    'top_n': 5,  # Top 5 推荐
}

def load_latest_predictions():
    """加载最新的预测数据"""
    predictions_path = Path(CONFIG['workspace']) / CONFIG['predictions_dir']
    
    # 查找最新的小时预测文件
    hourly_files = sorted(predictions_path.glob("2026-03-17_*-[0-9][0-9].json"), reverse=True)
    
    if not hourly_files:
        #  fallback 到每日预测文件
        daily_files = sorted(predictions_path.glob("2026-03-17.json"), reverse=True)
        prediction_files = daily_files
    else:
        prediction_files = hourly_files
    
    if not prediction_files:
        print("❌ 未找到预测数据文件")
        return []
    
    latest_file = prediction_files[0]
    print(f"📊 加载预测数据：{latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'predictions' in data:
        return data['predictions']
    elif isinstance(data, list):
        return data
    
    return []

def analyze_and_rank(predictions):
    """分析并排名股票"""
    qualified = []
    
    for pred in predictions:
        rise_pct = pred.get('predicted_change', 0)
        confidence = pred.get('confidence', '')
        direction = pred.get('direction', '')
        
        # 只考虑上涨的股票
        if direction != '上涨':
            continue
        
        qualified.append({
            'code': pred.get('stock_code', ''),
            'name': pred.get('stock_name', ''),
            'industry': pred.get('industry', ''),
            'current_price': pred.get('current_price', 0),
            'predicted_price': pred.get('predicted_price', 0),
            'rise_pct': rise_pct,
            'confidence': confidence,
            'direction': direction,
            'ma5': pred.get('ma5', 0),
            'ma20': pred.get('ma20', 0),
            'rsi': pred.get('rsi', 0),
            'trend_score': pred.get('trend_score', 0),
            'momentum_5d': pred.get('momentum_5d', 0),
        })
    
    # 综合评分：涨幅 * 置信度权重 + 趋势分
    def score(stock):
        conf_weight = {'高': 1.5, '中': 1.2, '低': 1.0}.get(stock['confidence'], 1.0)
        return stock['rise_pct'] * conf_weight + stock['trend_score']
    
    qualified.sort(key=score, reverse=True)
    
    return qualified

def generate_recommendation_report(top_stocks, all_qualified):
    """生成推荐报告"""
    now = datetime.now()
    report_time = now.strftime('%Y-%m-%d %H:%M')
    
    report = f"""# 📈 股票推荐报告

**生成时间**: {report_time}
**数据来源**: 小时预测模型 (2026-03-17)
**筛选范围**: 全部监控股票 ({len(all_qualified)} 只上涨股票)

---

## 🏆 Top 5 推荐股票

| 排名 | 股票 | 代码 | 行业 | 当前价 | 预测价 | 预期涨幅 | 置信度 | 趋势分 |
|------|------|------|------|--------|--------|----------|--------|--------|
"""
    
    for i, stock in enumerate(top_stocks, 1):
        report += f"| {i} | {stock['name']} | {stock['code']} | {stock['industry']} | "
        report += f"{stock['current_price']:.2f} | {stock['predicted_price']:.2f} | "
        report += f"+{stock['rise_pct']:.2f}% | {stock['confidence']} | {stock['trend_score']:.1f} |\n"
    
    report += f"""
---

## 📊 推荐分析

### 1. {top_stocks[0]['name']} ({top_stocks[0]['code']})
- **行业**: {top_stocks[0]['industry']}
- **当前价格**: ¥{top_stocks[0]['current_price']:.2f}
- **目标价格**: ¥{top_stocks[0]['predicted_price']:.2f}
- **预期涨幅**: +{top_stocks[0]['rise_pct']:.2f}%
- **置信度**: {top_stocks[0]['confidence']}
- **推荐理由**: 综合评分最高，趋势强劲，{top_stocks[0]['momentum_5d']:.2f}% 的 5 日动量

### 2. {top_stocks[1]['name']} ({top_stocks[1]['code']})
- **行业**: {top_stocks[1]['industry']}
- **当前价格**: ¥{top_stocks[1]['current_price']:.2f}
- **目标价格**: ¥{top_stocks[1]['predicted_price']:.2f}
- **预期涨幅**: +{top_stocks[1]['rise_pct']:.2f}%
- **置信度**: {top_stocks[1]['confidence']}
- **推荐理由**: 高置信度上涨信号，技术面良好

### 3. {top_stocks[2]['name']} ({top_stocks[2]['code']})
- **行业**: {top_stocks[2]['industry']}
- **当前价格**: ¥{top_stocks[2]['current_price']:.2f}
- **目标价格**: ¥{top_stocks[2]['predicted_price']:.2f}
- **预期涨幅**: +{top_stocks[2]['rise_pct']:.2f}%
- **置信度**: {top_stocks[2]['confidence']}
- **推荐理由**: 趋势分数高，上涨动能充足

### 4. {top_stocks[3]['name']} ({top_stocks[3]['code']})
- **行业**: {top_stocks[3]['industry']}
- **当前价格**: ¥{top_stocks[3]['current_price']:.2f}
- **目标价格**: ¥{top_stocks[3]['predicted_price']:.2f}
- **预期涨幅**: +{top_stocks[3]['rise_pct']:.2f}%
- **置信度**: {top_stocks[3]['confidence']}
- **推荐理由**: 技术指标向好，具备上涨潜力

### 5. {top_stocks[4]['name']} ({top_stocks[4]['code']})
- **行业**: {top_stocks[4]['industry']}
- **当前价格**: ¥{top_stocks[4]['current_price']:.2f}
- **目标价格**: ¥{top_stocks[4]['predicted_price']:.2f}
- **预期涨幅**: +{top_stocks[4]['rise_pct']:.2f}%
- **置信度**: {top_stocks[4]['confidence']}
- **推荐理由**: 综合评估具备投资价值

---

## 📈 整体统计

- **监控股票总数**: 345 只
- **上涨信号股票**: {len(all_qualified)} 只
- **高置信度股票**: {sum(1 for s in all_qualified if s['confidence'] == '高')} 只
- **Top 5 平均预期涨幅**: +{sum(s['rise_pct'] for s in top_stocks) / len(top_stocks):.2f}%

---

## ⚠️ 风险提示

1. 本推荐基于历史数据和技术分析模型，**不构成投资建议**
2. 股市有风险，投资需谨慎
3. 建议结合基本面、市场消息和个人风险承受能力综合判断
4. 设置合理止损位，控制仓位风险
5. 过往预测表现不代表未来结果

---

*报告由股票推荐系统自动生成 | 每小时更新*
"""
    
    return report

def generate_brief_message(top_stocks):
    """生成简要推荐消息"""
    now = datetime.now()
    report_time = now.strftime('%H:%M')
    
    msg = f"📈 **股票推荐** ({report_time})\n\n"
    msg += f"**Top 5 推荐股票** (基于小时预测模型)\n\n"
    
    for i, stock in enumerate(top_stocks, 1):
        emoji = '🟢' if stock['confidence'] == '高' else '🟡'
        msg += f"{i}. {emoji} **{stock['name']}** ({stock['code']})\n"
        msg += f"   行业：{stock['industry']} | 预期涨幅：+{stock['rise_pct']:.2f}% [{stock['confidence']}置信度]\n"
        msg += f"   当前价：¥{stock['current_price']:.2f} → 目标价：¥{stock['predicted_price']:.2f}\n\n"
    
    msg += "📄 完整报告已保存至 `stock-recommendations/` 目录\n\n"
    msg += "⚠️ 风险提示：本推荐不构成投资建议，股市有风险，投资需谨慎"
    
    return msg

def main():
    print("=" * 60)
    print("每小时股票推荐任务")
    print("=" * 60)
    
    # 加载预测数据
    predictions = load_latest_predictions()
    if not predictions:
        print("❌ 无法加载预测数据")
        return
    
    print(f"📊 加载了 {len(predictions)} 只股票的预测数据")
    
    # 分析并排名
    all_qualified = analyze_and_rank(predictions)
    print(f"✅ 筛选出 {len(all_qualified)} 只上涨股票")
    
    # 获取 Top 5
    top_stocks = all_qualified[:CONFIG['top_n']]
    print(f"🏆 Top 5 推荐股票已确定")
    
    # 生成报告
    report = generate_recommendation_report(top_stocks, all_qualified)
    
    # 保存报告
    now = datetime.now()
    report_file = Path(CONFIG['workspace']) / CONFIG['recommendations_dir'] / f"hourly-{now.strftime('%Y-%m-%d-%H')}.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 报告已保存：{report_file}")
    
    # 保存 JSON 数据
    json_file = Path(CONFIG['workspace']) / CONFIG['recommendations_dir'] / f"hourly-{now.strftime('%Y-%m-%d-%H')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': now.isoformat(),
            'top_stocks': top_stocks,
            'total_qualified': len(all_qualified)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"📄 JSON 数据已保存：{json_file}")
    
    # 生成简要消息
    brief_msg = generate_brief_message(top_stocks)
    
    print("\n" + "=" * 60)
    print("✅ 推荐完成")
    print("=" * 60)
    
    # 输出简要消息
    print(f"\n[MESSAGE]\n{brief_msg}")

if __name__ == "__main__":
    main()
