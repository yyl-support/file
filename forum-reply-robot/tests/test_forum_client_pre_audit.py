from unittest.mock import Mock

from src.ForumBot.forum_client import ForumClient


def test_fetch_all_forum_topics_passes_pre_audit_keys(monkeypatch):
    config = {
        "monitor": {},
        "forum": {"base_url": "https://forum.test"},
    }
    client = ForumClient(config)
    captured = {}

    def fake_fetch_all_forum_topics(config_arg, tag_key, cutoff_date_key, category_path_key):
        captured["config"] = config_arg
        captured["tag_key"] = tag_key
        captured["cutoff_date_key"] = cutoff_date_key
        captured["category_path_key"] = category_path_key
        return [{"id": 1}]

    monkeypatch.setattr("src.ForumBot.forum_client.fetch_all_forum_topics", fake_fetch_all_forum_topics)

    result = client.fetch_all_forum_topics(
        tag_key="pre_audit_tag",
        cutoff_date_key="pre_audit_cutoff_date",
        category_path_key="pre_audit_category_path",
    )

    assert result == [{"id": 1}]
    assert captured == {
        "config": config,
        "tag_key": "pre_audit_tag",
        "cutoff_date_key": "pre_audit_cutoff_date",
        "category_path_key": "pre_audit_category_path",
    }
