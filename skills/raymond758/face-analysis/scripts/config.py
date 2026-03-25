#!/usr/bin/env python3
# 中医面诊分析工具配置文件
import os
import sys

# def import_path_common():
#     current_dir = os.path.dirname(os.path.abspath(__file__))  # .../face_analysis/scripts
#     # common 位于 /root/.openclaw/workspace/skills/scripts/common
#     skills_dir = os.path.dirname(os.path.dirname(current_dir))  # .../skills
#     workspace_dir = os.path.dirname(skills_dir)  # .../skills
#     common_dir = os.path.join(skills_dir, 'scripts', 'common')
#     scripts_dir = os.path.join(skills_dir, 'scripts')
#     if scripts_dir not in sys.path:
#         sys.path.insert(1, workspace_dir)
#         sys.path.insert(1, scripts_dir)
#         sys.path.insert(1, common_dir)
#
#
# import_path_common()
from enum import Enum

from skills.smyx_common.scripts.config import ApiEnum as ApiEnumBase, ConstantEnum as ConstantEnumBase


class ApiEnum(ApiEnumBase):
    ANALYSIS_URL = "/web/health-analysis/v2/start-health-analysis"

    ANALYSIS_RESULT_URL = "/web/health-analysis/get-health-analysis-result"

    PAGE_URL = "/web/health-analysis/page-health-analysis-result"

    DETAIL_EXPORT_URL = ApiEnumBase.BASE_URL_HEALTH + "/health/order/api/getReportDetailExport?id="


class SceneCodeEnum(Enum):
    OPEN_HEALTH_AI_ANALYSIS = "OPEN_HEALTH_AI_ANALYSIS"
    OPEN_PERSON_RISK_ANALYSIS = "OPEN_PERSON_RISK_ANALYSIS"
    PET_ANALYSIS = "PET_ANALYSIS"
    CRAWL_ANALYSIS = "CRAWL_ANALYSIS"
    AQUARIUM_ANALYSIS = "AQUARIUM_ANALYSIS"
    PSYCHOLOGY_ANALYSIS = "PSYCHOLOGY_ANALYSIS"
    AUTISM_ANALYSIS = "AUTISM_ANALYSIS"
    DIET_ANALYSIS = "DIET_ANALYSIS"
    DRIVE_ANALYSIS = "DRIVE_ANALYSIS"
    SPORT_ANALYSIS = "SPORT_ANALYSIS"
    EMOTION_ANALYSIS = "EMOTION_ANALYSIS"
    STUDY_ANALYSIS = "STUDY_ANALYSIS"


class ConstantEnum(ConstantEnumBase):
    DEFAULT__SCENE_CODE = ""
