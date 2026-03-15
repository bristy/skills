import os
import subprocess
import time
import json
from DrissionPage import ChromiumPage, ChromiumOptions

def solo_bili_mission():
    print("--- [Solo Mission: Bilibili In-Sandbox Scrape] ---")
    
    # 1. 强制清理
    os.system("pkill -9 chrome")
    os.system("pkill -9 Xvfb")
    
    # 2. 构造单兵启动命令 (集成 Xvfb)
    chrome_path = "/home/jiahao/.pixi/bin/google-chrome-stable"
    user_data = "/tmp/solo_bili_data"
    os.system(f"rm -rf {user_data}")
    
    # 启动命令：使用 xvfb-run 包裹
    cmd = [
        "xvfb-run", "--server-args=-screen 0 1920x1080x24",
        chrome_path, "--headless=new", "--no-sandbox",
        "--remote-debugging-port=9444", f"--user-data-dir={user_data}",
        "--disable-gpu", "--disable-dev-shm-usage"
    ]
    
    print("正在沙箱内空降浏览器...")
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(8) # 等待冷启动
    
    try:
        # 3. 直接接管
        page = ChromiumPage(addr_or_opts="127.0.0.1:9444")
        print("!!! 接管成功 !!! 正在强行浏览 B 站空间...")
        
        page.get("https://space.bilibili.com/392025345/video")
        # 深度等待 B 站复杂的异步脚本执行完毕
        page.wait.load_start()
        time.sleep(12) 
        
        # 4. 视觉层提取 (即使选择器变了，A 标签的文本是很难骗人的)
        print("正在进行全页面深度扫描...")
        
        # 针对小lin说的视频标题，使用更精准的选择器
        titles = page.eles('tag:a@class^title')
        if not titles:
            # Fallback
            titles = page.eles('tag:a@href^//www.bilibili.com/video/')
            
        video_list = [t.text for t in titles if len(t.text) > 5][:5]
        
        print(f"任务达成：已捕获 {len(video_list)} 条视频。")
        page.quit()
        return {"status": "success", "videos": video_list}
        
    except Exception as e:
        return {"status": "error", "msg": str(e)}
    finally:
        p.terminate()

if __name__ == "__main__":
    print(json.dumps(solo_bili_mission(), indent=2, ensure_ascii=False))
