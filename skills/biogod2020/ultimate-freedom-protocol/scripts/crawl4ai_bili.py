import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def crawl_bili_sota():
    print("--- [Crawl4AI: Bilibili Advanced Stealth v2] ---")
    
    # 修正 v0.8.0 版本的配置格式
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium"
    )
    
    run_config = CrawlerRunConfig(
        cache_mode="bypass",
        wait_for_images=False,
        js_code="window.scrollTo(0, 500);",
        # 针对 B 站视频列表的 SOTA 等待策略
        wait_for="css:a.title", 
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        url = "https://space.bilibili.com/392025345/video"
        print(f"正在通过分布式 Playwright 节点访问: {url}")
        
        result = await crawler.arun(url=url, config=run_config)
        
        if result.success:
            print("!!! 抓取成功 !!!")
            return {
                "status": "success",
                "title": result.metadata.get('title'),
                "content_peek": result.markdown[:1000]
            }
        else:
            return {"status": "error", "error_log": result.error_message}

if __name__ == "__main__":
    try:
        res = asyncio.run(crawl_bili_sota())
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "exception", "msg": str(e)}, indent=2))
