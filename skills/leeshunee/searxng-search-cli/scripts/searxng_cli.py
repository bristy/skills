#!/usr/bin/env python3
"""
SearXNG CLI for OpenClaw
Usage: searxng-search <command> [options]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

# 配置
SEARXNG_DIR = Path.home() / "projects" / "searxng"
SEARXNG_PORT = os.environ.get("SEARXNG_PORT", "8888")
SEARXNG_HOST = os.environ.get("SEARXNG_HOST", "127.0.0.1")
SEARXNG_SECRET = os.environ.get("SEARXNG_SECRET", "")


def log(msg):
    print(f"[searxng] {msg}", file=sys.stderr)


def run(cmd, check=True, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if check and result.returncode != 0:
        log(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def is_installed():
    return SEARXNG_DIR.exists() and (SEARXNG_DIR / ".venv").exists()


def is_running():
    try:
        resp = urllib.request.urlopen(f"http://{SEARXNG_HOST}:{SEARXNG_PORT}/search?q=test&format=json", timeout=2)
        return resp.status == 200
    except:
        return False


def cmd_install(args):
    """一键安装 SearXNG"""
    log("开始安装 SearXNG...")
    
    # 1. 安装 uv
    if not subprocess.run("which uv", shell=True, capture_output=True).returncode == 0:
        log("安装 uv...")
        run('curl -LsSf https://astral.sh/uv/install.sh | sh')
        # 添加到 PATH
        uv_path = Path.home() / ".local" / "bin" / "uv"
        if uv_path.exists():
            os.environ["PATH"] = f"{uv_path.parent}:{os.environ['PATH']}"
    
    # 2. 克隆 SearXNG
    if not SEARXNG_DIR.exists():
        log("克隆 SearXNG...")
        SEARXNG_DIR.parent.mkdir(parents=True, exist_ok=True)
        run(f"git clone --depth 1 https://github.com/searxng/searxng.git {SEARXNG_DIR}")
    
    # 3. 创建虚拟环境
    venv_dir = SEARXNG_DIR / ".venv"
    if not venv_dir.exists():
        log("创建虚拟环境...")
        run(f"cd {SEARXNG_DIR} && uv venv .venv")
    
    # 4. 安装依赖
    log("安装依赖...")
    pip = SEARXNG_DIR / ".venv" / "bin" / "pip"
    run(f"{pip} install -r {SEARXNG_DIR / 'requirements.txt'}")
    
    # 5. 启用 JSON API
    settings_file = SEARXNG_DIR / "searx" / "settings.yml"
    if settings_file.exists():
        with open(settings_file) as f:
            content = f.read()
        if "json" not in content.split("formats:")[1].split(":")[0] if "formats:" in content else False:
            # 简单检查，如需要可改进
            pass
    
    # 6. 生成 secret
    if not SEARXNG_SECRET:
        secret = subprocess.run(
            f"python3 -c 'import secrets; print(secrets.token_hex(32))'",
            shell=True, capture_output=True, text=True
        ).stdout.strip()
        os.environ["SEARXNG_SECRET"] = secret
        log(f"生成的密钥: {secret[:16]}...")
    
    # 7. 启动服务
    cmd_start(args)
    
    log("安装完成！")


def cmd_start(args):
    """启动服务"""
    if is_running():
        log("服务已在运行")
        return
    
    log("启动服务...")
    env = os.environ.copy()
    env["SEARXNG_SECRET"] = SEARXNG_SECRET or env.get("SEARXNG_SECRET", "devsecret")
    
    # 后台启动
    cmd = f'cd {SEARXNG_DIR} && SEARXNG_SECRET={env["SEARXNG_SECRET"]} {SEARXNG_DIR}/.venv/bin/python -m searx.webapp --host {SEARXNG_HOST} --port {SEARXNG_PORT}'
    subprocess.Popen(cmd, shell=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 等待启动
    for _ in range(10):
        if is_running():
            log(f"服务已启动: http://{SEARXNG_HOST}:{SEARXNG_PORT}")
            return
        import time
        time.sleep(1)
    
    log("启动失败")


def cmd_stop(args):
    """停止服务"""
    log("停止服务...")
    run("pkill -f 'searx.webapp'", check=False)
    log("服务已停止")


def cmd_restart(args):
    """重启服务"""
    cmd_stop(args)
    cmd_start(args)


def cmd_status(args):
    """查看状态"""
    if is_running():
        print(f"✓ 服务运行中: http://{SEARXNG_HOST}:{SEARXNG_PORT}")
    else:
        print("✗ 服务未运行")


def cmd_enable(args):
    """开机自启"""
    # 写入 systemd 服务文件
    service_file = Path.home() / ".config" / "systemd" / "user" / "searxng.service"
    service_file.parent.mkdir(parents=True, exist_ok=True)
    
    secret = SEARXNG_SECRET or "devsecret"
    content = f"""[Unit]
Description=SearXNG Search Engine

[Service]
Type=simple
WorkingDirectory={SEARXNG_DIR}
ExecStart={SEARXNG_DIR}/.venv/bin/python -m searx.webapp --host {SEARXNG_HOST} --port {SEARXNG_PORT}
Environment=SEARXNG_SECRET={secret}
Restart=on-failure

[Install]
WantedBy=default.target
"""
    with open(service_file, "w") as f:
        f.write(content)
    
    run("systemctl --user daemon-reload", check=False)
    run("systemctl --user enable searxng", check=False)
    log("已启用开机自启")


def cmd_disable(args):
    """取消开机自启"""
    run("systemctl --user disable searxng", check=False)
    log("已取消开机自启")


def cmd_search(args):
    """搜索"""
    if not is_running():
        log("服务未运行，请先执行: searxng-search start")
        sys.exit(1)
    
    query = args.query
    params = {
        "q": query,
        "format": "json"
    }
    
    if args.engine:
        params["engines"] = args.engine
    if args.lang:
        params["lang"] = args.lang
    if args.page:
        params["pageno"] = args.page
    if args.time_range:
        params["time_range"] = args.time_range
    if args.safe_search:
        params["safesearch"] = args.safe_search
    
    # 构建 URL
    from urllib.parse import urlencode
    url = f"http://{SEARXNG_HOST}:{SEARXNG_PORT}/search?{urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.load(resp)
        
        results = data.get("results", [])
        if not results:
            print("未找到结果")
            return
        
        for r in results[:args.limit]:
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")[:100]
            print(f"【{title}】")
            print(f"{url}")
            print(f"{content}...")
            print()
    except Exception as e:
        log(f"搜索失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="searxng-search")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # install
    subparsers.add_parser("install", help="一键安装 SearXNG")
    
    # start
    subparsers.add_parser("start", help="启动服务")
    
    # stop
    subparsers.add_parser("stop", help="停止服务")
    
    # restart
    subparsers.add_parser("restart", help="重启服务")
    
    # status
    subparsers.add_parser("status", help="查看服务状态")
    
    # enable
    subparsers.add_parser("enable", help="开机自启")
    
    # disable
    subparsers.add_parser("disable", help="取消开机自启")
    
    # search
    search_parser = subparsers.add_parser("search", help="搜索")
    search_parser.add_argument("query", help="搜索关键词")
    search_parser.add_argument("-e", "--engine", help="指定引擎")
    search_parser.add_argument("-l", "--lang", help="语言")
    search_parser.add_argument("-p", "--page", type=int, help="页码")
    search_parser.add_argument("-t", "--time-range", help="时间范围")
    search_parser.add_argument("-s", "--safe-search", help="安全搜索")
    search_parser.add_argument("--limit", type=int, default=5, help="结果数量")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 根据命令调用对应函数
    {
        "install": cmd_install,
        "start": cmd_start,
        "stop": cmd_stop,
        "restart": cmd_restart,
        "status": cmd_status,
        "enable": cmd_enable,
        "disable": cmd_disable,
        "search": cmd_search,
    }[args.command](args)


if __name__ == "__main__":
    main()
