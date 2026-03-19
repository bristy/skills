#!/usr/bin/env python3
"""GitHub Hosts Optimizer - 回滚脚本"""
import sys
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path("/etc")

def find_latest_backup():
    backups = sorted(BACKUP_DIR.glob("hosts.backup_*"), reverse=True)
    if backups:
        return backups[0]
    return None

def rollback():
    backup = find_latest_backup()
    if not backup:
        print("❌ 未找到备份文件")
        sys.exit(1)
    
    print(f"回滚到: {backup}")
    content = backup.read_text()
    Path("/etc/hosts").write_text(content)
    print(f"✅ /etc/hosts 已回滚")
    print(f"   备份仍保留在: {backup}")

if __name__ == "__main__":
    rollback()
