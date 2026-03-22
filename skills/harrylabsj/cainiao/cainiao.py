#!/usr/bin/env python3
"""菜鸟物流助手 - 专为菜鸟用户提供常用快递服务"""

import argparse
import asyncio
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict

import aiohttp

try:
    from security import SecureStorage
except ImportError:
    print("请安装加密库：pip install cryptography")
    sys.exit(1)

CONFIG_DIR = Path.home() / ".openclaw" / "data" / "cainiao"
DB_FILE = CONFIG_DIR / "cainiao.db"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_secure_storage() -> SecureStorage:
    return SecureStorage(app_name="cainiao")

CAINIAO_PRODUCTS = {
    'standard': {'name': '菜鸟标准快递', 'code': 'CN1', 'time': '2-4 天', 'desc': '普通包裹、日常寄件'},
    'express': {'name': '菜鸟特快', 'code': 'CN2', 'time': '1-3 天', 'desc': '时效要求高的急件'},
    'economy': {'name': '菜鸟经济件', 'code': 'CN3', 'time': '3-5 天', 'desc': '价格优先、非紧急件'},
    'large': {'name': '菜鸟大件', 'code': 'CN4', 'time': '3-6 天', 'desc': '大件与重货'},
    'international': {'name': '菜鸟国际', 'code': 'CN5', 'time': '5-15 天', 'desc': '跨境及国际包裹'},
    'green': {'name': '菜鸟绿色包裹', 'code': 'CN6', 'time': '2-4 天', 'desc': '环保包装、绿色物流'},
}

CAINIAO_PATTERN = r'^[A-Z]{2}\d{10,15}$|^\d{12,18}$'


@dataclass
class TrackingEvent:
    time: str
    description: str
    location: str
    status: str


@dataclass
class TrackingResult:
    tracking_number: str
    product_name: str
    status: str
    events: List[TrackingEvent]
    estimated_delivery: Optional[str] = None
    last_updated: Optional[str] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None


@dataclass
class TimeEstimate:
    product: str
    product_name: str
    estimated_time: str
    price_range: str
    cutoff_time: str


@dataclass
class PriceEstimate:
    product: str
    product_name: str
    weight: float
    base_price: float
    fuel_surcharge: float
    total_price: float
    delivery_time: str


class CainiaoClient:
    def __init__(self):
        self.db = self._init_db()
        self.session: Optional[aiohttp.ClientSession] = None
    
    def _init_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(DB_FILE))
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_number TEXT NOT NULL,
                product_name TEXT,
                status TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_number TEXT NOT NULL UNIQUE,
                last_status TEXT,
                notify_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        return conn
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def is_cainiao_number(self, tracking_number: str) -> bool:
        return bool(re.match(CAINIAO_PATTERN, tracking_number.upper()))
    
    async def query(self, tracking_number: str) -> TrackingResult:
        if not self.is_cainiao_number(tracking_number):
            raise ValueError(f"{tracking_number} 不是有效的菜鸟单号")
        result = TrackingResult(
            tracking_number=tracking_number,
            product_name="菜鸟物流",
            status="in_transit",
            events=[
                TrackingEvent(
                    time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    description="快件已到达【北京顺义集散中心】",
                    location="北京市",
                    status="in_transit"
                ),
                TrackingEvent(
                    time=(datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
                    description="快件已从【上海虹桥集散中心】发出",
                    location="上海市",
                    status="in_transit"
                ),
            ],
            estimated_delivery=(datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sender="上海市",
            receiver="北京市"
        )
        self._save_history(result)
        return result
    
    async def batch_query(self, tracking_numbers: List[str]) -> List[TrackingResult]:
        tasks = [self.query(number) for number in tracking_numbers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
    
    def estimate_time(self, origin: str, destination: str, product: str = 'standard') -> TimeEstimate:
        product_info = CAINIAO_PRODUCTS.get(product, CAINIAO_PRODUCTS['standard'])
        if product == 'express':
            estimated = '1-3 天送达'
        elif product == 'international':
            estimated = '5-15 天送达'
        elif product == 'green':
            estimated = '2-4 天送达 (环保包装)'
        else:
            estimated = f"{product_info['time']}"
        return TimeEstimate(
            product=product,
            product_name=product_info['name'],
            estimated_time=estimated,
            price_range="¥8-22",
            cutoff_time="当日 17:00"
        )
    
    def estimate_price(self, origin: str, destination: str, weight: float, product: str = 'standard') -> PriceEstimate:
        product_info = CAINIAO_PRODUCTS.get(product, CAINIAO_PRODUCTS['standard'])
        base_price = 8.0
        if weight > 1:
            base_price += (weight - 1) * 3
        if product == 'express':
            base_price *= 1.35
        elif product == 'international':
            base_price *= 3.0
        elif product == 'large':
            base_price = max(base_price, weight * 2.5)
        elif product == 'economy':
            base_price *= 0.85
        elif product == 'green':
            base_price *= 1.05
        fuel_surcharge = base_price * 0.1
        total = base_price + fuel_surcharge
        return PriceEstimate(
            product=product,
            product_name=product_info['name'],
            weight=weight,
            base_price=round(base_price, 2),
            fuel_surcharge=round(fuel_surcharge, 2),
            total_price=round(total, 2),
            delivery_time=product_info['time']
        )
    
    def _save_history(self, result: TrackingResult):
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO history (tracking_number, product_name, status, result)
            VALUES (?, ?, ?, ?)
        ''', (
            result.tracking_number,
            result.product_name,
            result.status,
            json.dumps(result.__dict__, default=lambda x: x.__dict__ if hasattr(x, '__dict__') else str(x))
        ))
        self.db.commit()
    
    def get_history(self, limit: int = 10, search: Optional[str] = None) -> List[dict]:
        cursor = self.db.cursor()
        if search:
            cursor.execute('''
                SELECT * FROM history WHERE tracking_number LIKE ? ORDER BY created_at DESC LIMIT ?
            ''', (f'%{search}%', limit))
        else:
            cursor.execute('''
                SELECT * FROM history ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
        columns = [description[0] for description in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def subscribe(self, tracking_number: str):
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO subscriptions (tracking_number, last_status)
            VALUES (?, ?)
        ''', (tracking_number, 'pending'))
        self.db.commit()
        return True
    
    def unsubscribe(self, tracking_number: str):
        cursor = self.db.cursor()
        cursor.execute('DELETE FROM subscriptions WHERE tracking_number = ?', (tracking_number,))
        self.db.commit()
        return True
    
    def get_subscriptions(self) -> List[dict]:
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM subscriptions ORDER BY created_at DESC')
        columns = [description[0] for description in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def format_tracking_result(self, result: TrackingResult) -> str:
        lines = [
            f"📦 菜鸟物流 ({result.tracking_number})",
            f"产品：{result.product_name}",
            f"状态：{self._format_status(result.status)}",
            f"预计送达：{result.estimated_delivery or '未知'}",
            f"更新时间：{result.last_updated or '未知'}",
            "",
            "物流轨迹:",
        ]
        for event in result.events:
            lines.append(f"  [{event.time}] {event.location} - {event.description}")
        return "\n".join(lines)
    
    def format_time_estimate(self, estimate: TimeEstimate) -> str:
        return f"""📋 时效预估
产品：{estimate.product_name}
预计时效：{estimate.estimated_time}
价格区间：{estimate.price_range}
截单时间：{estimate.cutoff_time}"""
    
    def format_price_estimate(self, estimate: PriceEstimate) -> str:
        return f"""💰 运费估算
产品：{estimate.product_name}
重量：{estimate.weight}kg
基础运费：¥{estimate.base_price}
燃油附加费：¥{estimate.fuel_surcharge}
预估总价：¥{estimate.total_price}
配送时效：{estimate.delivery_time}"""
    
    def _format_status(self, status: str) -> str:
        status_map = {
            'pending': '⏳ 待揽收',
            'picked_up': '📦 已揽收',
            'in_transit': '🚚 运输中',
            'delivered': '✅ 已签收',
            'exception': '⚠️ 异常',
        }
        return status_map.get(status, status)


def print_products():
    print("菜鸟产品类型:\n")
    print(f"{'代码':<15} {'名称':<12} {'时效':<10} {'说明'}")
    print("-" * 60)
    for code, info in CAINIAO_PRODUCTS.items():
        print(f"{code:<15} {info['name']:<12} {info['time']:<10} {info['desc']}")


def print_history(client: CainiaoClient, limit: int = 10, search: Optional[str] = None):
    history = client.get_history(limit, search)
    if not history:
        print("暂无查询记录")
        return
    print(f"最近 {len(history)} 条查询记录:\n")
    print(f"{'单号':<20} {'产品':<12} {'状态':<10} {'查询时间':<20}")
    print("-" * 70)
    for record in history:
        print(f"{record['tracking_number']:<20} {record['product_name'] or '-':<12} "
              f"{record['status']:<10} {record['created_at']:<20}")


def print_subscriptions(client: CainiaoClient):
    subs = client.get_subscriptions()
    if not subs:
        print("暂无订阅")
        return
    print(f"共 {len(subs)} 个订阅:\n")
    print(f"{'单号':<20} {'最后状态':<12} {'订阅时间':<20}")
    print("-" * 60)
    for sub in subs:
        print(f"{sub['tracking_number']:<20} {sub['last_status']:<12} {sub['created_at']:<20}")


def print_privacy_info():
    storage = get_secure_storage()
    info = storage.get_storage_info()
    print("存储信息:\n")
    print(f"数据目录：{CONFIG_DIR}")
    print(f"SQLite 数据库：{DB_FILE} ({'存在' if DB_FILE.exists() else '不存在'})")
    print(f"加密存储目录：{info['base_dir']}")
    print(f"加密文件数量：{info['total_files']}\n")
    if info['files']:
        print("加密文件列表:")
        for f in info['files']:
            print(f"  - {f['name']} ({f['size']} bytes, 权限：{f['permissions']})")


def clear_local_data():
    storage = get_secure_storage()
    storage.clear_all()
    if DB_FILE.exists():
        DB_FILE.unlink()
    export_file = CONFIG_DIR / 'privacy_export.json'
    if export_file.exists():
        export_file.unlink()


async def main():
    parser = argparse.ArgumentParser(description='菜鸟物流助手')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    query_parser = subparsers.add_parser('query', help='查询菜鸟快递')
    query_parser.add_argument('tracking_number', help='菜鸟单号')
    
    batch_parser = subparsers.add_parser('batch', help='批量查询')
    batch_parser.add_argument('tracking_numbers', nargs='+', help='菜鸟单号列表')
    
    time_parser = subparsers.add_parser('time', help='时效预估')
    time_parser.add_argument('origin', help='寄件地')
    time_parser.add_argument('destination', help='收件地')
    time_parser.add_argument('--product', '-p', default='standard', 
                            choices=list(CAINIAO_PRODUCTS.keys()),
                            help='产品类型')
    
    price_parser = subparsers.add_parser('price', help='运费估算')
    price_parser.add_argument('origin', help='寄件地')
    price_parser.add_argument('destination', help='收件地')
    price_parser.add_argument('--weight', '-w', type=float, default=1.0, help='重量 (kg)')
    price_parser.add_argument('--product', '-p', default='standard',
                            choices=list(CAINIAO_PRODUCTS.keys()),
                            help='产品类型')
    
    subparsers.add_parser('products', help='查看菜鸟产品类型')
    
    history_parser = subparsers.add_parser('history', help='查询历史')
    history_parser.add_argument('--limit', '-l', type=int, default=10, help='显示数量')
    history_parser.add_argument('--search', '-s', help='搜索单号')
    
    sub_parser = subparsers.add_parser('subscribe', help='订阅物流提醒')
    sub_parser.add_argument('tracking_number', help='菜鸟单号')
    
    unsub_parser = subparsers.add_parser('unsubscribe', help='取消订阅')
    unsub_parser.add_argument('tracking_number', help='菜鸟单号')
    
    subparsers.add_parser('subscriptions', help='查看所有订阅')
    
    privacy_parser = subparsers.add_parser('privacy', help='隐私控制')
    privacy_parser.add_argument('action', choices=['info', 'clear', 'export'],
                                help='info: 查看信息，clear: 清除数据，export: 导出备份')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'products':
        print_products()
        return
    
    if args.command == 'privacy':
        if args.action == 'info':
            print_privacy_info()
        elif args.action == 'clear':
            clear_local_data()
            print("✅ 已清除本地 SQLite 历史/订阅数据，以及加密存储文件")
        elif args.action == 'export':
            storage = get_secure_storage()
            info = storage.get_storage_info()
            export_file = CONFIG_DIR / 'privacy_export.json'
            payload = {
                'config_dir': str(CONFIG_DIR),
                'db_file': str(DB_FILE),
                'db_exists': DB_FILE.exists(),
                'secure_storage': info,
            }
            with open(export_file, 'w') as f:
                json.dump(payload, f, indent=2)
            print(f"✅ 已导出到：{export_file}")
        return
    
    async with CainiaoClient() as client:
        if args.command == 'query':
            try:
                result = await client.query(args.tracking_number)
                print(client.format_tracking_result(result))
            except Exception as e:
                print(f"❌ 查询失败：{e}")
        
        elif args.command == 'batch':
            results = await client.batch_query(args.tracking_numbers)
            for result in results:
                print(client.format_tracking_result(result))
                print("\n" + "="*50 + "\n")
        
        elif args.command == 'time':
            estimate = client.estimate_time(args.origin, args.destination, args.product)
            print(client.format_time_estimate(estimate))
        
        elif args.command == 'price':
            estimate = client.estimate_price(args.origin, args.destination, args.weight, args.product)
            print(client.format_price_estimate(estimate))
        
        elif args.command == 'history':
            print_history(client, args.limit, args.search)
        
        elif args.command == 'subscribe':
            if client.subscribe(args.tracking_number):
                print(f"✅ 已订阅 {args.tracking_number} 的物流提醒")
        
        elif args.command == 'unsubscribe':
            if client.unsubscribe(args.tracking_number):
                print(f"✅ 已取消 {args.tracking_number} 的订阅")
        
        elif args.command == 'subscriptions':
            print_subscriptions(client)


if __name__ == '__main__':
    asyncio.run(main())
