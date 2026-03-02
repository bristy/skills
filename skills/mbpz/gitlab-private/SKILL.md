---
name: gitlab-private
description: 通过 OAuth 授权访问私有 GitLab 仓库，支持在群聊中使用
tags: [gitlab, oauth, api, private, code]
---

# GitLab Private

通过 OAuth 授权访问私有 GitLab 仓库，支持在群聊中使用。

## 功能

- **自动识别 OAuth code**：用户在群里发的 40-64 位 16 进制字符串会自动识别并换取 token
- 授权持久化：一次授权，持久生效
- 列出用户仓库
- 读取仓库文件
- 查看最后一次合并信息
- 搜索项目

## 群聊使用流程

### 1. 用户发 GitLab 仓库链接

机器人自动回复授权链接：

```
抱歉，GitLab 仓库位于内网，需要授权才能访问。

请按以下步骤授权：
1. 打开浏览器访问：
http://gitlab.dmall.com/oauth/authorize?client_id=xxx&redirect_uri=http://localhost/callback&response_type=code&scope=api

2. 授权后浏览器跳转到 http://localhost/callback?code=xxx

3. 把 code 发给我
```

### 2. 用户发授权链接

用户把浏览器跳转后的 **完整链接** 发给机器人（如：`http://localhost/callback?code=d2a1e9d2f440419a7378bb7fa95c3baded9859168b21ed0446a5f8f54b0fd10c`）

**机器人自动识别并处理**：
- 从链接中提取 code → 自动换取 token → 保存
- 支持完整链接或纯 code
- 无需手动运行任何命令

### 3. 后续使用

同一个人后续发仓库链接，**直接读取，无需再授权**。

## 命令行使用

```bash
# 自动处理 code 或 token（群里使用）
node index.js handle <code或token>

# 配置 OAuth 应用（首次设置）
node index.js config <Application ID> <Secret>

# 生成授权链接
node index.js auth <Application ID> <Secret>

# 列出仓库
node index.js list

# 搜索项目
node index.js project <关键词>

# 读取文件
node index.js read <项目ID> <文件路径>

# 查看最后一次合并
node index.js merge <项目ID> [分支名]
```

## 配置文件

- `config.json` - GitLab 访问 token
- `oauth-config.json` - OAuth 应用配置

## 自动识别逻辑

当用户发的消息符合以下条件时，自动识别为 OAuth code：
- 长度 40-64 位
- 仅包含 0-9, a-f, A-F（16 进制）
