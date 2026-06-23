from flask import Blueprint, request, jsonify, g, redirect, session
from datetime import datetime, timedelta
import uuid
import requests
import os
import hashlib
import tempfile
from werkzeug.utils import secure_filename
from .auth_middleware import AuthMiddleware
from .rate_limiter import RateLimiter
from .rbac_middleware import RBACMiddleware
from .oidc_client import OIDCClient
from .logging_config import main_logger as logger
from ..update_lightrag.lightrag_client import LightRAGClient


rag_api_bp = Blueprint('rag_api', __name__, url_prefix='/api/v1/rag')


class RAGAPIController:
    """RAG API 控制器：tokenize、检索、知识上传接口"""

    def __init__(self, config):
        self.config = config
        
        self.oidc_client = OIDCClient(config)
        self.auth_middleware = AuthMiddleware(config, self.oidc_client)
        self.rate_limiter = RateLimiter(config)
        self.rbac_middleware = RBACMiddleware(config)
        self.lightrag_client = LightRAGClient(config)
        
        self.retrieval_config = config.get('retrieval', {})
        self.base_url = self.retrieval_config.get('base_url')
        self.query_endpoint = self.retrieval_config.get('query_endpoint', '/query')
        self.verify_ssl = self.retrieval_config.get('verify_ssl', True)
        
        self.max_text_length = 5000
        self.max_query_length = 1000
        self._bp = None

    def register_routes(self):
        """注册所有路由"""
        bp = Blueprint('rag_api', __name__, url_prefix='/api/v1/rag')
        bp.route('/auth/authorize', methods=['GET'])(self.authorize)
        bp.route('/auth/callback', methods=['GET'])(self.auth_callback)
        bp.route('/auth/refresh', methods=['POST'])(self.refresh_token)
        bp.route('/tokenize', methods=['POST'])(
            self.auth_middleware.require_auth(
                self.rate_limiter.rate_limit(self.tokenize)
            )
        )
        bp.route('/retrieve', methods=['POST'])(
            self.auth_middleware.require_auth(
                self.rate_limiter.rate_limit(self.retrieve)
            )
        )
        bp.route('/knowledge/upload', methods=['POST'])(
            self.auth_middleware.require_auth(
                self.rbac_middleware.require_role()(self.knowledge_upload)
            )
        )
        
        self._bp = bp
        return bp

    def authorize(self):
        """OIDC授权入口"""
        state = self.oidc_client.generate_state()
        session['oidc_state'] = state
        
        auth_url = self.oidc_client.get_authorization_url(state)
        
        logger.info(f"Redirecting user to OneID authorization: {auth_url}")
        return redirect(auth_url)

    def auth_callback(self):
        """OIDC回调处理"""
        code = request.args.get('code')
        state_param = request.args.get('state')
        
        stored_state = session.get('oidc_state')
        
        if not self.oidc_client.validate_state(state_param, stored_state):
            logger.error(f"State validation failed: {state_param} != {stored_state}")
            return jsonify({
                'error': 'INVALID_STATE',
                'message': 'state参数不匹配，可能存在CSRF攻击'
            }), 400
        
        token_result = self.oidc_client.exchange_code_for_token(code)
        
        if not token_result.get('success'):
            logger.error(f"Token exchange failed: {token_result.get('error')}")
            return jsonify({
                'error': 'OIDC_ERROR',
                'message': token_result.get('error_description', 'Token换取失败')
            }), 500
        
        access_token = token_result['access_token']
        refresh_token = token_result['refresh_token']
        expires_in = token_result['expires_in']
        user_id = token_result.get('user_id')
        user_roles = token_result.get('user_roles', [])
        
        if not user_id:
            user_id = self._extract_user_id_from_token(access_token)
            logger.warning(f"Could not extract user_id from id_token, using fallback hash")
        
        if not self.auth_middleware.save_session(user_id, access_token, refresh_token, expires_in, user_roles):
            logger.error(f"Failed to save session for user {user_id}")
        
        logger.info(f"User {user_id} authenticated successfully with roles: {user_roles}")
        
        return jsonify({
            'access_token': access_token,
            'expires_in': expires_in,
            'refresh_token': refresh_token
        })

    def refresh_token(self):
        """Token刷新"""
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': '请求体必须为JSON'
            }), 400
        
        refresh_token_input = data.get('refresh_token')
        
        if not refresh_token_input:
            return jsonify({
                'error': 'TOKEN_MISSING',
                'message': '缺少refresh_token'
            }), 401
        
        token_result = self.oidc_client.refresh_access_token(refresh_token_input)
        
        if not token_result.get('success'):
            logger.error(f"Token refresh failed: {token_result.get('error')}")
            return jsonify({
                'error': 'TOKEN_EXPIRED',
                'message': 'refresh_token无效或已过期'
            }), 401
        
        access_token = token_result['access_token']
        new_refresh_token = token_result['refresh_token']
        expires_in = token_result['expires_in']
        
        user_id = token_result.get('user_id')
        user_roles = token_result.get('user_roles', [])
        
        if not user_id:
            user_id = self._extract_user_id_from_token(access_token)
            logger.warning(f"Could not extract user_id from id_token, using fallback hash")
        
        if not self.auth_middleware.update_session(user_id, access_token, new_refresh_token, expires_in, user_roles):
            logger.error(f"Failed to update session for user {user_id}")
        
        logger.info(f"Token refreshed for user {user_id}")
        
        return jsonify({
            'access_token': access_token,
            'expires_in': expires_in
        })

    def tokenize(self):
        """文本分词接口"""
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': '请求体必须为JSON'
            }), 400
        
        text = data.get('text')
        
        if not text:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': '缺少text参数'
            }), 400
        
        if len(text) > self.max_text_length:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': f'文本长度超过限制({self.max_text_length}字符)'
            }), 400
        
        try:
            url = f"{self.base_url}/tokenize"
            
            payload = {
                'text': text
            }
            
            response = requests.post(
                url,
                json=payload,
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                tokens = result.get('tokens', [])
                
                logger.info(f"Tokenized text for user {g.current_user.get('user_id')}: {len(tokens)} tokens")
                
                return jsonify({
                    'tokens': tokens
                })
            else:
                logger.error(f"Tokenize request failed: {response.status_code}")
                return jsonify({
                    'error': 'RAG_ERROR',
                    'message': 'LightRAG tokenize服务异常'
                }), 500
                
        except Exception as e:
            logger.error(f"Tokenize failed: {e}")
            return jsonify({
                'error': 'RAG_ERROR',
                'message': f'分词失败: {str(e)}'
            }), 500

    def retrieve(self):
        """文档检索接口"""
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': '请求体必须为JSON'
            }), 400
        
        query = data.get('query')
        top_k = data.get('top_k', 3)
        
        if not query:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': '缺少query参数'
            }), 400
        
        if len(query) > self.max_query_length:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': f'查询长度超过限制({self.max_query_length}字符)'
            }), 400
        
        if top_k < 1 or top_k > 10:
            top_k = min(max(top_k, 1), 10)
        
        try:
            url = f"{self.base_url}{self.query_endpoint}"
            
            payload = {
                'query': query,
                'only_need_prompt': False,
                'only_need_context': True,
                'top_k': top_k,
                'chunk_top_k': self.retrieval_config.get('chunk_top_k', 10),
                'enable_rerank': self.retrieval_config.get('enable_rerank', True)
            }
            
            response = requests.post(
                url,
                json=payload,
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                context_data = result.get('context', {})
                
                results = []
                
                chunks = context_data.get('chunks', [])
                for i, chunk in enumerate(chunks[:top_k]):
                    results.append({
                        'doc_id': chunk.get('doc_id', f'doc_{i}'),
                        'score': chunk.get('score', 0.0),
                        'snippet': chunk.get('content', ''),
                        'source': chunk.get('source', '')
                    })
                
                logger.info(f"Retrieved {len(results)} documents for user {g.current_user.get('user_id')}")
                
                return jsonify({
                    'results': results,
                    'total': len(results)
                })
            else:
                logger.error(f"Retrieve request failed: {response.status_code}")
                return jsonify({
                    'error': 'RAG_ERROR',
                    'message': 'LightRAG检索服务异常'
                }), 500
                
        except Exception as e:
            logger.error(f"Retrieve failed: {e}")
            return jsonify({
                'error': 'RAG_ERROR',
                'message': f'检索失败: {str(e)}'
            }), 500

    def knowledge_upload(self):
        """知识上传接口（仅授权角色）"""
        if 'file' not in request.files:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': '缺少文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': '未选择文件'
            }), 400
        
        try:
            safe_filename = secure_filename(file.filename)
            if not safe_filename:
                return jsonify({
                    'error': 'INVALID_REQUEST',
                    'message': '文件名无效'
                }), 400
            
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=f'_{safe_filename}') as temp_file:
                temp_file_path = temp_file.name
                file.save(temp_file_path)
            
            api_url = self.base_url
            api_key = self.retrieval_config.get('api_key')
            
            result = self.lightrag_client.upload_document(temp_file_path, api_url, api_key)
            
            os.remove(temp_file_path)
            
            if result.get('status') == 'success':
                doc_id = result.get('doc_id') or result.get('track_id')
                
                logger.info(f"Knowledge uploaded by user {g.current_user.get('user_id')}: {doc_id}")
                
                return jsonify({
                    'status': 'success',
                    'doc_id': doc_id
                })
            else:
                logger.error(f"Knowledge upload failed: {result}")
                return jsonify({
                    'error': 'RAG_ERROR',
                    'message': '知识上传失败'
                }), 500
                
        except Exception as e:
            logger.error(f"Knowledge upload failed: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({
                'error': 'RAG_ERROR',
                'message': f'上传失败: {str(e)}'
            }), 500

    def _extract_user_id_from_token(self, access_token):
        """从token中提取用户ID（简化实现，实际应解析JWT）
        
        注意：此方法仅为fallback，用于无法从id_token获取user_id的场景。
        MD5在此不用于安全目的（如密码hash或加密），仅用于生成短字符串标识符。
        """
        md5_hash = hashlib.md5(access_token.encode(), usedforsecurity=False)
        return f"user_{md5_hash.hexdigest()[:8]}"


def create_rag_api_controller(config):
    """创建RAG API控制器并注册路由
    
    Returns:
        tuple: (controller, blueprint)
    """
    controller = RAGAPIController(config)
    bp = controller.register_routes()
    return controller, bp