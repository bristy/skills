import json
import re
from curl_cffi import requests

def bili_native_ip_probe():
    print("--- [Bilibili Probe: Native VPS IP Mode] ---")
    url = "https://m.bilibili.com/space/392025345"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.google.com/"
    }

    try:
        # 使用原生 IP 进行 CFFI 突防
        r = requests.get(url, headers=headers, impersonate="chrome110", timeout=20)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            # 尝试通过正则表达式在 HTML 文本中直接定位视频标题
            # 这种方法虽然原始，但在数据包被加密/截断时最有效
            
            # 搜索包含 "title":"..." 的 JSON 片段
            raw_titles = re.findall(r'\"title\"\:\"(.*?)\"', r.text)
            
            clean_list = []
            for t in raw_titles:
                # 排除通用 UI 词汇
                if len(t) > 6 and t not in ["小Lin说", "哔哩哔哩", "bilibili"]:
                    # 解码 unicode
                    try:
                        t_decoded = t.encode('utf-8').decode('unicode_escape')
                        if t_decoded not in clean_list:
                            clean_list.append(t_decoded)
                    except:
                        if t not in clean_list:
                            clean_list.append(t)
            
            return {
                "status": "success",
                "ip_used": "198.23.155.120 (Native)",
                "latest_videos": clean_list[:5]
            }
        else:
            return {"status": "blocked", "code": r.status_code}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    res = bili_native_ip_probe()
    print(json.dumps(res, indent=2, ensure_ascii=False))
