---
name: aliyun-domain
description: Manage domain assets via Aliyun OpenAPI: query, renew, transfer, register, and modify domains. Requires user confirmation for financial operations. Provides policy consulting (pricing, discounts, promo codes) and industry consulting (registration, trading, hosting, ICP filing) via RAG-based local knowledge base. Includes domain monitoring for expiration, WHOIS changes, and SSL certificates.
triggers:
  - "domain monitoring"
  - "WHOIS"
  - "domain expiration"
  - "SSL certificate"
  - "domain query"
  - "domain renewal"
  - "domain registration"
  - "domain transfer"
  - "domain ownership change"
  - "ICP filing"
  - "domain hosting"
  - "domain trading"
  - "domain investment"
  - "trending domains"
  - "domain pricing"
  - "promo codes"
---
# Aliyun Domain Management Skill

Manage domain assets via Aliyun OpenAPI with query, renewal, transfer, registration, and modification capabilities.

## 🆕 Industry Consulting (RAG)

### Function

When users ask about domain registration, trading, hosting, or ICP filing, **must use RAG to search local knowledge base** `knowledge/aliyun-domain-help` and answer based on retrieved documentation.

### Trigger Rules

**Must trigger RAG search for these topics:**

| Category | Triggers | Keywords |
|:---|:---|:---|
| 🆕 **Registration** | How to register, registration process, requirements | `domain registration` `registration flow` `real-name auth` |
| 💰 **Trading** | Domain buying/selling, fixed-price, push, repurchase | `domain trading` `buy domain` `fixed price` `push` |
| 🏗️ **Hosting** | How to host website, site setup, domain binding | `hosting` `website setup` `domain binding` `DNS` |
| 📋 **ICP Filing** | ICP filing, filing process, materials, requirements | `ICP` `filing` `website filing` `filing materials` |
| 🔒 **Security** | Domain locking, transfer lock, update lock | `lock` `security lock` `transfer prohibited` |
| 📝 **Management** | Ownership change, info modification, DNS change | `ownership change` `modify info` `DNS` `transfer` |
| 💸 **Renewal/Redemption** | Domain renewal, expired redemption, pricing | `renewal` `redemption` `expired domain` |
| ❓ **FAQ** | Registration failures, audit errors, error messages | `FAQ` `troubleshooting` `error` `failed` |

### RAG Workflow

1. **Identify intent**: Extract keywords from user query
2. **Search knowledge base**: Use `domain_knowledge_rag.py` to retrieve docs
3. **Synthesize answer**: Compile retrieved content into coherent response
4. **Cite sources**: Must cite document names and categories
5. **Provide links**: Include original Aliyun help links when available

### Response Guidelines

1. **Search first**: Always search knowledge base before answering
2. **Cite sources**: Clearly state referenced documents (e.g., "According to 'Domain Registration Quick Start'...")
3. **Maintain accuracy**: Key steps and requirements must match source docs
4. **Segment citations**: Label multiple sources separately
5. **Note timeliness**: Remind users of doc update dates; refer to official site for latest info
6. **Acknowledge gaps**: If no relevant docs found, state this and provide official links

### Example

```
User: How do I register a domain?
AI: 📚 According to Aliyun docs "Domain Registration Quick Start":

1. **Check domain availability**
   - Visit Aliyun domain search page
   - Enter desired domain name
   - Verify availability

2. **Real-name verification**
   - Individual: Upload ID card (front & back)
   - Enterprise: Upload business license
   - Wait for audit (1-2 business days)

3. **Submit order**
   - Select registration period (1-10 years)
   - Fill registrant information
   - Complete payment

4. **Domain management**
   - Configure DNS servers
   - Set up domain resolution
   - Enable security locks

📄 Source: knowledge/aliyun-domain-help/02-Quick-Start/domain-registration.md
🔗 Link: https://help.aliyun.com/zh/dws/getting-started/domain-name-quick-start
```

## ⚠️ Security Rules (Critical)

### 🔐 Two-Factor Confirmation for Financial Operations

**All payment-related API calls require explicit user confirmation before execution!**

#### Operations Requiring Confirmation

| Operation | Risk Level | Confirmation Details |
|:---|:---|:---|
| 🆕 Domain registration | 🔴 High | Domain name, years, total cost, registrant info |
| 💰 Domain renewal | 🔴 High | Domain name, years, cost, expiration date |
| 🔄 Domain redemption | 🔴 High | Domain name, redemption price, current status |
| 📝 Domain transfer | 🟡 Medium | Domain name, fee, target registrar |
| 🔒 Domain lock/unlock | 🟡 Medium | Domain name, operation type, impact |
| ✏️ Contact info change | 🟡 Medium | Domain name, fields changed, before/after values |
| 🌐 DNS modification | 🟡 Medium | Domain name, old/new DNS list |

#### Confirmation Flow

1. **Show details**: List operation content, impact, costs
2. **Wait for confirmation**: Require explicit user approval (e.g., "confirm", "yes", "ok")
3. **Execute**: Call API after confirmation
4. **Report result**: Provide immediate feedback after completion

#### Example

❌ **Wrong** (no confirmation):
```
User: Register shenyue.xyz
AI: ✅ Registered shenyue.xyz (Order: xxx)
```

✅ **Correct** (confirm first):
```
User: Register shenyue.xyz
AI: 🛒 Registration Confirmation

Domain: shenyue.xyz
Period: 1 year
Cost: ¥7
Registrant: shenyu (Template ID: 24485442)
Verification: ✅ Approved

Confirm registration? Reply "confirm" to proceed.

User: confirm
AI: ✅ Registration successful! Order: xxx
```

#### No Confirmation Needed

Query operations can execute directly:
- ✅ Domain list query
- ✅ Domain detail query
- ✅ Availability check
- ✅ Task status query
- ✅ Contact info query
- ✅ Statistics retrieval
- ✅ Expiring domain query
- ✅ Pricing/promo query

## 📚 Knowledge Base

### Files

| Path | Content |
|:---|:---|
| `knowledge/domain_pricing_discounts.md` | Aliyun pricing policies (registration prices, bulk discounts, transfer deals, renewal discounts, promo codes) |
| `knowledge/aliyun-domain-help/` | Aliyun help docs (registration, trading, management, hosting, ICP filing guides) |

> Update `domain_pricing_discounts.md` monthly.
> Regularly update `aliyun-domain-help/` for accuracy.

### Help Docs Structure

```
knowledge/aliyun-domain-help/
├── 01-Product-Overview/      # Domain service intro, basic concepts, pricing
├── 02-Quick-Start/           # Registration, trading, hosting guides
├── 03-Operations-Guide/      # Detailed tutorials (registration, auth, transfer, security)
├── 04-Domain-Trading/        # Trading types, purchase flow, fraud prevention
├── 05-ICP-Filing/            # ICP filing process, compliance requirements
└── 06-FAQ/                   # Common questions and solutions
```

### RAG Search Script

```bash
# CLI usage
python3 scripts/domain_knowledge_rag.py "domain registration process"
python3 scripts/domain_knowledge_rag.py "ICP filing materials"
python3 scripts/domain_knowledge_rag.py "how to host website"

# Python usage
from domain_knowledge_rag import answer_with_rag
answer = answer_with_rag("domain ownership change requirements?")
print(answer)
```

### Pricing Query Triggers

**Must read `knowledge/domain_pricing_discounts.md` before answering:**

- Domain registration price/cost
- Domain renewal price/cost
- Transfer pricing
- Bulk registration/renewal discounts
- Promotions/discounts/sales
- Promo codes/renewal codes
- Premium domain discounts
- Multi-year registration deals
- Cheapest TLD recommendations
- Cost confirmation before registration/renewal/transfer operations

### Hotspot Investment Analysis ⭐ NEW

**Trigger keywords for domain investment analysis:**

| Keyword | Example | Action |
|:---|:---|:---|
| `hotspot` | "Any domain investment hotspots?" | Recommend claw/ai/agent keywords |
| `investment` | "Is claw domain worth investing?" | Analyze claw keyword opportunities |
| `recommend` | "Recommend some domains" | Suggest registrable domains |
| `bulk` | "Want to bulk register domains" | Recommend .xyz combos |
| `lucky-numbers` | "Lucky number domains?" | Analyze 168/518/678 combos |
| `AI-domain` | "AI-related domains?" | Analyze ai/agent/bot keywords |

**Analysis Flow**:
1. Extract hotspot keywords
2. Generate 50+ candidate domains
3. Check availability via API
4. Rank by热度/price/potential, output TOP 10
5. Include promo codes and cost estimates
6. Generate Aliyun purchase links

### Purchase Links ⭐ NEW (Universal)

**All recommended registrable domains include purchase links:**

| Scenario | Example |
|:---|:---|
| Hotspot analysis | `python3 domain_hotspot_analyzer.py claw` |
| Daily checks | `check_domain("example.cn")` |
| Bulk screening | Loop through domain list |
| Keyword recommendations | "Recommend AI-related domains" |
| Lucky number combos | "168-ending domains" |

**Link Format**:
- Pattern: `https://wanwang.aliyun.com/buy/commonbuy?domain={domain}&suffix={tld}&duration=12`
- Auto-extract TLD from full domain (tryagent.cn → domain: tryagent, suffix: cn)
- One-click purchase: Pre-filled domain and period (1 year)
- Output: Markdown clickable links + quick link list

**Example**:
```
✅ Registrable domains:

1. [claw168.cn](https://wanwang.aliyun.com/buy/commonbuy?domain=claw168&suffix=cn&duration=12) - ¥38 🔢 Lucky number
2. [claw518.cn](https://wanwang.aliyun.com/buy/commonbuy?domain=claw518&suffix=cn&duration=12) - ¥38 🔢 Lucky number
3. [tryagent.cn](https://wanwang.aliyun.com/buy/commonbuy?domain=tryagent&suffix=cn&duration=12) - ¥38 🤖 AI agent

🔗 Quick links:
  1. https://wanwang.aliyun.com/buy/commonbuy?domain=claw168&suffix=cn&duration=12
  2. https://wanwang.aliyun.com/buy/commonbuy?domain=claw518&suffix=cn&duration=12
  3. https://wanwang.aliyun.com/buy/commonbuy?domain=tryagent&suffix=cn&duration=12
```

### Response Guidelines

1. **Read before answering**: Always read knowledge base first; don't guess prices
2. **Note timeliness**: Mention promo validity periods (e.g., "March promo, ends Mar 31")
3. **Include links**: Provide official links from knowledge base
4. **Cost confirmation synergy**: Reference promo prices during user confirmation for operations
5. **Acknowledge gaps**: If query not covered, state this and direct to official site
6. **Price disclaimer**: Actual prices subject to Aliyun API/website

## 📋 Features

### 🆕 Industry Consulting (RAG)

- ✅ **Registration**: Process, real-name auth, requirements, materials
- ✅ **Trading**: Buying/selling, fixed-price, push, repurchase, flow
- ✅ **Hosting**: Full website setup flow, domain binding, DNS config
- ✅ **ICP Filing**: Process, materials, requirements, regional rules
- ✅ **Management**: Ownership change, info modification, DNS, security
- ✅ **Renewal/Redemption**: Process, pricing, expired domain handling
- ✅ **FAQ**: Registration failures, audit errors, troubleshooting

**RAG Features**:
- 📚 Based on official Aliyun docs
- 🔍 Semantic search for精准 matching
- 📄 Cite sources and categories
- 🔗 Provide original links
- ⏰ Note doc update times

### Domain Management

- List, query, renew, transfer, register, lock/unlock domains
- Query tasks and task details
- Modify contact info and DNS

### Domain Investment Analysis ⭐ NEW

- ✅ **Hotspot analysis**: Recommend investment opportunities based on trends
- ✅ **Bulk screening**: Auto-generate candidates and check availability
- ✅ **Value assessment**: Provide热度 ratings, investment rationale, price estimates
- ✅ **Lucky numbers**: Support 168/518/678/886 combos
- ✅ **Asset dashboard** 📊: Generate portfolio overview/expiration distribution/value stats/recommendations
- ✅ **Purchase links**: Auto-generate one-click links for all registrable domains

**Supported Keywords**:

| Keyword | Theme |热度 | Description |
|:---|:---|:---:|:---|
| `claw` | Claw (OpenClaw) | ⭐⭐⭐⭐⭐ | 2026's hottest GitHub AI project, 180k stars |
| `ai` | AI | ⭐⭐⭐⭐⭐ | AI.com sold for $70M, agent boom |
| `agent` | AI Agent | ⭐⭐⭐⭐⭐ | Hottest 2026 investment direction |
| `bot` | Bot/Automation | ⭐⭐⭐⭐ | Automation/robot concept |
| `qwen` | Qwen | ⭐⭐⭐⭐ | Alibaba Qwen model series |
| `168/518/678/886` | Lucky Numbers | ⭐⭐⭐ | Chinese-preferred lucky combos |

### Domain Monitoring 🆕 NEW

- ✅ **Expiration monitoring**: Track domain expiration dates, early warnings
- ✅ **WHOIS tracking**: Record registrar, DNS, key info changes
- ✅ **SSL monitoring**: Check certificate validity and expiration
- ✅ **Status change alerts**: Timely notifications for important changes
- ✅ **History query**: View monitoring records and alert history

### Pricing Consulting

- ✅ Registration promo prices (TLD-specific deals, premium discounts)
- ✅ Bulk registration discounts (.com/.cn/.net/.xin tiered pricing)
- ✅ Transfer deals (Wednesday transfer day promos)
- ✅ Renewal discounts (bulk discounts + promo codes)
- ✅ Optimal registration/renewal/transfer recommendations

## 🔐 Configuration

### 1. Get Aliyun AccessKey

1. Login to [Aliyun Console](https://ram.console.aliyun.com/)
2. Go to RAM Access Control
3. Create user or use existing
4. Create AccessKey (AK/SK)
5. Grant `AliyunDomainFullAccess` permission

### 2. Configure Environment Variables (Recommended)

```bash
export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"
```

**Permanent config** (add to `~/.bashrc` or `~/.zshrc`):
```bash
echo 'export ALIYUN_ACCESS_KEY_ID="your-access-key-id"' >> ~/.zshrc
echo 'export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"' >> ~/.zshrc
source ~/.zshrc
```

| Env Var | Description | Example |
|:---|:---|:---|
| `ALIYUN_ACCESS_KEY_ID` | Aliyun AccessKey ID | `LTAI5t...` |
| `ALIYUN_ACCESS_KEY_SECRET` | Aliyun AccessKey Secret | `abcdef...` |

### 3. Security Best Practices

- ✅ Use environment variables, avoid hardcoding
- ✅ Use RAM sub-account AK, not main account
- ✅ Rotate AccessKeys regularly
- ⚠️ Never commit AccessKeys to Git or share

## 🚀 Usage

### CLI

```bash
# Configure env (first use or new session)
export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"

# List domains
python3 scripts/aliyun_domain.py list

# Domain detail
python3 scripts/aliyun_domain.py detail --domain example.com

# Expiring domains
python3 scripts/aliyun_domain.py expiring --days 30

# Renew domain
python3 scripts/aliyun_domain.py renew --domain example.com --years 1

# Query tasks
python3 scripts/aliyun_domain.py tasks --status Running

# 🔥 Hotspot analysis (NEW)
python3 scripts/domain_hotspot_analyzer.py claw
python3 scripts/domain_hotspot_analyzer.py ai
python3 scripts/domain_hotspot_analyzer.py agent

# List supported keywords
python3 scripts/domain_hotspot_analyzer.py --list

# 🆕 Domain monitoring (NEW)
python3 scripts/domain_monitor.py add example.com           # Add monitoring
python3 scripts/domain_monitor.py status example.com        # Check status
python3 scripts/domain_monitor.py list                      # List all
python3 scripts/domain_monitor.py check                     # Check all
python3 scripts/domain_monitor.py remove example.com        # Remove
python3 scripts/domain_monitor.py history example.com       # View history
```

### RAG Search Script

```python
from domain_knowledge_rag import answer_with_rag, DomainKnowledgeRAG

# Method 1: Direct answer
answer = answer_with_rag("Domain registration process?")
print(answer)

# Method 2: Detailed search
rag = DomainKnowledgeRAG()
sections = rag.get_relevant_sections("ICP filing materials", max_sections=3)
for section in sections:
    print(f"Title: {section['title']}")
    print(f"Category: {section['category']}")
    print(f"Excerpt: {section['excerpt'][:200]}...")
```

**Supported Queries**:

| Type | Example | Description |
|:---|:---|:---|
| Registration | "How to register domain" | Process, requirements, materials |
| Real-name auth | "ICP filing materials" | Individual/enterprise auth |
| Trading | "What is fixed-price domain" | Trading types, flow, tips |
| Hosting | "How to host after registration" | Full flow, server selection |
| ICP Filing | "Individual filing materials" | Process, materials, requirements |
| Management | "How to change ownership" | Ownership change, info mod, DNS |
| Security | "How to lock domain" | Transfer lock, update lock |
| Renewal | "Expired domain怎么办" | Renewal, redemption, pricing |
| FAQ | "Registration failed" | Error handling, FAQ |

### Python SDK

```python
import os
from aliyun_domain import AliyunDomainClient

# Read from env
access_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID')
access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')

# Init client
client = AliyunDomainClient(
    access_key_id=access_key_id,
    access_key_secret=access_key_secret
)

# List domains
domains = client.list_domains(page_size=100)
for domain in domains:
    print(f"{domain['DomainName']} - {domain['ExpirationDate']}")

# Domain detail
detail = client.query_domain_detail("example.com")

# Expiring domains
expiring = client.query_expiring_domains(days=30)

# Renewal (⚠️ requires confirmation)
# Step 1: Show confirmation info
print("🛒 Renewal Confirmation")
print("Domain: example.com")
print("Period: 1 year")
print("Cost: ¥85")
confirm = input("Confirm renewal? (yes/no): ")

# Step 2: Execute after user confirmation
if confirm.lower() == 'yes':
    result = client.renew_domain("example.com", years=1)
    print(f"Renewal successful! Order: {result.get('OrderId')}")
```

## 📚 API Reference

### Domain Management API

| Method | Function | API Action |
|:---|:---|:---|
| `list_domains()` | List domains | DescribeDomains |
| `query_domain_detail()` | Domain detail | QueryDomainDetail |
| `query_domain_list()` | Paginated query | QueryDomainList |
| `query_expiring_domains()` | Expiring domains | QueryDomainList |
| `save_single_domain_update()` | Modify info | SaveSingleTaskForUpdatingContactInfo |
| `transfer_domain_in()` | Transfer in | TransferDomainIn |
| `transfer_domain_out()` | Transfer out | TransferDomainOut |
| `renew_domain()` | Renewal | SaveSingleTaskForRenewingDomain |
| `register_domain()` | Registration | SaveSingleTaskForCreatingOrderActivate |
| `lock_domain()` | Lock | SaveSingleTaskForTransferProhibitionLock |
| `unlock_domain()` | Unlock | SaveSingleTaskForTransferProhibitionLock |

### Task Management API

| Method | Function | API Action |
|:---|:---|:---|
| `query_task_list()` | Task list | QueryTaskList |
| `query_task_detail()` | Task detail | QueryTaskDetailList |

## 📁 Structure

```
aliyun_domain/
├── SKILL.md                        # Skill documentation
├── README.md                       # Project readme
├── SAFE_OPERATION_GUIDE.md         # Safety guide
├── config/
│   ├── credentials.json            # Credentials
│   └── credentials.json.example    # Template
├── knowledge/                      # Knowledge base 📚
│   ├── domain_pricing_discounts.md # Pricing policies
│   └── aliyun-domain-help/         # Aliyun help docs (RAG) ⭐ NEW
│       ├── 01-Product-Overview/
│       ├── 02-Quick-Start/
│       ├── 03-Operations-Guide/
│       ├── 04-Domain-Trading/
│       ├── 05-ICP-Filing/
│       ├── 06-FAQ/
│       └── README.md
├── learnings/                      # Learnings ⭐
│   ├── README.md                   # Index
│   ├── API_QUICK_REFERENCE.md      # API quick ref
│   ├── API_FIELD_CASE_ISSUE.md     # Field case issues
│   ├── DOMAIN_LOCK_OPERATION.md    # Lock operations
│   └── REGISTRANT_PROFILE_QUERY.md # Template query issues
├── scripts/
│   ├── aliyun_domain.py            # Domain API client (1345 lines)
│   ├── domain_hotspot_analyzer.py  # 🔥 Hotspot analysis (NEW)
│   ├── domain_knowledge_rag.py     # 📚 RAG search (NEW)
│   ├── domain_promotion_search.py  # 💰 Promo search
│   ├── domain_monitor.py           # 🆕 Monitoring (NEW)
│   ├── safe_operation_example.py   # Safety examples
│   └── ...                         # Other scripts
└── .gitignore                      # Git ignore
```

## 🔧 Dependencies

```bash
pip3 install aliyun-python-sdk-core aliyun-python-sdk-domain
```

## ⚠️ Notes

1. **API rate limits**: Aliyun API has QPS limits; avoid high-frequency calls
2. **Permissions**: Requires `AliyunDomainFullAccess` or custom policy
3. **Region**: Domain API uses `cn-hangzhou` region
4. **Costs**: Some API calls incur fees (registration, renewal)
5. **Redemption period**: Expired domains enter redemption phase with higher fees (¥200-500)

## 🆘 Troubleshooting

| Issue | Solution |
|:---|:---|
| `InvalidAccessKeyId.NotFound` | Verify AK/SK in credentials.json; confirm RAM user has permissions |
| `Forbidden.Ram` | Grant `AliyunDomainFullAccess` to RAM user |
| `SDK.Server.Unreachable` | Check network; ensure api.aliyuncs.com is accessible |
| `MissingAliyunDns` error | Set `set_AliyunDns(False)` parameter |
| `set_DomainList()` AttributeError | Use `set_DomainNames()` instead |
| `query_task_list()` returns `[]` | Use raw API call |
| `query_registrant_profiles()` returns `[]` | Use raw API; path is `RegistrantProfiles.RegistrantProfile` |
| `AuditStatus` not found | Use `RealNameStatus` instead |
| `InvalidStatus` error for lock | Use string `'true'`/`'false'`, not boolean |
| `MissingPageNum` error | Add `set_PageNum(1)` and `set_PageSize(10)` |

**Detailed docs**: See `learnings/` folder for in-depth troubleshooting.

## 🔒 Domain Lock Operations (2026-03-14)

### Transfer Lock & Update Lock Parameters

**⚠️ Critical: Status must be string, not boolean!**

```python
# ✅ Correct
request.set_Status('true')   # Enable lock
request.set_Status('false')  # Disable lock

# ❌ Wrong
request.set_Status(True)           # Boolean causes error
request.set_Status('OPEN')         # String OPEN causes error
request.set_Status('Enable')       # String Enable causes error
```

### Example Code

```python
# Enable transfer lock
from aliyunsdkdomain.request.v20180129.SaveSingleTaskForTransferProhibitionLockRequest import SaveSingleTaskForTransferProhibitionLockRequest

request = SaveSingleTaskForTransferProhibitionLockRequest()
request.set_DomainName('shenyue.xyz')
request.set_Status('true')  # ⚠️ Must be string "true"

response = client.client.do_action_with_exception(request)
result = json.loads(response)
task_no = result.get('TaskNo', '')

# Enable update lock
from aliyunsdkdomain.request.v20180129.SaveSingleTaskForUpdateProhibitionLockRequest import SaveSingleTaskForUpdateProhibitionLockRequest

request = SaveSingleTaskForUpdateProhibitionLockRequest()
request.set_DomainName('shenyue.xyz')
request.set_Status('true')  # ⚠️ Must be string "true"
```

### Check Lock Status

```python
detail = client.query_domain_detail('shenyue.xyz')

transfer_lock = detail.get('TransferProhibitionLock')  # OPEN / CLOSE
update_lock = detail.get('UpdateProhibitionLock')      # OPEN / CLOSE

print(f'Transfer lock: {"🔒 Enabled" if transfer_lock == "OPEN" else "🔓 Disabled"}')
print(f'Update lock: {"🔒 Enabled" if update_lock == "OPEN" else "🔓 Disabled"}')
```

**Full docs**: [learnings/DOMAIN_LOCK_OPERATION.md](learnings/DOMAIN_LOCK_OPERATION.md)

## 📞 Support

- Aliyun Docs: https://help.aliyun.com/product/35836.html
- API Reference: https://next.api.aliyun.com/api/Domain/2018-01-29
- 🔐 Safety Guide: [SAFE_OPERATION_GUIDE.md](SAFE_OPERATION_GUIDE.md)

---

**Version**: v1.12.0  
**Last Updated**: 2026-03-17  
**Maintainer**: 神月 🦐

**Security Rule**: ⚠️ All payment-related API calls require explicit user confirmation before execution!

**Changelog**:
- v1.12.0 (2026-03-17): Added domain monitoring (expiration, WHOIS, SSL) 🆕
- v1.11.0 (2026-03-16): Added industry consulting via RAG (registration, trading, hosting, ICP filing) 📚
- v1.10.0 (2026-03-15): Added auto-renewal link generation
- v1.9.0 (2026-03-15): Added domain asset dashboard
- v1.8.0 (2026-03-15): Added 6-letter domain recommendations
- v1.7.0 (2026-03-15): Purchase links now universal for all scenarios
- v1.6.0 (2026-03-15): Added purchase link generation
- v1.5.0 (2026-03-15): Added hotspot domain investment analysis
- v1.4.0 (2026-03-14): Restructured dirs, added `learnings/` folder
- v1.3.0 (2026-03-14): Added registrant profile query docs
- v1.2.0 (2026-03-14): Added domain lock operation docs
- v1.1.0 (2026-03-14): Added API field case docs, troubleshooting tips
