#!/usr/bin/env python3
"""
场景配置模块 - 统一管理所有 OCR/扫描场景的配置
"""
from typing import Dict, Any, Optional, List


# 场景配置映射表
# key: 场景名（对应 resource/references/scenarios/*.md 文件名，去掉数字前缀和 .md 后缀）
# value: 包含 service_option, input_configs, output_configs, data_type 的配置字典
SCENE_CONFIGS: Dict[str, Dict[str, str]] = {
    # ==================== OCR 识别类 ====================
    "general-ocr": {
        "service_option": "ocr",
        "input_configs": '{"function_option":"RecognizeGeneralDocument"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "handwritten-ocr": {
        "service_option": "ocr",
        "input_configs": '{"function_option":"RecognizeWritten"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "table-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeTable"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "idcard-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeIDCard"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "social-security-card-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeSocialSecurityCard"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "travel-permit-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeTravelPermit"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "degree-certificate-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeDegreeCertificate"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "vat-invoice-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeTaxInvoice"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "train-ticket-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeTrainTicket"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "formula-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeFormula"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "question-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeQuestion"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "driver-license-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeDriverLicense"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "vehicle-license-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeVehicleLicense"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "commercial-invoice-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeCommercialInvoice"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "medical-report-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizeMedicalReport"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "business-license-ocr": {
        "service_option": "ocr",
        "input_configs": '{"function_option":"RecognizeBusinessLicense"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "product-image-ocr": {
        "service_option": "structure",
        "input_configs": '{"function_option":"RecognizePackaging"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },

    # ==================== 图像增强类 ====================
    "exam-enhance": {
        "service_option": "scan",
        "input_configs": '{"function_option":"enhance"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "image-hd-enhance": {
        "service_option": "scan",
        "input_configs": '{"function_option":"nature_high_definition"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "certificate-enhance": {
        "service_option": "scan",
        "input_configs": '{"function_option":"certificate"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "remove-handwriting": {
        "service_option": "scan",
        "input_configs": '{"function_option":"handwriting_remover"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "remove-watermark": {
        "service_option": "scan",
        "input_configs": '{"function_option":"watermark_remover"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "remove-shadow": {
        "service_option": "scan",
        "input_configs": '{"function_option":"rectification"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "remove-screen-pattern": {
        "service_option": "scan",
        "input_configs": '{"function_option":"screen_enhance"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "remove-background-color": {
        "service_option": "scan",
        "input_configs": '{"function_option":"monochrome"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "image-crop-rectify": {
        "service_option": "scan",
        "input_configs": '{"function_option":"no_genre"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "sketch-drawing": {
        "service_option": "scan",
        "input_configs": '{"function_option":"painting_drawing_sketch"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "extract-lineart": {
        "service_option": "scan",
        "input_configs": '{"function_option":"painting_toner_saving"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "scan-document": {
        "service_option": "scan",
        "input_configs": '{"function_option":"auto_select"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },

    # ==================== 文档转换类 ====================
    "image-to-excel": {
        "service_option": "typeset",
        "input_configs": '{"function_option":"excel"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
    "image-to-word": {
        "service_option": "typeset",
        "input_configs": '{"function_option":"word"}',
        "output_configs": '{"need_return_image":"false"}',
        "data_type": "image",
    },
}


def get_scene_config(scene_name: str) -> Dict[str, str]:
    """
    根据场景名获取配置
    
    Args:
        scene_name: 场景名称（如 'general-ocr', 'handwritten-ocr' 等）
    
    Returns:
        包含 service_option, input_configs, output_configs, data_type 的字典
    
    Raises:
        ValueError: 场景名不存在时抛出
    """
    if scene_name not in SCENE_CONFIGS:
        available = ", ".join(sorted(SCENE_CONFIGS.keys()))
        raise ValueError(
            f"Unknown scene: '{scene_name}'. "
            f"Available scenes: {available}"
        )
    return SCENE_CONFIGS[scene_name]


def list_scenes() -> List[str]:
    """
    获取所有可用场景名列表
    
    Returns:
        场景名列表（已排序）
    """
    return sorted(SCENE_CONFIGS.keys())
