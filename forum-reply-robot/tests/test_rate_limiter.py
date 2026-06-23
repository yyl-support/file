import pytest
import unittest.mock as mock
from src.ForumBot.rate_limiter import RateLimiter, create_tables
from datetime import datetime, timedelta
from flask import Flask, g


class TestRateLimiter:
    
    @pytest.fixture
    def rate_limit_config(self):
        return {
            'rate_limit': {
                'user_hourly_limit': 100,
                'window_seconds': 3600
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'user': 'test_user',
                'password': 'test_password',
                'sslmode': 'prefer'
            }
        }
    
    @pytest.fixture
    def rate_limiter(self, rate_limit_config):
        return RateLimiter(rate_limit_config)
    
    @pytest.fixture
    def mock_db_connection(self):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor
    
    def test_rate_limiter_initialization(self, rate_limiter):
        assert rate_limiter.hourly_limit == 100
        assert rate_limiter.window_seconds == 3600
    
    @mock.patch('src.ForumBot.rate_limiter.release_db_connection_to_pool')
    @mock.patch('src.ForumBot.rate_limiter.get_db_connection_from_pool')
    def test_check_rate_limit_first_request(self, mock_get_pool, mock_release, rate_limiter):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_pool.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = None
        
        user_id = 'test_user'
        result = rate_limiter.check_rate_limit(user_id)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @mock.patch('src.ForumBot.rate_limiter.release_db_connection_to_pool')
    @mock.patch('src.ForumBot.rate_limiter.get_db_connection_from_pool')
    def test_check_rate_limit_within_limit(self, mock_get_pool, mock_release, rate_limiter):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_pool.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=30)
        
        mock_cursor.fetchone.return_value = (50, window_start, now)
        
        user_id = 'test_user'
        result = rate_limiter.check_rate_limit(user_id)
        
        assert result is True
    
    @mock.patch('src.ForumBot.rate_limiter.release_db_connection_to_pool')
    @mock.patch('src.ForumBot.rate_limiter.get_db_connection_from_pool')
    def test_check_rate_limit_exceeded(self, mock_get_pool, mock_release, rate_limiter):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_pool.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=30)
        
        mock_cursor.fetchone.return_value = (101, window_start, now)
        
        user_id = 'test_user'
        result = rate_limiter.check_rate_limit(user_id)
        
        assert result is False
    
    @mock.patch('src.ForumBot.rate_limiter.release_db_connection_to_pool')
    @mock.patch('src.ForumBot.rate_limiter.get_db_connection_from_pool')
    def test_check_rate_limit_window_expired(self, mock_get_pool, mock_release, rate_limiter):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_pool.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        now = datetime.utcnow()
        old_window_start = now - timedelta(hours=2)
        
        mock_cursor.fetchone.return_value = (100, old_window_start, now)
        
        user_id = 'test_user'
        result = rate_limiter.check_rate_limit(user_id)
        
        assert result is True
        mock_cursor.execute.assert_called()
    
    @mock.patch('src.ForumBot.rate_limiter.release_db_connection_to_pool')
    @mock.patch('src.ForumBot.rate_limiter.get_db_connection_from_pool')
    def test_get_retry_after(self, mock_get_pool, mock_release, rate_limiter):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_pool.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=30)
        
        mock_cursor.fetchone.return_value = (window_start, now)
        
        user_id = 'test_user'
        retry_after = rate_limiter.get_retry_after(user_id)
        
        assert retry_after >= 0
        assert retry_after <= 3600
    
    @mock.patch('src.ForumBot.rate_limiter.release_db_connection_to_pool')
    @mock.patch('src.ForumBot.rate_limiter.get_db_connection_from_pool')
    def test_get_retry_after_no_record(self, mock_get_pool, mock_release, rate_limiter):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_pool.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = None
        
        user_id = 'test_user'
        retry_after = rate_limiter.get_retry_after(user_id)
        
        assert retry_after == 0
    
    def test_rate_limit_decorator_success(self, rate_limiter):
        app = Flask(__name__)
        
        with app.test_request_context():
            g.current_user = {'user_id': 'test_user'}
            
            with mock.patch.object(rate_limiter, 'check_rate_limit', return_value=True):
                @rate_limiter.rate_limit
                def test_func():
                    return 'success'
                
                result = test_func()
                assert result == 'success'
    
    def test_rate_limit_decorator_exceeded(self, rate_limiter):
        app = Flask(__name__)
        
        with app.test_request_context():
            g.current_user = {'user_id': 'test_user'}
            
            with mock.patch.object(rate_limiter, 'check_rate_limit', return_value=False):
                with mock.patch.object(rate_limiter, 'get_retry_after', return_value=1800):
                    @rate_limiter.rate_limit
                    def test_func():
                        return 'success'
                    
                    result = test_func()
                    assert result.status_code == 429
                    assert 'Retry-After' in result.headers
    
    @mock.patch('src.ForumBot.rate_limiter.ensure_database_exists', return_value=True)
    @mock.patch('psycopg2.connect')
    def test_create_tables(self, mock_connect, mock_ensure, rate_limit_config):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        create_tables(rate_limit_config)
        
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @mock.patch('src.ForumBot.rate_limiter.release_db_connection_to_pool')
    @mock.patch('psycopg2.connect')
    @mock.patch('src.ForumBot.rate_limiter.get_db_connection_from_pool', return_value=None)
    def test_check_rate_limit_db_connection_failure(self, mock_get_pool, mock_connect, mock_release, rate_limiter):
        mock_connect.side_effect = Exception("Connection failed")
        
        user_id = 'test_user'
        result = rate_limiter.check_rate_limit(user_id)
        
        assert result is True
    
    def test_rate_limit_decorator_no_user_info(self, rate_limiter):
        app = Flask(__name__)
        
        with app.test_request_context(headers={'X-User-ID': 'anonymous'}):
            with mock.patch.object(rate_limiter, 'check_rate_limit', return_value=True):
                @rate_limiter.rate_limit
                def test_func():
                    return 'success'
                
                result = test_func()
                assert result == 'success'