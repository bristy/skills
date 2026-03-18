"""
Content Claw - Autonomous Topic Discovery

Discovers trending topics relevant to a brand using Exa search and
Playwright-based scraping of Reddit and X/Twitter.

Usage:
    uv run discover_topics.py <brand-dir> [--reddit-cookie <path>] [--x-cookie <path>]

Environment:
    EXA_API_KEY - Required. Set in .env file.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from env import load_env
from browser import create_browser_context


def load_brand_graph(brand_dir: str) -> dict:
    """Load all YAML files from a brand graph directory."""
    import yaml
    brand_path = Path(brand_dir)
    graph = {}
    for f in brand_path.glob("*.yaml"):
        with open(f) as fh:
            data = yaml.safe_load(fh)
            if data:
                graph[f.stem] = data
    return graph


def plan_queries(brand_graph: dict) -> dict:
    """Generate search queries from brand graph context."""
    identity = brand_graph.get("identity", {})
    audience = brand_graph.get("audience", {})
    strategy = brand_graph.get("strategy", {})

    keywords = strategy.get("niche_keywords", [])
    interests = audience.get("interests", [])
    positioning = identity.get("positioning", "")
    pain_points = audience.get("pain_points", [])

    keyword_str = " ".join(keywords[:5]) if keywords else positioning
    audience_str = " ".join(interests[:3]) if interests else ""

    exa_queries = [
        f"trending {keyword_str} news",
        f"{keyword_str} new tools launches announcements",
        f"{keyword_str} {audience_str} insights analysis",
    ]
    if pain_points:
        exa_queries.append(f"{pain_points[0]} solutions {keyword_str}")

    return {
        "exa_queries": exa_queries,
        "reddit_queries": [keyword_str],
        "x_queries": [keyword_str],
    }


def search_exa(queries: list[str], num_results: int = 10) -> list[dict]:
    """Search Exa for trending content."""
    from exa_py import Exa

    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return [{"error": "EXA_API_KEY not set"}]

    exa = Exa(api_key=api_key)
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00.000Z")

    results = []
    for query in queries:
        try:
            response = exa.search(
                query,
                type="auto",
                num_results=num_results,
                start_published_date=week_ago,
                contents={
                    "text": {"maxCharacters": 1500},
                    "highlights": {"maxCharacters": 300},
                    "summary": {"query": "what is the main topic and why does it matter"},
                },
            )
            for r in response.results:
                results.append({
                    "title": r.title,
                    "url": r.url,
                    "published_date": r.published_date,
                    "summary": getattr(r, "summary", ""),
                    "highlights": getattr(r, "highlights", []),
                    "text_preview": (r.text or "")[:500],
                    "score": r.score,
                    "source": "exa",
                    "query": query,
                })
        except Exception as e:
            results.append({"error": str(e), "query": query, "source": "exa"})

    return results


def scrape_reddit(queries: list[str], cookie_path: str | None = None) -> list[dict]:
    """Scrape Reddit for trending discussions."""
    results = []
    try:
        with create_browser_context(cookie_path) as (page, context, browser):
            for query in queries:
                try:
                    url = f"https://www.reddit.com/search/?q={query}&sort=hot&t=week"
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)

                    links = page.eval_on_selector_all(
                        'a[href*="/comments/"]',
                        "els => els.map(el => ({href: el.href, text: el.textContent})).slice(0, 10)"
                    )

                    seen_urls = set()
                    for link in links:
                        link_url = link.get("href", "")
                        title = link.get("text", "").strip()
                        if not link_url or not title or len(title) < 10 or link_url in seen_urls:
                            continue
                        seen_urls.add(link_url)
                        results.append({
                            "title": title, "url": link_url, "source": "reddit",
                            "query": query, "text_preview": "", "summary": "",
                        })
                except Exception as e:
                    results.append({"error": str(e), "query": query, "source": "reddit"})
    except Exception as e:
        results.append({"error": f"Browser launch failed: {e}", "source": "reddit"})

    return results


def scrape_x(queries: list[str], cookie_path: str | None = None) -> list[dict]:
    """Scrape X/Twitter for trending discussions."""
    results = []
    try:
        with create_browser_context(cookie_path) as (page, context, browser):
            for query in queries:
                try:
                    url = f"https://x.com/search?q={query}&src=typed_query&f=top"
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(5000)

                    tweets = page.eval_on_selector_all(
                        'article[data-testid="tweet"]',
                        """els => els.slice(0, 10).map(el => {
                            const textEl = el.querySelector('div[data-testid="tweetText"]');
                            const linkEl = el.querySelector('a[href*="/status/"]');
                            const authorEl = el.querySelector('div[dir="ltr"] > span');
                            return {
                                text: textEl ? textEl.innerText : '',
                                url: linkEl ? linkEl.href : '',
                                author: authorEl ? authorEl.innerText : ''
                            };
                        })"""
                    )

                    for tweet in tweets:
                        text = tweet.get("text", "").strip()
                        tweet_url = tweet.get("url", "")
                        if not text or not tweet_url:
                            continue
                        results.append({
                            "title": f"@{tweet.get('author', 'unknown')}: {text[:80]}",
                            "url": tweet_url, "text_preview": text[:500],
                            "source": "x", "query": query, "summary": "",
                        })
                except Exception as e:
                    results.append({"error": str(e), "query": query, "source": "x"})
    except Exception as e:
        results.append({"error": f"Browser launch failed: {e}", "source": "x"})

    return results


def deduplicate(topics: list[dict]) -> list[dict]:
    """Deduplicate by URL and title similarity."""
    seen_urls = set()
    seen_titles = set()
    deduped = []
    for topic in topics:
        if "error" in topic:
            continue
        url = topic.get("url", "")
        title = topic.get("title", "").lower().strip()
        if url in seen_urls:
            continue
        title_key = title[:40]
        if title_key and title_key in seen_titles:
            continue
        if url:
            seen_urls.add(url)
        if title_key:
            seen_titles.add(title_key)
        deduped.append(topic)
    return deduped


def score_topics(topics: list[dict], brand_graph: dict) -> list[dict]:
    """Score topics by relevance to brand graph."""
    strategy = brand_graph.get("strategy", {})
    audience = brand_graph.get("audience", {})
    identity = brand_graph.get("identity", {})

    keywords = set()
    for k in strategy.get("niche_keywords", []):
        keywords.update(k.lower().split())
    for k in audience.get("interests", []):
        keywords.update(k.lower().split())
    keywords.update(identity.get("positioning", "").lower().split())
    keywords -= {"the", "a", "an", "and", "or", "for", "to", "in", "of", "is", "with"}

    for topic in topics:
        text = f"{topic.get('title', '')} {topic.get('summary', '')} {topic.get('text_preview', '')}".lower()
        matches = sum(1 for k in keywords if k in text)
        topic["relevance_score"] = min(100, int((matches / max(len(keywords), 1)) * 100))

    topics.sort(key=lambda t: t.get("relevance_score", 0), reverse=True)
    return topics


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: discover_topics.py <brand-dir> [--reddit-cookie <path>] [--x-cookie <path>]"}), file=sys.stderr)
        sys.exit(1)

    load_env()

    brand_dir = sys.argv[1]
    reddit_cookie = None
    x_cookie = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--reddit-cookie" and i + 1 < len(args):
            reddit_cookie = args[i + 1]
            i += 2
        elif args[i] == "--x-cookie" and i + 1 < len(args):
            x_cookie = args[i + 1]
            i += 2
        else:
            i += 1

    brand_graph = load_brand_graph(brand_dir)
    if not brand_graph:
        print(json.dumps({"error": f"No brand graph found at {brand_dir}"}), file=sys.stderr)
        sys.exit(1)

    queries = plan_queries(brand_graph)
    all_topics = []

    exa_results = search_exa(queries["exa_queries"])
    all_topics.extend(exa_results)

    reddit_results = scrape_reddit(queries["reddit_queries"], reddit_cookie)
    all_topics.extend(reddit_results)

    if x_cookie:
        x_results = scrape_x(queries["x_queries"], x_cookie)
        all_topics.extend(x_results)

    topics = deduplicate(all_topics)
    topics = score_topics(topics, brand_graph)

    output = {
        "brand": brand_graph.get("identity", {}).get("name", "unknown"),
        "discovered_at": datetime.now().isoformat(),
        "query_plan": queries,
        "topic_count": len(topics),
        "topics": topics,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
