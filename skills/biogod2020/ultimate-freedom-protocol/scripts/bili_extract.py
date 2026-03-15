import json
import re
from curl_cffi import requests

def extract_bili_videos():
    print("--- [Bilibili Stealth Extractor: Moving Mode] ---")
    url = "https://m.bilibili.com/space/392025345"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
    }

    try:
        r = requests.get(url, headers=headers, impersonate="chrome110", timeout=20)
        
        if r.status_code == 200:
            # 使用更鲁棒的正则捕获视频数据
            # 移动端 B 站的视频信息通常在 "list": [...] 结构中
            titles = re.findall(r'"title"\s*:\s*"(.*?)"', r.text)
            
            # 过滤掉非视频标题（如用户名、导航栏等）
            # 小lin说的视频标题通常较长且不包含 '小Lin说' 自身
            clean_titles = []
            for t in titles:
                if len(t) > 5 and t not in ["小Lin说", "视频", "动态", "投稿"]:
                    clean_titles.append(t)
            
            return {
                "status": "success",
                "latest_videos": clean_titles[:5]
            }
        else:
            return {"status": "blocked", "code": r.status_code}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    res = extract_bili_videos()
    print(json.dumps(res, indent=2, ensure_ascii=False))
