#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema 验证 Debug 日志模块

试运行阶段，用于记录每个 topic 处理过程中的全部中间产物数据。
每个 topic 写入一条完整记录到 PostgreSQL schema_debug_logs 表，
包含各步骤的输入/输出及耗时（JSONB 格式）。
"""

import contextlib
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2

logger = logging.getLogger(__name__)

# ==================== 模块级状态 ====================

_db_config: Optional[dict] = None
_initialized = False
_disabled = False


# ==================== 初始化 ====================

def init_debug_logger(db_config: dict) -> None:
    """
    初始化 debug 日志记录器（幂等，多次调用安全）。

    Args:
        db_config: 数据库连接配置 dict（host, port, database, user, password, sslmode）
    """
    global _db_config, _initialized, _disabled

    if _initialized:
        return

    try:
        # 存储配置
        _db_config = db_config

        # 轻量连接测试
        conn = psycopg2.connect(
            host=db_config.get('host'),
            port=db_config.get('port'),
            database=db_config.get('database'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            sslmode=db_config.get('sslmode', 'disable')
        )
        conn.close()

        _initialized = True
        _disabled = False
    except Exception as e:
        # 数据库不可达时静默降级
        _disabled = True
        _initialized = True
        logging.getLogger(__name__).warning(f"[schema_debug] 初始化失败，debug 日志已禁用: {e}")


def write_debug_record(record: dict) -> None:
    """
    将一条记录写入 schema_debug_logs 表。

    永远不会抛出异常。
    """
    if _disabled or _db_config is None:
        return

    conn = None
    try:
        conn = psycopg2.connect(
            host=_db_config.get('host'),
            port=_db_config.get('port'),
            database=_db_config.get('database'),
            user=_db_config.get('user'),
            password=_db_config.get('password'),
            sslmode=_db_config.get('sslmode', 'disable')
        )
        cursor = conn.cursor()

        # 从 record 提取独立列字段
        topic_id = record.get('topic_id', '')
        title = record.get('title')
        overall_pass = record.get('overall_pass')
        total_time = record.get('total_processing_time_seconds')
        error = record.get('error')

        # 完整记录序列化为 JSON 字符串供 JSONB 列
        record_json = json.dumps(record, ensure_ascii=False, default=str)

        cursor.execute(
            """INSERT INTO schema_debug_logs
               (topic_id, title, overall_pass, total_processing_time_seconds, error, record)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (topic_id, title, overall_pass, total_time, error, record_json)
        )
        conn.commit()
        cursor.close()
    except Exception as e:
        logging.getLogger(__name__).warning(f"[schema_debug] 写入记录失败: {e}")
        if conn:
            try:
                conn.rollback()
            except Exception:
                logger.debug("[schema_debug] rollback failed", exc_info=True)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                logger.debug("[schema_debug] close connection failed", exc_info=True)


# ==================== 计时工具 ====================

@contextlib.contextmanager
def timed():
    """
    计时上下文管理器，yield 一个 dict，退出时自动填充 duration_seconds。

    Usage:
        with timed() as t:
            do_something()
        print(t["duration_seconds"])  # 耗时秒数
    """
    t = {"duration_seconds": 0.0}
    start = time.monotonic()
    try:
        yield t
    finally:
        t["duration_seconds"] = round(time.monotonic() - start, 4)


# ==================== DebugRecordBuilder ====================

class DebugRecordBuilder:
    """
    累加器 + 上下文管理器，收集单个 topic 处理过程中的全部中间数据。

    用法:
        with DebugRecordBuilder(topic_id, title) as builder:
            builder.set_relevance(...)
            builder.set_review_points(...)
            ...
            builder.finalize(...)
    """

    def __init__(self, topic_id: str, title: str):
        self._start_time = time.monotonic()
        self._record: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "topic_id": topic_id,
            "title": title,
            "total_processing_time_seconds": 0.0,
            "steps": {
                "redfish_relevance": None,
                "extract_review_points": None,
                "filter_review_points": None,
                "check_review_points": []
            },
            "final_result_preview": None,
            "overall_pass": None,  # nosec
            "error": None
        }
        self._finalized = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._finalized:
            error_msg = str(exc_val) if exc_val else None
            try:
                self.finalize(
                    final_result_preview=None,
                    overall_pass=None,
                    error=error_msg
                )
            except Exception:
                logger.debug("[schema_debug] finalize on exit failed", exc_info=True)
        # 不吞掉异常
        return False

    def set_relevance(self, is_related: bool, reason: str, duration: float) -> None:
        """记录 Redfish 相关性判断结果"""
        try:
            self._record["steps"]["redfish_relevance"] = {
                "is_related": is_related,
                "reason": reason,
                "duration_seconds": duration
            }
        except Exception:
            logger.debug("[schema_debug] set relevance failed", exc_info=True)

    def set_review_points(self, points: List[Dict[str, str]], duration: float) -> None:
        """记录评审点提取结果"""
        try:
            self._record["steps"]["extract_review_points"] = {
                "total_count": len(points),
                "review_points": points,
                "duration_seconds": duration
            }
        except Exception:
            logger.debug("[schema_debug] set review points failed", exc_info=True)

    def set_filter_result(
        self,
        redfish_points: List[Dict[str, str]],
        non_redfish_points: List[Dict[str, str]],
        duration: float
    ) -> None:
        """记录评审点过滤结果"""
        try:
            self._record["steps"]["filter_review_points"] = {
                "redfish_count": len(redfish_points),
                "non_redfish_count": len(non_redfish_points),
                "redfish_titles": [p.get("title", "") for p in redfish_points],
                "non_redfish_titles": [p.get("title", "") for p in non_redfish_points],
                "duration_seconds": duration
            }
        except Exception:
            logger.debug("[schema_debug] set filter result failed", exc_info=True)

    def add_review_point_check(self, check_data: Dict[str, Any]) -> None:
        """添加单个评审点的检查结果"""
        try:
            self._record["steps"]["check_review_points"].append(check_data)
        except Exception:
            logger.debug("[schema_debug] add review point check failed", exc_info=True)

    def finalize(
        self,
        final_result_preview: Optional[str] = None,
        overall_pass: Optional[bool] = None,
        error: Optional[str] = None
    ) -> None:
        """完成记录并写入数据库"""
        if self._finalized:
            return
        self._finalized = True

        try:
            self._record["total_processing_time_seconds"] = round(
                time.monotonic() - self._start_time, 4
            )
            self._record["final_result_preview"] = final_result_preview
            self._record["overall_pass"] = overall_pass
            self._record["error"] = error

            write_debug_record(self._record)
        except Exception:
            logger.debug("[schema_debug] write debug record failed", exc_info=True)
