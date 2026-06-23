import threading
import time
import functools
from .logging_config import main_logger as logger

_evaluation_context = threading.local()


def get_evaluation_context():
    return _evaluation_context


def capture_retrieval_metrics(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            related_docs, data = func(*args, **kwargs)
            latency = time.time() - start_time
            ctx = get_evaluation_context()
            ctx.retrieval_context = related_docs
            ctx.retrieval_latency = latency
            ctx.retrieval_data = data
            return related_docs, data
        except Exception as e:
            logger.warning(f"数据采集钩子异常(检索节点): {e}")
            ctx = get_evaluation_context()
            ctx.retrieval_context = None
            ctx.retrieval_latency = None
            ctx.retrieval_data = None
            return func(*args, **kwargs)
    return wrapper


def capture_generation_metrics(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            latency = time.time() - start_time
            ctx = get_evaluation_context()
            ctx.actual_output = result
            ctx.generation_latency = latency
            return result
        except Exception as e:
            logger.warning(f"数据采集钩子异常(生成节点): {e}")
            ctx = get_evaluation_context()
            ctx.actual_output = None
            ctx.generation_latency = None
            raise
    return wrapper


def classify_question(title, user_question):
    combined_text = f"{title} {user_question}".lower()
    
    if any(kw in combined_text for kw in ['报错', 'error', '日志', '配置', '参数', '接口', 'api', '代码']):
        return '技术问题'
    
    if any(kw in combined_text for kw in ['怎么', '如何', '教程', '文档', '安装', '部署', '下载']):
        return '使用问题'
    
    if any(kw in combined_text for kw in ['规范', '规则', '要求', '审核', 'pr', '提交']):
        return '社区规则'
    
    return '其他'