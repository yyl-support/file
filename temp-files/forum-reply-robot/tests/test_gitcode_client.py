import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import json
import base64
from src.update_lightrag.gitcode_client import GitCodeClient


class TestGitCodeClient:
    """测试 GitCodeClient 类"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'gitcode': {
                'owner': 'test_owner',
                'repo': 'test_repo',
                'api_token': 'test_token',
                'verify_ssl': True,
                'request_delay': 0.1,
                'base_path': 'docs/zh/development',
                'skip_dirs': ['images']
            }
        }

    @pytest.fixture
    def client(self, config):
        """创建 GitCodeClient 实例"""
        return GitCodeClient(config)

    def test_init(self, client, config):
        """测试初始化"""
        assert client.config == config
        assert client.owner == 'test_owner'
        assert client.repo == 'test_repo'
        assert client.api_token == 'test_token'
        assert client.verify_ssl == True
        assert client.request_delay == 0.1
        assert client.base_url == "https://api.gitcode.com/api/v5"
        assert 'Authorization' in client.headers
        assert 'PRIVATE-TOKEN' in client.headers

    def test_init_default_values(self):
        """测试默认配置值"""
        config = {}
        client = GitCodeClient(config)
        assert client.owner == 'openUBMC'
        assert client.repo == 'docs'
        assert client.api_token == ''
        assert client.verify_ssl == True
        assert client.request_delay == 0.5

    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_file_content_base64(self, mock_get, client):
        """测试获取文件内容 - base64编码"""
        content = 'test file content'
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'encoding': 'base64',
            'content': encoded_content
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = client.get_file_content('test/path.md')

        assert result == content
        mock_get.assert_called_once()

    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_file_content_plain(self, mock_get, client):
        """测试获取文件内容 - 普通文本"""
        content = 'plain text content'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'encoding': 'plain',
            'content': content
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = client.get_file_content('test/path.md')

        assert result == content

    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_file_content_with_ref(self, mock_get, client):
        """测试获取文件内容 - 指定分支"""
        content = 'test content'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': content
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = client.get_file_content('test/path.md', ref='dev')

        assert result == content
        call_args = mock_get.call_args
        assert call_args[1]['params']['ref'] == 'dev'

    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_file_content_request_error(self, mock_get, client):
        """测试获取文件内容 - 请求异常"""
        mock_get.side_effect = requests.exceptions.RequestException('Network error')

        result = client.get_file_content('test/path.md')

        assert result is None

    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_file_content_json_error(self, mock_get, client):
        """测试获取文件内容 - JSON解析异常"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError('Invalid JSON', '', 0)
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = client.get_file_content('test/path.md')

        assert result is None

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_success(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - 成功"""
        commits_data = [
            {'sha': 'abc123', 'commit': {'message': 'First commit'}},
            {'sha': 'def456', 'commit': {'message': 'Second commit'}}
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = commits_data
        mock_get.return_value = mock_response

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert len(result) == 2
        assert result[0]['sha'] == 'abc123'
        mock_sleep.assert_called()

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_empty(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - 空"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert result == []

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_not_list(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - 返回非列表"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'error': 'not a list'}
        mock_get.return_value = mock_response

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert result == []

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_error_status(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - 错误状态码"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = 'Not found'
        mock_get.return_value = mock_response

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert result == []

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_request_error(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - 请求异常"""
        mock_get.side_effect = requests.exceptions.RequestException('Network error')

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert result == []

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_json_error(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - JSON解析异常"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError('Invalid', '', 0)
        mock_get.return_value = mock_response

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert result == []

    def test_get_commits_since_time_format_conversion(self, client):
        """测试时间格式转换"""
        with patch('src.update_lightrag.gitcode_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response
            
            with patch('src.update_lightrag.gitcode_client.time.sleep'):
                result = client.get_commits_since('2024-01-01T00:00:00+00:00')
                
                call_args = mock_get.call_args
                since_param = call_args[1]['params']['since']
                assert since_param == '2024-01-01T00:00:00Z'

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_pagination_single_page(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - 单页（少于per_page）"""
        commits_data = [
            {'sha': 'abc123', 'commit': {'message': 'First commit'}},
            {'sha': 'def456', 'commit': {'message': 'Second commit'}}
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = commits_data
        mock_get.return_value = mock_response

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert len(result) == 2
        assert result[0]['sha'] == 'abc123'
        mock_get.assert_called_once()

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_pagination_multiple_pages(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - 多页分页"""
        page1_data = [{'sha': f'commit{i}', 'commit': {'message': f'Message {i}'}} for i in range(100)]
        page2_data = [{'sha': f'commit{i}', 'commit': {'message': f'Message {i}'}} for i in range(100, 150)]
        
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1_data
        
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = page2_data
        
        mock_get.side_effect = [mock_response1, mock_response2]

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert len(result) == 150
        assert mock_get.call_count == 2

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_pagination_three_pages(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - 三页分页"""
        page1_data = [{'sha': f'commit{i}', 'commit': {'message': f'Message {i}'}} for i in range(100)]
        page2_data = [{'sha': f'commit{i}', 'commit': {'message': f'Message {i}'}} for i in range(100, 200)]
        page3_data = [{'sha': f'commit{i}', 'commit': {'message': f'Message {i}'}} for i in range(200, 250)]
        
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1_data
        
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = page2_data
        
        mock_response3 = Mock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = page3_data
        
        mock_get.side_effect = [mock_response1, mock_response2, mock_response3]

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert len(result) == 250
        assert mock_get.call_count == 3

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_commits_since_pagination_error_on_second_page(self, mock_get, mock_sleep, client):
        """测试获取提交列表 - 第二页出错"""
        page1_data = [{'sha': f'commit{i}', 'commit': {'message': f'Message {i}'}} for i in range(100)]
        
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1_data
        
        mock_response2 = Mock()
        mock_response2.status_code = 500
        mock_response2.text = 'Server error'
        
        mock_get.side_effect = [mock_response1, mock_response2]

        result = client.get_commits_since('2024-01-01T00:00:00Z')

        assert len(result) == 100

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_compare_files_success(self, mock_get, mock_sleep, client):
        """测试获取变更文件 - 成功"""
        files_data = {
            'files': [
                {'filename': 'docs/zh/test.md', 'status': 'added'},
                {'filename': 'docs/zh/dev.md', 'status': 'modified'},
                {'filename': 'docs/test.txt', 'status': 'modified'}
            ]
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = files_data
        mock_get.return_value = mock_response

        result = client.get_compare_files('base123', 'head456')

        assert len(result) == 2
        assert result[0]['filename'] == 'docs/zh/test.md'
        assert result[0]['status'] == 'added'

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_compare_files_empty(self, mock_get, mock_sleep, client):
        """测试获取变更文件 - 空"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'files': []}
        mock_get.return_value = mock_response

        result = client.get_compare_files('base123', 'head456')

        assert result == []

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_compare_files_no_files_key(self, mock_get, mock_sleep, client):
        """测试获取变更文件 - 无files字段"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'commits': []}
        mock_get.return_value = mock_response

        result = client.get_compare_files('base123', 'head456')

        assert result == []

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_compare_files_invalid_file_info(self, mock_get, mock_sleep, client):
        """测试获取变更文件 - 无效文件信息"""
        files_data = {
            'files': [
                {'filename': 'docs/zh/test.md', 'status': 'added'},
                'invalid_string',
                None,
                {'filename': '', 'status': 'added'}
            ]
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = files_data
        mock_get.return_value = mock_response

        result = client.get_compare_files('base123', 'head456')

        assert len(result) == 1
        assert result[0]['filename'] == 'docs/zh/test.md'

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_compare_files_error_status(self, mock_get, mock_sleep, client):
        """测试获取变更文件 - 错误状态码"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = 'Not found'
        mock_get.return_value = mock_response

        result = client.get_compare_files('base123', 'head456')

        assert result == []

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_compare_files_rate_limit(self, mock_get, mock_sleep, client):
        """测试获取变更文件 - 速率限制"""
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        
        mock_get.return_value = mock_response_429

        result = client.get_compare_files('base123', 'head456')

        assert result == []

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_compare_files_request_error(self, mock_get, mock_sleep, client):
        """测试获取变更文件 - 请求异常"""
        mock_get.side_effect = requests.exceptions.RequestException('Network error')

        result = client.get_compare_files('base123', 'head456')

        assert result == []

    @patch('src.update_lightrag.gitcode_client.time.sleep')
    @patch('src.update_lightrag.gitcode_client.requests.get')
    def test_get_compare_files_json_error(self, mock_get, mock_sleep, client):
        """测试获取变更文件 - JSON解析异常"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError('Invalid', '', 0)
        mock_get.return_value = mock_response

        result = client.get_compare_files('base123', 'head456')

        assert result == []