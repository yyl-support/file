import logging
import yaml
import os
import shutil
import psycopg2
from psycopg2 import pool
import re


def ensure_database_exists(db_config):
    """
    确保目标数据库存在，不存在则自动创建
    用于解决 'database does not exist' 问题
    
    Args:
        db_config: 数据库配置字典，包含 host, port, database, user, password, sslmode
    
    Returns:
        bool: True 表示数据库存在或创建成功，False 表示失败
    """
    target_db = db_config.get('database')
    if not target_db:
        logging.error("数据库配置中缺少 database 字段")
        return False
    
    admin_conn = None
    try:
        admin_conn = psycopg2.connect(
            host=db_config.get('host'),
            port=db_config.get('port'),
            database='postgres',
            user=db_config.get('user'),
            password=db_config.get('password'),
            sslmode=db_config.get('sslmode', 'prefer')
        )
        admin_conn.autocommit = True
        cursor = admin_conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (target_db,)
        )
        
        if cursor.fetchone():
            logging.info(f"数据库 '{target_db}' 已存在")
            return True
        
        cursor.execute(f'CREATE DATABASE "{target_db}"')
        logging.info(f"数据库 '{target_db}' 创建成功")
        return True
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if 'database' in error_msg and 'does not exist' in error_msg:
            try:
                admin_conn = psycopg2.connect(
                    host=db_config.get('host'),
                    port=db_config.get('port'),
                    database='postgres',
                    user=db_config.get('user'),
                    password=db_config.get('password'),
                    sslmode=db_config.get('sslmode', 'prefer')
                )
                admin_conn.autocommit = True
                cursor = admin_conn.cursor()
                cursor.execute(f'CREATE DATABASE "{target_db}"')
                logging.info(f"数据库 '{target_db}' 创建成功（通过 postgres 库）")
                return True
            except Exception as inner_e:
                logging.error(f"通过 postgres 库创建数据库失败: {inner_e}")
                return False
        else:
            logging.error(f"数据库连接失败: {e}")
            return False
    except Exception as e:
        logging.error(f"确保数据库存在失败: {e}")
        return False
    finally:
        if admin_conn:
            admin_conn.close()


def load_config(config_file='config/config.yaml'):
    """
    加载配置文件
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
        return {}


def delete_config_file(config_file='config/config.yaml'):
    """
    删除配置文件以防止敏感信息落盘
    """
    try:
        if os.path.exists(config_file):
            os.remove(config_file)
            # 验证文件是否真的被删除
            if os.path.exists(config_file):
                logging.warning(f"配置文件 {config_file} 似乎未被成功删除")
            else:
                logging.info(f"已成功删除配置文件 {config_file}")
        else:
            logging.info(f"配置文件 {config_file} 不存在")
    except Exception as e:
        logging.error(f"删除配置文件失败: {e}")


def clear_directory(directory_path, ignore_file):
    """只删除文件，保留目录结构"""
    if not os.path.exists(directory_path):
        logging.error(f"目录 {directory_path} 不存在")
        return

    ignore_file_name = os.path.basename(ignore_file)
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            # 跳过需要忽略的文件
            if ignore_file and file == ignore_file_name:
                continue
            file_path = os.path.join(root, file)
            os.remove(file_path)
    logging.info(f"已清空目录 {directory_path}")


def delete_directory(directory_path):
    """删除整个目录及其内容"""
    if os.path.exists(directory_path):
        try:
            shutil.rmtree(directory_path)
            logging.info(f"已删除目录: {directory_path}")
        except Exception as e:
            logging.error(f"删除目录失败: {e}")


db_connection_pool = None


def init_db_connection_pool(db_config, min_connections=2, max_connections=10):
    """
    初始化数据库连接池
    
    Args:
        db_config: 数据库配置字典
        min_connections: 最小连接数
        max_connections: 最大连接数
    
    Returns:
        bool: True 表示成功，False 表示失败
    """
    global db_connection_pool
    
    if not db_config:
        logging.error("数据库配置缺失")
        return False
    
    try:
        db_connection_pool = pool.ThreadedConnectionPool(
            min_connections,
            max_connections,
            host=db_config.get('host'),
            port=db_config.get('port'),
            database=db_config.get('database'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            sslmode=db_config.get('sslmode', 'prefer')
        )
        logging.info(f"数据库连接池初始化成功（min={min_connections}, max={max_connections})")
        return True
    except Exception as e:
        logging.error(f"数据库连接池初始化失败: {e}")
        db_connection_pool = None
        return False


def get_db_connection_from_pool():
    """
    从连接池获取数据库连接
    
    Returns:
        connection: 数据库连接对象，失败时返回 None
    """
    global db_connection_pool
    
    if not db_connection_pool:
        logging.error("数据库连接池未初始化")
        return None
    
    try:
        conn = db_connection_pool.getconn()
        return conn
    except Exception as e:
        logging.error(f"从连接池获取连接失败: {e}")
        return None


def release_db_connection_to_pool(conn):
    """
    将数据库连接归还到连接池
    
    Args:
        conn: 数据库连接对象
    """
    global db_connection_pool
    
    if not db_connection_pool:
        return
    
    if conn:
        try:
            db_connection_pool.putconn(conn)
        except Exception as e:
            logging.error(f"归还连接到连接池失败: {e}")
            try:
                conn.close()
            except Exception as close_err:
                logging.debug(f"关闭连接时出错（已忽略）: {close_err}")


def close_db_connection_pool():
    """
    关闭数据库连接池
    """
    global db_connection_pool
    
    if db_connection_pool:
        try:
            db_connection_pool.closeall()
            logging.info("数据库连接池已关闭")
        except Exception as e:
            logging.error(f"关闭数据库连接池失败: {e}")
        db_connection_pool = None