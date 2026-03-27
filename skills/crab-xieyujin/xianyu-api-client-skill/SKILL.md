# XianYu API Client Skill

## Overview
A robust and secure client library for integrating with the Xianyu Guanjia (Goofish) Open Platform API. This skill handles all authentication, request signing, and error handling complexities, allowing developers to focus on building business logic rather than infrastructure.

## Key Features

### 🔐 Secure Authentication
- Implements MD5-based signature algorithm as required by Xianyu API
- Automatic timestamp generation with proper validation
- Secure credential management via environment variables
- No hardcoded secrets in source code

### 📡 Reliable API Communication  
- Built-in HTTPS connection handling
- Automatic JSON serialization with proper formatting (separators=(',', ':'))
- Comprehensive error handling and retry mechanisms
- Detailed logging for debugging and monitoring

### ⚙️ Configuration Flexibility
- Environment variable based configuration (`XIAN_YU_APP_KEY`, `XIAN_YU_APP_SECRET`)
- Programmatic configuration override support
- Domain and host configuration for different environments
- Type-safe parameter validation

## Technical Specifications

### Authentication Flow
1. **Request Body Serialization**: Convert JSON payload using `json.dumps(data, separators=(',', ':'))`
2. **Body MD5**: Generate MD5 hash of the serialized request body
3. **Signature String**: Construct signature string as `"{app_key},{body_md5},{timestamp},{app_secret}"`
4. **Final Signature**: Generate MD5 hash of the signature string
5. **URL Construction**: Append `appid`, `timestamp`, and `sign` as query parameters

### API Endpoints Supported
- `/api/open/product/create` - Create new products
- `/api/open/product/detail` - Retrieve product details
- Extensible for additional endpoints as needed

### Error Handling
- Network connectivity errors
- Authentication failures (invalid signatures, expired timestamps)
- API rate limiting responses
- Invalid request parameter errors

## Usage Examples

### Basic Initialization
```python
from xianyu_api_client_skill import XianYuAPIClient

# Using environment variables (recommended)
client = XianYuAPIClient()

# Using explicit credentials
client = XianYuAPIClient(
    app_key="your_app_key",
    app_secret="your_app_secret"
)
```

### Product Creation
```python
product_data = {
    "item_biz_type": 2,
    "sp_biz_type": 1,
    "channel_cat_id": "e11455b218c06e7ae10cfa39bf43dc0f",
    "price": 29900,
    "stock": 20,
    "publish_shop": [{
        "title": "AI Workflow Automation Service",
        "content": "Professional AI workflow customization...",
        "service_support": "SDR"
    }]
}

response = client.create_product(product_data)
if response.get('code') == 200:
    print(f"Product created successfully: {response['data']['product_id']}")
else:
    print(f"Error: {response.get('msg')}")
```

## Configuration Requirements

### Environment Variables (Recommended)
```bash
export XIAN_YU_APP_KEY=203413189371893
export XIAN_YU_APP_SECRET=o9wl81dncmvby3ijpq7eur456zhgtaxs
```

### Dependencies
- Python 3.7+
- Standard library only (no external dependencies)
- Built-in modules: `os`, `json`, `time`, `hashlib`, `http.client`, `typing`

## Security Best Practices

### Credential Management
- Never commit credentials to version control
- Use environment variables or secure secret management systems
- Rotate credentials regularly
- Restrict API key permissions to minimum required scope

### Request Validation
- Validate all input parameters before API calls
- Implement proper error handling for failed requests
- Log errors without exposing sensitive information
- Monitor API usage patterns for anomalies

## Integration Notes

This skill serves as the foundational dependency for all other Xianyu-related skills:
- **xianyu-product-manager-skill**: Uses this client for product operations
- **xianyu-automation-skill**: Relies on this client for all API communications

## Version Information
- **Current Version**: 1.0.0
- **Compatibility**: Xianyu Guanjia Open Platform API v1
- **License**: MIT License

## Support and Maintenance

For issues or feature requests, please ensure you have:
- Valid Xianyu Guanjia developer credentials
- Proper API permissions enabled
- Latest version of this skill installed
- Complete error logs for troubleshooting