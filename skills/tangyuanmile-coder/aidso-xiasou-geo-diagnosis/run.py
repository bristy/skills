#!/usr/bin/env python3
import sys
import os
import json
import re
import time
import mimetypes
import tempfile
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API_URL = "https://testapi.aidso.com/openapi/skills/band_report/md"

API_TOKEN = os.environ.get("GEO_API_TOKEN", "").strip()
AUTH_HEADER = os.environ.get("GEO_AUTH_HEADER", "Authorization").strip()
AUTH_PREFIX = os.environ.get("GEO_AUTH_PREFIX", "Bearer ").strip()

BRAND_PARAM = os.environ.get("GEO_BRAND_PARAM", "brandName").strip()
POLL_INTERVAL_SEC = float(os.environ.get("GEO_POLL_INTERVAL_SEC", "8"))
POLL_TIMEOUT_SEC = int(os.environ.get("GEO_POLL_TIMEOUT_SEC", "900"))

SUCCESS_CODE_VALUES = {None, 0, 200, "0", "200"}
URL_FIELD_CANDIDATES = ["fileUrl", "downloadUrl", "url", "mdUrl", "pdfUrl", "reportUrl"]
TEXT_FIELD_CANDIDATES = ["markdown", "md", "report", "reportMarkdown"]
PROCESSING_TEXTS = ["正在处理中，请稍后", "处理中，请稍后"]

def build_headers(extra=None):
    headers = {"Accept": "*/*", "User-Agent": "openclaw-geo-report-skill/1.0"}
    if API_TOKEN:
        headers[AUTH_HEADER] = f"{AUTH_PREFIX}{API_TOKEN}".strip()
    if extra:
        headers.update(extra)
    return headers

def http_get(url, params=None):
    full_url = url
    if params:
        full_url += ("&" if "?" in url else "?") + urlencode(params, doseq=True)
    req = Request(full_url, method="GET", headers=build_headers())
    with urlopen(req, timeout=180) as resp:
        return {"status": resp.status, "headers": dict(resp.headers), "body": resp.read(), "url": full_url}

def decode_body(raw):
    for enc in ("utf-8", "utf-8-sig", "gb18030", "latin1"):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", errors="replace")

def parse_json_maybe(text):
    try:
        return json.loads(text)
    except Exception:
        return None

def extract_nested_value(data, keys):
    if not isinstance(data, dict):
        return None
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur

def normalize_api_json_or_raise(data):
    if isinstance(data, dict):
        code = data.get("code")
        msg = data.get("msg") or data.get("message") or ""
        if code not in SUCCESS_CODE_VALUES:
            raise ValueError(f"API 返回错误：code={code}, msg={msg}")
    return data

def extract_filename_from_headers(headers):
    cd = headers.get("Content-Disposition", "") or headers.get("content-disposition", "")
    if not cd:
        return None
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd, flags=re.I)
    if m:
        return m.group(1)
    m = re.search(r'filename="?([^";]+)"?', cd, flags=re.I)
    if m:
        return m.group(1)
    return None

def guess_ext_from_content_type(content_type):
    content_type = (content_type or "").split(";")[0].strip().lower()
    mapping = {
        "application/pdf": ".pdf",
        "text/markdown": ".md",
        "text/plain": ".txt",
        "application/json": ".json",
        "text/html": ".html",
        "application/octet-stream": ".bin",
    }
    if content_type in mapping:
        return mapping[content_type]
    return mimetypes.guess_extension(content_type) or ""

def save_binary_temp(content, suffix):
    fd, path = tempfile.mkstemp(prefix="geo_report_", suffix=suffix or ".dat")
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return path

def find_extra_urls_in_json(data):
    urls = []
    if isinstance(data, dict):
        for path in [
            ("data", "mdUrl"), ("data", "pdfUrl"), ("data", "fileUrl"), ("data", "downloadUrl"), ("data", "reportUrl"), ("data", "url"),
            ("result", "mdUrl"), ("result", "pdfUrl"), ("result", "fileUrl"), ("result", "downloadUrl"), ("result", "reportUrl"), ("result", "url"),
        ]:
            v = extract_nested_value(data, path)
            if isinstance(v, str) and v.strip().startswith(("http://", "https://")):
                urls.append(v.strip())
    seen, deduped = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped

def find_first_text_in_json(data):
    candidates = []
    if isinstance(data, dict):
        for key in TEXT_FIELD_CANDIDATES:
            v = data.get(key)
            if isinstance(v, str) and v.strip():
                candidates.append(v.strip())
        for path in [
            ("data", "markdown"), ("data", "md"), ("data", "report"), ("data", "reportMarkdown"),
            ("result", "markdown"), ("result", "md"), ("result", "report"), ("result", "reportMarkdown"),
        ]:
            v = extract_nested_value(data, path)
            if isinstance(v, str) and v.strip():
                candidates.append(v.strip())
    return candidates[0] if candidates else None

def is_processing_text(text):
    text = (text or "").strip()
    return bool(text) and any(s in text for s in PROCESSING_TEXTS)

def looks_like_markdown_report(text):
    text = (text or "").strip()
    if not text or is_processing_text(text):
        return False
    if text.startswith("#") or "\n#" in text or "## " in text or "|---" in text or "\n- " in text or "\n1. " in text:
        return True
    return len(text) >= 120

def handle_report_response(resp):
    headers = resp["headers"]
    content_type = (headers.get("Content-Type") or headers.get("content-type") or "").lower()

    # 非 JSON，优先判断是否文本
    if "application/json" not in content_type and resp.get("body"):
        text = decode_body(resp["body"]).strip() if (content_type.startswith("text/") or not content_type) else None

        if text is not None:
            if is_processing_text(text):
                return {"type": "processing"}
            return {"type": "text", "text": text}

        suffix = guess_ext_from_content_type(content_type) or ".dat"
        path = save_binary_temp(resp["body"], suffix)
        return {"type": "media", "lines": [f"MEDIA:{path}"]}

    text = decode_body(resp["body"]).strip()
    data = parse_json_maybe(text)

    if data is not None:
        data = normalize_api_json_or_raise(data)

        urls = find_extra_urls_in_json(data)
        if urls:
            return {"type": "media", "lines": [f"MEDIA:{u}" for u in urls]}

        md_text = find_first_text_in_json(data)
        if md_text:
            if is_processing_text(md_text):
                return {"type": "processing"}
            return {"type": "text", "text": md_text}

        msg = ""
        if isinstance(data, dict):
            msg = (data.get("msg") or data.get("message") or "").strip()
        if is_processing_text(msg):
            return {"type": "processing"}

        return {"type": "text", "text": text}

    if is_processing_text(text):
        return {"type": "processing"}

    if looks_like_markdown_report(text):
        return {"type": "text", "text": text}

    if text:
        return {"type": "text", "text": text}

    raise ValueError("接口返回为空")

def action_poll_report(brand):
    started_at = time.time()

    while True:
        resp = http_get(API_URL, {BRAND_PARAM: brand})
        parsed = handle_report_response(resp)

        if parsed["type"] == "text":
            print(parsed["text"])
            return

        if parsed["type"] == "media":
            for line in parsed["lines"]:
                print(line)
            return

        if time.time() - started_at > POLL_TIMEOUT_SEC:
            raise TimeoutError("诊断任务仍在处理中，请稍后再试")

        time.sleep(POLL_INTERVAL_SEC)

def main():
    if len(sys.argv) < 3:
        print("用法: run.py poll_report <brand>", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1].strip()
    brand = sys.argv[2].strip()
    if not brand:
        print("品牌名称不能为空", file=sys.stderr)
        sys.exit(1)

    try:
        if action == "poll_report":
            action_poll_report(brand)
        else:
            raise ValueError(f"未知 action: {action}")
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        print(f"HTTP 错误: {e.code} {e.reason} {body}", file=sys.stderr)
        sys.exit(2)
    except URLError as e:
        print(f"网络错误: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
