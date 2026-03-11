# 壁纸源配置

## 优先级

| 优先级 | 源            | 需要 Key   | 质量 | 说明              |
| ------ | ------------- | ---------- | ---- | ----------------- |
| 1      | Bing 每日壁纸 | 否         | 高   | 每日更新，4K 高清 |
| 2      | Unsplash API  | 是（可选） | 高   | 专业摄影，需配置  |
| 3      | Picsum        | 否         | 中   | 兜底方案          |

## Bing 每日壁纸

**免费**，不需要 API Key。

```python
# API 端点
BING_API = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8"

# 图片 URL 拼接
# 返回 JSON 中 images[0].url 为相对路径
# 完整 URL: https://cn.bing.com + url
```

### 参数说明

- `format=js` — 返回 JSON 格式
- `idx=0` — 0=今天，1=昨天，最大7
- `n=8` — 返回图片数量（1-8）
- `mkt=zh-CN` — 市场区域

### 响应示例

```json
{
  "images": [
    {
      "url": "/th?id=OHR.Example_ZH-CN1234_1920x1080.jpg",
      "title": "壁纸标题",
      "copyright": "版权信息"
    }
  ]
}
```

## Unsplash API（可选）

需要注册获取 Access Key：https://unsplash.com/developers

```bash
# 配置环境变量
export UNSPLASH_ACCESS_KEY="your_access_key"
```

### API 端点

```python
# 随机照片
UNSPLASH_RANDOM = "https://api.unsplash.com/photos/random"

# 请求头
headers = {
    "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
}

# 参数
params = {
    "query": "nature wallpaper",
    "orientation": "landscape",
    "content_filter": "high"
}
```

### 免费额度

- 50 次/小时（Demo）
- 5000 次/小时（Production，需申请）

## Picsum（兜底）

**免费**，无需配置。

```python
# 随机图片
PICSUM_URL = "https://picsum.photos/3840/2160?random={seed}"

# 指定图片 ID
PICSUM_ID_URL = "https://picsum.photos/id/{id}/3840/2160"
```

### 参数

- `?grayscale` — 灰度
- `?blur={1-10}` — 模糊程度

## 在代码中配置

编辑 `scripts/change-wallpaper.py` 中的 `WALLPAPER_SOURCES`：

```python
WALLPAPER_SOURCES = {
    "bing": {
        "api": "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1",
        "base_url": "https://cn.bing.com",
        "priority": 1
    },
    "unsplash": {
        "api": "https://api.unsplash.com/photos/random",
        "requires_key": True,
        "priority": 2
    },
    "picsum": {
        "url": "https://picsum.photos/3840/2160?random={seed}",
        "priority": 3
    }
}
```
