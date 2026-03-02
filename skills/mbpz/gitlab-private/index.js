const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const url = require('url');

// 读取配置
const configPath = path.join(__dirname, 'config.json');
let config = {
  gitlab_url: process.env.GITLAB_URL || 'http://gitlab.dmall.com',
  access_token: process.env.GITLAB_TOKEN || null
};

try {
  if (fs.existsSync(configPath)) {
    const fileConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    config = { ...config, ...fileConfig };
  }
} catch (e) {}

// API 请求封装
function request(method, endpoint, data = null) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new url.parse(config.gitlab_url + endpoint);
    const isHttps = config.gitlab_url.startsWith('https');
    const lib = isHttps ? https : http;

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (isHttps ? 443 : 80),
      path: parsedUrl.path,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.access_token}`
      }
    };

    const req = lib.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          resolve(body);
        }
      });
    });

    req.on('error', reject);

    if (data) {
      req.write(JSON.stringify(data));
    }
    req.end();
  });
}

// 命令处理
const command = process.argv[2];

async function main() {
  switch (command) {
    case 'auth':
      // 生成授权 URL
      const clientId = process.argv[3];
      const clientSecret = process.argv[4];
      const redirectUri = 'http://localhost/callback';
      const authUrl = `${config.gitlab_url}/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=api`;
      
      console.log('请访问以下链接进行授权:');
      console.log(authUrl);
      console.log('\n授权完成后，浏览器会跳转到 http://localhost/callback?code=xxx');
      console.log('请将 URL 中的 code 参数值复制下来，运行:');
      console.log(`node index.js token ${clientId} ${clientSecret} <code>`);
      break;

    case 'token':
      // 交换 token
      const cid = process.argv[3];
      const csecret = process.argv[4];
      const code = process.argv[5];
      
      if (!code) {
        console.log('用法: node index.js token <Application ID> <Secret> <code>');
        process.exit(1);
      }

      const tokenData = await new Promise((resolve, reject) => {
        const postData = new url.URLSearchParams({
          client_id: cid,
          client_secret: csecret,
          code: code,
          grant_type: 'authorization_code',
          redirect_uri: 'http://localhost/callback'
        }).toString();

        const parsedUrl = new url.parse(config.gitlab_url + '/oauth/token');
        const isHttps = config.gitlab_url.startsWith('https');
        const lib = isHttps ? https : http;

        const options = {
          hostname: parsedUrl.hostname,
          port: parsedUrl.port || (isHttps ? 443 : 80),
          path: parsedUrl.path,
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': Buffer.byteLength(postData)
          }
        };

        const req = lib.request(options, (res) => {
          let body = '';
          res.on('data', chunk => body += chunk);
          res.on('end', () => {
            try {
              resolve(JSON.parse(body));
            } catch (e) {
              reject(e);
            }
          });
        });

        req.on('error', reject);
        req.write(postData);
        req.end();
      });

      if (tokenData.access_token) {
        console.log('授权成功!');
        console.log('Access Token:', tokenData.access_token);
        
        // 保存到配置
        config.access_token = tokenData.access_token;
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        console.log('Token 已保存到 config.json');
      } else {
        console.log('授权失败:', tokenData);
      }
      break;

    case 'list':
      // 列出仓库
      if (!config.access_token) {
        console.log('请先进行授权: node index.js auth <Application ID> <Secret>');
        process.exit(1);
      }
      
      const response = await request('GET', '/api/v4/users/891/projects');
      const projects = Array.isArray(response) ? response : [];
      console.log('你的仓库:');
      projects.forEach(p => {
        console.log(`- ${p.name} (ID: ${p.id})`);
        console.log(`  ${p.web_url}`);
      });
      break;

    case 'read':
      // 读取文件
      if (!config.access_token) {
        console.log('请先进行授权: node index.js auth <Application ID> <Secret>');
        process.exit(1);
      }

      const projectId = process.argv[3];
      const filePath = process.argv[4];

      if (!projectId || !filePath) {
        console.log('用法: node index.js read <项目ID> <文件路径>');
        console.log('示例: node index.js read 11102 README.md');
        process.exit(1);
      }

      const fileData = await request('GET', `/api/v4/projects/${projectId}/repository/files/${encodeURIComponent(filePath)}?ref=master`);
      
      if (fileData.content) {
        const content = Buffer.from(fileData.content, 'base64').toString('utf8');
        console.log(content);
      } else {
        console.log('文件读取失败:', fileData.message || fileData);
      }
      break;

    case 'merge':
      // 查看最后一次合并
      if (!config.access_token) {
        console.log('请先进行授权: node index.js auth <Application ID> <Secret>');
        process.exit(1);
      }

      const mergeProjectId = process.argv[3];
      const branch = process.argv[4] || 'master';

      if (!mergeProjectId) {
        console.log('用法: node index.js merge <项目ID> [分支名]');
        console.log('示例: node index.js merge 10954 master');
        process.exit(1);
      }

      // 获取分支最近的提交
      const commits = await request('GET', `/api/v4/projects/${mergeProjectId}/repository/commits?ref_name=${branch}&per_page=10`);
      
      // 找到合并提交（parent_ids 有多个的）
      const mergeCommit = commits.find(c => c.parent_ids && c.parent_ids.length > 1);
      
      if (!mergeCommit) {
        console.log('未找到合并提交');
        console.log('最近提交:', commits.slice(0, 3).map(c => c.title).join('\n'));
        break;
      }

      // 获取合并提交的详情
      const mergeDiff = await request('GET', `/api/v4/projects/${mergeProjectId}/repository/commits/${mergeCommit.id}/diff`);
      
      console.log('='.repeat(50));
      console.log('最后一次合并信息');
      console.log('='.repeat(50));
      console.log(`合并时间: ${mergeCommit.created_at}`);
      console.log(`提交者: ${mergeCommit.author_name} (${mergeCommit.author_email})`);
      console.log(`提交信息: ${mergeCommit.title}`);
      console.log(`来源分支: (从 ${mergeCommit.parent_ids.length} 个 parent 判断为合并提交)`);
      console.log('');
      console.log('变更文件:');
      mergeDiff.forEach(f => {
        console.log(`  - ${f.new_path || f.old_path} (${f.new_file ? '新增' : f.deleted_file ? '删除' : '修改'})`);
      });
      break;

    case 'project':
      // 搜索项目
      if (!config.access_token) {
        console.log('请先进行授权');
        process.exit(1);
      }

      const searchKeyword = process.argv[3];
      if (!searchKeyword) {
        console.log('用法: node index.js project <关键词>');
        process.exit(1);
      }

      const searchResult = await request('GET', `/api/v4/projects?search=${searchKeyword}`);
      const searchProjects = Array.isArray(searchResult) ? searchResult : [];
      
      console.log(`搜索 "${searchKeyword}" 结果:`);
      searchProjects.forEach(p => {
        console.log(`- ${p.name_with_namespace}`);
        console.log(`  ID: ${p.id}`);
        console.log(`  地址: ${p.web_url}`);
      });
      break;

    default:
      console.log(`
GitLab OAuth Tool

用法:
  node index.js auth <Application ID> <Secret>     - 生成授权链接
  node index.js token <ID> <Secret> <code>        - 交换 Access Token
  node index.js list                                - 列出仓库
  node index.js read <项目ID> <文件路径>           - 读取文件

示例:
  node index.js auth your_app_id your_app_secret
  node index.js token your_app_id your_app_secret the_code_from_url
  node index.js list
  node index.js read 11102 README.md
`);
      break;

    case 'handle':
      // 处理用户发来的 code 或 token
      const input = process.argv[3];
      
      if (!input) {
        console.log('用法: node index.js handle <code或token> [用户ID]');
        console.log('');
        console.log('自动识别处理：');
        console.log('- 如果是 OAuth code (40-64位 16进制)，自动换取 token');
        console.log('- 如果是已存在的 token，直接保存');
        console.log('- 如果是项目ID，返回项目信息');
        process.exit(1);
      }

      // 检查是否是 OAuth 授权链接，包含 code=
      let code = input;
      
      // 如果是完整链接，提取 code
      if (input.includes('code=')) {
        const urlMatch = input.match(/[?&]code=([a-f0-9]+)/i);
        if (urlMatch) {
          code = urlMatch[1];
          console.log('从授权链接中提取到 code:', code);
        }
      }
      
      // 检查是否是 OAuth code (40-64 位 16 进制字符串)
      const isOAuthCode = /^[a-f0-9]{40,64}$/i.test(code);
      
      if (isOAuthCode) {
        // 尝试换取 token
        console.log('检测到 OAuth code，正在换取 token...');
        
        // 读取 OAuth 配置
        let clientId, clientSecret;
        try {
          const oauthConfig = JSON.parse(fs.readFileSync(path.join(__dirname, 'oauth-config.json'), 'utf8'));
          clientId = oauthConfig.client_id;
          clientSecret = oauthConfig.client_secret;
        } catch (e) {
          console.log('未找到 OAuth 配置，请先运行: node index.js auth <Application ID> <Secret>');
          process.exit(1);
        }

        const tokenData = await new Promise((resolve, reject) => {
          const postData = new url.URLSearchParams({
            client_id: clientId,
            client_secret: clientSecret,
            code: code,
            grant_type: 'authorization_code',
            redirect_uri: 'http://localhost/callback'
          }).toString();

          const parsedUrl = new url.parse(config.gitlab_url + '/oauth/token');
          const isHttps = config.gitlab_url.startsWith('https');
          const lib = isHttps ? https : http;

          const options = {
            hostname: parsedUrl.hostname,
            port: parsedUrl.port || (isHttps ? 443 : 80),
            path: parsedUrl.path,
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Content-Length': Buffer.byteLength(postData)
            }
          };

          const req = lib.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
              try {
                resolve(JSON.parse(body));
              } catch (e) {
                reject(e);
              }
            });
          });

          req.on('error', reject);
          req.write(postData);
          req.end();
        });

        if (tokenData.access_token) {
          console.log('✅ 授权成功！Token 已保存。');
          console.log(`Access Token: ${tokenData.access_token.substring(0, 20)}...`);
          
          // 保存到配置
          config.access_token = tokenData.access_token;
          fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
          console.log('Token 已保存到 config.json');
          
          // 验证 token
          const userInfo = await request('GET', '/api/v4/user');
          console.log(`授权用户: ${userInfo.name} (${userInfo.username})`);
        } else {
          console.log('❌ 授权失败:', tokenData.error_description || tokenData.msg);
        }
      } else {
        // 尝试作为 token 直接使用
        console.log('尝试作为 Token 使用...');
        const testResult = await fetch(config.gitlab_url + '/api/v4/user', {
          headers: { 'Authorization': `Bearer ${input}` }
        }).then(r => r.json());

        if (testResult.id) {
          console.log('✅ Token 有效！');
          console.log(`用户: ${testResult.name} (${testResult.username})`);
          
          // 保存 token
          config.access_token = input;
          fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
          console.log('Token 已保存到 config.json');
        } else {
          console.log('❌ 无效的 Token');
        }
      }
      break;

    case 'config':
      // 配置 OAuth 应用信息
      const configClientId = process.argv[3];
      const configClientSecret = process.argv[4];
      
      if (!configClientId || !configClientSecret) {
        console.log('用法: node index.js config <Application ID> <Secret>');
        console.log('保存 OAuth 应用配置，用于自动处理群里收到的 code');
        process.exit(1);
      }

      const oauthConfig = {
        client_id: configClientId,
        client_secret: configClientSecret
      };
      fs.writeFileSync(path.join(__dirname, 'oauth-config.json'), JSON.stringify(oauthConfig, null, 2));
      console.log('✅ OAuth 配置已保存');
      break;
  }
}

main().catch(console.error);
