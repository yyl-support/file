from flask import Flask, jsonify
from src.ForumBot.monitor import ForumMonitor
from src.update_lightrag.full_data_init import FullDataUpdate
from src.update_lightrag.increment_date_update_timer import UpdateLightRAGTimer
from src.ForumBot.logging_config import setup_logger
from src.ForumBot.rag_api import create_rag_api_controller
from src.ForumBot.auth_middleware import create_tables as create_auth_tables
from src.ForumBot.rate_limiter import create_tables as create_rate_limit_tables
from prometheus_client import generate_latest
import os
import threading
import netifaces
import socket
import ipaddress
import time

# 设置主日志记录器，启用日志轮转
logger = setup_logger('main', 'logs/main.log', max_bytes=20*1024*1024, backup_count=4)

# 初始化 Flask 应用
app = Flask(__name__)

# 全局 RAG API 控制器（延迟初始化）
rag_api_controller = None

# 全局变量用于跟踪服务状态
service_initialized = False
monitor_instance = None
monitor_thread = None

class MonitorThread(threading.Thread):
    """监控线程类"""
    def __init__(self, monitor):
        threading.Thread.__init__(self)
        self.monitor = monitor
        self.daemon = True  # 设置为守护线程，主程序退出时自动退出

    def run(self):
        """运行监控器"""
        try:
            self.monitor.start()
        except Exception as e:
            logger.error(f"监控线程运行出错: {e}")

def get_private_ips_netifaces():
    private_ips = []
    for interface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(interface):
            for address in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                ip = address['addr']
                if ip != '127.0.0.1' and ipaddress.ip_address(ip).is_private:
                    private_ips.append(ip)
    return private_ips

def get_best_private_ip():
    try:
        ips = get_private_ips_netifaces()
    except ImportError:
        ips = get_local_ips()

    if not ips:
        raise RuntimeError("无法获取本地IP地址")

    for ip in ips:
        if ip.startswith('10.'):
            return ip
    for ip in ips:
        if ip.startswith('192.168.'):
            return ip
    return ips[0]

def is_private_ip(ip):
    """
    判断IP地址是否为私有地址
    """
    try:
        ip_address = ipaddress.ip_address(ip)
        return ip_address.is_private
    except ValueError:
        return False


def get_local_ips():
    """
    获取本地所有IP地址
    """
    private_ips = []
    hostname = socket.gethostname()
    try:
        addrinfo = socket.getaddrinfo(hostname, None)
        for family, type, proto, canonname, sockaddr in addrinfo:
            if family == socket.AF_INET:
                ip = sockaddr[0]
                if is_private_ip(ip) and ip != '127.0.0.1':
                    private_ips.append(ip)
    except socket.gaierror:
        pass

    return private_ips


def initialize_service(config):
    """
    初始化服务组件
    """
    global service_initialized, monitor_instance, monitor_thread

    try:
        logger.info("开始初始化服务...")

        # 初始化监控器，传递已加载的配置
        monitor_instance = ForumMonitor(config=config)

        # 在单独的线程中启动监控器
        monitor_thread = MonitorThread(monitor_instance)
        monitor_thread.start()

        service_initialized = True
        logger.info("服务初始化成功")
        return True
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        service_initialized = False
        return False

# LightRAG数据初始化
def lightrag_data_init(config):
    """
    LightRAG数据初始化
    """
    try:
        logger.info("开始初始化LightRAG数据...")
        full_data_update = FullDataUpdate(config=config)
        full_data_update.update_full_data()

        logger.info("LightRAG数据初始化成功")
        return True
    except Exception as e:
        logger.error(f"LightRAG数据初始化失败: {e}")
        return False

# LightRAG数据更新定时器
def lightrag_data_update_timer(config):
    """
    在线程中启动lightrag更新定时器
    """

    try:
        logger.info("启动LightRAG更新定时器")
        # 初始化定时器
        update_lightrag_timer = UpdateLightRAGTimer(config=config)

        # 在单独线程中启动定时器
        scheduler_thread = threading.Thread(target=update_lightrag_timer.run_scheduler)
        scheduler_thread.daemon = True  # 设置为守护线程
        scheduler_thread.start()

        logger.info("LightRAG更新定时器启动成功")
        return True
    except Exception as e:
        logger.error(f"LightRAG更新定时器启动失败: {e}")
        return False

@app.route('/startup', methods=['GET'])
def startup_check():
    """
    Startup probe endpoint
    Used by Kubernetes startupProbe to verify container startup
    Returns 200 once service is initialized, 503 otherwise
    """
    if service_initialized:
        return jsonify({
            "status": "ready",
            "message": "Service startup completed"
        }), 200
    else:
        return jsonify({
            "status": "not_ready",
            "message": "Service startup in progress"
        }), 503

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    返回200表示服务正常运行，返回503表示服务异常
    """
    if service_initialized and monitor_instance and monitor_thread and monitor_thread.is_alive():
        return jsonify({
            "status": "healthy",
            "message": "Service is running normally"
        }), 200
    else:
        return jsonify({
            "status": "unhealthy",
            "message": "Service not initialized or monitor not running"
        }), 503

@app.route('/health/detail', methods=['GET'])
def detailed_health_check():
    """
    详细的健康检查接口
    返回更详细的服务状态信息（包含 OIDC 和 LightRAG 服务状态）
    """
    global rag_api_controller
    
    oidc_status = 'not_configured'
    lightrag_status = 'not_configured'
    
    if rag_api_controller:
        oidc_config = rag_api_controller.config.get('oidc', {})
        lightrag_config = rag_api_controller.config.get('retrieval', {})
        
        oidc_status = 'configured' if oidc_config and oidc_config.get('client_id') else 'not_configured'
        lightrag_status = 'configured' if lightrag_config and lightrag_config.get('base_url') else 'not_configured'
    
    health_info = {
        "status": "healthy" if service_initialized and monitor_instance and monitor_thread and monitor_thread.is_alive() else "unhealthy",
        "oidc_service_status": oidc_status,
        "lightrag_service_status": lightrag_status,
        "components": {
            "service_initialized": service_initialized,
            "monitor_instance": monitor_instance is not None,
            "monitor_thread_alive": monitor_thread.is_alive() if monitor_thread else False,
            "oidc_client": oidc_status == 'configured',
            "lightrag_client": lightrag_status == 'configured'
        }
    }

    if service_initialized and monitor_instance and monitor_thread and monitor_thread.is_alive():
        health_info["message"] = "All components are working properly"
        return jsonify(health_info), 200
    else:
        health_info["message"] = "Service initialization failed or monitor not running"
        return jsonify(health_info), 503

@app.route('/metrics', methods=['GET'])
def metrics_endpoint():
    """
    Prometheus metrics 端点
    """
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

def check_schema_files():
    """
    检查 SchemaFiles 目录是否存在且包含文件
    确保在服务启动前 Schema 文件已正确拉取
    """
    schema_dir = os.path.join(
        os.path.dirname(__file__),
        'src', 'ForumBot', 'SchemaValidation', 'SchemaFiles'
    )
    
    if not os.path.exists(schema_dir):
        logger.error(f"SchemaFiles 目录不存在: {schema_dir}")
        logger.error("请确保在 Docker 构建时已正确执行 git clone 拉取 Schema 文件")
        return False
    
    # 检查目录是否非空（排除 .gitkeep 等占位文件）
    files = [f for f in os.listdir(schema_dir) if not f.startswith('.')]
    if not files:
        logger.error(f"SchemaFiles 目录为空: {schema_dir}")
        logger.error("请确保 Schema 文件已正确拉取")
        return False
    
    logger.info(f"SchemaFiles 目录检查通过，包含 {len(files)} 个文件/目录")
    return True


def check_mdb_rule_files():
    """
    检查 MdbRuleFiles 目录下是否存在规则 JSON 文件
    """
    mdb_rules_dir = os.path.join(
        os.path.dirname(__file__),
        'src', 'ForumBot', 'MdbValidation', 'MdbRuleFiles'
    )

    if not os.path.exists(mdb_rules_dir):
        logger.warning(f"MdbRuleFiles 目录不存在: {mdb_rules_dir}，MDB 校验将不可用")
        return True  # 非致命错误，MDB 校验为可选功能

    rule_files = [f for f in os.listdir(mdb_rules_dir)
                  if f.endswith('.json') and not f.startswith('.')]
    if not rule_files:
        logger.warning(f"MdbRuleFiles 目录中无规则 JSON 文件: {mdb_rules_dir}，MDB 校验将不可用")
        return True

    logger.info(f"MdbRuleFiles 目录检查通过，包含 {len(rule_files)} 个规则文件")
    return True


def initialization_worker(config):
    """后台初始化线程：在 Flask 启动后异步完成初始化"""
    global service_initialized
    
    logger.info("后台初始化线程启动...")
    
    try:
        logger.info("开始 LightRAG 数据初始化...")
        if not lightrag_data_init(config):
            logger.error("LightRAG数据初始化失败，服务将保持未就绪状态")
            service_initialized = False
            return
        
        logger.info("开始服务初始化...")
        if not initialize_service(config):
            logger.error("服务初始化失败，服务将保持未就绪状态")
            service_initialized = False
            return
        
        logger.info("启动 LightRAG 数据更新定时器...")
        if not lightrag_data_update_timer(config):
            logger.warning("LightRAG数据更新定时器启动失败，但不影响主服务")
        
        logger.info("后台初始化完成")
    except Exception as e:
        logger.error(f"后台初始化异常: {e}")
        service_initialized = False

def main():
    logger.info("Robot应用启动")
    
    # 检查 SchemaFiles 目录
    if not check_schema_files():
        logger.error("SchemaFiles 检查失败，应用退出")
        return

    # 检查 MdbRuleFiles 目录
    check_mdb_rule_files()

    # 确保必要目录存在
    config = None
    try:
        from src.utils import load_config, delete_config_file, init_db_connection_pool
        config = load_config()
        # 删除配置文件以防止敏感信息落盘
        delete_config_file()
        
        # 配置 Flask SECRET_KEY（用于 session 加密，OIDC state 验证需要）
        # 部署链路：Vault → config.yaml，优先从 config 读取，环境变量作为备用
        import sys
        flask_secret_key = config.get('flask_secret_key')
        if not flask_secret_key:
            flask_secret_key = os.environ.get('FLASK_SECRET_KEY')
        
        if flask_secret_key:
            app.config['SECRET_KEY'] = flask_secret_key
            logger.info("Flask SECRET_KEY 已从 config.yaml 加载")
        else:
            # 本地调试允许使用默认值，但会记录警告
            if '--debug' in sys.argv or os.environ.get('FLASK_DEBUG') == '1':
                app.config['SECRET_KEY'] = 'dev-secret-key-for-local-debug-only'
                logger.warning("Flask SECRET_KEY 使用调试默认值，生产环境必须在 config.yaml 设置 flask_secret_key")
            else:
                logger.error("Flask SECRET_KEY 未设置，生产环境必须在 config.yaml 的 flask_secret_key 字段配置")
                # 不退出，允许其他功能运行，但 OIDC 认证将不可用
        
        # 初始化数据库连接池
        db_config = config.get('database', {})
        if db_config:
            if not init_db_connection_pool(db_config, min_connections=2, max_connections=10):
                logger.error("数据库连接池初始化失败，API服务可能无法正常工作")

        # 确保数据目录存在
        data_dir = config.get('paths', {}).get('forum_data_dir', 'data/forum_data')
        os.makedirs(data_dir, exist_ok=True)

        # 确保日志目录存在（已在logging_config.py中处理）
        log_dir = config.get('logging', {}).get('log_dir', 'logs')
        os.makedirs(log_dir, exist_ok=True)

        logger.info("目录检查完成")
    except Exception as e:
        # 如果配置加载失败，使用默认目录
        logger.error(f"配置加载失败: {e}")
        os.makedirs('data/forum_data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        logger.info("目录检查完成（使用默认配置）")

    # 启动后台初始化线程（异步执行初始化）
    if config:
        # 注册 RAG API Blueprint 到主应用（5000端口）
        try:
            external_api_enabled = config.get('external_api', {}).get('enabled', True)
            if external_api_enabled:
                # 创建认证和限流相关数据库表
                create_auth_tables(config)
                create_rate_limit_tables(config)
                
                # 创建并初始化 RAG API 控制器（注册路由到 Blueprint）
                global rag_api_controller
                rag_api_controller, rag_api_bp = create_rag_api_controller(config)
                
                # 注册 RAG API Blueprint 到主应用（必须在路由添加之后）
                app.register_blueprint(rag_api_bp)
                
                logger.info("RAG API 已注册到主应用（5000端口）")
                logger.info("RAG API 路径: /api/v1/rag/*")
        except Exception as e:
            logger.error(f"RAG API 注册失败: {e}")
        
        init_thread = threading.Thread(target=initialization_worker, args=(config,), daemon=True)
        init_thread.start()
        logger.info("后台初始化线程已启动，Flask 应用开始监听")
    else:
        logger.error("配置加载失败，无法启动初始化线程")
        service_initialized = False

    # 启动Flask应用（始终启动，即使初始化失败）
    bind_ip = get_best_private_ip()
    app.run(host=bind_ip, port=5000, debug=False)

if __name__ == "__main__":
    main()
