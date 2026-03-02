# GitLab Private 更新日志

## v0.4.0 (2026-03-02)

### 新功能
- **支持完整授权链接**：用户发 `http://localhost/callback?code=xxx` 完整链接也能自动识别
- 自动从链接中提取 code

### 修复
- 修复变量重复声明 bug

---

## v0.3.0 (2026-03-02)

### 新功能
- **自动识别 OAuth code**：用户在群里发的 40-64 位 16 进制字符串会自动识别并换取 token
- 新增 `handle` 命令：自动处理用户发的 code 或 token
- 新增 `config` 命令：保存 OAuth 应用配置
- 支持多人授权：群里不同人授权后各自的 token 都会保存

### 配置
- 新增 `oauth-config.json`：保存 OAuth 应用 client_id 和 client_secret

---

## v0.2.0 (2026-03-02)

### 新功能
- **授权持久化**：用户首次授权后，token 自动保存到 config.json，后续无需再授权

### 修复
- 修复命令行参数解析错误
- 优化 README.md 文档

---

## v0.1.0 (2026-03-02)

### 新功能
- 支持 GitLab OAuth 授权认证
- 支持列出用户仓库 (`list`)
- 支持搜索项目 (`project`)
- 支持读取仓库文件 (`read`)
- 支持查看最后一次合并 (`merge`)

### 初始版本
- 基础 GitLab API 封装
- 支持私有仓库访问

---

## 技术说明

### 授权流程
1. 用户访问 OAuth 授权链接
2. 用户把授权 code 发给机器人
3. 机器人用 code 换取 access_token
4. **token 保存到 config.json**，后续自动读取

### 配置文件
```json
{
  "gitlab_url": "http://gitlab.dmall.com",
  "access_token": "your_token_here"
}
```

### 环境变量
- `GITLAB_URL`: GitLab 地址
- `GITLAB_TOKEN`: Access Token
