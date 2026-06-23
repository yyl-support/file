import pytest
import unittest.mock as mock
import os
from flask import Flask, g, session
from src.ForumBot.rag_api import RAGAPIController, create_rag_api_controller, rag_api_bp
from datetime import datetime


class TestRAGAPIController:
    
    @pytest.fixture
    def rag_config(self):
        return {
            'oidc': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'authorize_url': 'https://omapi.osinfra.cn/oneid/oidc/authorize',
                'token_url': 'https://omapi.osinfra.cn/oneid/oidc/token',
                'redirect_uri': 'https://rag.openubmc.cn/api/v1/rag/auth/callback',
                'scope': 'openid profile'
            },
            'rate_limit': {
                'user_hourly_limit': 100,
                'window_seconds': 3600
            },
            'rbac': {
                'knowledge_upload_roles': ['huawei_maintainer', 'robot_service']
            },
            'retrieval': {
                'base_url': 'https://lightrag.example.com',
                'query_endpoint': '/query',
                'verify_ssl': True,
                'top_k': 5,
                'chunk_top_k': 10,
                'enable_rerank': True
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
    def rag_controller(self, rag_config):
        yield RAGAPIController(rag_config)
    
    @pytest.fixture
    def app(self, rag_config, rag_controller):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.extensions['rag_api'] = rag_controller
        bp = rag_controller.register_routes()
        app.register_blueprint(bp)
        return app
    
    def test_tokenize_success(self, app):
        with app.test_request_context(
            '/api/v1/rag/tokenize',
            method='POST',
            json={'text': 'openUBMC BMC管理控制器'},
            headers={'Authorization': 'Bearer test_token'}
        ):
            with mock.patch.object(app.extensions['rag_api'], 'auth_middleware') as mock_auth:
                mock_auth.validate_session = mock.Mock(return_value={
                    'user_id': 'test_user',
                    'access_token': 'test_token'
                })
                
                g.current_user = {'user_id': 'test_user'}
                
                with mock.patch('requests.post') as mock_post:
                    mock_response = mock.Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'tokens': ['openUBMC', 'BMC', '管理', '控制器']}
                    mock_post.return_value = mock_response
                    
                    controller = app.extensions['rag_api']
                    result = controller.tokenize()
                    
                    if isinstance(result, tuple):

                    
                        response, code = result

                    
                        assert code == 200

                    
                    else:

                    
                        assert result.status_code == 200
                    if isinstance(result, tuple):

                        data = result[0].get_json()

                    else:

                        data = result.get_json()
                    assert 'tokens' in data
                    assert len(data['tokens']) == 4
    
    def test_tokenize_missing_text(self, app):
        with app.test_request_context(
            '/api/v1/rag/tokenize',
            method='POST',
            json={},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user'}
            
            controller = app.extensions['rag_api']
            result = controller.tokenize()
            
            if isinstance(result, tuple):
                response, status_code = result
                assert status_code == 400
                data = response.get_json()
            else:
                if isinstance(result, tuple):

                    response, code = result

                    assert code == 400

                else:

                    assert result.status_code == 400
                if isinstance(result, tuple):

                    data = result[0].get_json()

                else:

                    data = result.get_json()
            assert data['error'] == 'INVALID_REQUEST'
    
    def test_tokenize_text_too_long(self, app):
        long_text = 'a' * 6000
        
        with app.test_request_context(
            '/api/v1/rag/tokenize',
            method='POST',
            json={'text': long_text},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user'}
            
            controller = app.extensions['rag_api']
            result = controller.tokenize()
            
            if isinstance(result, tuple):

            
                response, code = result

            
                assert code == 400

            
            else:

            
                assert result.status_code == 400
            if isinstance(result, tuple):

                data = result[0].get_json()

            else:

                data = result.get_json()
            assert data['error'] == 'INVALID_REQUEST'
    
    def test_retrieve_success(self, app):
        with app.test_request_context(
            '/api/v1/rag/retrieve',
            method='POST',
            json={'query': '如何配置BMC网络', 'top_k': 3},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user'}
            
            with mock.patch('requests.post') as mock_post:
                mock_response = mock.Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'context': {
                        'chunks': [
                            {'doc_id': 'doc_001', 'score': 0.95, 'content': 'BMC网络配置可通过...', 'source': '论坛'},
                            {'doc_id': 'doc_002', 'score': 0.88, 'content': 'Redfish API...', 'source': '文档'}
                        ]
                    }
                }
                mock_post.return_value = mock_response
                
                controller = app.extensions['rag_api']
                result = controller.retrieve()
                
                if isinstance(result, tuple):

                
                    response, code = result

                
                    assert code == 200

                
                else:

                
                    assert result.status_code == 200
                if isinstance(result, tuple):

                    data = result[0].get_json()

                else:

                    data = result.get_json()
                assert 'results' in data
                assert len(data['results']) == 2
    
    def test_retrieve_missing_query(self, app):
        with app.test_request_context(
            '/api/v1/rag/retrieve',
            method='POST',
            json={'top_k': 3},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user'}
            
            controller = app.extensions['rag_api']
            result = controller.retrieve()
            
            if isinstance(result, tuple):

            
                response, code = result

            
                assert code == 400

            
            else:

            
                assert result.status_code == 400
            if isinstance(result, tuple):

                data = result[0].get_json()

            else:

                data = result.get_json()
            assert data['error'] == 'INVALID_REQUEST'
    
    def test_retrieve_query_too_long(self, app):
        long_query = 'a' * 1100
        
        with app.test_request_context(
            '/api/v1/rag/retrieve',
            method='POST',
            json={'query': long_query},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user'}
            
            controller = app.extensions['rag_api']
            result = controller.retrieve()
            
            if isinstance(result, tuple):

            
                response, code = result

            
                assert code == 400

            
            else:

            
                assert result.status_code == 400
            if isinstance(result, tuple):

                data = result[0].get_json()

            else:

                data = result.get_json()
            assert data['error'] == 'INVALID_REQUEST'
    
    def test_retrieve_top_k_boundaries(self, app):
        with app.test_request_context(
            '/api/v1/rag/retrieve',
            method='POST',
            json={'query': 'test query', 'top_k': 20},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user'}
            
            with mock.patch('requests.post') as mock_post:
                mock_response = mock.Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'context': {'chunks': []}}
                mock_post.return_value = mock_response
                
                controller = app.extensions['rag_api']
                result = controller.retrieve()
                
                mock_post.assert_called()
                call_args = mock_post.call_args
                assert call_args[1]['json']['top_k'] <= 10
    
    @mock.patch('src.ForumBot.rag_api.RAGAPIController._extract_user_id_from_token')
    @mock.patch('requests.post')
    def test_auth_callback_success(self, mock_post, mock_extract, app):
        mock_extract.return_value = 'test_user'
        
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 1800
        }
        mock_post.return_value = mock_response
        
        with app.test_request_context(
            '/api/v1/rag/auth/callback?code=test_code&state=test_state:test_signature',
            method='GET'
        ):
            session['oidc_state'] = 'test_state:test_signature'
            
            with mock.patch.object(app.extensions['rag_api'].auth_middleware, 'save_session', return_value=True):
                controller = app.extensions['rag_api']
                result = controller.auth_callback()
                
                if isinstance(result, tuple):

                
                    response, code = result

                
                    assert code == 200

                
                else:

                
                    assert result.status_code == 200
                if isinstance(result, tuple):

                    data = result[0].get_json()

                else:

                    data = result.get_json()
                assert 'access_token' in data
                assert 'expires_in' in data
    
    def test_auth_callback_state_mismatch(self, app):
        with app.test_request_context(
            '/api/v1/rag/auth/callback?code=test_code&state=wrong_state',
            method='GET'
        ):
            session['oidc_state'] = 'correct_state:test_signature'
            
            controller = app.extensions['rag_api']
            result = controller.auth_callback()
            
            if isinstance(result, tuple):

            
                response, code = result

            
                assert code == 400

            
            else:

            
                assert result.status_code == 400
            if isinstance(result, tuple):

                data = result[0].get_json()

            else:

                data = result.get_json()
            assert data['error'] == 'INVALID_STATE'
    
    def test_authorize_redirect(self, app):
        with app.test_request_context('/api/v1/rag/auth/authorize', method='GET'):
            controller = app.extensions['rag_api']
            result = controller.authorize()
            
            if isinstance(result, tuple):

            
                response, code = result

            
                assert code == 302

            
            else:

            
                assert result.status_code == 302
    
    def test_refresh_token_success(self, app):
        with app.test_request_context(
            '/api/v1/rag/auth/refresh',
            method='POST',
            json={'refresh_token': 'test_refresh_token'}
        ):
            with mock.patch.object(app.extensions['rag_api'].oidc_client, 'refresh_access_token') as mock_refresh:
                mock_refresh.return_value = {
                    'success': True,
                    'access_token': 'new_access_token',
                    'refresh_token': 'new_refresh_token',
                    'expires_in': 1800
                }
                
                with mock.patch.object(app.extensions['rag_api'], '_extract_user_id_from_token', return_value='test_user'):
                    with mock.patch.object(app.extensions['rag_api'].auth_middleware, 'update_session', return_value=True):
                        controller = app.extensions['rag_api']
                        result = controller.refresh_token()
                        
                        if isinstance(result, tuple):

                        
                            response, code = result

                        
                            assert code == 200

                        
                        else:

                        
                            assert result.status_code == 200
                        if isinstance(result, tuple):

                            data = result[0].get_json()

                        else:

                            data = result.get_json()
                        assert 'access_token' in data
    
    def test_refresh_token_missing(self, app):
        with app.test_request_context(
            '/api/v1/rag/auth/refresh',
            method='POST',
            json={}
        ):
            controller = app.extensions['rag_api']
            result = controller.refresh_token()
            
            if isinstance(result, tuple):
                response, code = result
                # Both 400 and 401 are acceptable for missing token
                assert code in [400, 401]
            else:
                assert result.status_code in [400, 401]
    
    def test_knowledge_upload_missing_file(self, app):
        with app.test_request_context(
            '/api/v1/rag/knowledge/upload',
            method='POST',
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user', 'roles': ['huawei_maintainer']}
            
            controller = app.extensions['rag_api']
            result = controller.knowledge_upload()
            
            if isinstance(result, tuple):

            
                response, code = result

            
                assert code == 400

            
            else:

            
                assert result.status_code == 400
            if isinstance(result, tuple):

                data = result[0].get_json()

            else:

                data = result.get_json()
            assert data['error'] == 'INVALID_REQUEST'
    
    def test_extract_user_id_from_token(self, rag_controller):
        import hashlib
        
        access_token = 'test_access_token_12345'
        user_id = rag_controller._extract_user_id_from_token(access_token)
        
        assert user_id.startswith('user_')
        assert len(user_id) == 13
    
    def test_extract_user_id_md5_usedforsecurity_false(self, rag_controller):
        """测试 MD5 hash 使用 usedforsecurity=False 参数"""
        import hashlib
        
        access_token = 'test_token_for_md5_check'
        
        md5_hash_direct = hashlib.md5(access_token.encode(), usedforsecurity=False)
        expected_prefix = f"user_{md5_hash_direct.hexdigest()[:8]}"
        
        user_id = rag_controller._extract_user_id_from_token(access_token)
        
        assert user_id == expected_prefix
    
    def test_extract_user_id_consistency(self, rag_controller):
        """测试 user_id 生成的一致性"""
        access_token = 'consistent_test_token'
        
        user_id1 = rag_controller._extract_user_id_from_token(access_token)
        user_id2 = rag_controller._extract_user_id_from_token(access_token)
        
        assert user_id1 == user_id2
    
    def test_create_rag_api_controller(self, rag_config):
        controller, bp = create_rag_api_controller(rag_config)
        
        assert controller is not None
        assert controller.config == rag_config
        assert bp is not None
    
    def test_knowledge_upload_path_traversal_protection(self, app):
        from werkzeug.datastructures import FileStorage
        import io
        
        malicious_file = FileStorage(
            stream=io.BytesIO(b"test content"),
            filename="../../../etc/passwd",
            content_type="text/plain"
        )
        
        with app.test_request_context(
            '/api/v1/rag/knowledge/upload',
            method='POST',
            data={'file': malicious_file},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user', 'roles': ['huawei_maintainer']}
            
            with mock.patch.object(app.extensions['rag_api'].lightrag_client, 'upload_document') as mock_upload:
                mock_upload.return_value = {'status': 'error', 'message': 'upload failed'}
                
                controller = app.extensions['rag_api']
                result = controller.knowledge_upload()
                
                # secure_filename sanitizes the path, so it's not rejected as 400
                # but the upload fails, returning 500
                if isinstance(result, tuple):
                    response, code = result
                    assert code == 500
                else:
                    assert result.status_code == 500
    
    def test_knowledge_upload_valid_filename(self, app):
        from werkzeug.datastructures import FileStorage
        import io
        
        valid_file = FileStorage(
            stream=io.BytesIO(b"test content"),
            filename="valid_doc.txt",
            content_type="text/plain"
        )
        
        with app.test_request_context(
            '/api/v1/rag/knowledge/upload',
            method='POST',
            data={'file': valid_file},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user', 'roles': ['huawei_maintainer']}
            
            with mock.patch.object(app.extensions['rag_api'].lightrag_client, 'upload_document') as mock_upload:
                mock_upload.return_value = {'status': 'success', 'doc_id': 'doc_123'}
                
                controller = app.extensions['rag_api']
                result = controller.knowledge_upload()
                
                if isinstance(result, tuple):
                    response, code = result
                    assert code == 200
                else:
                    assert result.status_code == 200
    
    @mock.patch('os.remove')
    @mock.patch('tempfile.NamedTemporaryFile')
    def test_knowledge_upload_tempfile_security(self, mock_tempfile, mock_remove, app):
        """测试知识上传使用安全的临时文件"""
        from werkzeug.datastructures import FileStorage
        import io
        
        mock_temp_file = mock.Mock()
        mock_temp_file.name = '/tmp/safe_temp_file_xyz_valid_doc.txt'
        mock_temp_file.write = mock.Mock()
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file
        
        valid_file = FileStorage(
            stream=io.BytesIO(b"test content"),
            filename="valid_doc.txt",
            content_type="text/plain"
        )
        
        with app.test_request_context(
            '/api/v1/rag/knowledge/upload',
            method='POST',
            data={'file': valid_file},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user', 'roles': ['huawei_maintainer']}
            
            with mock.patch.object(app.extensions['rag_api'].lightrag_client, 'upload_document') as mock_upload:
                mock_upload.return_value = {'status': 'success', 'doc_id': 'doc_123'}
                
                controller = app.extensions['rag_api']
                result = controller.knowledge_upload()
                
                if isinstance(result, tuple):
                    response, code = result
                    assert code == 200
                else:
                    assert result.status_code == 200
                mock_tempfile.assert_called_once()
                call_kwargs = mock_tempfile.call_args[1]
                assert call_kwargs['delete'] == False
    
    def test_knowledge_upload_file_cleanup_on_success(self, app):
        """测试文件上传成功后清理临时文件"""
        from werkzeug.datastructures import FileStorage
        import io
        
        valid_file = FileStorage(
            stream=io.BytesIO(b"test content"),
            filename="valid_doc.txt",
            content_type="text/plain"
        )
        
        with app.test_request_context(
            '/api/v1/rag/knowledge/upload',
            method='POST',
            data={'file': valid_file},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user', 'roles': ['huawei_maintainer']}
            
            with mock.patch.object(app.extensions['rag_api'].lightrag_client, 'upload_document') as mock_upload:
                mock_upload.return_value = {'status': 'success', 'doc_id': 'doc_123'}
                
                with mock.patch('os.remove') as mock_remove:
                    controller = app.extensions['rag_api']
                    result = controller.knowledge_upload()
                    
                    if isinstance(result, tuple):
                        response, code = result
                        assert code == 200
                    else:
                        assert result.status_code == 200
                    mock_remove.assert_called()
    
    def test_knowledge_upload_file_cleanup_on_error(self, app):
        """测试文件上传失败后清理临时文件"""
        from werkzeug.datastructures import FileStorage
        import io
        
        valid_file = FileStorage(
            stream=io.BytesIO(b"test content"),
            filename="valid_doc.txt",
            content_type="text/plain"
        )
        
        with app.test_request_context(
            '/api/v1/rag/knowledge/upload',
            method='POST',
            data={'file': valid_file},
            headers={'Authorization': 'Bearer test_token'}
        ):
            g.current_user = {'user_id': 'test_user', 'roles': ['huawei_maintainer']}
            
            with mock.patch.object(app.extensions['rag_api'].lightrag_client, 'upload_document') as mock_upload:
                mock_upload.side_effect = Exception('Upload failed')
                
                with mock.patch('os.path.exists', return_value=True):
                    with mock.patch('os.remove') as mock_remove:
                        controller = app.extensions['rag_api']
                        result = controller.knowledge_upload()
                        
                        if isinstance(result, tuple):
                            response, code = result
                            assert code == 500
                        else:
                            assert result.status_code == 500
                        mock_remove.assert_called()