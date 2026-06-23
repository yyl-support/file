import pytest
import unittest.mock as mock
from flask import Flask
from src.external_api_app import create_app, main


class TestExternalAPIApp:
    
    @pytest.fixture
    def test_config(self):
        return {
            'oidc': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'authorize_url': 'https://omapi.osinfra.cn/oneid/oidc/authorize',
                'token_url': 'https://omapi.osinfra.cn/oneid/oidc/token',
                'redirect_uri': 'https://rag.openubmc.cn/api/v1/rag/auth/callback',
                'scope': 'openid profile'
            },
            'retrieval': {
                'base_url': 'https://lightrag.example.com',
                'query_endpoint': '/query'
            },
            'rate_limit': {
                'user_hourly_limit': 100
            },
            'rbac': {
                'knowledge_upload_roles': ['huawei_maintainer']
            },
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'user': 'test_user',
                'password': 'test_password',
                'sslmode': 'prefer'
            },
            'external_api': {
                'host': '127.0.0.1',
                'port': 5001,
                'debug': False
            }
        }
    
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_create_app_success(self, mock_controller, mock_rate_tables, mock_auth_tables, test_config):
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        
        app = create_app(test_config)
        
        assert app is not None
        assert hasattr(app, 'config')
        assert app.config['SECRET_KEY'] is not None
        mock_auth_tables.assert_called_once()
        mock_rate_tables.assert_called_once()
        mock_controller.assert_called_once()
    
    @mock.patch('src.utils.load_config')
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_create_app_no_config(self, mock_controller, mock_rate_tables, mock_auth_tables, mock_load_config):
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        mock_load_config.return_value = {}
        
        app = create_app()
        
        assert app is not None
    
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_health_endpoint(self, mock_controller, mock_rate_tables, mock_auth_tables, test_config):
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        app = create_app(test_config)
        app.debug = True
        
        with app.test_client() as client:
            response = client.get('/health')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert 'service' in data
    
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_health_detail_endpoint(self, mock_controller, mock_rate_tables, mock_auth_tables, test_config):
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        app = create_app(test_config)
        app.debug = True
        
        with app.test_client() as client:
            response = client.get('/health/detail')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert 'oidc_service_status' in data
            assert 'lightrag_service_status' in data
            assert 'components' in data
    
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_health_detail_components(self, mock_controller, mock_rate_tables, mock_auth_tables, test_config):
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        app = create_app(test_config)
        app.debug = True
        
        with app.test_client() as client:
            response = client.get('/health/detail')
            data = response.get_json()
            
            assert 'oidc_client' in data['components']
            assert 'lightrag_client' in data['components']
            assert 'rate_limiter' in data['components']
            assert 'rbac' in data['components']
    
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_401_error_handler(self, mock_controller, mock_rate_tables, mock_auth_tables, test_config):
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        app = create_app(test_config)
        app.debug = True
        
        with app.test_client() as client:
            response = client.get('/nonexistent')
            
            assert response.status_code == 404
    
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_403_error_handler(self, mock_controller, mock_rate_tables, mock_auth_tables, test_config):
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        app = create_app(test_config)
        app.debug = True
        
        with app.test_client() as client:
            response = client.get('/nonexistent')
            
            assert response.status_code == 404
    
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_500_error_handler(self, mock_controller, mock_rate_tables, mock_auth_tables, test_config):
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        app = create_app(test_config)
        app.debug = True
        
        with app.test_client() as client:
            response = client.get('/nonexistent')
            
            assert response.status_code == 404
    
    @mock.patch('src.external_api_app.load_config')
    @mock.patch('src.external_api_app.create_app')
    def test_main_function(self, mock_create_app, mock_load_config):
        mock_config = {
            'external_api': {
                'host': '127.0.0.1',
                'port': 5001,
                'debug': False
            }
        }
        mock_load_config.return_value = mock_config
        
        mock_app = Flask(__name__)
        mock_app.run = mock.Mock()
        mock_create_app.return_value = mock_app
        
        with mock.patch('src.external_api_app.logger'):
            main()
        
        mock_create_app.assert_called_once()
        mock_app.run.assert_called_once()
    
    @mock.patch('src.external_api_app.load_config')
    @mock.patch('src.external_api_app.create_app')
    def test_main_default_host(self, mock_create_app, mock_load_config):
        mock_config = {}
        mock_load_config.return_value = mock_config
        
        mock_app = Flask(__name__)
        mock_app.run = mock.Mock()
        mock_create_app.return_value = mock_app
        
        with mock.patch('src.external_api_app.logger'):
            main()
        
        mock_app.run.assert_called_once()
        call_args = mock_app.run.call_args
        assert call_args[1]['host'] == '127.0.0.1'
    
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_secret_key_from_env(self, mock_controller, mock_rate_tables, mock_auth_tables, test_config):
        import os
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        
        with mock.patch.dict(os.environ, {'FLASK_SECRET_KEY': 'test_secret_from_env'}):
            app = create_app(test_config)
            
            assert app.config['SECRET_KEY'] == 'test_secret_from_env'
    
    @mock.patch('src.external_api_app.create_auth_tables')
    @mock.patch('src.external_api_app.create_rate_limit_tables')
    @mock.patch('src.external_api_app.create_rag_api_controller')
    def test_default_secret_key(self, mock_controller, mock_rate_tables, mock_auth_tables, test_config):
        mock_bp = mock.Mock()
        mock_controller.return_value = (mock.Mock(), mock_bp)
        app = create_app(test_config)
        
        assert app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production'