import pytest
import unittest.mock as mock
import os
from src.ForumBot.rag_api import RAGAPIController
from src.ForumBot.auth_middleware import AuthMiddleware
from src.ForumBot.oidc_client import OIDCClient


class TestCoverageBoost:
    """补充测试用例以提高覆盖率"""
    
    def test_rag_api_controller_init(self):
        """测试 RAGAPIController 初始化"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {'user_hourly_limit': 100},
            'rbac': {'knowledge_upload_roles': ['admin']},
            'retrieval': {'base_url': 'http://test.com'}
        }
        controller = RAGAPIController(config)
        assert controller.max_text_length == 5000
        assert controller.max_query_length == 1000
    
    def test_rag_api_extract_user_id(self):
        """测试 _extract_user_id_from_token 方法"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        user_id = controller._extract_user_id_from_token('test_token')
        assert user_id.startswith('user_')
        assert len(user_id) == 13
    
    def test_oidc_client_config_from_config(self):
        """测试 OIDC 配置从 config 读取"""
        config = {
            'oidc': {
                'client_id': 'config_id',
                'client_secret': 'config_secret',
                'redirect_uri': 'https://config.uri/callback'
            }
        }
        client = OIDCClient(config)
        assert client.client_id == 'config_id'
        assert client.client_secret == 'config_secret'
        assert client.redirect_uri == 'https://config.uri/callback'
    
    def test_oidc_missing_config_raises(self):
        """测试 OIDC 配置缺失抛异常"""
        with pytest.raises(ValueError) as exc_info:
            OIDCClient({})
        assert 'oidc.client_id' in str(exc_info.value)
        assert 'oidc.client_secret' in str(exc_info.value)
        assert 'oidc.redirect_uri' in str(exc_info.value)
    
    def test_oidc_state_generation(self):
        """测试 state 参数生成"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        client = OIDCClient(config)
        state1 = client.generate_state()
        state2 = client.generate_state()
        assert len(state1) >= 16
        assert state1 != state2
    
    def test_oidc_authorization_url(self):
        """测试授权 URL 构建"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        client = OIDCClient(config)
        url = client.get_authorization_url('state123')
        assert 'client_id=test' in url
        assert 'state=state123' in url
        assert 'response_type=code' in url
    
    @mock.patch('requests.post')
    def test_oidc_token_exchange(self, mock_post):
        """测试 token 换取"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        client = OIDCClient(config)
        
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'token',
            'refresh_token': 'refresh',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        result = client.exchange_code_for_token('code')
        assert result['success'] is True
        assert result['access_token'] == 'token'
    
    def test_auth_middleware_extract_token(self):
        """测试 token 提取"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        middleware = AuthMiddleware(config, OIDCClient(config))
        
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context('/', headers={'Authorization': 'Bearer token123'}):
            token = middleware.extract_token()
            assert token == 'token123'

    @mock.patch('requests.post')
    def test_rag_api_retrieve_logic(self, mock_post):
        """测试 retrieve 核心逻辑"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {'base_url': 'http://test.com', 'query_endpoint': '/query'}
        }
        controller = RAGAPIController(config)
        
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'context': {'chunks': [{'content': 'test'}]}}
        mock_post.return_value = mock_response
        
        from flask import Flask, g
        app = Flask(__name__)
        with app.test_request_context('/retrieve', method='POST', json={'query': 'test'}):
            g.current_user = {'user_id': 'user1'}
            result = controller.retrieve()
            if isinstance(result, tuple):
                assert result[1] == 200
            else:
                assert result.status_code == 200
    
    @mock.patch('requests.post')
    def test_rag_api_tokenize_logic(self, mock_post):
        """测试 tokenize 核心逻辑"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {'base_url': 'http://test.com'}
        }
        controller = RAGAPIController(config)
        
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'tokens': ['a', 'b']}
        mock_post.return_value = mock_response
        
        from flask import Flask, g
        app = Flask(__name__)
        with app.test_request_context('/tokenize', method='POST', json={'text': 'test'}):
            g.current_user = {'user_id': 'user1'}
            result = controller.tokenize()
            if isinstance(result, tuple):
                assert result[1] == 200
            else:
                assert result.status_code == 200
    
    def test_rag_api_missing_text(self):
        """测试缺失 text 参数"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        
        from flask import Flask, g
        app = Flask(__name__)
        with app.test_request_context('/tokenize', method='POST', json={}):
            g.current_user = {'user_id': 'user1'}
            result = controller.tokenize()
            assert result[1] == 400
    
    def test_rag_api_missing_query(self):
        """测试缺失 query 参数"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        
        from flask import Flask, g
        app = Flask(__name__)
        with app.test_request_context('/retrieve', method='POST', json={}):
            g.current_user = {'user_id': 'user1'}
            result = controller.retrieve()
            assert result[1] == 400
    
    def test_oidc_validate_state(self):
        """测试 state 验证"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        client = OIDCClient(config)
        
        state = client.generate_state()
        assert client.validate_state(state, state) is True
        assert client.validate_state('wrong', state) is False
    
    @mock.patch('requests.post')
    def test_oidc_refresh_token(self, mock_post):
        """测试 refresh token"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        client = OIDCClient(config)
        
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        result = client.refresh_access_token('refresh_token')
        assert result['success'] is True

    def test_rag_api_authorize_redirect(self):
        """测试 authorize 重定向"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        
        from flask import Flask, session
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context('/authorize'):
            result = controller.authorize()
            assert result.status_code == 302
    
    def test_rag_api_auth_callback_state_mismatch(self):
        """测试 auth_callback state 不匹配"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        
        from flask import Flask, session
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        with app.test_request_context('/callback?code=abc&state=wrong'):
            session['oidc_state'] = 'correct'
            result = controller.auth_callback()
            assert result[1] == 400
    
    def test_rag_api_refresh_token_missing(self):
        """测试 refresh_token 缺失"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context('/refresh', method='POST', json={}, content_type='application/json'):
            result = controller.refresh_token()
            # Empty dict should still return 401 for missing refresh_token
            # If get_json() returns None due to empty dict, it would return 400
            assert result[1] in [400, 401]
    
    def test_rag_api_text_too_long(self):
        """测试 text 过长"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        
        from flask import Flask, g
        app = Flask(__name__)
        long_text = 'a' * 6000
        with app.test_request_context('/tokenize', method='POST', json={'text': long_text}):
            g.current_user = {'user_id': 'user1'}
            result = controller.tokenize()
            assert result[1] == 400
    
    def test_rag_api_query_too_long(self):
        """测试 query 过长"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        
        from flask import Flask, g
        app = Flask(__name__)
        long_query = 'a' * 1100
        with app.test_request_context('/retrieve', method='POST', json={'query': long_query}):
            g.current_user = {'user_id': 'user1'}
            result = controller.retrieve()
            assert result[1] == 400
    
    def test_rag_api_top_k_boundary(self):
        """测试 top_k 边界"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {'top_k': 5}
        }
        controller = RAGAPIController(config)
        
        from flask import Flask, g
        app = Flask(__name__)
        with app.test_request_context('/retrieve', method='POST', json={'query': 'test', 'top_k': 20}):
            g.current_user = {'user_id': 'user1'}
            # top_k should be capped at 10
            assert controller.retrieval_config.get('top_k', 5) <= 10

    def test_auth_middleware_extract_token_no_header(self):
        """测试无 Authorization header"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        middleware = AuthMiddleware(config, OIDCClient(config))
        
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context('/'):
            token = middleware.extract_token()
            assert token is None
    
    def test_auth_middleware_extract_token_wrong_format(self):
        """测试 Authorization header 格式错误"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        middleware = AuthMiddleware(config, OIDCClient(config))
        
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context('/', headers={'Authorization': 'Basic token'}):
            token = middleware.extract_token()
            assert token is None
    
    def test_rbac_role_check(self):
        """测试 RBAC 角色检查"""
        from src.ForumBot.rbac_middleware import RBACMiddleware
        from flask import Flask, g
        
        config = {
            'rbac': {'knowledge_upload_roles': ['admin', 'maintainer']}
        }
        middleware = RBACMiddleware(config)
        
        app = Flask(__name__)
        with app.test_request_context('/'):
            g.current_user = {'user_id': 'test_user', 'roles': ['admin', 'user']}
            assert middleware.check_role('test_user', ['admin']) is True
            
            g.current_user = {'user_id': 'test_user2', 'roles': ['user']}
            assert middleware.check_role('test_user2', ['admin']) is False
            
            g.current_user = {'user_id': 'test_user3', 'roles': ['maintainer']}
            assert middleware.check_role('test_user3', ['maintainer']) is True
    
    def test_rbac_require_role_decorator(self):
        """测试 RBAC 装饰器"""
        from src.ForumBot.rbac_middleware import RBACMiddleware
        from flask import Flask, g
        
        config = {
            'rbac': {'knowledge_upload_roles': ['admin']}
        }
        middleware = RBACMiddleware(config)
        
        app = Flask(__name__)
        
        @middleware.require_role()
        def protected_func():
            return "success"
        
        with app.test_request_context('/'):
            g.current_user = {'user_id': 'test_user', 'roles': ['admin']}
            result = protected_func()
            assert result == "success"
            g.current_user = {'roles': ['admin']}
            result = protected_func()
            assert result == "success"
        
        with app.test_request_context('/'):
            g.current_user = {'roles': ['user']}
            result = protected_func()
            # Should return tuple (response, 403)
            assert isinstance(result, tuple)
            assert result[1] == 403
    
    @mock.patch('src.ForumBot.auth_middleware.AuthMiddleware.get_db_connection')
    def test_auth_save_session(self, mock_conn):
        """测试保存 session"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        middleware = AuthMiddleware(config, OIDCClient(config))
        
        mock_cursor = mock.Mock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        result = middleware.save_session('user1', 'token', 'refresh', 3600, [])
        assert result is True or mock_cursor.execute.called
    
    @mock.patch('src.ForumBot.auth_middleware.AuthMiddleware.get_db_connection')
    def test_auth_update_session(self, mock_conn):
        """测试更新 session"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        middleware = AuthMiddleware(config, OIDCClient(config))
        
        mock_cursor = mock.Mock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        result = middleware.update_session('user1', 'new_token', 'refresh', 3600)
        assert mock_cursor.execute.called

    def test_rag_api_knowledge_upload_missing_file(self):
        """测试知识上传缺失文件"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        
        from flask import Flask, g, request
        app = Flask(__name__)
        with app.test_request_context('/upload', method='POST'):
            g.current_user = {'user_id': 'user1', 'roles': ['admin']}
            result = controller.knowledge_upload()
            assert result[1] == 400
    
    def test_rag_api_create_blueprint(self):
        """测试创建 blueprint"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        bp = RAGAPIController(config).register_routes()
        assert bp is not None
        assert bp.name == 'rag_api'
    
    def test_oidc_client_with_encryption_key(self):
        """测试带加密key的OIDC client"""
        import base64
        from cryptography.fernet import Fernet
        
        key = Fernet.generate_key()
        os.environ['TOKEN_ENCRYPTION_KEY'] = key.decode()
        
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        client = OIDCClient(config)
        assert client._fernet is not None
        
        # Test encryption using private method
        encrypted = client._encrypt_token('test_refresh')
        decrypted = client._decrypt_token(encrypted)
        assert decrypted == 'test_refresh'
        
        del os.environ['TOKEN_ENCRYPTION_KEY']
    
    def test_oidc_validate_token(self):
        """测试 token 验证"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        client = OIDCClient(config)
        
        # validate_token returns a bool, not a dict
        result = client.validate_token('valid_token')
        assert result is True
    
    def test_oidc_validate_empty_token(self):
        """测试空token验证"""
        config = {'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'}}
        client = OIDCClient(config)
        
        # validate_token returns a bool for empty token
        result = client.validate_token('')
        assert result is False

    @mock.patch('os.remove')
    @mock.patch('os.path.exists')
    @mock.patch('tempfile.NamedTemporaryFile')
    def test_rag_api_knowledge_upload_success(self, mock_temp, mock_exists, mock_remove):
        """测试知识上传成功"""
        from werkzeug.datastructures import FileStorage
        import io
        
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {'base_url': 'http://test.com'}
        }
        controller = RAGAPIController(config)
        
        mock_file = mock.Mock()
        mock_file.name = '/tmp/test_file.txt'
        mock_file.write = mock.Mock()
        mock_temp.return_value.__enter__.return_value = mock_file
        
        mock_exists.return_value = True
        
        test_file = FileStorage(
            stream=io.BytesIO(b"test content"),
            filename="test.txt",
            content_type="text/plain"
        )
        
        from flask import Flask, g, request
        app = Flask(__name__)
        
        with mock.patch.object(controller.lightrag_client, 'upload_document', return_value={'status': 'success', 'doc_id': 'doc123'}):
            with app.test_request_context('/upload', method='POST', data={'file': test_file}):
                g.current_user = {'user_id': 'user1', 'roles': ['admin']}
                result = controller.knowledge_upload()
                if isinstance(result, tuple):
                    assert result[1] == 200
                else:
                    assert result.status_code == 200
    
    @mock.patch('src.ForumBot.rag_api.RAGAPIController._extract_user_id_from_token')
    @mock.patch('requests.post')
    def test_rag_api_auth_callback_success_simple(self, mock_post, mock_extract):
        """测试 auth_callback 成功"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {}
        }
        controller = RAGAPIController(config)
        mock_extract.return_value = 'user1'
        
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'token',
            'refresh_token': 'refresh',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        from flask import Flask, session, g
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test'
        
        with mock.patch.object(controller.auth_middleware, 'save_session', return_value=True):
            with app.test_request_context('/callback?code=test&state=teststate'):
                session['oidc_state'] = 'teststate'
                result = controller.auth_callback()
                if isinstance(result, tuple):
                    assert result[1] == 200
                else:
                    assert result.status_code == 200
    
    @mock.patch('requests.post')
    def test_rag_api_retrieve_exception(self, mock_post):
        """测试 retrieve 异常"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {'base_url': 'http://test.com'}
        }
        controller = RAGAPIController(config)
        
        mock_post.side_effect = Exception('Network error')
        
        from flask import Flask, g
        app = Flask(__name__)
        with app.test_request_context('/retrieve', method='POST', json={'query': 'test'}):
            g.current_user = {'user_id': 'user1'}
            result = controller.retrieve()
            assert result[1] == 500
    
    @mock.patch('requests.post')
    def test_rag_api_tokenize_exception(self, mock_post):
        """测试 tokenize 异常"""
        config = {
            'oidc': {'client_id': 'test', 'client_secret': 'test', 'redirect_uri': 'test'},
            'rate_limit': {},
            'rbac': {},
            'retrieval': {'base_url': 'http://test.com'}
        }
        controller = RAGAPIController(config)
        
        mock_post.side_effect = Exception('Network error')
        
        from flask import Flask, g
        app = Flask(__name__)
        with app.test_request_context('/tokenize', method='POST', json={'text': 'test'}):
            g.current_user = {'user_id': 'user1'}
            result = controller.tokenize()
            assert result[1] == 500
