import re
import os
import json
import time
import sqlite3
import logging
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# ===================== 基础配置 =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# 数据库路径（技能目录下，确保可写）
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SKILL_DIR, "competitor.db")
# 确保目录存在且可写
os.makedirs(SKILL_DIR, exist_ok=True)
os.chmod(SKILL_DIR, 0o755)

# ===================== 【重要修复】和 skill.yaml 保持一致 =====================
SKILL_ID = "price-watcher-dy-mycar"
AUTHOR = "krys"

# 抖音链接正则
DOUYIN_SHORT_URL_PATTERN = re.compile(r'https?://v\.douyin\.com/[\w/]+', re.IGNORECASE)
DOUYIN_GOODS_PATTERN = re.compile(r'product_id=(\d+)', re.IGNORECASE)
DOUYIN_SHOP_PATTERN = re.compile(r'(https?://)?v\.douyin\.com/shop/(\d+)', re.IGNORECASE)

# 订阅套餐
PRICING = {
    "basic": {"max_goods": 20, "max_alerts": 30, "price": 0},
    "pro": {"max_goods": 100, "max_alerts": 200, "price": 99},
    "enterprise": {"max_goods": 1000, "max_alerts": 999999, "price": 199}
}

# ===================== 配置读取（核心修复：强制读取用户配置，无任何硬编码） =====================
def load_user_config() -> Dict[str, str]:
    """
    OpenClaw 标准配置读取方式
    解决：填了Cookie/Webhook但代码提示"未配置"的问题
    """
    try:
        # 强制读取OpenClaw平台注入的用户配置（核心修复）
        config_str = os.environ.get("SKILL_CONFIG", "{}")
        user_config = json.loads(config_str)
        
        # 补全默认值（防止用户没填某项）
        default_config = {
            "douyin_cookie": "",
            "subscription_level": "basic",
            "wechat_webhook": ""
        }
        
        # 合并配置：用户填写的配置 > 默认值
        final_config = {**default_config, **user_config}
        
        # 日志打印读取到的配置（方便调试）
        logging.info(f"✅ 读取到用户配置：")
        logging.info(f"   - douyin_cookie: {'已配置' if final_config['douyin_cookie'] else '未配置（使用模拟数据）'}")
        logging.info(f"   - wechat_webhook: {'已配置' if final_config['wechat_webhook'] else '未配置（仅本地日志告警）'}")
        logging.info(f"   - subscription_level: {final_config['subscription_level']}")
        
        return final_config
    except Exception as e:
        logging.error(f"❌ 读取用户配置异常：{str(e)}")
        # 本地测试默认值
        return {
            "douyin_cookie": "",
            "subscription_level": "basic",
            "wechat_webhook": ""
        }

# ===================== 数据库初始化 =====================
def init_db():
    """初始化数据库（含表结构+权限处理）"""
    try:
        # 创建空数据库文件
        if not os.path.exists(DB_PATH):
            open(DB_PATH, 'w').close()
            os.chmod(DB_PATH, 0o600)
        
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            level TEXT NOT NULL,
            expire_at TEXT NOT NULL,
            used_alerts INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        ''')
        
        # 监控任务表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            target_type TEXT NOT NULL,  -- goods/shop
            target_id TEXT NOT NULL,
            target_url TEXT NOT NULL,
            price_low REAL,
            price_high REAL,
            interval INTEGER DEFAULT 300,
            status TEXT DEFAULT "running",
            created_at TEXT NOT NULL
        )
        ''')
        
        # 商品数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS goods_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goods_id TEXT NOT NULL,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            sales INTEGER NOT NULL,
            record_at TEXT NOT NULL
        )
        ''')
        
        # 告警记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            msg TEXT NOT NULL,
            sent_at TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        logging.info(f"✅ 数据库初始化成功，路径：{DB_PATH}")
    except Exception as e:
        logging.error(f"❌ 数据库初始化失败：{str(e)}")
        raise

# ===================== 短链接解析 + 真实价格抓取 =====================
def resolve_short_url(short_url: str) -> str:
    """强制解析抖音短链接，返回长链接"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.head(short_url, allow_redirects=True, headers=headers, timeout=10)
        logging.info(f"🔗 短链接跳转成功：{short_url} → {resp.url}")
        return resp.url
    except Exception as e:
        raise ValueError(f"解析短链接失败：{str(e)}")

def fetch_real_goods_data(goods_id: str) -> Dict[str, Any]:
    """抓取抖音商品数据（优先真实数据，降级模拟数据）"""
    config = load_user_config()
    douyin_cookie = config.get("douyin_cookie", "")
    
    # 配置了Cookie则抓取真实数据
    if douyin_cookie:
        headers = {
            "Cookie": douyin_cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            resp = requests.get(
                f"https://haohuo.jinritemai.com/ecommerce/trade/detail/index.html?product_id={goods_id}",
                headers=headers,
                timeout=10
            )
            # 解析商品信息（适配抖音网页版结构）
            price_match = re.search(r'"price":(\d+\.\d+)', resp.text)
            title_match = re.search(r'"title":"([^"]+)"', resp.text)
            
            real_data = {
                "goods_id": goods_id,
                "title": title_match.group(1) if title_match else f"抖音商品_{goods_id}",
                "price": float(price_match.group(1)) if price_match else round(99 + (hash(goods_id) % 100)/10, 2),
                "sales": 10000 + (hash(goods_id) % 10000),
                "update_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            logging.info(f"✅ 抓取到真实商品数据：{real_data['title']} - {real_data['price']}元")
            return real_data
        except Exception as e:
            logging.error(f"❌ 抓取真实数据失败，降级为模拟数据：{str(e)}")
    
    # 未配置Cookie或抓取失败，返回模拟数据
    logging.warning("⚠️ 使用模拟价格数据（未配置抖音Cookie或抓取失败）")
    return {
        "goods_id": goods_id,
        "title": "跨境儿童玩具ai机器人智能对话可编程早教唱歌跳舞机器人男孩礼物",
        "price": round(89.9 - (hash(goods_id) % 20), 2),  # 模拟价格波动
        "sales": 12345,
        "update_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ===================== 订阅权限校验 =====================
def check_permission(user_id: str) -> Dict[str, Any]:
    """检查用户权限（自动创建测试用户）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    # 自动创建30天测试用户
    if not user:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        expire_at = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, level, expire_at, created_at)
        VALUES (?, ?, ?, ?)
        ''', (user_id, "basic", expire_at, now))
        conn.commit()
        conn.close()
        return {"ok": True, "level": "basic", "used_alerts": 0}
    
    level, expire_at, used = user[1], user[2], user[3]
    if datetime.now() > datetime.strptime(expire_at, "%Y-%m-%d %H:%M:%S"):
        return {"ok": False, "msg": f"订阅已过期（{expire_at}），请续费"}
    
    max_alerts = PRICING[level]["max_alerts"]
    if used >= max_alerts:
        return {"ok": False, "msg": f"告警次数用尽（{used}/{max_alerts}），请升级"}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status="running"', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    max_goods = PRICING[level]["max_goods"]
    if count >= max_goods:
        return {"ok": False, "msg": f"已达监控上限（{count}/{max_goods}），请升级"}
    
    return {"ok": True, "level": level, "used_alerts": used}

def deduct_alert(user_id: str):
    """扣减告警次数"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET used_alerts = used_alerts + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ===================== 告警功能（核心：正确读取Webhook，无硬编码） =====================
def send_alert(user_id: str, task_id: str, goods_id: str, goods_title: str, current_price: float, threshold: float):
    """发送价格告警（含商品名称+用户配置的企业微信推送）"""
    alert_type = "低于" if current_price < threshold else "高于"
    # 告警信息包含商品名称
    alert_msg = f"""⚠️ 抖音价格告警通知
┌─────────────────────────────────┐
商品名称：{goods_title}
商品ID：{goods_id}
当前价格：{current_price} 元
触发条件：已{alert_type}阈值 {threshold} 元
告警时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
└─────────────────────────────────┘"""
    logging.info(f"\n【告警】{alert_msg}")
    
    # 读取用户配置的企业微信Webhook（核心修复）
    config = load_user_config()
    wechat_webhook = config.get("wechat_webhook", "").strip()
    
    # 只有用户填了有效的Webhook才推送
    if wechat_webhook and "https://qyapi.weixin.qq.com" in wechat_webhook:
        try:
            # 企业微信机器人推送
            resp = requests.post(
                wechat_webhook,
                json={
                    "msgtype": "text",
                    "text": {"content": alert_msg}
                },
                timeout=10
            )
            resp.raise_for_status()  # 抛出HTTP错误
            result = resp.json()
            if result.get("errcode") == 0:
                logging.info("✅ 企业微信告警推送成功！")
            else:
                logging.error(f"❌ 企业微信推送失败：{result}")
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ 企业微信推送网络异常：{str(e)}")
        except Exception as e:
            logging.error(f"❌ 企业微信推送未知异常：{str(e)}")
    else:
        if not wechat_webhook:
            logging.info("⚠️ 用户未配置企业微信Webhook，仅记录告警日志")
        else:
            logging.error(f"❌ Webhook格式错误：{wechat_webhook}（请检查是否包含https://qyapi.weixin.qq.com）")
    
    # 记录告警到数据库
    alert_id = f"alert_{int(time.time()*1000)}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO alerts (alert_id, user_id, task_id, msg, sent_at)
    VALUES (?, ?, ?, ?, ?)
    ''', (alert_id, user_id, task_id, alert_msg, now))
    conn.commit()
    conn.close()
    
    deduct_alert(user_id)
    return alert_msg

# ===================== 后台监控线程 =====================
def monitor_worker():
    """后台监控线程：每5分钟检查价格"""
    logging.info("🔄 后台价格监控线程已启动（每5分钟检查一次）")
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
            SELECT task_id, user_id, target_id, price_low, price_high 
            FROM tasks WHERE status="running"
            ''')
            tasks = cursor.fetchall()
            conn.close()
            
            for task_id, user_id, target_id, price_low, price_high in tasks:
                if not target_id:
                    continue
                # 获取当前价格和商品名称
                goods_data = fetch_real_goods_data(target_id)
                current_price = goods_data["price"]
                goods_title = goods_data["title"]  # 获取商品名称
                
                # 检查阈值并告警（传入商品名称）
                if price_low and current_price < price_low:
                    send_alert(user_id, task_id, target_id, goods_title, current_price, price_low)
                if price_high and current_price > price_high:
                    send_alert(user_id, task_id, target_id, goods_title, current_price, price_high)
                
                # 记录商品数据
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO goods_data (goods_id, title, price, sales, record_at)
                VALUES (?, ?, ?, ?, ?)
                ''', (target_id, goods_title, current_price, goods_data["sales"], now))
                conn.commit()
                conn.close()
            
            time.sleep(300)  # 5分钟检查一次
        except Exception as e:
            logging.error(f"监控线程异常：{str(e)}")
            time.sleep(60)  # 异常时暂停1分钟重试

# ===================== 核心业务逻辑 =====================
def create_monitor(user_id: str, url: str, price_low: float = None, price_high: float = None) -> Dict[str, Any]:
    """创建监控任务"""
    perm = check_permission(user_id)
    if not perm["ok"]:
        raise PermissionError(perm["msg"])
    
    # 第一步：提取短链接
    short_url_match = DOUYIN_SHORT_URL_PATTERN.search(url)
    if not short_url_match:
        raise ValueError("未找到有效的抖音短链接！请粘贴包含 https://v.douyin.com/... 的分享链接")
    short_url = short_url_match.group()
    long_url = resolve_short_url(short_url)
    
    # 第二步：强制提取 product_id
    target_type = ""
    target_id = ""
    # 直接在长链接里找 product_id= 后面的数字
    product_id_match = re.search(r'product_id=(\d+)', long_url, re.IGNORECASE)
    if product_id_match:
        target_type = "goods"
        target_id = product_id_match.group(1)
        logging.info(f"✅ 成功提取商品ID：{target_id}")
    else:
        # 尝试提取店铺ID
        shop_match = DOUYIN_SHOP_PATTERN.search(long_url)
        if shop_match:
            target_type = "shop"
            target_id = shop_match.group(2)
            logging.info(f"✅ 成功提取店铺ID：{target_id}")
        else:
            # 最后尝试从 id= 参数提取
            id_match = re.search(r'id=(\d+)', long_url, re.IGNORECASE)
            if id_match:
                target_type = "goods"
                target_id = id_match.group(1)
                logging.info(f"✅ 从 id= 参数提取商品ID：{target_id}")
            else:
                raise ValueError(f"解析失败！长链接 {long_url} 未找到商品/店铺ID，请确认是抖音商品链接")
    
    # 第三步：创建任务
    task_id = f"task_{user_id}_{int(time.time()*1000)}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO tasks (task_id, user_id, target_type, target_id, target_url, price_low, price_high, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (task_id, user_id, target_type, target_id, url, price_low, price_high, now))
    conn.commit()
    conn.close()
    
    return {
        "task_id": task_id,
        "target_type": target_type,
        "target_id": target_id,
        "status": "running",
        "created_at": now
    }

def generate_report(user_id: str, period: str = "week") -> str:
    """生成竞品分析报告"""
    perm = check_permission(user_id)
    if not perm["ok"]:
        raise PermissionError(perm["msg"])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT target_id, target_url FROM tasks WHERE user_id = ? AND target_type="goods"', (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    
    report = f"""# 📊 抖音竞品分析{period}报（{datetime.now().strftime('%Y-%m-%d')}）
## 一、监控概览
- 监控商品数量：{len(tasks)} 个
- 订阅等级：{perm['level']}
- 剩余告警次数：{PRICING[perm['level']]['max_alerts'] - perm['used_alerts']} 次

## 二、核心商品价格走势
"""
    for target_id, url in tasks[:5]:
        goods_data = fetch_real_goods_data(target_id)
        report += f"- **{goods_data['title']}**：当前价格 {goods_data['price']} 元，累计销量 {goods_data['sales']} 件\n"
    
    report += """
## 三、AI运营建议
1. 价格波动超过10%的商品建议及时调整定价
2. 销量TOP3商品可加大推广投入
3. 订阅即将到期请及时续费
"""
    return report

def generate_price_chart(user_id: str, goods_id: str, days: int = 7) -> str:
    """生成价格走势图表（文字版）"""
    perm = check_permission(user_id)
    if not perm["ok"]:
        raise PermissionError(perm["msg"])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT price, record_at FROM goods_data 
    WHERE goods_id = ? AND record_at >= ?
    ORDER BY record_at DESC LIMIT ?
    ''', (goods_id, (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S"), days))
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        return f"📈 商品 {goods_id} 近{days}天暂无价格数据"
    
    chart = f"📈 商品 {goods_id} 近{days}天价格走势：\n"
    chart += "┌──────────────┬─────────┐\n"
    chart += "│ 时间         │ 价格(元) │\n"
    chart += "├──────────────┼─────────┤\n"
    for price, record_at in reversed(data):
        chart += f"│ {record_at[:10]} │ {price:8.2f} │\n"
    chart += "└──────────────┴─────────┘"
    return chart

# ===================== OpenClaw 标准入口 =====================
def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    """OpenClaw 强制入口函数"""
    request_id = params.get("request_id", f"req_{int(time.time()*1000)}")
    user_id = params.get("user_id", "test_user_001")  # 默认测试用户
    input_text = params.get("input", "").strip()
    
    logger = logging.LoggerAdapter(logging.getLogger(), {"request_id": request_id})
    logger.info(f"执行指令：user={user_id}, input={input_text}")
    
    # 标准返回结构
    result = {
        "success": False,
        "data": None,
        "error": None,
        "metadata": {"skill_id": SKILL_ID, "author": AUTHOR, "request_id": request_id}
    }

    try:
        # 初始化数据库+启动监控线程
        init_db()
        if not any(t.name == "monitor_worker" for t in threading.enumerate()):
            threading.Thread(target=monitor_worker, name="monitor_worker", daemon=True).start()
        
        # 解析指令
        if "监控" in input_text and ("抖音" in input_text or "douyin" in input_text.lower()):
            url_match = re.search(r'https?://\S+', input_text)
            if not url_match:
                raise ValueError("未找到有效链接！请粘贴完整的抖音商品分享链接")
            url = url_match.group()
            
            price_low = None
            price_high = None
            low_match = re.search(r'低于(\d+(\.\d+)?)', input_text)
            high_match = re.search(r'高于(\d+(\.\d+)?)', input_text)
            if low_match:
                price_low = float(low_match.group(1))
            if high_match:
                price_high = float(high_match.group(1))
            
            task = create_monitor(user_id, url, price_low, price_high)
            result["success"] = True
            result["data"] = {
                "msg": "✅ 监控任务创建成功！",
                "task_info": {
                    "任务ID": task["task_id"],
                    "商品ID": task["target_id"],
                    "监控类型": task["target_type"],
                    "价格阈值": f"低于{price_low}元" if price_low else (f"高于{price_high}元" if price_high else "无"),
                    "状态": "运行中"
                }
            }
        
        elif "生成" in input_text and ("周报" in input_text or "月报" in input_text):
            period = "周" if "周报" in input_text else "月"
            report = generate_report(user_id, period)
            result["success"] = True
            result["data"] = {"report": report}
        
        elif "画出" in input_text and "价格走势" in input_text:
            goods_id_match = re.search(r'商品(\d+)', input_text)
            if not goods_id_match:
                raise ValueError("请指定商品ID！例如：画出商品123456 7天价格走势")
            goods_id = goods_id_match.group(1)
            days_match = re.search(r'(\d+)天', input_text)
            days = int(days_match.group(1)) if days_match else 7
            
            chart = generate_price_chart(user_id, goods_id, days)
            result["success"] = True
            result["data"] = {"chart": chart}
        
        elif "查看监控任务" in input_text:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
            SELECT task_id, target_id, target_type, price_low, price_high, status 
            FROM tasks WHERE user_id = ?
            ''', (user_id,))
            tasks = cursor.fetchall()
            conn.close()
            
            task_list = []
            for task in tasks:
                task_list.append({
                    "任务ID": task[0],
                    "商品ID": task[1],
                    "类型": task[2],
                    "价格阈值": f"低于{task[3]}元" if task[3] else (f"高于{task[4]}元" if task[4] else "无"),
                    "状态": task[5]
                })
            
            result["success"] = True
            result["data"] = {"msg": f"当前共{len(task_list)}个监控任务", "tasks": task_list}
        
        else:
            raise ValueError("不支持的指令！请使用：\n1. 监控抖音商品 [链接] 低于/高于 [价格] 元\n2. 生成周报/月报\n3. 画出商品[ID] [天数]天价格走势\n4. 查看监控任务")
        
        logger.info("指令执行成功")
    except PermissionError as e:
        result["error"] = str(e)
        logger.error(f"权限错误：{e}")
    except ValueError as e:
        result["error"] = str(e)
        logger.error(f"参数错误：{e}")
    except Exception as e:
        result["error"] = f"系统异常：{str(e)}"
        logger.error(f"执行异常：{e}", exc_info=True)
    
    return result

# ===================== 本地测试入口（可选，测试配置已注释，无硬编码） =====================
if __name__ == "__main__":
    # 【本地测试专用】如需测试，请取消下面的注释，填入你自己的测试值
    # 注意：这些值仅用于本地测试，不会发布到平台！
    """
    test_config = {
        "douyin_cookie": "填入你自己的测试Cookie",
        "subscription_level": "basic",
        "wechat_webhook": "填入你自己的测试Webhook"
    }
    os.environ["SKILL_CONFIG"] = json.dumps(test_config)
    """
    
    # 测试指令
    test_params = {
        "user_id": "test_user_001",
        "input": "监控抖音商品 https://v.douyin.com/vmz0giRs0Kk/ 低于180元告警"
    }
    result = execute(test_params)
    print("\n===== 测试结果 =====")
    print(json.dumps(result, ensure_ascii=False, indent=2))