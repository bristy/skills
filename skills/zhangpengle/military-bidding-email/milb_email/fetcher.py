#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
军工采购商机邮件发送工具 (milb-email)

自动抓取全军武器装备采购信息网、军队采购网、国防科大采购信息网的商机数据，
生成 Excel 汇总文件，并通过邮件发送报告。

用法:
    milb-email [选项]

示例:
    milb-email                           # 发送昨日报告（默认）
    milb-email --today                   # 发送今日报告
    milb-email --date 2026-03-23        # 发送指定日期报告
    milb-email --keywords "模型,仿真"    # 使用自定义关键词筛选
    milb-email --to test@example.com     # 测试发送至指定收件人
"""

import sys
import os
import subprocess
import json
import pandas as pd
from pathlib import Path

from milb_email.config import get_email_config


def _import_fetcher():
    """延迟导入避免循环依赖"""
    sys.modules.pop('config', None)
    sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/skills/military-bidding-fetcher')
    from fetcher import fetch_all_bidding
    return fetch_all_bidding


def get_high_recommend_items(df_weain, df_military, df_nudt):
    """
    从各渠道数据中提取高推荐等级的项目。

    Args:
        df_weain: 全军武器装备采购信息网 DataFrame
        df_military: 军队采购网 DataFrame
        df_nudt: 国防科大采购信息网 DataFrame

    Returns:
        dict: 包含三个渠道高推荐项目的字典，结构为 {'weain': [], 'military': [], 'nudt': []}
    """
    result = {'weain': [], 'military': [], 'nudt': []}

    # 全军武器装备采购信息网
    if len(df_weain) > 0:
        high = df_weain[df_weain['推荐等级'] == '高']
        for _, row in high.iterrows():
            result['weain'].append({
                'title': row['项目名称'][:50],
                'type': row['公告类型'],
                'deadline': row.get('截止日期', '')
            })

    # 军队采购网
    if len(df_military) > 0:
        high = df_military[df_military['推荐等级'] == '高']
        for _, row in high.iterrows():
            result['military'].append({
                'title': row['项目名称'][:50],
                'type': row['采购方式'],
                'region': row.get('地区', '')
            })

    # 国防科大采购信息网
    if len(df_nudt) > 0:
        high = df_nudt[df_nudt['推荐等级'] == '高']
        for _, row in high.iterrows():
            result['nudt'].append({
                'title': row['项目名称'][:50],
                'type': row['公告类型']
            })

    return result


def send_email(date_str, df_weain, df_military, df_nudt, dates_info, to_override=None, cc_override=None):
    """
    发送商机报告邮件。

    Args:
        date_str: 报告日期字符串，格式 YYYY-MM-DD
        df_weain: 全军武器装备采购信息网 DataFrame
        df_military: 军队采购网 DataFrame
        df_nudt: 国防科大采购信息网 DataFrame
        dates_info: 各渠道更新日期信息字典
        to_override: 覆盖默认收件人，用于测试发送
        cc_override: 覆盖默认抄送人
    """
    env_config = get_email_config()
    recipient_name = env_config['recipient_name']
    sender_name = env_config['sender_name']
    subject_prefix = env_config['subject_prefix']
    body_intro = env_config['body_intro']

    # 获取高推荐项目
    high_items = get_high_recommend_items(df_weain, df_military, df_nudt)

    # 构建邮件正文
    body = f"""{recipient_name}，{body_intro}

汇总如下：

【全军武器装备采购信息网】{len(df_weain)}条（更新日期: {dates_info.get('weain', date_str)}）

高推荐项目：
"""

    for i, item in enumerate(high_items['weain'], 1):
        deadline = f" | 截止{item['deadline']}" if item.get('deadline') else ""
        body += f"{i}. {item['title']}... | {item['type']}{deadline}\n"

    body += f"""
【军队采购网】{len(df_military)}条（更新日期: {dates_info.get('military', date_str)}）

高推荐项目：
"""

    for i, item in enumerate(high_items['military'], 1):
        region = f" | {item['region']}" if item.get('region') else ""
        body += f"{i}. {item['title']}... | {item['type']}{region}\n"

    body += f"""
【国防科大采购信息网】{len(df_nudt)}条（更新日期: {dates_info.get('nudt', date_str)}）

高推荐项目：
"""

    for i, item in enumerate(high_items['nudt'], 1):
        body += f"{i}. {item['title']}... | {item['type']}\n"

    body += f"""
详情请见附件Excel。

{sender_name}"""

    # 获取Excel文件路径
    excel_path = f"/home/ubuntu/.openclaw/workspace/military-bidding/商机信息汇总_{date_str}.xlsx"

    # 确定收件人/抄送人
    env_config = get_email_config()
    if to_override:
        to_list = [to_override]
        cc_list = []
    else:
        to_list = env_config['to']
        cc_list = env_config['cc']

    # 构建并发送邮件
    mml_content = build_mml_message(date_str, body, excel_path, to_list, cc_list)

    try:
        send_email_via_himalaya(mml_content, to_list, cc_list)
        print("[SUCCESS] 邮件发送成功")
        return True
    except Exception as e:
        print(f"[ERROR] 邮件发送失败: {e}")
        return False


def build_mml_message(date_str, body, excel_path, to_list, cc_list):
    """
    构建 MML 格式邮件内容。

    Args:
        date_str: 报告日期
        body: 邮件正文
        excel_path: Excel 附件路径
        to_list: 收件人列表
        cc_list: 抄送人列表

    Returns:
        str: MML 格式邮件内容
    """
    env_config = get_email_config()
    from_addr = env_config['from']
    subject_prefix = env_config['subject_prefix']

    msg = f"""From: {from_addr}
To: {', '.join(to_list)}
Cc: {', '.join(cc_list)}
Subject: 【{subject_prefix}】{date_str}

<#multipart type=mixed>
<#part type=text/plain>
{body}
"""

    if excel_path and os.path.exists(excel_path):
        msg += f"<#part filename={excel_path} name={os.path.basename(excel_path)}><#/part>\n"

    msg += "<#/multipart>\n"
    return msg


def send_email_via_himalaya(mml_content, to_list, cc_list):
    """
    使用 himalaya CLI 发送邮件，失败时自动回退到 SMTP。

    Args:
        mml_content: MML 格式邮件内容
        to_list: 收件人列表
        cc_list: 抄送人列表

    Returns:
        bool: 发送成功返回 True
    """
    import subprocess
    import os

    himalaya_path = os.path.expanduser('~/.local/bin/himalaya')

    if not os.path.exists(himalaya_path):
        print(f"[WARN] himalaya 不存在 ({himalaya_path})，直接使用 SMTP")
        return send_email_via_smtp(mml_content, to_list, cc_list)

    result = subprocess.run(
        [himalaya_path, 'message', 'send'],
        input=mml_content,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"[INFO] 邮件已发送至: {', '.join(to_list)}, 抄送: {', '.join(cc_list)}")
        return True

    print(f"[WARN] himalaya 发送失败，回退到 SMTP")
    return send_email_via_smtp(mml_content, to_list, cc_list)


def send_email_via_smtp(mml_content, to_list, cc_list):
    """
    使用 SMTP 直接发送邮件（回退方案）。

    Args:
        mml_content: MML 格式邮件内容
        to_list: 收件人列表
        cc_list: 抄送人列表

    Returns:
        bool: 发送成功返回 True
    """
    import smtplib
    import re
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    from email.header import Header
    from email.utils import formatdate

    env_config = get_email_config()
    SMTP_HOST = env_config['smtp_host']
    SMTP_PORT = int(env_config['smtp_port'])
    SMTP_USER = env_config['smtp_user']
    SMTP_PASSWORD = env_config['smtp_password']

    # 解析 MML 内容
    lines = mml_content.split('\n')
    subject = ''
    body = ''
    in_body = False
    attachments = []
    for line in lines:
        if line.startswith('Subject:'):
            subject = line.replace('Subject:', '').strip()
        elif line.startswith('<#part filename='):
            match = re.search(r'filename=(\S+)', line)
            name_match = re.search(r'name=([^>/\s]+)', line)
            if match:
                filepath = match.group(1)
                filename = name_match.group(1) if name_match else os.path.basename(filepath)
                attachments.append({'path': filepath, 'name': filename})
        elif line.startswith('<#multipart') or line.startswith('<#part type='):
            in_body = True
        elif line == '<#/multipart>':
            break
        elif in_body and not line.startswith('<#'):
            body += line + '\n'

    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = ', '.join(to_list)
    msg['Cc'] = ', '.join(cc_list)
    msg['Subject'] = subject
    msg['Date'] = formatdate()

    msg.attach(MIMEText(body.strip(), 'plain', 'utf-8'))

    # 添加附件
    for att in attachments:
        att_path = att['path']
        att_name = att['name']
        if os.path.exists(att_path):
            with open(att_path, 'rb') as f:
                part = MIMEApplication(f.read(), _subtype='xlsx')
            filename_encoded = Header(att_name, 'utf-8').encode()
            part.add_header('Content-Disposition', 'attachment', filename=filename_encoded)
            msg.attach(part)
        else:
            print(f"[WARNING] 附件不存在: {att_path}")

    # 发送邮件
    smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
    smtp.login(SMTP_USER, SMTP_PASSWORD)
    smtp.send_message(msg)
    smtp.quit()

    print(f"[INFO] 邮件已发送（SMTP）至: {', '.join(to_list)}, 抄送: {', '.join(cc_list)}")
    return True


def send_bidding_report(date=None, keywords=None, auto_latest=False, to_override=None):
    """
    发送商机报告邮件。

    Args:
        date: 指定日期，格式 YYYY-MM-DD。默认为 None，配合 auto_latest 使用
        keywords: 关键词列表，用于筛选商机。默认为 None，使用配置中的默认关键词
        auto_latest: 是否自动获取各渠道最新日期。默认为 False（默认获取昨日数据）
        to_override: 覆盖默认收件人，用于测试发送。默认为 None

    Returns:
        tuple: (df_weain, df_military, df_nudt) 三个 DataFrame
    """
    from datetime import datetime, timedelta

    # 确定查询日期
    if not auto_latest and date is None:
        # 默认获取昨日数据（解决军队采购网白天更新的问题）
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        date = yesterday_date
        print(f"[INFO] 默认获取昨日商机: {date}")

    print(f"[INFO] 开始抓取商机信息 - 自动获取最新日期: {auto_latest}")

    # 抓取数据
    fetch_all_bidding = _import_fetcher()
    result = fetch_all_bidding(keywords=keywords, date=date, auto_latest=auto_latest)

    if len(result) == 4:
        df_weain, df_military, df_nudt, dates_info = result
    else:
        df_weain, df_military, df_nudt = result
        dates_info = {'weain': date, 'military': date, 'nudt': date}

    file_date = date if date else datetime.now().strftime('%Y-%m-%d')

    print(f"[INFO] 采集完成: 全军{len(df_weain)}条, 军队{len(df_military)}条, 国防科大{len(df_nudt)}条")

    # 发送邮件
    send_email(file_date, df_weain, df_military, df_nudt, dates_info, to_override=to_override)

    return df_weain, df_military, df_nudt


HELP_TEXT = """军工采购商机邮件发送工具

用法:
    milb-email [选项]

选项:
    --date DATE         日期，格式 YYYY-MM-DD
    --keywords WORDS   关键词，逗号分隔，如: 模型,仿真,AI
    --to ADDRESS       测试发送至指定收件人
    --today            发送今日报告（获取各渠道最新数据）
    --help             显示此帮助信息

示例:
    milb-email                           # 发送昨日报告（默认）
    milb-email --today                   # 发送今日报告
    milb-email --date 2026-03-23        # 发送指定日期报告
    milb-email --keywords "模型,仿真"    # 使用自定义关键词
    milb-email --to test@example.com    # 测试发送
"""


def main():
    """
    CLI 入口函数。

    支持的参数:
        --date DATE: 指定日期，格式 YYYY-MM-DD
        --keywords WORDS: 关键词，逗号分隔
        --to ADDRESS: 测试发送至指定收件人
        --today: 发送今日报告
        --help: 显示帮助信息
    """
    import argparse
    import fcntl
    from datetime import datetime, timedelta

    parser = argparse.ArgumentParser(
        description='军工采购商机邮件发送工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HELP_TEXT
    )
    parser.add_argument('--date', type=str, help='日期，格式 YYYY-MM-DD')
    parser.add_argument('--keywords', type=str, help='关键词，逗号分隔')
    parser.add_argument('--to', type=str, help='测试发送至指定收件人（覆盖配置）')
    parser.add_argument('--today', action='store_true',
                       help='发送今日报告（获取各渠道最新数据）')

    args = parser.parse_args()

    # --help 时显示帮助
    if '--help' in sys.argv:
        print(HELP_TEXT)
        sys.exit(0)

    # 确定日期和模式
    date = args.date
    auto_latest = args.today  # --today 表示获取各渠道最新数据

    # 锁文件防止并发执行
    LOCK_FILE = '/tmp/bidding_email.lock'

    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        print("[INFO] 已有任务在运行，跳过本次执行")
        sys.exit(0)

    # 解析关键词
    keywords = None
    if args.keywords:
        keywords = args.keywords.split(',')

    # 发送报告
    try:
        send_bidding_report(date=date, keywords=keywords, auto_latest=auto_latest, to_override=args.to)
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        try:
            os.remove(LOCK_FILE)
        except:
            pass


if __name__ == '__main__':
    main()
