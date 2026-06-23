import json

import pytest

from src.ForumBot.SchemaValidation import redfish_checker


RULES = [
    {"id": "RULE-001", "category": "Naming", "rule": "must be correct", "severity": "must"},
    {"id": "RULE-002", "category": "Type", "rule": "must be typed", "severity": "must"},
]


def test_parse_batch_check_result_from_markdown_json():
    response = """
    ```json
    [
      {"rule_id": "RULE-001", "category": "Naming", "rule": "must be correct", "severity": "must", "compliant": true, "summary": "ok", "advice": null},
      {"rule_id": "RULE-002", "category": "Type", "rule": "must be typed", "severity": "must", "compliant": false, "summary": "bad", "advice": "fix"}
    ]
    ```
    """

    result = redfish_checker.parse_batch_check_result(response, RULES)

    assert len(result) == 2
    assert result[0]["rule_id"] == "RULE-001"
    assert result[0]["compliant"] is True
    assert result[1]["compliant"] is False


def test_parse_batch_check_result_invalid_json_returns_error_results():
    result = redfish_checker.parse_batch_check_result("not-json", RULES)

    assert len(result) == 2
    assert all("error" in item for item in result)
    assert result[0]["rule_id"] == "RULE-001"


def test_validate_and_fix_results_adds_missing_rule_result():
    partial = [
        {
            "rule_id": "RULE-001",
            "category": "Naming",
            "rule": "must be correct",
            "severity": "must",
            "compliant": True,
            "summary": "符合规范",
            "advice": None,
        }
    ]

    result = redfish_checker.validate_and_fix_results(partial, RULES)

    assert len(result) == 2
    missing = next(item for item in result if item["rule_id"] == "RULE-002")
    assert missing["compliant"] is False
    assert missing["error"] == "Rule result missing from LLM output"


def test_extract_top_level_json_array_handles_nested_content():
    text = 'prefix [{"rule_id":"RULE-001","findings":["[ok]"],"summary":"done"}] suffix'

    extracted = redfish_checker.extract_top_level_json_array(text)

    assert extracted == '[{"rule_id":"RULE-001","findings":["[ok]"],"summary":"done"}]'


def test_repair_json_text_removes_trailing_commas_and_smart_quotes():
    repaired = redfish_checker.repair_json_text('{\u201cname\u201d: "value",}')

    assert repaired == '{"name": "value"}'


def test_extract_markdown_json_fence_supports_uppercase():
    text = "```JSON\n[{\"rule_id\": \"RULE-001\"}]\n```"

    assert redfish_checker.extract_markdown_json_fence(text) == '[{"rule_id": "RULE-001"}]'


def test_parse_batch_check_result_empty_response_returns_errors():
    result = redfish_checker.parse_batch_check_result("", RULES)

    assert [item["error"] for item in result] == ["Empty response", "Empty response"]


def test_validate_and_fix_results_normalizes_result_fields():
    result = redfish_checker.validate_and_fix_results(
        [
            {
                "rule_id": "RULE-001",
                "rule_category": "Naming",
                "rule_description": "must be correct",
                "severity": "must",
                "compliant": False,
                "summary": "needs review",
                "advice": None,
                "findings": ["issue"],
            },
            {
                "rule_id": "RULE-002",
                "category": "Type",
                "rule": "must be typed",
                "severity": "must",
                "compliant": True,
                "summary": "ok",
                "advice": None,
            },
        ],
        RULES,
    )

    assert result[0]["category"] == "Naming"
    assert result[0]["rule"] == "must be correct"
    assert result[0]["findings"] == ["issue"]


def test_check_all_rules_batch_delegates_to_review_point_compliance(monkeypatch):
    monkeypatch.setattr(
        redfish_checker,
        "check_review_point_compliance",
        lambda rules, review_point_title, review_point_content, model, save_result: {
            "delegated": True,
            "title": review_point_title,
        },
    )

    result = redfish_checker.check_all_rules_batch(
        RULES,
        uri="/redfish/v1/Systems/1",
        payload={},
        review_point_title="rp",
        review_point_content="content",
    )

    assert result == {"delegated": True, "title": "rp"}


def test_check_all_rules_batch_returns_fail_summary_when_llm_raises(monkeypatch):
    monkeypatch.setattr(redfish_checker, "create_llm", lambda model=None, temperature=0.1: (_ for _ in ()).throw(RuntimeError("quota exceeded")))
    monkeypatch.setattr(redfish_checker.time, "sleep", lambda _: None)

    result = redfish_checker.check_all_rules_batch(
        RULES,
        uri="/redfish/v1/Systems/1",
        payload={"@odata.type": "#ComputerSystem.v1_0_0.ComputerSystem"},
        save_result=False,
    )

    assert result["result"] == "fail"
    assert result["failed_checks_num"] == len(RULES)
    assert len(result["error_details"]["MODEL_VALIDATION"]) == len(RULES)
    assert result["error_details"]["MODEL_VALIDATION"][0]["message"].startswith("检查失败")


def test_check_review_point_compliance_success_and_save(monkeypatch, tmp_path):
    class FakeLLM:
        def invoke(self, prompt):
            return type(
                "Response",
                (),
                {
                    "content": json.dumps(
                        [
                            {
                                "rule_id": "RULE-001",
                                "category": "Naming",
                                "rule": "must be correct",
                                "severity": "must",
                                "compliant": True,
                                "summary": "ok",
                                "advice": None,
                            },
                            {
                                "rule_id": "RULE-002",
                                "category": "Type",
                                "rule": "must be typed",
                                "severity": "must",
                                "compliant": True,
                                "summary": "ok too",
                                "advice": None,
                            },
                        ]
                    )
                },
            )()

    monkeypatch.setattr(redfish_checker, "create_llm", lambda model=None, temperature=0.1: FakeLLM())
    monkeypatch.setattr(redfish_checker.time, "sleep", lambda _: None)
    monkeypatch.chdir(tmp_path)

    result = redfish_checker.check_review_point_compliance(
        RULES,
        review_point_title="Review/Point",
        review_point_content="Body",
        save_result=True,
    )

    assert result["result"] == "pass"
    assert result["overall_compliant"] is True
    assert list(tmp_path.glob("review_point_check_result_*.json"))


def test_check_review_point_compliance_handles_llm_exception(monkeypatch):
    monkeypatch.setattr(redfish_checker, "create_llm", lambda model=None, temperature=0.1: (_ for _ in ()).throw(RuntimeError("timeout")))
    monkeypatch.setattr(redfish_checker.time, "sleep", lambda _: None)

    result = redfish_checker.check_review_point_compliance(
        RULES,
        review_point_title="Title",
        review_point_content="Body",
        save_result=False,
    )

    assert result["result"] == "fail"
    assert result["failed_rules"] == len(RULES)
    assert len(result["error_details"]["MODEL_VALIDATION"]) == len(RULES)


@pytest.mark.parametrize(
    ("payload", "error_type"),
    [
        (None, FileNotFoundError),
        ({}, ValueError),
        ([{"id": "RULE-001", "rule": "x", "check": "y"}, "bad-item"], ValueError),
        ([{"id": "RULE-001", "rule": "x"}], ValueError),
        (
            [
                {"id": "RULE-001", "rule": "x", "check": "y"},
                {"id": "RULE-001", "rule": "z", "check": "w"},
            ],
            ValueError,
        ),
    ],
)
def test_load_compliance_rules_validation_errors(tmp_path, payload, error_type):
    rules_path = tmp_path / "rules.json"
    if payload is not None:
        rules_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(error_type):
        redfish_checker._load_compliance_rules(rules_path)


def test_static_postcheck_rule001_marks_multiple_text_issues():
    results = [
        {
            "rule_id": "RULE-001",
            "category": "Naming",
            "rule": "must be correct",
            "severity": "must",
            "compliant": True,
            "summary": "ok",
            "advice": None,
            "findings": [],
        }
    ]
    review_point_title = "Action Reset uses bool"
    review_point_content = "\n".join(
        [
            "| Name | Type |",
            "| Test | bool |",
            "@data.id should be @odata.id",
            "Action Demo Reset",
            "/Actions/Demo.Reset",
            "/redfish/v1/systems/{id}{id}/Memorys",
            "NetworkAdapterse should be fixed",
            "CompStatus and ComponentStatus are mixed",
            "/redfish/v1/Chassis/1/Temperature",
        ]
    )

    updated = redfish_checker.static_postcheck_rule001(results, review_point_title, review_point_content)

    assert updated[0]["compliant"] is False
    assert len(updated[0]["findings"]) >= 6
    assert "Memorys" in updated[0]["summary"]
    assert updated[0]["advice"]


def test_static_postcheck_rule001_returns_original_when_no_extra_findings():
    results = [
        {
            "rule_id": "RULE-001",
            "category": "Naming",
            "rule": "must be correct",
            "severity": "must",
            "compliant": True,
            "summary": "ok",
            "advice": None,
            "findings": [],
        }
    ]

    updated = redfish_checker.static_postcheck_rule001(results, "Clean title", "No rule issue here.")

    assert updated == results


def test_create_error_result_preserves_rule_metadata():
    error_result = redfish_checker.create_error_result(RULES[0], "boom")

    assert error_result["rule_id"] == "RULE-001"
    assert error_result["error"] == "boom"
    assert error_result["compliant"] is False
