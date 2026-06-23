"""MDB 集成测试：测试 end_to_end_check.py 中的 MDB 分类编排逻辑。"""
import pytest
from unittest.mock import patch, MagicMock

from src.ForumBot.SchemaValidation.end_to_end_check import (
    is_post_relevant,
    classify_review_point,
    check_mdb_review_point,
    generate_final_result,
    process_post,
)


# ==================== is_post_relevant ====================


class TestIsPostRelevant:
    def test_mdb_post(self):
        is_rel, reason = is_post_relevant(
            "新增资源协作接口",
            "接口路径 bmc.kepler.xxx.yyy"
        )
        assert is_rel is True
        assert "MDB" in reason

    def test_redfish_post(self):
        is_rel, reason = is_post_relevant(
            "Redfish接口设计",
            "使用redfish API获取数据"
        )
        assert is_rel is True
        assert "Redfish" in reason

    def test_unrelated_post(self):
        is_rel, reason = is_post_relevant(
            "普通帖子",
            "与接口无关的内容"
        )
        assert is_rel is False

    def test_mdb_takes_priority(self):
        """MDB 和 Redfish 都相关时，MDB 优先返回。"""
        is_rel, reason = is_post_relevant(
            "新增资源协作接口",
            "接口路径 bmc.kepler.xxx.yyy"
        )
        assert is_rel is True


# ==================== classify_review_point ====================


class TestClassifyReviewPoint:
    def test_mdb_point(self):
        cat = classify_review_point(
            "新增资源协作接口属性",
            "路径 bmc.kepler.xxx.yyy.zzz"
        )
        assert cat == 'mdb'

    def test_redfish_point(self):
        cat = classify_review_point(
            "Redfish接口新增属性",
            "使用 redfish API"
        )
        assert cat == 'redfish'

    def test_other_point(self):
        cat = classify_review_point(
            "普通标题",
            "普通内容"
        )
        assert cat == 'other'


# ==================== check_mdb_review_point ====================


class TestCheckMdbReviewPoint:
    @patch('src.ForumBot.SchemaValidation.end_to_end_check.MdbComplianceChecker')
    def test_successful_check(self, MockChecker):
        mock_instance = MagicMock()
        mock_instance.check_review_point.return_value = {
            "total_rules": 44,
            "compliant_rules": 44,
            "failed_rules": 0,
            "warning_rules": 0,
            "overall_compliant": True,
            "compliance_rate": "100.0%",
            "result": "pass",
            "error_details": {"MODEL_VALIDATION": [], "WARNING_DETAILS": [], "STATIC_VALIDATION": []},
        }
        MockChecker.return_value = mock_instance

        result = check_mdb_review_point(
            {"title": "测试评审点", "content": "测试内容"},
            {"schema_validation": {"model": "test", "api_key": "key"}}
        )
        assert result["mdb_related"] is True
        assert result["checks"]["rule_compliance"]["overall_compliant"] is True

    def test_mdb_module_not_available(self):
        """当 MdbComplianceChecker 为 None 时应优雅降级。"""
        with patch('src.ForumBot.SchemaValidation.end_to_end_check.MdbComplianceChecker', None):
            result = check_mdb_review_point(
                {"title": "测试", "content": "内容"},
                {}
            )
            assert "error" in result["checks"]["rule_compliance"]

    @patch('src.ForumBot.SchemaValidation.end_to_end_check.MdbComplianceChecker')
    def test_exception_during_check(self, MockChecker):
        MockChecker.side_effect = Exception("连接超时")
        result = check_mdb_review_point(
            {"title": "测试", "content": "内容"},
            {}
        )
        assert "error" in result["checks"]["rule_compliance"]


# ==================== generate_final_result ====================


class TestGenerateFinalResult:
    def test_unrelated_post(self):
        result = {
            "title": "测试",
            "post_redfish_related": False,
            "post_redfish_reason": "无关",
        }
        md = generate_final_result(result)
        assert "无关" in md
        assert "进一步检查" in md

    def test_mdb_and_redfish_mixed(self):
        """测试 MDB 和 Redfish 混合评审点的报告生成。"""
        result = {
            "title": "混合帖子",
            "post_redfish_related": True,
            "post_redfish_reason": "MDB 相关",
            "total_review_points": 3,
            "mdb_review_points": 1,
            "redfish_review_points": 1,
            "non_redfish_review_points": 1,
            "results": [
                {
                    "title": "新增资源协作属性",
                    "category": "mdb",
                    "checks": {
                        "rule_compliance": {
                            "overall_compliant": True,
                            "total_rules": 44,
                            "compliant_rules": 44,
                            "failed_rules": 0,
                            "warning_rules": 0,
                            "compliance_rate": "100.0%",
                            "result": "pass",
                            "error_details": {},
                        }
                    },
                },
                {
                    "title": "Redfish接口设计",
                    "category": "redfish",
                    "checks": {
                        "uri_sample": {"status": "success"},
                        "schema_validation": {"result": "pass", "pass_count": 1, "warn_count": 0, "schema_check": {}},
                        "rule_compliance": {
                            "result": "pass",
                            "total_checks_num": 14,
                            "failed_checks_num": 0,
                            "error_details": {},
                        }
                    },
                },
            ],
        }
        md = generate_final_result(result)
        assert "MDB" in md
        assert "Redfish" in md
        assert "评审点 1" in md
        assert "评审点 2" in md
        assert "通过" in md

    def test_failed_mdb_point(self):
        """测试 MDB 评审点不通过时的报告。"""
        result = {
            "title": "测试",
            "post_redfish_related": True,
            "post_redfish_reason": "MDB 相关",
            "total_review_points": 1,
            "mdb_review_points": 1,
            "redfish_review_points": 0,
            "non_redfish_review_points": 0,
            "results": [
                {
                    "title": "新增资源协作属性",
                    "category": "mdb",
                    "checks": {
                        "rule_compliance": {
                            "overall_compliant": False,
                            "total_rules": 44,
                            "compliant_rules": 40,
                            "failed_rules": 4,
                            "warning_rules": 0,
                            "compliance_rate": "90.9%",
                            "result": "fail",
                            "error_details": {
                                "MODEL_VALIDATION": [
                                    {"rule": "[MDB-005] 属性表结构", "message": "属性表缺少列", "advice": "补充属性表列"}
                                ],
                                "WARNING_DETAILS": [],
                                "STATIC_VALIDATION": [],
                            },
                        }
                    },
                },
            ],
        }
        md = generate_final_result(result)
        assert "不通过" in md
        assert "MDB-005" in md


# ==================== process_post 集成 ====================


class TestProcessPostIntegration:
    @patch('src.ForumBot.SchemaValidation.end_to_end_check.check_mdb_review_point')
    @patch('src.ForumBot.SchemaValidation.end_to_end_check.classify_review_point')
    @patch('src.ForumBot.SchemaValidation.end_to_end_check.extract_all_review_points')
    def test_mdb_only_post(self, mock_extract, mock_classify, mock_check_mdb):
        """帖子只含 MDB 评审点。"""
        mock_extract.return_value = [
            {"title": "新增资源协作属性", "content": "bmc.kepler.xxx.yyy"}
        ]
        mock_classify.return_value = 'mdb'
        mock_check_mdb.return_value = {
            "title": "新增资源协作属性",
            "checks": {
                "rule_compliance": {
                    "overall_compliant": True,
                    "total_rules": 44,
                    "compliant_rules": 44,
                    "failed_rules": 0,
                    "warning_rules": 0,
                    "result": "pass",
                    "error_details": {},
                }
            },
            "mdb_related": True,
        }

        result = process_post(
            title="资源协作帖子",
            content="内容",
            schema_dir="/tmp/schema",
            output_dir="/tmp/output",
            generate_uri=False,
            config={"schema_validation": {"model": "test"}},
        )
        assert result["total_review_points"] == 1
        assert result["mdb_review_points"] == 1
        assert result["redfish_review_points"] == 0
        assert len(result["results"]) == 1
        assert result["results"][0]["category"] == "mdb"

    @patch('src.ForumBot.SchemaValidation.end_to_end_check.classify_review_point')
    @patch('src.ForumBot.SchemaValidation.end_to_end_check.extract_all_review_points')
    def test_unrelated_post(self, mock_extract, mock_classify):
        """帖子与 Redfish/MDB 均无关。"""
        mock_extract.return_value = []

        result = process_post(
            title="普通帖子",
            content="普通内容",
            schema_dir="/tmp/schema",
            output_dir="/tmp/output",
            generate_uri=False,
            config={},
        )
        assert result["post_redfish_related"] is False

    @patch('src.ForumBot.SchemaValidation.end_to_end_check.is_post_relevant')
    @patch('src.ForumBot.SchemaValidation.end_to_end_check.check_mdb_review_point')
    @patch('src.ForumBot.SchemaValidation.end_to_end_check.classify_review_point')
    @patch('src.ForumBot.SchemaValidation.end_to_end_check.extract_all_review_points')
    def test_mixed_post_preserves_order(self, mock_extract, mock_classify, mock_check_mdb, mock_relevant):
        """混合帖子保持评审点原始顺序。"""
        mock_relevant.return_value = (True, "MDB + Redfish 相关")
        mock_extract.return_value = [
            {"title": "MDB评审点", "content": "mdb内容"},
            {"title": "Redfish评审点", "content": "redfish内容"},
            {"title": "另一个MDB评审点", "content": "mdb内容2"},
        ]
        mock_classify.side_effect = ['mdb', 'redfish', 'mdb']
        mock_check_mdb.return_value = {
            "title": "MDB",
            "checks": {"rule_compliance": {"overall_compliant": True, "result": "pass", "error_details": {}, "total_rules": 44, "compliant_rules": 44, "failed_rules": 0, "warning_rules": 0}},
            "mdb_related": True,
        }

        with patch('src.ForumBot.SchemaValidation.end_to_end_check.check_single_review_point') as mock_check_rf:
            mock_check_rf.return_value = {
                "title": "Redfish",
                "checks": {"rule_compliance": {"result": "pass", "total_checks_num": 14, "failed_checks_num": 0, "error_details": {}}},
                "redfish_related": True,
            }

            result = process_post(
                title="混合帖子",
                content="内容",
                schema_dir="/tmp/schema",
                output_dir="/tmp/output",
                generate_uri=False,
                config={"schema_validation": {"model": "test"}},
            )

        assert len(result["results"]) == 3
        assert result["results"][0]["category"] == "mdb"
        assert result["results"][1]["category"] == "redfish"
        assert result["results"][2]["category"] == "mdb"
