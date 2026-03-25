# FB GraphQL Response Patterns

Facebook's internal GraphQL API returns posts in nested structures. The exact schema
shifts over time, so treat these as patterns to search, not guaranteed paths.

## Interception Setup

```python
responses = []

async def capture_response(response):
    if "graphql" in response.url and response.status == 200:
        try:
            data = await response.json()
            responses.append(data)
        except Exception:
            pass

page.on("response", capture_response)
await page.goto(group_url, wait_until="domcontentloaded")
await asyncio.sleep(6)  # allow feed to populate
```

## Extracting Posts from Responses

GraphQL responses are deeply nested. Walk them recursively:

```python
import json, re

def walk(obj, depth=0):
    """Recursively yield all dict nodes that look like posts."""
    if depth > 20:
        return
    if isinstance(obj, dict):
        # Post nodes typically have these keys together
        if "creation_time" in obj and ("url" in obj or "permalink_url" in obj):
            yield obj
        for v in obj.values():
            yield from walk(v, depth + 1)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk(item, depth + 1)

for resp in responses:
    for node in walk(resp):
        post_url = node.get("url") or node.get("permalink_url", "")
        created_ts = node.get("creation_time", 0)
        # Post text lives in various locations:
        text = (
            node.get("message", {}).get("text", "") or
            node.get("story", {}).get("message", {}).get("text", "") or
            node.get("comet_sections", {}).get("message", {}).get("story", {}).get("message", {}).get("text", "") or
            ""
        )
        author = (
            node.get("actor", {}).get("name", "") or
            node.get("author", {}).get("name", "") or
            ""
        )
```

## Key Fields

| Field | Location in node |
|-------|-----------------|
| Post text | `message.text` or `story.message.text` |
| Post URL | `url` or `permalink_url` |
| Timestamp | `creation_time` (Unix epoch) |
| Author | `actor.name` or `author.name` |
| Post ID | `id` or `post_id` |

## Age Filtering

```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc).timestamp()
age_days = (now - created_ts) / 86400

if age_days > MAX_AGE_DAYS:
    continue  # skip old posts
```

## Debugging Tips

- Log all raw graphql responses to a file during development
- Filter by `len(json.dumps(resp)) > 1000` to skip tiny/empty responses
- FB often returns the same post in multiple responses — deduplicate by URL
- If you get 0 results, check: are you intercepting BEFORE navigation? Yes — register handler first.
- `blob:` URLs in responses are not real post URLs — skip them

## Deduplication

```python
seen_urls = set()
posts = []
for node in walk(resp):
    url = node.get("url") or node.get("permalink_url", "")
    if url and url not in seen_urls and "facebook.com" in url:
        seen_urls.add(url)
        posts.append(node)
```
