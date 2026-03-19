#!/usr/bin/env python3
"""
GitHub Hosts Optimizer - 智能版
功能：
1. 检测当前 GitHub CDN IP 是否可用（速度测试）
2. 当所有已知 IP 都失效时，通过 DNS 自动发现新 IP
3. 自动更新 /etc/hosts
4. 自动提交到 Git 并发布到 ClawHub
5. 支持 --auto 模式（cron 任务调用）
"""

import argparse
import subprocess
import time
import socket
import concurrent.futures
import json
import re
import shutil
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

LOG_FILE = Path("/tmp/github-hosts-optimizer.log")
SKILL_DIR = Path("/root/.openclaw/workspace/skills/github-hosts-optimizer")

# GitHub CDN 域名列表
GITHUB_HOSTS = [
    "github.com",
    "assets-cdn.github.com",
    "github.global.ssl.fastly.net",
    "github.works",
    "objects.githubusercontent.com",
    "upload.githubusercontent.com",
    "codeload.github.com",
]

# 已知可用的 IP 池（按优先级排序）
KNOWN_IPS = [
    # github.com
    ("140.82.112.0/22", "github.com"),
    ("140.82.113.0/22", "github.com"),
    ("140.82.114.0/22", "github.com"),
    ("140.82.121.0/22", "github.com"),
    # assets-cdn
    ("185.199.108.0/22", "assets-cdn.github.com"),
    ("185.199.109.0/22", "assets-cdn.github.com"),
    ("185.199.110.0/22", "assets-cdn.github.com"),
    ("185.199.111.0/22", "assets-cdn.github.com"),
    # fastly
    ("199.232.69.0/24", "github.global.ssl.fastly.net"),
    # Backup IPs
    ("140.82.113.3", "github.com"),
    ("140.82.121.4", "github.com"),
    ("185.199.108.153", "assets-cdn.github.com"),
    ("185.199.109.153", "assets-cdn.github.com"),
    ("185.199.110.153", "assets-cdn.github.com"),
    ("199.232.69.194", "github.global.ssl.fastly.net"),
]

HOSTS_HEADER = "# === GitHub Hosts Optimizer - Auto Updated ==="
HOSTS_FOOTER = "# === GitHub Hosts Optimizer End ==="


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def backup_hosts() -> Optional[Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f"/etc/hosts.backup_{timestamp}")
    try:
        shutil.copy2("/etc/hosts", backup_path)
        log(f"备份已保存: {backup_path}")
        return backup_path
    except Exception as e:
        log(f"备份失败: {e}")
        return None


def cidr_to_ips(cidr: str) -> list[str]:
    """将 CIDR 转换为 IP 列表（最多256个）"""
    if "/" not in cidr:
        return [cidr]
    parts = cidr.split("/")
    base_parts = parts[0].rsplit(".", 1)
    if len(base_parts) != 2:
        return [cidr]
    base = base_parts[0]
    prefix = int(parts[1])
    host_bits = 32 - prefix
    count = min(2 ** host_bits, 256)
    last_octet = int(base_parts[1])
    return [f"{base}.{last_octet + i}" for i in range(count)]


def expand_known_ips() -> dict[str, list[str]]:
    """展开已知 IP 池，按域名分组"""
    expanded: dict[str, list[str]] = {}
    for item in KNOWN_IPS:
        if isinstance(item, tuple):
            ip_or_cidr, hostname = item[0], item[1]
        else:
            ip_or_cidr, hostname = item, "github.com"
        ips = cidr_to_ips(ip_or_cidr)
        if hostname not in expanded:
            expanded[hostname] = []
        expanded[hostname].extend(ips)
    return expanded


def speed_test(ip: str, hostname: str, timeout: int = 5) -> float:
    """TCP 连接测速（毫秒），最可靠的 hosts 测速方式"""
    try:
        start = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, 443))
        s.close()
        return (time.time() - start) * 1000
    except Exception:
        return 9999


def check_connectivity() -> dict[str, bool]:
    """检查 GitHub 基础连通性，返回 {域名: 是否可达}"""
    log("=== 连通性检查 ===")
    results: dict[str, bool] = {}
    for host in GITHUB_HOSTS[:3]:
        try:
            r = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "--connect-timeout", "5", "--max-time", "10",
                 f"https://{host}"],
                capture_output=True, text=True, timeout=12
            )
            ok = r.stdout.strip() == "200"
            log(f"{'✅' if ok else '❌'} {host}: {r.stdout.strip()}")
            results[host] = ok
        except Exception as e:
            log(f"❌ {host}: {e}")
            results[host] = False
    return results


def probe_best_ips(ips_to_test: list[str], hostname: str, max_workers: int = 20) -> list[tuple[str, float]]:
    """并发测速，返回 [(IP, 延迟ms)]，按延迟排序"""
    results: list[tuple[str, float]] = []
    
    def single_test(ip: str) -> tuple[str, float]:
        latency = speed_test(ip, hostname)
        return (ip, latency)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(single_test, ip): ip for ip in ips_to_test}
        for future in concurrent.futures.as_completed(futures, timeout=30):
            try:
                result = future.result()
                results.append(result)
            except Exception:
                pass
    
    results.sort(key=lambda x: x[1])
    return results


# 已知公共 DNS 服务器 IP（被劫持时返回自己 IP）
PUBLIC_DNS_IPS = {"223.5.5.5", "119.29.29.29", "180.76.76.76", "8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "9.9.9.9"}


def dns_discovery() -> dict[str, list[str]]:
    """通过 DNS 发现 GitHub CDN 当前解析的 IP"""
    log("=== DNS 发现模式 ===")
    discovered: dict[str, list[str]] = {}
    
    # 使用多个 DNS 服务器
    dns_servers = ["8.8.8.8", "1.1.1.1", "9.9.9.9", "223.5.5.5", "119.29.29.29"]
    
    for hostname in GITHUB_HOSTS:
        for dns in dns_servers:
            try:
                cmd = ["nslookup", hostname, dns]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    cmd = ["dig", "+short", hostname, f"@{dns}"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                output = result.stdout
                # 提取 IP
                ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
                ips = list(set(ip for ip in ips if not ip.startswith("127.") and ip not in PUBLIC_DNS_IPS))
                if ips:
                    discovered[hostname] = ips
                    log(f"DNS[{dns}] {hostname} -> {ips[0]}")
                    break  # 找到就不试下一个 DNS
            except Exception:
                pass
    
    if not discovered:
        log("DNS 发现未找到任何 IP")
    
    return discovered


def get_all_test_ips() -> tuple[list[str], dict[str, list[str]]]:
    """获取所有需要测速的 IP 列表 + 按域名分组"""
    expanded = expand_known_ips()
    all_ips: list[str] = []
    by_hostname: dict[str, list[str]] = {}
    
    for hostname, ips in expanded.items():
        by_hostname[hostname] = ips
        all_ips.extend(ips[:32])  # 每个域名最多测32个
    
    return list(set(all_ips)), by_hostname


def update_hosts(entries: dict[str, str]):
    """将 hosts 条目写入 /etc/hosts"""
    backup_hosts()
    
    hosts_content = Path("/etc/hosts").read_text()
    
    # 移除旧条目
    start = hosts_content.find(HOSTS_HEADER)
    end = hosts_content.find(HOSTS_FOOTER)
    if start != -1 and end != -1:
        hosts_content = hosts_content[:start].rstrip() + "\n"
    elif start != -1:
        hosts_content = hosts_content[:start].rstrip() + "\n"
    
    # 追加新条目
    block = [HOSTS_HEADER]
    block.append(f"# 更新于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for hostname, ip in entries.items():
        block.append(f"{ip}  {hostname}")
    
    block.append(HOSTS_FOOTER + "\n")
    
    new_content = hosts_content + "\n".join(block)
    Path("/etc/hosts").write_text(new_content)
    log(f"hosts 已更新，共 {len(entries)} 条")


def smart_update() -> bool:
    """智能更新主流程"""
    log("=== 智能更新开始 ===")
    
    # Step 1: 连通性检查
    connectivity = check_connectivity()
    github_ok = connectivity.get("github.com", False)
    
    # Step 2: 如果 GitHub 连通正常，检查是否需要更新
    if github_ok:
        log("github.com 当前可达，检查最优 IP...")
        all_ips, by_hostname = get_all_test_ips()
        best = probe_best_ips(all_ips[:32], "github.com")
        
        if best and best[0][1] < 3000:  # 延迟 < 3s，认为可用
            log(f"当前最优 IP: {best[0][0]} ({best[0][1]:.0f}ms)，无需更新")
            return True
        
        log("当前 IP 较慢，尝试测速找更优 IP...")
    else:
        log("github.com 不可达，触发 DNS 发现模式")
    
    # Step 3: DNS 发现新 IP
    discovered = dns_discovery()
    
    # Step 4: 对发现的 IP 测速
    final_entries: dict[str, str] = {}
    
    for hostname in GITHUB_HOSTS:
        if hostname in discovered:
            ips = discovered[hostname]
            log(f"测速 {hostname}: {ips[:3]}")
            best = probe_best_ips(ips, hostname, max_workers=10)
            if best and best[0][1] < 8000:
                final_entries[hostname] = best[0][0]
                log(f"  ✅ {hostname} -> {best[0][0]} ({best[0][1]:.0f}ms)")
            else:
                # DNS IP 也不行，用已知 IP
                log(f"  ❌ DNS IP 全部超时，使用备用 IP")
                _, bh = get_all_test_ips()
                if hostname in bh:
                    best_known = probe_best_ips(bh[hostname][:8], hostname, max_workers=8)
                    if best_known and best_known[0][1] < 10000:
                        final_entries[hostname] = best_known[0][0]
                    else:
                        final_entries[hostname] = bh[hostname][0]
        else:
            # 未知主机，用备用 IP
            _, bh = get_all_test_ips()
            if hostname in bh:
                best_known = probe_best_ips(bh[hostname][:8], hostname, max_workers=8)
                if best_known and best_known[0][1] < 10000:
                    final_entries[hostname] = best_known[0][0]
                else:
                    final_entries[hostname] = bh[hostname][0]
    
    # Step 5: 更新 hosts
    update_hosts(final_entries)
    
    # Step 6: 验证更新结果
    log("=== 更新后验证 ===")
    check_connectivity()
    
    return True


def git_commit_and_push(reason: str):
    """提交更改到 Git"""
    try:
        log("=== Git 提交 ===")
        
        # Stage all files in skill dir
        skill_dir = str(SKILL_DIR)
        
        # Stage only the skill directory files (not workspace-wide changes)
        subprocess.run(["git", "-C", skill_dir, "add", "."], check=True)
        
        # Check if anything changed in skill dir
        status = subprocess.run(
            ["git", "-C", skill_dir, "status", "--porcelain"],
            capture_output=True, text=True
        )
        if not status.stdout.strip():
            log("无文件变更，跳过提交")
            return False
        
        # Commit
        msg = f"auto: {reason} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        subprocess.run(
            ["git", "-C", skill_dir, "commit", "-m", msg],
            capture_output=True, text=True, check=True
        )
        log(f"提交成功: {msg}")
        
        # Push
        result = subprocess.run(
            ["git", "-C", skill_dir, "push", "origin", "main"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            log("Git push 成功")
            return True
        else:
            log(f"Git push 失败: {result.stderr[:100]}")
            return False
    except Exception as e:
        log(f"Git 操作失败: {e}")
        return False


def get_version() -> str:
    """获取并递增版本号（使用 VERSION 文件）"""
    ver_file = SKILL_DIR / "VERSION"
    if ver_file.exists():
        try:
            version = ver_file.read_text().strip()
            parts = version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            new_ver = ".".join(parts)
        except Exception:
            new_ver = "1.0.0"
    else:
        new_ver = "1.0.0"
    ver_file.write_text(new_ver)
    return new_ver


def clawhub_publish():
    """发布到 ClawHub"""
    try:
        ver = get_version()
        log(f"=== ClawHub 发布 (v{ver}) ===")
        changelog = f"自动更新 GitHub CDN IPs ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        result = subprocess.run(
            ["npx", "-y", "clawhub", "publish",
             "skills/github-hosts-optimizer",
             "--slug", "github-hosts-optimizer-cn",
             "--version", ver,
             "--changelog", changelog,
             "--tags", "github,hosts,cn,dns,optimization"],
            cwd="/root/.openclaw/workspace",
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            log(f"ClawHub 发布成功 (v{ver})")
            return True
        else:
            err = result.stderr + result.stdout
            if "already exists" in err.lower():
                ver = get_version()
                log(f"版本号冲突，重试 v{ver}")
                result2 = subprocess.run(
                    ["npx", "-y", "clawhub", "publish",
                     "skills/github-hosts-optimizer",
                     "--slug", "github-hosts-optimizer-cn",
                     "--version", ver,
                     "--changelog", changelog,
                     "--tags", "github,hosts,cn,dns,optimization"],
                    cwd="/root/.openclaw/workspace",
                    capture_output=True, text=True, timeout=60
                )
                if result2.returncode == 0:
                    log(f"ClawHub 发布成功 (v{ver})")
                    return True
            log(f"ClawHub 发布失败: {err[:200]}")
            return False
    except Exception as e:
        log(f"ClawHub 发布异常: {e}")
        return False


def auto_mode():
    """全自动模式：检测 → DNS发现 → 更新 → ClawHub发布"""
    log("=== AUTO 模式启动 ===")
    
    connectivity = check_connectivity()
    github_ok = connectivity.get("github.com", False)
    
    if github_ok:
        # 快速检查：直接测 github.com 的已知最优 IP
        all_ips, _ = get_all_test_ips()
        best = probe_best_ips(all_ips[:16], "github.com")
        
        if best and best[0][1] < 5000:
            log(f"github.com 状态良好 ({best[0][0]}, {best[0][1]:.0f}ms)，无需操作")
            return "SKIP"
    
    # 需要更新
    smart_update()
    
    # Git 提交（跳过，因 skill 是 workspace git worktree，频繁 commit 会冲突）
    # 如需记录变更，可在 workspace 层面手动 commit
    
    # ClawHub 发布
    clawhub_publish()
    
    return "DONE"


def main():
    parser = argparse.ArgumentParser(description="GitHub Hosts Optimizer")
    parser.add_argument("--check", action="store_true", help="仅检查连通性")
    parser.add_argument("--static", action="store_true", help="静态更新（直接写入）")
    parser.add_argument("--auto", action="store_true", help="全自动模式（检测+更新+发布）")
    parser.add_argument("--skip-publish", action="store_true", help="跳过 ClawHub 发布")
    args = parser.parse_args()
    
    if args.check:
        check_connectivity()
    elif args.static:
        backup_hosts()
        all_ips, by_hostname = get_all_test_ips()
        entries = {}
        for hostname in GITHUB_HOSTS:
            if hostname in by_hostname:
                entries[hostname] = by_hostname[hostname][0]
        update_hosts(entries)
    elif args.auto:
        result = auto_mode()
        log(f"=== AUTO 模式完成: {result} ===")
    else:
        # 默认：智能更新
        smart_update()


if __name__ == "__main__":
    main()
