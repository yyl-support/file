from unittest.mock import Mock

import pytest

from src.ForumBot import data_processor as data_processor_module
from src.ForumBot.data_processor import DataProcessor, fetch_all_forum_topics, parse_pre_audit_readiness


@pytest.fixture
def config():
    return {
        "api": {"base_url": "https://api.example.com", "api_key": "dummy-key"},
        "image_processing": {"model1": "model-a", "model2": "model-b", "model3": "model-c", "base_url": "https://images.example.com"},
        "database": {"host": "localhost", "port": 5432, "database": "forum", "user": "tester", "password": "secret", "sslmode": "disable"},
        "pre_audit": {"readiness_field": "是否准备好AI预审（必选）", "readiness_yes_value": "是"},
    }


def test_parse_pre_audit_readiness_from_table(config):
    html = "<table><tr><td>是否准备好AI预审（必选）</td><td>是</td></tr></table>"
    assert parse_pre_audit_readiness(html, config) is True


def test_parse_pre_audit_readiness_from_heading_template(config):
    html = """
<h2>是否准备好AI预审</h2>
<p><em><code>（必选）是/否</code></em><br>
是</p>
"""
    assert parse_pre_audit_readiness(html, config) is True


def test_parse_pre_audit_readiness_heading_stops_at_next_heading(config):
    readiness_field = config["pre_audit"]["readiness_field"]
    html = """
<h2>{readiness_field}</h2>
<h2>Other field</h2>
<p>鏄?/p>
""".format(readiness_field=readiness_field)
    assert parse_pre_audit_readiness(html, config) is None


def test_parse_pre_audit_readiness_heading_ignores_unknown_value(config):
    readiness_field = config["pre_audit"]["readiness_field"]
    html = """
<h2>{readiness_field}</h2>
<p>unknown</p>
""".format(readiness_field=readiness_field)
    assert parse_pre_audit_readiness(html, config) is None


def test_load_pre_audit_existing_data_returns_id_map(config, monkeypatch):
    processor, cursor, conn, close_mock = DataProcessor(config), Mock(), Mock(), Mock()
    cursor.fetchall.return_value = [(101,), (202,)]
    conn.cursor.return_value = cursor
    monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
    monkeypatch.setattr(processor, "_close_db_connection", close_mock)
    assert processor.load_pre_audit_existing_data() == {101: True, 202: True}
    cursor.execute.assert_called_once_with("SELECT id FROM pre_audit_topics")
    close_mock.assert_called_once_with(conn)


def test_append_to_db_accepts_pre_audit_table(config, monkeypatch):
    processor, cursor, conn, captured = DataProcessor(config), Mock(), Mock(), {}
    cursor.execute = Mock(side_effect=lambda query, *args: captured.update(query=query, args=args) if "INSERT" in query else None)
    conn.cursor.return_value = cursor
    monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
    monkeypatch.setattr(processor, "_close_db_connection", lambda connection: None)
    payload = [{"id": 1, "title": "topic", "user_question": "question", "best_answer": "answer", "tags": [{"name": "pre-audit"}], "replies": [{"id": 2}], "created_at": "2026-04-16T00:00:00Z", "llm_answer": "done", "summary_question": "summary"}]
    assert processor.append_to_db(payload, "pre_audit_topics") is True
    assert "INSERT INTO pre_audit_topics" in captured.get("query", "")
    conn.commit.assert_called_once()


def test_append_to_db_rejects_invalid_table(config):
    with pytest.raises(ValueError, match="Invalid table name"):
        DataProcessor(config).append_to_db([{"id": 1}], "bad_table")


@pytest.mark.parametrize(("html", "expected"), [("", None), ("<div>是否准备好AI预审：是</div>", True), ("<div>nothing relevant</div>", None)])
def test_parse_pre_audit_readiness_extra_cases(config, html, expected):
    assert parse_pre_audit_readiness(html, config) is expected


def test_parse_pre_audit_readiness_returns_none_on_parser_error(config, monkeypatch):
    monkeypatch.setattr(data_processor_module, "BeautifulSoup", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    assert parse_pre_audit_readiness("<div>ignored</div>", config) is None


def test_fetch_all_forum_topics_uses_custom_pre_audit_keys(monkeypatch):
    config = {"forum": {"base_url": "https://forum.example.com", "verify_ssl": False, "request_delay": 0}, "monitor": {"pre_audit_tag": ["pre-audit"], "pre_audit_cutoff_date": "2026-01-01", "pre_audit_category_path": ["/c/pre-audit"]}}
    responses, urls = [{"topic_list": {"topics": [{"id": 1, "tags": ["pre-audit"], "created_at": "2026-04-16T00:00:00.000Z"}, {"id": 2, "tags": ["general"], "created_at": "2026-04-16T00:00:00.000Z"}]}}, {"topic_list": {"topics": []}}], []

    class FakeResponse:
        def __init__(self, payload): self._payload = payload
        def raise_for_status(self): return None
        def json(self): return self._payload

    monkeypatch.setattr(data_processor_module.requests, "get", lambda url, **kwargs: (urls.append(url), FakeResponse(responses.pop(0)))[1])
    monkeypatch.setattr(data_processor_module.time, "sleep", lambda _: None)
    result = fetch_all_forum_topics(config, tag_key="pre_audit_tag", cutoff_date_key="pre_audit_cutoff_date", category_path_key="pre_audit_category_path")
    assert [topic["id"] for topic in result] == [1]
    assert urls[0].endswith("/c/pre-audit.json")


def test_create_tables_creates_pre_audit_tables(config, monkeypatch):
    processor, cursor, conn = DataProcessor(config), Mock(), Mock()
    conn.cursor.return_value = cursor
    monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
    monkeypatch.setattr(processor, "_close_db_connection", lambda connection: None)
    processor.create_tables()
    executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
    assert "CREATE TABLE IF NOT EXISTS pre_audit_topics" in executed_sql
    assert "CREATE TABLE IF NOT EXISTS pre_audit_processed_topics" in executed_sql


def test_process_html_content_preserves_tables_as_gfm_markdown():
    html = """
<p>评审点1：新增资源协作接口属性RevisionId</p>
<table>
  <tr><th>属性名称</th><th>签名</th><th>只读</th><th>变化通知</th><th>属性描述</th><th>访问权限</th></tr>
  <tr><td>RevisionId</td><td>y</td><td>true</td><td>true</td><td>PCIe功能的RevisionId，默认值：空</td><td>R：ReadOnly</td></tr>
</table>
"""

    text = data_processor_module.process_html_content_with_image_links(html)

    assert "| 属性名称 | 签名 | 只读 | 变化通知 | 属性描述 | 访问权限 |" in text
    assert "| --- | --- | --- | --- | --- | --- |" in text
    assert "| RevisionId | y | true | true | PCIe功能的RevisionId，默认值：空 | R：ReadOnly |" in text


def test_process_html_content_preserves_heading_markers():
    html = """
<h2>背景</h2>
<p>支持电源异常状态指示</p>
<h2>评审点：变更资源协作接口 bmc.kepler.Systems.PowerMgmt.OnePower.Status</h2>
<p><strong>变更描述</strong><br>接口承载电源状态信息</p>
<h3>变更属性</h3>
<table>
  <tr><th>属性名称</th><th>签名</th><th>只读</th></tr>
  <tr><td>PowerAbnormal</td><td>u</td><td>true</td></tr>
</table>
<h2>是否准备好AI预审</h2>
<p>是</p>
"""

    text = data_processor_module.process_html_content_with_image_links(html)

    # h2 标题应保留 ## 标记
    assert "## 背景" in text
    assert "## 评审点：变更资源协作接口" in text
    # h3 标题应保留 ### 标记
    assert "### 变更属性" in text
    # 粗体应保留 ** 标记
    assert "**变更描述**" in text
    # 表格应仍为 GFM 格式
    assert "| 属性名称 | 签名 | 只读 |" in text
    assert "| PowerAbnormal | u | true |" in text


class TestAppendToDbRepliesHandling:
    """测试 append_to_db 中 replies 字段的 JSONB 适配"""

    def test_replies_list_wrapped_in_json(self, config, monkeypatch):
        """list 类型的 replies 应被包装为 psycopg2.extras.Json()"""
        import json
        import psycopg2.extras

        processor, cursor, conn, captured = DataProcessor(config), Mock(), Mock(), {}
        cursor.execute = Mock(side_effect=lambda query, *args: captured.update(query=query, args=args) if "INSERT" in query else None)
        conn.cursor.return_value = cursor
        monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
        monkeypatch.setattr(processor, "_close_db_connection", lambda connection: None)

        replies_list = [{"id": 2, "content": "reply content"}]
        payload = [{"id": 99, "replies": replies_list}]
        assert processor.append_to_db(payload, "forum_topics") is True

        assert "INSERT INTO forum_topics" in captured.get("query", "")
        flat_args = captured["args"][0]
        replies_arg = flat_args[5]
        assert isinstance(replies_arg, str), "list 应被 Json() 序列化为 JSON 字符串"
        parsed = json.loads(replies_arg)
        assert parsed == replies_list

    def test_replies_empty_list_wrapped_in_json(self, config, monkeypatch):
        """空列表 [] 也应被包装为 Json()，而不是被 psycopg2 适配为 text[]"""
        import json

        processor, cursor, conn, captured = DataProcessor(config), Mock(), Mock(), {}
        cursor.execute = Mock(side_effect=lambda query, *args: captured.update(query=query, args=args) if "INSERT" in query else None)
        conn.cursor.return_value = cursor
        monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
        monkeypatch.setattr(processor, "_close_db_connection", lambda connection: None)

        payload = [{"id": 100}]
        assert processor.append_to_db(payload, "forum_topics") is True

        flat_args = captured["args"][0]
        replies_arg = flat_args[5]
        parsed = json.loads(replies_arg)
        assert parsed == []

    def test_replies_json_string_passed_through(self, config, monkeypatch):
        """已是 JSON 字符串的 replies 应原样传入（append_to_csv 前置处理）"""
        import json

        processor, cursor, conn, captured = DataProcessor(config), Mock(), Mock(), {}
        cursor.execute = Mock(side_effect=lambda query, *args: captured.update(query=query, args=args) if "INSERT" in query else None)
        conn.cursor.return_value = cursor
        monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
        monkeypatch.setattr(processor, "_close_db_connection", lambda connection: None)

        json_str = json.dumps([{"id": 3}])
        payload = [{"id": 101, "replies": json_str}]
        assert processor.append_to_db(payload, "processed_forum_topics") is True

        flat_args = captured["args"][0]
        replies_arg = flat_args[5]
        assert replies_arg == json_str

    def test_replies_none_passed_as_empty_list_json(self, config, monkeypatch):
        """replies 缺失时默认 [] 应被包装为 Json([])"""
        import json

        processor, cursor, conn, captured = DataProcessor(config), Mock(), Mock(), {}
        cursor.execute = Mock(side_effect=lambda query, *args: captured.update(query=query, args=args) if "INSERT" in query else None)
        conn.cursor.return_value = cursor
        monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
        monkeypatch.setattr(processor, "_close_db_connection", lambda connection: None)

        payload = [{"id": 102, "title": "no replies key"}]
        assert processor.append_to_db(payload, "pre_audit_topics") is True

        flat_args = captured["args"][0]
        replies_arg = flat_args[5]
        parsed = json.loads(replies_arg)
        assert parsed == []


class TestAppendToDbErrorPaths:
    """测试 append_to_db 和 save_search_results_to_db 的错误路径"""

    def test_append_to_db_no_connection(self, config, monkeypatch):
        """conn 为 None 时应返回 False"""
        processor = DataProcessor(config)
        monkeypatch.setattr(processor, "_get_db_connection", lambda: None)
        monkeypatch.setattr(processor, "_close_db_connection", lambda c: None)
        result = processor.append_to_db([{"id": 1}], "forum_topics")
        assert result is False

    def test_append_to_db_empty_data(self, config):
        """data 为空列表时应返回 False"""
        processor = DataProcessor(config)
        result = processor.append_to_db([], "forum_topics")
        assert result is False

    def test_save_search_results_to_db_no_connection(self, config, monkeypatch):
        """conn 为 None 时应静默返回"""
        processor = DataProcessor(config)
        monkeypatch.setattr(processor, "_get_db_connection", lambda: None)
        monkeypatch.setattr(processor, "_close_db_connection", lambda c: None)
        result = processor.save_search_results_to_db(1, [], "kw")
        assert result is None

    def test_append_to_db_multi_row_flattens_values(self, config, monkeypatch):
        """多行数据应被 flatten 为单层元组传入 cursor.execute"""
        from unittest.mock import Mock
        processor, cursor, conn, captured = DataProcessor(config), Mock(), Mock(), {}
        cursor.execute = Mock(side_effect=lambda query, *args: captured.update(query=query, args=args) if "INSERT" in query else None)
        conn.cursor.return_value = cursor
        monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
        monkeypatch.setattr(processor, "_close_db_connection", lambda c: None)

        payload = [
            {"id": 1},
            {"id": 2},
        ]
        assert processor.append_to_db(payload, "forum_topics") is True
        flat_args = captured["args"][0]
        assert flat_args[0] == 1
        assert flat_args[9] == 2

    def test_append_to_db_db_error_triggers_rollback(self, config, monkeypatch):
        """数据库写入失败时应触发 rollback 并返回 False"""
        from unittest.mock import Mock
        processor = DataProcessor(config)
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute = Mock(side_effect=RuntimeError("db error"))
        mock_conn.cursor.return_value = mock_cursor
        monkeypatch.setattr(processor, "_get_db_connection", lambda: mock_conn)
        monkeypatch.setattr(processor, "_close_db_connection", lambda c: None)
        result = processor.append_to_db([{"id": 99}], "processed_forum_topics")
        assert result is False
        mock_conn.rollback.assert_called_once()


class TestAppendToDbAdditionalPaths:
    """测试 append_to_db 的更多路径覆盖"""

    def test_append_to_db_commit_error_triggers_rollback(self, config, monkeypatch):
        """commit 失败时应触发 rollback"""
        from unittest.mock import Mock
        processor = DataProcessor(config)
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.commit = Mock(side_effect=RuntimeError("commit failed"))
        monkeypatch.setattr(processor, "_get_db_connection", lambda: mock_conn)
        monkeypatch.setattr(processor, "_close_db_connection", lambda c: None)
        result = processor.append_to_db([{"id": 88}], "forum_topics")
        assert result is False
        mock_conn.rollback.assert_called_once()

    def test_append_to_db_replies_with_mixed_types(self, config, monkeypatch):
        """replies 包含多种类型元素时应正确序列化"""
        import json
        processor, cursor, conn, captured = DataProcessor(config), Mock(), Mock(), {}
        cursor.execute = Mock(side_effect=lambda query, *args: captured.update(query=query, args=args) if "INSERT" in query else None)
        conn.cursor.return_value = cursor
        monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
        monkeypatch.setattr(processor, "_close_db_connection", lambda c: None)
        mixed_replies = ["string_reply", {"id": 1, "content": "dict_reply"}, 123, None]
        payload = [{"id": 77, "replies": mixed_replies, "tags": []}]
        result = processor.append_to_db(payload, "forum_topics")
        assert result is True
        flat_args = captured["args"][0]
        replies_arg = flat_args[5]
        parsed = json.loads(replies_arg)
        assert parsed == mixed_replies

    def test_append_to_db_with_all_fields_present(self, config, monkeypatch):
        """所有字段都存在时应正确插入"""
        processor, cursor, conn, captured = DataProcessor(config), Mock(), Mock(), {}
        cursor.execute = Mock(side_effect=lambda query, *args: captured.update(query=query, args=args) if "INSERT" in query else None)
        conn.cursor.return_value = cursor
        monkeypatch.setattr(processor, "_get_db_connection", lambda: conn)
        monkeypatch.setattr(processor, "_close_db_connection", lambda c: None)
        full_payload = [{
            "id": 55,
            "title": "Full Title",
            "user_question": "Full Question",
            "best_answer": "Full Answer",
            "tags": [{"name": "tag1"}, {"name": "tag2"}],
            "replies": [{"id": 1, "text": "reply1"}],
            "created_at": "2026-01-01T00:00:00Z",
            "llm_answer": "LLM Answer",
            "summary_question": "Summary"
        }]
        result = processor.append_to_db(full_payload, "forum_topics")
        assert result is True
        flat_args = captured["args"][0]
        assert flat_args[1] == "Full Title"
        assert flat_args[2] == "Full Question"
        assert flat_args[3] == "Full Answer"
        assert flat_args[4] == "tag1,tag2"

    def test_append_to_db_close_connection_error_logged(self, config, monkeypatch):
        """关闭连接失败时应记录日志但不影响返回值"""
        from unittest.mock import Mock
        import logging
        processor = DataProcessor(config)
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        close_error_mock = Mock()
        monkeypatch.setattr(processor, "_get_db_connection", lambda: mock_conn)
        monkeypatch.setattr(processor, "_close_db_connection", close_error_mock)
        result = processor.append_to_db([{"id": 66}], "forum_topics")
        assert result is True
        close_error_mock.assert_called_once()
