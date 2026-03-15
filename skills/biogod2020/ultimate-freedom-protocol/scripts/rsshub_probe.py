import json
from curl_cffi import requests
from lxml import html

def rsshub_penetration():
    print("--- [SOTA Pivot: RSSHub Intel Extraction] ---")
    # 小lin说的 B 站 UID
    mid = 392025345
    
    # 尝试多个公共高信誉 RSSHub 实例
    # 这些实例通常部署在 Vercel/Fly.io/Zeabur 等高信誉平台
    nodes = [
        f"https://rsshub.app/bilibili/user/video/{mid}",
        f"https://rss.lif35.com/bilibili/user/video/{mid}",
        f"https://rsshub.rssbuddy.com/bilibili/user/video/{mid}"
    ]
    
    for node in nodes:
        print(f"正在通过节点中转获取情报: {node}")
        try:
            # 同样使用 SOTA 协议模拟，确保节点本身不反爬我们
            r = requests.get(node, impersonate="chrome124", timeout=20)
            
            if r.status_code == 200:
                print("!!! 中转成功 !!! 正在解析 XML 情报流...")
                # RSSHub 返回的是 XML 格式
                tree = html.fromstring(r.content)
                # 提取 <title> 标签（排除频道标题）
                titles = tree.xpath("//item/title/text()")
                
                if titles:
                    return {
                        "status": "success",
                        "node_used": node,
                        "latest_videos": [t.strip() for t in titles[:5]]
                    }
            else:
                print(f"节点返回异常: {r.status_code}")
        except Exception as e:
            print(f"连接节点失败: {e}")
            
    return {"status": "all_nodes_failed"}

if __name__ == "__main__":
    res = rsshub_penetration()
    print(json.dumps(res, indent=2, ensure_ascii=False))
