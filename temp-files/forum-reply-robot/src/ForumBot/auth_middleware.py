from flask import request, jsonify, g
from functools import wraps
from datetime import datetime, timedelta
import psycopg2
from .logging_config import main_logger as logger
from .oidc_client import OIDCClient
from ..utils import ensure_database_exists, get_db_connection_from_pool, release_db_connection_to_pool


class AuthMiddleware:
    """认证中间件：从请求头提取token、校验有效性、提取用户信息"""

    def __init__(self, config, oidc_client=None):
        self.config = config
        self.oidc_client = oidc_client or OIDCClient(config)
        self.db_config = config.get('database', {})

    def get_db_connection(self):
        """获取数据库连接（从连接池）"""
        conn = get_db_connection_from_pool()
        if not conn:
            logger.error("无法从连接池获取数据库连接，尝试创建新连接")
            try:
                conn = psycopg2.connect(
                    host=self.db_config.get('host'),
                    port=self.db_config.get('port'),
                    database=self.db_config.get('database'),
                    user=self.db_config.get('user'),
                    password=self.db_config.get('password'),
                    sslmode=self.db_config.get('sslmode', 'prefer')
                )
                return conn
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                return None
        return conn

    def extract_token(self):
        """从请求头提取access_token"""
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        
        return None

    def validate_session(self, access_token):
        """验证session并获取用户信息"""
        if not access_token:
            return None
        
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, access_token, refresh_token, token_expires_at, created_at, roles
                FROM user_sessions
                WHERE access_token = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (access_token,))
            
            result = cursor.fetchone()
            
            if result:
                user_id, stored_token, refresh_token, expires_at, created_at, roles_json = result
                
                if expires_at and datetime.utcnow() > expires_at:
                    logger.warning(f"Token expired for user {user_id}")
                    return None
                
                roles = []
                if roles_json:
                    try:
                        import json
                        roles = json.loads(roles_json) if isinstance(roles_json, str) else roles_json
                    except Exception as e:
                        logger.warning(f"Failed to parse roles: {e}")
                        roles = []
                
                return {
                    'user_id': user_id,
                    'access_token': stored_token,
                    'refresh_token': refresh_token,
                    'expires_at': expires_at,
                    'roles': roles
                }
            
            return None
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return None
        finally:
            release_db_connection_to_pool(conn)

    def save_session(self, user_id, access_token, refresh_token, expires_in, roles=None):
        """保存用户session到数据库"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            import json
            roles_json = json.dumps(roles or [])
            
            cursor.execute("""
                INSERT INTO user_sessions (user_id, access_token, refresh_token, token_expires_at, created_at, roles)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, access_token, refresh_token, expires_at, datetime.utcnow(), roles_json))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Session save failed: {e}")
            conn.rollback()
            return False
        finally:
            release_db_connection_to_pool(conn)

    def update_session(self, user_id, new_access_token, new_refresh_token, expires_in, roles=None):
        """更新用户session"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            import json
            roles_json = json.dumps(roles or [])
            
            cursor.execute("""
                UPDATE user_sessions
                SET access_token = %s, refresh_token = %s, token_expires_at = %s, updated_at = %s, roles = %s
                WHERE user_id = %s
            """, (new_access_token, new_refresh_token, expires_at, datetime.utcnow(), roles_json, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Session update failed: {e}")
            conn.rollback()
            return False
        finally:
            release_db_connection_to_pool(conn)

    def require_auth(self, f):
        """认证装饰器"""
        @wraps(f)
        def decorated(*args, **kwargs):
            access_token = self.extract_token()
            
            if not access_token:
                return jsonify({
                    'error': 'TOKEN_MISSING',
                    'message': '请先完成 OneID 认证授权'
                }), 401
            
            session = self.validate_session(access_token)
            
            if not session:
                return jsonify({
                    'error': 'TOKEN_INVALID',
                    'message': 'Token无效或已过期，请重新认证'
                }), 401
            
            g.current_user = session
            
            return f(*args, **kwargs)
        
        return decorated


def create_tables(config):
    """创建用户session表"""
    db_config = config.get('database', {})
    conn = None
    
    if not ensure_database_exists(db_config):
        logger.error("无法确保数据库存在，跳过表创建")
        return
    
    try:
        conn = psycopg2.connect(
            host=db_config.get('host'),
            port=db_config.get('port'),
            database=db_config.get('database'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            sslmode=db_config.get('sslmode', 'prefer')
        )
        
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                roles TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_access_token ON user_sessions(access_token)
        """)
        
        conn.commit()
        logger.info("User sessions table created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create user_sessions table: {e}")
    finally:
        if conn:
            conn.close()