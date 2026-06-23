from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.ForumBot import monitor as monitor_module
from src.ForumBot.monitor import ForumMonitor


def build_monitor():
    monitor = ForumMonitor.__new__(ForumMonitor)
    monitor.config = {"monitor": {"pre_audit_tag": ["pre-audit"], "pre_audit_category_path": [], "pre_audit_title_filter_keywords": ["已评审"]}, "paths": {"processed_csv_file": "processed.csv"}}
    monitor.forum_client = Mock()
    monitor.data_processor = Mock()
    monitor.ai_processor = Mock()
    return monitor


def check_monitor():
    monitor = build_monitor()
    monitor.data_processor.load_pre_audit_existing_data.return_value = {}
    monitor.forum_client.fetch_all_forum_topics.return_value = [{"id": 10, "title": "待预审主题"}]
    monitor.forum_client.fetch_topic_details.return_value = {"id": 10, "post_stream": {"posts": [{"cooked": "<p>ready</p>"}]}}
    monitor.data_processor.extract_topic_data.return_value = [{"id": 10, "title": "待预审主题", "user_question": "问题内容"}]
    monitor._process_pre_audit_topic = Mock()
    return monitor


def test_check_pre_audit_topics_ready_topic_calls_process(monkeypatch):
    monitor = build_monitor()
    monitor.data_processor.load_pre_audit_existing_data.return_value = {}
    monitor.forum_client.fetch_all_forum_topics.return_value = [{"id": 10, "title": "待预审主题"}, {"id": 20, "title": "已评审主题"}]
    monitor.forum_client.fetch_topic_details.return_value = {"id": 10, "post_stream": {"posts": [{"cooked": "<p>ready</p>"}]}}
    monitor.data_processor.extract_topic_data.return_value = [{"id": 10, "title": "待预审主题", "user_question": "问题内容"}]
    process_mock = Mock()
    monitor._process_pre_audit_topic = process_mock
    monkeypatch.setattr(monitor_module, "parse_pre_audit_readiness", lambda html, config: True)
    monitor._check_pre_audit_topics()
    monitor.forum_client.fetch_all_forum_topics.assert_called_once_with(tag_key="pre_audit_tag", cutoff_date_key="pre_audit_cutoff_date", category_path_key="pre_audit_category_path")
    monitor.data_processor.append_to_db.assert_called_once_with([{"id": 10, "title": "待预审主题"}], "pre_audit_topics")
    process_mock.assert_called_once_with({"id": 10, "title": "待预审主题", "user_question": "问题内容"})


def test_process_pre_audit_topic_skips_when_prompt_injection_detected():
    monitor = build_monitor()
    monitor.ai_processor.check_prompt_injection.return_value = "yes"
    topic = {"id": 1, "title": "topic", "user_question": "question"}
    monitor._process_pre_audit_topic(topic)
    monitor.data_processor.append_to_db.assert_called_once_with([topic], "pre_audit_processed_topics")
    monitor.forum_client.reply_to_topic.assert_not_called()


def test_process_pre_audit_topic_skips_empty_answer(monkeypatch):
    monitor = build_monitor()
    monitor.ai_processor.check_prompt_injection.return_value = "no"
    monkeypatch.setattr(monitor_module, "run_schema_check", lambda **kwargs: "Empty response")
    topic = {"id": 2, "title": "topic", "user_question": "question"}
    monitor._process_pre_audit_topic(topic)
    monitor.data_processor.append_to_db.assert_called_once_with([topic], "pre_audit_processed_topics")
    monitor.forum_client.reply_to_topic.assert_not_called()


def test_process_pre_audit_topic_blocks_timeout_answer(monkeypatch):
    monitor = build_monitor()
    monitor.ai_processor.check_prompt_injection.return_value = "no"
    monkeypatch.setattr(
        monitor_module,
        "run_schema_check",
        lambda **kwargs: "规则合规性失败项：\n[RULE-001] 检查失败: Request timed out.",
    )
    topic = {"id": 8, "title": "topic", "user_question": "question"}

    monitor._process_pre_audit_topic(topic)

    monitor.data_processor.append_to_db.assert_called_once_with([topic], "pre_audit_processed_topics")
    monitor.forum_client.reply_to_topic.assert_not_called()


def test_process_pre_audit_topic_success_replies_and_records(monkeypatch):
    monitor = build_monitor()
    monitor.ai_processor.check_prompt_injection.return_value = "no"
    monitor.forum_client.reply_to_topic.return_value = {"success": True}
    monkeypatch.setattr(monitor_module, "run_schema_check", lambda **kwargs: "审核结论")
    monkeypatch.setattr(monitor_module, "token_tracker", SimpleNamespace(get_usage=lambda topic_id: {"total_tokens": 12, "prompt_tokens": 5, "completion_tokens": 7, "model_calls": 1}))
    topic = {"id": 3, "title": "topic", "user_question": "question"}
    monitor._process_pre_audit_topic(topic)
    monitor.forum_client.reply_to_topic.assert_called_once()
    monitor.data_processor.append_to_csv.assert_called_once()
    monitor.data_processor.append_to_db.assert_called_once_with([topic], "pre_audit_processed_topics")
    monitor.data_processor.save_token_usage_to_db.assert_called_once()


@pytest.mark.parametrize("case", ["no_config", "existing_none", "no_topics", "already_seen", "missing_details", "not_ready", "missing_field", "extract_empty"])
def test_check_pre_audit_topics_skip_paths(monkeypatch, case):
    monitor, readiness = check_monitor(), True
    if case == "no_config":
        monitor.config["monitor"].update(pre_audit_tag=[], pre_audit_category_path=[])
    elif case == "existing_none":
        monitor.data_processor.load_pre_audit_existing_data.return_value = None
    elif case == "no_topics":
        monitor.forum_client.fetch_all_forum_topics.return_value = []
    elif case == "already_seen":
        monitor.data_processor.load_pre_audit_existing_data.return_value = {10: True}
    elif case == "missing_details":
        monitor.forum_client.fetch_topic_details.return_value = None
    elif case == "not_ready":
        readiness = False
    elif case == "missing_field":
        readiness = None
    else:
        monitor.data_processor.extract_topic_data.return_value = []
    monkeypatch.setattr(monitor_module, "parse_pre_audit_readiness", lambda html, config: readiness)
    monitor._check_pre_audit_topics()
    if case == "no_config":
        monitor.data_processor.load_pre_audit_existing_data.assert_not_called()
    elif case == "existing_none":
        monitor.forum_client.fetch_all_forum_topics.assert_not_called()
    else:
        monitor.data_processor.append_to_db.assert_not_called()
        monitor._process_pre_audit_topic.assert_not_called()


def test_check_pre_audit_topics_continues_after_topic_exception(monkeypatch):
    monitor = check_monitor()
    monitor.forum_client.fetch_all_forum_topics.return_value = [{"id": 10, "title": "first"}, {"id": 20, "title": "second"}]
    monitor.forum_client.fetch_topic_details.side_effect = [RuntimeError("boom"), None]
    monkeypatch.setattr(monitor_module, "parse_pre_audit_readiness", lambda html, config: True)
    monitor._check_pre_audit_topics()
    assert monitor.forum_client.fetch_topic_details.call_count == 2


@pytest.mark.parametrize(("answer", "should_append"), [("处理失败: downstream error", False), ("   ", True)])
def test_process_pre_audit_topic_non_reply_variants(monkeypatch, answer, should_append):
    monitor = build_monitor()
    monitor.ai_processor.check_prompt_injection.return_value = "no"
    monkeypatch.setattr(monitor_module, "run_schema_check", lambda **kwargs: answer)
    topic = {"id": 4, "title": "topic", "user_question": "question"}
    monitor._process_pre_audit_topic(topic)
    assert monitor.data_processor.append_to_db.called is should_append
    monitor.forum_client.reply_to_topic.assert_not_called()


def test_process_pre_audit_topic_records_when_reply_fails(monkeypatch):
    monitor = build_monitor()
    monitor.ai_processor.check_prompt_injection.return_value = "no"
    monitor.forum_client.reply_to_topic.return_value = {"success": False, "error_message": "bad gateway"}
    monkeypatch.setattr(monitor_module, "run_schema_check", lambda **kwargs: "review result")
    monkeypatch.setattr(monitor_module, "token_tracker", SimpleNamespace(get_usage=lambda topic_id: {"total_tokens": 8, "prompt_tokens": 3, "completion_tokens": 5, "model_calls": 1}))
    topic = {"id": 7, "title": "topic", "user_question": "question"}
    monitor._process_pre_audit_topic(topic)
    monitor.forum_client.reply_to_topic.assert_called_once()
    monitor.data_processor.append_to_csv.assert_called_once()
    monitor.data_processor.append_to_db.assert_called_once_with([topic], "pre_audit_processed_topics")


def test_start_checks_pre_audit_topics_before_sleep(monkeypatch):
    monitor = ForumMonitor.__new__(ForumMonitor)
    monitor.config = {"paths": {"csv_file": "topics.csv"}, "monitor": {"check_interval": 1}}
    monitor._check_new_topics = Mock()
    monitor._check_pre_audit_topics = Mock()
    monkeypatch.setattr(monitor_module.time, "sleep", lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()))
    monitor.start()
    monitor._check_new_topics.assert_called_once_with("topics.csv")
    monitor._check_pre_audit_topics.assert_called_once_with()


def test_sync_csv_to_git_repo_runs_validated_git_commands(monkeypatch):
    monitor = build_monitor()
    monitor.config = {
        "git": {
            "repo_dir": "/repo",
            "data_dir": "data",
            "branch": "main",
        }
    }
    monitor.git_path = "/usr/bin/git"
    monitor._copy_csv_with_bom = Mock()

    commands = []
    returncodes = iter([0, 0, 0, 1, 0, 0])

    def fake_run(command, cwd, capture_output, text):
        commands.append(command)
        return SimpleNamespace(returncode=next(returncodes), stderr="")

    monkeypatch.setattr(monitor_module.subprocess, "run", fake_run)
    monkeypatch.setattr(monitor_module.os, "makedirs", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(monitor_module.os.path, "exists", lambda _path: True)

    monitor._sync_csv_to_git_repo("/input/source.csv", topic_id=42)

    assert commands[0] == ["/usr/bin/git", "fetch"]
    assert commands[1] == ["/usr/bin/git", "reset", "--hard", "origin/main"]
    assert commands[2] == ["/usr/bin/git", "add", "data/source.csv"]
    assert commands[3] == ["/usr/bin/git", "diff", "--cached", "--exit-code"]
    assert commands[4][0:3] == ["/usr/bin/git", "commit", "-m"]
    assert commands[5] == ["/usr/bin/git", "push", "origin", "main"]
