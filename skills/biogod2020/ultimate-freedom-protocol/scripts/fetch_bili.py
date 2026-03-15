import json
import os
import sys
import time
from DrissionPage import ChromiumPage, ChromiumOptions

def get_bili_videos(url):
    print(f"--- [D-Mode: Bilibili Scraping] ---")
    co = ChromiumOptions().set_argument('--no-sandbox').set_argument('--headless=new')
    browser_path = '/home/jiahao/.pixi/bin/google-chrome-stable'
    if os.path.exists(browser_path):
        co.set_browser_path(browser_path)
    
    try:
        page = ChromiumPage(co)
        page.get(url)
        print("Waiting for page hydration...")
        page.wait.load_start()
        
        # B站空间页面需要一定时间加载视频列表
        time.sleep(5)
        
        # 抓取视频标题
        # 小lin说的视频列表选择器通常是 .list-list .title
        titles = page.eles('.list-list .title')
        if not titles:
            # 备选选择器
            titles = page.eles('tag:a@class^title')
            
        video_list = [t.text for t in titles[:5]]
        
        res = {
            "status": "success",
            "channel": "小lin说",
            "latest_videos": video_list
        }
        page.quit()
        return res
    except Exception as e:
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    target_url = "https://space.bilibili.com/392025345/video"
    print(json.dumps(get_bili_videos(target_url), indent=2, ensure_ascii=False))
