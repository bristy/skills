import json
from curl_cffi import requests

def get_bili_api_videos(mid):
    print(f"--- [CFFI: Bilibili API Fetch] ---")
    # B站用户视频列表 API
    url = f"https://api.bilibili.com/x/space/wbi/arc/search?mid={mid}&ps=5&tid=0&pn=1&keyword=&order=pubdate"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": f"https://space.bilibili.com/{mid}/video",
        "Origin": "https://space.bilibili.com"
    }
    
    try:
        # 使用 impersonate 模拟真实浏览器
        r = requests.get(url, headers=headers, impersonate="chrome124", timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            if data['code'] == 0:
                vlist = data['data']['list']['vlist']
                videos = [v['title'] for v in vlist]
                return {"status": "success", "videos": videos}
            else:
                return {"status": "error", "msg": f"Bilibili API error code: {data['code']}"}
        else:
            return {"status": "error", "msg": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    # 小lin说的 MID 是 392025345
    print(json.dumps(get_bili_api_videos(392025345), indent=2, ensure_ascii=False))
