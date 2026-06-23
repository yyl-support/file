import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from src.update_lightrag.gitode_full_fetcher import GitCodeFullFetcher


class TestGitCodeFullFetcher:
    """测试 GitCodeFullFetcher 类"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'gitcode': {
                'owner': 'test_owner',
                'repo': 'test_repo',
                'base_path': 'docs/zh/development',
                'skip_dirs': ['images', 'assets']
            },
            'lightrag_paths': {
                'rag_data_dir': '/tmp/test_rag_data',
                'new_rag_files': '/tmp/test_new_rag_files.txt'
            }
        }

    @pytest.fixture
    def fetcher(self, config):
        """创建 GitCodeFullFetcher 实例"""
        return GitCodeFullFetcher(config)

    def test_init(self, fetcher, config):
        """测试初始化"""
        assert fetcher.config == config
        assert fetcher.owner == 'test_owner'
        assert fetcher.repo == 'test_repo'
        assert fetcher.base_path == 'docs/zh/development'
        assert fetcher.branch == 'main'
        assert fetcher.skip_dirs == {'images', 'assets'}

    def test_init_default_values(self):
        """测试默认配置值"""
        config = {
            'lightrag_paths': {
                'rag_data_dir': '/tmp/rag',
                'new_rag_files': '/tmp/new.txt'
            }
        }
        fetcher = GitCodeFullFetcher(config)
        assert fetcher.owner == 'openUBMC'
        assert fetcher.repo == 'docs'
        assert fetcher.base_path == 'docs/zh/development'
        assert fetcher.skip_dirs == {'images'}

    @patch('src.update_lightrag.gitode_full_fetcher.git.Repo')
    def test_clone_or_pull_repo_clone_success(self, mock_repo, fetcher):
        """测试克隆仓库 - 成功"""
        fetcher.local_repo_dir = '/tmp/test_repo'
        
        with patch('os.path.exists', return_value=False):
            result = fetcher.clone_or_pull_repo()
        
        assert result == True
        mock_repo.clone_from.assert_called_once()

    @patch('src.update_lightrag.gitode_full_fetcher.git.Repo')
    def test_clone_or_pull_repo_pull_success(self, mock_repo, fetcher):
        """测试拉取仓库 - 成功"""
        fetcher.local_repo_dir = '/tmp/test_repo'
        
        mock_repo_instance = Mock()
        mock_origin = Mock()
        mock_repo_instance.remotes.origin = mock_origin
        mock_repo.return_value = mock_repo_instance
        
        with patch('os.path.exists', return_value=True):
            result = fetcher.clone_or_pull_repo()
        
        assert result == True
        mock_origin.pull.assert_called_once_with('main')

    @patch('src.update_lightrag.gitode_full_fetcher.git.Repo')
    @patch('src.update_lightrag.gitode_full_fetcher.git.exc')
    def test_clone_or_pull_repo_git_error(self, mock_git_exc, mock_repo, fetcher):
        """测试克隆/拉取仓库 - Git命令错误"""
        fetcher.local_repo_dir = '/tmp/test_repo'
        git_error = Exception('Git error')
        mock_git_exc.GitCommandError = type('GitCommandError', (Exception,), {})
        mock_repo.clone_from.side_effect = git_error
        
        with patch('os.path.exists', return_value=False):
            result = fetcher.clone_or_pull_repo()
        
        assert result == False

    @patch('src.update_lightrag.gitode_full_fetcher.git.Repo')
    def test_clone_or_pull_repo_exception(self, mock_repo, fetcher):
        """测试克隆/拉取仓库 - 其他异常"""
        fetcher.local_repo_dir = '/tmp/test_repo'
        mock_repo.clone_from.side_effect = Exception('Unexpected error')
        
        with patch('os.path.exists', return_value=False):
            result = fetcher.clone_or_pull_repo()
        
        assert result == False

    def test_traverse_markdown_files_success(self, fetcher):
        """测试遍历markdown文件 - 成功"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher.local_repo_dir = tmpdir
            target_dir = 'docs/zh'
            
            os.makedirs(os.path.join(tmpdir, target_dir), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, target_dir, 'images'), exist_ok=True)
            
            with open(os.path.join(tmpdir, target_dir, 'test.md'), 'w') as f:
                f.write('test content')
            with open(os.path.join(tmpdir, target_dir, 'images', 'skip.md'), 'w') as f:
                f.write('skip content')
            with open(os.path.join(tmpdir, target_dir, 'read.txt'), 'w') as f:
                f.write('text content')
            
            result = fetcher.traverse_markdown_files(target_dir)
            
            assert len(result) == 1
            assert result[0]['name'] == 'test.md'

    def test_traverse_markdown_files_dir_not_exist(self, fetcher):
        """测试遍历markdown文件 - 目录不存在"""
        fetcher.local_repo_dir = '/nonexistent/path'
        
        result = fetcher.traverse_markdown_files('docs/zh')
        
        assert result == []

    def test_traverse_markdown_files_multiple_files(self, fetcher):
        """测试遍历markdown文件 - 多个文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher.local_repo_dir = tmpdir
            target_dir = 'docs'
            
            os.makedirs(os.path.join(tmpdir, target_dir), exist_ok=True)
            
            for i in range(3):
                with open(os.path.join(tmpdir, target_dir, f'file{i}.md'), 'w') as f:
                    f.write(f'content {i}')
            
            result = fetcher.traverse_markdown_files(target_dir)
            
            assert len(result) == 3

    def test_read_file_content_success(self, fetcher):
        """测试读取文件内容 - 成功"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.md') as f:
            f.write('Test content')
            test_file = f.name
        
        try:
            result = fetcher.read_file_content(test_file)
            assert result == 'Test content'
        finally:
            os.unlink(test_file)

    def test_read_file_content_unicode_error(self, fetcher):
        """测试读取文件内容 - 编码错误"""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.md') as f:
            f.write(b'\xff\xfe invalid utf-8')
            test_file = f.name
        
        try:
            result = fetcher.read_file_content(test_file)
            assert result is None
        finally:
            os.unlink(test_file)

    def test_read_file_content_file_not_found(self, fetcher):
        """测试读取文件内容 - 文件不存在"""
        result = fetcher.read_file_content('/nonexistent/file.md')
        assert result is None

    def test_get_file_path_docs_path(self, fetcher):
        """测试获取文件路径 - docs路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher.output_dir = tmpdir
            fetcher.local_repo_dir = tmpdir
            
            with open(os.path.join(tmpdir, 'docs_zh_test.md'), 'w') as f:
                f.write('test content')
            
            file_info = {
                'path': 'docs/zh/test.md',
                'name': 'test.md',
                'full_path': os.path.join(tmpdir, 'docs_zh_test.md')
            }
            
            result = fetcher.get_file_path(file_info)
            
            assert result is not None
            assert 'docs_zh_test.md' in result

    def test_get_file_path_non_docs_path(self, fetcher):
        """测试获取文件路径 - 非docs路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher.output_dir = tmpdir
            fetcher.local_repo_dir = tmpdir
            
            with open(os.path.join(tmpdir, 'readme.md'), 'w') as f:
                f.write('readme content')
            
            file_info = {
                'path': 'other/readme.md',
                'name': 'readme.md',
                'full_path': os.path.join(tmpdir, 'readme.md')
            }
            
            result = fetcher.get_file_path(file_info)
            
            assert result is not None
            assert 'readme.md' in result

    @patch('src.update_lightrag.gitode_full_fetcher.os.makedirs', side_effect=PermissionError('Permission denied'))
    @patch('src.update_lightrag.gitode_full_fetcher.os.path.exists', return_value=False)
    def test_get_file_path_makedirs_error(self, mock_exists, mock_makedirs, fetcher):
        """测试获取文件路径 - 创建目录失败"""
        fetcher.output_dir = '/any/path'
        
        file_info = {
            'path': 'docs/test.md',
            'name': 'test.md',
            'full_path': '/tmp/test.md'
        }
        
        result = fetcher.get_file_path(file_info)
        assert result is None

    def test_get_file_path_read_failure(self, fetcher):
        """测试获取文件路径 - 读取失败"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher.output_dir = tmpdir
            
            file_info = {
                'path': 'docs/test.md',
                'name': 'test.md',
                'full_path': '/nonexistent/test.md'
            }
            
            result = fetcher.get_file_path(file_info)
            assert result is None

    @patch.object(GitCodeFullFetcher, 'clone_or_pull_repo')
    @patch.object(GitCodeFullFetcher, 'traverse_markdown_files')
    @patch.object(GitCodeFullFetcher, 'read_file_content')
    @patch.object(GitCodeFullFetcher, 'get_file_path')
    @patch('src.update_lightrag.gitode_full_fetcher.delete_directory')
    def test_fetch_and_save_all_files_clone_failure(self, mock_delete, mock_get_path, mock_read, mock_traverse, mock_clone, fetcher):
        """测试获取并保存所有文件 - 克隆失败"""
        mock_clone.return_value = False
        
        result = fetcher.fetch_and_save_all_files()
        
        assert result == []
        mock_traverse.assert_not_called()

    @patch.object(GitCodeFullFetcher, 'clone_or_pull_repo')
    @patch.object(GitCodeFullFetcher, 'traverse_markdown_files')
    @patch('src.update_lightrag.gitode_full_fetcher.delete_directory')
    def test_fetch_and_save_all_files_no_files(self, mock_delete, mock_traverse, mock_clone, fetcher):
        """测试获取并保存所有文件 - 无文件"""
        mock_clone.return_value = True
        mock_traverse.return_value = []
        fetcher.local_repo_dir = '/tmp/test_repo'
        
        result = fetcher.fetch_and_save_all_files()
        
        assert result == []
        mock_delete.assert_not_called()

    @patch.object(GitCodeFullFetcher, 'clone_or_pull_repo')
    @patch.object(GitCodeFullFetcher, 'traverse_markdown_files')
    @patch.object(GitCodeFullFetcher, 'read_file_content')
    @patch.object(GitCodeFullFetcher, 'get_file_path')
    @patch('src.update_lightrag.gitode_full_fetcher.delete_directory')
    def test_fetch_and_save_all_files_success(self, mock_delete, mock_get_path, mock_read, mock_traverse, mock_clone, fetcher):
        """测试获取并保存所有文件 - 成功"""
        mock_clone.return_value = True
        mock_traverse.return_value = [
            {'path': 'docs/test.md', 'name': 'test.md', 'full_path': '/tmp/test.md'},
            {'path': 'docs/dev.md', 'name': 'dev.md', 'full_path': '/tmp/dev.md'}
        ]
        mock_read.return_value = 'content'
        mock_get_path.side_effect = ['/output/test.md', '/output/dev.md']
        
        result = fetcher.fetch_and_save_all_files()
        
        assert len(result) == 2
        mock_delete.assert_called_once()

    @patch.object(GitCodeFullFetcher, 'clone_or_pull_repo')
    @patch.object(GitCodeFullFetcher, 'traverse_markdown_files')
    @patch.object(GitCodeFullFetcher, 'read_file_content')
    @patch.object(GitCodeFullFetcher, 'get_file_path')
    @patch('src.update_lightrag.gitode_full_fetcher.delete_directory')
    def test_fetch_and_save_all_files_read_failure(self, mock_delete, mock_get_path, mock_read, mock_traverse, mock_clone, fetcher):
        """测试获取并保存所有文件 - 读取失败"""
        mock_clone.return_value = True
        mock_traverse.return_value = [
            {'path': 'docs/test.md', 'name': 'test.md', 'full_path': '/tmp/test.md'}
        ]
        mock_read.return_value = None
        
        result = fetcher.fetch_and_save_all_files()
        
        assert result == []

    @patch.object(GitCodeFullFetcher, 'clone_or_pull_repo')
    @patch.object(GitCodeFullFetcher, 'traverse_markdown_files')
    @patch.object(GitCodeFullFetcher, 'read_file_content')
    @patch.object(GitCodeFullFetcher, 'get_file_path')
    @patch('src.update_lightrag.gitode_full_fetcher.delete_directory')
    def test_fetch_and_save_all_files_get_path_failure(self, mock_delete, mock_get_path, mock_read, mock_traverse, mock_clone, fetcher):
        """测试获取并保存所有文件 - 获取路径失败"""
        mock_clone.return_value = True
        mock_traverse.return_value = [
            {'path': 'docs/test.md', 'name': 'test.md', 'full_path': '/tmp/test.md'}
        ]
        mock_read.return_value = 'content'
        mock_get_path.return_value = None
        
        result = fetcher.fetch_and_save_all_files()
        
        assert result == []
