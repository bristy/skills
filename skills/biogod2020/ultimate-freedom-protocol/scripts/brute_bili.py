import json
import websocket
import time
import requests

def brute_force_bili():
    print("--- [D-Mode: Bilibili Brute Force] ---")
    port = 9223 
    
    try:
        # 1. 连接内核
        pages = requests.get(f"http://127.0.0.1:{port}/json").json()
        target_page = next((p for p in pages if p['type'] == 'page'), None)
        ws_url = target_page['webSocketDebuggerUrl'].replace(':9222', ':9223')
        ws = websocket.create_connection(ws_url)
        
        msg_id = 1
        def send(method, params={}):
            nonlocal msg_id
            ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
            msg_id += 1
            while True:
                res = json.loads(ws.recv())
                if res.get('id') == msg_id - 1: return res

        # 2. 导航至 B 站空间 (PC 端，虽然封锁严，但如果能通，数据最全)
        print("正在命令浏览器加载 B 站空间...")
        send("Page.navigate", {"url": "https://space.bilibili.com/392025345/video"})
        
        # 3. 深度等待渲染
        time.sleep(10)
        
        # 4. 暴力提取所有 A 标签文本
        print("正在执行 DOM 穿透提取...")
        res = send("Runtime.evaluate", {
            "expression": "[...document.querySelectorAll('a')].map(e => e.innerText).filter(t => t.length > 10)",
            "returnByValue": True
        })
        
        raw_titles = res['result']['result'].get('value', [])
        
        # 5. 过滤出真正的视频标题
        videos = [t for t in raw_titles if "小Lin说" not in t and "分钟" not in t and "观看" not in t][:5]
        
        ws.close()
        return {"status": "success", "videos": videos}
        
    except Exception as e:
        return {"status": "error", "msg": str(e)}

if __name__ == "__main__":
    print(json.dumps(brute_force_bili(), indent=2, ensure_ascii=False))
