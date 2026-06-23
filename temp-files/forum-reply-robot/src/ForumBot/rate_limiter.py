from flask import request, jsonify, g
from functools import wraps
from datetime import datetime, timedelta
import psycopg2
from .logging_config import main_logger as logger
from ..utils import ensure_database_exists, get_db_connection_from_pool, release_db_connection_to_pool


class RateLimiter:
    """用户级限流：基于 PostgreSQL 计数器实现滑动窗口限流"""

    def __init__(self, config):
        self.config = config
        rate_limit_config = config.get('rate_limit', {})
        
        self.hourly_limit = rate_limit_config.get('user_hourly_limit', 100)
        self.window_seconds = rate_limit_config.get('window_seconds', 3600)
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

    def check_rate_limit(self, user_id):
        """检查用户是否超过限流阈值"""
        conn = self.get_db_connection()
        if not conn:
            return True
        
        try:
            cursor = conn.cursor()
            
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            cursor.execute("""
                SELECT request_count, window_start, updated_at
                FROM rate_limits
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                request_count, stored_window_start, updated_at = result
                
                if stored_window_start and now > stored_window_start + timedelta(seconds=self.window_seconds):
                    cursor.execute("""
                        UPDATE rate_limits
                        SET request_count = 1, window_start = %s, updated_at = %s
                        WHERE user_id = %s
                    """, (now, now, user_id))
                    conn.commit()
                    return True
                
                if request_count >= self.hourly_limit:
                    retry_after = int((stored_window_start + timedelta(seconds=self.window_seconds) - now).total_seconds())
                    logger.warning(f"Rate limit exceeded for user {user_id}: {request_count}/{self.hourly_limit}")
                    return False
                
                cursor.execute("""
                    UPDATE rate_limits
                    SET request_count = request_count + 1, updated_at = %s
                    WHERE user_id = %s
                """, (now, user_id))
                conn.commit()
                return True
            else:
                cursor.execute("""
                    INSERT INTO rate_limits (user_id, request_count, window_start, updated_at)
                    VALUES (%s, 1, %s, %s)
                """, (user_id, now, now))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True
        finally:
            release_db_connection_to_pool(conn)

    def get_retry_after(self, user_id):
        """获取需要等待的秒数"""
        conn = self.get_db_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT window_start, updated_at
                FROM rate_limits
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                window_start, _ = result
                if window_start:
                    retry_after = int((window_start + timedelta(seconds=self.window_seconds) - datetime.utcnow()).total_seconds())
                    return max(0, retry_after)
            
            return 0
        except Exception as e:
            logger.error(f"Get retry_after failed: {e}")
            return 0
        finally:
            release_db_connection_to_pool(conn)

    def rate_limit(self, f):
        """限流装饰器"""
        @wraps(f)
        def decorated(*args, **kwargs):
            if hasattr(g, 'current_user'):
                user_id = g.current_user.get('user_id')
            else:
                user_id = request.headers.get('X-User-ID', 'anonymous')
            
            if not self.check_rate_limit(user_id):
                retry_after = self.get_retry_after(user_id)
                
                response = jsonify({
                    'error': 'RATE_LIMITED',
                    'message': f'请求频率超限，请等待 {retry_after} 秒后重试'
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(retry_after)
                return response
            
            return f(*args, **kwargs)
        
        return decorated


def create_tables(config):
    """创建限流表"""
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
            CREATE TABLE IF NOT EXISTS rate_limits (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL UNIQUE,
                request_count INTEGER DEFAULT 0,
                window_start TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rate_limits_user_id ON rate_limits(user_id)
        """)
        
        conn.commit()
        logger.info("Rate limits table created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create rate_limits table: {e}")
    finally:
        if conn:
            conn.close()