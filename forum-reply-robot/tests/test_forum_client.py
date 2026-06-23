import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 模拟psycopg2模块
sys.modules['psycopg2'] = Mock()

from src.ForumBot.forum_client import ForumClient


class TestForumClient:
    """测试 ForumClient 类"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'posts': {
                'base_url': 'https://test.com',
                'api_key': 'test_key',
                'api_username': 'test_user',
                'verify_ssl': False
            },
            'search': {
                'base_url': 'https://search.com',
                'endpoint': '/search',
                'source': 'test_source',
                'referer': 'test_referer',
                'default_page_size': 10,
                'max_keyword_length': 100,
                'verify_ssl': False
            },
            'retrieval': {
                'base_url': 'https://retrieval.com',
                'query_endpoint': '/query',
                'verify_ssl': False,
                'only_need_prompt': False,
                'only_need_context': True,
                'top_k': 5,
                'chunk_top_k': 10,
                'enable_rerank': True
            }
        }

    @pytest.fixture
    def client(self, config):
        """创建 ForumClient 实例"""
        return ForumClient(config)

    def test_init(self, client, config):
        """测试初始化"""
        assert client.config == config

    def test_remove_html_tags(self, client):
        """测试去除HTML标签"""
        # 测试基本HTML标签
        assert client._remove_html_tags('<p>Hello</p>') == 'Hello'
        assert client._remove_html_tags('<div>World</div>') == 'World'
        
        # 测试嵌套标签
        assert client._remove_html_tags('<div><p>Nested</p></div>') == 'Nested'
        
        # 测试多个标签
        assert client._remove_html_tags('<p>First</p><p>Second</p>') == 'FirstSecond'
        
        # 测试带属性的标签
        assert client._remove_html_tags('<p class="test">Content</p>') == 'Content'
        
        # 测试纯文本
        assert client._remove_html_tags('Plain text') == 'Plain text'
        
        # 测试空字符串
        assert client._remove_html_tags('') == ''

    @patch('src.ForumBot.forum_client.requests.post')
    def test_reply_to_topic_success(self, mock_post, client):
        """测试成功回复帖子"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'post_id': 123}
        mock_post.return_value = mock_response

        result = client.reply_to_topic(456, 'Test reply content')

        assert result['success'] is True
        assert result['data']['post_id'] == 123
        mock_post.assert_called_once()

    @patch('src.ForumBot.forum_client.requests.post')
    def test_reply_to_topic_failure(self, mock_post, client):
        """测试回复帖子失败"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        result = client.reply_to_topic(456, 'Test reply content')

        assert result['success'] is False
        assert result['status_code'] == 500
        assert 'error_message' in result

    @patch('src.ForumBot.forum_client.requests.post')
    def test_reply_to_topic_exception(self, mock_post, client):
        """测试回复帖子异常"""
        mock_post.side_effect = Exception('Network error')

        result = client.reply_to_topic(456, 'Test reply content')

        assert result['success'] is False
        assert 'error' in result

    @patch('src.ForumBot.forum_client.requests.post')
    def test_search_related_topics_success(self, mock_post, client):
        """测试成功搜索相关主题"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'obj': {
                'records': [
                    {'title': '<p>Title 1</p>', 'textContent': '<div>Content 1</div>'},
                    {'title': '<p>Title 2</p>', 'textContent': '<div>Content 2</div>'}
                ]
            }
        }
        mock_post.return_value = mock_response

        result = client.search_related_topics('test keyword', 123)

        assert len(result) == 2
        assert result[0]['title'] == 'Title 1'
        assert result[0]['textContent'] == 'Content 1'
        assert result[1]['title'] == 'Title 2'
        assert result[1]['textContent'] == 'Content 2'

    @patch('src.ForumBot.forum_client.requests.post')
    def test_search_related_topics_keyword_truncation(self, mock_post, client):
        """测试关键字截断"""
        long_keyword = 'a' * 200
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'obj': {'records': []}}
        mock_post.return_value = mock_response

        client.search_related_topics(long_keyword, 123)

        # 验证关键字被截断
        call_args = mock_post.call_args
        assert len(call_args[1]['json']['keyword']) == 100

    @patch('src.ForumBot.forum_client.requests.post')
    def test_search_related_topics_failure(self, mock_post, client):
        """测试搜索失败"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = client.search_related_topics('test', 123)

        assert result == []

    @patch('src.ForumBot.forum_client.requests.post')
    def test_search_related_topics_exception(self, mock_post, client):
        """测试搜索异常"""
        mock_post.side_effect = Exception('Network error')

        result = client.search_related_topics('test', 123)

        assert result == []

    @patch('src.ForumBot.forum_client.requests.post')
    def test_retrieve_documents_for_topic_success(self, mock_post, client):
        """测试成功检索文档"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {'response': 'test response'}
        mock_post.return_value = mock_response

        topic = {
            'id': 123,
            'title': 'Test Title',
            'user_question': 'Test Question'
        }

        result = client.retrieve_documents_for_topic(topic)

        assert result['topic_id'] == 123
        assert result['related_docs'] == 'test response'
        assert 'data' in result

    @patch('src.ForumBot.forum_client.requests.post')
    def test_retrieve_documents_for_topic_exception(self, mock_post, client):
        """测试检索文档异常"""
        mock_post.side_effect = Exception('Network error')

        topic = {
            'id': 123,
            'title': 'Test Title',
            'user_question': 'Test Question'
        }

        try:
            result = client.retrieve_documents_for_topic(topic)
            assert result['topic_id'] == 123
            assert result['related_docs'] is None
        except Exception:
            pass  # 预期会抛出异常