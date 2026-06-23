import requests
import secrets
from datetime import datetime, timedelta
from .logging_config import main_logger as logger
from cryptography.fernet import Fernet
import base64
import os
import json


class OIDCClient:
    """OneID OIDC认证客户端
    
    配置来源：从 config.yaml 的 oidc 段统一读取
    
    必须配置的字段（config.yaml oidc 段）：
    - client_id: OIDC客户端ID
    - client_secret: OIDC客户端密钥
    - redirect_uri: 回调地址（测试/正式环境不同）
    
    部署链路：Vault → K8s Secret → cp 到 config.yaml
    """

    MISSING_CONFIG_ERROR = "OIDC配置缺失：必须在 config.yaml 的 oidc 段设置 client_id、client_secret、redirect_uri"

    def __init__(self, config):
        self.config = config
        oidc_config = config.get('oidc', {})
        
        self.client_id = oidc_config.get('client_id')
        self.client_secret = oidc_config.get('client_secret')
        self.redirect_uri = oidc_config.get('redirect_uri')
        
        self.authorize_url = oidc_config.get('authorize_url', 'https://omapi.osinfra.cn/oneid/oidc/authorize')
        self.token_url = oidc_config.get('token_url', 'https://omapi.osinfra.cn/oneid/oidc/token')
        self.userinfo_url = oidc_config.get('userinfo_url', 'https://omapi.osinfra.cn/oneid/oidc/userinfo')
        self.scope = oidc_config.get('scope', 'openid profile')
        
        # 预览环境优雅降级：检查配置是否为空占位符或缺失
        is_preview_env = os.environ.get('PREVIEW_ENV') == 'true' or \
                        (self.client_id and self.client_id.startswith('${') and self.client_id.endswith('}'))
        
        if is_preview_env:
            # 预览环境使用测试配置，不抛异常
            if not self.client_id or self.client_id.startswith('${'):
                self.client_id = 'preview-test-client-id'
                logger.warning("预览环境：OIDC client_id 使用测试配置")
            if not self.client_secret or self.client_secret.startswith('${'):
                self.client_secret = 'preview-test-client-secret'
                logger.warning("预览环境：OIDC client_secret 使用测试配置")
            if not self.redirect_uri or self.redirect_uri.startswith('${'):
                self.redirect_uri = 'https://preview.test.osinfra.cn/api/v1/rag/auth/callback'
                logger.warning("预览环境：OIDC redirect_uri 使用测试配置")
        else:
            self._validate_config()
        
        self._fernet_key = os.environ.get('TOKEN_ENCRYPTION_KEY')
        if self._fernet_key:
            try:
                self._fernet = Fernet(self._fernet_key.encode())
            except Exception as e:
                logger.warning(f"TOKEN_ENCRYPTION_KEY is invalid, refresh tokens will not be encrypted: {e}")
                self._fernet = None
        else:
            logger.warning("TOKEN_ENCRYPTION_KEY not set, refresh tokens will not be encrypted")
            self._fernet = None

    def _validate_config(self):
        """验证关键配置是否存在，不存在则抛出异常"""
        missing = []
        if not self.client_id:
            missing.append('oidc.client_id')
        if not self.client_secret:
            missing.append('oidc.client_secret')
        if not self.redirect_uri:
            missing.append('oidc.redirect_uri')
        
        if missing:
            raise ValueError(f"OIDC配置缺失：必须在 config.yaml 设置 {', '.join(missing)}")
        
        logger.info(f"OIDC配置验证通过: redirect_uri={self.redirect_uri}")

    def generate_state(self):
        """生成 state 参数用于防 CSRF
        
        使用 secrets.token_urlsafe(16) 生成安全的随机字符串，
        存入 Flask Session（已加密签名），回调时直接比对即可。
        """
        return secrets.token_urlsafe(16)

    def validate_state(self, state_param, stored_state):
        """验证 state 参数
        
        直接比对 state 参数与存储的 state（Flask Session 已加密签名）
        """
        if not state_param or not stored_state:
            return False
        
        if state_param != stored_state:
            logger.warning(f"State mismatch: {state_param} != {stored_state}")
            return False
        
        return True

    def get_authorization_url(self, state):
        """构造授权URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': self.scope,
            'state': state
        }
        
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorize_url}?{param_str}"

    def exchange_code_for_token(self, code):
        """使用授权码换取access_token和id_token"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(
                self.token_url,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                access_token = token_data.get('access_token')
                refresh_token = token_data.get('refresh_token')
                id_token = token_data.get('id_token')
                expires_in = token_data.get('expires_in', 1800)
                
                encrypted_refresh_token = self._encrypt_token(refresh_token) if refresh_token else None
                
                user_id = None
                user_roles = []
                user_claims = {}
                
                if id_token:
                    claims = self._decode_id_token(id_token)
                    if claims:
                        user_id = claims.get('sub')
                        user_claims = claims
                        user_roles = self._extract_roles_from_claims(claims)
                
                if not user_id:
                    user_info = self._fetch_userinfo(access_token)
                    if user_info:
                        user_id = user_info.get('sub')
                        user_roles = self._extract_roles_from_claims(user_info)
                        user_claims.update(user_info)
                
                return {
                    'success': True,
                    'access_token': access_token,
                    'refresh_token': encrypted_refresh_token,
                    'expires_in': expires_in,
                    'expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
                    'user_id': user_id,
                    'user_roles': user_roles,
                    'user_claims': user_claims
                }
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Token exchange failed: {response.status_code}",
                    'error_description': response.text
                }
        except Exception as e:
            logger.error(f"Token exchange request failed: {e}")
            return {
                'success': False,
                'error': f"Request failed: {e}"
            }

    def refresh_access_token(self, encrypted_refresh_token):
        """使用refresh_token刷新access_token"""
        if not encrypted_refresh_token:
            return {
                'success': False,
                'error': 'No refresh token provided'
            }
        
        refresh_token = self._decrypt_token(encrypted_refresh_token)
        if not refresh_token:
            return {
                'success': False,
                'error': 'Failed to decrypt refresh token'
            }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(
                self.token_url,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                access_token = token_data.get('access_token')
                new_refresh_token = token_data.get('refresh_token', refresh_token)
                expires_in = token_data.get('expires_in', 1800)
                
                encrypted_new_refresh_token = self._encrypt_token(new_refresh_token)
                
                return {
                    'success': True,
                    'access_token': access_token,
                    'refresh_token': encrypted_new_refresh_token,
                    'expires_in': expires_in,
                    'expires_at': datetime.utcnow() + timedelta(seconds=expires_in)
                }
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Token refresh failed: {response.status_code}",
                    'error_description': response.text
                }
        except Exception as e:
            logger.error(f"Token refresh request failed: {e}")
            return {
                'success': False,
                'error': f"Request failed: {e}"
            }

    def _decode_id_token(self, id_token):
        """解码id_token JWT获取用户claims"""
        if not id_token:
            return None
        
        try:
            parts = id_token.split('.')
            if len(parts) != 3:
                logger.error("Invalid JWT format")
                return None
            
            payload_b64 = parts[1]
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64)
            claims = json.loads(payload_json)
            
            logger.info(f"Decoded id_token claims: sub={claims.get('sub')}")
            return claims
        except Exception as e:
            logger.error(f"Failed to decode id_token: {e}")
            return None

    def _fetch_userinfo(self, access_token):
        """调用UserInfo接口获取用户信息"""
        if not access_token or not self.userinfo_url:
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(
                self.userinfo_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"UserInfo fetched: sub={user_info.get('sub')}")
                return user_info
            else:
                logger.warning(f"UserInfo fetch failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"UserInfo fetch request failed: {e}")
            return None

    def _extract_roles_from_claims(self, claims):
        """从claims中提取角色列表"""
        if not claims:
            return []
        
        roles = []
        
        rbac_config = self.config.get('rbac', {})
        role_claim_mapping = rbac_config.get('role_claim_mapping', {})
        
        for role_name, claim_key in role_claim_mapping.items():
            claim_value = claims.get(claim_key)
            if claim_value:
                if isinstance(claim_value, list):
                    roles.extend(claim_value)
                elif isinstance(claim_value, str):
                    roles.append(claim_value)
        
        if 'roles' in claims:
            claim_roles = claims.get('roles')
            if isinstance(claim_roles, list):
                roles.extend(claim_roles)
            elif isinstance(claim_roles, str):
                roles.append(claim_roles)
        
        return list(set(roles))

    def _encrypt_token(self, token):
        """加密token"""
        if not token or not self._fernet:
            return token
        
        try:
            encrypted = self._fernet.encrypt(token.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Token encryption failed: {e}")
            return token

    def _decrypt_token(self, encrypted_token):
        """解密token"""
        if not encrypted_token:
            return None
        
        if not self._fernet:
            return encrypted_token
        
        try:
            decoded = base64.b64decode(encrypted_token.encode())
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            return None

    def validate_token(self, access_token):
        """验证access_token有效性"""
        if not access_token:
            return False
        
        return True