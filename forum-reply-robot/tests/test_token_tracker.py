import pytest
from src.ForumBot.token_tracker import TokenTracker


class TestTokenTracker:
    """测试 TokenTracker 类"""

    def test_init(self):
        """测试初始化"""
        tracker = TokenTracker()
        assert tracker.token_usage == {}

    def test_reset_usage(self):
        """测试重置token使用量"""
        tracker = TokenTracker()
        tracker.reset_usage(123)
        assert 123 in tracker.token_usage
        assert tracker.token_usage[123]['prompt_tokens'] == 0
        assert tracker.token_usage[123]['completion_tokens'] == 0
        assert tracker.token_usage[123]['total_tokens'] == 0
        assert tracker.token_usage[123]['model_calls'] == 0

    def test_add_usage(self):
        """测试累加token使用量"""
        tracker = TokenTracker()
        tracker.add_usage(123, prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert tracker.token_usage[123]['prompt_tokens'] == 10
        assert tracker.token_usage[123]['completion_tokens'] == 20
        assert tracker.token_usage[123]['total_tokens'] == 30
        assert tracker.token_usage[123]['model_calls'] == 1

        # 再次累加
        tracker.add_usage(123, prompt_tokens=5, completion_tokens=10, total_tokens=15)
        assert tracker.token_usage[123]['prompt_tokens'] == 15
        assert tracker.token_usage[123]['completion_tokens'] == 30
        assert tracker.token_usage[123]['total_tokens'] == 45
        assert tracker.token_usage[123]['model_calls'] == 2

    def test_add_usage_new_topic(self):
        """测试为新topic添加使用量"""
        tracker = TokenTracker()
        tracker.add_usage(456, prompt_tokens=100, completion_tokens=200, total_tokens=300)
        assert 456 in tracker.token_usage
        assert tracker.token_usage[456]['prompt_tokens'] == 100
        assert tracker.token_usage[456]['completion_tokens'] == 200
        assert tracker.token_usage[456]['total_tokens'] == 300
        assert tracker.token_usage[456]['model_calls'] == 1

    def test_get_usage_existing_topic(self):
        """测试获取已存在topic的使用量"""
        tracker = TokenTracker()
        tracker.add_usage(789, prompt_tokens=50, completion_tokens=100, total_tokens=150)
        usage = tracker.get_usage(789)
        assert usage['prompt_tokens'] == 50
        assert usage['completion_tokens'] == 100
        assert usage['total_tokens'] == 150
        assert usage['model_calls'] == 1

    def test_get_usage_nonexistent_topic(self):
        """测试获取不存在topic的使用量"""
        tracker = TokenTracker()
        usage = tracker.get_usage(999)
        assert usage['prompt_tokens'] == 0
        assert usage['completion_tokens'] == 0
        assert usage['total_tokens'] == 0
        assert usage['model_calls'] == 0

    def test_get_all_usage(self):
        """测试获取所有topic的使用量"""
        tracker = TokenTracker()
        tracker.add_usage(1, prompt_tokens=10, completion_tokens=20, total_tokens=30)
        tracker.add_usage(2, prompt_tokens=40, completion_tokens=50, total_tokens=90)
        all_usage = tracker.get_all_usage()
        assert len(all_usage) == 2
        assert 1 in all_usage
        assert 2 in all_usage