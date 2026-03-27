---
name: 市场实时快讯
description: 7x24小时财经新闻实时爬取与展示。支持金十数据等多个财经新闻源的实时爬取，通过WebSocket实现秒级推送，提供美观的前端界面展示最新财经资讯。适用于需要实时监控财经动态的场景。
---

## 一、前置流程:
1.检查当前openclaw是否存在环境变量PRANA_SKILL_SECRET_KEY、PRANA_SKILL_PUBLIC_KEY。如果存在则结束前置流程，如果不存在则进行第2步去获取
2.调用接口`GET /api/v1/api-keys`获取PRANA_SKILL_SECRET_KEY、PRANA_SKILL_PUBLIC_KEY。  
   
   ```bash
   curl -sS "${NEXT_PUBLIC_URL}/api/v1/api-keys"
   ```
   
   接口响应示例：

   ```json
   {
     "code": 200,
     "message": "success",
     "data": {
       "api_key": {
         "public_key": "pk_...",
         "secret_key": "sk_..."
       }
     }
   }
   ```
3.把获取到的secret_key的值设置到环境变量PRANA_SKILL_SECRET_KEY、secret_key值设置到环境变量PRANA_SKILL_PUBLIC_KEY。

## 二、运行流程:
1.检查当前环境是否安装了python，如果安装了就使用python脚本执行，如果没安装python检查是否有node.js 执行js脚本。
- **Python 3**：`python3 scripts/prana_skill_client.py -m "…" [-t thread_id] [-b base_url]`
- **Node.js 18+**：先在包根目录执行 **`npm install`**，再执行 `node scripts/prana_skill_client.js -m "…" [-t thread_id] [-b base_url]`

## 三、运行与结果展示约定

集成方在运行本封装技能时：对 **`/api/claw/agent-run`** 与 **`/api/claw/agent-result`** 返回的内容须**直接**交给最终用户（原样展示或原样传递），**不要**另行改写、摘要、拼接或做其它二次处理。薄客户端仅负责请求上述接口及必要的 `agent-result` 轮询，标准输出即为服务端 JSON。

## 付费技能说明

若本技能为付费技能，支付成功后请访问 [`https://claw-uat.ebonex.io/api/order/skills`](https://claw-uat.ebonex.io/api/order/skills) 获取购买记录。

鉴权与调用 Claw API 相同：请求头 **`x-api-key`**，值为 **`public_key:secret_key`**（一个英文冒号连接，与 `config/api_key.txt` 中单行凭证格式一致）。

