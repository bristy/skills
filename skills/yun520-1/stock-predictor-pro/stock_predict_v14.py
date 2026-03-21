#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票走势预测系统 v14.0 - 增强版
核心改进：
1. 放宽预测上限到 8%（可预测强势股）
2. 增强动量和趋势权重
3. 增加均线偏离度、RSI、MACD 加分
4. 禁用过度保守的收缩策略
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
    'max_workers': 5,
    'retry_times': 3,
    'timeout': 10,
    'delay_between_batch': 0.5,
    'batch_size': 20,
    'days_for_analysis': 60,
    
    # v14.0 增强配置
    'max_predicted_change': 8.0,  # 放宽到 8%
    'min_predicted_change': -8.0,
}

# ============== 股票列表 ==============
def load_stocks():
    stocks_file = os.path.join(os.path.dirname(__file__), 'stocks.json')
    if os.path.exists(stocks_file):
        with open(stocks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# ============== 数据获取 ==============
def fetch_tencent_data(code: str, days: int = 60) -> pd.DataFrame:
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
        if df.shape[1] < 7:
            return None
        df = df.rename(columns={0: 'trade_date', 1: 'open', 2: 'close', 3: 'high', 4: 'low', 5: 'vol', 6: 'amount'})
        for col in ['open', 'close', 'high', 'low', 'vol']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except:
        return None

def fetch_sina_data(code: str, days: int = 60) -> pd.DataFrame:
    try:
        symbol = code[2:] if len(code) > 2 else code
        url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&datalen={days}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=CONFIG['timeout'])
        data = response.json()
        if not data or not isinstance(data, list):
            return None
        df = pd.DataFrame(data)
        if len(df) < 20:
            return None
        df = df.rename(columns={'day': 'trade_date', 'open': 'open', 'close': 'close', 'high': 'high', 'low': 'low', 'volume': 'vol'})
        for col in ['open', 'close', 'high', 'low', 'vol']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except:
        return None

def fetch_eastmoney_data(code: str, days: int = 60) -> pd.DataFrame:
    try:
        market = "SH" if code.startswith("sh") else "SZ"
        symbol = code[2:]
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market}.{symbol}&klt=101&fqt=1&beg=19900101&end=20991231"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=CONFIG['timeout'])
        data = response.json()
        if not data.get('data') or not data['data'].get('klines'):
            return None
        klines = data['data']['klines'][-days:]
        rows = [k.split(',') for k in klines]
        df = pd.DataFrame(rows, columns=['trade_date', 'open', 'close', 'high', 'low', 'vol', 'amount', 'amplitude', 'chg', 'change', 'turnover'])
        for col in ['open', 'close', 'high', 'low', 'vol']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except:
        return None

def fetch_data_with_fallback(code: str, days: int = 60) -> pd.DataFrame:
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

# ============== 特征计算 ==============
def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values('trade_date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50).clip(0, 100)
    
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    df['daily_return'] = df['close'].pct_change()
    df['volatility_20d'] = df['daily_return'].rolling(20).std() * np.sqrt(252) * 100
    df['vol_ma5'] = df['vol'].rolling(5).mean()
    df['vol_ratio'] = df['vol'] / df['vol_ma5']
    
    return df

# ============== v14.0 增强预测逻辑 ==============
def predict_enhanced(df: pd.DataFrame, ts_code: str) -> dict:
    """
    v14.0 增强预测：
    1. 增强动量和趋势权重
    2. 增加均线偏离度、RSI、MACD 加分
    3. 放宽预测上限到 8%
    """
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
    volatility = latest.get('volatility_20d', 20)
    vol_ratio = latest.get('vol_ratio', 1)
    
    # 1. 趋势评分（增强权重）
    trend_score = 0
    if close > ma5: trend_score += 1.5
    if close > ma20: trend_score += 1.5
    if close > ma60: trend_score += 1.5
    if rsi > 50 and rsi < 70: trend_score += 1.0
    if rsi < 30: trend_score -= 1.0
    if rsi > 70: trend_score += 0.5  # 强势股可能继续涨
    if macd > macd_signal: trend_score += 1.0
    
    # 2. 近期收益率（增强权重）
    recent_returns = df['close'].pct_change().dropna().tail(10)
    mean_return = recent_returns.mean() * 100
    
    # 3. 动量因子（增强权重）
    momentum_5d = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # 4. 基础预测（增强）
    base_prediction = mean_return * 2.5 + (trend_score * 1.2) + (momentum_5d * 0.6)
    
    # 5. 均线偏离度加分
    dev_from_ma5 = (close - ma5) / ma5 * 100 if ma5 > 0 else 0
    if dev_from_ma5 > 3:
        base_prediction += 2.0
    elif dev_from_ma5 > 2:
        base_prediction += 1.5
    elif dev_from_ma5 > 1:
        base_prediction += 1.0
    
    # 6. RSI 动量加分
    if 60 < rsi < 80:
        base_prediction += 1.5  # 强势区间
    elif rsi >= 80:
        base_prediction += 1.0  # 超买但可能继续涨
    elif 50 < rsi <= 60:
        base_prediction += 0.5
    
    # 7. MACD 加分
    if macd > 0 and macd > macd_signal:
        base_prediction += 1.5  # 金叉且为正
    
    # 8. 成交量确认加分
    if vol_ratio > 1.5:
        base_prediction += 1.0  # 放量
    elif vol_ratio > 1.2:
        base_prediction += 0.5
    
    # 9. 波动率调整（轻微）
    if volatility > 60:
        base_prediction *= 0.9
    elif volatility > 40:
        base_prediction *= 0.95
    
    # 10. 保守上限（放宽到 8%）
    adjusted_prediction = np.clip(base_prediction, CONFIG['min_predicted_change'], CONFIG['max_predicted_change'])
    
    # 11. 确定方向和信号
    if adjusted_prediction > 1.5:
        direction = "上涨"
        signal = "🟢"
    elif adjusted_prediction > 0.5:
        direction = "上涨"
        signal = "🟢"
    elif adjusted_prediction < -1.5:
        direction = "下跌"
        signal = "🔴"
    else:
        direction = "震荡"
        signal = "🟡"
    
    # 12. 置信度评估
    confidence_score = 0
    if abs(adjusted_prediction) > 3.0: confidence_score += 2
    elif abs(adjusted_prediction) > 1.5: confidence_score += 1
    
    if trend_score >= 4: confidence_score += 2
    elif trend_score >= 2: confidence_score += 1
    
    if volatility < 40: confidence_score += 1
    if vol_ratio > 1.2: confidence_score += 1
    
    if confidence_score >= 5:
        confidence = "高"
    elif confidence_score >= 3:
        confidence = "中"
    else:
        confidence = "低"
    
    return {
        "current_price": round(close, 2),
        "predicted_change": round(adjusted_prediction, 2),
        "predicted_price": round(close * (1 + adjusted_prediction/100), 2),
        "direction": direction,
        "signal": signal,
        "confidence": confidence,
        "ma5": round(ma5, 2),
        "ma20": round(ma20, 2),
        "ma60": round(ma60, 2) if not pd.isna(ma60) else None,
        "rsi": round(rsi, 2),
        "macd": round(macd, 4) if not pd.isna(macd) else None,
        "trend_score": round(trend_score, 1),
        "momentum_5d": round(momentum_5d, 2),
        "volatility_20d": round(volatility, 2),
        "vol_ratio": round(vol_ratio, 2),
    }

def fetch_single_stock(stock: dict) -> dict:
    code = stock["code"]
    name = stock["name"]
    ts_code = stock.get("ts_code", code[2:])
    industry = stock.get("industry", "未知")
    
    df = fetch_data_with_fallback(code, CONFIG['days_for_analysis'])
    if df is None or len(df) < 20:
        return {
            "stock_code": ts_code,
            "stock_name": name,
            "industry": industry,
            "error": "数据获取失败",
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    df = calculate_features(df)
    pred = predict_enhanced(df, ts_code)
    pred["stock_code"] = ts_code
    pred["stock_name"] = name
    pred["industry"] = industry
    pred["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    time.sleep(random.uniform(0.1, 0.3))
    return pred

def run_prediction():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')
    hour_str = datetime.now().strftime('%H:00')
    
    print("=" * 80)
    print(f"股票走势预测系统 v14.0（增强版）- {timestamp}")
    print("=" * 80)
    print(f"⚙️  预测上限：±{CONFIG['max_predicted_change']}%")
    print(f"⚙️  增强策略：动量 + 趋势 + 均线偏离 + RSI + MACD")
    print()
    
    stocks = load_stocks()
    total = len(stocks)
    print(f"📊 监控股票数量：{total} 只")
    print()
    
    results = []
    errors = []
    
    batches = [stocks[i:i+CONFIG['batch_size']] for i in range(0, total, CONFIG['batch_size'])]
    
    for batch_idx, batch in enumerate(batches):
        batch_num = batch_idx + 1
        print(f"📦 处理批次 {batch_num}/{len(batches)} ({len(batch)} 只股票)...")
        
        with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
            futures = {executor.submit(fetch_single_stock, stock): stock for stock in batch}
            for future in as_completed(futures):
                result = future.result()
                if "error" in result and result.get("error") == "数据获取失败":
                    errors.append(result)
                else:
                    results.append(result)
        
        if batch_idx < len(batches) - 1:
            time.sleep(CONFIG['delay_between_batch'])
    
    print()
    print("=" * 80)
    print(f"✅ 成功：{len(results)} 只")
    print(f"❌ 失败：{len(errors)} 只")
    print()
    
    valid_results = [r for r in results if "error" not in r]
    valid_results.sort(key=lambda x: x.get('predicted_change', 0), reverse=True)
    
    print("📈 预测涨幅 TOP 10:")
    print("-" * 80)
    for i, r in enumerate(valid_results[:10], 1):
        print(f"{i}. {r['signal']} {r['stock_name']} ({r['stock_code']}): "
              f"{r['current_price']} → {r['predicted_price']} ({r['predicted_change']:+.2f}%) "
              f"[{r['direction']}] 置信度:{r['confidence']}")
    print()
    
    print("📉 预测跌幅 TOP 5:")
    print("-" * 80)
    for i, r in enumerate(valid_results[-5:], 1):
        print(f"{i}. {r['signal']} {r['stock_name']} ({r['stock_code']}): "
              f"{r['current_price']} → {r['predicted_price']} ({r['predicted_change']:+.2f}%) "
              f"[{r['direction']}]")
    print()
    
    output_dir = '/home/admin/openclaw/workspace/predictions'
    os.makedirs(output_dir, exist_ok=True)
    
    daily_file = f"{output_dir}/{date_str}.json"
    hourly_file = f"{output_dir}/{date_str}_{hour_str.replace(':', '-')}.json"
    
    existing_daily = []
    if os.path.exists(daily_file):
        with open(daily_file, 'r', encoding='utf-8') as f:
            existing_daily = json.load(f)
    
    existing_daily.append({
        "timestamp": timestamp,
        "hour": hour_str,
        "total_stocks": total,
        "success": len(results),
        "failed": len(errors),
        "version": "v14.0",
        "predictions": valid_results
    })
    
    with open(daily_file, 'w', encoding='utf-8') as f:
        json.dump(existing_daily, f, indent=2, ensure_ascii=False)
    
    with open(hourly_file, 'w', encoding='utf-8') as f:
        json.dump(valid_results, f, indent=2, ensure_ascii=False)
    
    print(f"📁 数据已保存:")
    print(f"   每日：{daily_file}")
    print(f"   每小时：{hourly_file}")
    print()
    print("=" * 80)
    print("✅ 预测完成")
    print("=" * 80)
    
    return {
        'total': total,
        'success': len(results),
        'failed': len(errors),
        'top_gainers': valid_results[:10],
        'top_losers': valid_results[-5:],
        'daily_file': daily_file,
        'hourly_file': hourly_file
    }

if __name__ == '__main__':
    run_prediction()
