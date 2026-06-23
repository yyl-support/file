import pytest
import unittest.mock as mock
from flask import Flask, g, request
from datetime import datetime, timedelta
from src.ForumBot.auth_middleware import AuthMiddleware, create_tables
import json


class TestAuthMiddleware:
    
    @pytest.fixture
    def auth_config(self):
        return {
            'oidc': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'authorize_url': 'https://omapi.osinfra.cn/oneid/oidc/authorize',
                'token_url': 'https://omapi.osinfra.cn/oneid/oidc/token',
                'redirect_uri': 'https://rag.openubmc.cn/api/v1/rag/auth/callback',
                'scope': 'openid profile'
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
    def auth_middleware(self, auth_config):
        return AuthMiddleware(auth_config)
    
    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test_secret_key'
        return app
    
    def test_extract_token_with_bearer(self, auth_middleware, app):
        with app.test_request_context(
            '/test',
            headers={'Authorization': 'Bearer test_token_123'}
        ):
            token = auth_middleware.extract_token()
            assert token == 'test_token_123'
    
    def test_extract_token_without_bearer(self, auth_middleware, app):
        with app.test_request_context(
            '/test',
            headers={'Authorization': 'Basic test_token'}
        ):
            token = auth_middleware.extract_token()
            assert token is None
    
    def test_extract_token_no_auth_header(self, auth_middleware, app):
        with app.test_request_context('/test'):
            token = auth_middleware.extract_token()
            assert token is None
    
    def test_extract_token_empty_auth_header(self, auth_middleware, app):
        with app.test_request_context('/test', headers={'Authorization': ''}):
            token = auth_middleware.extract_token()
            assert token is None
    
    @mock.patch('src.ForumBot.auth_middleware.AuthMiddleware.get_db_connection')
    def test_validate_session_success(self, mock_get_conn, auth_middleware):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        expires_at = datetime.utcnow() + timedelta(hours=1)
        roles_json = json.dumps(['huawei_maintainer', 'robot_service'])
        mock_cursor.fetchone.return_value = (
            'test_user',
            'test_token',
            'test_refresh',
            expires_at,
            datetime.utcnow(),
            roles_json
        )
        
        with mock.patch('src.utils.release_db_connection_to_pool'):
            result = auth_middleware.validate_session('test_token')
            
            assert result is not None
            assert result['user_id'] == 'test_user'
            assert result['roles'] == ['huawei_maintainer', 'robot_service']
    
    @mock.patch('src.ForumBot.auth_middleware.AuthMiddleware.get_db_connection')
    def test_validate_session_expired_token(self, mock_get_conn, auth_middleware):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        expires_at = datetime.utcnow() - timedelta(hours=1)
        mock_cursor.fetchone.return_value = (
            'test_user',
            'test_token',
            'test_refresh',
            expires_at,
            datetime.utcnow(),
            None
        )
        
        with mock.patch('src.utils.release_db_connection_to_pool'):
            result = auth_middleware.validate_session('test_token')
            assert result is None
    
    @mock.patch('src.ForumBot.auth_middleware.AuthMiddleware.get_db_connection')
    def test_validate_session_no_result(self, mock_get_conn, auth_middleware):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        with mock.patch('src.utils.release_db_connection_to_pool'):
            result = auth_middleware.validate_session('invalid_token')
            assert result is None
    
    def test_validate_session_empty_token(self, auth_middleware):
        result = auth_middleware.validate_session(None)
        assert result is None
    
    @mock.patch('src.ForumBot.auth_middleware.AuthMiddleware.get_db_connection')
    def test_validate_session_invalid_roles_json(self, mock_get_conn, auth_middleware):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_cursor.fetchone.return_value = (
            'test_user',
            'test_token',
            'test_refresh',
            expires_at,
            datetime.utcnow(),
            'invalid_json'
        )
        
        with mock.patch('src.utils.release_db_connection_to_pool'):
            result = auth_middleware.validate_session('test_token')
            assert result is not None
            assert result['roles'] == []
    
    @mock.patch('src.ForumBot.auth_middleware.get_db_connection_from_pool')
    def test_get_db_connection_from_pool_success(self, mock_get_pool, auth_middleware):
        mock_conn = mock.Mock()
        mock_get_pool.return_value = mock_conn
        
        with mock.patch('src.utils.release_db_connection_to_pool'):
            result = auth_middleware.get_db_connection()
        assert result == mock_conn
    
    @mock.patch('psycopg2.connect')
    @mock.patch('src.ForumBot.auth_middleware.get_db_connection_from_pool')
    def test_get_db_connection_fallback(self, mock_get_pool, mock_connect, auth_middleware):
        mock_get_pool.return_value = None
        mock_conn = mock.Mock()
        mock_connect.return_value = mock_conn
        
        with mock.patch('src.ForumBot.auth_middleware.release_db_connection_to_pool'):
            result = auth_middleware.get_db_connection()
        assert result == mock_conn
        mock_connect.assert_called_once()
    
    @mock.patch('psycopg2.connect')
    @mock.patch('src.ForumBot.auth_middleware.get_db_connection_from_pool')
    def test_get_db_connection_failure(self, mock_get_pool, mock_connect, auth_middleware):
        mock_get_pool.return_value = None
        mock_connect.side_effect = Exception('Connection failed')
        
        with mock.patch('src.utils.release_db_connection_to_pool'):
            result = auth_middleware.get_db_connection()
        assert result is None
    
    def test_require_auth_decorator_success(self, auth_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = auth_middleware.require_auth(test_func)
        
        with app.test_request_context(
            '/test',
            headers={'Authorization': 'Bearer test_token'}
        ):
            with mock.patch.object(auth_middleware, 'validate_session', return_value={
                'user_id': 'test_user',
                'access_token': 'test_token',
                'roles': []
            }):
                g.current_user = {'user_id': 'test_user', 'roles': []}
                result = decorated()
                
                assert result['status'] == 'success'
    
    def test_require_auth_decorator_no_token(self, auth_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = auth_middleware.require_auth(test_func)
        
        with app.test_request_context('/test'):
            result = decorated()
            
            assert result[1] == 401
    
    def test_require_auth_decorator_invalid_token(self, auth_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = auth_middleware.require_auth(test_func)
        
        with app.test_request_context(
            '/test',
            headers={'Authorization': 'Bearer invalid_token'}
        ):
            with mock.patch.object(auth_middleware, 'validate_session', return_value=None):
                result = decorated()
                
                assert result[1] == 401
    
    @mock.patch('src.ForumBot.auth_middleware.ensure_database_exists', return_value=True)
    @mock.patch('psycopg2.connect')
    def test_create_tables(self, mock_connect, mock_ensure):
        mock_conn = mock.Mock()
        mock_cursor = mock.Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.autocommit = True
        
        config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'user': 'test_user',
                'password': 'test_password',
                'sslmode': 'prefer'
            }
        }
        
        create_tables(config)
        
        mock_cursor.execute.assert_called()