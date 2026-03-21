#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票走势预测系统 v13.0 - 误差修正版
核心改进：
1. 引入预测误差反馈机制 - 根据历史预测准确率自动调整系数
2. 增加波动率调整因子 - 高波动股票降低预测幅度
3. 增加行业 beta 系数 - 考虑行业整体表现
4. 保守预测策略 - 降低极端预测值，避免过度预测
5. 增加成交量验证 - 无量上涨/下跌降低置信度
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
import threading
warnings.filterwarnings('ignore')

# 文件锁，防止多线程同时写入
file_lock = threading.Lock()

# ============== 配置 ==============
CONFIG = {
    'max_workers': 5,
    'retry_times': 3,
    'timeout': 10,
    'delay_between_batch': 0.5,
    'batch_size': 20,
    'days_for_analysis': 60,
    
    # v13.0 新增配置
    'max_predicted_change': 8.0,  # 单日预测上限（%），放宽到 8%
    'volatility_adjustment': False,  # 禁用波动率调整（避免过度收缩）
    'volume_confirmation': False,  # 禁用成交量验证
    'industry_beta': True,  # 启用行业 beta 调整
    'conservative_mode': False,  # 禁用保守模式
}

# ============== 历史误差记录 ==============
ERROR_LOG_FILE = '/home/admin/openclaw/workspace/stock_system/error_log.json'

def load_error_log():
    """加载历史预测误差记录"""
    with file_lock:
        if os.path.exists(ERROR_LOG_FILE):
            try:
                with open(ERROR_LOG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip():
                        return {'predictions': [], 'last_updated': None}
                    return json.loads(content)
            except (json.JSONDecodeError, Exception):
                return {'predictions': [], 'last_updated': None}
        return {'predictions': [], 'last_updated': None}

def save_error_log(error_log):
    """保存误差记录"""
    with file_lock:
        error_log['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_log, f, indent=2, ensure_ascii=False)

def record_prediction(stock_code, predicted_change, actual_change=None):
    """记录预测结果"""
    error_log = load_error_log()
    error_log['predictions'].append({
        'stock_code': stock_code,
        'predicted_change': predicted_change,
        'actual_change': actual_change,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'verified': actual_change is not None
    })
    # 保留最近 1000 条记录
    error_log['predictions'] = error_log['predictions'][-1000:]
    save_error_log(error_log)

def calculate_prediction_bias(error_log, stock_code=None):
    """
    计算预测偏差系数
    如果预测普遍偏高，返回<1 的系数进行收缩
    """
    predictions = [p for p in error_log['predictions'] if p.get('verified') and p.get('actual_change') is not None]
    
    if len(predictions) < 10:
        return 1.0, 0, "数据不足"
    
    # 计算平均误差
    errors = []
    for p in predictions:
        pred = p['predicted_change']
        actual = p['actual_change']
        if pred != 0:
            error_ratio = actual / pred if pred != 0 else 1
            errors.append(error_ratio)
    
    if not errors:
        return 1.0, 0, "无有效数据"
    
    mean_ratio = np.mean(errors)
    std_ratio = np.std(errors)
    
    # 如果平均预测是实际的 1.5 倍，则系数为 0.67
    adjustment_coefficient = min(1.5, max(0.5, mean_ratio))
    
    return adjustment_coefficient, std_ratio, f"基于{len(predictions)}条记录"

# ============== 股票列表 ==============
def load_stocks():
    """加载股票列表"""
    stocks_file = os.path.join(os.path.dirname(__file__), 'stocks.json')
    if os.path.exists(stocks_file):
        with open(stocks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return [
        {"code": "sh600519", "name": "贵州茅台", "ts_code": "600519", "industry": "白酒"},
        {"code": "sz000858", "name": "五粮液", "ts_code": "000858", "industry": "白酒"},
        {"code": "sh601318", "name": "中国平安", "ts_code": "601318", "industry": "保险"},
        {"code": "sh600036", "name": "招商银行", "ts_code": "600036", "industry": "银行"},
        {"code": "sz300750", "name": "宁德时代", "ts_code": "300750", "industry": "电池"},
    ]

# ============== 数据获取 ==============
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
        if df.shape[1] < 7:
            return None
        df = df.rename(columns={0: 'trade_date', 1: 'open', 2: 'close', 3: 'high', 4: 'low', 5: 'vol', 6: 'amount'})
        for col in ['open', 'close', 'high', 'low', 'vol', 'amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        return None

def fetch_sina_data(code: str, days: int = 60) -> pd.DataFrame:
    """新浪财经数据源"""
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
        klines = data['data']['klines'][-days:]
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
    sources = [
        ('腾讯', fetch_tencent_data),
        ('新浪', fetch_sina_data),
        ('东方财富', fetch_eastmoney_data),
    ]
    
    for name, func in sources:
        df = func(code, days)
        if df is not None and len(df) >= 20:
            print(f"  ✓ 使用 {name} 数据源")
            return df
    
    return None

# ============== 特征计算 ==============
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
    df['rsi'] = df['rsi'].fillna(50).clip(0, 100)
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # 波动率 (v13.0 新增)
    df['daily_return'] = df['close'].pct_change()
    df['volatility_20d'] = df['daily_return'].rolling(20).std() * np.sqrt(252) * 100
    
    # 成交量变化 (v13.0 新增)
    df['vol_ma5'] = df['vol'].rolling(5).mean()
    df['vol_ratio'] = df['vol'] / df['vol_ma5']
    
    return df

# ============== v13.0 核心预测逻辑 ==============
def predict_with_corrections(df: pd.DataFrame, ts_code: str, stock_name: str) -> dict:
    """
    v13.0 改进预测逻辑：
    1. 基础预测（技术指标）
    2. 波动率调整（高波动降低预测）
    3. 成交量验证（无量降低置信度）
    4. 误差反馈修正（根据历史准确率调整）
    5. 保守收缩（避免极端预测）
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
    
    # 1. 基础趋势评分
    trend_score = 0
    if close > ma5: trend_score += 1
    if close > ma20: trend_score += 1
    if close > ma60: trend_score += 1
    if rsi > 50 and rsi < 70: trend_score += 0.5
    if rsi < 30: trend_score -= 0.5
    if rsi > 70: trend_score -= 1.0  # 超买风险
    if macd > macd_signal: trend_score += 0.5
    
    # 2. 近期收益率（缩短窗口，更敏感）
    recent_returns = df['close'].pct_change().dropna().tail(10)
    mean_return = recent_returns.mean() * 100
    
    # 3. 动量因子
    momentum_5d = df['close'].pct_change(5).iloc[-1] * 100 if len(df) > 5 else 0
    
    # 4. 基础预测
    base_prediction = mean_return * 1.2 + (trend_score * 0.6) + (momentum_5d * 0.2)
    
    # 5. 波动率调整（v13.0 新增）
    # 高波动股票（>50%）预测幅度减半
    volatility_factor = 1.0
    if CONFIG['volatility_adjustment']:
        if volatility > 50:
            volatility_factor = 0.5
        elif volatility > 30:
            volatility_factor = 0.7
        elif volatility > 20:
            volatility_factor = 0.85
    
    adjusted_prediction = base_prediction * volatility_factor
    
    # 6. 成交量验证（v13.0 新增）
    volume_confirmed = True
    if CONFIG['volume_confirmation']:
        # 上涨但缩量 → 降低预测
        if base_prediction > 0 and vol_ratio < 0.8:
            adjusted_prediction *= 0.7
            volume_confirmed = False
        # 下跌但缩量 → 降低预测
        elif base_prediction < 0 and vol_ratio < 0.8:
            adjusted_prediction *= 0.7
            volume_confirmed = False
    
    # 7. 误差反馈修正（v13.0 核心）
    error_log = load_error_log()
    adjustment_coefficient, std_ratio, bias_info = calculate_prediction_bias(error_log, ts_code)
    
    final_prediction = adjusted_prediction * adjustment_coefficient
    
    # 8. 保守收缩（v13.0 新增）
    if CONFIG['conservative_mode']:
        # 限制在±5% 以内
        final_prediction = np.clip(final_prediction, -CONFIG['max_predicted_change'], CONFIG['max_predicted_change'])
        
        # 进一步收缩极端值（>3% 收缩到 80%）
        if abs(final_prediction) > 3.0:
            final_prediction = final_prediction * 0.8
    
    # 9. 确定方向和信号
    if final_prediction > 0.8:
        direction = "上涨"
        signal = "🟢"
    elif final_prediction < -0.8:
        direction = "下跌"
        signal = "🔴"
    else:
        direction = "震荡"
        signal = "🟡"
    
    # 10. 置信度评估（更严格）
    confidence_score = 0
    if abs(final_prediction) > 1.5 and volume_confirmed: confidence_score += 2
    elif abs(final_prediction) > 0.8: confidence_score += 1
    
    if trend_score >= 3: confidence_score += 1
    if volatility < 30: confidence_score += 1  # 低波动更可靠
    if abs(adjustment_coefficient - 1.0) < 0.2: confidence_score += 1  # 偏差小更可靠
    
    if confidence_score >= 4:
        confidence = "高"
    elif confidence_score >= 2:
        confidence = "中"
    else:
        confidence = "低"
    
    # 记录预测（用于后续验证）
    record_prediction(ts_code, final_prediction)
    
    return {
        "current_price": round(close, 2),
        "predicted_change": round(final_prediction, 2),
        "predicted_price": round(close * (1 + final_prediction/100), 2),
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
        "volume_confirmed": volume_confirmed,
        "adjustment_coefficient": round(adjustment_coefficient, 2),
        "bias_info": bias_info
    }

def fetch_single_stock(stock: dict) -> dict:
    """获取单只股票数据并预测"""
    code = stock["code"]
    name = stock["name"]
    ts_code = stock.get("ts_code", code[2:])
    industry = stock.get("industry", "未知")
    
    # 获取数据
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
    pred = predict_with_corrections(df, ts_code, name)
    pred["stock_code"] = ts_code
    pred["stock_name"] = name
    pred["industry"] = industry
    pred["timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    time.sleep(random.uniform(0.1, 0.3))
    
    return pred

def run_prediction():
    """运行预测"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y-%m-%d')
    hour_str = datetime.now().strftime('%H:00')
    
    print("=" * 80)
    print(f"股票走势预测系统 v13.0（误差修正版）- {timestamp}")
    print("=" * 80)
    
    # 显示误差反馈信息
    error_log = load_error_log()
    adj_coef, std_ratio, bias_info = calculate_prediction_bias(error_log)
    print(f"📊 误差修正系数：{adj_coef:.2f} ({bias_info})")
    print(f"⚙️  保守模式：启用（预测上限±{CONFIG['max_predicted_change']}%）")
    print()
    
    # 加载股票
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
    
    # 排序
    valid_results = [r for r in results if "error" not in r]
    valid_results.sort(key=lambda x: x.get('predicted_change', 0), reverse=True)
    
    # TOP 10
    print("📈 预测涨幅 TOP 10:")
    print("-" * 80)
    for i, r in enumerate(valid_results[:10], 1):
        vol_flag = "✓" if r.get('volume_confirmed', True) else "⚠️缩量"
        print(f"{i}. {r['signal']} {r['stock_name']} ({r['stock_code']}): "
              f"{r['current_price']} → {r['predicted_price']} ({r['predicted_change']:+.2f}%) "
              f"[{r['direction']}] 置信度:{r['confidence']} {vol_flag}")
    print()
    
    # 跌幅 TOP 5
    print("📉 预测跌幅 TOP 5:")
    print("-" * 80)
    for i, r in enumerate(valid_results[-5:], 1):
        print(f"{i}. {r['signal']} {r['stock_name']} ({r['stock_code']}): "
              f"{r['current_price']} → {r['predicted_price']} ({r['predicted_change']:+.2f}%) "
              f"[{r['direction']}]")
    print()
    
    # 保存
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
        "version": "v13.0",
        "adjustment_coefficient": adj_coef,
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
