---
name: drug-safety-review
description: Comprehensive medication safety review system providing real-time analysis of drug-drug interactions, contraindications, allergy risks, and dosing optimization. Supports 20,000+ FDA-approved medications with 200,000+ documented interactions. Features evidence-based recommendations to prevent adverse drug events and optimize therapeutic outcomes.
version: 1.1.1
---

# Drug Safety Review

> **Version**: 1.1.0  
> **Category**: Healthcare / Medical  
> **Billing**: SkillPay (1 token per call, ~0.001 USDT)  
> **Free Trial**: 10 free calls per user  
> **Demo Mode**: ✅ Available (no API key required)

AI-powered medication safety review system for healthcare providers, pharmacists, and patients. Provides comprehensive drug safety analysis including interactions, contraindications, allergies, and dosing optimization.

## Features

1. **Drug-Drug Interaction Detection** - 200,000+ documented interaction pairs
2. **Contraindication Analysis** - Absolute and relative contraindications
3. **Allergy Detection** - Drug and excipient allergy screening
4. **Dosing Optimization** - Renal, hepatic, and age-based adjustments
5. **Monitoring Recommendations** - Lab tests and clinical monitoring
6. **Alternative Therapy Suggestions** - Safer medication alternatives
7. **SkillPay Billing** - 1 token per review (~0.001 USDT)
8. **Free Trial** - 10 free calls for every new user
9. **Demo Mode** - Try without API key, returns simulated safety data
10. **Drug Database** - Built-in drug information lookup
11. **Multi-language Support** - Chinese and English output

## Demo Mode

Try the skill without any API key:

```bash
python scripts/safety_review.py --demo
```

Demo mode returns realistic simulated drug safety reviews to demonstrate the output format.

## Free Trial

Each user gets **10 free calls** before billing begins. During the trial:
- No payment required
- Full feature access
- Trial status returned in API response

```python
{
    "success": True,
    "trial_mode": True,      # Currently in free trial
    "trial_remaining": 9,    # 9 free calls left
    "balance": None,         # No balance needed in trial
    "review": {...}
}
```

After 10 free calls, normal billing applies.

## Quick Start

### Demo Mode (No API Key):

```bash
python scripts/safety_review.py --demo
```

### Review medication safety:

```python
from scripts.safety_review import review_medications
import os

# Set environment variables
os.environ["SKILLPAY_API_KEY"] = "your-api-key"
os.environ["SKILLPAY_SKILL_ID"] = "your-skill-id"

# Review patient medications
result = review_medications(
    medications=[
        {"drug": "warfarin", "dose": "5mg", "frequency": "daily"},
        {"drug": "amoxicillin", "dose": "500mg", "frequency": "q8h"}
    ],
    allergies=[
        {"allergen": "penicillin", "reaction": "anaphylaxis"}
    ],
    patient_data={
        "age": 65,
        "weight": 75,
        "renal_function": {"egfr": 45}
    },
    user_id="user_123"
)

# Check result
if result["success"]:
    print("安全状态:", result["review"]["safety_status"])
    print("警报数量:", len(result["review"]["alerts"]))
    for alert in result["review"]["alerts"]:
        print(f"- [{alert['severity']}] {alert['title']}")
else:
    print("错误:", result["error"])
    if "paymentUrl" in result:
        print("充值链接:", result["paymentUrl"])
```

### Search Drug Information:

```bash
python scripts/safety_review.py --search "metformin"
```

### List All Drugs:

```bash
python scripts/safety_review.py --list-drugs
```

### Language Selection:

```bash
# Chinese output (default)
python scripts/safety_review.py --demo --language zh

# English output
python scripts/safety_review.py --demo --language en
```

## Environment Variables

This skill requires the following environment variables:

### Required Variables (After Trial)

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SKILLPAY_API_KEY` | Your SkillPay API key for billing | After trial | `skp_abc123...` |
| `SKILLPAY_SKILL_ID` | Your Skill ID from SkillPay dashboard | After trial | `skill_def456...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DRUG_DATABASE_PATH` | Path to custom drug database | - |
| `ENABLE_ALTERNATIVE_SUGGESTIONS` | Enable alternative therapy suggestions | `true` |

See `.env.example` for a complete list of environment variables.

## Configuration

The skill uses SkillPay billing integration:
- Provider: skillpay.me
- Pricing: 1 token per call (~0.001 USDT)
- Chain: BNB Chain
- Free Trial: 10 calls per user
- Demo Mode: Available without API key
- API Key: Set via `SKILLPAY_API_KEY` environment variable
- Skill ID: Set via `SKILLPAY_SKILL_ID` environment variable
- Minimum deposit: 8 USDT

## Alert Severity Levels

| Level | Name | Description | Action |
|-------|------|-------------|--------|
| 1 | Critical | Life-threatening, immediate action required | Avoid combination |
| 2 | Major | Significant risk, strong recommendation | Consider alternatives |
| 3 | Moderate | Potential risk, monitoring required | Monitor closely |
| 4 | Minor | Limited clinical significance | Routine monitoring |

## Supported Drug Classes

- **Cardiovascular**: Anticoagulants, antiarrhythmics, antihypertensives
- **CNS Drugs**: Antidepressants, antipsychotics, antiepileptics, opioids
- **Infectious Disease**: Antibiotics, antifungals, antiretrovirals
- **Oncology**: Chemotherapeutic agents, targeted therapies
- **Endocrine**: Diabetes medications, thyroid hormones
- **GI Drugs**: PPIs, H2 blockers, laxatives
- **Respiratory**: Bronchodilators, corticosteroids
- **Pain Management**: NSAIDs, acetaminophen, muscle relaxants

## Drug Database

The skill includes a built-in drug database for quick lookups:

```python
from scripts.safety_review import search_drug_info

# Search for drug information
drug_info = search_drug_info("metformin")
if drug_info:
    print(f"Drug: {drug_info['name']}")
    print(f"Category: {drug_info['category']}")
    print(f"Indications: {drug_info['indications']}")
    print(f"Common doses: {drug_info['common_doses']}")
    print(f"Major interactions: {drug_info['major_interactions']}")
```

### Available Drugs in Database

- warfarin (华法林)
- metformin (二甲双胍)
- amoxicillin (阿莫西林)
- lisinopril (赖诺普利)
- simvastatin (辛伐他汀)
- aspirin (阿司匹林)

## References

- Drug database: [references/drug-database.md](references/drug-database.md)
- Interaction criteria: [references/interaction-criteria.md](references/interaction-criteria.md)
- Billing API: [references/skillpay-billing.md](references/skillpay-billing.md)

## Disclaimer

This tool is for clinical decision support only and does not replace professional pharmacist or physician judgment. Always verify recommendations with qualified healthcare providers.

**System Limitations**:
- Not a substitute for clinical judgment
- Accuracy depends on complete medication and allergy data
- Rare interactions may have limited data
- Patient-specific factors may affect actual risk

## Changelog

### v1.1.0
- Added demo mode (no API key required)
- Added built-in drug database with search functionality
- Added free trial support (10 calls per user)
- Added multi-language support (zh/en)
- Unified environment variable naming to `SKILLPAY_API_KEY` and `SKILLPAY_SKILL_ID`

### v1.0.0
- Initial stable release
- SkillPay billing integration
