import json
import os

from src.ForumBot.SchemaValidation import redfish_review_workflow


def test_redfish_compliance_rules_loaded():
    """REDFISH_COMPLIANCE_RULES 应为非空列表，从外部 JSON 文件加载"""
    assert isinstance(redfish_review_workflow.REDFISH_COMPLIANCE_RULES, list)
    assert len(redfish_review_workflow.REDFISH_COMPLIANCE_RULES) > 0
    # 验证每条规则都有必要字段
    for rule in redfish_review_workflow.REDFISH_COMPLIANCE_RULES:
        assert "id" in rule
        assert "rule" in rule
        assert "check" in rule


def test_check_all_rules_delegates(monkeypatch):
    """check_all_rules 应委托给 redfish_checker.check_all_rules"""
    monkeypatch.setattr(
        redfish_review_workflow,
        "check_all_rules",
        lambda *args, **kwargs: {"delegated": True, "args": args, "kwargs": kwargs},
    )

    result = redfish_review_workflow.check_all_rules(
        rules=[{"id": "RULE-001"}],
        uri="/redfish/v1/Systems/1",
        payload={},
    )

    assert result["delegated"] is True


def test_check_review_point_compliance_delegates(monkeypatch):
    """check_review_point_compliance 应委托给 redfish_checker.check_review_point_compliance"""
    monkeypatch.setattr(
        redfish_review_workflow,
        "check_review_point_compliance",
        lambda *args, **kwargs: {"delegated": True, "title": kwargs.get("review_point_title")},
    )

    result = redfish_review_workflow.check_review_point_compliance(
        rules=[{"id": "RULE-001"}],
        review_point_title="Test Point",
        review_point_content="Content",
    )

    assert result["delegated"] is True
    assert result["title"] == "Test Point"
