#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票走势预测系统 v12.0
- 扩展股票列表至 300+ 只
- 多数据源支持（腾讯、新浪、东方财富）
- 并发请求 + 分批获取
- 自动重试机制
- v12.0 修正：提高趋势权重、增加动量因子、优化置信度阈值
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import requests
import warnings
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

# ============== 配置 ==============
CONFIG = {
    'max_workers': 5,  # 并发线程数
    'retry_times': 3,  # 重试次数
    'timeout': 10,  # 请求超时（秒）
    'delay_between_batch': 0.5,  # 批次间隔（秒）
    'batch_size': 20,  # 每批股票数量
    'days_for_analysis': 60,  # 分析天数
}

# ============== 股票列表 ==============
def load_stocks():
    """加载股票列表"""
    stocks_file = os.path.join(os.path.dirname(__file__), 'stocks.json')
    if os.path.exists(stocks_file):
        with open(stocks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    # 默认股票（如果配置文件不存在）
    return [
        {"code": "sh600519", "name": "贵州茅台", "ts_code": "600519"},
        {"code": "sz000858", "name": "五粮液", "ts_code": "000858"},
        {"code": "sh601318", "name": "中国平安", "ts_code": "601318"},
        {"code": "sh600036", "name": "招商银行", "ts_code": "600036"},
        {"code": "sz300750", "name": "宁德时代", "ts_code": "300750"},
    ]

# ============== 多数据源 ==============
def fetch_tencent_data(code: str, days: int = 60) -> pd.DataFrame:
    """腾讯财经数据源"""
    try:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{days},qfq"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=CONFIG['timeout'])
        data = response.json()
        if data.get('code') != 0 or 'data' not in data:
            return None
        stock_data = data['data'].get(code, {})
        klines = stock_data.get('qfqday', [])
        if not klines:
            return None
        df = pd.DataFrame(klines)
        if df.shape[1] < 5:
            return None
        df = df.rename(columns={0: 'trade_date', 1: 'open', 2: 'close', 3: 'high', 4: 'low', 5: 'vol'})
        for col in ['open', 'close', 'high', 'low', 'vol']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        return None

def fetch_sina_data(code: str, days: int = 60) -> pd.DataFrame:
    """新浪财经数据源"""
    try:
        # 新浪接口
        symbol = code[2:] if len(code) > 2 else code
        url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&datalen={days}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=CONFIG['timeout'])
        data = response.json()
        if not data or not isinstance(data, list):
            return None
        df = pd.DataFrame(data)
        if len(df) < 5:
            return None
        df = df.rename(columns={'day': 'trade_date', 'open': 'open', 'close': 'close', 'high': 'high', 'low': 'low', 'volume': 'vol'})
        for col in ['open', 'close', 'high', 'low', 'vol']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        return None

def fetch_eastmoney_data(code: str, days: int = 60) -> pd.DataFrame:
    """东方财富数据源"""
    try:
        market = "SH" if code.startswith("sh") else "SZ"
        symbol = code[2:]
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market}.{symbol}&klt=101&fqt=1&beg=19900101&end=20991231"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=CONFIG['timeout'])
        data = response.json()
        if not data.get('data') or not data['data'].get('klines'):
            return None
        klines = data['data']['klines'][-days:]  # 取最近 N 天
        if not klines:
            return None
        rows = [k.split(',') for k in klines]
        df = pd.DataFrame(rows, columns=['trade_date', 'open', 'close', 'high', 'low', 'vol', 'amount', 'amplitude', 'chg', 'change', 'turnover'])
        for col in ['open', 'close', 'high', 'low', 'vol']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        return None

def fetch_data_with_fallback(code: str, days: int = 60) -> pd.DataFrame:
    """多数据源 fallback 策略"""
    # 尝试顺序：腾讯 -> 新浪 -> 东方财富
    sources = [
        ('腾讯', fetch_tencent_data),
        ('新浪', fetch_sina_data),
        ('东方财富', fetch_eastmoney_data),
    ]
    
    for name, func in sources:
        df = func(code, days)
        if df is not None and len(df) >= 20:
            return df
    
    return None

def fetch_single_stock(stock: dict) -> dict:
    """获取单只股票数据并预测"""
    code = stock["code"]
    name = stock["name"]
    ts_code = stock.get("ts_code", code[2:])
    industry = stock.get("industry", "未知")
    
    # 获取数据（多数据源 fallback）
    df = fetch_data_with_fallback(code, CONFIG['days_for_analysis'])
    if df is None or len(df) < 20:
        return {
            "stock_code": ts_code,
            "stock_name": name,
            "industry": industry,
            "error": "数据获取失败",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    # 计算特征
    df = calculate_features(df)
    
    # 预测
    pred = predict_next_day(df, ts_code)
    pred["stock_code"] = ts_code
    pred["stock_name"] = name
    pred["industry"] = industry
    pred["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 添加小延迟避免请求过快
    time.sleep(random.uniform(0.1, 0.3))
    
    return pred

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    df = df.sort_values('trade_date').reset_index(drop=True)
    
    # 均线
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    # 偏离度
    df['dev_ma5'] = (df['close'] - df['ma5']) / df['ma5'] * 100
    df['dev_ma20'] = (df['close'] - df['ma20']) / df['ma20'] * 100
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50)
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # 目标（5 日后涨跌幅）
    df['target_5d'] = df['close'].shift(-5) / df['close'] - 1
    df['target_5d_pct'] = df['target_5d'] * 100
    
    return df

def predict_next_day(df: pd.DataFrame, ts_code: str) -> dict:
    """预测走势"""
    if len(df) < 20:
        return {"error": "数据不足"}
    
    latest = df.iloc[-1]
    close = latest['close']
    ma5 = latest['ma5']
    ma20 = latest['ma20']
    ma60 = latest.get('ma60', ma20)
    rsi = latest['rsi']
    macd = latest.get('macd', 0)
    macd_signal = latest.get('macd_signal', 0)
    
    # 趋势评分 (v12.0 修正)
    trend_score = 0
    if close > ma5: trend_score += 1
    if close > ma20: trend_score += 1
    if close > ma60: trend_score += 1
    if rsi > 50: trend_score += 0.5
    if rsi < 30: trend_score -= 0.5
    if rsi > 70: trend_score -= 0.5
    if macd > macd_signal: trend_score += 0.5
    
    # 近期收益率 (v12.0: 窗口从 10 日延长至 15 日，减少噪音)
    recent_returns = df['close'].pct_change().dropna().tail(15)
    mean_return = recent_returns.mean() * 100
    std_return = recent_returns.std() * 100
    
    # 动量因子 (v12.0 新增): 5 日收益率趋势
    momentum_5d = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    momentum_factor = momentum_5d * 0.3 if abs(momentum_5d) > 0 else 0
    
    # 预测 (v12.0 修正：提高趋势权重，增加动量因子)
    predicted_change = mean_return * 1.5 + (trend_score * 0.8) + momentum_factor
    
    # 方向 (v12.0: 阈值从 1% 调整为 0.8%)
    if predicted_change > 0.8:
        direction = "上涨"
        signal = "🟢"
    elif predicted_change < -0.8:
        direction = "下跌"
        signal = "🔴"
    else:
        direction = "震荡"
        signal = "🟡"
    
    return {
        "current_price": round(close, 2),
        "predicted_change": round(predicted_change, 2),
        "predicted_price": round(close * (1 + predicted_change/100), 2),
        "direction": direction,
        "signal": signal,
        "confidence": "高" if abs(predicted_change) > 1.5 else ("中" if abs(predicted_change) > 0.8 else "低"),
        "ma5": round(ma5, 2),
        "ma20": round(ma20, 2),
        "ma60": round(ma60, 2) if not pd.isna(ma60) else None,
        "rsi": round(rsi, 2),
        "macd": round(macd, 4) if not pd.isna(macd) else None,
        "trend_score": round(trend_score, 1),
        "momentum_5d": round(momentum_5d, 2)
    }

def run_prediction():
    """运行预测（并发 + 分批）"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')
    hour_str = datetime.now().strftime('%H:00')
    
    print("=" * 80)
    print(f"股票走势预测系统 v12.0 - {timestamp}")
    print("=" * 80)
    
    # 加载股票
    stocks = load_stocks()
    total = len(stocks)
    print(f"📊 监控股票数量：{total} 只")
    print(f"⚙️  并发线程：{CONFIG['max_workers']}, 批次大小：{CONFIG['batch_size']}")
    print()
    
    results = []
    errors = []
    
    # 分批处理
    batches = [stocks[i:i+CONFIG['batch_size']] for i in range(0, total, CONFIG['batch_size'])]
    
    for batch_idx, batch in enumerate(batches):
        batch_num = batch_idx + 1
        print(f"📦 处理批次 {batch_num}/{len(batches)} ({len(batch)} 只股票)...")
        
        # 并发获取
        with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
            futures = {executor.submit(fetch_single_stock, stock): stock for stock in batch}
            for future in as_completed(futures):
                result = future.result()
                if "error" in result and result.get("error") == "数据获取失败":
                    errors.append(result)
                else:
                    results.append(result)
        
        # 批次间隔
        if batch_idx < len(batches) - 1:
            time.sleep(CONFIG['delay_between_batch'])
    
    # 打印结果摘要
    print()
    print("=" * 80)
    print(f"✅ 成功：{len(results)} 只")
    print(f"❌ 失败：{len(errors)} 只")
    print()
    
    # 按预测涨幅排序
    valid_results = [r for r in results if "error" not in r]
    valid_results.sort(key=lambda x: x.get('predicted_change', 0), reverse=True)
    
    # 打印 TOP 10
    print("📈 预测涨幅 TOP 10:")
    print("-" * 80)
    for i, r in enumerate(valid_results[:10], 1):
        print(f"{i}. {r['signal']} {r['stock_name']} ({r['stock_code']}): "
              f"{r['current_price']} → {r['predicted_price']} ({r['predicted_change']:+.2f}%) "
              f"[{r['direction']}] 置信度:{r['confidence']}")
    print()
    
    # 打印跌幅 TOP 5
    print("📉 预测跌幅 TOP 5:")
    print("-" * 80)
    for i, r in enumerate(valid_results[-5:], 1):
        print(f"{i}. {r['signal']} {r['stock_name']} ({r['stock_code']}): "
              f"{r['current_price']} → {r['predicted_price']} ({r['predicted_change']:+.2f}%) "
              f"[{r['direction']}]")
    print()
    
    # 保存记录
    output_dir = '/home/admin/openclaw/workspace/predictions'
    os.makedirs(output_dir, exist_ok=True)
    
    daily_file = f"{output_dir}/{date_str}.json"
    hourly_file = f"{output_dir}/{date_str}_{hour_str.replace(':', '-')}.json"
    
    # 读取已有记录
    existing_daily = []
    if os.path.exists(daily_file):
        with open(daily_file, 'r', encoding='utf-8') as f:
            existing_daily = json.load(f)
    
    # 添加新预测
    existing_daily.append({
        "timestamp": timestamp,
        "hour": hour_str,
        "total_stocks": total,
        "success": len(results),
        "failed": len(errors),
        "predictions": results
    })
    
    # 保存
    with open(daily_file, 'w', encoding='utf-8') as f:
        json.dump(existing_daily, f, ensure_ascii=False, indent=2)
    
    with open(hourly_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "total_stocks": total,
            "success": len(results),
            "failed": len(errors),
            "predictions": results
        }, f, ensure_ascii=False, indent=2)
    
    print("=" * 80)
    print(f"📁 记录已保存:")
    print(f"   每日：{daily_file}")
    print(f"   每小时：{hourly_file}")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    run_prediction()
