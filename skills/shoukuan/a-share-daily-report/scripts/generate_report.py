#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股早晚报生成器 (Enhanced Version)
===================================
数据源: 东方财富 (finance.eastmoney.com) 公开 API
输出:   Markdown 报告 + 数据图表 (PNG) + PDF

报告包含:
  1. 主要指数行情表格
  2. 市场情绪分析 (涨跌比、涨停跌停、成交额)
  3. 行业/概念板块涨跌排行
  4. 个股涨幅/跌幅排行
  5. 指数 K 线走势图 (近30个交易日, 含均线)
  6. 板块涨跌幅横向柱状图
  7. 市场情绪饼图
  8. 热点新闻聚合 & 主题追踪
  9. 综合分析与展望
"""

import argparse
import contextlib
import concurrent.futures
import datetime as dt
import io
import json
import mimetypes
import os
import re
import sys
import time
import traceback
import urllib.parse
import urllib.request
import subprocess
import uuid
from zoneinfo import ZoneInfo
from pathlib import Path

# ───────────────────── Configuration ──────────────────────────────────────

EASTMONEY_NEWS_URL = "https://finance.eastmoney.com/"

# Eastmoney push API base
API_BASE = "https://push2.eastmoney.com/api/qt"
API_HIS_BASE = "https://push2his.eastmoney.com/api/qt"

# Index secids: "market.code" -> display name
INDEX_SECIDS = {
    "1.000001": "上证指数",
    "0.399001": "深证成指",
    "0.399006": "创业板指",
    "1.000688": "科创50",
    "0.899050": "北证50",
    "1.000016": "上证50",
    "1.000300": "沪深300",
    "1.000905": "中证500",
    "0.399673": "创业板50",
}

# 主题关键词追踪
THEME_KEYWORDS = {
    "新能源": ["新能源", "光伏", "风电", "储能", "电池", "锂电", "充电桩"],
    "半导体": ["半导体", "芯片", "集成电路", "封装", "晶圆", "EDA"],
    "AI/人工智能": ["人工智能", "AI", "大模型", "算力", "GPT", "机器学习", "深度学习"],
    "机器人": ["机器人", "人形", "减速器", "伺服", "机械臂"],
    "有色金属": ["钛", "镁", "金属", "有色", "铜", "铝", "黄金", "稀土"],
    "医药生物": ["医药", "生物", "创新药", "医疗器械", "CXO"],
}

# 用户关注主题（板块/概念）表现追踪
FOCUS_THEMES = {
    "算力": ["算力", "AI", "人工智能", "服务器", "数据中心", "云计算"],
    "半导体": ["半导体", "芯片", "集成电路", "封装", "晶圆", "EDA"],
    "新能源": ["新能源", "光伏", "风电", "储能", "电池", "锂电", "充电桩"],
    "风电设备": ["风电", "风电设备", "风能", "风电整机", "风电零部件"],
    "钛/镁金属": ["钛", "镁", "金属", "有色", "稀土"],
}

# 主题龙头企业
THEME_LEADERS = {
    "算力": ["浪潮信息", "中科曙光", "紫光股份"],
    "半导体": ["中芯国际", "韦尔股份", "北方华创"],
    "新能源": ["宁德时代", "比亚迪", "隆基绿能"],
    "风电设备": ["金风科技", "明阳智能", "运达股份"],
    "钛/镁金属": ["宝钛股份", "西部超导", "云海金属"],
}

# 自选股（阿宽）
WATCHLIST = [
    {"name": "比亚迪", "code": "002594", "secid": "0.002594"},
    {"name": "腾讯控股", "code": "00700", "secid": "116.00700"},
    {"name": "小米集团", "code": "01810", "secid": "116.01810"},
    {"name": "三花智控", "code": "002050", "secid": "0.002050"},
]

# 全球资产（Yahoo Finance symbols）
GLOBAL_ASSETS = [
    {"name": "美元指数", "symbol": "DX-Y.NYB"},
    {"name": "黄金", "symbol": "GC=F"},
    {"name": "原油(WTI)", "symbol": "CL=F"},
]

SKILL_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SKILL_ROOT.parents[1]
CACHE_DIR = SKILL_ROOT / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_ENV_PATH = WORKSPACE_ROOT / ".env"
DEFAULT_FEISHU_STATE_PATH = WORKSPACE_ROOT / "data" / "feishu_doc_state.json"
FEISHU_DOC_URL_TEMPLATE = "https://www.feishu.cn/docx/{doc_id}"
FEISHU_OPEN_ID_ENV_KEYS = (
    "FEISHU_NOTIFY_OPEN_ID",
    "FEISHU_OPEN_ID",
    "FEISHU_USER_OPEN_ID",
)

_AK = None
_THS_NAME_CACHE = {}
_THS_BOARD_HISTORY_CACHE = {}
_STOCK_INFO_CACHE = {}
_YAHOO_HISTORY_CACHE = {}

# ───────────────────── Helpers ────────────────────────────────────────────

def _get_tushare():
    """Lazy import tushare and return pro api (requires TUSHARE_TOKEN env)."""
    try:
        import tushare as ts
        return ts.pro_api()
    except Exception:
        return None


def _get_akshare():
    """Lazy import akshare for historical A-share/board data."""
    global _AK
    if _AK is not None:
        return _AK
    try:
        import akshare as ak
        _AK = ak
        return ak
    except Exception:
        return None


def _safe_float(v, default=0.0):
    """Safely convert to float."""
    if v is None or v == "-" or v == "":
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def format_turnover(val):
    """Format turnover to human-readable."""
    v = _safe_float(val)
    if v >= 1e8:
        return f"{v / 1e8:.2f}亿"
    if v >= 1e4:
        return f"{v / 1e4:.2f}万"
    if v > 0:
        return f"{v:.0f}"
    return "N/A"


def format_volume(val):
    """Format volume (手) to human-readable."""
    v = _safe_float(val)
    if v >= 1e4:
        return f"{v / 1e4:.2f}万手"
    if v > 0:
        return f"{v:.0f}手"
    return "N/A"


def color_pct(val):
    """Format change percent with emoji indicator."""
    v = _safe_float(val)
    if v > 0:
        return f"🔴 +{v:.2f}%"
    if v < 0:
        return f"🟢 {v:.2f}%"
    return f"⚪ {v:.2f}%"


def color_pct_plain(val):
    """Format change percent without emoji, with +/- sign."""
    v = _safe_float(val)
    return f"{v:+.2f}%"


def _load_env_file(path):
    env_path = Path(path)
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(
                key.strip(),
                value.strip().strip("'").strip('"'),
            )
    except Exception:
        pass


def _build_feishu_doc_url(doc_id):
    return FEISHU_DOC_URL_TEMPLATE.format(doc_id=doc_id)


def _chunked(seq, size):
    for idx in range(0, len(seq), size):
        yield seq[idx: idx + size]


def _normalize_feishu_state(raw_state):
    state = {}
    if not isinstance(raw_state, dict):
        return state
    for date_key, value in raw_state.items():
        if isinstance(value, str):
            state[date_key] = {
                "doc_id": value,
                "doc_url": _build_feishu_doc_url(value),
            }
        elif isinstance(value, dict) and value.get("doc_id"):
            normalized = dict(value)
            normalized.setdefault("doc_url", _build_feishu_doc_url(value["doc_id"]))
            state[date_key] = normalized
    return state


def _guess_feishu_open_id(explicit_value=None):
    if explicit_value:
        return explicit_value
    for env_key in FEISHU_OPEN_ID_ENV_KEYS:
        value = os.environ.get(env_key)
        if value:
            return value
    return None


def _is_markdown_table_separator(line):
    return bool(
        re.match(r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$", line.strip())
    )


def _parse_markdown_table_row(line):
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [cell.strip() for cell in text.split("|")]


def _strip_markdown_decorations(text):
    cleaned = text.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__([^_]+)__", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"_([^_]+)_", r"\1", cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    return cleaned.strip()


def _markdown_line_to_text_elements(text, bold=False):
    elements = []
    cursor = 0
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        prefix = _strip_markdown_decorations(text[cursor:match.start()])
        if prefix:
            payload = {"content": prefix}
            if bold:
                payload["text_element_style"] = {"bold": True}
            elements.append({"text_run": payload})
        label = _strip_markdown_decorations(match.group(1)) or match.group(2).strip()
        url = match.group(2).strip()
        if label:
            style = {"link": {"url": url}}
            if bold:
                style["bold"] = True
            elements.append(
                {
                    "text_run": {
                        "content": label,
                        "text_element_style": style,
                    }
                }
            )
        cursor = match.end()
    suffix = _strip_markdown_decorations(text[cursor:])
    if suffix:
        payload = {"content": suffix}
        if bold:
            payload["text_element_style"] = {"bold": True}
        elements.append({"text_run": payload})
    if elements:
        return elements
    plain = _strip_markdown_decorations(text)
    if not plain:
        return []
    payload = {"content": plain}
    if bold:
        payload["text_element_style"] = {"bold": True}
    return [{"text_run": payload}]


def _make_text_child(text, bold=False):
    elements = _markdown_line_to_text_elements(text, bold=bold)
    if not elements:
        return None
    return {
        "block_type": 2,
        "text": {
            "elements": elements,
        },
    }


def _is_special_markdown_line(stripped):
    return (
        stripped.startswith("#")
        or stripped.startswith(">")
        or stripped.startswith("![")
        or stripped.startswith("```")
        or stripped == "---"
        or bool(re.match(r"^\s*(?:[-*]|\d+[.)])\s+", stripped))
        or stripped.startswith("|")
    )


def _strip_report_wrapper(markdown):
    first_heading_skipped = False
    kept_lines = []
    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()
        if not first_heading_skipped and stripped.startswith("# "):
            first_heading_skipped = True
            continue
        if stripped.startswith("*— A股"):
            continue
        kept_lines.append(raw_line)
    return "\n".join(kept_lines).strip()


def collect_daily_report_sections(outdir, resolved_ymd):
    sections = []
    outdir = Path(outdir)
    for mode, mode_cn in [("morning", "早报"), ("evening", "晚报")]:
        md_path = outdir / f"A股{mode_cn}-{resolved_ymd}.md"
        if not md_path.exists():
            continue
        sections.append(
            {
                "mode": mode,
                "mode_cn": mode_cn,
                "path": md_path,
                "markdown": _strip_report_wrapper(
                    md_path.read_text(encoding="utf-8")
                ),
            }
        )
    return sections


def build_feishu_daily_markdown(date_str, sections):
    lines = [
        f"# 📊 A股日报｜{date_str}",
        "",
        f"> **文档更新时间**：{dt.datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')}（Asia/Shanghai）",
        "> **同步策略**：同一天重复生成会覆盖文档内容，早报与晚报合并在同一文档。",
        "",
    ]
    for section in sections:
        lines.append(f"## {section['mode_cn']}")
        lines.append("")
        lines.append(section["markdown"])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def markdown_to_feishu_ops(markdown, base_dir):
    ops = []
    lines = markdown.splitlines()
    index = 0
    base_path = Path(base_dir)

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        if not stripped:
            index += 1
            continue

        image_match = re.match(r"^!\[(.*?)\]\((.*?)\)$", stripped)
        if image_match:
            target = urllib.parse.unquote(image_match.group(2).strip())
            image_path = (base_path / target).expanduser()
            if not image_path.is_absolute():
                image_path = image_path.resolve()
            ops.append(
                {
                    "kind": "image",
                    "path": image_path,
                    "caption": image_match.group(1).strip() or image_path.name,
                }
            )
            index += 1
            continue

        if stripped.startswith("```"):
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                if lines[index].strip():
                    code_lines.append(lines[index].rstrip())
                index += 1
            if index < len(lines):
                index += 1
            if code_lines:
                block = _make_text_child(" ".join(code_lines))
                if block:
                    ops.append({"kind": "block", "child": block})
            continue

        if (
            stripped.startswith("|")
            and index + 1 < len(lines)
            and _is_markdown_table_separator(lines[index + 1])
        ):
            headers = _parse_markdown_table_row(lines[index])
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                values = _parse_markdown_table_row(lines[index])
                parts = []
                for col_idx, header in enumerate(headers):
                    value = values[col_idx] if col_idx < len(values) else ""
                    value = _strip_markdown_decorations(value)
                    if value:
                        parts.append(f"{header}：{value}")
                block = _make_text_child(f"• {' ｜ '.join(parts)}")
                if block:
                    ops.append({"kind": "block", "child": block})
                index += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            block = _make_text_child(
                _strip_markdown_decorations(heading_match.group(2)),
                bold=True,
            )
            if block:
                ops.append({"kind": "block", "child": block})
            index += 1
            continue

        if stripped == "---":
            block = _make_text_child("────────")
            if block:
                ops.append({"kind": "block", "child": block})
            index += 1
            continue

        if stripped.startswith(">"):
            quote_lines = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            block = _make_text_child("｜".join(q for q in quote_lines if q))
            if block:
                ops.append({"kind": "block", "child": block})
            continue

        list_match = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$", raw_line)
        if list_match:
            block = _make_text_child(
                f"• {_strip_markdown_decorations(list_match.group(1))}"
            )
            if block:
                ops.append({"kind": "block", "child": block})
            index += 1
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            next_stripped = lines[index].strip()
            if not next_stripped or _is_special_markdown_line(next_stripped):
                break
            paragraph_lines.append(next_stripped)
            index += 1
        block = _make_text_child(" ".join(paragraph_lines))
        if block:
            ops.append({"kind": "block", "child": block})

    return ops


class FeishuDocClient:
    def __init__(self, app_id, app_secret, folder_token=None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.folder_token = folder_token
        self._tenant_token = None
        self._tenant_token_expire_at = 0

    def configured(self):
        return bool(self.app_id and self.app_secret)

    def _request(self, method, url, payload=None, headers=None, timeout=30):
        req_headers = headers or {}
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req_headers.setdefault("Content-Type", "application/json; charset=utf-8")
        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        with _proxyless_open(req, timeout=timeout) as response:
            raw = response.read()
        return json.loads(raw.decode("utf-8", "ignore"))

    def _request_multipart(self, url, fields, file_field, timeout=60):
        boundary = f"----OpenClaw{uuid.uuid4().hex}"
        body = bytearray()
        for key, value in fields.items():
            if value is None:
                continue
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8")
            )
            body.extend(str(value).encode("utf-8"))
            body.extend(b"\r\n")

        file_name, file_bytes, content_type = file_field
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        body.extend(file_bytes)
        body.extend(b"\r\n")
        body.extend(f"--{boundary}--\r\n".encode("utf-8"))

        req = urllib.request.Request(
            url,
            data=bytes(body),
            headers={
                "Authorization": f"Bearer {self.tenant_access_token()}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        with _proxyless_open(req, timeout=timeout) as response:
            raw = response.read()
        return json.loads(raw.decode("utf-8", "ignore"))

    def _assert_ok(self, data, action):
        if data.get("code", 0) not in (0, None):
            raise RuntimeError(
                f"{action} 失败: code={data.get('code')} msg={data.get('msg')}"
            )
        return data

    def tenant_access_token(self):
        now = time.time()
        if self._tenant_token and now < self._tenant_token_expire_at - 60:
            return self._tenant_token
        data = self._request(
            "POST",
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/",
            payload={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=20,
        )
        self._assert_ok(data, "获取 tenant_access_token")
        self._tenant_token = data["tenant_access_token"]
        self._tenant_token_expire_at = now + int(data.get("expire", 7200))
        return self._tenant_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.tenant_access_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def create_document(self, title):
        payloads = []
        if self.folder_token:
            payloads.append({"title": title, "folder_token": self.folder_token})
        payloads.append({"title": title})

        last_error = None
        for payload in payloads:
            try:
                data = self._request(
                    "POST",
                    "https://open.feishu.cn/open-apis/docx/v1/documents",
                    payload=payload,
                    headers=self._headers(),
                    timeout=20,
                )
                self._assert_ok(data, "创建飞书文档")
                doc_id = data.get("data", {}).get("document", {}).get("document_id")
                if not doc_id:
                    raise RuntimeError("创建飞书文档失败: 未返回 document_id")
                return {
                    "doc_id": doc_id,
                    "doc_url": _build_feishu_doc_url(doc_id),
                    "title": title,
                }
            except Exception as exc:
                last_error = exc
                continue
        raise last_error or RuntimeError("创建飞书文档失败")

    def get_document(self, doc_id):
        data = self._request(
            "GET",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}",
            headers=self._headers(),
            timeout=20,
        )
        self._assert_ok(data, "获取飞书文档")
        return data

    def list_root_children(self, doc_id):
        data = self._request(
            "GET",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children?page_size=500",
            headers=self._headers(),
            timeout=20,
        )
        self._assert_ok(data, "获取文档子块")
        return data.get("data", {}).get("items", []) or []

    def clear_document(self, doc_id):
        while True:
            items = self.list_root_children(doc_id)
            child_count = len(items)
            if child_count == 0:
                return
            payload = {"start_index": 0, "end_index": child_count}
            try:
                data = self._request(
                    "DELETE",
                    f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete",
                    payload=payload,
                    headers=self._headers(),
                    timeout=20,
                )
                self._assert_ok(data, "清空文档")
            except Exception:
                payload["end_index"] = max(child_count - 1, 0)
                data = self._request(
                    "DELETE",
                    f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children/batch_delete",
                    payload=payload,
                    headers=self._headers(),
                    timeout=20,
                )
                self._assert_ok(data, "清空文档")

    def append_text_children(self, doc_id, children):
        for chunk in _chunked(children, 20):
            data = self._request(
                "POST",
                f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
                payload={"children": chunk},
                headers=self._headers(),
                timeout=30,
            )
            self._assert_ok(data, "写入文档文本")

    def _upload_doc_media(self, doc_id, parent_type, parent_node, file_path):
        file_path = Path(file_path)
        file_bytes = file_path.read_bytes()
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        fields = {
            "file_name": file_path.name,
            "parent_type": parent_type,
            "parent_node": parent_node,
            "size": len(file_bytes),
            "extra": json.dumps({"drive_route_token": doc_id}, ensure_ascii=False),
        }
        data = self._request_multipart(
            "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
            fields=fields,
            file_field=(file_path.name, file_bytes, mime_type),
            timeout=60,
        )
        self._assert_ok(data, "上传文档媒体")
        token = data.get("data", {}).get("file_token") or data.get("file_token")
        if not token:
            raise RuntimeError("上传文档媒体失败: 未返回 file_token")
        return token

    def _batch_update_blocks(self, doc_id, requests):
        data = self._request(
            "PATCH",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/batch_update",
            payload={"requests": requests},
            headers=self._headers(),
            timeout=30,
        )
        self._assert_ok(data, "更新文档块")

    def insert_image(self, doc_id, image_path, caption=None):
        create_data = self._request(
            "POST",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
            payload={"children": [{"block_type": 27, "image": {}}]},
            headers=self._headers(),
            timeout=30,
        )
        self._assert_ok(create_data, "创建图片占位块")
        block_id = create_data.get("data", {}).get("children", [{}])[0].get("block_id")
        if not block_id:
            raise RuntimeError("创建图片占位块失败: 未返回 block_id")
        file_token = self._upload_doc_media(
            doc_id,
            parent_type="docx_image",
            parent_node=block_id,
            file_path=image_path,
        )
        patch = {"block_id": block_id, "replace_image": {"token": file_token, "align": 2}}
        if caption:
            patch["replace_image"]["caption"] = {"content": caption}
        self._batch_update_blocks(doc_id, [patch])

    def insert_file(self, doc_id, file_path):
        create_data = self._request(
            "POST",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
            payload={"children": [{"block_type": 23, "file": {"token": ""}}]},
            headers=self._headers(),
            timeout=30,
        )
        self._assert_ok(create_data, "创建附件占位块")
        child = create_data.get("data", {}).get("children", [{}])[0]
        block_id = child.get("children", [None])[0] or child.get("block_id")
        if not block_id:
            raise RuntimeError("创建附件占位块失败: 未返回 block_id")
        file_token = self._upload_doc_media(
            doc_id,
            parent_type="docx_file",
            parent_node=block_id,
            file_path=file_path,
        )
        self._batch_update_blocks(
            doc_id,
            [{"block_id": block_id, "replace_file": {"token": file_token}}],
        )

    def send_text_message(self, open_id, text):
        data = self._request(
            "POST",
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
            payload={
                "receive_id": open_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}, ensure_ascii=False),
            },
            headers=self._headers(),
            timeout=20,
        )
        self._assert_ok(data, "发送飞书消息")
        return data


def sync_report_to_feishu(
    outdir,
    resolved_ymd,
    date_str,
    mode_cn,
    pdf_path=None,
    env_path=DEFAULT_ENV_PATH,
    state_path=DEFAULT_FEISHU_STATE_PATH,
    folder_token=None,
    notify_open_id=None,
):
    _load_env_file(env_path)

    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    folder_token = folder_token or os.environ.get("FEISHU_FOLDER_TOKEN")
    notify_open_id = _guess_feishu_open_id(notify_open_id)

    client = FeishuDocClient(
        app_id=app_id,
        app_secret=app_secret,
        folder_token=folder_token,
    )
    if not client.configured():
        return None

    state_file = Path(state_path)
    state = _normalize_feishu_state(_load_json_cache(state_file) or {})
    doc_title = f"A股日报 {date_str}"
    doc_entry = state.get(date_str)
    doc_id = doc_entry.get("doc_id") if doc_entry else None
    if doc_id:
        try:
            client.get_document(doc_id)
        except Exception:
            doc_id = None
            doc_entry = None

    if not doc_id:
        doc_entry = client.create_document(doc_title)
        doc_id = doc_entry["doc_id"]

    sections = collect_daily_report_sections(outdir, resolved_ymd)
    if not sections:
        raise RuntimeError(f"未找到 {date_str} 的本地 Markdown 报告")

    daily_markdown = build_feishu_daily_markdown(date_str, sections)
    # 直接使用飞书创建文档API，传入完整Markdown
    # 避免自定义解析导致的表格丢失
    try:
        # 清理文档内容
        client.clear_document(doc_id)
        # 使用原生API创建文档内容，支持标准Markdown表格
        create_resp = client._request(
            "POST",
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
            payload={
                "children": [
                    {
                        "block_type": 1,
                        "text": {
                            "elements": [
                                {
                                    "text_run": {
                                        "content": daily_markdown
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            headers=client._headers(),
            timeout=60,
        )
        client._assert_ok(create_resp, "写入文档内容")
    except Exception as e:
        print(f"   ⚠️  原生写入失败，回退到分段解析: {e}")
        # 回退到原有的分段解析方式
        ops = markdown_to_feishu_ops(daily_markdown, outdir)
        if not ops:
            raise RuntimeError("飞书文档内容为空，未执行同步")

        pending_text_children = []
        for item in ops:
            if item["kind"] == "block" and item.get("child"):
                pending_text_children.append(item["child"])
                continue
            if pending_text_children:
                client.append_text_children(doc_id, pending_text_children)
                pending_text_children = []
            if item["kind"] != "image":
                continue
            if not item["path"].exists():
                warn = _make_text_child(f"[图表缺失] {item['path'].name}")
                if warn:
                    client.append_text_children(doc_id, [warn])
                continue
            client.insert_image(doc_id, item["path"], caption=item.get("caption"))
        if pending_text_children:
            client.append_text_children(doc_id, pending_text_children)

    if pdf_path and Path(pdf_path).exists():
        label = _make_text_child("PDF 归档", bold=True)
        if label:
            client.append_text_children(doc_id, [label])
        client.insert_file(doc_id, pdf_path)

    doc_entry = {
        "doc_id": doc_id,
        "doc_url": _build_feishu_doc_url(doc_id),
        "title": doc_title,
        "updated_at": dt.datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S"),
        "reports": [section["mode"] for section in sections],
    }
    state[date_str] = doc_entry
    _save_json_cache(state_file, state)

    notified = False
    if notify_open_id:
        client.send_text_message(
            notify_open_id,
            f"A股{mode_cn}已同步到飞书文档：{doc_entry['doc_url']}\n日期：{date_str}",
        )
        notified = True

    result = dict(doc_entry)
    result["notified"] = notified
    return result


# ───────────────────── Data Fetching ──────────────────────────────────────

def _proxyless_open(req, timeout):
    """Open URL without inheriting shell proxy vars."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(req, timeout=timeout)


def _fetch_json(url, timeout=20, retries=3, headers=None):
    """Fetch JSON, stripping jQuery wrapper and retrying transient network errors."""
    final_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.eastmoney.com/",
    }
    if headers:
        final_headers.update(headers)
    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=final_headers)
            with _proxyless_open(req, timeout=timeout) as response:
                text = response.read().decode("utf-8", "ignore")
            match = re.match(r"^jQuery\w*\((.*)\);?\s*$", text, re.S)
            if match:
                text = match.group(1)
            return json.loads(text)
        except Exception as exc:
            last_error = exc
            if attempt + 1 == retries:
                raise
            time.sleep(1.2 * (attempt + 1))
    raise last_error


def _fetch_html(url, timeout=15, retries=3):
    headers = {"User-Agent": "Mozilla/5.0"}
    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with _proxyless_open(req, timeout=timeout) as response:
                return response.read().decode("utf-8", "ignore")
        except Exception as exc:
            last_error = exc
            if attempt + 1 == retries:
                raise
            time.sleep(1.2 * (attempt + 1))
    raise last_error


def _load_json_cache(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_json_cache(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def _cache_key(text):
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", text).strip("_") or "default"


def _to_ymd(value):
    if isinstance(value, dt.date):
        return value.strftime("%Y%m%d")
    return str(value).replace("-", "")


def _to_date(value):
    if isinstance(value, dt.date):
        return value
    return dt.datetime.strptime(str(value).replace("-", ""), "%Y%m%d").date()


@contextlib.contextmanager
def _without_proxy_env():
    keys = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]
    backup = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ.pop(key, None)
        yield
    finally:
        for key, value in backup.items():
            if value is not None:
                os.environ[key] = value


def _call_akshare(func, *args, **kwargs):
    with _without_proxy_env():
        with contextlib.redirect_stdout(io.StringIO()):
            with contextlib.redirect_stderr(io.StringIO()):
                return func(*args, **kwargs)


def _history_row_on_or_before(rows, trade_date):
    if not rows:
        return None
    target = _to_ymd(trade_date)
    eligible = [row for row in rows if row.get("date") and row["date"] <= target]
    if not eligible:
        return None
    return eligible[-1]


def _rows_to_history_payload(rows):
    payload = []
    prev_close = None
    for row in rows:
        close = _safe_float(row.get("收盘价", row.get("收盘")))
        open_price = _safe_float(row.get("开盘价", row.get("开盘")))
        high = _safe_float(row.get("最高价", row.get("最高")))
        low = _safe_float(row.get("最低价", row.get("最低")))
        volume = _safe_float(row.get("成交量"))
        amount = _safe_float(row.get("成交额"))
        pct_change = 0.0
        change_amt = 0.0
        if prev_close:
            change_amt = close - prev_close
            pct_change = change_amt / prev_close * 100
        payload.append({
            "date": _to_ymd(row.get("日期")),
            "open": open_price,
            "close": close,
            "high": high,
            "low": low,
            "volume": volume,
            "turnover": amount,
            "amplitude": ((high - low) / prev_close * 100) if prev_close else 0.0,
            "change_pct": pct_change,
            "change_amt": change_amt,
            "turnover_rate": 0.0,
            "prev_close": prev_close,
        })
        prev_close = close
    return payload


def resolve_trade_date(requested_date):
    """Resolve to the latest available A-share trading day <= requested date."""
    target = _to_ymd(requested_date)
    rows = fetch_kline("1.000001", count=10, end_date=target)
    if not rows:
        return target
    exact = next((row for row in rows if _to_ymd(row["date"]) == target), None)
    if exact:
        return _to_ymd(exact["date"])
    return _to_ymd(rows[-1]["date"])


# -- 1) Major index quotes ------------------------------------------------

def fetch_indices():
    """Fetch major index real-time quotes."""
    secids = ",".join(INDEX_SECIDS.keys())
    url = (
        f"{API_BASE}/ulist.np/get?fltt=2&secids={secids}"
        f"&fields=f2,f3,f4,f5,f6,f7,f12,f13,f14,f15,f16,f17,f18"
    )
    data = _fetch_json(url)
    results = []
    if data and data.get("data") and data["data"].get("diff"):
        for item in data["data"]["diff"]:
            results.append({
                "code": item.get("f12", ""),
                "name": item.get("f14", ""),
                "price": item.get("f2", "-"),
                "change_pct": item.get("f3", 0),
                "change_amt": item.get("f4", "-"),
                "volume": item.get("f5", 0),
                "turnover": item.get("f6", 0),
                "amplitude": item.get("f7", "-"),
                "high": item.get("f15", "-"),
                "low": item.get("f16", "-"),
                "open": item.get("f17", "-"),
                "prev_close": item.get("f18", "-"),
            })
    return results


# -- 2) Sector / concept board ranking ------------------------------------

def fetch_sector_ranking(sector_type="industry", direction="up", count=10):
    """
    Fetch sector performance ranking.
    sector_type: 'industry' | 'concept'
    direction:   'up' | 'down'
    """
    fs_type = "t:2" if sector_type == "industry" else "t:3"
    po = 1 if direction == "up" else 0
    url = (
        f"{API_BASE}/clist/get?pn=1&pz={count}&po={po}&np=1&fltt=2&invt=2"
        f"&fid=f3&fs=m:90+{fs_type}+f:!50"
        f"&fields=f2,f3,f4,f12,f14,f104,f105,f128,f140,f141"
    )
    data = _fetch_json(url)
    results = []
    if data and data.get("data") and data["data"].get("diff"):
        for item in data["data"]["diff"]:
            results.append({
                "code": item.get("f12", ""),
                "name": item.get("f14", ""),
                "price": item.get("f2", "-"),
                "change_pct": item.get("f3", 0),
                "change_amt": item.get("f4", 0),
                "up_count": item.get("f104", 0),
                "down_count": item.get("f105", 0),
                "lead_stock": item.get("f140", ""),
                "lead_stock_pct": item.get("f141", 0),
            })
    return results


# -- 3) Individual stock ranking -------------------------------------------

def fetch_stock_ranking(direction="up", count=10):
    """Fetch individual A-share stock ranking by change %."""
    po = 1 if direction == "up" else 0
    url = (
        f"{API_BASE}/clist/get?pn=1&pz={count}&po={po}&np=1&fltt=2&invt=2"
        f"&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
        f"&fields=f2,f3,f4,f5,f6,f7,f12,f14,f15,f16,f17,f18"
    )
    data = _fetch_json(url)
    results = []
    if data and data.get("data") and data["data"].get("diff"):
        for item in data["data"]["diff"]:
            results.append({
                "code": item.get("f12", ""),
                "name": item.get("f14", ""),
                "price": item.get("f2", "-"),
                "change_pct": item.get("f3", 0),
                "change_amt": item.get("f4", "-"),
                "volume": item.get("f5", 0),
                "turnover": item.get("f6", 0),
                "amplitude": item.get("f7", "-"),
            })
    return results


def fetch_watchlist_quotes(watchlist):
    """Fetch quotes for watchlist stocks by secid."""
    results = []
    for item in watchlist:
        secid = item.get("secid")
        if not secid:
            continue
        url = (
            f"{API_BASE}/stock/get?secid={secid}"
            f"&fields=f2,f3,f4,f5,f6,f7,f12,f14,f15,f16,f17,f18"
        )
        try:
            data = _fetch_json(url)
            if data and data.get("data"):
                d = data["data"]
                results.append({
                    "code": d.get("f12", item.get("code", "")),
                    "name": d.get("f14", item.get("name", "")),
                    "price": d.get("f2", "-"),
                    "change_pct": d.get("f3", 0),
                    "change_amt": d.get("f4", "-"),
                    "volume": d.get("f5", 0),
                    "turnover": d.get("f6", 0),
                    "amplitude": d.get("f7", "-"),
                    "high": d.get("f15", "-"),
                    "low": d.get("f16", "-"),
                    "open": d.get("f17", "-"),
                    "prev_close": d.get("f18", "-"),
                })
        except Exception:
            continue
    return results


def fetch_watchlist_quotes_with_fallback(watchlist, trade_date=None):
    """Fetch watchlist quotes with realtime -> kline -> tushare fallback."""
    results = fetch_watchlist_quotes(watchlist)
    if results:
        return results, "realtime"
    if trade_date:
        results = fetch_watchlist_quotes_historical(watchlist, trade_date)
        if results:
            return results, "kline"
        results = fetch_watchlist_quotes_tushare(watchlist, trade_date)
        if results:
            return results, "tushare"
    return [], "none"


def fetch_global_assets(assets):
    """Fetch global asset quotes from Yahoo Finance."""
    if not assets:
        return []
    symbols = ",".join(a["symbol"] for a in assets)
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}"
    try:
        data = _fetch_json(url)
    except Exception:
        return []
    quote_list = data.get("quoteResponse", {}).get("result", []) if data else []
    quote_map = {q.get("symbol"): q for q in quote_list}
    results = []
    for a in assets:
        q = quote_map.get(a["symbol"], {})
        results.append({
            "name": a["name"],
            "symbol": a["symbol"],
            "price": q.get("regularMarketPrice", "-"),
            "change_pct": q.get("regularMarketChangePercent", 0),
            "change_amt": q.get("regularMarketChange", "-"),
            "time": q.get("regularMarketTime", None),
        })
    return results


def fetch_global_assets_stock_analysis(assets):
    """Fetch global assets via stock-analysis skill (Yahoo Finance backend)."""
    if not assets:
        return []
    base_dir = "/Users/yibiao/.openclaw/skills/stock-analysis"
    script = os.path.join(base_dir, "scripts", "analyze_stock.py")
    if not os.path.exists(script):
        return []
    results = []
    for a in assets:
        symbol = a.get("symbol")
        if not symbol:
            continue
        try:
            cmd = [
                "/Users/yibiao/.openclaw/workspace/venv/bin/python",
                script,
                symbol,
                "--fast",
                "--output",
                "json",
            ]
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            data = json.loads(out.decode("utf-8", "ignore"))
            price = data.get("current_price", "-")
            change_amt = data.get("change", data.get("price_change", "-"))
            change_pct = data.get("change_percent", 0)
            results.append({
                "name": a.get("name", symbol),
                "symbol": symbol,
                "price": price,
                "change_pct": change_pct,
                "change_amt": change_amt,
                "time": data.get("timestamp", None),
            })
        except Exception:
            continue
    return results


def fetch_watchlist_quotes_tushare(watchlist, trade_date=None):
    """Fetch watchlist quotes via tushare daily data."""
    pro = _get_tushare()
    if pro is None:
        return []
    results = []
    target_date = trade_date or dt.date.today().strftime("%Y%m%d")
    for item in watchlist:
        code = item.get("code")
        if not code:
            continue
        ts_code = f"{code}.SZ" if code.startswith("0") or code.startswith("3") else f"{code}.SH"
        try:
            df = pro.daily(ts_code=ts_code, start_date=target_date, end_date=target_date)
            if df is None or df.empty:
                continue
            row = df.iloc[0]
            prev = row.get("pre_close", None)
            close = row.get("close", None)
            change_pct = ((close - prev) / prev * 100) if prev else 0
            results.append({
                "code": code,
                "name": item.get("name", ""),
                "price": close,
                "change_pct": change_pct,
                "change_amt": close - prev if prev else "-",
                "volume": row.get("vol", 0),
                "turnover": row.get("amount", 0) * 1000,  # 千元->元
                "amplitude": "-",
            })
        except Exception:
            continue
    return results


def analyze_stock_8dim(symbol):
    """Use stock-analysis skill to get 8-dimension analysis for a stock."""
    base_dir = "/Users/yibiao/.openclaw/skills/stock-analysis"
    script = os.path.join(base_dir, "scripts", "analyze_stock.py")
    if not os.path.exists(script):
        return None
    try:
        cmd = [
            "/Users/yibiao/.openclaw/workspace/venv/bin/python",
            script,
            symbol,
            "--fast",
            "--output",
            "json",
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=30)
        data = json.loads(out.decode("utf-8", "ignore"))
        return {
            "ticker": data.get("ticker", symbol),
            "signal": data.get("signal", "HOLD"),
            "score": data.get("composite_score", 0),
            "current_price": data.get("current_price", "-"),
            "change_pct": data.get("change_percent", 0),
            "earnings_score": data.get("earnings_surprise", {}).get("score", 0),
            "fundamentals_score": data.get("fundamentals", {}).get("score", 0),
            "analyst_score": data.get("analyst_sentiment", {}).get("score", 0),
            "momentum_score": data.get("momentum", {}).get("score", 0),
            "sentiment_score": data.get("sentiment", {}).get("score", 0),
            "sector_score": data.get("sector_comparison", {}).get("score", 0),
            "summary": data.get("summary", ""),
        }
    except Exception:
        return None


def _analysis_code(analysis):
    ticker = str((analysis or {}).get("ticker", ""))
    return ticker.split(".")[0] if "." in ticker else ticker


def _analysis_looks_empty(analysis):
    if not analysis:
        return True
    score = _safe_float(analysis.get("score", 0))
    price = analysis.get("current_price", "-")
    summary = str(analysis.get("summary", "") or "").strip()
    dimensions = analysis.get("dimensions") or []
    dim_sum = sum(_safe_float(dim.get("score", 0)) for dim in dimensions)
    has_price = price not in [None, "", "-"] and _safe_float(price, 0) > 0
    return score <= 0 and dim_sum <= 0 and not has_price and not summary


def build_watchlist_analysis_data(watchlist, trade_date, benchmark_klines=None, prefer_realtime=False):
    """Build watchlist analysis with realtime analyzer fallback to A-share historical scorer."""
    results = []
    for item in watchlist:
        code = item.get("code")
        if not code:
            continue
        analysis = None
        if prefer_realtime:
            ts_code = f"{code}.SZ" if code.startswith(("0", "3")) else f"{code}.SH"
            analysis = analyze_stock_8dim(ts_code)
        if _analysis_looks_empty(analysis):
            analysis = analyze_watchlist_stock_historical(
                item,
                trade_date,
                benchmark_klines=benchmark_klines,
            )
        if analysis:
            results.append(analysis)
    return results


def _secid_from_code(code):
    market = "0" if str(code).startswith(("0", "3")) else "1"
    return f"{market}.{code}"


def _mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else 0.0


def _pct_return(closes, lookback):
    if len(closes) <= lookback:
        return 0.0
    prev = closes[-lookback - 1]
    if not prev:
        return 0.0
    return (closes[-1] - prev) / prev * 100


def _clip_score(value):
    return max(0.0, min(100.0, float(value)))


def _score_from_thresholds(value, bands):
    for threshold, score in bands:
        if value >= threshold:
            return score
    return bands[-1][1]


def fetch_stock_industry_name(code):
    """Fetch stock industry name via Eastmoney company profile."""
    if code in _STOCK_INFO_CACHE:
        return _STOCK_INFO_CACHE[code]
    ak = _get_akshare()
    if ak is None:
        return None
    try:
        df = _call_akshare(ak.stock_individual_info_em, symbol=code)
        info = {
            str(row["item"]): row["value"]
            for _, row in df.iterrows()
        }
        industry = info.get("行业")
        _STOCK_INFO_CACHE[code] = industry
        return industry
    except Exception:
        _STOCK_INFO_CACHE[code] = None
        return None


def analyze_watchlist_stock_historical(item, trade_date, benchmark_klines=None):
    """Generate an A-share-specific 8-dimension historical score."""
    code = item.get("code")
    secid = item.get("secid") or _secid_from_code(code)
    klines = fetch_kline(secid, count=120, end_date=trade_date)
    if len(klines) < 25:
        return None

    closes = [row["close"] for row in klines]
    volumes = [row["volume"] for row in klines]
    turnover = [row["turnover"] for row in klines]
    returns_1d = klines[-1]["change_pct"]
    ret_5 = _pct_return(closes, 5)
    ret_20 = _pct_return(closes, 20)
    ret_60 = _pct_return(closes, 60)
    ma5 = _mean(closes[-5:])
    ma10 = _mean(closes[-10:])
    ma20 = _mean(closes[-20:])
    rsi = _compute_rsi(closes, 14) or 50.0
    vol_ratio = volumes[-1] / _mean(volumes[-6:-1]) if _mean(volumes[-6:-1]) else 1.0
    amp20 = _mean([row["amplitude"] for row in klines[-20:]])
    drawdown_60 = (closes[-1] / max(closes[-60:]) - 1) * 100 if len(closes) >= 60 else 0.0
    avg_turnover_20 = _mean(turnover[-20:]) / 1e8

    benchmark_ret_20 = 0.0
    if benchmark_klines and len(benchmark_klines) > 20:
        bench_closes = [row["close"] for row in benchmark_klines]
        benchmark_ret_20 = _pct_return(bench_closes, 20)
    relative_strength = ret_20 - benchmark_ret_20

    industry_name = item.get("industry") or fetch_stock_industry_name(code)
    sector_ret_20 = None
    if industry_name:
        try:
            sector_rows = _get_ths_board_history("industry", industry_name)
            sector_row = _history_row_on_or_before(sector_rows, trade_date)
            if sector_row:
                sector_closes = [row["close"] for row in sector_rows if row["date"] <= sector_row["date"]]
                sector_ret_20 = _pct_return(sector_closes, 20)
        except Exception:
            sector_ret_20 = None

    trend_score = 80 if closes[-1] > ma5 > ma10 > ma20 else 65 if closes[-1] > ma20 else 35 if closes[-1] < ma20 else 50
    momentum_score = _clip_score(50 + ret_5 * 4 + ret_20 * 1.5)
    rsi_score = 80 if 45 <= rsi <= 65 else 65 if 35 <= rsi < 45 or 65 < rsi <= 72 else 35 if rsi < 25 or rsi > 80 else 50
    volume_score = _clip_score(50 + (vol_ratio - 1) * 25 + max(0, returns_1d) * 1.5)
    volatility_score = _clip_score(80 - amp20 * 4)
    relative_score = _clip_score(50 + relative_strength * 4)
    sector_score = 50.0 if sector_ret_20 is None else _clip_score(50 + (ret_20 - sector_ret_20) * 4)
    liquidity_score = _score_from_thresholds(avg_turnover_20, [(80, 85), (30, 72), (10, 60), (3, 48), (0, 35)])
    drawdown_score = 78 if drawdown_60 >= -8 else 62 if drawdown_60 >= -15 else 45 if drawdown_60 >= -25 else 30

    dimensions = [
        ("趋势", trend_score),
        ("动量", momentum_score),
        ("RSI", rsi_score),
        ("量能", volume_score),
        ("波动", volatility_score),
        ("相对强弱", relative_score),
        ("行业强弱", sector_score),
        ("回撤", drawdown_score),
    ]
    score = round(_mean([score for _, score in dimensions]), 1)
    signal = "BUY" if score >= 70 else "SELL" if score <= 40 else "HOLD"

    summary_bits = []
    if closes[-1] > ma20:
        summary_bits.append("站上20日线")
    else:
        summary_bits.append("仍在20日线下方")
    if relative_strength > 5:
        summary_bits.append("明显跑赢沪深300")
    elif relative_strength < -5:
        summary_bits.append("明显弱于沪深300")
    if sector_ret_20 is not None:
        if ret_20 > sector_ret_20:
            summary_bits.append(f"强于所属行业「{industry_name}」")
        else:
            summary_bits.append(f"弱于所属行业「{industry_name}」")
    if vol_ratio >= 1.5:
        summary_bits.append("量能放大")
    if rsi > 72:
        summary_bits.append("短线偏热")
    elif rsi < 30:
        summary_bits.append("短线偏冷")

    return {
        "ticker": f"{code}.SZ" if code.startswith(("0", "3")) else f"{code}.SH",
        "signal": signal,
        "score": score,
        "current_price": closes[-1],
        "change_pct": returns_1d,
        "industry_name": industry_name,
        "dimensions": [{"name": name, "score": round(value, 1)} for name, value in dimensions],
        "summary": "；".join(summary_bits),
    }



# -- 4) Market breadth -----------------------------------------------------

def fetch_market_breadth():
    """Fetch all A-share stocks change % and compute breadth stats."""
    # 优先尝试东方财富行情API获取全市场涨跌数据
    try:
        url = (
            f"{API_BASE}/clist/get?pn=1&pz=6000&np=1&fltt=2&invt=2&fid=f3"
            f"&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
            f"&fields=f3"
        )
        data = _fetch_json(url)
        stats = {
            "up": 0, "down": 0, "flat": 0,
            "limit_up": 0, "limit_down": 0,
            "big_up": 0, "big_down": 0,
            "total": 0,
        }
        if data and data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"]:
                pct = item.get("f3")
                if pct is None or pct == "-":
                    continue
                pct = _safe_float(pct)
                stats["total"] += 1
                if pct > 0:
                    stats["up"] += 1
                elif pct < 0:
                    stats["down"] += 1
                else:
                    stats["flat"] += 1
                if pct >= 9.9:
                    stats["limit_up"] += 1
                elif pct >= 5.0:
                    stats["big_up"] += 1
                if pct <= -9.9:
                    stats["limit_down"] += 1
                elif pct <= -5.0:
                    stats["big_down"] += 1
        
        # 如果数据不完整，尝试从首页接口补充涨跌家数
        if stats["total"] < 1000:
            try:
                home_url = "https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001&fields=f104,f105,f106,f107,f108,f109"
                home_data = _fetch_json(home_url)
                if home_data and home_data.get("data") and home_data["data"].get("diff"):
                    item = home_data["data"]["diff"][0]
                    stats["up"] = int(item.get("f104", stats["up"]))  # 上涨家数
                    stats["down"] = int(item.get("f105", stats["down"]))  # 下跌家数
                    stats["flat"] = int(item.get("f106", stats["flat"]))  # 平盘家数
                    stats["limit_up"] = int(item.get("f107", stats["limit_up"]))  # 涨停数
                    stats["limit_down"] = int(item.get("f108", stats["limit_down"]))  # 跌停数
                    stats["total"] = stats["up"] + stats["down"] + stats["flat"]
            except Exception:
                pass
    except Exception:
        # Fallback: 返回合理的默认值
        stats = {
            "up": 0, "down": 0, "flat": 0,
            "limit_up": 0, "limit_down": 0,
            "big_up": 0, "big_down": 0,
            "total": 0,
        }
    
    return stats


# -- 5) K-line data --------------------------------------------------------

def fetch_kline(secid, count=30, end_date=None, beg_date=None):
    """Fetch daily K-line data for an index / stock."""
    end = _to_ymd(end_date) if end_date else "20500101"
    beg = f"&beg={_to_ymd(beg_date)}" if beg_date else ""
    url = (
        f"{API_HIS_BASE}/stock/kline/get?"
        f"secid={secid}&fields1=f1,f2,f3,f4,f5,f6"
        f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        f"&klt=101&fqt=1&end={end}{beg}&lmt={count}"
    )
    data = _fetch_json(url)
    results = []
    if data and data.get("data") and data["data"].get("klines"):
        for line in data["data"]["klines"]:
            parts = line.split(",")
            if len(parts) >= 11:
                results.append({
                    "date": parts[0],
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": float(parts[5]),
                    "turnover": float(parts[6]),
                    "amplitude": float(parts[7]),
                    "change_pct": float(parts[8]),
                    "change_amt": float(parts[9]),
                    "turnover_rate": float(parts[10]),
                })
    return results


def fetch_indices_historical(trade_date):
    """Fetch major index data for a resolved trade date."""
    results = []
    for secid, display_name in INDEX_SECIDS.items():
        try:
            klines = fetch_kline(secid, count=2, end_date=trade_date)
            if not klines:
                continue
            row = klines[-1]
            results.append({
                "code": secid.split(".")[1],
                "name": display_name,
                "price": f"{row['close']:.2f}",
                "change_pct": row["change_pct"],
                "change_amt": f"{row['change_amt']:.2f}",
                "volume": row["volume"],
                "turnover": row["turnover"],
                "amplitude": row["amplitude"],
                "high": f"{row['high']:.2f}",
                "low": f"{row['low']:.2f}",
                "open": f"{row['open']:.2f}",
                "prev_close": f"{(row['close'] - row['change_amt']):.2f}",
            })
        except Exception:
            continue
    return results


def fetch_watchlist_quotes_historical(watchlist, trade_date):
    """Fetch watchlist close snapshot for a historical trade date."""
    results = []
    for item in watchlist:
        secid = item.get("secid")
        if not secid:
            continue
        try:
            klines = fetch_kline(secid, count=2, end_date=trade_date)
            row = _history_row_on_or_before(klines, trade_date)
            if not row:
                continue
            prev_close = row.get("prev_close")
            if prev_close is None:
                prev_close = row["close"] - row["change_amt"]
            results.append({
                "code": item.get("code", secid.split(".")[1]),
                "name": item.get("name", ""),
                "price": row["close"],
                "change_pct": row["change_pct"],
                "change_amt": row["change_amt"],
                "volume": row["volume"],
                "turnover": row["turnover"],
                "amplitude": row["amplitude"],
                "high": row["high"],
                "low": row["low"],
                "open": row["open"],
                "prev_close": prev_close,
                "trade_date": row["date"],
            })
        except Exception:
            continue
    return results


def _fetch_yahoo_history(symbol, trade_date):
    """Fetch daily history around trade date from Yahoo chart API."""
    target = _to_date(trade_date)
    cache_key = (symbol, _to_ymd(trade_date))
    cached = _YAHOO_HISTORY_CACHE.get(cache_key)
    if cached is not None:
        return cached

    start = int(dt.datetime.combine(target - dt.timedelta(days=10), dt.time()).timestamp())
    end = int(dt.datetime.combine(target + dt.timedelta(days=2), dt.time()).timestamp())
    symbol_q = urllib.parse.quote(symbol, safe="")
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol_q}"
        f"?period1={start}&period2={end}&interval=1d&includePrePost=false&events=div,splits"
    )
    data = _fetch_json(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.yahoo.com/"})
    result = (data.get("chart", {}).get("result") or [None])[0]
    if not result:
        _YAHOO_HISTORY_CACHE[cache_key] = []
        return []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    timestamps = result.get("timestamp") or []
    tz_name = result.get("meta", {}).get("exchangeTimezoneName") or "UTC"
    tz = ZoneInfo(tz_name)
    rows = []
    prev_close = None
    for idx, ts in enumerate(timestamps):
        close = (quote.get("close") or [None])[idx]
        open_price = (quote.get("open") or [None])[idx]
        high = (quote.get("high") or [None])[idx]
        low = (quote.get("low") or [None])[idx]
        volume = _safe_float((quote.get("volume") or [0])[idx])
        if close is None:
            continue
        local_date = dt.datetime.fromtimestamp(ts, tz).date().strftime("%Y%m%d")
        change_amt = 0.0 if prev_close is None else float(close) - float(prev_close)
        pct_change = 0.0 if prev_close in [None, 0] else change_amt / float(prev_close) * 100
        rows.append({
            "date": local_date,
            "open": _safe_float(open_price),
            "close": _safe_float(close),
            "high": _safe_float(high),
            "low": _safe_float(low),
            "volume": volume,
            "change_amt": change_amt,
            "change_pct": pct_change,
        })
        prev_close = close
    _YAHOO_HISTORY_CACHE[cache_key] = rows
    return rows


def _fetch_dollar_index_history(trade_date):
    rows = fetch_kline("100.UDI", count=15, end_date=trade_date)
    return rows


def _fetch_foreign_future_history(contract_symbol):
    ak = _get_akshare()
    if ak is None:
        return []
    df = _call_akshare(ak.futures_foreign_hist, symbol=contract_symbol)
    if df is None or df.empty:
        return []
    rows = []
    prev_close = None
    for raw in df.to_dict("records"):
        close = _safe_float(raw.get("close"))
        open_price = _safe_float(raw.get("open"))
        high = _safe_float(raw.get("high"))
        low = _safe_float(raw.get("low"))
        change_amt = 0.0 if prev_close is None else close - prev_close
        pct_change = 0.0 if prev_close in [None, 0] else change_amt / prev_close * 100
        rows.append({
            "date": _to_ymd(raw.get("date")),
            "open": open_price,
            "close": close,
            "high": high,
            "low": low,
            "volume": _safe_float(raw.get("volume")),
            "change_amt": change_amt,
            "change_pct": pct_change,
        })
        prev_close = close
    return rows


def fetch_global_assets_historical(assets, trade_date):
    """Fetch global assets as of historical trade date."""
    results = []
    for asset in assets:
        try:
            if asset["name"] == "美元指数":
                rows = _fetch_dollar_index_history(trade_date)
            elif asset["symbol"] == "GC=F":
                rows = _fetch_foreign_future_history("GC")
            elif asset["symbol"] == "CL=F":
                rows = _fetch_foreign_future_history("CL")
            else:
                rows = _fetch_yahoo_history(asset["symbol"], trade_date)
            row = _history_row_on_or_before(rows, trade_date)
            if not row:
                continue
            results.append({
                "name": asset["name"],
                "symbol": asset["symbol"],
                "price": row["close"],
                "change_pct": row["change_pct"],
                "change_amt": row["change_amt"],
                "time": row["date"],
            })
        except Exception:
            continue
    return results


def _get_ths_board_names(board_type):
    """Load cached THS board names."""
    if board_type in _THS_NAME_CACHE:
        return _THS_NAME_CACHE[board_type]
    cache_path = CACHE_DIR / f"ths_{board_type}_names.json"
    cached = _load_json_cache(cache_path)
    if cached:
        _THS_NAME_CACHE[board_type] = cached
        return cached

    ak = _get_akshare()
    if ak is None:
        return []
    if board_type == "industry":
        df = _call_akshare(ak.stock_board_industry_name_ths)
    else:
        df = _call_akshare(ak.stock_board_concept_name_ths)
    rows = df.to_dict("records") if df is not None else []
    _THS_NAME_CACHE[board_type] = rows
    _save_json_cache(cache_path, rows)
    return rows


def _get_ths_board_history(board_type, board_name):
    """Fetch and memoize full THS board history."""
    cache_key = (board_type, board_name)
    if cache_key in _THS_BOARD_HISTORY_CACHE:
        return _THS_BOARD_HISTORY_CACHE[cache_key]
    cache_path = CACHE_DIR / f"ths_{board_type}_{_cache_key(board_name)}.json"
    cached = _load_json_cache(cache_path)
    if cached:
        _THS_BOARD_HISTORY_CACHE[cache_key] = cached
        return cached

    ak = _get_akshare()
    if ak is None:
        return []
    if board_type == "industry":
        df = _call_akshare(ak.stock_board_industry_index_ths, symbol=board_name)
    else:
        df = _call_akshare(ak.stock_board_concept_index_ths, symbol=board_name)
    rows = _rows_to_history_payload(df.to_dict("records")) if df is not None else []
    _THS_BOARD_HISTORY_CACHE[cache_key] = rows
    _save_json_cache(cache_path, rows)
    return rows


def _fetch_board_snapshot(board_type, board_meta, trade_date):
    try:
        rows = _get_ths_board_history(board_type, board_meta["name"])
        row = _history_row_on_or_before(rows, trade_date)
        if not row:
            return None
        return {
            "code": board_meta.get("code", ""),
            "name": board_meta["name"],
            "price": row["close"],
            "change_pct": row["change_pct"],
            "change_amt": row["change_amt"],
            "up_count": "-",
            "down_count": "-",
            "lead_stock": "-",
            "lead_stock_pct": "-",
            "trade_date": row["date"],
            "history": rows,
        }
    except Exception:
        return None


def fetch_sector_ranking_historical(board_type, trade_date, count=10):
    """Compute historical THS board ranking for a given trade date."""
    names = _get_ths_board_names(board_type)
    if not names:
        return []
    snapshots = []
    for meta in names:
        snapshot = _fetch_board_snapshot(board_type, meta, trade_date)
        if snapshot is not None:
            snapshots.append(snapshot)
    snapshots.sort(key=lambda item: item.get("change_pct", -999), reverse=True)
    if count and count > 0:
        return snapshots[:count]
    return snapshots


def _match_theme_board(board_type, keywords):
    candidates = _get_ths_board_names(board_type)
    matches = []
    for item in candidates:
        name = item.get("name", "")
        best = max((len(k) for k in keywords if k in name), default=0)
        if best:
            matches.append((best, len(name), item))
    if not matches:
        return None
    matches.sort(key=lambda entry: (-entry[0], entry[1], entry[2]["name"]))
    return matches[0][2]


def summarize_focus_themes_historical(industry_all, trade_date):
    """Resolve user focus themes against THS concept/industry boards."""
    focus_rows = []
    industry_rank = {item["name"]: idx + 1 for idx, item in enumerate(industry_all)}
    for theme, keywords in FOCUS_THEMES.items():
        best_source = None
        best_row = None

        concept_meta = _match_theme_board("concept", keywords)
        if concept_meta:
            concept_row = _fetch_board_snapshot("concept", concept_meta, trade_date)
            if concept_row:
                best_source = "概念"
                best_row = concept_row

        if best_row is None:
            industry_meta = _match_theme_board("industry", keywords)
            if industry_meta:
                industry_row = _fetch_board_snapshot("industry", industry_meta, trade_date)
                if industry_row:
                    best_source = "行业"
                    best_row = industry_row

        if best_row is None:
            focus_rows.append({
                "theme": theme,
                "source": "-",
                "rank": "-",
                "board": "未匹配到历史板块",
                "change_pct": None,
            })
            continue

        rank = industry_rank.get(best_row["name"], "-") if best_source == "行业" else "-"
        focus_rows.append({
            "theme": theme,
            "source": best_source,
            "rank": rank,
            "board": best_row["name"],
            "change_pct": best_row["change_pct"],
        })
    return focus_rows


# -- 6) News scraping ------------------------------------------------------

def fetch_news_links():
    """Scrape news links from Eastmoney finance homepage."""
    html = _fetch_html(EASTMONEY_NEWS_URL)
    links = re.findall(
        r'<a[^>]+href="(https?://finance\.eastmoney\.com/a/[^\"]+)"[^>]*>(.*?)</a>',
        html,
    )
    items = []
    seen = set()
    for href, text in links:
        text = re.sub(r"<.*?>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text and len(text) > 6 and text not in seen:
            seen.add(text)
            items.append((text, href))
    return items


def summarize_focus_themes(concept_list, industry_list):
    """Find performance of user focus themes from concept/industry lists."""
    focus_rows = []
    for theme, keywords in FOCUS_THEMES.items():
        best = None
        # search concept list
        for idx, item in enumerate(concept_list or []):
            name = item.get("name", "")
            if any(k in name for k in keywords):
                best = ("概念", idx + 1, name, item)
                break
        # fallback to industry list
        if best is None:
            for idx, item in enumerate(industry_list or []):
                name = item.get("name", "")
                if any(k in name for k in keywords):
                    best = ("行业", idx + 1, name, item)
                    break
        if best is None:
            focus_rows.append({
                "theme": theme,
                "source": "-",
                "rank": "-",
                "board": "未进榜",
                "change_pct": None,
            })
        else:
            src, rank, board_name, item = best
            focus_rows.append({
                "theme": theme,
                "source": src,
                "rank": rank,
                "board": board_name,
                "change_pct": item.get("change_pct", 0),
            })
    return focus_rows


# ───────────────────── Chart Generation ───────────────────────────────────

_PLT = None  # lazy-loaded


def _setup_matplotlib():
    """Setup matplotlib with Chinese font support. Returns plt or None."""
    global _PLT
    if _PLT is not None:
        return _PLT
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        chinese_fonts = [
            "PingFang HK", "Songti SC", "Heiti TC", "STHeiti",
            "Kaiti SC", "Arial Unicode MS", "SimHei", "WenQuanYi Micro Hei",
        ]
        matplotlib.rcParams["font.sans-serif"] = chinese_fonts
        matplotlib.rcParams["axes.unicode_minus"] = False
        matplotlib.rcParams["figure.dpi"] = 150
        matplotlib.rcParams["savefig.bbox"] = "tight"
        matplotlib.rcParams["savefig.facecolor"] = "white"

        _PLT = plt
        return plt
    except ImportError:
        print("   ⚠️  matplotlib unavailable, skipping charts.")
        return None


def generate_kline_chart(kline_data, outdir, stem="index_kline"):
    """Generate K-line + MA + Volume chart for major indices. Returns filename."""
    plt = _setup_matplotlib()
    if plt is None:
        return None

    indices_to_plot = [(n, d) for n, d in kline_data.items() if d]
    if not indices_to_plot:
        return None

    n_panels = len(indices_to_plot)
    fig, axes = plt.subplots(n_panels, 1, figsize=(15, 4.5 * n_panels), squeeze=False)
    fig.suptitle("A股主要指数近期走势", fontsize=17, fontweight="bold", y=0.995)

    palette = {"上证指数": "#E74C3C", "深证成指": "#3498DB", "创业板指": "#27AE60"}

    for idx, (name, klines) in enumerate(indices_to_plot):
        ax = axes[idx][0]
        dates = [k["date"][-5:] for k in klines]
        closes = [k["close"] for k in klines]
        opens = [k["open"] for k in klines]
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]
        volumes = [k["turnover"] / 1e8 for k in klines]
        changes = [k["change_pct"] for k in klines]
        x = list(range(len(dates)))

        # Candlestick
        for i in x:
            c = "#E74C3C" if closes[i] >= opens[i] else "#27AE60"
            body_lo = min(opens[i], closes[i])
            body_hi = max(opens[i], closes[i])
            body_h = body_hi - body_lo or (closes[i] * 0.001)
            ax.add_patch(plt.Rectangle(
                (i - 0.35, body_lo), 0.7, body_h,
                facecolor=c, edgecolor=c, linewidth=0.8,
            ))
            ax.plot([i, i], [lows[i], highs[i]], color=c, linewidth=0.7)

        ax.set_xlim(-0.8, len(dates) - 0.2)
        ax.set_ylim(min(lows) * 0.998, max(highs) * 1.002)

        # Moving averages
        def _ma(data, period):
            return [
                sum(data[max(0, i - period + 1): i + 1]) / min(i + 1, period)
                for i in range(len(data))
            ]

        if len(closes) >= 5:
            ax.plot(x, _ma(closes, 5), color="#F39C12", linewidth=1.2,
                    linestyle="--", alpha=0.85, label="MA5")
        if len(closes) >= 10:
            ax.plot(x, _ma(closes, 10), color="#9B59B6", linewidth=1.2,
                    linestyle="-.", alpha=0.85, label="MA10")
        if len(closes) >= 20:
            ax.plot(x, _ma(closes, 20), color="#1ABC9C", linewidth=1.2,
                    linestyle=":", alpha=0.85, label="MA20")

        ax.set_title(f"{name}  收盘 {closes[-1]:.2f}  ({changes[-1]:+.2f}%)",
                     fontsize=13, fontweight="bold")
        ax.set_ylabel("点位", fontsize=10)
        ax.legend(loc="upper left", fontsize=8, framealpha=0.7)
        ax.grid(True, alpha=0.25)
        ax.set_xticks(x)
        ax.set_xticklabels(dates, fontsize=7, rotation=45)
        step = max(1, len(dates) // 10)
        for i, lbl in enumerate(ax.xaxis.get_ticklabels()):
            if i % step != 0:
                lbl.set_visible(False)

        # Volume bars
        ax2 = ax.twinx()
        bar_colors = ["#E74C3C" if c >= 0 else "#27AE60" for c in changes]
        ax2.bar(x, volumes, alpha=0.25, color=bar_colors, width=0.55)
        ax2.set_ylabel("成交额(亿元)", fontsize=8, alpha=0.6)
        ax2.tick_params(axis="y", labelsize=7)
        ax2.set_ylim(0, max(volumes) * 3)

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    fname = f"{stem}.png"
    fig.savefig(outdir / fname, dpi=150)
    plt.close(fig)
    return fname


def generate_sector_chart(sectors_up, sectors_down, outdir, stem="sector_ranking"):
    """Horizontal bar chart of top gaining/losing sectors."""
    plt = _setup_matplotlib()
    if plt is None:
        return None
    if not sectors_up and not sectors_down:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("行业板块涨跌排行", fontsize=17, fontweight="bold")

    if sectors_up:
        names = [s["name"] for s in reversed(sectors_up[:10])]
        pcts = [_safe_float(s["change_pct"]) for s in reversed(sectors_up[:10])]
        colors = ["#E74C3C" if p >= 0 else "#27AE60" for p in pcts]
        bars = ax1.barh(names, pcts, color=colors, height=0.55, edgecolor="white")
        ax1.set_title("涨幅 Top 10", fontsize=13, fontweight="bold", color="#C0392B")
        ax1.set_xlabel("涨跌幅 (%)")
        for bar, pct in zip(bars, pcts):
            ax1.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height() / 2,
                     f"{pct:+.2f}%", va="center", fontsize=9, fontweight="bold")
        ax1.grid(True, axis="x", alpha=0.25)
    else:
        ax1.text(0.5, 0.5, "暂无数据", transform=ax1.transAxes, ha="center")

    if sectors_down:
        names = [s["name"] for s in sectors_down[:10]]
        pcts = [_safe_float(s["change_pct"]) for s in sectors_down[:10]]
        colors = ["#E74C3C" if p >= 0 else "#27AE60" for p in pcts]
        bars = ax2.barh(names, pcts, color=colors, height=0.55, edgecolor="white")
        ax2.set_title("跌幅 Top 10", fontsize=13, fontweight="bold", color="#27AE60")
        ax2.set_xlabel("涨跌幅 (%)")
        for bar, pct in zip(bars, pcts):
            offset = bar.get_width() - 0.08 if pct < 0 else bar.get_width() + 0.08
            ha = "right" if pct < 0 else "left"
            ax2.text(offset, bar.get_y() + bar.get_height() / 2,
                     f"{pct:+.2f}%", va="center", fontsize=9, fontweight="bold", ha=ha)
        ax2.grid(True, axis="x", alpha=0.25)
    else:
        ax2.text(0.5, 0.5, "暂无数据", transform=ax2.transAxes, ha="center")

    plt.tight_layout()
    fname = f"{stem}.png"
    fig.savefig(outdir / fname, dpi=150)
    plt.close(fig)
    return fname


def generate_breadth_chart(stats, outdir, stem="market_breadth"):
    """Pie chart + bar chart for market breadth."""
    plt = _setup_matplotlib()
    if plt is None or stats["total"] == 0:
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle("市场情绪全景", fontsize=17, fontweight="bold")

    labels = ["上涨", "下跌", "平盘"]
    sizes = [stats["up"], stats["down"], stats["flat"]]
    colors_pie = ["#E74C3C", "#27AE60", "#BDC3C7"]
    explode = (0.04, 0.04, 0)
    wedges, texts, autotexts = ax1.pie(
        sizes, explode=explode, labels=labels, colors=colors_pie,
        autopct="%1.1f%%", startangle=90, textprops={"fontsize": 11},
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_fontweight("bold")
    ax1.set_title(f"涨跌分布（共 {stats['total']} 只）", fontsize=12)

    categories = ["涨停", "涨>5%", "跌>5%", "跌停"]
    values = [stats["limit_up"], stats["big_up"], stats["big_down"], stats["limit_down"]]
    bar_colors = ["#E74C3C", "#E67E22", "#2ECC71", "#27AE60"]
    bars = ax2.bar(categories, values, color=bar_colors, width=0.55, edgecolor="white")
    ax2.set_title("极端涨跌统计", fontsize=12)
    ax2.set_ylabel("家数")
    for bar, val in zip(bars, values):
        if val > 0:
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                     str(val), ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax2.grid(True, axis="y", alpha=0.25)

    plt.tight_layout()
    fname = f"{stem}.png"
    fig.savefig(outdir / fname, dpi=150)
    plt.close(fig)
    return fname


# ───────────────────── Market Analysis Engine ─────────────────────────────

def _compute_rsi(closes, period=14):
    """Compute RSI from closing prices list. Returns latest RSI or None."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(diff if diff > 0 else 0)
        losses.append(-diff if diff < 0 else 0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def analyze_market(indices, breadth, kline_sh, industry_up, industry_down,
                   concept_up, is_morning, global_assets=None):
    """Generate multi-dimensional market analysis commentary."""
    analysis = []

    sh = next((i for i in indices if i["code"] == "000001"), None)
    sz = next((i for i in indices if i["code"] == "399001"), None)
    cy = next((i for i in indices if i["code"] == "399006"), None)

    # 1. 大盘走势
    if sh:
        pct = _safe_float(sh["change_pct"])
        price = sh["price"]
        if pct > 2:
            desc = "大幅上涨，市场做多热情高涨"
        elif pct > 1:
            desc = "强势上涨，多头占据明显优势"
        elif pct > 0.3:
            desc = "温和上涨，市场情绪偏暖"
        elif pct > -0.3:
            desc = "窄幅震荡，多空博弈激烈"
        elif pct > -1:
            desc = "小幅回调，空头略占上风"
        elif pct > -2:
            desc = "明显下跌，市场承压运行"
        else:
            desc = "大幅下跌，恐慌情绪蔓延"
        analysis.append(
            f"**大盘走势**：上证指数报 {price} 点，{desc}（{pct:+.2f}%）。"
        )

    # 2. 量能分析
    if sh and sh.get("turnover") and sh["turnover"] != "-":
        turnover = _safe_float(sh["turnover"])
        if turnover >= 1e12:
            vol_desc = ("两市成交额突破万亿，市场交投极为活跃，"
                        "增量资金入场迹象明显")
        elif turnover >= 8000e8:
            vol_desc = "两市成交额维持高位，资金参与意愿较强"
        elif turnover >= 5000e8:
            vol_desc = "两市成交额处于中等水平，存量博弈为主"
        else:
            vol_desc = ("两市成交量能偏弱，市场观望情绪浓厚，"
                        "增量资金不足")
        analysis.append(
            f"**量能分析**：{vol_desc}（成交额 {format_turnover(turnover)}元）。"
        )

    if kline_sh and len(kline_sh) >= 5:
        recent_vol = [k["turnover"] for k in kline_sh[-5:]]
        prev_vol = ([k["turnover"] for k in kline_sh[-10:-5]]
                    if len(kline_sh) >= 10 else [])
        if prev_vol:
            avg_recent = sum(recent_vol) / len(recent_vol)
            avg_prev = sum(prev_vol) / len(prev_vol)
            ratio = avg_recent / avg_prev if avg_prev else 1
            if ratio > 1.3:
                analysis.append(
                    f"**量价配合**：近5日平均成交额较前5日放大 "
                    f"{(ratio-1)*100:.0f}%，量能放大趋势明显，"
                    "关注是否配合价格突破。"
                )
            elif ratio < 0.7:
                analysis.append(
                    f"**量价配合**：近5日成交额较前5日萎缩 "
                    f"{(1-ratio)*100:.0f}%，市场交投趋于清淡。"
                )

    # 3. 创业板风格
    if cy and sh:
        cy_pct = _safe_float(cy["change_pct"])
        sh_pct = _safe_float(sh["change_pct"])
        diff = cy_pct - sh_pct
        if diff > 0.5:
            analysis.append(
                f"**风格分化**：创业板指（{cy_pct:+.2f}%）明显强于"
                f"主板（{sh_pct:+.2f}%），成长/科技风格占优，"
                "市场风险偏好提升。"
            )
        elif diff < -0.5:
            analysis.append(
                f"**风格分化**：创业板指（{cy_pct:+.2f}%）弱于"
                f"主板（{sh_pct:+.2f}%），资金偏好大盘蓝筹和"
                "防御性品种，避险情绪升温。"
            )

    # 4. 市场广度
    if breadth and breadth["total"] > 0:
        up_ratio = breadth["up"] / breadth["total"] * 100
        if up_ratio > 70:
            bd = "普涨格局，赚钱效应极强，可积极参与"
        elif up_ratio > 55:
            bd = "多数个股上涨，赚钱效应较好"
        elif up_ratio > 45:
            bd = "涨跌参半，结构性行情，需精选个股"
        elif up_ratio > 30:
            bd = "多数个股下跌，亏钱效应明显，宜控制仓位"
        else:
            bd = "普跌格局，市场风险偏好极低，建议观望为主"
        analysis.append(
            f"**市场宽度**：上涨 {breadth['up']} 家 vs "
            f"下跌 {breadth['down']} 家"
            f"（涨跌比 {breadth['up']}:{breadth['down']}），{bd}。"
            f"涨停 {breadth['limit_up']} 家，"
            f"跌停 {breadth['limit_down']} 家。"
        )

    # 5. 技术面 (K线 + 均线 + RSI)
    if kline_sh and len(kline_sh) >= 5:
        closes = [k["close"] for k in kline_sh]
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else None
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else None
        current = closes[-1]
        rsi = _compute_rsi(closes, 14)

        tech_parts = []

        # Consecutive trend detection
        up_days = 0
        for i in range(len(closes) - 1, 0, -1):
            if closes[i] >= closes[i - 1]:
                up_days += 1
            else:
                break
        down_days = 0
        for i in range(len(closes) - 1, 0, -1):
            if closes[i] <= closes[i - 1]:
                down_days += 1
            else:
                break

        if up_days >= 5:
            tech_parts.append(
                f"指数连续{up_days}日收阳，短线偏强但注意超买回调风险"
            )
        elif up_days >= 3:
            tech_parts.append(f"指数连续{up_days}日反弹，短期趋势向好")
        elif down_days >= 5:
            tech_parts.append(
                f"指数连续{down_days}日收阴，短线偏弱，关注能否企稳"
            )
        elif down_days >= 3:
            tech_parts.append(f"指数连续{down_days}日调整，注意下方支撑")

        # MA alignment
        if ma20 is not None:
            if ma10 and current > ma5 > ma10 > ma20:
                tech_parts.append("均线多头排列，中短期趋势偏强")
            elif current < ma5 < ma20:
                tech_parts.append("均线空头排列，中短期趋势偏弱")
            elif current > ma20 and current < ma5:
                tech_parts.append(
                    f"价格回踩5日均线（{ma5:.0f}），"
                    f"20日均线（{ma20:.0f}）提供支撑"
                )

        # RSI
        if rsi is not None:
            if rsi > 80:
                tech_parts.append(
                    f"RSI(14)={rsi:.1f}，已进入超买区间，短线回调概率增大"
                )
            elif rsi > 70:
                tech_parts.append(
                    f"RSI(14)={rsi:.1f}，接近超买，注意高位风险"
                )
            elif rsi < 20:
                tech_parts.append(
                    f"RSI(14)={rsi:.1f}，已进入超卖区间，存在技术性反弹需求"
                )
            elif rsi < 30:
                tech_parts.append(
                    f"RSI(14)={rsi:.1f}，接近超卖，可关注底部信号"
                )
            else:
                tech_parts.append(f"RSI(14)={rsi:.1f}，处于中性区间")

        if tech_parts:
            analysis.append("**技术面**：" + "；".join(tech_parts) + "。")

    # 6. 板块轮动
    if industry_up and concept_up:
        top_ind = [s["name"] for s in industry_up[:3]]
        top_con = [s["name"] for s in concept_up[:3]]
        analysis.append(
            f"**板块轮动**：领涨行业为「{'、'.join(top_ind)}」，"
            f"活跃概念为「{'、'.join(top_con)}」。"
        )
        if industry_down:
            bot_ind = [s["name"] for s in industry_down[:3]]
            analysis.append(
                f"调整板块为「{'、'.join(bot_ind)}」，"
                "注意规避短期弱势方向。"
            )

    # 6.5 宏观联动（美元/黄金/原油）
    if global_assets:
        asset_map = {a["name"]: a for a in global_assets}
        usd = asset_map.get("美元指数")
        gold = asset_map.get("黄金")
        oil = asset_map.get("原油(WTI)")
        macro_parts = []
        if usd and usd.get("change_pct") is not None:
            usd_pct = _safe_float(usd.get("change_pct"))
            if usd_pct > 0.5:
                macro_parts.append("美元走强可能抑制风险偏好与外资情绪")
            elif usd_pct < -0.5:
                macro_parts.append("美元回落有利于风险资产修复")
        if gold and gold.get("change_pct") is not None:
            gold_pct = _safe_float(gold.get("change_pct"))
            if gold_pct > 0.8:
                macro_parts.append("黄金走强体现避险需求升温")
            elif gold_pct < -0.8:
                macro_parts.append("黄金回落，避险情绪有所降温")
        if oil and oil.get("change_pct") is not None:
            oil_pct = _safe_float(oil.get("change_pct"))
            if oil_pct > 1.0:
                macro_parts.append("油价上行推升通胀预期，关注化工/运输成本")
            elif oil_pct < -1.0:
                macro_parts.append("油价走弱有利于成本端缓解")
        if macro_parts:
            analysis.append("**宏观联动**：" + "；".join(macro_parts) + "。")

    # 7. 操作建议
    if is_morning:
        analysis.append(
            "**操作参考**：盘前关注外围市场表现和消息面变化，"
            "若高开则关注持续性，低开则关注支撑位能否企稳。"
            "建议控制仓位，聚焦主线板块。"
        )
    else:
        analysis.append(
            "**后市展望**：关注量能变化和板块轮动节奏，"
            "保持仓位弹性，攻守兼备。"
            "如有突发利好/利空，及时调整策略。"
        )

    return analysis


# ───────────────────── Markdown Composition ───────────────────────────────

def md_table(headers, rows, align=None):
    """Generate a Markdown table string."""
    if not rows:
        return "*暂无数据*\n"
    if align is None:
        align = ["left"] * len(headers)
    sep_map = {"right": "---:", "center": ":---:", "left": ":---"}
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(sep_map.get(a, ":---") for a in align) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines) + "\n"


def compose_report(
    date_str, is_morning, indices, industry_up, industry_down,
    concept_up, stocks_up, stocks_down, breadth, kline_data,
    news, chart_files, watchlist_quotes=None, focus_themes=None,
    global_assets=None, stock_analysis_data=None,
    historical_mode=False, resolved_trade_date=None, data_source_label=None,
):
    """Compose the full enhanced Markdown report."""
    mode = "早报" if is_morning else "晚报"
    gen_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    md = []

    # Header
    md.append(f"# 📊 A股{mode}｜{date_str}")
    md.append("")
    md.append(f"> **生成时间**：{gen_time}（Asia/Shanghai）  ")
    md.append(f"> **数据源**：{data_source_label or '东方财富 / 同花顺 / Yahoo Finance'}  ")
    md.append(f"> **报告类型**：{'盘前参考' if is_morning else '盘后复盘'}")
    if historical_mode and resolved_trade_date:
        md.append(f"> **历史模式**：按交易日回放，实际取数日为 {resolved_trade_date}")
    md.append("")
    md.append("---")
    md.append("")

    # == Section 1: 主要指数行情 ==
    md.append("## 📈 一、主要指数行情")
    md.append("")
    if indices:
        headers = ["指数", "最新价", "涨跌幅", "涨跌额", "振幅",
                   "今开", "最高", "最低", "成交额"]
        align = ["left"] + ["right"] * 8
        rows = []
        for idx in indices:
            rows.append([
                f"**{idx['name']}**",
                f"{idx['price']}" if idx["price"] != "-" else "N/A",
                color_pct(idx["change_pct"]),
                f"{idx['change_amt']}" if idx["change_amt"] != "-" else "N/A",
                f"{idx['amplitude']}%" if idx["amplitude"] != "-" else "N/A",
                f"{idx['open']}" if idx["open"] != "-" else "N/A",
                f"{idx['high']}" if idx["high"] != "-" else "N/A",
                f"{idx['low']}" if idx["low"] != "-" else "N/A",
                format_turnover(idx["turnover"]),
            ])
        md.append(md_table(headers, rows, align))
    else:
        md.append("*指数数据获取失败*\n")
    md.append("")

    # == Section 2: 全球资产 & 宏观联动 ==
    md.append("## 🌍 二、全球资产 & 宏观联动")
    md.append("")
    if global_assets:
        headers = ["资产", "最新价", "涨跌幅", "涨跌额"]
        align = ["left", "right", "right", "right"]
        rows = []
        for a in global_assets:
            price = a.get("price", "-")
            change_pct = a.get("change_pct", 0)
            change_amt = a.get("change_amt", "-")
            rows.append([
                f"**{a.get('name','')}**",
                f"{price}" if price != "-" else "N/A",
                color_pct(change_pct),
                f"{change_amt}" if change_amt != "-" else "N/A",
            ])
        md.append(md_table(headers, rows, align))
        md.append("> **影响解读**：美元、黄金、原油的同向或背离变化，")
        md.append("> 通常反映市场风险偏好与通胀预期变化，对A股风格与板块轮动有指引意义。")
    else:
        md.append("*全球资产历史数据获取失败*\n" if historical_mode else "*全球资产数据获取失败*\n")
    md.append("")

    # == Section 3: 市场情绪 ==
    md.append("## 🌡️ 三、市场情绪")
    md.append("")
    if breadth and breadth["total"] > 0:
        up_ratio = breadth["up"] / breadth["total"] * 100
        bar_len = 20
        up_bars = round(up_ratio / 100 * bar_len)
        down_bars = bar_len - up_bars
        md.append(
            f"**涨跌温度计** {'🟥' * up_bars}{'🟩' * down_bars}"
        )
        md.append("")
        headers = ["指标", "数值", "指标", "数值"]
        align = ["left", "right", "left", "right"]
        rows = [
            ["上涨家数", f"**{breadth['up']}**",
             "下跌家数", f"**{breadth['down']}**"],
            ["平盘家数", f"{breadth['flat']}",
             "涨跌比", f"{breadth['up']}:{breadth['down']}"],
            ["涨停", f"🔴 **{breadth['limit_up']}**",
             "跌停", f"🟢 **{breadth['limit_down']}**"],
            ["涨幅 >5%", f"{breadth['big_up']}",
             "跌幅 >5%", f"{breadth['big_down']}"],
            ["上涨占比", f"**{up_ratio:.1f}%**",
             "总计", f"{breadth['total']}只"],
        ]
        md.append(md_table(headers, rows, align))
    else:
        if historical_mode:
            md.append("*历史模式下未接入全市场宽度快照*\n")
        else:
            md.append("*市场涨跌数据获取失败*\n")
    md.append("")

    if chart_files.get("breadth"):
        md.append(f"![市场情绪全景]({chart_files['breadth']})")
        md.append("")

    # == Section 4: 指数走势图 ==
    if chart_files.get("kline"):
        md.append("## 📉 四、指数走势（近30个交易日）")
        md.append("")
        md.append(f"![指数K线走势图]({chart_files['kline']})")
        md.append("")

    # == Section 5: 行业板块排行 ==
    md.append("## 🏭 五、行业板块表现")
    md.append("")
    md.append("### 涨幅 Top 10")
    md.append("")
    if industry_up:
        headers = ["#", "板块", "涨跌幅", "领涨股", "板块涨/跌家数"]
        align = ["center", "left", "right", "left", "center"]
        rows = []
        for i, s in enumerate(industry_up[:10], 1):
            lead = s.get("lead_stock", "")
            lead_pct = _safe_float(s.get("lead_stock_pct", 0))
            lead_str = (f"{lead}（{lead_pct:+.2f}%）"
                        if lead and lead != "-" else "-")
            rows.append([
                f"{i}", f"**{s['name']}**", color_pct(s["change_pct"]),
                lead_str,
                f"{s.get('up_count', '-')}/{s.get('down_count', '-')}",
            ])
        md.append(md_table(headers, rows, align))
    else:
        md.append("*历史行业板块数据获取失败*\n")
    md.append("")
    md.append("### 跌幅 Top 10")
    md.append("")
    if industry_down:
        headers = ["#", "板块", "涨跌幅", "领跌股", "板块涨/跌家数"]
        align = ["center", "left", "right", "left", "center"]
        rows = []
        for i, s in enumerate(industry_down[:10], 1):
            lead = s.get("lead_stock", "")
            lead_pct = _safe_float(s.get("lead_stock_pct", 0))
            lead_str = (f"{lead}（{lead_pct:+.2f}%）"
                        if lead and lead != "-" else "-")
            rows.append([
                f"{i}", f"**{s['name']}**", color_pct(s["change_pct"]),
                lead_str,
                f"{s.get('up_count', '-')}/{s.get('down_count', '-')}",
            ])
        md.append(md_table(headers, rows, align))
    else:
        md.append("*历史行业板块数据获取失败*\n")
    md.append("")

    if chart_files.get("sector"):
        md.append(f"![行业板块涨跌排行]({chart_files['sector']})")
        md.append("")

    # == Section 6: 热门概念板块 ==
    md.append("## 🔥 六、热门概念 Top 10")
    md.append("")
    if concept_up:
        headers = ["#", "概念", "涨跌幅", "领涨股"]
        align = ["center", "left", "right", "left"]
        rows = []
        for i, s in enumerate(concept_up[:10], 1):
            lead = s.get("lead_stock", "")
            lead_pct = _safe_float(s.get("lead_stock_pct", 0))
            lead_str = (f"{lead}（{lead_pct:+.2f}%）"
                        if lead and lead != "-" else "-")
            rows.append([
                f"{i}", f"**{s['name']}**",
                color_pct(s["change_pct"]), lead_str,
            ])
        md.append(md_table(headers, rows, align))
    else:
        if historical_mode:
            md.append("*历史模式下未启用全量概念排行，请参考关注主题表现*\n")
        else:
            md.append("*概念板块数据暂无*\n")
    md.append("")

    # == Section 7: 关注主题追踪 ==
    md.append("## 🎯 七、关注主题追踪")
    md.append("")
    if focus_themes:
        headers = ["主题", "板块类型", "板块名称", "今日涨跌幅", "排名", "龙头企业表现"]
        align = ["left", "center", "left", "right", "center", "left"]
        rows = []
        for theme in focus_themes:
            theme_name = theme["theme"]
            leaders = THEME_LEADERS.get(theme_name, [])
            leader_str = "、".join(leaders) if leaders else "-"
            rows.append([
                f"**{theme_name}**",
                theme["source"],
                theme["board"],
                color_pct(theme["change_pct"]),
                theme["rank"] if theme["rank"] != "-" else "-",
                leader_str,
            ])
        md.append(md_table(headers, rows, align))
        md.append("")
        
        # 高级分析师分析
        md.append("### 🧐 主题投资分析")
        md.append("")
        md.append("> 作为资深投资分析师，对当前各主题的投资价值点评：")
        md.append("")
        
        # 算力板块分析
        power_theme = next((t for t in focus_themes if t["theme"] == "算力"), None)
        if power_theme and power_theme["change_pct"] is not None:
            power_pct = _safe_float(power_theme["change_pct"])
            if power_pct > 2:
                md.append("- **算力板块**：今日大幅上涨，AI算力需求持续爆发，产业链上游芯片、服务器厂商受益明显，长期赛道确定性高，可逢低布局龙头企业。")
            elif power_pct > 0:
                md.append("- **算力板块**：今日小幅上涨，数字经济政策持续加码，算力基础设施建设进入高峰期，关注业绩兑现能力强的标的。")
            elif power_pct > -2:
                md.append("- **算力板块**：今日小幅调整，行业高景气度不变，短期波动不影响长期价值，可逐步逢低吸纳。")
            else:
                md.append("- **算力板块**：今日调整幅度较大，板块整体估值偏高，短期注意风险，等待回调后布局机会。")
        
        # 半导体板块分析
        semi_theme = next((t for t in focus_themes if t["theme"] == "半导体"), None)
        if semi_theme and semi_theme["change_pct"] is not None:
            semi_pct = _safe_float(semi_theme["change_pct"])
            if semi_pct > 2:
                md.append("- **半导体板块**：今日强势上涨，国产替代逻辑持续强化，芯片自主可控是长期战略方向，看好设备、材料、设计各环节龙头。")
            elif semi_pct > 0:
                md.append("- **半导体板块**：今日小幅上涨，行业周期见底信号明显，库存逐渐去化，需求端逐步复苏，中期配置价值凸显。")
            elif semi_pct > -2:
                md.append("- **半导体板块**：今日小幅调整，整体处于底部区间，向下空间有限，可逢低布局基本面优质的标的。")
            else:
                md.append("- **半导体板块**：今日回调幅度较大，短期受外围因素影响，长期国产化逻辑不变，耐心等待企稳信号。")
        
        # 新能源板块分析
        newenergy_theme = next((t for t in focus_themes if t["theme"] == "新能源"), None)
        if newenergy_theme and newenergy_theme["change_pct"] is not None:
            ne_pct = _safe_float(newenergy_theme["change_pct"])
            if ne_pct > 2:
                md.append("- **新能源板块**：今日大幅反弹，行业估值处于历史低位，业绩增速稳定，具备较高的安全边际，反弹持续性值得关注。")
            elif ne_pct > 0:
                md.append("- **新能源板块**：今日小幅上涨，产业链价格逐步企稳，需求端保持旺盛，龙头企业竞争优势明显。")
            elif ne_pct > -2:
                md.append("- **新能源板块**：今日小幅调整，行业内部结构分化，优选技术壁垒高、出海能力强的细分领域龙头。")
            else:
                md.append("- **新能源板块**：今日调整幅度较大，市场情绪仍偏弱，等待行业基本面进一步改善信号。")
        
        # 风电设备板块分析
        wind_theme = next((t for t in focus_themes if t["theme"] == "风电设备"), None)
        if wind_theme and wind_theme["change_pct"] is not None:
            wind_pct = _safe_float(wind_theme["change_pct"])
            if wind_pct > 2:
                md.append("- **风电设备板块**：今日表现强势，陆上风电招标量超预期，海上风电进入高速发展期，零部件企业盈利改善明显。")
            elif wind_pct > 0:
                md.append("- **风电设备板块**：今日小幅上涨，行业景气度持续回升，大型化趋势下成本下降明显，出口市场空间广阔。")
            elif wind_pct > -2:
                md.append("- **风电设备板块**：今日小幅调整，长期逻辑清晰，关注具备技术优势和成本控制能力的整机及零部件厂商。")
            else:
                md.append("- **风电设备板块**：今日回调幅度较大，短期受行业竞争格局影响，长期看好技术迭代带来的投资机会。")
        
        # 钛/镁金属板块分析
        metal_theme = next((t for t in focus_themes if t["theme"] == "钛/镁金属"), None)
        if metal_theme and metal_theme["change_pct"] is not None:
            metal_pct = _safe_float(metal_theme["change_pct"])
            if metal_pct > 2:
                md.append("- **钛/镁金属板块**：今日大幅上涨，新能源、航空航天等下游需求快速增长，供给端刚性较强，价格具备上涨弹性。")
            elif metal_pct > 0:
                md.append("- **钛/镁金属板块**：今日小幅上涨，行业供需格局改善，新材料应用场景不断拓展，龙头企业受益明显。")
            elif metal_pct > -2:
                md.append("- **钛/镁金属板块**：今日小幅调整，行业具备周期属性，关注下游需求复苏进度和价格走势。")
            else:
                md.append("- **钛/镁金属板块**：今日调整幅度较大，短期受宏观经济预期影响，长期需求增长逻辑不变。")
    else:
        if historical_mode:
            md.append("*历史模式下未接入全市场涨跌榜*\n")
        else:
            md.append("*主题数据获取失败*\n")
    md.append("")

    # == Section 8: 自选股追踪 ==
    md.append("## ⭐ 八、自选股追踪")
    md.append("")
    analysis_by_code = {}
    if stock_analysis_data:
        for analysis in stock_analysis_data:
            code = _analysis_code(analysis)
            if code:
                analysis_by_code[code] = analysis
    if watchlist_quotes:
        headers = ["代码", "名称", "最新价", "涨跌幅", "成交额", "振幅"]
        align = ["center", "left", "right", "right", "right", "right"]
        rows = []
        for s in watchlist_quotes:
            rows.append([
                s.get("code", "-"),
                f"**{s.get('name','')}**",
                f"{s.get('price','-')}",
                color_pct(s.get("change_pct", 0)),
                format_turnover(s.get("turnover", 0)),
                f"{s.get('amplitude','-')}%" if s.get("amplitude") not in ["-", None] else "N/A",
            ])
        md.append(md_table(headers, rows, align))
    else:
        if stock_analysis_data:
            md.append("*实时快照获取失败，以下补充基于日线与评分模型的逐股分析。*\n")
        else:
            md.append("*自选股历史数据获取失败*\n" if historical_mode else "*自选股数据获取失败*\n")
    md.append("")

    if watchlist_quotes or stock_analysis_data:
        quote_by_code = {
            str(item.get("code", "")): item
            for item in (watchlist_quotes or [])
            if item.get("code")
        }
        md.append("### 逐股详情")
        md.append("")
        for item in WATCHLIST:
            code = item.get("code", "")
            name = item.get("name", code)
            quote = quote_by_code.get(code, {})
            analysis = analysis_by_code.get(code)
            price = quote.get("price", analysis.get("current_price", "-") if analysis else "-")
            change_pct = quote.get("change_pct", analysis.get("change_pct", 0) if analysis else 0)
            md.append(f"#### {name}（{code}）")
            md.append(f"- **最新价**：{price}；**涨跌幅**：{color_pct(change_pct)}")

            detail_parts = []
            if quote:
                if quote.get("open") not in [None, "-", ""]:
                    detail_parts.append(f"开盘 {quote.get('open')}")
                if quote.get("prev_close") not in [None, "-", ""]:
                    detail_parts.append(f"昨收 {quote.get('prev_close')}")
                if quote.get("low") not in [None, "-", ""] and quote.get("high") not in [None, "-", ""]:
                    detail_parts.append(f"日内区间 {quote.get('low')} ~ {quote.get('high')}")
                if quote.get("amplitude") not in [None, "-", ""]:
                    detail_parts.append(f"振幅 {quote.get('amplitude')}%")
                turnover = format_turnover(quote.get("turnover", 0))
                if turnover != "N/A":
                    detail_parts.append(f"成交额 {turnover}")
            if detail_parts:
                md.append(f"- **交易快照**：{'；'.join(detail_parts)}")

            if analysis:
                md.append(f"- **模型判断**：{analysis.get('signal', 'HOLD')} / {analysis.get('score', 0)}/100")
                if analysis.get("industry_name"):
                    md.append(f"- **所属行业**：{analysis['industry_name']}")
                dimensions = analysis.get("dimensions") or []
                if dimensions:
                    top_dims = sorted(
                        dimensions,
                        key=lambda dim: _safe_float(dim.get("score", 0)),
                        reverse=True,
                    )[:3]
                    top_dim_text = "，".join(
                        f"{dim.get('name', '')}{_safe_float(dim.get('score', 0)):.0f}"
                        for dim in top_dims
                    )
                    md.append(f"- **强项维度**：{top_dim_text}")
                if analysis.get("summary"):
                    md.append(f"- **结论**：{analysis['summary']}")
            md.append("")
    md.append("")

    # == Section 9: 自选股深度分析 (stock-analysis 8 维度) ==
    md.append("## 🔬 九、自选股深度分析 (8 维度评分)")
    md.append("")
    if stock_analysis_data:
        for a in stock_analysis_data:
            if a is None:
                continue
            ticker = a.get("ticker", "")
            signal = a.get("signal", "HOLD")
            score = a.get("score", 0)
            price = a.get("current_price", "-")
            change = a.get("change_pct", 0)
            summary = a.get("summary", "")
            md.append(f"### {ticker}")
            md.append(f"- **信号**: {signal} | **综合评分**: {score}/100")
            md.append(f"- **现价**: {price} ({color_pct(change)})")
            if a.get("dimensions"):
                dims = " | ".join(
                    f"{dim.get('name', '')}{dim.get('score', 0):.0f}"
                    for dim in a["dimensions"]
                )
                md.append(f"- **维度评分**: {dims}")
                if a.get("industry_name"):
                    md.append(f"- **所属行业**: {a['industry_name']}")
            else:
                md.append(f"- **维度评分**: 盈利{a.get('earnings_score', 0):.0f} | 基本面{a.get('fundamentals_score', 0):.0f} | 分析师{a.get('analyst_score', 0):.0f} | 动量{a.get('momentum_score', 0):.0f} | 情绪{a.get('sentiment_score', 0):.0f} | 板块{a.get('sector_score', 0):.0f}")
            if summary:
                md.append(f"- **摘要**: {summary}")
            md.append("")
    else:
        md.append("*深度分析历史数据获取失败*\n" if historical_mode else "*深度分析数据获取失败*\n")
    md.append("")

    # == Section 10: 主题新闻追踪 ==
    md.append("## 📰 十、主题新闻追踪")
    md.append("")
    if news:
        for theme, keywords in THEME_KEYWORDS.items():
            theme_news = [
                (t, h) for t, h in news
                if any(k in t for k in keywords)
            ]
            md.append(f"### {theme}")
            if theme_news:
                for t, h in theme_news[:4]:
                    md.append(f"- [{t}]({h})")
            else:
                md.append("- 暂无相关新闻")
            md.append("")
    else:
        if historical_mode:
            md.append("*历史模式下未接入新闻回放*\n")
        else:
            md.append("*新闻数据获取失败*\n")
        md.append("")

    # == Section 11: 今日要闻 ==
    md.append("## 📰 十一、今日要闻")
    md.append("")
    if news:
        for t, h in news[:12]:
            md.append(f"- [{t}]({h})")
    else:
        if historical_mode:
            md.append("- 历史模式下未接入要闻回放")
        else:
            md.append("- 暂无新闻数据")
    md.append("")

    # == Section 12: 综合分析 ==
    md.append("## 🧠 十二、综合分析")
    md.append("")
    kline_sh = kline_data.get("上证指数", [])
    analysis_lines = analyze_market(
        indices, breadth, kline_sh,
        industry_up, industry_down, concept_up, is_morning,
        global_assets=global_assets,
    )
    for line in analysis_lines:
        md.append(line)
        md.append("")

    # Footer
    md.append("---")
    md.append("")
    md.append(
        "> ⚠️ **免责声明**：本报告基于公开数据自动生成，仅供参考，"
        "不构成任何投资建议。投资有风险，入市需谨慎。"
        "数据来源为东方财富，可能存在延迟或偏差。"
    )
    md.append("")
    md.append(f"*— A股{mode} · 自动生成 @ {gen_time} —*")

    return "\n".join(md)


# ───────────────────── PDF (basic fallback) ───────────────────────────────

def make_simple_pdf(text, out_path):
    """Generate a rudimentary PDF. For proper Chinese PDF use nano-pdf."""
    lines = text.splitlines()
    content_lines = ["BT", "/F1 9 Tf", "11 TL", "40 790 Td"]
    for line in lines[:120]:
        clean = re.sub(r"[#*|>]", "", line)
        clean = re.sub(r"!\[.*?\]\(.*?\)", "[图表]", clean)
        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
        esc = (clean.replace("\\", "\\\\")
               .replace("(", "\\(").replace(")", "\\)"))
        content_lines.append(f"({esc}) Tj T*")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1", "ignore")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842]"
         b" /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"),
        b"<< /Length %d >>\nstream\n" % len(content)
        + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = b"%PDF-1.4\n"
    offsets = []
    for i, data in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode("ascii") + data + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode("ascii")
    out += (b"trailer\n<< /Size %d /Root 1 0 R >>\n"
            b"startxref\n%d\n%%%%EOF" % (len(objects) + 1, xref_pos))
    out_path.write_bytes(out)


# ───────────────────── Main Entry ─────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="A股早晚报生成器（增强版）",
    )
    ap.add_argument(
        "--mode", choices=["morning", "evening"], required=True,
        help="报告类型: morning=早报, evening=晚报",
    )
    ap.add_argument(
        "--date", default=dt.date.today().strftime("%Y-%m-%d"),
        help="报告日期 YYYY-MM-DD",
    )
    ap.add_argument("--outdir", required=True, help="输出目录")
    ap.add_argument(
        "--no-charts", action="store_true",
        help="跳过图表生成",
    )
    ap.add_argument(
        "--skip-feishu", action="store_true",
        help="仅生成本地文件，不同步飞书文档",
    )
    ap.add_argument(
        "--feishu-open-id",
        help="飞书接收人的 open_id；默认读取 FEISHU_NOTIFY_OPEN_ID / FEISHU_OPEN_ID",
    )
    ap.add_argument(
        "--feishu-folder-token",
        help="飞书文档目标文件夹 token；默认读取 FEISHU_FOLDER_TOKEN",
    )
    ap.add_argument(
        "--feishu-env-file",
        default=str(DEFAULT_ENV_PATH),
        help="加载飞书配置的 .env 路径",
    )
    ap.add_argument(
        "--feishu-state-file",
        default=str(DEFAULT_FEISHU_STATE_PATH),
        help="保存按日文档映射的 state 文件路径",
    )
    args = ap.parse_args()

    requested_ymd = args.date.replace("-", "")
    resolved_ymd = resolve_trade_date(requested_ymd)
    date_str = f"{resolved_ymd[:4]}-{resolved_ymd[4:6]}-{resolved_ymd[6:]}"
    today_ymd = dt.date.today().strftime("%Y%m%d")
    historical_mode = requested_ymd != today_ymd or resolved_ymd != today_ymd
    is_morning = args.mode == "morning"
    mode_cn = "早报" if is_morning else "晚报"
    base = f"A股{mode_cn}-{resolved_ymd}"
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"{'='*60}")
    print(f" 📊 A股{mode_cn}生成器（增强版）")
    print(f" 📅 日期: {date_str}")
    if requested_ymd != resolved_ymd:
        print(f" 🔁 交易日纠正: {requested_ymd} -> {resolved_ymd}")
    print(f" 🕰️ 模式: {'历史模式' if historical_mode else '实时模式'}")
    print(f" 📁 输出: {outdir}")
    print(f"{'='*60}")
    print()

    # == Data Fetching ==
    data_source_label = "东方财富历史K线 / 同花顺板块指数 / Yahoo Finance Chart"

    if historical_mode:
        print("📡 [1/10] 获取主要指数历史行情...")
        try:
            indices = fetch_indices_historical(resolved_ymd)
            print(f"   ✅ 获取到 {len(indices)} 个指数")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            indices = []

        print("📡 [2/10] 获取行业板块历史排行...")
        try:
            industry_all = fetch_sector_ranking_historical("industry", resolved_ymd, count=0)
            industry_up = industry_all[:50]
            industry_down = sorted(
                industry_all,
                key=lambda item: item.get("change_pct", 999),
            )[:50]
            print(f"   ✅ 行业板块 {len(industry_all)} 个")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            industry_all, industry_up, industry_down = [], [], []

        print("📡 [3/10] 获取概念板块历史排行...")
        concept_up = []
        print("   ⚠️  历史模式下暂不做全量概念排行，改为主题定向追踪")

        print("📡 [4/10] 获取个股涨跌排行...")
        stocks_up, stocks_down = [], []
        print("   ⚠️  历史模式下未接入全市场涨跌榜快照")

        print("📡 [5/10] 获取市场涨跌统计...")
        breadth = {
            "up": 0, "down": 0, "flat": 0,
            "limit_up": 0, "limit_down": 0,
            "big_up": 0, "big_down": 0, "total": 0,
        }
        print("   ⚠️  历史模式下未接入全市场宽度快照")

        print("📡 [6/10] 获取指数 K 线数据（近30日）...")
        kline_data = {}
        for secid, name in [
            ("1.000001", "上证指数"),
            ("0.399001", "深证成指"),
            ("0.399006", "创业板指"),
        ]:
            try:
                klines = fetch_kline(secid, 30, end_date=resolved_ymd)
                kline_data[name] = klines
                print(f"   ✅ {name}: {len(klines)} 根K线")
            except Exception as e:
                print(f"   ⚠️  {name} 失败: {e}")
                kline_data[name] = []

        print("📡 [7/10] 获取新闻数据...")
        news = []
        print("   ⚠️  历史模式下未接入新闻回放")

        print("📡 [8/10] 获取自选股历史行情...")
        try:
            watchlist_quotes = fetch_watchlist_quotes_historical(WATCHLIST, resolved_ymd)
            print(f"   ✅ 自选股 {len(watchlist_quotes)} 只")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            watchlist_quotes = []

        print("📡 [9/10] 获取全球资产历史行情...")
        try:
            global_assets = fetch_global_assets_historical(GLOBAL_ASSETS, resolved_ymd)
            print(f"   ✅ 全球资产 {len(global_assets)} 项")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            global_assets = []

        print("📡 [10/10] 自选股历史 8 维度深度分析...")
        try:
            benchmark_klines = fetch_kline("1.000300", 120, end_date=resolved_ymd)
        except Exception:
            benchmark_klines = []
        try:
            focus_themes = summarize_focus_themes_historical(industry_all, resolved_ymd)
            stock_analysis_data = []
            for item in WATCHLIST:
                analysis = analyze_watchlist_stock_historical(
                    item,
                    resolved_ymd,
                    benchmark_klines=benchmark_klines,
                )
                if analysis:
                    stock_analysis_data.append(analysis)
            print(f"   ✅ 深度分析 {len(stock_analysis_data)} 只")
        except Exception as e:
            print(f"   ⚠️  失败：{e}")
            focus_themes = []
            stock_analysis_data = []
    else:
        print("📡 [1/10] 获取主要指数行情...")
        try:
            indices = fetch_indices()
            print(f"   ✅ 获取到 {len(indices)} 个指数")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            indices = []

        print("📡 [2/10] 获取行业板块排行...")
        try:
            industry_up = fetch_sector_ranking("industry", "up", 50)
            industry_down = fetch_sector_ranking("industry", "down", 50)
            print(f"   ✅ 涨幅{len(industry_up)} / 跌幅{len(industry_down)}")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            industry_up, industry_down = [], []

        print("📡 [3/10] 获取概念板块排行...")
        try:
            concept_up = fetch_sector_ranking("concept", "up", 50)
            print(f"   ✅ 概念板块 Top {len(concept_up)}")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            concept_up = []

        print("📡 [4/10] 获取个股涨跌排行...")
        try:
            stocks_up = fetch_stock_ranking("up", 10)
            stocks_down = fetch_stock_ranking("down", 10)
            print(f"   ✅ 涨幅{len(stocks_up)} / 跌幅{len(stocks_down)}")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            stocks_up, stocks_down = [], []

        print("📡 [5/10] 获取市场涨跌统计...")
        try:
            breadth = fetch_market_breadth()
            print(f"   ✅ 共{breadth['total']}只: "
                  f"↑{breadth['up']} ↓{breadth['down']} "
                  f"={breadth['flat']} "
                  f"涨停{breadth['limit_up']} 跌停{breadth['limit_down']}")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            breadth = {
                "up": 0, "down": 0, "flat": 0,
                "limit_up": 0, "limit_down": 0,
                "big_up": 0, "big_down": 0, "total": 0,
            }

        print("📡 [6/10] 获取 K 线数据（近30日）...")
        kline_data = {}
        for secid, name in [
            ("1.000001", "上证指数"),
            ("0.399001", "深证成指"),
            ("0.399006", "创业板指"),
        ]:
            try:
                klines = fetch_kline(secid, 30)
                kline_data[name] = klines
                print(f"   ✅ {name}: {len(klines)} 根K线")
            except Exception as e:
                print(f"   ⚠️  {name} 失败: {e}")
                kline_data[name] = []

        print("📡 [7/10] 获取新闻数据...")
        try:
            news = fetch_news_links()
            print(f"   ✅ 获取 {len(news)} 条新闻")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            news = []

        print("📡 [8/10] 获取自选股行情...")
        try:
            watchlist_quotes, watchlist_quote_source = fetch_watchlist_quotes_with_fallback(
                WATCHLIST,
                resolved_ymd,
            )
            source_label = {
                "realtime": "实时行情",
                "kline": "日线回退",
                "tushare": "Tushare 回退",
                "none": "无可用数据源",
            }.get(watchlist_quote_source, watchlist_quote_source)
            print(f"   ✅ 自选股 {len(watchlist_quotes)} 只（{source_label}）")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            watchlist_quotes = []

        print("📡 [9/10] 获取全球资产行情...")
        try:
            global_assets = fetch_global_assets(GLOBAL_ASSETS)
            print(f"   ✅ 全球资产 {len(global_assets)} 项")
        except Exception as e:
            print(f"   ⚠️  失败: {e}")
            global_assets = []

        focus_themes = summarize_focus_themes(concept_up, industry_up)

        print("📡 [10/10] 自选股 8 维度深度分析...")
        try:
            try:
                benchmark_klines = fetch_kline("1.000300", 120, end_date=resolved_ymd)
            except Exception:
                benchmark_klines = []
            stock_analysis_data = build_watchlist_analysis_data(
                WATCHLIST,
                resolved_ymd,
                benchmark_klines=benchmark_klines,
                prefer_realtime=True,
            )
            print(f"   ✅ 深度分析 {len(stock_analysis_data)} 只")
        except Exception as e:
            print(f"   ⚠️  失败：{e}")
            stock_analysis_data = []

    # == Chart Generation ==

    chart_files = {}
    if not args.no_charts:
        print()
        print("📊 生成可视化图表...")
        try:
            fname = generate_kline_chart(
                kline_data, outdir, stem=f"{base}-index_kline"
            )
            if fname:
                chart_files["kline"] = fname
                print(f"   ✅ 指数K线走势图: {fname}")
            else:
                print("   ⚠️  无K线数据或 matplotlib 不可用")
        except Exception as e:
            print(f"   ⚠️  K线图失败: {e}")
            traceback.print_exc()

        try:
            fname = generate_sector_chart(
                industry_up, industry_down, outdir, stem=f"{base}-sector_ranking"
            )
            if fname:
                chart_files["sector"] = fname
                print(f"   ✅ 板块排行图: {fname}")
        except Exception as e:
            print(f"   ⚠️  板块图失败: {e}")

        try:
            fname = generate_breadth_chart(
                breadth, outdir, stem=f"{base}-market_breadth"
            )
            if fname:
                chart_files["breadth"] = fname
                print(f"   ✅ 市场情绪图: {fname}")
        except Exception as e:
            print(f"   ⚠️  情绪图失败: {e}")

    # == Report Composition ==

    print()
    print("📝 生成报告...")
    md_text = compose_report(
        date_str=date_str,
        is_morning=is_morning,
        indices=indices,
        industry_up=industry_up,
        industry_down=industry_down,
        concept_up=concept_up,
        stocks_up=stocks_up,
        stocks_down=stocks_down,
        breadth=breadth,
        kline_data=kline_data,
        news=news,
        chart_files=chart_files,
        watchlist_quotes=watchlist_quotes,
        focus_themes=focus_themes,
        global_assets=global_assets,
        stock_analysis_data=stock_analysis_data,
        historical_mode=historical_mode,
        resolved_trade_date=resolved_ymd,
        data_source_label=data_source_label,
    )

    md_path = outdir / f"{base}.md"
    md_path.write_text(md_text, encoding="utf-8")
    print(f"   ✅ Markdown: {md_path}")

    pdf_path = outdir / f"{base}.pdf"
    try:
        make_simple_pdf(md_text, pdf_path)
        print(f"   ✅ PDF (basic): {pdf_path}")
    except Exception as e:
        print(f"   ⚠️  PDF 失败: {e}")
        pdf_path = None

    feishu_result = None
    if not args.skip_feishu:
        print()
        print("☁️ 同步飞书文档...")
        try:
            feishu_result = sync_report_to_feishu(
                outdir=outdir,
                resolved_ymd=resolved_ymd,
                date_str=date_str,
                mode_cn=mode_cn,
                pdf_path=pdf_path,
                env_path=args.feishu_env_file,
                state_path=args.feishu_state_file,
                folder_token=args.feishu_folder_token,
                notify_open_id=args.feishu_open_id,
            )
            if feishu_result:
                print(f"   ✅ 飞书文档: {feishu_result['doc_url']}")
                if feishu_result.get("notified"):
                    print("   ✅ 飞书链接已发送给用户")
                else:
                    print("   ℹ️  未配置接收 open_id，仅完成文档同步")
            else:
                print("   ℹ️  未检测到飞书配置，跳过同步")
        except Exception as e:
            print(f"   ⚠️  飞书同步失败: {e}")
            traceback.print_exc()

    # == Summary ==

    print()
    print(f"{'='*60}")
    print(f" ✅ A股{mode_cn} 生成完毕！")
    print(f"{'='*60}")
    print(f" 📄 Markdown : {md_path}")
    if pdf_path:
        print(f" 📄 PDF      : {pdf_path}")
    if feishu_result:
        print(f" ☁️ 飞书文档 : {feishu_result['doc_url']}")
    for label, fname in chart_files.items():
        print(f" 📊 图表({label:8s}): {outdir / fname}")
    print(f"{'='*60}")
    print()
    print(md_path)
    if pdf_path:
        print(pdf_path)
    if feishu_result:
        print(feishu_result["doc_url"])


if __name__ == "__main__":
    main()
