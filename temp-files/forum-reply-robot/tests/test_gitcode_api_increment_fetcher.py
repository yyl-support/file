import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import json
import tempfile
from src.update_lightrag.gitcode_api_increment_fetcher import GitCodeAPIIncrementFetcher


class TestGitCodeAPIIncrementFetcher:
    """测试 GitCodeAPIIncrementFetcher 类"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'gitcode': {
                'owner': 'test_owner',
                'repo': 'test_repo',
                'api_token': 'test_token',
                'base_path': 'docs/zh/development',
                'skip_dirs': ['images', 'assets']
            },
            'lightrag_paths': {
                'rag_data_dir': '/tmp/test_rag_data',
                'new_rag_files': '/tmp/test_new_rag_files.txt',
                'delete_rag_files_id': '/tmp/test_delete_files.txt',
                'files_id_mapping': '/tmp/test_mapping.json'
            }
        }

    @pytest.fixture
    def fetcher(self, config):
        """创建 GitCodeAPIIncrementFetcher 实例"""
        return GitCodeAPIIncrementFetcher(config)

    def test_init(self, fetcher, config):
        """测试初始化"""
        assert fetcher.config == config
        assert fetcher.base_path == 'docs/zh/development'
        assert fetcher.output_dir == '/tmp/test_rag_data'
        assert fetcher.update_files_path == '/tmp/test_new_rag_files.txt'
        assert fetcher.delete_files_path == '/tmp/test_delete_files.txt'
        assert fetcher.skip_dirs == ['images', 'assets']

    def test_init_default_values(self):
        """测试默认配置值"""
        config = {
            'lightrag_paths': {
                'rag_data_dir': '/tmp/rag',
                'new_rag_files': '/tmp/new.txt'
            }
        }
        fetcher = GitCodeAPIIncrementFetcher(config)
        assert fetcher.base_path == 'docs/zh/development'
        assert fetcher.skip_dirs == ['images']
        assert fetcher.delete_files_path == ''

    @patch.object(GitCodeAPIIncrementFetcher, '__init__', return_value=None)
    def test_get_safe_filename_docs_path(self, mock_init):
        """测试获取安全文件名 - docs路径"""
        fetcher = GitCodeAPIIncrementFetcher({})
        fetcher._get_safe_filename = lambda path: path.replace('/', '_') if path.startswith('docs') else os.path.basename(path)
        
        result = fetcher._get_safe_filename('docs/zh/development/test.md')
        assert result == 'docs_zh_development_test.md'

    @patch.object(GitCodeAPIIncrementFetcher, '__init__', return_value=None)
    def test_get_safe_filename_non_docs_path(self, mock_init):
        """测试获取安全文件名 - 非docs路径"""
        fetcher = GitCodeAPIIncrementFetcher({})
        fetcher._get_safe_filename = lambda path: path.replace('/', '_') if path.startswith('docs') else os.path.basename(path)
        
        result = fetcher._get_safe_filename('test/readme.md')
        assert result == 'readme.md'

    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_commits_since')
    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_compare_files')
    def test_get_updated_files_by_commits_no_commits(self, mock_compare, mock_commits, fetcher):
        """测试获取更新文件 - 无提交"""
        mock_commits.return_value = []
        
        result = fetcher.get_updated_files_by_commits('2024-01-01T00:00:00Z')
        
        assert result == ([], [])
        mock_commits.assert_called_once()

    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_commits_since')
    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_compare_files')
    def test_get_updated_files_by_commits_no_parents(self, mock_compare, mock_commits, fetcher):
        """测试获取更新文件 - 提交无父提交"""
        mock_commits.return_value = [
            {'sha': 'abc123', 'commit': {'message': 'First commit'}, 'parents': []}
        ]
        
        result = fetcher.get_updated_files_by_commits('2024-01-01T00:00:00Z')
        
        assert result == ([], [])
        mock_compare.assert_not_called()

    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_commits_since')
    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_compare_files')
    def test_get_updated_files_by_commits_parent_no_sha(self, mock_compare, mock_commits, fetcher):
        """测试获取更新文件 - 父提交无SHA"""
        mock_commits.return_value = [
            {'sha': 'abc123', 'commit': {'message': 'First commit'}, 'parents': [{'sha': ''}]}
        ]
        
        result = fetcher.get_updated_files_by_commits('2024-01-01T00:00:00Z')
        
        assert result == ([], [])
        mock_compare.assert_not_called()

    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_commits_since')
    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_compare_files')
    def test_get_updated_files_by_commits_success(self, mock_compare, mock_commits, fetcher):
        """测试获取更新文件 - 成功"""
        mock_commits.return_value = [
            {
                'sha': 'abc123',
                'commit': {'message': 'Add docs'},
                'parents': [{'sha': 'base123'}]
            }
        ]
        mock_compare.return_value = [
            {'filename': 'docs/zh/development/test.md', 'status': 'added'},
            {'filename': 'docs/zh/development/dev.md', 'status': 'modified'},
            {'filename': 'docs/zh/development/old.md', 'status': 'deleted'},
            {'filename': 'other/path.md', 'status': 'added'},
            {'filename': 'docs/zh/development/images/img.md', 'status': 'added'}
        ]
        
        result = fetcher.get_updated_files_by_commits('2024-01-01T00:00:00Z')
        
        updated, deleted = result
        assert 'docs/zh/development/test.md' in updated
        assert 'docs/zh/development/dev.md' in updated
        assert 'docs/zh/development/old.md' in deleted
        assert 'other/path.md' not in updated
        assert 'docs/zh/development/images/img.md' not in updated

    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_commits_since')
    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_compare_files')
    def test_get_updated_files_by_commits_invalid_file_info(self, mock_compare, mock_commits, fetcher):
        """测试获取更新文件 - 无效文件信息"""
        mock_commits.return_value = [
            {
                'sha': 'abc123',
                'commit': {'message': 'Add docs'},
                'parents': [{'sha': 'base123'}]
            }
        ]
        mock_compare.return_value = [
            {'filename': 'docs/zh/development/test.md', 'status': 'added'},
            'invalid_string',
            None,
            {'filename': '', 'status': 'added'},
            {'filename': 'docs/zh/development/dev.md', 'status': 'modified'}
        ]
        
        result = fetcher.get_updated_files_by_commits('2024-01-01T00:00:00Z')
        
        updated, deleted = result
        assert len(updated) == 2
        assert len(deleted) == 0

    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_commits_since')
    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_compare_files')
    def test_get_updated_files_by_commits_multiple_commits(self, mock_compare, mock_commits, fetcher):
        """测试获取更新文件 - 多个提交"""
        mock_commits.return_value = [
            {
                'sha': 'abc123',
                'commit': {'message': 'First commit'},
                'parents': [{'sha': 'base123'}]
            },
            {
                'sha': 'def456',
                'commit': {'message': 'Second commit'},
                'parents': [{'sha': 'abc123'}]
            }
        ]
        mock_compare.side_effect = [
            [{'filename': 'docs/zh/development/test.md', 'status': 'added'}],
            [{'filename': 'docs/zh/development/test.md', 'status': 'modified'}]
        ]
        
        result = fetcher.get_updated_files_by_commits('2024-01-01T00:00:00Z')
        
        updated, deleted = result
        assert 'docs/zh/development/test.md' in updated

    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_file_content')
    def test_fetch_file_content_success(self, mock_get_content, fetcher):
        """测试获取文件内容 - 成功"""
        mock_get_content.return_value = 'Test content'
        
        result = fetcher.fetch_file_content('docs/zh/test.md')
        
        assert result is not None
        assert result['file_path'] == 'docs/zh/test.md'
        assert result['file_name'] == 'test.md'
        assert result['content'] == 'Test content'

    @patch('src.update_lightrag.gitcode_client.GitCodeClient.get_file_content')
    def test_fetch_file_content_failure(self, mock_get_content, fetcher):
        """测试获取文件内容 - 失败"""
        mock_get_content.return_value = None
        
        result = fetcher.fetch_file_content('docs/zh/test.md')
        
        assert result is None

    def test_save_file_to_local_success(self, fetcher):
        """测试保存文件到本地 - 成功"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher.output_dir = tmpdir
            file_data = {
                'file_path': 'docs/zh/development/test.md',
                'file_name': 'test.md',
                'content': 'Test content'
            }
            
            result = fetcher.save_file_to_local(file_data)
            
            assert result is not None
            assert os.path.exists(result)
            with open(result, 'r', encoding='utf-8') as f:
                assert f.read() == 'Test content'

    def test_save_file_to_local_non_docs_path(self, fetcher):
        """测试保存文件到本地 - 非docs路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher.output_dir = tmpdir
            file_data = {
                'file_path': 'other/test.md',
                'file_name': 'test.md',
                'content': 'Test content'
            }
            
            result = fetcher.save_file_to_local(file_data)
            
            assert result is not None
            assert 'test.md' in result

    @patch('src.update_lightrag.gitcode_api_increment_fetcher.os.makedirs', side_effect=PermissionError('Permission denied'))
    @patch('src.update_lightrag.gitcode_api_increment_fetcher.os.path.exists', return_value=False)
    def test_save_file_to_local_makedirs_error(self, mock_exists, mock_makedirs, fetcher):
        """测试保存文件到本地 - 创建目录失败"""
        fetcher.output_dir = '/any/path'
        file_data = {
            'file_path': 'docs/test.md',
            'file_name': 'test.md',
            'content': 'Test content'
        }
        
        result = fetcher.save_file_to_local(file_data)
        
        assert result is None

    def test_append_to_file_success(self, fetcher):
        """测试追加写入文件 - 成功"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_file = f.name
        
        try:
            fetcher._append_to_file(test_file, 'test_item')
            
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            assert 'test_item' in content
        finally:
            os.unlink(test_file)

    def test_append_to_file_empty_path(self, fetcher):
        """测试追加写入文件 - 空路径"""
        result = fetcher._append_to_file('', 'test_item')
        assert result is None

    def test_append_to_file_error(self, fetcher):
        """测试追加写入文件 - 异常"""
        fetcher._append_to_file('/nonexistent/path/file.txt', 'test_item')

    @patch.object(GitCodeAPIIncrementFetcher, 'get_updated_files_by_commits')
    @patch.object(GitCodeAPIIncrementFetcher, 'fetch_file_content')
    @patch.object(GitCodeAPIIncrementFetcher, 'save_file_to_local')
    def test_fetch_and_save_updated_files_no_updates(self, mock_save, mock_fetch, mock_get_updates, fetcher):
        """测试获取并保存更新文件 - 无更新"""
        mock_get_updates.return_value = ([], [])
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({}, f)
            mapping_file = f.name
        
        try:
            result = fetcher.fetch_and_save_updated_files(mapping_file, '2024-01-01T00:00:00Z')
            assert result == []
        finally:
            os.unlink(mapping_file)

    @patch.object(GitCodeAPIIncrementFetcher, 'get_updated_files_by_commits')
    def test_fetch_and_save_updated_files_mapping_not_found(self, mock_get_updates, fetcher):
        """测试获取并保存更新文件 - mapping文件不存在"""
        mock_get_updates.return_value = (['docs/test.md'], [])
        
        result = fetcher.fetch_and_save_updated_files('/nonexistent/mapping.json', '2024-01-01T00:00:00Z')
        assert result == []

    @patch.object(GitCodeAPIIncrementFetcher, 'get_updated_files_by_commits')
    def test_fetch_and_save_updated_files_mapping_invalid_json(self, mock_get_updates, fetcher):
        """测试获取并保存更新文件 - mapping文件无效JSON"""
        mock_get_updates.return_value = (['docs/test.md'], [])
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('invalid json content')
            mapping_file = f.name
        
        try:
            result = fetcher.fetch_and_save_updated_files(mapping_file, '2024-01-01T00:00:00Z')
            assert result == []
        finally:
            os.unlink(mapping_file)

    @patch.object(GitCodeAPIIncrementFetcher, 'get_updated_files_by_commits')
    @patch.object(GitCodeAPIIncrementFetcher, 'fetch_file_content')
    @patch.object(GitCodeAPIIncrementFetcher, 'save_file_to_local')
    @patch.object(GitCodeAPIIncrementFetcher, '_append_to_file')
    def test_fetch_and_save_updated_files_success(self, mock_append, mock_save, mock_fetch, mock_get_updates, fetcher):
        """测试获取并保存更新文件 - 成功"""
        mock_get_updates.return_value = (
            ['docs/zh/development/test.md', 'docs/zh/development/dev.md'],
            ['docs/zh/development/old.md']
        )
        mock_fetch.side_effect = [
            {'file_path': 'docs/zh/development/test.md', 'file_name': 'test.md', 'content': 'Test'},
            {'file_path': 'docs/zh/development/dev.md', 'file_name': 'dev.md', 'content': 'Dev'}
        ]
        mock_save.side_effect = ['/tmp/test.md', '/tmp/dev.md']
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({'docs_zh_development_test.md': 'id123'}, f)
            mapping_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            fetcher.update_files_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            fetcher.delete_files_path = f.name
        
        try:
            result = fetcher.fetch_and_save_updated_files(mapping_file, '2024-01-01T00:00:00Z')
            
            assert len(result) == 2
        finally:
            os.unlink(mapping_file)

    @patch.object(GitCodeAPIIncrementFetcher, 'get_updated_files_by_commits')
    @patch.object(GitCodeAPIIncrementFetcher, 'fetch_file_content')
    @patch.object(GitCodeAPIIncrementFetcher, 'save_file_to_local')
    def test_fetch_and_save_updated_files_fetch_failure(self, mock_save, mock_fetch, mock_get_updates, fetcher):
        """测试获取并保存更新文件 - 获取失败"""
        mock_get_updates.return_value = (['docs/test.md'], [])
        mock_fetch.return_value = None
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({}, f)
            mapping_file = f.name
        
        try:
            result = fetcher.fetch_and_save_updated_files(mapping_file, '2024-01-01T00:00:00Z')
            assert result == []
        finally:
            os.unlink(mapping_file)

    @patch.object(GitCodeAPIIncrementFetcher, 'get_updated_files_by_commits')
    @patch.object(GitCodeAPIIncrementFetcher, 'fetch_file_content')
    @patch.object(GitCodeAPIIncrementFetcher, 'save_file_to_local')
    def test_fetch_and_save_updated_files_save_failure(self, mock_save, mock_fetch, mock_get_updates, fetcher):
        """测试获取并保存更新文件 - 保存失败"""
        mock_get_updates.return_value = (['docs/test.md'], [])
        mock_fetch.return_value = {'file_path': 'docs/test.md', 'file_name': 'test.md', 'content': 'Test'}
        mock_save.return_value = None
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({}, f)
            mapping_file = f.name
        
        try:
            result = fetcher.fetch_and_save_updated_files(mapping_file, '2024-01-01T00:00:00Z')
            assert result == []
        finally:
            os.unlink(mapping_file)
