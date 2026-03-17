#!/usr/bin/env python3
"""
Device Capture Skill (设备抓图技能)

支持多个萤石设备批量抓图，只需配置 appKey 和 appSecret。

功能:
- 自动获取 AccessToken
- 支持多个设备同时抓图
- 返回图片 URL 列表
- 可选下载图片到本地
"""

import sys
import os
import time
import hashlib
import json
import requests
from datetime import datetime

# Configuration
TOKEN_GET_API_URL = "https://open.ys7.com/api/lapp/token/get"
DEVICE_CAPTURE_API_URL = "https://open.ys7.com/api/lapp/device/capture"

# Environment variables
APP_KEY = os.environ.get("EZVIZ_APP_KEY", "")
APP_SECRET = os.environ.get("EZVIZ_APP_SECRET", "")
DEVICE_SERIAL = os.environ.get("EZVIZ_DEVICE_SERIAL", "")
CHANNEL_NO = os.environ.get("EZVIZ_CHANNEL_NO", "1")
DOWNLOAD_PATH = os.environ.get("EZVIZ_DOWNLOAD_PATH", "")


def get_current_timestamp():
    """Get current Unix timestamp in milliseconds."""
    return int(time.time() * 1000)


def get_access_token(app_key, app_secret):
    """
    Get access token using appKey and appSecret.
    
    API: POST /api/lapp/token/get
    
    Returns:
        dict: {success: bool, access_token: str, expire_time: int, error: str}
    """
    print(f"[INFO] Getting access token...")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "appKey": app_key,
        "appSecret": app_secret
    }
    
    try:
        response = requests.post(
            TOKEN_GET_API_URL,
            headers=headers,
            data=data,
            timeout=30
        )
        
        result = response.json()
        
        if result.get("code") == "200":
            data = result.get("data", {})
            expire_time = data.get("expireTime", 0)
            expire_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expire_time / 1000))
            print(f"[SUCCESS] Token obtained, expires: {expire_str}")
            return {
                "success": True,
                "access_token": data.get("accessToken", ""),
                "expire_time": expire_time
            }
        else:
            error_msg = result.get("msg", "Unknown error")
            print(f"[ERROR] Get token failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "code": result.get("code")
            }
    
    except Exception as e:
        print(f"[ERROR] Get token failed: {type(e).__name__}")
        return {
            "success": False,
            "error": str(e)
        }


def parse_device_list(device_str, channel_str="1"):
    """
    Parse device list from string.
    
    Supports formats:
    - Single device: "BA5918431" or "BA5918431,1"
    - Multiple devices: "BA5918431,BA5918432,BA5918433"
    - Multiple devices with channels: "BA5918431:1,BA5918432:1,BA5918433:2"
    - Mixed: "BA5918431,BA5918432:2,BA5918433"
    
    Returns:
        list: [(device_serial, channel_no), ...]
    """
    devices = []
    
    if not device_str:
        return devices
    
    for item in device_str.split(","):
        item = item.strip()
        if not item:
            continue
        
        if ":" in item:
            parts = item.split(":")
            serial = parts[0].strip().upper()
            channel = int(parts[1].strip()) if len(parts) > 1 else int(channel_str)
        else:
            serial = item.upper()
            channel = int(channel_str)
        
        devices.append((serial, channel))
    
    return devices


def capture_device_image(access_token, device_serial, channel_no=1):
    """
    Capture image from device.
    
    API: POST /api/lapp/device/capture
    
    Args:
        access_token: Ezviz access token
        device_serial: Device serial number (uppercase letters)
        channel_no: Channel number (default 1 for IPC)
    
    Returns:
        dict: {success: bool, pic_url: str, error: str, code: str}
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "accessToken": access_token,
        "deviceSerial": device_serial.upper(),
        "channelNo": str(channel_no)
    }
    
    try:
        response = requests.post(
            DEVICE_CAPTURE_API_URL,
            headers=headers,
            data=data,
            timeout=30
        )
        
        result = response.json()
        
        if result.get("code") == "200":
            data = result.get("data", {})
            pic_url = data.get("picUrl", "")
            print(f"[SUCCESS] Image captured: {pic_url[:50]}...")
            return {
                "success": True,
                "pic_url": pic_url,
                "expire_hours": 2
            }
        else:
            error_msg = result.get("msg", "Capture failed")
            print(f"[ERROR] Capture failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "code": result.get("code")
            }
    
    except Exception as e:
        print(f"[ERROR] Capture failed: {type(e).__name__}")
        return {
            "success": False,
            "error": str(e)
        }


def download_image(url, output_path):
    """
    Download image from URL to local file.
    
    Args:
        url: Image URL
        output_path: Local file path
    
    Returns:
        bool: True if successful
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(output_path)
        print(f"[INFO] Downloaded: {output_path} ({file_size} bytes)")
        return True
    
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False


def main():
    """
    Main workflow: get token -> capture images from multiple devices.
    """
    print("=" * 60)
    print("Device Capture Skill (设备抓图技能)")
    print("=" * 60)
    print(f"[Time] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Configuration from environment or arguments
    app_key = APP_KEY or sys.argv[1] if len(sys.argv) > 1 else ""
    app_secret = APP_SECRET or sys.argv[2] if len(sys.argv) > 2 else ""
    device_str = DEVICE_SERIAL or sys.argv[3] if len(sys.argv) > 3 else ""
    channel_str = CHANNEL_NO or (sys.argv[4] if len(sys.argv) > 4 else "1")
    download_path = DOWNLOAD_PATH or (sys.argv[5] if len(sys.argv) > 5 else "")
    
    # Validate configuration
    if not app_key or not app_secret:
        print("[ERROR] appKey and appSecret required.")
        print("[INFO] Set EZVIZ_APP_KEY and EZVIZ_APP_SECRET env vars, or pass as arguments.")
        sys.exit(1)
    
    # Parse device list
    devices = parse_device_list(device_str, channel_str)
    
    if not devices:
        print("[ERROR] At least one device serial required.")
        print("[INFO] Format: \"device1,device2,device3\" or \"device1:1,device2:2\"")
        print("[INFO] Set EZVIZ_DEVICE_SERIAL env var or pass as argument.")
        sys.exit(1)
    
    print(f"[INFO] Target devices: {len(devices)}")
    for serial, channel in devices:
        print(f"       - {serial} (Channel: {channel})")
    
    # Step 1: Get access token
    print(f"\n{'='*60}")
    print("[Step 1] Getting access token...")
    token_result = get_access_token(app_key, app_secret)
    
    if not token_result["success"]:
        print(f"[ERROR] Failed to get token: {token_result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    access_token = token_result["access_token"]
    expire_time = token_result.get("expire_time", 0)
    expire_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expire_time / 1000))
    print(f"[SUCCESS] Token obtained, expires: {expire_str}")
    
    # Step 2: Capture images from all devices
    print(f"\n{'='*60}")
    print("[Step 2] Capturing images...")
    print(f"{'='*60}")
    
    results = {
        "total": len(devices),
        "success": 0,
        "failed": 0,
        "captures": []
    }
    
    for device_serial, channel_no in devices:
        print(f"\n[Device] {device_serial} (Channel: {channel_no})")
        
        capture_result = capture_device_image(access_token, device_serial, channel_no)
        
        if capture_result["success"]:
            pic_url = capture_result["pic_url"]
            print(f"[SUCCESS] Image captured: {pic_url[:60]}...")
            
            # Download if path specified
            local_path = None
            if download_path:
                os.makedirs(download_path, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_serial}_{timestamp}.jpg"
                local_path = os.path.join(download_path, filename)
                download_image(pic_url, local_path)
            
            results["success"] += 1
            results["captures"].append({
                "device": device_serial,
                "channel": channel_no,
                "pic_url": pic_url,
                "local_path": local_path,
                "expire_hours": 2
            })
        else:
            error_msg = capture_result.get("error", "Unknown error")
            error_code = capture_result.get("code", "")
            print(f"[FAILED] {error_msg} (Code: {error_code})")
            results["failed"] += 1
            results["captures"].append({
                "device": device_serial,
                "channel": channel_no,
                "error": error_msg,
                "code": error_code
            })
        
        # Wait 4s between captures to avoid rate limiting (Ezviz recommends >=4s interval)
        time.sleep(4)
    
    # Print summary
    print(f"\n{'='*60}")
    print("CAPTURE SUMMARY")
    print(f"{'='*60}")
    print(f"  Total devices:  {results['total']}")
    print(f"  Success:        {results['success']}")
    print(f"  Failed:         {results['failed']}")
    print(f"{'='*60}")
    
    # Output JSON result
    print(f"\n[JSON Result]")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    print(f"\n{'='*60}")
    print("Workflow completed")
    print(f"{'='*60}")
    
    # Exit with error if any failed
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
