# Post Filter Logic

## Two-Stage Filter Architecture

Every post goes through this pipeline. ALL conditions must pass to be a match.

```
post_text
  → [1] Contains TRIGGER phrase?        No → skip
  → [2] Contains TOPIC keyword?         No → skip
  → [3] Headline matches EXCLUSION?     Yes → skip
  → [4] Matches SEEKING_WORK pattern?   Yes → skip
  → MATCH ✓
```

## Stage 1: Trigger Phrases (someone is hiring)

```python
TRIGGER_PHRASES = [
    "hiring", "looking for", "need a", "need an", "seeking",
    "searching for", "want to hire", "we're hiring", "we are hiring",
    "i'm hiring", "i am hiring", "open position", "job opportunity",
    "job opening", "looking to hire", "looking to bring on", "[hiring]",
]
```

## Stage 2: Topic Keywords (role matches target)

```python
TOPIC_KEYWORDS = [
    "csm", "client success manager", "client success managers",
    "csd", "client success director", "ascension", "renewals",
    "renewal", "retention", "customer success", "onboarding specialist",
]

# Short keywords (≤4 chars) need word-boundary matching to avoid false positives
import re
for kw in TOPIC_KEYWORDS:
    if len(kw) <= 4:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            matched = kw; break
    else:
        if kw in text_lower:
            matched = kw; break
```

## Stage 3: Exclusion Job Titles (different role, not our target)

Check only the **headline** (first 200 chars) to avoid false positives from body mentions.

```python
EXCLUSION_JOB_TITLES = [
    # Executive: "coo ", "cfo ", "cto ", "ceo ", "vice president"
    # Finance: "lending", "loan officer", "mortgage"  
    # Sales: "appointment setter", "high ticket closer"
    # Marketing: "copywriter", "media buyer", "ads manager", "seo "
    # Tech: "funnel builder", "wordpress ", "shopify "
    # Admin: "bookkeeper", "virtual assistant", "data analyst"
]

headline = text_lower[:200]
for excl in EXCLUSION_JOB_TITLES:
    if excl in headline:
        return None, None  # skip
```

## Stage 4: Seeking-Work Exclusions (they're offering services, not hiring)

These are people promoting themselves or their agency — NOT what we want.

```python
SEEKING_WORK_PHRASES = [
    "seeking work", "seeking clients", "looking for clients",
    "available for hire", "open to work", "open for work",
    "taking on new clients", "accepting new clients",
    "i build", "i create", "i specialize", "i offer", "i provide",
    "my services", "our services", "what you get:", "what we offer",
    "done for you", "done-for-you", "free audit", "free consultation",
    "fiverr", "upwork", "order now", "look no further",
]
```

## Returning Results

```python
def matches_filter(text: str) -> tuple[str | None, str | None]:
    """Returns (matched_trigger, matched_topic) or (None, None)."""
    text_lower = text.lower()
    
    trigger = next((p for p in TRIGGER_PHRASES if p in text_lower), None)
    if not trigger:
        return None, None
    
    headline = text_lower[:200]
    if any(e in headline for e in EXCLUSION_JOB_TITLES):
        return None, None
    
    if any(p in text_lower for p in SEEKING_WORK_PHRASES):
        return None, None
    
    topic = None
    for kw in TOPIC_KEYWORDS:
        if len(kw) <= 4:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                topic = kw; break
        else:
            if kw in text_lower:
                topic = kw; break
    
    if not topic:
        return None, None
    
    return trigger, topic
```

## Tuning Tips

- **Too many false positives?** Add more EXCLUSION_JOB_TITLES patterns
- **Missing real matches?** Add more TRIGGER_PHRASES or TOPIC_KEYWORDS
- **Keyword too broad?** Use word-boundary matching (`\b`) instead of substring
- **Test with real data** by logging all raw post texts to a file first, then tune filters offline
