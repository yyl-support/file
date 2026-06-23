from prometheus_client import Counter, Gauge, Histogram
from .logging_config import main_logger as logger

try:
    forum_retrieval_latency_seconds = Histogram(
        'forum_retrieval_latency_seconds',
        'LightRAG检索延迟（秒）',
        buckets=[0.5, 2.0, 10.0]
    )
    forum_generation_latency_seconds = Histogram(
        'forum_generation_latency_seconds',
        '大模型生成延迟（秒）',
        buckets=[5.0, 30.0, 120.0]
    )
    forum_end_to_end_latency_seconds = Histogram(
        'forum_end_to_end_latency_seconds',
        '端到端处理延迟（秒）',
        buckets=[10.0, 60.0, 300.0]
    )
    forum_empty_reply_rate = Gauge(
        'forum_empty_reply_rate',
        '空回复率（%）'
    )
    forum_retrieval_doc_count = Counter(
        'forum_retrieval_doc_count',
        '检索召回文档数'
    )
    forum_processed_topic_count = Counter(
        'forum_processed_topic_count',
        '已处理帖子总数'
    )
except ValueError as e:
    logger.warning(f"Prometheus指标重复注册（重启场景）: {e}")


def update_prometheus_metrics(evaluation_data):
    try:
        retrieval_latency = evaluation_data.get('retrieval_latency', 0.0)
        if retrieval_latency is not None and retrieval_latency > 0:
            forum_retrieval_latency_seconds.observe(retrieval_latency)
        
        generation_latency = evaluation_data.get('generation_latency', 0.0)
        if generation_latency is not None and generation_latency > 0:
            forum_generation_latency_seconds.observe(generation_latency)
        
        actual_output = evaluation_data.get('actual_output', '')
        if not actual_output:
            forum_empty_reply_rate.set(1.0)
        else:
            forum_empty_reply_rate.set(0.0)
        
        retrieval_context = evaluation_data.get('retrieval_context')
        if retrieval_context:
            if isinstance(retrieval_context, dict):
                forum_retrieval_doc_count.inc(len(retrieval_context.values()))
            elif isinstance(retrieval_context, list):
                forum_retrieval_doc_count.inc(len(retrieval_context))
            elif isinstance(retrieval_context, str) and retrieval_context:
                forum_retrieval_doc_count.inc(1)
        
        forum_processed_topic_count.inc(1)
        
        r_lat = retrieval_latency if retrieval_latency is not None else 0.0
        g_lat = generation_latency if generation_latency is not None else 0.0
        end_to_end_latency = r_lat + g_lat
        if end_to_end_latency > 0:
            forum_end_to_end_latency_seconds.observe(end_to_end_latency)
            
    except Exception as e:
        logger.warning(f"更新Prometheus指标失败: {e}")