---
name: github-hosts-optimizer
description: 配置中国大陆服务器访问 GitHub 的 hosts 优化。自动检测 GitHub CDN IP 是否失效（速度测试），失效时通过 DNS 发现新 IP，自动更新 hosts 并发布到 ClawHub。解决 GitHub 限流/超时问题。支持：智能检测、自动 DNS 发现、备份 hosts、Git 自动提交、ClawHub 自动发布。当用户提到 GitHub 访问慢、GitHub 超时、GitHub 连接失败、GitHub CDN 优化、/etc/hosts GitHub 时触发。
---

# GitHub Hosts Optimizer

自动优化中国大陆服务器访问 GitHub 的 DNS 解析，破解限流/超时。

## 一键优化

```bash
sudo python3 /root/.openclaw/workspace/skills/github-hosts-optimizer/scripts/update_hosts.py
```

## 工作原理

1. 从多个可信源获取 GitHub CDN 当前最优 IP（DNS 探测 + 测速）
2. 备份当前 hosts 文件
3. 追加/更新 GitHub 相关条目到 `/etc/hosts`
4. 验证连通性

## IP 来源

- GitHub 官方公告 IP
- CDNNS / IPAddress.com 等 DNS 探测服务
- Cloudflare / Fastly 官方 IP 段

## 脚本使用

```bash
# 完整更新（测速选最优）
python3 scripts/update_hosts.py

# 仅添加静态条目（不测速）
python3 scripts/update_hosts.py --static-only

# 回滚到上次备份
python3 scripts/rollback.py

# 检查当前连通性
python3 scripts/check_connectivity.py
```

## 自动更新 Cron

默认每2小时自动运行一次，确保持续有效：

```
cron add github-hosts-optimizer
```

## 已知最优 IP（静态备用）

```
140.82.113.3  github.com
185.199.108.153 assets-cdn.github.com
199.232.69.194 github.global.ssl.fastly.net
140.82.112.0/22 github.works
```

> 注意：IP 地址会变动，`--static-only` 模式可能失效，建议使用完整测速模式。

## 详细说明

- **测速原理**：对多个候选 IP 并发 curl 测速，选择延迟最低的
- **备份位置**：`/etc/hosts.backup.{timestamp}`
- **回滚命令**：`scripts/rollback.py`
- **日志**：`/tmp/github-hosts-optimizer.log`
