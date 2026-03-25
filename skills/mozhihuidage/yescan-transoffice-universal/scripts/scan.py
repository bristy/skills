#!/usr/bin/env python3
"""
Quark OCR - 夸克扫描王 OCR识别服务（保存 Word/Excel 到 documents 目录）
"""
import sys
import json
import argparse
from pathlib import Path

# 导入公共模块 - 使用相对路径（项目根目录）
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from common import (
    OCRResult,
    CredentialManager,
    QuarkOCRClient,
    FileSaver,
    get_scene_config,
    list_scenes,
)


def save_document_from_result(result: OCRResult, doc_type: str = "word") -> OCRResult:
    """从 OCR 结果中提取并保存文档"""
    file_base64 = None
    if isinstance(result.data, dict) and "TypesetInfo" in result.data:
        typeset_info_list = result.data["TypesetInfo"]
        if isinstance(typeset_info_list, list) and len(typeset_info_list) > 0:
            typeset_info = typeset_info_list[0]
            if isinstance(typeset_info, dict) and "FileBase64" in typeset_info:
                file_base64 = typeset_info["FileBase64"]

    if file_base64 and result.code == "00000":
        try:
            saver = FileSaver()
            if doc_type == "word":
                save_res = saver.save_word_from_base64(file_base64)
            elif doc_type == "excel":
                save_res = saver.save_excel_from_base64(file_base64)
            else:
                return OCRResult(code="INVALID_DOC_TYPE", message=f"Invalid document type: {doc_type}", data={})
            
            if save_res["code"] == 0:
                result.data = {"path": save_res["data"]["path"]}
            else:
                result = OCRResult(code=save_res["code"], message=save_res["msg"], data=save_res["data"])
        except (IOError, OSError) as e:
            result = OCRResult(code="FILE_SAVE_ERROR", message=f"File save failed: {e}", data={})

    return result


def main():
    """主函数 - 调用 API 并保存文档"""
    parser = argparse.ArgumentParser(description="Quark OCR - 支持图片 URL、本地路径、BASE64 字符串")
    
    parser.add_argument("--scene", "-s", required=True, 
                        help=f"场景名称，可选: {', '.join(list_scenes())}")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", "-u", help="图片 URL")
    group.add_argument("--path", "-p", help="本地图片文件路径")
    group.add_argument("--base64", "-b", help="BASE64 字符串")
    
    args = parser.parse_args()
    
    try:
        config = get_scene_config(args.scene)
    except ValueError as e:
        print(OCRResult(code="INVALID_SCENE", message=str(e), data=None).to_json())
        sys.exit(1)
    
    try:
        api_key = CredentialManager.load()
        with QuarkOCRClient(
            api_key=api_key,
            service_option=config["service_option"],
            input_configs=config["input_configs"],
            output_configs=config["output_configs"],
            data_type=config["data_type"]
        ) as client:
            if args.base64:
                result = client.recognize(base64_data=args.base64)
            elif args.url:
                result = client.recognize(image_url=args.url)
            else:
                result = client.recognize(image_path=args.path)
        
        # 根据 function_option 判断保存类型
        doc_type = None
        try:
            input_configs = json.loads(config["input_configs"])
            func_option = input_configs.get("function_option", "")
            if func_option == "word":
                doc_type = "word"
            elif func_option == "excel":
                doc_type = "excel"
        except json.JSONDecodeError:
            pass
        
        if doc_type:
            result = save_document_from_result(result, doc_type)
        
        print(result.to_json())
        
    except ValueError as e:
        print(OCRResult(code="A0100", message=str(e), data=None).to_json())
        sys.exit(1)
    except Exception as e:
        print(OCRResult(code="UNKNOWN_ERROR", message=f"Unexpected error: {str(e)}", data=None).to_json())
        sys.exit(1)


if __name__ == "__main__":
    main()
