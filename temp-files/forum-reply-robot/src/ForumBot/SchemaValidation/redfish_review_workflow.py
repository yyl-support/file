#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redfish 规则检查器入口（瘦再导出）

仅负责动态加载 redfish_checker，并向上层 end_to_end_check 暴露：
- REDFISH_COMPLIANCE_RULES
- check_review_point_compliance
- check_all_rules
"""

# version: 1.0.6

import importlib.util
from pathlib import Path
import sys

_SCHEMA_VALIDATION_DIR = Path(__file__).parent.resolve()
if str(_SCHEMA_VALIDATION_DIR) not in sys.path:
    sys.path.insert(0, str(_SCHEMA_VALIDATION_DIR))

from redfish_common import Config, get_timestamp, setup_logger

# ==================== 日志配置 ====================

Config.init_directories()
log_file = None
if not Config.DISABLE_FILE_OUTPUT:
    log_file = Config.LOG_DIR / f"redfish_review_workflow_{get_timestamp()}.log"
    logger = setup_logger(__name__, str(log_file), console_output=False)
else:
    logger = setup_logger(__name__, None, console_output=True)

# ==================== 动态导入 redfish_checker ====================

spec = importlib.util.spec_from_file_location(
    "redfish_checker", str(_SCHEMA_VALIDATION_DIR / "redfish_checker.py")
)
redfish_checker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(redfish_checker_module)

REDFISH_COMPLIANCE_RULES = redfish_checker_module.REDFISH_COMPLIANCE_RULES
check_all_rules = redfish_checker_module.check_all_rules
check_review_point_compliance = redfish_checker_module.check_review_point_compliance

DEFAULT_MODEL = Config.MODELSCOPE_MODEL
