import pytest
import unittest.mock as mock
import os
from src.ForumBot.oidc_client import OIDCClient
from datetime import datetime, timedelta
import hashlib


class TestOIDCClient:
    
    @pytest.fixture
    def oidc_config(self):
        return {
            'oidc': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'authorize_url': 'https://omapi.osinfra.cn/oneid/oidc/authorize',
                'token_url': 'https://omapi.osinfra.cn/oneid/oidc/token',
                'userinfo_url': 'https://omapi.osinfra.cn/oneid/oidc/userinfo',
                'redirect_uri': 'https://rag.openubmc.cn/api/v1/rag/auth/callback',
                'scope': 'openid profile'
            },
            'rbac': {
                'role_claim_mapping': {
                    'huawei_maintainer': 'https://omapi.osinfra.cn/claims/roles'
                }
            }
        }
    
    @pytest.fixture
    def oidc_client(self, oidc_config):
        yield OIDCClient(oidc_config)
    
    def test_init_from_config(self, oidc_config):
        client = OIDCClient(oidc_config)
        assert client.client_id == 'test_client_id'
        assert client.client_secret == 'test_client_secret'
        assert client.redirect_uri == 'https://rag.openubmc.cn/api/v1/rag/auth/callback'
    
    def test_init_missing_required_config_raises_error(self):
        with pytest.raises(ValueError) as exc_info:
            OIDCClient({})
        assert 'oidc.client_id' in str(exc_info.value)
        assert 'oidc.client_secret' in str(exc_info.value)
        assert 'oidc.redirect_uri' in str(exc_info.value)
    
    def test_init_missing_redirect_uri_raises_error(self, oidc_config):
        del oidc_config['oidc']['redirect_uri']
        with pytest.raises(ValueError) as exc_info:
            OIDCClient(oidc_config)
        assert 'oidc.redirect_uri' in str(exc_info.value)
    
    def test_generate_state(self, oidc_client):
        state = oidc_client.generate_state()
        
        assert state is not None
        assert len(state) >= 16
    
    def test_validate_state_success(self, oidc_client):
        state = oidc_client.generate_state()
        
        result = oidc_client.validate_state(state, state)
        
        assert result is True
    
    def test_validate_state_failure_mismatch(self, oidc_client):
        state1 = oidc_client.generate_state()
        state2 = oidc_client.generate_state()
        
        result = oidc_client.validate_state(state2, state1)
        
        assert result is False
    
    def test_validate_state_failure_empty(self, oidc_client):
        result = oidc_client.validate_state(None, None)
        
        assert result is False
    
    def test_validate_state_failure_invalid_format(self, oidc_client):
        result = oidc_client.validate_state('state1', 'state2')
        
        assert result is False
    
    def test_get_authorization_url(self, oidc_client):
        state = oidc_client.generate_state()
        
        url = oidc_client.get_authorization_url(state)
        
        assert url is not None
        assert oidc_client.authorize_url in url
        assert 'client_id=' in url
        assert 'redirect_uri=' in url
        assert 'response_type=code' in url
        assert 'scope=' in url
        assert 'state=' in url
    
    @mock.patch('requests.post')
    def test_exchange_code_for_token_success(self, mock_post, oidc_client):
        import base64
        import json
        
        payload = {'sub': 'test_user_sub', 'roles': ['user']}
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        id_token = f'header.{payload_b64}.signature'
        
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'id_token': id_token,
            'expires_in': 1800
        }
        mock_post.return_value = mock_response
        
        result = oidc_client.exchange_code_for_token('test_code')
        
        assert result['success'] is True
        assert result['access_token'] == 'test_access_token'
        assert result['expires_in'] == 1800
        assert 'expires_at' in result
        assert result['user_id'] == 'test_user_sub'
    
    @mock.patch('requests.post')
    def test_exchange_code_for_token_failure(self, mock_post, oidc_client):
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid code'
        mock_post.return_value = mock_response
        
        result = oidc_client.exchange_code_for_token('invalid_code')
        
        assert result['success'] is False
        assert 'error' in result
    
    @mock.patch('requests.post')
    def test_refresh_access_token_success(self, mock_post, oidc_client):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 1800
        }
        mock_post.return_value = mock_response
        
        result = oidc_client.refresh_access_token('test_refresh_token')
        
        assert result['success'] is True
        assert result['access_token'] == 'new_access_token'
        assert result['expires_in'] == 1800
    
    @mock.patch('requests.post')
    def test_refresh_access_token_failure(self, mock_post, oidc_client):
        mock_response = mock.Mock()
        mock_response.status_code = 401
        mock_response.text = 'Invalid refresh token'
        mock_post.return_value = mock_response
        
        result = oidc_client.refresh_access_token('invalid_refresh_token')
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_refresh_access_token_no_token(self, oidc_client):
        result = oidc_client.refresh_access_token(None)
        
        assert result['success'] is False
        assert result['error'] == 'No refresh token provided'
    
    def test_validate_token_success(self, oidc_client):
        result = oidc_client.validate_token('test_access_token')
        
        assert result is True
    
    def test_validate_token_empty(self, oidc_client):
        result = oidc_client.validate_token(None)
        
        assert result is False
    
    def test_encrypt_decrypt_token_without_fernet(self, oidc_config):
        client = OIDCClient(oidc_config)
        
        token = 'test_token'
        encrypted = client._encrypt_token(token)
        
        assert encrypted == token
        
        decrypted = client._decrypt_token(encrypted)
        
        assert decrypted == token
    
    @mock.patch('cryptography.fernet.Fernet')
    def test_encrypt_decrypt_token_with_fernet(self, mock_fernet_class, oidc_config):
        mock_fernet = mock.Mock()
        mock_fernet.encrypt.return_value = b'encrypted_token'
        mock_fernet.decrypt.return_value = b'test_token'
        mock_fernet_class.return_value = mock_fernet
        
        os.environ['TOKEN_ENCRYPTION_KEY'] = 'dGVzdF9rZXlfZm9yX2Zlcm5ldF90ZXN0'
        
        client = OIDCClient(oidc_config)
        
        token = 'test_token'
        encrypted = client._encrypt_token(token)
        
        assert encrypted is not None
        
        decrypted = client._decrypt_token(encrypted)
        
        assert decrypted == 'test_token'
        
        if 'TOKEN_ENCRYPTION_KEY' in os.environ:
            del os.environ['TOKEN_ENCRYPTION_KEY']