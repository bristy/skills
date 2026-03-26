# Error Codes Reference

## Common Errors

### Authentication Errors

| Code | Message | Description | Solution |
|------|---------|-------------|----------|
| 1 | Unknown error | Unknown error occurred | Retry request, contact support if persistent |
| 2 | Service temporarily unavailable | Service is temporarily down | Retry request, contact support if persistent |
| 3 | Unsupported openapi method | API endpoint does not exist | Check URL, remove non-English characters |
| 4 | Open api request limit reached | Cluster quota exceeded | Retry request, contact support if persistent |
| 6 | No permission to access data | No API access permission | Enable API in Baidu Cloud console |
| 14 | IAM Certification failed | IAM authentication failed | Check sign generation or use AK/SK |
| 17 | Open api daily request limit reached | Daily quota exceeded | Purchase quota or wait for reset |
| 18 | Open api qps request limit reached | QPS limit exceeded | Reduce request frequency |
| 19 | Open api total request limit reached | Total quota exceeded | Purchase additional quota |
| 100 | Invalid parameter | Invalid access_token | Re-obtain access token |
| 110 | Access token invalid or no longer valid | Token is invalid | Token expires after 30 days, get new token |
| 111 | Access token expired | Token has expired | Token expires after 30 days, get new token |

### File Errors

| Code | Message | Description | Solution |
|------|---------|-------------|----------|
| 216200 | empty file or fileurl | File or URL is empty | Provide file_data or file_url |
| 216201 | file format error | Unsupported file format | Use supported format (PDF, Word, Excel, etc.) |
| 216202 | file size error | File size exceeds limit | Reduce file size (max 50MB or 300MB for PDF URL) |

### Task Processing Errors

| Code | Message | Description | Solution |
|------|---------|-------------|----------|
| 282000 | internal error | Task processing failed | Retry or contact support |
| 282001 | template not found | Contract type not found | Check contract type name |
| 282003 | missing parameters | Required parameters missing | Check required parameters |
| 282005 | quota exceed error | Quota exceeded | Request quota increase |
| 282006 | check user auth error | User permission check failed | Verify user permissions |
| 282007 | task not exist, please check task id | Task does not exist | Check task_id |
| 282018 | Service busy | Service is busy | Reduce request frequency |

### URL Errors

| Code | Message | Description | Solution |
|------|---------|-------------|----------|
| 282111 | url format illegal | URL format is invalid | Check URL format |
| 282112 | url download timeout | URL download timed out | Check URL accessibility |
| 282113 | url response invalid | URL returned invalid response | Check URL response |
| 282114 | url size error | URL length exceeds 1024 bytes | Shorten URL |

### Parameter Errors

| Code | Message | Description | Solution |
|------|---------|-------------|----------|
| 283016 | parameters value error | Invalid parameter value | Check parameter format and values |

## Error Response Format

```json
{
  "error_code": 110,
  "error_msg": "Access token invalid or no longer valid"
}
```

## Handling Errors

### Retry Strategy

1. **Transient errors (1, 2, 4, 282000, 282018)**: Retry with exponential backoff
2. **Authentication errors (110, 111)**: Re-obtain access token
3. **Quota errors (17, 18, 19, 282005)**: Wait or purchase additional quota
4. **Parameter errors**: Fix the issue and retry

### Exponential Backoff

```python
import time

def retry_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            wait_time = 2 ** i  # 1s, 2s, 4s
            time.sleep(wait_time)
```

### Token Refresh

```python
# Check if token is expired (30-day validity)
def ensure_valid_token(client):
    try:
        # Try a simple API call
        client.query_task("test-task-id")
    except Exception as e:
        if "110" in str(e) or "111" in str(e):
            # Token expired, get new one
            client.access_token = client._get_access_token()
```

## Getting Help

- [Submit Ticket](https://ticket.bce.baidu.com/?_=1648086674827&fromai=1#/ticket/create~productId=96&questionId=1306&channel=2)
- [Permission Diagnostic Tool](https://console.bce.baidu.com/tools/#/aiInterfacePermissions)
- [Baidu Cloud Console](https://console.bce.baidu.com/ai/)