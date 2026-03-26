# Baidu Document Parser API Key Setup Guide (OpenClaw)

## BAIDU_DOC_AI_API_KEY And  BAIDU_DOC_AI_SECRET_KEY Not Configured

When the `BAIDU_DOC_AI_API_KEY` and `BAIDU_DOC_AI_SECRET_KEY`environment variable is not set, follow these steps:

### 1. Get API and AI_SECRET_KEY Key
Visit: **https://ai.baidu.com/ai-doc/REFERENCE/Tkru0geon**
- Log in to your Baidu Cloud account
- Create an application or view existing API keys and AI_SECRET_KEY
- Copy your **API Key** and **AI_SECRET_KEY**


### 2. Configure OpenClaw
Edit the OpenClaw configuration file: `~/.openclaw/openclaw.json`

Add or merge the following structure:

```json
{
  "skills": {
    "entries": {
      "xmind-doc-parser": {
        "env": {
          "BAIDU_DOC_AI_API_KEY": "your_actual_api_key_here",
          "BAIDU_DOC_AI_SECRET_KEY": "your_actual_secret_key_here"
        }
      }
    }
  }
}
```

Replace `"your_actual_api_key_here"` with your actual API key and "your_actual_secret_key_here" with your actual SECRET key .

### 3. Verify Configuration
```bash
# Check JSON format
cat ~/.openclaw/openclaw.json | python -m json.tool
```
```bash
# Check  access_token
curl -X POST 'https://aip.baidubce.com/oauth/2.0/token' \
  -d 'grant_type=client_credentials' \
  -d 'client_id={api_key}' \
  -d 'client_secret={secret_key}'
```

### 4. Restart OpenClaw
```bash
openclaw gateway restart
```

### 5. Test
```bash
cd ~/.openclaw/workspace/skills/xmind-doc-parser
python3 scripts/baidu_doc_parser.py --file_data <文件的base64编码> 
python3 scripts/baidu_doc_parser.py --file_url <文件数据URL> 
```

## Troubleshooting
- Ensure `~/.openclaw/openclaw.json` exists with correct JSON format
- Confirm API key is valid and Baidu AI Search service is activated
- Check account balance on Baidu Cloud
- Restart OpenClaw after configuration changes

**Recommended**: Use OpenClaw configuration file for centralized management
