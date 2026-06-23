from flask import Flask, jsonify, request
from src.utils import load_config
from src.ForumBot.logging_config import setup_logger
from src.ForumBot.rag_api import create_rag_api_controller
from src.ForumBot.auth_middleware import create_tables as create_auth_tables
from src.ForumBot.rate_limiter import create_tables as create_rate_limit_tables
import os
import sys

logger = setup_logger('external_api', 'logs/external_api.log', max_bytes=20*1024*1024, backup_count=4)


def create_app(config=None):
    """创建外部API Flask应用（仅用于独立调试，生产环境已集成到主应用）"""
    if config is None:
        config = load_config()
    
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    create_auth_tables(config)
    create_rate_limit_tables(config)
    
    # 创建并初始化 RAG API 控制器（先注册路由到 Blueprint）
    controller, rag_api_bp = create_rag_api_controller(config)
    
    # 注册 RAG API Blueprint 到应用（必须在路由添加之后）
    app.register_blueprint(rag_api_bp)
    
    @app.route('/health')
    def health():
        """健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'service': 'forum-reply-robot-external-api',
            'note': 'RAG API 已集成到主应用（5000端口），此服务仅用于调试'
        })
    
    @app.route('/health/detail')
    def health_detail():
        """详细健康检查接口"""
        oidc_config = config.get('oidc', {})
        lightrag_config = config.get('retrieval', {})
        
        return jsonify({
            'status': 'healthy',
            'service': 'forum-reply-robot-external-api',
            'note': 'RAG API 已集成到主应用（5000端口）',
            'oidc_service_status': 'configured' if oidc_config else 'not_configured',
            'lightrag_service_status': 'configured' if lightrag_config else 'not_configured',
            'components': {
                'oidc_client': oidc_config.get('client_id') is not None,
                'lightrag_client': lightrag_config.get('base_url') is not None,
                'rate_limiter': config.get('rate_limit') is not None,
                'rbac': config.get('rbac') is not None
            }
        })
    
    @app.before_request
    def enforce_https():
        """强制HTTPS"""
        if not request.is_secure and not app.debug:
            return jsonify({
                'error': 'HTTPS_REQUIRED',
                'message': '请使用HTTPS访问API'
            }), 403
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'UNAUTHORIZED',
            'message': '请先完成 OneID 认证授权'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'FORBIDDEN',
            'message': '您无权限执行此操作'
        }), 403
    
    @app.errorhandler(429)
    def rate_limited(error):
        return jsonify({
            'error': 'RATE_LIMITED',
            'message': '请求频率超限，请稍后重试'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': '服务器内部错误'
        }), 500
    
    return app


def main():
    """外部API服务主入口
    
    注意：此服务仅用于本地调试和开发。
    生产环境已将 RAG API 集成到主应用（main.py）的 5000 端口，
    由反向代理/K8s Ingress 负责外部访问控制和网络安全。
    绑定 0.0.0.0 仅用于开发调试环境，不建议在生产环境使用。
    """
    config = load_config()
    
    app = create_app(config)
    
    host = config.get('external_api', {}).get('host', '127.0.0.1')
    port = config.get('external_api', {}).get('port', 5001)
    debug = config.get('external_api', {}).get('debug', False)
    
    logger.info(f"Starting external API server on {host}:{port}")
    logger.info("This service is for local debugging only. Production uses main.py with reverse proxy.")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()