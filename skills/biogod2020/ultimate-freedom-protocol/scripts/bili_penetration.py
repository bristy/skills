import json
import random
from curl_cffi import requests

def penetration_bili():
    print("--- [Bilibili Deep Penetration: Protocol Spoofer] ---")
    
    # 模拟 B 站 App 或 移动端浏览器的 Headers
    # 重点在于 sec-ch-ua 指纹和移动端特有的 Accept 头
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Ch-Ua": '"Google Chrome";v="124", "Chromium";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?1", # 模拟移动端
        "Sec-Ch-Ua-Platform": '"Android"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    }

    # B站移动端空间 URL
    target = "https://m.bilibili.com/space/392025345"
    
    try:
        # 使用 chrome110 栈进行 TLS 握手
        r = requests.get(target, headers=headers, impersonate="chrome110", timeout=20)
        
        print(f"突防结果: {r.status_code}")
        
        if r.status_code == 200:
            print("!!! 成功穿透 B 站移动端防火墙 !!!")
            # 在移动端 HTML 中提取视频标题
            # 移动端通常将数据序列化在 __INITIAL_STATE__ 中
            import re
            match = re.search(r'window\.__INITIAL_STATE__=(.*?);', r.text)
            if match:
                state = json.loads(match.group(1))
                # 尝试从 state 中提取视频列表
                print("成功解析页面状态机。")
                return {"status": "success", "data_found": True, "raw_peek": r.text[:200]}
            else:
                return {"status": "partial", "msg": "Page loaded but state data hidden."}
        else:
            return {"status": "blocked", "code": r.status_code}
            
    except Exception as e:
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    print(json.dumps(penetration_bili(), indent=2, ensure_ascii=False))
