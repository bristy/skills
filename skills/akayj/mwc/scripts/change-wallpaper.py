#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#     "polars>=1.0.0",
#     "duckdb>=1.0.0",
#     "pyobjc-framework-Cocoa>=10.0",
# ]
# ///
"""
Mac 壁纸自动更换脚本
支持智能推荐和偏好学习

图片源优先级：
1. Bing 每日壁纸（免费、高清）
2. Unsplash API（需配置 Key）
3. Picsum（兆底）
"""

import subprocess
import urllib.request
import urllib.parse
import os
import random
import json
from datetime import datetime
from pathlib import Path

# 壁纸保存目录
WALLPAPER_DIR = Path.home() / "wallpaper-daily"
WALLPAPER_DIR.mkdir(exist_ok=True)

# 日志目录
LOG_DIR = WALLPAPER_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 偏好数据文件
PREFERENCES_FILE = WALLPAPER_DIR / "preferences.parquet"

# Unsplash API Key（可选，通过环境变量配置）
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# Unsplash 高质量图片 ID 池（无需 API Key）
UNSPLASH_PHOTO_IDS = {
    "nature": [
        "1470071459604-3b5ec3a7fe05", "1501854140884-074cf2b21d25",
        "1464822759023-fed622ff59b8", "1502083110173-b3544182ed71",
        "1472214103451-9374bd1c798e", "1441974231531-c6227db76b6e",
    ],
    "mountain": [
        "1506905925346-21bda4d32df4", "1454496522488-7a8e488e8606",
        "1519681393784-d120267933ba", "1464278533981-50106e6176b1",
        "1486870591958-9b9d0d1dda99", "1483728642387-6c3bdd6c93e5",
    ],
    "forest": [
        "1448375240586-882707db888b", "1542273917363-3b1e2e9c58c8",
        "1473448912268-2022ce9509d8", "1476231682828-37e571bc172f",
        "1425913397330-cf8af2ff40a1", "1440581572325-0bea30075d9d",
    ],
    "ocean": [
        "1505142468610-359e7d316be0", "1507525428034-b723cf961d3e",
        "1439405326854-014607f694d7", "1518837695005-2083093ee35b",
        "1484291470158-b8f8d608850d", "1468413253725-0d5181091126",
    ],
    "city": [
        "1480714378408-67cf0d13bc1b", "1514565131-fce0801e5785",
        "1477959858617-67f85cf4f1df", "1534430480872-3498386e7856",
        "1519501025264-65ba15a82390", "1444723121867-7a241cacace9",
    ],
    "space": [
        "1462331940025-496dfbfc7564", "1451187580459-43490279c0fa",
        "1419242902214-272b3f66ee7a", "1506318137071-a8e063b4bec0",
        "1465101162946-4377e57745c3", "1543722530-d2c3201371e7",
    ],
}

# 壁纸分类（用于 Picsum 和 Unsplash 查询）
CATEGORIES = ["nature", "mountain", "forest", "ocean", "city", "space"]

# Picsum 兆底源
PICSUM_SOURCES = {
    "nature": "https://picsum.photos/3840/2160?random={seed}&nature",
    "mountain": "https://picsum.photos/3840/2160?random={seed}&mountain",
    "forest": "https://picsum.photos/3840/2160?random={seed}&forest",
    "ocean": "https://picsum.photos/3840/2160?random={seed}&ocean",
    "city": "https://picsum.photos/3840/2160?random={seed}&city",
    "space": "https://picsum.photos/3840/2160?random={seed}&space",
}

COLOR_TONES = ["dark", "bright", "warm", "cool"]


def get_bing_wallpaper(random_from_recent: bool = True) -> dict | None:
    """
    获取 Bing 每日壁纸（优先级 1）
    
    Args:
        random_from_recent: 如果为 True，从过去 8 天的壁纸中随机选择一张
    """
    try:
        # Bing API 支持 idx=0-7（过去 8 天），n=8 一次获取多张
        if random_from_recent:
            api_url = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt=zh-CN"
        else:
            api_url = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=zh-CN"
        
        req = urllib.request.Request(api_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if data.get("images"):
            # 随机选择一张或取今天的
            if random_from_recent and len(data["images"]) > 1:
                img = random.choice(data["images"])
            else:
                img = data["images"][0]
            
            # 拼接完整 URL，并请求 4K 分辨率
            url = img["url"]
            # 尝试获取 4K 版本
            if "1920x1080" in url:
                url_4k = url.replace("1920x1080", "UHD")
            else:
                url_4k = url
            
            return {
                "url": f"https://cn.bing.com{url_4k}",
                "title": img.get("title", ""),
                "copyright": img.get("copyright", ""),
                "source": "bing"
            }
    except Exception as e:
        log_message(f"Bing 获取失败：{e}", "WARN")
    return None


def get_unsplash_wallpaper(category: str = "nature") -> dict | None:
    """
    获取 Unsplash 壁纸（优先级 2）
    
    使用预设的高质量图片 ID 池，无需 API Key
    """
    try:
        # 从 ID 池中随机选择
        ids = UNSPLASH_PHOTO_IDS.get(category, UNSPLASH_PHOTO_IDS["nature"])
        photo_id = random.choice(ids)
        
        # 直接构造 URL，请求 4K 分辨率
        url = f"https://images.unsplash.com/photo-{photo_id}?w=3840&h=2160&fit=crop&q=85"
        
        return {
            "url": url,
            "title": f"Unsplash {category}",
            "photo_id": photo_id,
            "source": "unsplash"
        }
    except Exception as e:
        log_message(f"Unsplash 获取失败：{e}", "WARN")
    return None


def get_picsum_wallpaper(category: str = "nature") -> dict | None:
    """获取 Picsum 壁纸（兆底方案）"""
    seed = random.randint(1, 10000)
    url_template = PICSUM_SOURCES.get(category, PICSUM_SOURCES["nature"])
    return {
        "url": url_template.format(seed=seed),
        "title": f"Picsum {category}",
        "source": "picsum"
    }


def log_message(message: str, level: str = "INFO") -> None:
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    
    # 写入日志文件
    log_file = LOG_DIR / f"change-wallpaper-{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")


def download_image(url: str, filepath: Path) -> bool:
    """下载图片"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        log_message(f"下载失败：{e}", "ERROR")
        return False


def refresh_desktop() -> bool:
    """
    刷新桌面以强制壁纸生效
    
    macOS Tahoe (26+) 的坑：设置壁纸后不会立即生效
    解决方案：重启 WallpaperAgent 进程
    """
    import time
    
    try:
        # 短暂延迟让系统有时间处理壁纸设置
        time.sleep(0.3)
        
        # macOS Tahoe: 重启 WallpaperAgent 让壁纸生效
        result = subprocess.run(
            ['killall', 'WallpaperAgent'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            log_message("✓ 已重启 WallpaperAgent，壁纸应已生效")
            return True
        else:
            # WallpaperAgent 可能不存在（旧版系统），回退到 Dock
            log_message("WallpaperAgent 未找到，尝试刷新 Dock", "WARN")
            result2 = subprocess.run(
                ['killall', 'Dock'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result2.returncode == 0:
                log_message("✓ 已刷新 Dock")
                return True
    except subprocess.TimeoutExpired:
        log_message("刷新超时", "WARN")
    except Exception as e:
        log_message(f"刷新出错：{e}", "WARN")
    
    return False


def set_wallpaper_all_displays(image_path: Path) -> bool:
    """
    设置所有显示器的壁纸
    
    使用 PyObjC 调用 NSWorkspace.setDesktopImageURL，
    然后重启 WallpaperAgent 让壁纸生效（macOS Tahoe 必须）
    """
    abs_path = str(image_path.absolute())
    
    # 方法 1：PyObjC + NSWorkspace（推荐）
    try:
        from AppKit import NSWorkspace, NSScreen
        from Foundation import NSURL
        
        url = NSURL.fileURLWithPath_(abs_path)
        workspace = NSWorkspace.sharedWorkspace()
        
        success_count = 0
        for screen in NSScreen.screens():
            result, error = workspace.setDesktopImageURL_forScreen_options_error_(
                url, screen, {}, None
            )
            if result:
                success_count += 1
                log_message(f"✓ 已设置壁纸到屏幕：{screen.localizedName()}")
            else:
                log_message(f"屏幕 {screen.localizedName()} 设置失败：{error}", "WARN")
        
        if success_count > 0:
            log_message(f"✓ 已设置壁纸到 {success_count} 个屏幕")
            refresh_desktop()
            return True
            
    except ImportError:
        log_message("PyObjC 未安装，回退到 desktoppr", "WARN")
    except Exception as e:
        log_message(f"NSWorkspace 方法失败：{e}", "WARN")
    
    # 方法 2：desktoppr（回退方案，需 brew install desktoppr）
    try:
        result = subprocess.run(
            ['desktoppr', abs_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            log_message(f"✓ 已设置壁纸 (desktoppr)")
            refresh_desktop()
            return True
    except FileNotFoundError:
        log_message("desktoppr 未安装，请运行: brew install --cask desktoppr", "ERROR")
    except subprocess.TimeoutExpired:
        log_message("设置壁纸超时", "ERROR")
    except Exception as e:
        log_message(f"设置壁纸失败：{e}", "ERROR")
    
    return False


def save_preference(
    wallpaper_path: str,
    rating: int,
    tags: list[str],
    color_tone: str,
    category: str,
    source_url: str
) -> None:
    """保存用户偏好"""
    import polars as pl
    
    # 创建新记录
    new_record = pl.DataFrame({
        "date": [datetime.now()],
        "wallpaper_path": [wallpaper_path],
        "rating": [rating],
        "tags": [tags],
        "color_tone": [color_tone],
        "category": [category],
        "source_url": [source_url],
    })
    
    # 读取或创建偏好数据
    if PREFERENCES_FILE.exists():
        try:
            existing_data = pl.read_parquet(PREFERENCES_FILE)
            combined = pl.concat([existing_data, new_record])
        except Exception:
            combined = new_record
    else:
        combined = new_record
    
    # 保存
    combined.write_parquet(PREFERENCES_FILE)
    log_message(f"✓ 已保存偏好评分：{rating}/10")


def ask_rating() -> tuple[int, list[str], str, str] | None:
    """询问用户评分和标签"""
    try:
        print("\n=== 壁纸评分 ===")
        print("请为这张壁纸评分 (1-10, 10 为最喜欢):")
        
        rating_input = input("评分：").strip()
        if not rating_input.isdigit():
            log_message("用户跳过评分", "INFO")
            return None
            
        rating = int(rating_input)
        if rating < 1 or rating > 10:
            print("评分必须在 1-10 之间")
            return None
        
        # 标签建议
        print("\n可选标签（用逗号分隔，直接回车跳过）:")
        print("建议：森林、山脉、海洋、暗色调、明亮、宁静、壮观...")
        tags_input = input("标签：").strip()
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
        
        # 色调
        print("\n色调分类:")
        for i, tone in enumerate(COLOR_TONES, 1):
            print(f"  {i}. {tone}")
        tone_input = input("选择 (1-4, 回车跳过): ").strip()
        color_tone = COLOR_TONES[int(tone_input) - 1] if tone_input.isdigit() and 1 <= int(tone_input) <= 4 else "unknown"
        
        # 分类
        print("\n壁纸分类:")
        for i, cat in enumerate(CATEGORIES, 1):
            print(f"  {i}. {cat}")
        cat_input = input("选择 (1-6, 回车跳过): ").strip()
        category = CATEGORIES[int(cat_input) - 1] if cat_input.isdigit() and 1 <= int(cat_input) <= len(CATEGORIES) else "nature"
        
        return rating, tags, color_tone, category
        
    except KeyboardInterrupt:
        print("\n评分已取消")
        return None
    except Exception as e:
        log_message(f"评分过程出错：{e}", "ERROR")
        return None


def get_random_wallpaper(category: str | None = None, color_tone: str | None = None, source: str | None = None) -> tuple[str, str, str, str]:
    """
    获取壁纸（按优先级尝试）
    返回: (url, category, color_tone, source_name)
    """
    wallpaper = None
    
    # 指定源或按优先级尝试
    if source == "bing" or source is None:
        wallpaper = get_bing_wallpaper()
        if wallpaper:
            log_message(f"使用 Bing 每日壁纸: {wallpaper.get('title', '')[:30]}")
    
    if not wallpaper and (source == "unsplash" or source is None):
        wallpaper = get_unsplash_wallpaper(category or "nature")
        if wallpaper:
            log_message(f"使用 Unsplash: {wallpaper.get('title', '')}")
    
    if not wallpaper or source == "picsum":
        wallpaper = get_picsum_wallpaper(category or "nature")
        log_message("使用 Picsum 兆底源")
    
    url = wallpaper["url"]
    source_name = wallpaper.get("source", "unknown")
    
    # 确定色调
    if color_tone:
        tone = color_tone
    elif category in ["space", "forest"]:
        tone = "dark"
    elif category in ["ocean"]:
        tone = "cool"
    else:
        tone = random.choice(COLOR_TONES)
    
    return url, category or "nature", tone, source_name


def main() -> int:
    import argparse
    
    parser = argparse.ArgumentParser(
        description="下载并设置 Mac 壁纸，支持分类和色调筛选",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/change-wallpaper.py
  uv run scripts/change-wallpaper.py --ask-rating
  uv run scripts/change-wallpaper.py --category mountain --color-tone dark
  uv run scripts/change-wallpaper.py --download-only --count 5
"""
    )
    parser.add_argument("--ask-rating", action="store_true", help="设置后询问评分")
    parser.add_argument("--category", type=str, choices=CATEGORIES, 
                        help="壁纸分类: nature, mountain, forest, ocean, city, space")
    parser.add_argument("--color-tone", type=str, choices=COLOR_TONES, 
                        help="色调: dark, bright, warm, cool")
    parser.add_argument("--source", type=str, choices=["bing", "unsplash", "picsum"],
                        help="指定图片源（默认按优先级自动选择）")
    parser.add_argument("--download-only", action="store_true", help="仅下载不设置")
    parser.add_argument("--count", type=int, default=1, help="下载数量（与 --download-only 配合）")
    args = parser.parse_args()
    
    log_message("=" * 50)
    log_message("开始更换壁纸")
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = WALLPAPER_DIR / today
    today_dir.mkdir(exist_ok=True)
    
    if args.download_only and args.count > 1:
        # 批量下载模式
        log_message(f"批量下载 {args.count} 张壁纸...")
        for i in range(args.count):
            url, category, tone, source_name = get_random_wallpaper(args.category, args.color_tone, args.source)
            filename = f"wallpaper-{today}-{i+1}.jpg"
            filepath = today_dir / filename
            
            if download_image(url, filepath):
                size = filepath.stat().st_size
                if size > 100 * 1024:
                    log_message(f"✓ 下载成功：{filename} ({size // 1024} KB)")
                else:
                    filepath.unlink()
                    log_message(f"文件太小，跳过：{filename}", "WARN")
        return 0
    
    # 单张模式
    url, category, tone, source_name = get_random_wallpaper(args.category, args.color_tone, args.source)
    filename = f"wallpaper-{today}.jpg"
    filepath = today_dir / filename
    
    log_message(f"下载壁纸：{url}")
    if download_image(url, filepath):
        size = filepath.stat().st_size
        if size > 100 * 1024:
            log_message(f"下载成功：{filepath} ({size // 1024} KB)")
            
            if args.download_only:
                log_message("仅下载模式，不设置壁纸")
                return 0
            
            # 设置壁纸
            if set_wallpaper_all_displays(filepath):
                log_message("✓ 壁纸更新成功")
                
                # 询问评分
                if args.ask_rating:
                    result = ask_rating()
                    if result:
                        rating, tags, color_tone, cat = result
                        save_preference(
                            wallpaper_path=str(filepath),
                            rating=rating,
                            tags=tags,
                            color_tone=color_tone,
                            category=cat,
                            source_url=url
                        )
                
                return 0
            else:
                log_message("设置壁纸失败", "ERROR")
        else:
            log_message("文件太小，可能是错误页面", "ERROR")
            filepath.unlink()
    else:
        log_message("下载失败", "ERROR")
    
    log_message("壁纸更换失败")
    return 1


if __name__ == "__main__":
    exit(main())
