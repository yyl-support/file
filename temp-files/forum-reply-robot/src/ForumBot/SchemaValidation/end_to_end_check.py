#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redfish 端对端检测脚本

功能流程：
1. 输入一篇帖子（HTML 或 JSON 格式）
2. 判断帖子是否与 Redfish 相关
3. 提取帖子中的所有评审点
4. 判断每个评审点是否与 Redfish 相关
5. 如果是，进行 Schema 验证和模型检测
6. 保存检测结果

使用方式：
    修改 main() 函数中的配置变量，然后运行：
    python end_to_end_check.py
"""
# version：1.0.30

import contextlib
import importlib.util
import os
import re
import sys
import time
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 将 SchemaValidation 目录添加到 sys.path 以支持绝对导入
_SCHEMA_VALIDATION_DIR = Path(__file__).parent.resolve()
if str(_SCHEMA_VALIDATION_DIR) not in sys.path:
    sys.path.insert(0, str(_SCHEMA_VALIDATION_DIR))

# 导入通用模块
from redfish_common import (
    Config,
    get_timestamp,
    safe_title,
    setup_logger
)
from redfish_schema_validator import JSONSchemaValidator, generate_schema_advice_from_error
from redfish_uri_generator import URIGenerator, URIGenerationError
from schema_debug_logger import DebugRecordBuilder, init_debug_logger, timed

# ==================== 日志配置 ====================
import logging

Config.init_directories()
log_file = None
if not Config.DISABLE_FILE_OUTPUT:
    log_file = Config.LOG_DIR / f"end_to_end_check_{get_timestamp()}.log"
    logger = setup_logger(__name__, str(log_file), console_output=True)
else:
    logger = setup_logger(__name__, None, console_output=True)

INFRASTRUCTURE_ERROR_KEYWORDS = (
    "request timed out",
    "timed out",
    "read timeout",
    "read timed out",
    "connection timeout",
    "connect timeout",
    "gateway timeout",
    "api timeout",
    "llm timeout",
    "timeout while",
    "empty response",
    "rate limit",
    "quota",
    "429",
    "insufficient_quota",
    "insufficient quota",
    "context_length_exceeded",
    "service unavailable",
    "server overloaded",
    "bad gateway",
    "connection error",
    "connection reset",
    "connection aborted",
    "connection refused",
    "remote protocol error",
    "null value is not allowed",
    "expected a string, got null",
    "object has no attribute 'choices'",
    "choices[0]",
    "no choices",
    "空响应",
    "规则检查服务调用失败",
    "服务调用失败",
)


def is_infrastructure_error_text(value: Any) -> bool:
    """Return True for transient/model-service errors that must not be posted."""
    text = str(value or "").lower()
    return any(keyword in text for keyword in INFRASTRUCTURE_ERROR_KEYWORDS)


def _iter_rule_detail_messages(error_details: Dict[str, Any]):
    for section in ("MODEL_VALIDATION", "WARNING_DETAILS", "STATIC_VALIDATION"):
        entries = error_details.get(section, [])
        if not isinstance(entries, list):
            entries = [entries]
        for entry in entries:
            if isinstance(entry, dict):
                for field in ("message", "error", "summary", "advice"):
                    yield entry.get(field, "")
            else:
                yield entry


def _is_api_error(check_result: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    Detect service/API failures that are not real review findings.

    Return phase: 'uri', 'rule', or ''.
    """
    checks = check_result.get('checks', {}) if isinstance(check_result, dict) else {}

    uri_check = checks.get('uri_sample', {})
    if uri_check.get('status') == 'error':
        return True, uri_check.get('error', 'URI generation failed'), 'uri'

    rule_check = checks.get('rule_compliance', {})
    for error_msg in (
        rule_check.get('error', ''),
        rule_check.get('message', ''),
        rule_check.get('summary', ''),
    ):
        if is_infrastructure_error_text(error_msg):
            return True, str(error_msg), 'rule'

    error_details = rule_check.get('error_details', {})
    for message in _iter_rule_detail_messages(error_details):
        if is_infrastructure_error_text(message):
            return True, str(message), 'rule'

    return False, '', ''


def _format_infrastructure_failure(review_title: str, max_retry: Optional[int] = None) -> str:
    retry_text = f"经 {max_retry} 次重试后" if max_retry else ""
    title_text = f"评审点 '{review_title[:30]}' " if review_title else ""
    return f"处理失败: {title_text}{retry_text}规则检查服务调用失败，请稍后重试"

# 注意：不在这里重定向 stdout/stderr，因为 argparse 需要原始的 stdout
# 重定向将在 main() 函数中，在解析完参数后进行

# ==================== 动态导入外部模块 ====================

# 导入 extract_reviews 模块
spec = importlib.util.spec_from_file_location("extract_reviews", str(_SCHEMA_VALIDATION_DIR / "extract_reviews.py"))
extract_reviews_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_reviews_module)
extract_review_points_from_html = extract_reviews_module.extract_review_points_from_html
extract_all_review_points = extract_reviews_module.extract_all_review_points
is_redfish_related = extract_reviews_module.is_redfish_related

# 导入 MDB 分类器
sys.path.insert(0, str(Path(__file__).parent.parent / "MdbValidation"))
try:
    from mdb_classifier import is_mdb_related as _is_mdb_related
    from mdb_checker import MdbComplianceChecker
except ImportError:
    _is_mdb_related = None
    MdbComplianceChecker = None

# 导入 method2 模块（包含 schema 验证、URI 生成、规则检查等功能）
spec = importlib.util.spec_from_file_location(
    "redfish_review_workflow",
    str(_SCHEMA_VALIDATION_DIR / "redfish_review_workflow.py"),
)
redfish_review_workflow_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(redfish_review_workflow_module)
check_review_point_compliance = redfish_review_workflow_module.check_review_point_compliance
REDFISH_COMPLIANCE_RULES = redfish_review_workflow_module.REDFISH_COMPLIANCE_RULES

DEFAULT_MODEL = Config.MODELSCOPE_MODEL


# ==================== MDB 相关性判断 ====================

def is_post_relevant(title: str, content: str) -> Tuple[bool, str]:
    """判断帖子是否与 Redfish 或 MDB 资源协作接口相关。"""
    if _is_mdb_related is not None:
        mdb_related, mdb_reason = _is_mdb_related(title, content)
        if mdb_related:
            return True, f"MDB 相关: {mdb_reason}"

    is_redfish, redfish_reason = is_post_redfish_related(title, content)
    if is_redfish:
        return True, f"Redfish 相关: {redfish_reason}"

    return False, "帖子与 Redfish 和 MDB 资源协作接口均无关"


def classify_review_point(title: str, content: str) -> str:
    """对单个评审点进行三路分类: 'mdb' / 'redfish' / 'other'"""
    if _is_mdb_related is not None:
        mdb_related, _ = _is_mdb_related(title, content)
        if mdb_related:
            return 'mdb'

    if is_redfish_related(title, content):
        return 'redfish'

    return 'other'


def check_mdb_review_point(review_point: Dict[str, str], config: dict = None, sibling_context: str = "") -> Dict[str, Any]:
    """调用 MDB 校验器检查单个评审点。"""
    result = {
        "title": review_point.get('title', ''),
        "checks": {},
        "redfish_related": False,
        "mdb_related": True,
    }

    if MdbComplianceChecker is None:
        result['checks']['rule_compliance'] = {"error": "MdbValidation 模块未加载"}
        return result

    _mdb_t0 = time.monotonic()
    try:
        logger.info("[MDB] 开始创建 MdbComplianceChecker...")
        checker = MdbComplianceChecker(config or {})
        logger.info("[MDB] MdbComplianceChecker 创建完成, 耗时=%.2fs, 开始调用 check_review_point...",
                     time.monotonic() - _mdb_t0)
        mdb_result = checker.check_review_point(
            review_point.get('title', ''),
            review_point.get('content', ''),
            sibling_context
        )
        _mdb_elapsed = round(time.monotonic() - _mdb_t0, 2)
        logger.info("[MDB] check_review_point 完成, 总耗时=%.2fs, result=%s",
                     _mdb_elapsed, mdb_result.get('result', 'unknown'))
        result['checks']['rule_compliance'] = mdb_result
    except Exception as e:
        _mdb_elapsed = round(time.monotonic() - _mdb_t0, 2)
        logger.error(f"MDB 校验失败 (耗时={_mdb_elapsed}s): {e}")
        result['checks']['rule_compliance'] = {"error": str(e)}

    return result


# ==================== 核心功能函数 ====================

def is_post_redfish_related(title: str, content: str) -> Tuple[bool, str]:
    """
    判断帖子是否与 Redfish 相关

    Args:
        title: 帖子标题
        content: 帖子内容

    Returns:
        (是否相关, 原因说明)
    """
    title_lower = title.lower() if title else ''
    content_lower = content.lower() if content else ''

    # 检查是否包含 redfish 关键字
    if 'redfish' in title_lower or 'redfish' in content_lower:
        return True, "帖子内容包含 'redfish' 关键字"

    # 检查是否包含相关技术关键字（可能间接涉及 Redfish）
    redfish_related_keywords = [
        'bmc', 'ipmi', 'restful api', 'rest api',
        'dmtf', 'smart platform', 'management interface',
        '@odata.id', '@odata.type', 'json-schema'
    ]
    for keyword in redfish_related_keywords:
        if keyword.lower() in content_lower:
            return True, f"帖子内容包含相关关键字 '{keyword}'"

    return False, "帖子内容不包含任何 Redfish 相关关键字"


def extract_review_points(post_content: str) -> List[Dict[str, str]]:
    """
    从帖子内容中提取所有评审点

    Args:
        post_content: 帖子内容

    Returns:
        评审点列表，每个评审点包含 title 和 content
    """
    return extract_review_points_from_html(post_content)


def filter_redfish_review_points(review_points: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    过滤出与 Redfish 相关的评审点

    Args:
        review_points: 所有评审点列表

    Returns:
        (Redfish 相关评审点列表, 非 Redfish 评审点列表)
    """
    redfish_points = []
    non_redfish_points = []

    for rp in review_points:
        if is_redfish_related(rp.get('title', ''), rp.get('content', '')):
            redfish_points.append(rp)
        else:
            non_redfish_points.append(rp)

    return redfish_points, non_redfish_points


def validate_uri_sample(uri_sample: Dict[str, Any], schema_dir: str) -> Dict[str, Any]:
    """
    验证 URI 示例是否符合 Schema 定义。

    新版 JSONSchemaValidator 会同时尝试 dmtf/ 与 rackmount/oem/openubmc[/json_schema] 两个来源，
    并把所用 schema 的来源、文件名等记录在 ``validator.schema_check_meta`` 中，
    本函数将这些信息透传到返回结果的 ``schema_check`` 字段，方便上层 md/日志展示。

    Args:
        uri_sample: URI 返回体示例
        schema_dir: Schema 文件目录（应指向 SchemaFiles 根，validator 会自动识别 dmtf/oem 子目录）

    Returns:
        验证结果字典
    """
    output = StringIO()

    try:
        validator = JSONSchemaValidator(schema_dir, no_oem=False)

        with contextlib.redirect_stdout(output):
            result = validator.validate(uri_sample.get("@odata.id", "/redfish/v1"), uri_sample)

        validation_output = output.getvalue()

        if result.result == "skip":
            result_status = "skip"
        elif result.is_pass:
            result_status = "pass"
        elif result.is_fail:
            result_status = "fail"
        else:
            result_status = "error"

        return {
            "result": result_status,
            "pass_count": validator.pass_count,
            "warn_count": validator.warn_count,
            "fail_count": validator.fail_count,
            "skip_count": validator.skip_count,
            "output": validation_output,
            "errors": validator.errors,
            "warnings": validator.warnings,
            "schema_check": dict(validator.schema_check_meta),
        }
    except Exception as e:
        return {
            "result": "error",
            "error": str(e),
            "fail_count": 0,
            "schema_check": {},
        }


def merge_schema_and_rule_results(result_dict: Dict, uri_sample: Dict, rule_check_result: Dict) -> Dict:
    """
    合并 Schema 验证和规则检查的结果

    Args:
        result_dict: 包含 schema_validation 的结果字典
        uri_sample: URI 示例数据
        rule_check_result: 规则检查结果

    Returns:
        修改后的 rule_check_result
    """
    checks = result_dict.get('checks', {})
    schema_validation = checks.get('schema_validation', {})
    sch_meta = schema_validation.get("schema_check")
    if sch_meta:
        rule_check_result["schema_check"] = sch_meta
    schema_failed = schema_validation.get('result') == 'fail'
    schema_skipped = schema_validation.get('result') == 'skip'
    schema_fail_count = schema_validation.get('fail_count', 0)

    error_details = rule_check_result.get('error_details', {})
    static_validation = error_details.get('STATIC_VALIDATION', [])

    if schema_failed and schema_fail_count > 0:
        for error in schema_validation.get('errors', []):
            err = error if isinstance(error, dict) else {"message": str(error)}
            static_validation.append({
                "rule": "[Schema] 模型静态检查",
                "message": f"{err.get('type', 'Error')}: {err.get('message', 'Schema validation failed')}",
                "advice": generate_schema_advice_from_error(err),
            })
        error_details['STATIC_VALIDATION'] = static_validation

    if schema_skipped:
        warning_details = error_details.get('WARNING_DETAILS', [])
        for warn in schema_validation.get('warnings', []):
            w = warn if isinstance(warn, dict) else {"message": str(warn)}
            warning_details.append({
                "rule": "[Schema] 静态验证跳过",
                "message": w.get('message', 'Schema definition missing, validation skipped'),
                "advice": "请确认 SchemaFiles/dmtf 或 SchemaFiles/rackmount/oem/openubmc[/json_schema] 中是否包含该资源类型的实际 JSON Schema 定义文件（含 definitions/properties），而非仅有 JsonSchemaFile 指针文件。",
            })
        error_details['WARNING_DETAILS'] = warning_details

    uri = uri_sample.get("@odata.id", "/redfish/v1")
    odata_type = uri_sample.get("@odata.type", "")
    resource_type = odata_type.split(".")[-2] if "." in odata_type else "Unknown"

    rule_check_result['uri'] = uri
    rule_check_result['resource_type'] = f"#{resource_type}"
    rule_check_result['total_checks_num'] = rule_check_result.get('total_checks_num', len(REDFISH_COMPLIANCE_RULES)) + 1
    rule_check_result['failed_checks_num'] = rule_check_result.get('failed_checks_num', 0) + (1 if schema_failed else 0)
    rule_check_result['error_details'] = error_details

    if schema_failed:
        rule_check_result['result'] = 'fail'

    return rule_check_result


def check_single_review_point(
    review_point: Dict[str, str],
    schema_dir: str,
    output_dir: str,
    generate_uri: bool = True,
    _cached_uri_sample: Optional[Dict] = None,
    _cached_checks: Optional[Dict] = None,
    debug_record: Optional[DebugRecordBuilder] = None
) -> Dict[str, Any]:
    """
    检查单个评审点

    Args:
        review_point: 评审点数据（包含 title 和 content）
        schema_dir: Schema 文件目录
        output_dir: 输出目录
        generate_uri: 是否生成 URI 示例并进行 Schema 验证
        _cached_uri_sample: 缓存的 URI 示例（重试时跳过 URI 生成和 Schema 验证）
        _cached_checks: 缓存的已成功检查结果（重试时复用）

    Returns:
        检查结果字典
    """
    result = {
        "title": review_point.get('title', ''),
        "checks": {},
        "redfish_related": True
    }

    logger.info(f"{'='*70}")
    logger.info(f"正在检查: {result['title']}")
    logger.info(f"{'='*70}")

    # 如果有缓存的 URI 示例和检查结果，直接复用（用于重试场景，跳过已成功的步骤）
    uri_sample = None
    if _cached_uri_sample is not None:
        uri_sample = _cached_uri_sample
        if _cached_checks:
            result['checks'] = dict(_cached_checks)
        logger.info("[1/3] 使用缓存的 URI 示例（跳过重新生成）")
        logger.info("[2/3] 使用缓存的 Schema 验证结果（跳过重新验证）")
    else:
        # 1. 生成 URI 示例（如果需要）
        if generate_uri:
            logger.info("[1/3] 生成 URI 返回体示例...")
            safe_title_str = safe_title(review_point['title'])
            uri_sample_file = None if Config.DISABLE_FILE_OUTPUT else os.path.join(output_dir, f"{safe_title_str}.json")

            try:
                with timed() as _t_uri:
                    generator = URIGenerator()
                    uri_sample = generator.generate(review_point, uri_sample_file)

                result['_debug_uri_duration'] = _t_uri["duration_seconds"]

                if uri_sample:
                    result['checks']['uri_sample'] = {
                        "status": "success",
                        "file": uri_sample_file
                    }
                    logger.info("[OK] URI 示例已生成")
                else:
                    result['checks']['uri_sample'] = {
                        "status": "failed",
                        "error": "生成失败"
                    }
                    logger.warning("[FAIL] URI 示例生成失败")
                    return result
            except URIGenerationError as e:
                result['checks']['uri_sample'] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"[FAIL] URI 示例生成出错: {e}")
                return result
            except Exception as e:
                result['checks']['uri_sample'] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"[FAIL] URI 示例生成出错: {e}")
                return result

        # 2. 验证静态 Schema（如果生成了 URI 示例）
        if uri_sample:
            logger.info("[2/3] 验证静态 Schema...")
            with timed() as _t_schema:
                schema_result = validate_uri_sample(uri_sample, schema_dir)
            result['_debug_schema_duration'] = _t_schema["duration_seconds"]
            result['checks']['schema_validation'] = schema_result

            sch_meta = schema_result.get("schema_check") or {}
            summary_zh = sch_meta.get("validation_summary_zh")
            if summary_zh:
                logger.info(f"  [Schema 依据] {summary_zh}")

            if schema_result['result'] == 'pass':
                logger.info(f"[OK] Schema 验证通过 (Pass: {schema_result.get('pass_count', 0)})")
            elif schema_result['result'] == 'skip':
                logger.info("[SKIP] Schema 定义文件缺失或仅含指针，跳过静态校验")
            elif schema_result['result'] == 'fail':
                logger.warning(f"[FAIL] Schema 验证失败 (Fail: {schema_result.get('fail_count', 0)})")
            else:
                logger.error(f"[FAIL] Schema 验证出错: {schema_result.get('error', 'Unknown')}")

    # 保存 uri_sample 到结果中，便于重试时复用
    if uri_sample:
        result['_uri_sample'] = uri_sample

    # 3. 规则合规性检查
    logger.info("[规则合规性检查...]")
    if generate_uri and uri_sample:
        # 如果有 URI 示例，使用 URI 和 payload 进行检查
        uri = uri_sample.get("@odata.id", "/redfish/v1")
        odata_type = uri_sample.get("@odata.type", "")
        resource_type = odata_type.split(".")[-2] if "." in odata_type else "Unknown"

        try:
            # 使用 method2 的 check_all_rules 函数
            check_all_rules = redfish_review_workflow_module.check_all_rules
            with timed() as _t_rule:
                rule_check_result = check_all_rules(
                    rules=REDFISH_COMPLIANCE_RULES,
                    uri=uri,
                    payload=uri_sample,
                    resource_type=resource_type,
                    model=DEFAULT_MODEL,
                    save_result=False
                )
            result['_debug_rule_duration'] = _t_rule["duration_seconds"]

            # 合并 schema 和 rule 结果
            merge_schema_and_rule_results(result, uri_sample, rule_check_result)
            result['checks']['rule_compliance'] = rule_check_result

            # 打印结果（URI-based 检查返回的格式是 total_checks_num, failed_checks_num）
            logger.info(f"  总检测数: {rule_check_result.get('total_checks_num', 0)}")
            logger.info(f"  失败数: {rule_check_result.get('failed_checks_num', 0)}")
            logger.info(f"  结果: {'[OK] 通过' if rule_check_result.get('result') == 'pass' else '[FAIL] 失败'}")

        except Exception as e:
            result['checks']['rule_compliance'] = {
                "error": str(e),
                "overall_compliant": False
            }
            logger.error(f"[FAIL] 规则检查出错: {e}")
    else:
        # 没有 URI 示例，只基于评审点内容进行检查
        try:
            with timed() as _t_rule:
                rule_check_result = check_review_point_compliance(
                    rules=REDFISH_COMPLIANCE_RULES,
                    review_point_title=review_point['title'],
                    review_point_content=review_point['content'],
                    model=DEFAULT_MODEL,
                    save_result=False
                )
            result['_debug_rule_duration'] = _t_rule["duration_seconds"]

            result['checks']['rule_compliance'] = rule_check_result

            logger.info(f"  总规则数: {rule_check_result.get('total_rules', 0)}")
            logger.info(f"  合规: {rule_check_result.get('compliant_rules', 0)}")
            logger.info(f"  失败: {rule_check_result.get('failed_rules', 0)}")
            logger.info(f"  警告: {rule_check_result.get('warning_rules', 0)}")
            logger.info(f"  合规率: {rule_check_result.get('compliance_rate', 'N/A')}")
            logger.info(f"  总体合规: {'[OK] 是' if rule_check_result.get('overall_compliant') else '[FAIL] 否'}")

        except Exception as e:
            result['checks']['rule_compliance'] = {
                "error": str(e),
                "overall_compliant": False
            }
            logger.error(f"[FAIL] 规则检查出错: {e}")

    return result


def generate_final_result(result: Dict[str, Any]) -> str:
    """
    根据 process_post 的结果生成总体评审结论（Markdown 格式）

    Args:
        result: process_post 返回的结果字典

    Returns:
        Markdown 格式的总体评审结论
    """
    lines = []
    title = result.get('title', '未知帖子')
    lines.append(f"# 帖子评审结论：{title}")
    lines.append("")

    # 帖子相关性
    if not result.get('post_redfish_related', False):
        lines.append(f"**帖子相关性**：与 Redfish/MDB 无关（{result.get('post_redfish_reason', '')}），未进行进一步检查。")
        return "\n".join(lines)

    lines.append(f"**帖子相关性**：相关（{result.get('post_redfish_reason', '')}）")
    lines.append("")
    mdb_count = result.get('mdb_review_points', 0)
    redfish_count = result.get('redfish_review_points', 0)
    other_count = result.get('non_redfish_review_points', 0)
    lines.append(f"- 总评审点数：{result.get('total_review_points', 0)}")
    if mdb_count > 0:
        lines.append(f"- MDB 资源协作接口评审点：{mdb_count}")
    if redfish_count > 0:
        lines.append(f"- Redfish 相关评审点：{redfish_count}")
    lines.append(f"- 其他评审点：{other_count}")
    lines.append("")

    review_point_results = result.get('results', [])
    if not review_point_results:
        lines.append("**无评审点检查结果。**")
        return "\n".join(lines)

    # 汇总统计
    total_rp = len(review_point_results)
    passed_rp = 0
    failed_rp = 0

    for rp in review_point_results:
        overall = _judge_review_point_overall(rp)
        if overall == 'pass':
            passed_rp += 1
        else:
            failed_rp += 1

    lines.append("---")
    lines.append("")
    lines.append(f"## 总体结果：{'通过' if failed_rp == 0 else '不通过'}（{passed_rp}/{total_rp} 个评审点通过）")
    lines.append("")

    # 逐个评审点
    for idx, rp in enumerate(review_point_results, 1):
        rp_title = rp.get('title', '未知评审点')
        # 去除原始帖子中已有的"评审点N："前缀，避免与格式化前缀重复
        rp_title = re.sub(r'^评审点\s*\d+\s*[：:]\s*', '', rp_title)
        rp_category = rp.get('category', 'redfish')
        cat_label = 'MDB' if rp_category == 'mdb' else 'Redfish'
        checks = rp.get('checks', {})
        overall = _judge_review_point_overall(rp)

        lines.append(f"### 评审点 {idx}：{rp_title}【{cat_label}】")
        lines.append("")
        lines.append(f"**结果：{'通过' if overall == 'pass' else '不通过'}**")
        lines.append("")

        # URI 生成
        uri_check = checks.get('uri_sample', {})
        uri_status = uri_check.get('status', 'unknown')
        if uri_status == 'success':
            lines.append("- URI 示例生成：通过")
        elif uri_status in ('failed', 'error'):
            lines.append(f"- URI 示例生成：失败（{uri_check.get('error', '未知错误')}）")
        elif rp_category != 'mdb':
            lines.append("- URI 示例生成：未执行")

        # Schema 验证
        schema = checks.get('schema_validation', {})
        if schema:
            schema_result = schema.get('result', 'unknown')
            sch_meta = schema.get('schema_check') or {}
            summary_zh = sch_meta.get('validation_summary_zh')

            if schema_result == 'pass':
                pass_count = schema.get('pass_count', 0)
                warn_count = schema.get('warn_count', 0)
                detail = f"通过（{pass_count} 项通过"
                if warn_count > 0:
                    detail += f"，{warn_count} 项警告"
                detail += "）"
                lines.append(f"- Schema 验证：{detail}")
                _append_schema_meta(lines, sch_meta, summary_zh)
                # 通过时也把警告（例如"OEM 中无该类型 schema"）摆出来
                for warn in schema.get('warnings', []):
                    if isinstance(warn, dict):
                        lines.append(f"  - [{warn.get('type', 'Warning')}] {warn.get('message', '')}")
            elif schema_result == 'skip':
                lines.append("- Schema 验证：跳过（schema 定义文件缺失或仅含 JsonSchemaFile 指针）")
                _append_schema_meta(lines, sch_meta, summary_zh)
                for warn in schema.get('warnings', []):
                    if isinstance(warn, dict):
                        lines.append(f"  - [{warn.get('type', 'Warning')}] {warn.get('message', '')}")
            elif schema_result == 'fail':
                fail_count = schema.get('fail_count', 0)
                warn_count = schema.get('warn_count', 0)
                detail = f"不通过（{fail_count} 项失败"
                if warn_count > 0:
                    detail += f"，{warn_count} 项警告"
                detail += "）"
                lines.append(f"- Schema 验证：{detail}")
                _append_schema_meta(lines, sch_meta, summary_zh)
                for err in schema.get('errors', []):
                    err_type = err.get('type', 'Error')
                    err_msg = err.get('message', '')
                    lines.append(f"  - [{err_type}] {err_msg}")
            elif schema_result == 'error':
                err_text = schema.get('error') or summary_zh or '未知错误'
                lines.append(f"- Schema 验证：出错（{err_text}）")
                _append_schema_meta(lines, sch_meta, summary_zh)
                # 把校验过程里收集到的 errors/warnings 也展开，避免再次出现"未知错误"黑盒
                for err in schema.get('errors', []):
                    if isinstance(err, dict):
                        lines.append(f"  - [{err.get('type', 'Error')}] {err.get('message', '')}")
                for warn in schema.get('warnings', []):
                    if isinstance(warn, dict):
                        lines.append(f"  - [{warn.get('type', 'Warning')}] {warn.get('message', '')}")
            elif rp_category != 'mdb':
                lines.append("- Schema 验证：未执行")
        elif rp_category != 'mdb':
            lines.append("- Schema 验证：未执行")

        # 规则合规性检查
        rule = checks.get('rule_compliance', {})
        if rule:
            if 'error' in rule:
                lines.append(f"- 规则合规性检查：出错（{rule['error']}）")
            elif 'result' in rule:
                # URI-based 模式
                rule_result = rule.get('result', 'unknown')
                total_checks = rule.get('total_checks_num', 0)
                failed_checks = rule.get('failed_checks_num', 0)
                if rule_result == 'pass':
                    lines.append(f"- 规则合规性检查：通过（{total_checks} 项检查全部通过）")
                else:
                    lines.append(f"- 规则合规性检查：不通过（{failed_checks}/{total_checks} 项失败）")
                # 列出具体失败详情
                error_details = rule.get('error_details', {})
                _append_error_details(lines, error_details)
            elif 'overall_compliant' in rule:
                # 评审点内容模式
                overall_compliant = rule.get('overall_compliant', False)
                total_rules = rule.get('total_rules', 0)
                compliant_rules = rule.get('compliant_rules', 0)
                failed_rules = rule.get('failed_rules', 0)
                warning_rules = rule.get('warning_rules', 0)
                if overall_compliant:
                    lines.append(f"- 规则合规性检查：通过（{compliant_rules}/{total_rules} 项合规）")
                else:
                    lines.append(f"- 规则合规性检查：不通过（{failed_rules}/{total_rules} 项失败，{warning_rules} 项警告）")
                # 列出具体失败详情
                error_details = rule.get('error_details', {})
                _append_error_details(lines, error_details)
                # 如果有 per_rule_results，也列出
                per_rule = rule.get('per_rule_results', [])
                if per_rule:
                    lines.append("  - **规则合规性失败项**：")
                    for pr in per_rule:
                        if not pr.get('compliant', True):
                            severity = str(pr.get('severity', 'shall')).lower()
                            level = "必须项" if severity in ('shall', 'must') else "建议性"
                            _append_rule_detail(lines, pr, level)
            else:
                lines.append("- 规则合规性检查：未知状态")
        else:
            lines.append("- 规则合规性检查：未执行")

        lines.append("")

    return "\n".join(lines)


def _judge_review_point_overall(rp: Dict[str, Any]) -> str:
    """判断单个评审点是否整体通过

    口径：
    - URI 生成 failed/error → fail
    - Schema 验证 fail / error → fail（注意：error 也视为 fail，避免吞掉真实异常；
      skip 视为通过，因为 schema 文件缺失不属于评审点本身的问题）
    - 规则合规性检查 fail / error / overall_compliant=False → fail
    """
    checks = rp.get('checks', {})

    uri_check = checks.get('uri_sample', {})
    if uri_check.get('status') in ('failed', 'error'):
        return 'fail'

    schema = checks.get('schema_validation', {})
    if schema.get('result') in ('fail', 'error'):
        return 'fail'

    rule = checks.get('rule_compliance', {})
    if 'error' in rule:
        return 'fail'
    if rule.get('result') == 'fail':
        return 'fail'
    if 'overall_compliant' in rule and not rule['overall_compliant']:
        return 'fail'

    return 'pass'


def _append_schema_meta(lines: list, sch_meta: Dict, summary_zh: Optional[str]) -> None:
    """把 schema_check 元信息（dmtf/oem 是否找到、使用了哪份 schema 文件）追加到 md 行里"""
    if not sch_meta:
        return

    has_dmtf = sch_meta.get('dmtf_schema_found')
    has_oem = sch_meta.get('oem_schema_found')
    validated_sources = sch_meta.get('validated_sources') or []

    if has_dmtf is not None or has_oem is not None or validated_sources:
        dmtf_label = "✓" if has_dmtf else ("✗" if has_dmtf is False else "?")
        oem_label = "✓" if has_oem else ("✗" if has_oem is False else "?")
        srcs = "/".join(s.upper() for s in validated_sources) if validated_sources else "无"
        lines.append(
            f"  - Schema 来源：DMTF {dmtf_label}，OEM {oem_label}（实际参与校验：{srcs}）"
        )

    entry_path = sch_meta.get('entry_schema_path_relative')
    entry_label = sch_meta.get('entry_schema_category_label_zh')
    if entry_path:
        if entry_label:
            lines.append(f"  - 入口 schema 文件：`{entry_path}`（{entry_label}）")
        else:
            lines.append(f"  - 入口 schema 文件：`{entry_path}`")

    def_path = sch_meta.get('definition_schema_path_relative')
    def_label = sch_meta.get('definition_schema_category_label_zh')
    if def_path:
        if def_label:
            lines.append(f"  - 实际定义文件：`{def_path}`（{def_label}）")
        else:
            lines.append(f"  - 实际定义文件：`{def_path}`")
    elif def_label and not def_path:
        lines.append(f"  - 实际定义来源：{def_label}")

    if summary_zh:
        lines.append(f"  - Schema 依据：{summary_zh}")


def _extract_rule_id(rule_name: str, default: str = "N/A") -> str:
    """从 "[MDB-001] xxx" / "[MDB-PROPERTY-014] xxx" 这类规则名中提取规则 ID。"""
    match = re.search(r"\[([A-Za-z]+(?:-[A-Za-z]+)?-\d+)\]", str(rule_name or ""))
    return match.group(1) if match else default


def _append_rule_detail(lines: list, err: Dict, level: str) -> None:
    rule_name = err.get('rule', '未知规则')
    rule_id = err.get('rule_id') or err.get('id') or _extract_rule_id(rule_name)
    message = err.get('message', '') or err.get('summary', '') or '未提供'
    advice = err.get('advice', '') or '无'

    lines.append(f"    **规则ID**：{rule_id}")
    lines.append(f"    **级别**：{level}")
    lines.append(f"    **问题描述**：{message}")
    lines.append(f"    **处理建议**：{advice}")


def _append_error_details(lines: list, error_details: Dict) -> None:
    """将 error_details 中的失败详情追加到 lines"""
    # 静态验证错误（Schema 合并进来的）
    static_errors = error_details.get('STATIC_VALIDATION', [])
    if static_errors:
        lines.append("  - **静态验证失败项**：")
        for idx, err in enumerate(static_errors):
            if idx:
                lines.append("")
            _append_rule_detail(lines, err, "Schema")

    # 模型验证错误（severity=shall/must 的规则失败）
    model_errors = error_details.get('MODEL_VALIDATION', [])
    if model_errors:
        lines.append("  - **规则合规性失败项（必须项）**：")
        for idx, err in enumerate(model_errors):
            if idx:
                lines.append("")
            _append_rule_detail(lines, err, "必须项")

    # 警告详情（severity=should/may）
    warning_errors = error_details.get('WARNING_DETAILS', [])
    if warning_errors:
        lines.append("  - **警告项（建议性）**：")
        for idx, err in enumerate(warning_errors):
            if idx:
                lines.append("")
            _append_rule_detail(lines, err, "建议性")


def process_post(
    title: str,
    content: str,
    schema_dir: str,
    output_dir: str,
    generate_uri: bool = True,
    save_non_redfish: bool = False,
    topic_id: str = "",
    debug_record: Optional['DebugRecordBuilder'] = None,
    config: dict = None,
) -> Dict[str, Any]:
    """
    处理单个帖子

    Args:
        title: 帖子标题
        content: 帖子内容
        schema_dir: Schema 文件目录
        output_dir: 输出目录
        generate_uri: 是否生成 URI 示例
        save_non_redfish: 是否保存非 Redfish 评审点结果
        topic_id: 帖子 ID（用于 debug 日志）
        debug_record: DebugRecordBuilder 实例（可选，用于收集中间数据）
        config: config.yaml 完整配置 dict，用于 MDB 校验器初始化

    Returns:
        处理结果字典
    """
    result = {
        "title": title,
        "post_redfish_related": False,
        "post_redfish_reason": "",
        "total_review_points": 0,
        "redfish_review_points": 0,
        "non_redfish_review_points": 0,
        "results": []
    }

    logger.info(f"{'='*70}")
    logger.info(f"处理帖子: {title[:60]}...")
    logger.info(f"{'='*70}")

    # 1. 判断帖子是否与 Redfish 或 MDB 相关
    logger.info("[步骤 1/4] 判断帖子是否与 Redfish 或 MDB 资源协作接口相关...")
    with timed() as _t_relevance:
        is_related, reason = is_post_relevant(title, content)
    result['post_redfish_related'] = is_related
    result['post_redfish_reason'] = reason

    if debug_record:
        debug_record.set_relevance(is_related, reason, _t_relevance["duration_seconds"])

    logger.info(f"  结果: {'[OK] 是' if is_related else '[SKIP] 否'}")
    logger.info(f"  原因: {reason}")

    if not is_related:
        logger.info("[SKIP] 帖子与 Redfish 和 MDB 均无关，跳过处理")
        result['final_result'] = generate_final_result(result)
        return result

    # 2. 提取所有评审点（使用增强提取逻辑）
    logger.info("[步骤 2/4] 提取评审点...")
    with timed() as _t_extract:
        review_points = extract_all_review_points(content)
    result['total_review_points'] = len(review_points)
    logger.info(f"  共提取到 {len(review_points)} 个评审点")

    if debug_record:
        debug_record.set_review_points(review_points, _t_extract["duration_seconds"])

    if not review_points:
        logger.info("[SKIP] 未提取到评审点，跳过处理")
        result['final_result'] = ""
        return result

    # 3. 逐评审点三路分类：MDB / Redfish / 其他
    logger.info("[步骤 3/4] 评审点分类...")
    mdb_points = []
    redfish_points = []
    other_points = []
    for rp in review_points:
        cat = classify_review_point(rp.get('title', ''), rp.get('content', ''))
        if cat == 'mdb':
            mdb_points.append(rp)
        elif cat == 'redfish':
            redfish_points.append(rp)
        else:
            other_points.append(rp)

    result['redfish_review_points'] = len(redfish_points)
    result['mdb_review_points'] = len(mdb_points)
    result['non_redfish_review_points'] = len(other_points)

    if debug_record:
        debug_record.set_filter_result(redfish_points, other_points, _t_extract.get("duration_seconds", 0))

    logger.info(f"  MDB 相关: {len(mdb_points)} 个")
    logger.info(f"  Redfish 相关: {len(redfish_points)} 个")
    logger.info(f"  其他: {len(other_points)} 个")

    if not redfish_points and not mdb_points:
        logger.info("[SKIP] 无相关评审点，跳过处理")
        result['final_result'] = ""
        return result

    # 4. 按原始顺序逐评审点处理（保持 review_points 的顺序）
    logger.info("[步骤 4/4] 检查相关评审点...")

    # 构建 MDB 同级评审点上下文（用于跨评审点误报防护）
    mdb_sibling_context = ""
    if len(mdb_points) > 1:
        mdb_sibling_context = "\n\n---\n\n".join(
            f"【{rp.get('title', '评审点')}】\n{rp.get('content', '')}"
            for rp in mdb_points
        )
        logger.info("  MDB 同级上下文: %d 个评审点, %d 字符", len(mdb_points), len(mdb_sibling_context))

    # 创建输出目录（仅在文件输出启用时）
    if not Config.DISABLE_FILE_OUTPUT:
        os.makedirs(output_dir, exist_ok=True)

    # 构建分类索引，保持原始顺序
    _category_map = {}
    for rp in mdb_points:
        _category_map[id(rp)] = 'mdb'
    for rp in redfish_points:
        _category_map[id(rp)] = 'redfish'

    relevant_points = [rp for rp in review_points if id(rp) in _category_map]

    for i, rp in enumerate(relevant_points, 1):
        rp_category = _category_map[id(rp)]
        cat_label = 'MDB' if rp_category == 'mdb' else 'Redfish'
        logger.info(f">>> [{i}/{len(relevant_points)}] [{cat_label}] 检查评审点: {rp['title'][:50]}...")

        if rp_category == 'mdb':
            # MDB 评审点：调用 MDB 校验器
            _rp_start = time.monotonic()
            check_result = check_mdb_review_point(rp, config, mdb_sibling_context)
            check_result['category'] = 'mdb'
            _rp_duration = round(time.monotonic() - _rp_start, 4)

            # 收集 debug 数据
            if debug_record:
                _debug_check_data = {
                    "title": rp.get('title', ''),
                    "index": i,
                    "category": 'mdb',
                    "duration_seconds": _rp_duration,
                    "rule_compliance": check_result.get('checks', {}).get('rule_compliance'),
                }
                debug_record.add_review_point_check(_debug_check_data)

            result['results'].append(check_result)

            is_api_err, error_msg, _ = _is_api_error(check_result)
            if is_api_err:
                logger.error(f"[ABORT] MDB 评审点 '{rp['title'][:30]}' 检查服务调用失败，终止检查: {error_msg}")
                result['final_result'] = _format_infrastructure_failure(rp.get('title', ''))
                return result
        else:
            # Redfish 评审点：调用现有 Redfish 校验流程（含重试）
            max_retry = Config.MAX_RETRY
            retry_delay = Config.RETRY_DELAY
            check_result = None
            cached_uri_sample = None
            cached_checks = None
            _rp_start = time.monotonic()
            for attempt in range(1, max_retry + 1):
                check_result = check_single_review_point(
                    rp, schema_dir, output_dir, generate_uri,
                    _cached_uri_sample=cached_uri_sample,
                    _cached_checks=cached_checks,
                    debug_record=debug_record
                )
                # 如果不是 API 级别错误，视为检查完成（无论成功或业务层面失败）
                is_api_err, error_msg, error_phase = _is_api_error(check_result)
                if not is_api_err:
                    break
                # 缓存已成功的步骤结果，下次重试时跳过
                if error_phase != 'uri' and check_result.get('_uri_sample'):
                    cached_uri_sample = check_result['_uri_sample']
                    cached_checks = {k: v for k, v in check_result.get('checks', {}).items()
                                     if k != 'rule_compliance'}
                else:
                    # URI 生成阶段失败，需要完全重试
                    cached_uri_sample = None
                    cached_checks = None
                if attempt < max_retry:
                    retry_from = "规则检查" if cached_uri_sample else "完整流程"
                    logger.warning(f"[RETRY] 评审点 '{rp['title'][:30]}' 检查失败 (第{attempt}次)，{retry_delay}秒后重试（从{retry_from}开始）... 错误: {error_msg}")
                    time.sleep(retry_delay)

            _rp_duration = round(time.monotonic() - _rp_start, 4)
            check_result['category'] = 'redfish'

            # 收集 debug 数据（在清理临时 key 之前）
            if debug_record and check_result:
                _debug_check_data = {
                    "title": rp.get('title', ''),
                    "index": i,
                    "category": 'redfish',
                    "retry_count": attempt,
                    "duration_seconds": _rp_duration,
                    "uri_generation": {
                        "status": check_result.get('checks', {}).get('uri_sample', {}).get('status', 'not_executed'),
                        "uri_sample": check_result.get('_uri_sample'),
                        "duration_seconds": check_result.get('_debug_uri_duration', 0.0)
                    },
                    "schema_validation": check_result.get('checks', {}).get('schema_validation'),
                    "rule_compliance": check_result.get('checks', {}).get('rule_compliance'),
                }
                if _debug_check_data["schema_validation"]:
                    _debug_check_data["schema_validation"] = dict(_debug_check_data["schema_validation"])
                    _debug_check_data["schema_validation"]["duration_seconds"] = check_result.get('_debug_schema_duration', 0.0)
                _debug_check_data["rule_compliance_duration_seconds"] = check_result.get('_debug_rule_duration', 0.0)
                debug_record.add_review_point_check(_debug_check_data)

            # 清理临时缓存数据，避免序列化到 JSON
            if check_result and '_uri_sample' in check_result:
                del check_result['_uri_sample']
            if check_result:
                check_result.pop('_debug_uri_duration', None)
                check_result.pop('_debug_schema_duration', None)
                check_result.pop('_debug_rule_duration', None)
            result['results'].append(check_result)

            # 重试耗尽后仍为 API 错误，提前终止整个帖子检查
            is_api_err, error_msg, _ = _is_api_error(check_result)
            if is_api_err:
                logger.error(f"[ABORT] 评审点 '{rp['title'][:30]}' 经 {max_retry} 次重试仍失败，终止检查: {error_msg}")
                result['final_result'] = _format_infrastructure_failure(rp.get('title', ''), max_retry)
                return result

    # 生成总体评审结论
    for check_result in result.get('results', []):
        is_api_err, error_msg, _ = _is_api_error(check_result)
        if is_api_err:
            logger.error(f"[ABORT] 检查结果包含服务调用失败，终止生成回复: {error_msg}")
            result['final_result'] = _format_infrastructure_failure("")
            return result

    result['final_result'] = generate_final_result(result)

    # 保存非 Redfish/MDB 评审点信息
    if save_non_redfish and other_points:
        result['non_redfish_results'] = [
            {
                "title": rp['title'],
                "content": rp['content'],
                "redfish_related": False
            }
            for rp in other_points
        ]

    return result


def run_schema_check(title: str, user_question: str, topic_id: str, config: dict = None) -> str:
    """
    包装 process_post 的便捷函数，供主应用调用。

    Args:
        title: 帖子标题
        user_question: 帖子内容 (HTML)
        topic_id: 帖子 ID
        config: config.yaml 的完整配置 dict (包含 schema_validation section)。
                如果为 None，使用默认配置。

    Returns:
        result['final_result'] -- Markdown 格式的评审结论字符串。
        如果发生异常，返回错误信息字符串。
    """
    try:
        config = config or {}

        if config and 'schema_validation' in config:
            Config.configure_from_dict(config['schema_validation'])

        Config.init_directories()

        # 初始化 debug 日志（幂等）：pre_audit.readiness_field 有非空值时启用
        _debug_enabled = bool(config.get('pre_audit', {}).get('readiness_field'))
        if _debug_enabled:
            init_debug_logger(config.get('database', {}))

        schema_dir = str(Config.SCHEMA_DIR)
        output_dir = str(Config.OUTPUT_DIR)

        with DebugRecordBuilder(topic_id, title) as debug_record:
            result = process_post(
                title=title,
                content=user_question,
                schema_dir=schema_dir,
                output_dir=output_dir,
                generate_uri=True,
                save_non_redfish=False,
                topic_id=topic_id,
                debug_record=debug_record if _debug_enabled else None,
                config=config,
            )

            # 计算 overall_pass
            review_results = result.get('results', [])
            if review_results:
                overall_pass = all(
                    _judge_review_point_overall(rp) == 'pass'
                    for rp in review_results
                )
            else:
                overall_pass = None

            debug_record.finalize(
                final_result_preview=result.get('final_result', '')[:500] if result.get('final_result') else None,
                overall_pass=overall_pass
            )

        return result.get('final_result', '')

    except Exception as e:
        logger.error(f"run_schema_check 失败 (topic_id={topic_id}): {e}")
        return f"[Schema检查出错] {e}"

