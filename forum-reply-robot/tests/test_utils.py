import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, Mock
from src.utils import (
    load_config,
    delete_directory,
    clear_directory,
    ensure_database_exists,
    init_db_connection_pool,
    get_db_connection_from_pool,
    release_db_connection_to_pool,
    close_db_connection_pool
)


class TestEnsureDatabaseExists:
    """测试 ensure_database_exists 函数"""

    def test_ensure_database_exists_missing_database_field(self):
        """测试数据库配置缺少 database 字段"""
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'test_user',
            'password': 'test_password'
        }
        
        result = ensure_database_exists(db_config)
        assert result is False

    @patch('psycopg2.connect')
    def test_ensure_database_exists_already_exists(self, mock_connect):
        """测试数据库已存在"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.autocommit = True
        mock_cursor.fetchone.return_value = (1,)
        
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'existing_db',
            'user': 'test_user',
            'password': 'test_password',
            'sslmode': 'prefer'
        }
        
        result = ensure_database_exists(db_config)
        assert result is True
        mock_connect.assert_called()
        mock_cursor.execute.assert_called()

    @patch('psycopg2.connect')
    def test_ensure_database_exists_creates_database(self, mock_connect):
        """测试数据库不存在时自动创建"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.autocommit = True
        mock_cursor.fetchone.return_value = None
        
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'new_db',
            'user': 'test_user',
            'password': 'test_password',
            'sslmode': 'prefer'
        }
        
        result = ensure_database_exists(db_config)
        assert result is True
        mock_connect.assert_called()

    @patch('psycopg2.connect')
    def test_ensure_database_exists_connection_failure(self, mock_connect):
        """测试数据库连接失败"""
        mock_connect.side_effect = Exception('Connection failed')
        
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_password',
            'sslmode': 'prefer'
        }
        
        result = ensure_database_exists(db_config)
        assert result is False


class TestLoadConfig:
    """测试 load_config 函数"""

    def test_load_config_success(self):
        """测试成功加载配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            test_config = {
                'api': {
                    'base_url': 'http://test.com',
                    'api_key': 'test_key'
                },
                'database': {
                    'host': 'localhost',
                    'port': 5432
                }
            }
            yaml.dump(test_config, f)
            config_file = f.name

        try:
            config = load_config(config_file)
            assert config is not None
            assert config['api']['base_url'] == 'http://test.com'
            assert config['api']['api_key'] == 'test_key'
            assert config['database']['host'] == 'localhost'
            assert config['database']['port'] == 5432
        finally:
            os.unlink(config_file)

    def test_load_config_file_not_found(self):
        """测试配置文件不存在的情况"""
        config = load_config('nonexistent_config.yaml')
        assert config == {}

    def test_load_config_invalid_yaml(self):
        """测试无效的 YAML 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content:')
            config_file = f.name

        try:
            config = load_config(config_file)
            assert config == {}
        finally:
            os.unlink(config_file)

    def test_load_config_empty_file(self):
        """测试空配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_file = f.name

        try:
            config = load_config(config_file)
            assert config is None
        finally:
            os.unlink(config_file)


class TestDeleteDirectory:
    """测试 delete_directory 函数"""

    def test_delete_directory_success(self):
        """测试删除目录 - 成功"""
        with tempfile.TemporaryDirectory() as parent_dir:
            test_dir = os.path.join(parent_dir, 'test_delete_dir')
            os.makedirs(test_dir)
            
            with open(os.path.join(test_dir, 'file1.txt'), 'w') as f:
                f.write('content1')
            os.makedirs(os.path.join(test_dir, 'subdir'))
            with open(os.path.join(test_dir, 'subdir', 'file2.txt'), 'w') as f:
                f.write('content2')
            
            delete_directory(test_dir)
            
            assert not os.path.exists(test_dir)

    def test_delete_directory_nonexistent(self):
        """测试删除目录 - 目录不存在"""
        nonexistent_dir = '/tmp/nonexistent_directory_12345'
        
        if os.path.exists(nonexistent_dir):
            os.rmdir(nonexistent_dir)
        
        delete_directory(nonexistent_dir)
        
        assert not os.path.exists(nonexistent_dir)

    def test_delete_directory_with_nested_structure(self):
        """测试删除目录 - 嵌套结构"""
        with tempfile.TemporaryDirectory() as parent_dir:
            test_dir = os.path.join(parent_dir, 'nested_dir')
            os.makedirs(os.path.join(test_dir, 'level1', 'level2', 'level3'))
            
            delete_directory(test_dir)
            
            assert not os.path.exists(test_dir)

    @patch('src.utils.shutil.rmtree')
    def test_delete_directory_error(self, mock_rmtree):
        """测试删除目录 - 删除失败"""
        mock_rmtree.side_effect = PermissionError('Permission denied')
        test_dir = '/tmp/delete_directory_error'

        with patch('src.utils.os.path.exists', return_value=True):
            delete_directory(test_dir)

        mock_rmtree.assert_called_once_with(test_dir)


class TestClearDirectory:
    """测试 clear_directory 函数"""

    def test_clear_directory_success(self):
        """测试清空目录 - 成功"""
        with tempfile.TemporaryDirectory() as test_dir:
            with open(os.path.join(test_dir, 'file1.txt'), 'w') as f:
                f.write('content1')
            with open(os.path.join(test_dir, 'file2.txt'), 'w') as f:
                f.write('content2')
            
            clear_directory(test_dir, '')
            
            assert os.path.exists(test_dir)
            assert len(os.listdir(test_dir)) == 0

    def test_clear_directory_with_ignore_file(self):
        """测试清空目录 - 忽略文件"""
        with tempfile.TemporaryDirectory() as test_dir:
            with open(os.path.join(test_dir, 'ignore.txt'), 'w') as f:
                f.write('keep this')
            with open(os.path.join(test_dir, 'delete.txt'), 'w') as f:
                f.write('delete this')
            
            clear_directory(test_dir, 'ignore.txt')
            
            assert os.path.exists(test_dir)
            assert 'ignore.txt' in os.listdir(test_dir)
            assert 'delete.txt' not in os.listdir(test_dir)

    def test_clear_directory_nonexistent(self):
        """测试清空目录 - 目录不存在"""
        nonexistent_dir = '/tmp/nonexistent_clear_dir_12345'
        
        if os.path.exists(nonexistent_dir):
            import shutil
            shutil.rmtree(nonexistent_dir)
        
        clear_directory(nonexistent_dir, None)
        
        assert not os.path.exists(nonexistent_dir)

    def test_clear_directory_with_subdirectories(self):
        """测试清空目录 - 包含子目录"""
        with tempfile.TemporaryDirectory() as test_dir:
            subdir = os.path.join(test_dir, 'subdir')
            os.makedirs(subdir)
            with open(os.path.join(subdir, 'file.txt'), 'w') as f:
                f.write('content')
            
            clear_directory(test_dir, '')
            
            assert os.path.exists(test_dir)
            assert os.path.exists(subdir)
            assert len(os.listdir(subdir)) == 0


class TestDBConnectionPool:
    """测试数据库连接池功能"""

    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_init_db_connection_pool_success(self, mock_pool_class):
        """测试连接池初始化成功"""
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool
        
        import src.utils as utils
        utils.db_connection_pool = None
        
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_password',
            'sslmode': 'prefer'
        }
        
        result = init_db_connection_pool(db_config)
        assert result is True
        mock_pool_class.assert_called_once()

    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_init_db_connection_pool_failure(self, mock_pool_class):
        """测试连接池初始化失败"""
        mock_pool_class.side_effect = Exception('Connection failed')
        
        import src.utils as utils
        utils.db_connection_pool = None
        
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_password'
        }
        
        result = init_db_connection_pool(db_config)
        assert result is False

    def test_get_db_connection_from_pool_success(self):
        """测试从连接池获取连接成功"""
        import src.utils as utils
        
        mock_pool = Mock()
        mock_conn = Mock()
        mock_pool.getconn.return_value = mock_conn
        utils.db_connection_pool = mock_pool
        
        result = get_db_connection_from_pool()
        assert result == mock_conn
        mock_pool.getconn.assert_called_once()
        
        utils.db_connection_pool = None

    def test_get_db_connection_from_pool_none(self):
        """测试连接池为 None"""
        import src.utils as utils
        utils.db_connection_pool = None
        
        result = get_db_connection_from_pool()
        assert result is None

    def test_get_db_connection_from_pool_failure(self):
        """测试从连接池获取连接失败"""
        import src.utils as utils
        
        mock_pool = Mock()
        mock_pool.getconn.side_effect = Exception('Pool error')
        utils.db_connection_pool = mock_pool
        
        result = get_db_connection_from_pool()
        assert result is None
        
        utils.db_connection_pool = None

    def test_release_db_connection_to_pool_success(self):
        """测试归还连接到连接池成功"""
        import src.utils as utils
        
        mock_pool = Mock()
        mock_conn = Mock()
        utils.db_connection_pool = mock_pool
        
        release_db_connection_to_pool(mock_conn)
        mock_pool.putconn.assert_called_once_with(mock_conn)
        
        utils.db_connection_pool = None

    def test_release_db_connection_to_pool_none_pool(self):
        """测试连接池为 None 时归还连接"""
        import src.utils as utils
        utils.db_connection_pool = None
        
        mock_conn = Mock()
        release_db_connection_to_pool(mock_conn)
        
    def test_release_db_connection_to_pool_close_fallback(self):
        """测试归还连接失败时关闭连接"""
        import src.utils as utils
        
        mock_pool = Mock()
        mock_pool.putconn.side_effect = Exception('Putconn failed')
        mock_conn = Mock()
        utils.db_connection_pool = mock_pool
        
        release_db_connection_to_pool(mock_conn)
        
        mock_pool.putconn.assert_called_once()
        mock_conn.close.assert_called_once()
        
        utils.db_connection_pool = None

    def test_close_db_connection_pool_success(self):
        """测试关闭连接池成功"""
        import src.utils as utils
        
        mock_pool = Mock()
        utils.db_connection_pool = mock_pool
        
        close_db_connection_pool()
        
        mock_pool.closeall.assert_called_once()
        assert utils.db_connection_pool is None

    def test_close_db_connection_pool_failure(self):
        """测试关闭连接池失败"""
        import src.utils as utils
        
        mock_pool = Mock()
        mock_pool.closeall.side_effect = Exception('Close failed')
        utils.db_connection_pool = mock_pool
        
        close_db_connection_pool()
        
        mock_pool.closeall.assert_called_once()
        assert utils.db_connection_pool is None
