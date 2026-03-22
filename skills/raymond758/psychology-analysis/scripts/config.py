#!/usr/bin/env python3
# 心理健康分析工具配置文件
import os
import sys

from enum import Enum

from skills.smyx_common.scripts.config import ConstantEnum as ConstantEnumBase

from skills.face_analysis.scripts.config import ApiEnum as ApiEnumParent, ConstantEnum as ConstantEnumParent, \
    SceneCodeEnum


class ApiEnum(ApiEnumParent):

    @classmethod
    def init(cls, config=None):
        super().init(config)
        ApiEnumParent.ANALYSIS_URL = "/web/ai-analysis/v2/start-common-ai-analysis"
        ApiEnumParent.ANALYSIS_RESULT_URL = "/web/ai-analysis/get-common-ai-analysis-result"
        ApiEnumParent.PAGE_URL = "/web/ai-analysis/page-common-ai-analysis-result"


class ConstantEnum(ConstantEnumParent):
    DEFAULT__ANALYSIS_TYPE = "general"

    @classmethod
    def init(cls, config=None):
        super().init(config)
        ConstantEnumParent.DEFAULT__SCENE_CODE = SceneCodeEnum.PSYCHOLOGY_ANALYSIS.value
