import json
import os
import time
from DrissionPage import ChromiumPage, ChromiumOptions

def bili_network_listen():
    print("--- [SOTA Bilibili: Network Packet Interception] ---")
    
    co = ChromiumOptions().set_argument('--no-sandbox').set_argument('--headless=new')
    # 启用 CDP 网络监听
    
    try:
        page = ChromiumPage(co)
        # 1. 开启网络监听
        page.listen.start('api.bilibili.com/x/space/wbi/arc/search')
        
        # 2. 进入目标
        target = "https://space.bilibili.com/392025345/video"
        print(f"正在穿透并监听数据包: {target}")
        page.get(target)
        
        # 3. 模拟人类深度查阅，诱导数据包发出
        print("模拟深度查阅诱导请求...")
        for _ in range(3):
            page.scroll.down(400)
            time.sleep(3)
        
        # 4. 捕获并解析包
        packet = page.listen.wait()
        if packet:
            print("!!! 关键数据包截获成功 !!!")
            data = packet.response.body
            # 如果是压缩包或加密包，在此处通常会被 DrissionPage 自动处理为 dict
            if isinstance(data, dict) and data.get('code') == 0:
                vlist = data['data']['list']['vlist']
                videos = [v['title'] for v in vlist]
                page.quit()
                return {"status": "success", "videos": videos[:5]}
        
        page.quit()
        return {"status": "partial", "msg": "Page loaded but interceptor missed the pulse."}
        
    except Exception as e:
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    print(json.dumps(bili_network_listen(), indent=2, ensure_ascii=False))
