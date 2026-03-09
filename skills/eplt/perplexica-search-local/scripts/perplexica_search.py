#!/usr/bin/env python3
"""
Perplexica Search Skill
AI-powered search using local Perplexica instance
"""

import argparse
import json
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def fetch_providers(base_url):
    """Fetch available providers and models from Perplexica"""
    try:
        req = Request(f"{base_url}/api/providers")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("providers", [])
    except Exception as e:
        print(f"❌ Error fetching providers: {e}", file=sys.stderr)
        print(f"   Make sure Perplexica is running at {base_url}", file=sys.stderr)
        sys.exit(1)


def select_model(providers, model_type="chatModels", preferred=None):
    """Select a model from available providers"""
    for provider in providers:
        models = provider.get(model_type, [])
        if preferred:
            for model in models:
                if preferred.lower() in model.get("key", "").lower():
                    return provider["id"], model["key"]
        if models:
            return provider["id"], models[0]["key"]
    return None, None


def search(query, base_url, chat_provider_id, chat_model_key, 
           embed_provider_id, embed_model_key, mode="balanced", 
           sources=None, instructions=None, history=None, stream=False):
    """Execute search via Perplexica API"""
    
    if sources is None:
        sources = ["web"]
    
    payload = {
        "chatModel": {
            "providerId": chat_provider_id,
            "key": chat_model_key
        },
        "embeddingModel": {
            "providerId": embed_provider_id,
            "key": embed_model_key
        },
        "optimizationMode": mode,
        "sources": sources,
        "query": query,
        "stream": stream
    }
    
    if instructions:
        payload["systemInstructions"] = instructions
    
    if history:
        payload["history"] = history
    
    try:
        start_time = time.time()
        req = Request(
            f"{base_url}/api/search",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            took_ms = int((time.time() - start_time) * 1000)
            result["took_ms"] = took_ms
            result["model_used"] = chat_model_key
            return result
            
    except HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        try:
            error_body = json.loads(e.read().decode())
            print(f"   Details: {error_body}", file=sys.stderr)
        except:
            pass
        sys.exit(1)
    except URLError as e:
        print(f"❌ Connection Error: {e.reason}", file=sys.stderr)
        print(f"   Make sure Perplexica is running at {base_url}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Search failed: {e}", file=sys.stderr)
        sys.exit(1)


def format_output(result, query, mode, sources, json_output=False):
    """Format search results for display"""
    
    if json_output:
        print(json.dumps(result, indent=2))
        return
    
    answer = result.get("message", result.get("answer", "No answer generated"))
    sources_list = result.get("sources", [])
    took_ms = result.get("took_ms", 0)
    model_used = result.get("model_used", "unknown")
    
    print(f"\n🔍 Query: {query}")
    print(f"⚡ Mode: {mode} | Sources: {', '.join(sources)}")
    print(f"🤖 Model: {model_used} | Time: {took_ms}ms\n")
    print("📄 Answer:")
    print("─" * 60)
    print(answer)
    print("─" * 60)
    
    if sources_list:
        print(f"\n📚 Sources ({len(sources_list)}):")
        for i, source in enumerate(sources_list, 1):
            metadata = source.get("metadata", {})
            title = metadata.get("title", "Untitled")
            url = metadata.get("url", "No URL")
            print(f"[{i}] {title}")
            print(f"    {url}\n")
    else:
        print("\n⚠️  No sources cited")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Perplexica AI-powered search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What is quantum computing?"
  %(prog)s "Latest AI developments" --mode quality
  %(prog)s "ML papers" --sources academic
  %(prog)s "Python tips" --json
        """
    )
    
    parser.add_argument("query", help="Search query")
    parser.add_argument("-u", "--url", default="http://localhost:3000",
                        help="Perplexica instance URL (default: http://localhost:3000)")
    parser.add_argument("-m", "--mode", choices=["speed", "balanced", "quality"],
                        default="balanced", help="Optimization mode")
    parser.add_argument("-s", "--sources", default="web",
                        help="Search sources: web,academic,discussions (comma-separated)")
    parser.add_argument("--chat-model", help="Chat model key (e.g., gpt-4o-mini)")
    parser.add_argument("--embedding-model", help="Embedding model key")
    parser.add_argument("-i", "--instructions", help="Custom system instructions")
    parser.add_argument("--history", help="Conversation history as JSON array")
    parser.add_argument("-j", "--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--stream", action="store_true", help="Enable streaming")
    
    args = parser.parse_args()
    
    # Parse sources
    sources = [s.strip() for s in args.sources.split(",")]
    valid_sources = {"web", "academic", "discussions"}
    sources = [s for s in sources if s in valid_sources]
    if not sources:
        sources = ["web"]
    
    # Parse history
    history = None
    if args.history:
        try:
            history = json.loads(args.history)
        except json.JSONDecodeError:
            print("❌ Invalid JSON for --history", file=sys.stderr)
            sys.exit(1)
    
    # Fetch providers
    providers = fetch_providers(args.url)
    
    if not providers:
        print("❌ No providers found. Configure at least one model in Perplexica.", file=sys.stderr)
        sys.exit(1)
    
    # Select chat model
    chat_provider_id, chat_model_key = select_model(
        providers, "chatModels", args.chat_model
    )
    
    if not chat_provider_id:
        print("❌ No chat models available. Configure a provider in Perplexica.", file=sys.stderr)
        sys.exit(1)
    
    # Select embedding model
    embed_provider_id, embed_model_key = select_model(
        providers, "embeddingModels", args.embedding_model
    )
    
    if not embed_provider_id:
        print("❌ No embedding models available. Configure a provider in Perplexica.", file=sys.stderr)
        sys.exit(1)
    
    # Execute search
    result = search(
        query=args.query,
        base_url=args.url,
        chat_provider_id=chat_provider_id,
        chat_model_key=chat_model_key,
        embed_provider_id=embed_provider_id,
        embed_model_key=embed_model_key,
        mode=args.mode,
        sources=sources,
        instructions=args.instructions,
        history=history,
        stream=args.stream
    )
    
    # Output results
    format_output(result, args.query, args.mode, sources, args.json)


if __name__ == "__main__":
    main()
