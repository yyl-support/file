import pytest

from src.ForumBot.SchemaValidation import end_to_end_check as e2e


def test_run_schema_check_returns_final_result(monkeypatch, tmp_path):
    captured = {}

    def fake_configure(config_dict):
        captured["config"] = config_dict

    def fake_process_post(**kwargs):
        captured["kwargs"] = kwargs
        return {"final_result": "final markdown"}

    monkeypatch.setattr(e2e.Config, "configure_from_dict", fake_configure)
    monkeypatch.setattr(e2e.Config, "init_directories", lambda: None)
    monkeypatch.setattr(e2e.Config, "SCHEMA_DIR", str(tmp_path / "schemas"))
    monkeypatch.setattr(e2e.Config, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(e2e, "process_post", fake_process_post)

    result = e2e.run_schema_check(
        title="Redfish title",
        user_question="question body",
        topic_id="123",
        config={
            "schema_validation": {
                "api_key": "key",
                "base_url": "https://api.example.com",
                "model": "test-model",
            }
        },
    )

    assert result == "final markdown"
    assert captured["config"]["model"] == "test-model"
    assert captured["kwargs"]["title"] == "Redfish title"
    assert captured["kwargs"]["content"] == "question body"


def test_process_post_non_redfish_short_circuits(monkeypatch):
    monkeypatch.setattr(e2e, "is_post_relevant", lambda title, content: (False, "not relevant"))
    monkeypatch.setattr(e2e, "generate_final_result", lambda result: "skip result")

    result = e2e.process_post(
        title="普通帖子",
        content="<p>nothing</p>",
        schema_dir="schemas",
        output_dir="out",
    )

    assert result["post_redfish_related"] is False
    assert result["final_result"] == "skip result"
    assert result["results"] == []


def test_process_post_redfish_success_flow(monkeypatch):
    monkeypatch.setattr(e2e.Config, "DISABLE_FILE_OUTPUT", True)
    monkeypatch.setattr(e2e.Config, "MAX_RETRY", 1)
    monkeypatch.setattr(e2e.Config, "RETRY_DELAY", 0)
    monkeypatch.setattr(e2e, "is_post_relevant", lambda title, content: (True, "has redfish"))
    monkeypatch.setattr(e2e, "extract_all_review_points", lambda content: [{"title": "rp1", "content": "c1"}])
    monkeypatch.setattr(e2e, "classify_review_point", lambda title, content: 'redfish')
    monkeypatch.setattr(
        e2e,
        "check_single_review_point",
        lambda *args, **kwargs: {
            "checks": {
                "uri_sample": {"status": "ok"},
                "rule_compliance": {
                    "failed_checks_num": 0,
                    "error_details": {"MODEL_VALIDATION": [], "WARNING_DETAILS": []},
                },
            }
        },
    )
    monkeypatch.setattr(e2e, "generate_final_result", lambda result: "done")

    result = e2e.process_post(
        title="Redfish 帖子",
        content="<p>content</p>",
        schema_dir="schemas",
        output_dir="out",
    )

    assert result["post_redfish_related"] is True
    assert result["redfish_review_points"] == 1
    assert len(result["results"]) == 1
    assert result["final_result"] == "done"


def test_is_post_redfish_related_matches_keywords_and_negative():
    assert e2e.is_post_redfish_related("Question", "Need Redfish API help")[0] is True
    assert e2e.is_post_redfish_related("Question", "This mentions BMC management")[0] is True
    assert e2e.is_post_redfish_related("Question", "Plain HTML with no platform terms")[0] is False


def test_filter_redfish_review_points_splits_points(monkeypatch):
    monkeypatch.setattr(
        e2e,
        "is_redfish_related",
        lambda title, content: "redfish" in content.lower(),
    )
    review_points = [
        {"title": "A", "content": "Redfish requirement"},
        {"title": "B", "content": "General feedback"},
    ]

    redfish_points, non_redfish_points = e2e.filter_redfish_review_points(review_points)

    assert redfish_points == [review_points[0]]
    assert non_redfish_points == [review_points[1]]


def test_validate_uri_sample_returns_error_when_validator_raises(monkeypatch):
    class ExplodingValidator:
        def __init__(self, schema_dir, no_oem=False):
            raise RuntimeError("broken validator")

    monkeypatch.setattr(e2e, "JSONSchemaValidator", ExplodingValidator)

    result = e2e.validate_uri_sample({"@odata.id": "/redfish/v1/Systems/1"}, "schemas")

    assert result["result"] == "error"
    assert "broken validator" in result["error"]


def test_merge_schema_and_rule_results_adds_static_validation_details():
    result_dict = {
        "checks": {
            "schema_validation": {
                "result": "fail",
                "fail_count": 1,
                "errors": [{"type": "Property Type Error", "message": "bad field"}],
            }
        }
    }
    uri_sample = {
        "@odata.id": "/redfish/v1/Systems/1",
        "@odata.type": "#ComputerSystem.v1_0_0.ComputerSystem",
    }
    rule_check_result = {
        "result": "pass",
        "total_checks_num": 3,
        "failed_checks_num": 0,
        "error_details": {"STATIC_VALIDATION": []},
    }

    merged = e2e.merge_schema_and_rule_results(result_dict, uri_sample, rule_check_result)

    assert merged["result"] == "fail"
    assert merged["uri"] == "/redfish/v1/Systems/1"
    assert merged["resource_type"] == "#v1_0_0"
    assert merged["failed_checks_num"] == 1
    assert merged["error_details"]["STATIC_VALIDATION"][0]["message"].startswith("Property Type Error")


def test_check_single_review_point_returns_uri_generation_error(monkeypatch):
    class FakeGenerator:
        def generate(self, review_point, output_file=None):
            raise e2e.URIGenerationError("quota exceeded")

    monkeypatch.setattr(e2e, "URIGenerator", lambda: FakeGenerator())

    result = e2e.check_single_review_point(
        {"title": "rp", "content": "content"},
        schema_dir="schemas",
        output_dir="out",
        generate_uri=True,
    )

    assert result["checks"]["uri_sample"]["status"] == "error"
    assert "quota exceeded" in result["checks"]["uri_sample"]["error"]


def test_check_single_review_point_with_cached_uri_reuses_schema_result(monkeypatch):
    calls = {}

    monkeypatch.setattr(
        e2e.redfish_review_workflow_module,
        "check_all_rules",
        lambda **kwargs: {
            "result": "pass",
            "total_checks_num": 2,
            "failed_checks_num": 0,
            "error_details": {},
        },
    )

    def should_not_run(*args, **kwargs):
        calls["validate_called"] = True
        return {}

    monkeypatch.setattr(e2e, "validate_uri_sample", should_not_run)

    cached_checks = {"schema_validation": {"result": "pass", "fail_count": 0}}
    result = e2e.check_single_review_point(
        {"title": "rp", "content": "content"},
        schema_dir="schemas",
        output_dir="out",
        generate_uri=True,
        _cached_uri_sample={
            "@odata.id": "/redfish/v1/Systems/1",
            "@odata.type": "#ComputerSystem.v1_0_0.ComputerSystem",
        },
        _cached_checks=cached_checks,
    )

    assert "validate_called" not in calls
    assert result["checks"]["schema_validation"]["result"] == "pass"
    assert result["checks"]["rule_compliance"]["result"] == "pass"


def test_check_single_review_point_without_uri_generation_uses_review_point_compliance(monkeypatch):
    monkeypatch.setattr(
        e2e,
        "check_review_point_compliance",
        lambda **kwargs: {
            "overall_compliant": True,
            "total_rules": 1,
            "compliant_rules": 1,
            "failed_rules": 0,
            "warning_rules": 0,
            "error_details": {},
        },
    )

    result = e2e.check_single_review_point(
        {"title": "rp", "content": "content"},
        schema_dir="schemas",
        output_dir="out",
        generate_uri=False,
    )

    assert result["checks"]["rule_compliance"]["overall_compliant"] is True
    assert "schema_validation" not in result["checks"]


@pytest.mark.parametrize(
    ("review_point", "expected"),
    [
        ({"checks": {"uri_sample": {"status": "error"}}}, "fail"),
        ({"checks": {"schema_validation": {"result": "fail"}}}, "fail"),
        ({"checks": {"rule_compliance": {"error": "boom"}}}, "fail"),
        ({"checks": {"rule_compliance": {"result": "fail"}}}, "fail"),
        ({"checks": {"rule_compliance": {"overall_compliant": False}}}, "fail"),
        ({"checks": {"rule_compliance": {"overall_compliant": True}}}, "pass"),
    ],
)
def test_judge_review_point_overall(review_point, expected):
    assert e2e._judge_review_point_overall(review_point) == expected


def test_append_error_details_writes_all_sections():
    lines = []
    e2e._append_error_details(
        lines,
        {
            "STATIC_VALIDATION": [{"rule": "[SCHEMA-001] Schema", "message": "bad", "advice": "fix schema"}],
            "MODEL_VALIDATION": [{"rule": "[MDB-021] 属性 description 必填 (规则合规性检查)", "message": "fail", "advice": "fix rule"}],
            "WARNING_DETAILS": [{"rule": "[MDB-031] 需求背景与必要性 (规则合规性检查)", "message": "warn", "advice": "review"}],
        },
    )

    output = "\n".join(lines)
    assert "**规则ID**：SCHEMA-001" in output
    assert "**规则ID**：MDB-021" in output
    assert "**级别**：必须项" in output
    assert "**问题描述**：fail" in output
    assert "**处理建议**：fix rule" in output
    assert "**规则ID**：MDB-031" in output
    assert "**级别**：建议性" in output


def test_generate_final_result_treats_shall_per_rule_as_required():
    markdown = e2e.generate_final_result(
        {
            "title": "MDB post",
            "post_redfish_related": True,
            "results": [
                {
                    "title": "Point",
                    "content": "body",
                    "checks": {
                        "rule_compliance": {
                            "overall_compliant": False,
                            "total_rules": 1,
                            "compliant_rules": 0,
                            "failed_rules": 1,
                            "warning_rules": 0,
                            "error_details": {},
                            "per_rule_results": [
                                {
                                    "rule_id": "MDB-TEST-001",
                                    "severity": "shall",
                                    "compliant": False,
                                    "summary": "rule shall bad",
                                    "advice": "fix shall",
                                }
                            ],
                        }
                    },
                }
            ],
        }
    )

    assert "rule shall bad" in markdown
    assert "**级别**：必须项" in markdown


def test_generate_final_result_for_non_redfish_post():
    markdown = e2e.generate_final_result(
        {
            "title": "Plain post",
            "post_redfish_related": False,
            "post_redfish_reason": "not related",
        }
    )

    assert "Plain post" in markdown
    assert "not related" in markdown


def test_generate_final_result_includes_rule_and_schema_failures():
    markdown = e2e.generate_final_result(
        {
            "title": "Redfish post",
            "post_redfish_related": True,
            "post_redfish_reason": "has redfish",
            "total_review_points": 1,
            "redfish_review_points": 1,
            "non_redfish_review_points": 0,
            "results": [
                {
                    "title": "Review Point 1",
                    "checks": {
                        "uri_sample": {"status": "success"},
                        "schema_validation": {
                            "result": "fail",
                            "fail_count": 1,
                            "warn_count": 0,
                            "errors": [{"type": "Schema Error", "message": "bad schema"}],
                        },
                        "rule_compliance": {
                            "result": "fail",
                            "total_checks_num": 2,
                            "failed_checks_num": 1,
                            "error_details": {
                                "STATIC_VALIDATION": [{"rule": "Schema", "message": "bad", "advice": "fix"}]
                            },
                        },
                    },
                }
            ],
        }
    )

    assert "Redfish post" in markdown
    assert "bad schema" in markdown
    assert "Schema" in markdown


def test_process_post_returns_empty_when_no_review_points(monkeypatch):
    monkeypatch.setattr(e2e, "is_post_relevant", lambda title, content: (True, "redfish"))
    monkeypatch.setattr(e2e, "extract_all_review_points", lambda content: [])

    result = e2e.process_post("title", "content", "schemas", "out")

    assert result["total_review_points"] == 0
    assert result["final_result"] == ""


def test_process_post_returns_empty_when_no_redfish_points(monkeypatch):
    monkeypatch.setattr(e2e, "is_post_relevant", lambda title, content: (True, "redfish"))
    monkeypatch.setattr(e2e, "extract_all_review_points", lambda content: [{"title": "rp", "content": "plain"}])
    monkeypatch.setattr(e2e, "classify_review_point", lambda title, content: 'other')

    result = e2e.process_post("title", "content", "schemas", "out")

    assert result["redfish_review_points"] == 0
    assert result["final_result"] == ""


def test_process_post_retries_rule_phase_with_cached_uri(monkeypatch):
    monkeypatch.setattr(e2e.Config, "DISABLE_FILE_OUTPUT", True)
    monkeypatch.setattr(e2e.Config, "MAX_RETRY", 2)
    monkeypatch.setattr(e2e.Config, "RETRY_DELAY", 0)
    monkeypatch.setattr(
        e2e,
        "time",
        type(
            "FakeTime",
            (),
            {
                "sleep": staticmethod(lambda _: None),
                "monotonic": staticmethod(lambda: 1.0),
            },
        ),
    )
    monkeypatch.setattr(e2e, "is_post_relevant", lambda title, content: (True, "redfish"))
    monkeypatch.setattr(e2e, "extract_all_review_points", lambda content: [{"title": "rp1", "content": "c1"}])
    monkeypatch.setattr(e2e, "classify_review_point", lambda title, content: 'redfish')
    monkeypatch.setattr(e2e, "generate_final_result", lambda result: "final")

    calls = []

    def fake_check_single_review_point(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return {
                "_uri_sample": {"@odata.id": "/redfish/v1/Systems/1"},
                "checks": {
                    "schema_validation": {"result": "pass"},
                    "rule_compliance": {
                        "error_details": {"MODEL_VALIDATION": [{"message": "empty response"}], "WARNING_DETAILS": []}
                    },
                },
            }
        return {
            "checks": {
                "schema_validation": {"result": "pass"},
                "rule_compliance": {"result": "pass", "failed_checks_num": 0, "error_details": {}},
            }
        }

    monkeypatch.setattr(e2e, "check_single_review_point", fake_check_single_review_point)

    result = e2e.process_post("title", "content", "schemas", "out")

    assert result["final_result"] == "final"
    assert len(calls) == 2
    assert calls[1]["_cached_uri_sample"] == {"@odata.id": "/redfish/v1/Systems/1"}
    assert "rule_compliance" not in calls[1]["_cached_checks"]


def test_process_post_aborts_without_rendering_rule_timeouts(monkeypatch):
    monkeypatch.setattr(e2e.Config, "DISABLE_FILE_OUTPUT", True)
    monkeypatch.setattr(e2e.Config, "MAX_RETRY", 2)
    monkeypatch.setattr(e2e.Config, "RETRY_DELAY", 0)
    monkeypatch.setattr(
        e2e,
        "time",
        type(
            "FakeTime",
            (),
            {
                "sleep": staticmethod(lambda _: None),
                "monotonic": staticmethod(lambda: 1.0),
            },
        ),
    )
    monkeypatch.setattr(e2e, "is_post_relevant", lambda title, content: (True, "redfish"))
    monkeypatch.setattr(e2e, "extract_all_review_points", lambda content: [{"title": "新增资源协作接口", "content": "c1"}])
    monkeypatch.setattr(e2e, "classify_review_point", lambda title, content: "redfish")

    calls = []

    def fake_check_single_review_point(*args, **kwargs):
        calls.append(kwargs)
        return {
            "_uri_sample": {"@odata.id": "/redfish/v1/Systems/1"},
            "checks": {
                "uri_sample": {"status": "success"},
                "schema_validation": {"result": "skip"},
                "rule_compliance": {
                    "result": "fail",
                    "error_details": {
                        "MODEL_VALIDATION": [
                            {"rule": "RULE-001", "message": "普通规则失败"},
                            {"rule": "RULE-004", "message": "检查失败: Request timed out."},
                        ],
                        "WARNING_DETAILS": [
                            {"rule": "RULE-002", "message": "检查失败: Request timed out."}
                        ],
                    },
                },
            },
        }

    monkeypatch.setattr(e2e, "check_single_review_point", fake_check_single_review_point)
    monkeypatch.setattr(e2e, "generate_final_result", lambda result: "should not render")

    result = e2e.process_post("title", "content", "schemas", "out")

    assert len(calls) == 2
    assert result["final_result"].startswith("处理失败:")
    assert "Request timed out" not in result["final_result"]
    assert result["final_result"] != "should not render"


def test_run_schema_check_returns_error_string_on_exception(monkeypatch):
    monkeypatch.setattr(e2e.Config, "init_directories", lambda: None)
    monkeypatch.setattr(e2e.Config, "SCHEMA_DIR", "schemas")
    monkeypatch.setattr(e2e.Config, "OUTPUT_DIR", "out")
    monkeypatch.setattr(e2e, "process_post", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    result = e2e.run_schema_check("title", "content", "123")

    assert "boom" in result


def test_validate_uri_sample_maps_skip_fail_and_error_results(monkeypatch):
    class FakeValidator:
        def __init__(self, schema_dir, no_oem=False):
            self.pass_count = 1
            self.warn_count = 2
            self.fail_count = 3
            self.skip_count = 4
            self.errors = [{"type": "Schema Error", "message": "bad"}]
            self.warnings = [{"type": "Schema Warning", "message": "warn"}]
            self.schema_check_meta = {"entry_schema_path_relative": "dmtf/Service.json"}

        def validate(self, uri, payload):
            from redfish_common import ValidationResult

            result = ValidationResult()
            result.result = payload["expected_result"]
            return result

    monkeypatch.setattr(e2e, "JSONSchemaValidator", FakeValidator)

    skip_result = e2e.validate_uri_sample({"@odata.id": "/r", "expected_result": "skip"}, "schemas")
    fail_result = e2e.validate_uri_sample({"@odata.id": "/r", "expected_result": "fail"}, "schemas")

    assert skip_result["result"] == "skip"
    assert fail_result["result"] == "fail"
    assert fail_result["schema_check"]["entry_schema_path_relative"] == "dmtf/Service.json"

    class ExplodingValidator:
        def __init__(self, schema_dir, no_oem=False):
            raise RuntimeError("validator init failed")

    monkeypatch.setattr(e2e, "JSONSchemaValidator", ExplodingValidator)
    error_result = e2e.validate_uri_sample({"@odata.id": "/r"}, "schemas")

    assert error_result["result"] == "error"
    assert "validator init failed" in error_result["error"]


def test_merge_schema_and_rule_results_adds_skip_warnings_and_meta():
    merged = e2e.merge_schema_and_rule_results(
        {
            "checks": {
                "schema_validation": {
                    "result": "skip",
                    "warnings": [{"message": "definition missing"}],
                    "schema_check": {"validated_sources": ["dmtf"]},
                }
            }
        },
        {
            "@odata.id": "/redfish/v1/Systems/1",
            "@odata.type": "#ComputerSystem.v1_0_0.ComputerSystem",
        },
        {
            "result": "pass",
            "total_checks_num": 2,
            "failed_checks_num": 0,
            "error_details": {"STATIC_VALIDATION": [], "WARNING_DETAILS": []},
        },
    )

    assert merged["result"] == "pass"
    assert merged["total_checks_num"] == 3
    assert merged["schema_check"] == {"validated_sources": ["dmtf"]}
    assert merged["error_details"]["WARNING_DETAILS"][0]["message"] == "definition missing"


def test_append_schema_meta_handles_definition_label_without_path():
    lines = []
    e2e._append_schema_meta(
        lines,
        {
            "dmtf_schema_found": True,
            "oem_schema_found": False,
            "validated_sources": ["dmtf"],
            "entry_schema_path_relative": "dmtf/Service.json",
            "entry_schema_category_label_zh": "DMTF",
            "definition_schema_category_label_zh": "remote schema",
        },
        "summary text",
    )

    output = "\n".join(lines)
    assert "dmtf/Service.json" in output
    assert "remote schema" in output
    assert "summary text" in output


def test_generate_final_result_covers_schema_pass_skip_and_error_paths():
    markdown = e2e.generate_final_result(
        {
            "title": "Schema rich post",
            "post_redfish_related": True,
            "post_redfish_reason": "matched",
            "total_review_points": 3,
            "redfish_review_points": 3,
            "non_redfish_review_points": 0,
            "results": [
                {
                    "title": "Review Point 1",
                    "checks": {
                        "uri_sample": {"status": "success"},
                        "schema_validation": {
                            "result": "pass",
                            "pass_count": 2,
                            "warn_count": 1,
                            "warnings": [{"type": "Schema Warning", "message": "oem missing"}],
                            "schema_check": {
                                "dmtf_schema_found": True,
                                "oem_schema_found": False,
                                "validated_sources": ["dmtf"],
                                "entry_schema_path_relative": "dmtf/Service.json",
                                "entry_schema_category_label_zh": "DMTF",
                                "validation_summary_zh": "pass summary",
                            },
                        },
                        "rule_compliance": {
                            "result": "pass",
                            "total_checks_num": 2,
                            "failed_checks_num": 0,
                            "error_details": {},
                        },
                    },
                },
                {
                    "title": "Review Point 2",
                    "checks": {
                        "uri_sample": {"status": "success"},
                        "schema_validation": {
                            "result": "skip",
                            "warnings": [{"type": "Schema Skip", "message": "pointer unresolved"}],
                            "schema_check": {
                                "definition_schema_category_label_zh": "remote schema",
                                "validation_summary_zh": "skip summary",
                            },
                        },
                        "rule_compliance": {
                            "overall_compliant": True,
                            "total_rules": 2,
                            "compliant_rules": 2,
                            "failed_rules": 0,
                            "warning_rules": 0,
                            "error_details": {},
                        },
                    },
                },
                {
                    "title": "Review Point 3",
                    "checks": {
                        "uri_sample": {"status": "success"},
                        "schema_validation": {
                            "result": "error",
                            "error": "schema loader failed",
                            "errors": [{"type": "Schema Error", "message": "bad schema"}],
                            "warnings": [{"type": "Schema Warning", "message": "warn schema"}],
                            "schema_check": {
                                "validation_summary_zh": "error summary",
                            },
                        },
                        "rule_compliance": {
                            "result": "fail",
                            "total_checks_num": 2,
                            "failed_checks_num": 1,
                            "error_details": {
                                "STATIC_VALIDATION": [{"rule": "Schema", "message": "static bad", "advice": "fix static"}],
                                "MODEL_VALIDATION": [{"rule": "RULE-001", "message": "rule bad", "advice": "fix rule"}],
                                "WARNING_DETAILS": [{"rule": "RULE-002", "message": "rule warn", "advice": "review rule"}],
                            },
                        },
                    },
                },
            ],
        }
    )

    assert "Schema rich post" in markdown
    assert "oem missing" in markdown
    assert "pointer unresolved" in markdown
    assert "schema loader failed" in markdown
    assert "static bad" in markdown
    assert "rule bad" in markdown
    assert "rule warn" in markdown
