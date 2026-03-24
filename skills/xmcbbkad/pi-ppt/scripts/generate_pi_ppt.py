import argparse
import os
import time
import uuid
from typing import Any, Dict, Tuple, List
import hashlib
import json
import requests


#GENERATION_URL = "https://alpha-pi.deepvinci.tech/api/v1/integration/document/generation"
#GET_STATUS_URL = "https://alpha-pi.deepvinci.tech/api/v1/integration/document/status"
#UPLOAD_FILE_URL = "https://alpha-pi.deepvinci.tech/api/v1/integration/file/upload"
GENERATION_URL = "https://co-pi.deepvinci.tech/api/v1/integration/document/generation"
GET_STATUS_URL = "https://co-pi.deepvinci.tech/api/v1/integration/document/status"
UPLOAD_FILE_URL = "https://co-pi.deepvinci.tech/api/v1/integration/file/upload"

def generate_signature_payload(app_id: str, app_secret: str, **payload: dict) -> Tuple[str, dict]:
    """
    生成请求签名，基于时间戳和提供的参数

    Args:
        timestamp: 请求的时间戳
        parameters: 需要包含在签名中的键值对参数

    Returns:
        携带签名的请求参数
    """

    timestamp = int(time.time())

    # 按字母顺序排序请求参数key
    keys: List[str] = sorted(payload.keys())

    # 将非空参数格式化为"key=value"格式并按排序后的顺序组合
    formatted_params: List[str] = []
    for key in keys:
        value = payload[key]
        if isinstance(value, bool):
            formatted_params.append(f"{key}={str(value).lower()}")
        elif isinstance(value, dict):
            formatted_params.append(f"{key}={json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)}")
        elif value is not None:
            formatted_params.append(f"{key}={str(value)}")

    # 用冒号连接所有参数
    params_string: str = ":".join(formatted_params)

    # 构建签名字符串：app_secret:timestamp:params:app_secret
    signature_base = f"{app_secret}:{timestamp}:{params_string}:{app_secret}"

    # 计算SHA1哈希
    hash_result = hashlib.sha1(signature_base.encode("utf-8")).hexdigest()

    return {"app_id": app_id, "timestamp": timestamp, "sign": hash_result, **payload}


def upload_file(app_id: str, app_secret: str, file_path: str) -> Dict[str, Any]:
    """
    上传本地文件。接口要求 file 为 multipart 中的文件字段（FILE），不能放在 JSON body 里。
    签名字段（app_id、timestamp、sign、name 等）放在 form data，与 files['file'] 一起提交。
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)

    file_name = os.path.basename(file_path)
    payload = {"name": file_name}
    payload_with_sign = generate_signature_payload(app_id, app_secret, **payload)

    # multipart/form-data：所有可序列化字段走 data，二进制走 files（字段名一般为 file）
    data: Dict[str, str] = {}
    for k, v in payload_with_sign.items():
        if isinstance(v, bool):
            data[k] = str(v).lower()
        elif isinstance(v, (dict, list)):
            data[k] = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
        else:
            data[k] = str(v)

    with open(file_path, "rb") as f:
        files = {"file": (file_name, f)}
        response = requests.post(UPLOAD_FILE_URL, data=data, files=files, timeout=30)
    if response.status_code != 200:
        print(
            f"[upload_file] request failed, status_code={response.status_code}, response_text={response.text}"
        )
    response.raise_for_status()
    return response.json()

def create_document(app_id: str, app_secret: str, content: str, cards: int = 8, language: str = "zh", attachment_id: str = None) -> Dict[str, Any]:
    """
    Trigger Pi PPT generation task only (no polling).
    """
    if not isinstance(content, str) or not content.strip():
        raise ValueError("content must be a non-empty string.")
    if not isinstance(cards, int) or cards <= 0:
        raise ValueError("cards must be a positive integer.")
    if language not in {"cn", "zh", "en"}:
        raise ValueError("language must be one of 'zh', 'cn', or 'en'.")

    resource_id = f"draft-{uuid.uuid4().hex[:12]}"

    payload = {
        "resource_id": resource_id,
        "uid": "user_1",
        "content": content.strip(),
        "cards": cards,
        "language": language,
        "outline_type": "aippt"
    }
    if attachment_id:
        payload["attachment_id"] = attachment_id
    else:
        payload["search"] = True

    payload_with_sign = generate_signature_payload(app_id, app_secret, **payload)

    response = requests.post(GENERATION_URL, json=payload_with_sign, timeout=30)
    if response.status_code != 200:
        print(
            f"[create_document] request failed, status_code={response.status_code}, response_text={response.text}"
        )
    response.raise_for_status()
    data = response.json()

    return {
        "name": "generate_pi_ppt",
        "request": payload_with_sign,
        "response": data,
    }

def get_status(app_id: str, app_secret: str, resource_id: str) -> Dict[str, Any]:
    if not isinstance(resource_id, str) or not resource_id.strip():
        raise ValueError("resource_id must be a non-empty string.")

    timestamp = int(time.time())
    payload = {
        "resource_id": resource_id.strip(),
    }
    payload_with_sign = generate_signature_payload(app_id, app_secret, **payload)
    response = requests.post(GET_STATUS_URL, json=payload_with_sign, timeout=30)
    if response.status_code != 200:
        print(
            f"[get_status] request failed, status_code={response.status_code}, response_text={response.text}"
        )
    response.raise_for_status()
    response_json = response.json()

    data = response_json.get("data")
    if not isinstance(data, dict):
        raise ValueError(f"Status API returned unexpected format: {response_json}")

    status = data.get("status")
    if status not in {"running", "fail", "done"}:
        raise ValueError(f"Unknown status value: {status}, raw response: {response_json}")

    return {
        "resource_id": data.get("resource_id"),
        "status": status,
        "url": data.get("url"),
    }

def generate_pi_ppt(
    app_id: str,
    app_secret: str,
    content: str,
    cards: int = 8,
    language: str = "zh",
    file_path: str = None,
    timeout_s: int = 300,
    poll_interval_s: int = 20,
) -> Dict[str, Any]:
    """
    完整流程：
    1) 若提供 file_path，调用 upload_file 上传文件
    2) 调用 create_document 触发任务（上传文档时不传 cards）
    3) 调用 get_status 轮询，直到 done 返回 url
    """

    attachment_id = None
    if file_path:
        print(f"Uploading file: {file_path}")
        upload_result = upload_file(app_id, app_secret, file_path)
        attachment_id = upload_result.get("data", {}).get("id")
        if not attachment_id:
            raise ValueError(f"File upload failed: {upload_result}")
        print(f"File uploaded successfully, attachment_id={attachment_id}")

    create_result = create_document(
        app_id=app_id,
        app_secret=app_secret,
        content=content,
        cards=cards,
        language=language,
        attachment_id=attachment_id,
    )

    resource_id = create_result.get("request", {}).get("resource_id")
    if not isinstance(resource_id, str) or not resource_id:
        raise ValueError(f"Creation API did not return a usable resource_id: {create_result}")

    deadline = time.time() + timeout_s
    last_status: Dict[str, Any] = {}
    while time.time() < deadline:
        status_result = get_status(app_id, app_secret, resource_id)
        last_status = status_result
        status = status_result.get("status")

        if status == "done":
            url = status_result.get("url")
            if not url:
                raise ValueError(f"status is 'done' but no url was returned: {status_result}")
            return {
                "name": "generate_pi_ppt_2",
                "resource_id": resource_id,
                "status": "done",
                "url": url,
                "create_result": create_result,
            }

        if status == "fail":
            raise RuntimeError(f"PPT generation failed: {status_result}")

        time.sleep(poll_interval_s)

    raise TimeoutError(
        f"Polling timed out after {timeout_s}s, resource_id={resource_id}, last_status={last_status}"
    )

def parse_args():
    SUPPORTED_EXTS = {".doc", ".docx", ".txt", ".md", ".pdf", ".pptx", ".ppt"}
    parser = argparse.ArgumentParser(description="使用 PI 服务生成 PPT")
    parser.add_argument("--pippt_app_id", required=True, help="PI 平台分配的 app_id；不传则读取环境变量 PIPPT_APP_ID")
    parser.add_argument("--pippt_app_secret", required=True, help="PI 平台分配的 app_secret；不传则读取环境变量 PIPPT_APP_SECRET")
    parser.add_argument("--content", required=True, help="主题和描述，例如：'生成一个关于中国GPU厂商介绍的PPT，商务严肃风格'")
    parser.add_argument("--language", default="zh", choices=["zh", "cn", "en"], help="PPT语言，'zh'/'cn'为中文，'en'为英文，默认为'zh'")
    parser.add_argument("--cards", type=int, default=8, help="期望的PPT页数，默认为8。上传文档时此参数被忽略")
    parser.add_argument("--file", default=None, help="要上传的文档路径，支持 .doc/.docx/.txt/.md/.pdf/.pptx/.ppt")
    args = parser.parse_args()

    if args.file:
        ext = os.path.splitext(args.file)[1].lower()
        if ext not in SUPPORTED_EXTS:
            parser.error(
                f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(SUPPORTED_EXTS))}"
            )

    return args


def main():
    args = parse_args()
    print("Starting PPT generation; this usually takes about 2–3 minutes, please wait...")
    result = generate_pi_ppt(
        app_id=args.pippt_app_id,
        app_secret=args.pippt_app_secret,
        content=args.content,
        cards=args.cards,
        language=args.language,
        file_path=args.file,
    )
    url = result.get("url")
    if not url:
        raise ValueError(f"Generation failed: {result}")
    print(f"PPT generated successfully. Download URL: {url}")


if __name__ == "__main__":
    main()
