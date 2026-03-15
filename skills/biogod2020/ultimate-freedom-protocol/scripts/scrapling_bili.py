import json
from scrapling import Fetcher

def scrapling_bili_attempt():
    print("--- [Scrapling: Bilibili Deep Scrape] ---")
    url = "https://space.bilibili.com/392025345/video"
    
    try:
        # Scrapling 的 auto_match 会尝试各种逃逸技术
        fetcher = Fetcher(auto_match=True)
        response = fetcher.get(url)
        
        # 提取视频标题
        # B站标题通常在 i[@title] 或者是 a.title 中
        titles = response.css('a.title::text').all()
        if not titles:
            titles = response.xpath('//a[contains(@class, "title")]/text()').all()
            
        return {
            "status": "success",
            "videos": [t.strip() for t in titles[:5]]
        }
    except Exception as e:
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    print(json.dumps(scrapling_bili_attempt(), indent=2, ensure_ascii=False))
