---
name: atomgit
description: 基于 GitCode OpenAPI v5 的 OpenClaw 技能，提供仓库、用户、Issue、Pull Request 等操作的 MCP 工具封装。支持中英文文档。
---

# atomgit - GitCode/AtomGit API 技能

基于 GitCode OpenAPI v5 的 OpenClaw 技能，提供仓库、用户、Issue、Pull Request 等操作的 MCP 工具封装。

> 📖 **完整文档**: [README.md](./README.md) (包含中英文版本)

## 功能特性

- 👤 **用户管理**: 获取当前用户信息、查询用户详情
- 📦 **仓库管理**: 列出、创建、更新、删除仓库
- 🐛 **Issue 管理**: 创建、查询、更新 Issue
- 🔀 **Pull Request 管理**: 创建、审查、合并 PR
- 📁 **文件操作**: 读取、创建、更新仓库文件
- 🌿 **分支管理**: 列出、创建、删除分支
- 🍴 **Fork 管理**: Fork 仓库、查看 Fork 列表

## 快速开始

### 1. 获取 GitCode Token

访问 https://gitcode.com/setting/token-classic 生成个人访问令牌，需要以下权限：
- `api` - API 访问
- `read_user` - 读取用户信息
- `read_repository` - 读取仓库
- `write_repository` - 写入仓库（创建、更新、删除）
- `issues` - 管理 Issue
- `pull_requests` - 管理 PR

### 2. 测试 MCP 服务器

```bash
cd /root/.openclaw/extensions/wecom-openclaw-plugin/skills/atomgit

# 测试获取当前用户
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"getCurrentUser","arguments":{}}}' | ATOMGIT_TOKEN=your-token timeout 3 node mcp-server.js

# 测试列出仓库
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listRepos","arguments":{"perPage":5}}}' | ATOMGIT_TOKEN=your-token timeout 3 node mcp-server.js
```

### 3. 配置 Gateway

在 Gateway 配置中添加 MCP 配置：

```json
{
  "mcpConfig": {
    "atomgit": {
      "command": "node",
      "args": ["/root/.openclaw/extensions/wecom-openclaw-plugin/skills/atomgit/mcp-server.js"],
      "env": {
        "ATOMGIT_TOKEN": "your-personal-access-token"
      }
    }
  }
}
```

或使用环境变量：

```bash
export ATOMGIT_TOKEN="your-token-here"
```

## 工具列表

### 用户工具

| 工具 | 描述 | 参数 |
|------|------|------|
| `getCurrentUser` | 获取当前认证用户信息 | 无 |
| `getUser` | 获取指定用户详情 | `username` (必填) |

### 仓库工具

| 工具 | 描述 | 参数 |
|------|------|------|
| `listRepos` | 列出仓库 | `username`, `type`, `sort`, `direction`, `page`, `perPage` |
| `getRepo` | 获取仓库详情 | `owner`, `repo` (必填) |
| `createRepo` | 创建仓库 | `name` (必填), `description`, `private`, `autoInit`, `license`, `readme` |
| `updateRepo` | 更新仓库 | `owner`, `repo`, `name`, `description`, `private`, `hasIssues`, `hasWiki`, `defaultBranch` |
| `deleteRepo` | 删除仓库 | `owner`, `repo` (必填) |

### Issue 工具

| 工具 | 描述 | 参数 |
|------|------|------|
| `listIssues` | 列出 Issue | `owner`, `repo`, `state`, `labels`, `sort`, `direction`, `page`, `perPage` |
| `getIssue` | 获取 Issue 详情 | `owner`, `repo`, `number` (必填) |
| `createIssue` | 创建 Issue | `owner`, `repo`, `title` (必填), `body`, `assignee`, `labels` |
| `updateIssue` | 更新 Issue | `owner`, `repo`, `number`, `title`, `body`, `state`, `assignee`, `labels` |

### Pull Request 工具

| 工具 | 描述 | 参数 |
|------|------|------|
| `listPullRequests` | 列出 PR | `owner`, `repo`, `state`, `sort`, `direction`, `page`, `perPage` |
| `getPullRequest` | 获取 PR 详情 | `owner`, `repo`, `number` (必填) |
| `createPullRequest` | 创建 PR | `owner`, `repo`, `title` (必填), `body`, `head` (必填), `base` (必填) |
| `mergePullRequest` | 合并 PR | `owner`, `repo`, `number`, `commitTitle`, `commitMessage`, `mergeMethod` |

### 文件与分支工具

| 工具 | 描述 | 参数 |
|------|------|------|
| `getRepoFile` | 获取文件内容 | `owner`, `repo`, `path` (必填), `ref` |
| `createFile` | 创建/更新文件 | `owner`, `repo`, `path`, `content` (必填), `message` (必填), `branch`, `sha` |
| `listBranches` | 列出分支 | `owner`, `repo`, `page`, `perPage` |
| `createBranch` | 创建分支 | `owner`, `repo`, `branch` (必填), `ref` |
| `deleteBranch` | 删除分支 | `owner`, `repo`, `branch` (必填) |

### Fork 工具

| 工具 | 描述 | 参数 |
|------|------|------|
| `forkRepo` | Fork 仓库 | `owner`, `repo`, `organization` (可选) |
| `listForks` | 列出 Forks | `owner`, `repo`, `sort`, `page`, `perPage` |

## 使用示例

### 获取当前用户

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"getCurrentUser","arguments":{}}}' | ATOMGIT_TOKEN=your-token node mcp-server.js
```

### 创建仓库

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createRepo","arguments":{"name":"my-project","description":"My project","private":false,"autoInit":true}}}' | ATOMGIT_TOKEN=your-token node mcp-server.js
```

### 创建 Issue

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createIssue","arguments":{"owner":"weidongkl","repo":"my-project","title":"Bug report","body":"Description","labels":"bug"}}}' | ATOMGIT_TOKEN=your-token node mcp-server.js
```

### 创建 Pull Request

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createPullRequest","arguments":{"owner":"weidongkl","repo":"my-project","title":"Fix bug","body":"PR description","head":"fix-bug","base":"main"}}}' | ATOMGIT_TOKEN=your-token node mcp-server.js
```

### 更新文件

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"createFile","arguments":{"owner":"weidongkl","repo":"my-project","path":"README.md","content":"# Project","message":"Update README","branch":"main"}}}' | ATOMGIT_TOKEN=your-token node mcp-server.js
```

## 故障排查

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| 401 Unauthorized | Token 无效或过期 | 检查 token 配置，重新生成 |
| 404 Not Found | 资源不存在或无权限 | 确认 owner/repo 名称，检查权限 |
| 403 Forbidden | 权限不足 | 检查 token 权限，写操作需要 `write_repository` |
| 429 Too Many Requests | 超过速率限制 | 等待后重试，限制：50 次/分钟 |

## API 参考

- GitCode API 文档：https://docs.gitcode.com/docs/apis/
- 基础 URL：https://api.gitcode.com/api/v5
- 个人令牌管理：https://gitcode.com/setting/token-classic

## 更新日志

### v1.0.0

- ✅ 初始发布
- ✅ 修复 API 路径拼接 bug
- ✅ 支持用户管理
- ✅ 支持仓库管理
- ✅ 支持 Issue 管理
- ✅ 支持 Pull Request 管理
- ✅ 支持文件操作
- ✅ 支持分支管理
- ✅ 支持 Fork 操作
- ✅ 中英文文档

## 许可证

MIT License
