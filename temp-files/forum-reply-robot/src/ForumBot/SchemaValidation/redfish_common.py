#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redfish 通用工具模块

提供跨脚本共享的通用函数和类，包括：
- 日志配置
- 文件操作 (JSON, CSV)
- 配置管理
- 错误处理
"""
# version：1.0.30

import csv
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# ==================== 配置管理 ====================

class Config:
    """配置管理类 - 从 config.yaml 的 schema_validation section 初始化"""

    # API 配置（默认值为空，由 configure_from_dict 从 config.yaml 覆盖）
    MODELSCOPE_API_KEY = ""
    MODELSCOPE_BASE_URL = ""
    MODELSCOPE_MODEL = ""

    # 文件输出控制（默认禁用，所有结果在内存中处理）
    DISABLE_FILE_OUTPUT = True

    # 重试配置
    MAX_RETRY = 3
    RETRY_DELAY = 5

    # 目录配置
    PROJECT_ROOT = Path(__file__).parent.absolute()
    SCHEMA_DIR = str(PROJECT_ROOT / "SchemaFiles")
    LOG_DIR = PROJECT_ROOT / "log"
    OUTPUT_DIR = PROJECT_ROOT / "check_results"
    DATA_DIR = PROJECT_ROOT / "review_data"
    URI_SAMPLES_DIR = PROJECT_ROOT / "uri_samples"

    @classmethod
    def init_directories(cls) -> None:
        """初始化必要的目录（仅在文件输出启用时执行）"""
        if cls.DISABLE_FILE_OUTPUT:
            return
        cls.LOG_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.URI_SAMPLES_DIR.mkdir(exist_ok=True)

    @classmethod
    def configure_from_dict(cls, config_dict: dict) -> None:
        """
        从 config.yaml 的 schema_validation section 覆盖配置。

        Args:
            config_dict: config['schema_validation'] dict
        """
        if not config_dict:
            return

        if 'api_key' in config_dict:
            cls.MODELSCOPE_API_KEY = config_dict['api_key']
        if 'base_url' in config_dict:
            cls.MODELSCOPE_BASE_URL = config_dict['base_url']
        if 'model' in config_dict:
            cls.MODELSCOPE_MODEL = config_dict['model']
        if 'schema_dir' in config_dict:
            raw = config_dict['schema_dir']
            p = Path(raw)
            cls.SCHEMA_DIR = str(p if p.is_absolute() else (cls.PROJECT_ROOT / p).resolve())
        if 'output_dir' in config_dict:
            raw = config_dict['output_dir']
            p = Path(raw)
            cls.OUTPUT_DIR = p if p.is_absolute() else (cls.PROJECT_ROOT / raw).resolve()
        if 'disable_file_output' in config_dict:
            cls.DISABLE_FILE_OUTPUT = config_dict['disable_file_output']
        if 'max_retry' in config_dict:
            cls.MAX_RETRY = int(config_dict['max_retry'])
        if 'retry_delay' in config_dict:
            cls.RETRY_DELAY = int(config_dict['retry_delay'])


# ==================== 日志配置 ====================

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    配置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径（可选）
        level: 日志级别
        console_output: 是否输出到控制台

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除已有的 handlers
    logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 文件 handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 控制台 handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 抑制第三方库日志
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)

    return logger


def get_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ==================== 文件操作 ====================

def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    从文件加载 JSON 数据

    Args:
        file_path: JSON 文件路径

    Returns:
        解析后的 JSON 数据

    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON 格式错误
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(
    data: Any,
    file_path: Union[str, Path],
    indent: int = 2,
    ensure_ascii: bool = False
) -> None:
    """
    保存数据到 JSON 文件

    Args:
        data: 要保存的数据
        file_path: 文件路径
        indent: 缩进空格数
        ensure_ascii: 是否确保 ASCII 编码
    """
    # 确保目录存在
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


def load_csv(
    file_path: Union[str, Path],
    encoding: str = 'utf-8-sig'
) -> List[Dict[str, str]]:
    """
    从 CSV 文件加载数据

    Args:
        file_path: CSV 文件路径
        encoding: 文件编码

    Returns:
        行数据列表
    """
    with open(file_path, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_csv_row(
    file_path: Union[str, Path],
    topic_id: str,
    id_column: str = 'id',
    encoding: str = 'utf-8-sig'
) -> Optional[Dict[str, str]]:
    """
    从 CSV 文件中加载指定 ID 的行

    Args:
        file_path: CSV 文件路径
        topic_id: 要查找的 ID
        id_column: ID 列名
        encoding: 文件编码

    Returns:
        匹配的行数据，未找到返回 None
    """
    with open(file_path, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get(id_column) == str(topic_id):
                return row
    return None


# ==================== 时间格式化 ====================

def format_time(seconds: float) -> str:
    """
    格式化时间显示

    Args:
        seconds: 秒数

    Returns:
        格式化后的时间字符串 (如: 1分30秒, 45秒)
    """
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}小时{minutes}分{secs}秒"


# ==================== 字符串处理 ====================

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不合法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 替换不合法字符为下划线
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)

    # 移除控制字符
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)

    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]

    return filename.strip()


def safe_title(title: str) -> str:
    """
    生成安全的标题（用于文件名）

    Args:
        title: 原始标题

    Returns:
        安全的标题字符串
    """
    return sanitize_filename(
        title.replace('：', '_')
        .replace('/', '_')
        .replace('\\', '_')
        .replace(':', '_')
    )


# ==================== 错误处理 ====================

class RedfishError(Exception):
    """Redfish 相关错误基类"""
    pass


class SchemaValidationError(RedfishError):
    """Schema 验证错误"""
    pass


class URIGenerationError(RedfishError):
    """URI 生成错误"""
    pass


# ==================== 结果记录 ====================

class ValidationResult:
    """验证结果基类"""

    def __init__(self, result: str = "unknown"):
        """
        Args:
            result: 验证结果 ("pass", "fail", "error", "unknown")
        """
        self.result = result
        self.errors = []
        self.warnings = []
        self.timestamp = get_timestamp()

    def add_error(self, error_type: str, message: str, **kwargs) -> None:
        """添加错误"""
        error_entry = {"type": error_type, "message": message}
        error_entry.update(kwargs)
        self.errors.append(error_entry)

    def add_warning(self, warning_type: str, message: str, **kwargs) -> None:
        """添加警告"""
        warning_entry = {"type": warning_type, "message": message}
        warning_entry.update(kwargs)
        self.warnings.append(warning_entry)

    @property
    def is_pass(self) -> bool:
        return self.result == "pass"

    @property
    def is_fail(self) -> bool:
        return self.result == "fail"

    @property
    def is_error(self) -> bool:
        return self.result == "error"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "result": self.result,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp
        }

