---
name: jun-invest-option-master-installer
description: "Installer skill: via chat, install/upgrade & register the jun-invest-option-master isolated agent (no manual steps)."
---

# jun-invest-option-master-installer

这个 skill 负责把 **agent：`jun-invest-option-master`** 一键安装/升级到可运行状态（不包含 channel/bot 绑定）。

## 你只需要对我说一句
- **安装/升级 jun-invest-option-master（不绑定channel）**

我会按固定步骤完成：
1) 更新本 installer skill 到最新
2) 同步资产到独立 workspace：`/Users/lijunsheng/.openclaw/workspace-jun-invest-option-master`
3) 注册 isolated agent：`openclaw agents add jun-invest-option-master --non-interactive --workspace ...`
4) 需要时重启 gateway

## 资产内容
- prompts/config/templates（投研团队）
- `invest_agent/` 可运行代码（组装审批包、校验契约、Futu OpenAPI 适配器、fallback 数据源等）

## （可选）命令行一键
```bash
bash scripts/auto-install.sh
```
