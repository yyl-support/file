"""MDB 合规性检查器单元测试。"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ForumBot.MdbValidation.mdb_checker import (
    load_rules,
    parse_batch_result,
    _repair_json_text,
    _extract_top_level_json_array,
    _extract_markdown_fence,
    _try_repair_truncated_array,
    _validate_and_fill,
    _make_error_result,
    _has_concrete_evidence,
    _apply_false_positive_guard,
    build_rule_mappings,
    group_rules_for_check,
    format_rules_for_batch,
    is_blocking_severity,
    MdbComplianceChecker,
    RULES_DIR,
)


# ==================== 规则加载 ====================


class TestLoadRules:
    def test_load_rules_from_default_path(self):
        """默认路径应能加载到规则文件。"""
        rules = load_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_rules_have_required_fields(self):
        rules = load_rules()
        required = {"id", "category", "severity", "rule", "check", "rationale"}
        for r in rules:
            assert required.issubset(set(r.keys())), f"规则 {r.get('id')} 缺字段"

    def test_load_rules_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_rules(tmp_path / "nonexistent.json")

    def test_rules_drop_v6_2_id_and_use_shall(self):
        rules = load_rules()
        severities = [r["severity"] for r in rules]

        assert all("v6_2_id" not in r for r in rules)
        assert severities.count("must") == 0
        assert severities.count("shall") > 0
        assert set(severities).issubset({"shall", "should", "may"})

    def test_load_rules_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not a json array")
        with pytest.raises((ValueError, json.JSONDecodeError)):
            load_rules(bad_file)

    def test_load_rules_missing_fields(self, tmp_path):
        bad_file = tmp_path / "missing.json"
        bad_file.write_text(json.dumps([{"id": "RULE-001"}]))
        with pytest.raises(ValueError, match="缺字段"):
            load_rules(bad_file)

    def test_load_rules_duplicate_id(self, tmp_path):
        dup_file = tmp_path / "dup.json"
        dup_file.write_text(json.dumps([
            {"id": "RULE-001", "category": "a", "severity": "shall", "rule": "r", "check": "c", "rationale": "ra"},
            {"id": "RULE-001", "category": "b", "severity": "shall", "rule": "r", "check": "c", "rationale": "ra"},
        ]))
        with pytest.raises(ValueError, match="重复"):
            load_rules(dup_file)


# ==================== JSON 修复 ====================


class TestRepairJsonText:
    def test_bom_removal(self):
        assert _repair_json_text("\ufeff[1]") == "[1]"

    def test_smart_quotes(self):
        assert _repair_json_text('\u201chello\u201d') == '"hello"'

    def test_trailing_comma_array(self):
        assert _repair_json_text("[1, 2, ]") == "[1, 2]"

    def test_trailing_comma_object(self):
        assert _repair_json_text('{"a": 1, }') == '{"a": 1}'


class TestExtractTopLevelJsonArray:
    def test_simple_array(self):
        assert _extract_top_level_json_array("[1, 2, 3]") == "[1, 2, 3]"

    def test_embedded_array(self):
        text = "prefix [1, 2] suffix"
        assert _extract_top_level_json_array(text) == "[1, 2]"

    def test_nested_arrays(self):
        text = "[[1], [2]]"
        assert _extract_top_level_json_array(text) == "[[1], [2]]"

    def test_no_array(self):
        assert _extract_top_level_json_array("no array") is None


class TestExtractMarkdownFence:
    def test_json_fence(self):
        text = '```json\n[1, 2]\n```'
        assert _extract_markdown_fence(text) == "[1, 2]"

    def test_plain_fence(self):
        text = '```\n[1, 2]\n```'
        assert _extract_markdown_fence(text) == "[1, 2]"

    def test_no_fence(self):
        assert _extract_markdown_fence("[1, 2]") is None


class TestTryRepairTruncatedArray:
    def test_truncated_with_complete_objects(self):
        text = '[{"a": 1}, {"b": 2}, {"c":'
        result = _try_repair_truncated_array(text)
        assert result is not None
        parsed = json.loads(result)
        assert len(parsed) == 2

    def test_no_truncation(self):
        text = '[{"a": 1}]'
        # Not truncated, but function should still return something
        result = _try_repair_truncated_array(text)
        if result:
            json.loads(result)  # Should be valid

    def test_empty_input(self):
        assert _try_repair_truncated_array("no array") is None


# ==================== parse_batch_result ====================


_SAMPLE_RULES = [
    {"id": "RULE-001", "category": "structure", "severity": "shall", "rule": "r1", "check": "c1", "rationale": "ra1"},
    {"id": "RULE-002", "category": "naming", "severity": "should", "rule": "r2", "check": "c2", "rationale": "ra2"},
]


class TestSeverity:
    def test_shall_and_legacy_must_are_blocking(self):
        assert is_blocking_severity("shall") is True
        assert is_blocking_severity("must") is True
        assert is_blocking_severity("should") is False


class TestParseBatchResult:
    def test_valid_json_array(self):
        raw = json.dumps([
            {"rule_id": "RULE-001", "compliant": True, "summary": "ok", "advice": None, "findings": []},
            {"rule_id": "RULE-002", "compliant": True, "summary": "ok", "advice": None, "findings": []},
        ])
        results = parse_batch_result(raw, _SAMPLE_RULES)
        assert len(results) == 2
        assert all(r["compliant"] for r in results)

    def test_empty_response(self):
        results = parse_batch_result("", _SAMPLE_RULES)
        assert len(results) == 2
        assert all("error" in r for r in results)

    def test_markdown_wrapped(self):
        inner = json.dumps([
            {"rule_id": "RULE-001", "compliant": True, "summary": "ok", "advice": None, "findings": []},
            {"rule_id": "RULE-002", "compliant": True, "summary": "ok", "advice": None, "findings": []},
        ])
        raw = f"```json\n{inner}\n```"
        results = parse_batch_result(raw, _SAMPLE_RULES)
        assert len(results) == 2

    def test_missing_rule_in_response(self):
        raw = json.dumps([
            {"rule_id": "RULE-001", "compliant": True, "summary": "ok", "advice": None, "findings": []},
        ])
        results = parse_batch_result(raw, _SAMPLE_RULES)
        assert len(results) == 2
        # RULE-002 should get an error result
        mdb002 = [r for r in results if r["rule_id"] == "RULE-002"][0]
        assert "error" in mdb002

    def test_non_compliant_result(self):
        raw = json.dumps([
            {"rule_id": "RULE-001", "compliant": False, "summary": "违规", "advice": "修复建议", "findings": [{"evidence": "引用原文片段", "location": "表格行"}]},
            {"rule_id": "RULE-002", "compliant": True, "summary": "ok", "advice": None, "findings": []},
        ])
        results = parse_batch_result(raw, _SAMPLE_RULES)
        assert results[0]["compliant"] is False
        assert results[0]["advice"] == "修复建议"


class TestRuleMappings:
    def test_split_multi_legacy_ids(self):
        rules = [
            {
                "id": "RULE-NEW",
                "category": "structure",
                "severity": "shall",
                "rule": "r",
                "check": "c",
                "rationale": "ra",
                "legacy_id": "RULE-OLD-1、RULE-OLD-2, RULE-OLD-3",
            }
        ]

        mappings = build_rule_mappings(rules)

        assert mappings["legacy_to_new"]["RULE-OLD-1"] == "RULE-NEW"
        assert mappings["legacy_to_new"]["RULE-OLD-2"] == "RULE-NEW"
        assert mappings["legacy_to_new"]["RULE-OLD-3"] == "RULE-NEW"


# ==================== _validate_and_fill ====================


class TestValidateAndFill:
    def test_fill_compliant_result(self):
        raw_results = [{"rule_id": "RULE-001", "compliant": True, "summary": "ok"}]
        filled = _validate_and_fill(raw_results, _SAMPLE_RULES)
        assert len(filled) == 2  # RULE-001 + missing RULE-002

    def test_non_compliant_gets_default_advice(self):
        raw_results = [
            {"rule_id": "RULE-001", "compliant": False, "summary": "违规", "advice": None, "findings": []},
        ]
        filled = _validate_and_fill(raw_results, _SAMPLE_RULES)
        mdb001 = [r for r in filled if r["rule_id"] == "RULE-001"][0]
        assert mdb001["advice"] is not None  # Gets default advice

    def test_multi_legacy_id_response_maps_to_current_rule(self):
        rules = [
            {
                "id": "RULE-NEW",
                "category": "structure",
                "severity": "shall",
                "rule": "r",
                "check": "c",
                "rationale": "ra",
                "legacy_id": "RULE-OLD-1、RULE-OLD-2",
            }
        ]
        raw_results = [
            {
                "rule_id": "RULE-OLD-2",
                "compliant": False,
                "summary": "旧规则命中",
                "advice": "请修复",
                "findings": [{"evidence": "正文中引用到的具体片段内容很长", "location": "表格第1行"}],
            }
        ]

        filled = _validate_and_fill(raw_results, rules, build_rule_mappings(rules)["legacy_to_new"])

        assert filled[0]["rule_id"] == "RULE-NEW"
        assert filled[0]["compliant"] is False
        assert "error" not in filled[0]


# ==================== _make_error_result ====================


class TestMakeErrorResult:
    def test_structure(self):
        rule = _SAMPLE_RULES[0]
        result = _make_error_result(rule, "test_error")
        assert result["rule_id"] == "RULE-001"
        assert result["error"] == "test_error"
        assert result["compliant"] is True  # Error results default to compliant


# ==================== 误报防护 ====================


class TestHasConcreteEvidence:
    def test_no_findings(self):
        assert _has_concrete_evidence([]) is False

    def test_short_evidence(self):
        assert _has_concrete_evidence([{"evidence": "short", "location": "loc"}]) is False

    def test_generic_evidence(self):
        assert _has_concrete_evidence([{"evidence": "未提供相关信息数据", "location": "section"}]) is False

    def test_concrete_evidence(self):
        assert _has_concrete_evidence([
            {"evidence": "属性名称列的值写为 _Property_ 占位符", "location": "属性表格第2行"}
        ]) is True


class TestApplyFalsePositiveGuard:
    def test_rule_without_evidence_suppressed(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "违规",
            "advice": "修复",
            "findings": [],
        }]
        guarded = _apply_false_positive_guard(results)
        assert guarded[0]["compliant"] is True
        assert "suppressed_reason" in guarded[0]

    def test_rule_with_evidence_kept(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "违规",
            "advice": "修复",
            "findings": [{"evidence": "正文中明确写了属性名称的占位符值", "location": "表格"}],
        }]
        guarded = _apply_false_positive_guard(results)
        assert guarded[0]["compliant"] is False

    def test_rule_without_evidence_suppressed_regardless_of_rule_id(self):
        results = [{
            "rule_id": "RULE-B",
            "compliant": False,
            "summary": "违规",
            "advice": "修复",
            "findings": [],
        }]
        guarded = _apply_false_positive_guard(results)
        assert guarded[0]["compliant"] is True

    def test_missing_column_claim_refuted_by_body_is_suppressed(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "不合规：属性表缺少「访问权限」列，且属性描述中权限写法不规范。",
            "advice": "请在属性表中增加「访问权限」列。",
            "findings": [{"evidence": "属性表缺少访问权限列", "location": "属性表"}],
        }]
        body = """属性名称
签名
只读
变化通知
属性描述
访问权限
属性来源
持久化类型
CapableLinkSpeedGbps
aq
true
true
该网口支持的网络链路速率能力集合
R：ReadOnly
NA
无需持久化
"""

        guarded = _apply_false_positive_guard(results, body)

        assert guarded[0]["compliant"] is True
        assert guarded[0]["suppressed_reason"] == "missing_column_claim_refuted_by_body"


# ==================== 规则分组 ====================


    def test_missing_property_table_claim_refuted_by_gfm_table_is_suppressed(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "正文完全缺失属性表，未提供属性名称、签名、只读、变化通知、属性描述、访问权限等核心字段。",
            "advice": "补充属性表。",
            "findings": [{
                "evidence": "未看到 RevisionId 的属性表。",
                "location": "评审点1",
            }],
        }]
        body = """
评审点1：新增资源协作接口属性RevisionId

| 属性名称 | 签名 | 只读 | 变化通知 | 属性描述 | 访问权限 | 属性来源 | 持久化类型 | 易变属性 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RevisionId | y | true | true | PCIe功能的RevisionId，默认值：空 | R：ReadOnly | NA | 无需持久化 | true |
"""

        guarded = _apply_false_positive_guard(results, body)

        assert guarded[0]["compliant"] is True
        assert guarded[0]["suppressed_reason"] == "missing_table_claim_refuted_by_body"

    def test_system_reset_clear_does_not_contradict_reset_persistence(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "属性持久化类型为复位持久化，但描述中明确指出系统复位后清零，两者存在矛盾。",
            "advice": "请确认持久化类型定义。",
            "findings": [{
                "evidence": "系统上下电/系统复位/NPU复位，恢复为0。",
                "location": "属性表",
            }],
        }]
        body = """
| 属性名称 | 属性描述 | 持久化类型 |
| --- | --- | --- |
| CorrectableError | NPU发生可纠正错误，默认为0。系统上下电/系统复位/NPU复位，恢复为0。 | 复位持久化 |
| UncorrectableError | NPU发生不可纠正错误，默认为0。系统上下电/系统复位/NPU复位，恢复为0。 | 复位持久化 |
"""

        guarded = _apply_false_positive_guard(results, body)

        assert guarded[0]["compliant"] is True
        assert guarded[0]["suppressed_reason"] == "reset_persistence_domain_conflation"

    def test_bmc_reset_clear_keeps_reset_persistence_contradiction(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "属性持久化类型为复位持久化，但描述中明确指出BMC复位后清零，两者存在矛盾。",
            "advice": "请确认持久化类型定义。",
            "findings": [{
                "evidence": "BMC复位后清零。",
                "location": "属性表",
            }],
        }]
        body = """
| 属性名称 | 属性描述 | 持久化类型 |
| --- | --- | --- |
| Failure | BMC复位后清零。 | 复位持久化 |
"""

        guarded = _apply_false_positive_guard(results, body)

        assert guarded[0]["compliant"] is False

    def test_change_rationale_present_suppresses_missing_reason_claim(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "变更属性持久化类型未提供变更原因和影响说明",
            "advice": "请补充持久化类型变更为复位持久化的变更原因和影响说明",
            "findings": [{
                "evidence": "硬盘故障和预故障告警预期在BMC复位场景保持告警状态不变",
                "location": "背景",
            }],
        }]
        body = """
背景
硬盘故障和预故障告警预期在BMC复位场景保持告警状态不变，不因为BMC复位导致告警恢复再产生。

整体方案
硬盘故障告警关联的资源协作接口属性为Failure，硬盘预故障告警关联的资源协作接口属性为PredictiveFailure，这两个属性变更为复位持久化，在bmc复位场景保持属性不变，防止误恢复告警。
"""

        guarded = _apply_false_positive_guard(results, body)

        assert guarded[0]["compliant"] is True
        assert guarded[0]["suppressed_reason"] == "change_rationale_present_in_body"

    def test_generic_interface_name_with_instance_path_suppresses_path_contradiction_claim(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "标题声明新增接口为 bmc.kepler.Systems.Processor.ProcessorMemory，但正文路径实际挂载在 Processors/NPU 和 Processors/GPU 子层级下，标题与正文路径层级互相矛盾且未说明差异",
            "advice": "建议修改标题以准确反映路径层级",
            "findings": [{
                "evidence": "新增资源协作接口 bmc.kepler.Systems.Processor.ProcessorMemory",
                "location": "评审点2",
            }],
        }]
        body = """
评审点2：新增资源协作接口 bmc.kepler.Systems.Processor.ProcessorMemory
接口描述：提供处理器内存信息查询能力。

评审点3：新增资源协作路径 /bmc/kepler/Systems/{SystemId}/Processors/{ProcessorType}/{ProcessorId}/ProcessorMemory/{MemoryType}
路径描述：用于存储和管理处理器内存配置信息，路径区分NPU和GPU处理器类型。

| 实现接口 | 实现接口描述 |
| --- | --- |
| bmc.kepler.Systems.Processor.ProcessorMemory | 实现CapacityMiB、IntegratedMemory、MemoryType、SpeedMHz属性，提供处理器内存信息查询功能 |
"""

        guarded = _apply_false_positive_guard(results, body)

        assert guarded[0]["compliant"] is True
        assert guarded[0]["suppressed_reason"] == "generic_interface_implemented_by_instance_path"

    def test_state_code_explanation_does_not_imply_complete_enum(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "PredictiveFailure 属性默认值 255 不在声明的枚举范围 {0, 1} 内",
            "advice": "请在属性描述中补充默认值 255 的业务含义并将其加入候选集",
            "findings": [{
                "evidence": "硬盘是否预故障，0：否，1：是，默认值：255",
                "location": "属性表",
            }],
        }]
        body = """
| 属性名称 | 签名 | 只读 | 变化通知 | 属性描述 | 访问权限 | 属性来源 | 持久化类型 | 易变属性 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PredictiveFailure | y | true | false | 硬盘是否预故障，0：否，1：是，默认值：255 | R：ReadOnly |  | 复位持久化 | false |
"""

        guarded = _apply_false_positive_guard(results, body)

        assert guarded[0]["compliant"] is True
        assert guarded[0]["suppressed_reason"] == "state_code_explanation_not_complete_enum"

    def test_explicit_range_keeps_default_out_of_range_finding(self):
        results = [{
            "rule_id": "RULE-A",
            "compliant": False,
            "summary": "PredictiveFailure 属性默认值 255 不在声明的取值范围 {0, 1} 内",
            "advice": "请修正默认值或取值范围",
            "findings": [{
                "evidence": "取值范围：0：否，1：是，默认值：255",
                "location": "属性表",
            }],
        }]
        body = """
| 属性名称 | 签名 | 属性描述 |
| --- | --- | --- |
| PredictiveFailure | y | 取值范围：0：否，1：是，默认值：255 |
"""

        guarded = _apply_false_positive_guard(results, body)

        assert guarded[0]["compliant"] is False


class TestGroupRulesForCheck:
    def test_groups_cover_all_rules(self):
        rules = load_rules()
        groups = group_rules_for_check(rules)
        grouped_rules = []
        for _, group_rules in groups:
            grouped_rules.extend(group_rules)
        assert len(grouped_rules) == len(rules)

    def test_at_least_3_groups(self):
        rules = load_rules()
        groups = group_rules_for_check(rules)
        assert len(groups) >= 3


class TestFormatRulesForBatch:
    def test_format_output(self):
        rules = _SAMPLE_RULES
        text = format_rules_for_batch(rules)
        assert "RULE-001" in text
        assert "RULE-002" in text
        assert "规则 1" in text
        assert "规则 2" in text


# ==================== MdbComplianceChecker ====================


class TestMdbComplianceChecker:
    @pytest.fixture
    def mock_config(self):
        return {
            "schema_validation": {
                "model": "test-model",
                "api_key": "test-key",
                "base_url": "http://localhost:8080",
                "max_retry": 1,
            }
        }

    @pytest.fixture
    def sample_llm_response(self):
        """模拟 LLM 返回全部合规的结果。"""
        rules = load_rules()
        return json.dumps([
            {
                "rule_id": r["id"],
                "category": r["category"],
                "severity": r["severity"],
                "compliant": True,
                "summary": "合规",
                "advice": None,
                "findings": [],
            }
            for r in rules
        ])

    def test_init_with_config(self, mock_config):
        checker = MdbComplianceChecker(mock_config)
        assert checker._llm is not None
        assert len(checker._rules) > 0

    def test_init_empty_config(self):
        checker = MdbComplianceChecker({})
        assert checker._llm is not None

    @patch.object(MdbComplianceChecker, '_call_llm')
    def test_check_review_point_all_compliant(self, mock_call, mock_config, sample_llm_response):
        mock_call.return_value = sample_llm_response
        checker = MdbComplianceChecker(mock_config)
        result = checker.check_review_point("测试标题", "测试内容")
        assert result["overall_compliant"] is True
        assert result["result"] == "pass"
        assert result["total_rules"] > 0

    @patch.object(MdbComplianceChecker, '_call_llm')
    def test_check_review_point_with_failure(self, mock_call, mock_config):
        rules = load_rules()
        fail_rule_id = next(r["id"] for r in rules if r["severity"] == "shall")
        response = []
        for r in rules:
            if r["id"] == fail_rule_id:
                response.append({
                    "rule_id": r["id"],
                    "category": r["category"],
                    "severity": r["severity"],
                    "compliant": False,
                    "summary": f"{r['id']} 违规",
                    "advice": "请修复",
                    "findings": [{"evidence": "正文中引用到的具体片段内容很长", "location": "表格第1行"}],
                })
            else:
                response.append({
                    "rule_id": r["id"],
                    "category": r["category"],
                    "severity": r["severity"],
                    "compliant": True,
                    "summary": "合规",
                    "advice": None,
                    "findings": [],
                })
        mock_call.return_value = json.dumps(response)

        checker = MdbComplianceChecker(mock_config)
        result = checker.check_review_point("测试标题", "测试内容")
        assert result["failed_rules"] >= 1
        assert result["overall_compliant"] is False

    @patch.object(MdbComplianceChecker, '_call_llm')
    def test_should_failure_is_warning_only(self, mock_call, mock_config):
        mock_call.return_value = json.dumps([
            {
                "rule_id": "RULE-001",
                "compliant": True,
                "summary": "ok",
                "advice": None,
                "findings": [],
            },
            {
                "rule_id": "RULE-002",
                "compliant": False,
                "summary": "warning",
                "advice": "review",
                "findings": [{"evidence": "concrete evidence for warning result", "location": "table row 1"}],
            },
        ])
        checker = MdbComplianceChecker(mock_config)

        result = checker._check_review_point_grouped("title", "body", _SAMPLE_RULES)

        assert result["failed_rules"] == 0
        assert result["warning_rules"] == 1
        assert result["overall_compliant"] is True

    @patch.object(MdbComplianceChecker, '_call_llm')
    def test_check_review_point_llm_error(self, mock_call, mock_config):
        mock_call.side_effect = Exception("LLM connection timeout")
        checker = MdbComplianceChecker(mock_config)
        result = checker.check_review_point("测试标题", "测试内容")
        # All rules should get error results
        assert result["total_rules"] > 0

    def test_truncate_long_text(self, mock_config):
        checker = MdbComplianceChecker(mock_config)
        checker._body_max_chars = 100
        long_text = "x" * 200
        truncated = checker._truncate(long_text)
        assert len(truncated) <= 200
        assert "省略" in truncated
