import json
import os
import time
from DrissionPage import ChromiumPage, ChromiumOptions

def sota_bili_simulate():
    print("--- [SOTA Bilibili Simulator: MacBook Identity] ---")
    
    # 1. 极其严苛的指纹伪装
    co = ChromiumOptions()
    co.set_argument('--no-sandbox')
    co.set_argument('--headless=new')
    co.set_argument('--disable-blink-features=AutomationControlled') # 关键：移除 WebDriver 痕迹
    co.set_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    co.set_argument('--lang=zh-CN,zh;q=0.9')
    
    # 注入真实的渲染参数
    co.set_argument('--window-size=1920,1080')
    
    browser_path = '/home/jiahao/.pixi/bin/google-chrome-stable'
    if os.path.exists(browser_path):
        co.set_browser_path(browser_path)
    
    # 使用独立的 UserData 避免 Cookie 污染
    user_data = "/tmp/bili_sota_sim"
    co.set_paths(user_data_path=user_data)
    
    try:
        page = ChromiumPage(co)
        # 2. 访问主站获取基础身份令牌
        print("正在获取主站身份特征...")
        page.get("https://www.bilibili.com")
        page.wait(3)
        
        # 3. 突袭个人空间视频页
        target = "https://space.bilibili.com/392025345/video"
        print(f"正在以真实用户身份进入空间: {target}")
        page.get(target)
        
        # 关键：模拟人类滚动行为，触发异步加载
        print("模拟人类查阅视频流...")
        page.scroll.down(600)
        time.sleep(5)
        page.scroll.up(200)
        
        # 4. 抓取数据
        # 在 MacBook 模拟模式下，B 站通常会展示标准的 List
        videos = []
        eles = page.eles('tag:a@class^title')
        if not eles:
            eles = page.eles('tag:a@href^//www.bilibili.com/video/')
            
        for e in eles[:5]:
            if len(e.text) > 5:
                videos.append(e.text)
                
        # 截图存证
        ss_path = "/home/jiahao/.openclaw/workspace/skills/drission-sota-toolkit/assets/screenshots/BILI_SIMULATED.png"
        page.get_screenshot(path=ss_path)
        
        page.quit()
        return {"status": "success", "videos": videos, "proof": ss_path}
        
    except Exception as e:
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    res = sota_bili_simulate()
    print(json.dumps(res, indent=2, ensure_ascii=False))
