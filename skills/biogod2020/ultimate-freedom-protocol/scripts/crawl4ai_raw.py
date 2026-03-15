import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def crawl_bili_raw():
    print("--- [Crawl4AI: Bilibili Raw Dump Mode] ---")
    
    browser_config = BrowserConfig(
        headless=True,
        # 模拟移动端身份
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    )
    
    run_config = CrawlerRunConfig(
        cache_mode="bypass",
        # 不等待特定元素，只等待网络空闲
        wait_until="networkidle",
        page_timeout=30000
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        url = "https://m.bilibili.com/space/392025345"
        print(f"正在对移动端进行原始数据提取: {url}")
        
        result = await crawler.arun(url=url, config=run_config)
        
        if result.success:
            print("!!! 原始数据捕获成功 !!!")
            # 在原始 markdown 中搜索可能的视频标题
            return {
                "status": "success",
                "raw_peek": result.markdown[:2000]
            }
        else:
            return {"status": "error", "msg": result.error_message}

if __name__ == "__main__":
    try:
        res = asyncio.run(crawl_bili_raw())
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(str(e))
