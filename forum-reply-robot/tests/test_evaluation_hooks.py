import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from src.ForumBot.evaluation_hooks import (
    capture_retrieval_metrics,
    capture_generation_metrics,
    get_evaluation_context,
    classify_question
)


def test_get_evaluation_context():
    ctx = get_evaluation_context()
    assert hasattr(ctx, '__dict__') or isinstance(ctx, threading.local)


def test_capture_retrieval_metrics_success():
    mock_func = Mock(return_value=(["doc1", "doc2"], {"data": "test"}))
    decorated_func = capture_retrieval_metrics(mock_func)
    
    result = decorated_func()
    
    assert result == (["doc1", "doc2"], {"data": "test"})
    ctx = get_evaluation_context()
    assert hasattr(ctx, 'retrieval_context')
    assert ctx.retrieval_context == ["doc1", "doc2"]
    assert hasattr(ctx, 'retrieval_latency')
    assert isinstance(ctx.retrieval_latency, float)
    assert hasattr(ctx, 'retrieval_data')
    assert ctx.retrieval_data == {"data": "test"}


def test_capture_retrieval_metrics_exception():
    mock_func = Mock(side_effect=Exception("Test error"))
    decorated_func = capture_retrieval_metrics(mock_func)
    
    with pytest.raises(Exception, match="Test error"):
        decorated_func()
    
    ctx = get_evaluation_context()
    assert hasattr(ctx, 'retrieval_context')
    assert ctx.retrieval_context is None
    assert hasattr(ctx, 'retrieval_latency')
    assert ctx.retrieval_latency is None


def test_capture_generation_metrics_success():
    mock_func = Mock(return_value="Test output")
    decorated_func = capture_generation_metrics(mock_func)
    
    result = decorated_func()
    
    assert result == "Test output"
    ctx = get_evaluation_context()
    assert hasattr(ctx, 'actual_output')
    assert ctx.actual_output == "Test output"
    assert hasattr(ctx, 'generation_latency')
    assert isinstance(ctx.generation_latency, float)


def test_capture_generation_metrics_exception():
    mock_func = Mock(side_effect=Exception("Generation error"))
    decorated_func = capture_generation_metrics(mock_func)
    
    with pytest.raises(Exception, match="Generation error"):
        decorated_func()
    
    ctx = get_evaluation_context()
    assert hasattr(ctx, 'actual_output')
    assert ctx.actual_output is None
    assert hasattr(ctx, 'generation_latency')
    assert ctx.generation_latency is None


def test_classify_question_technical():
    result = classify_question("配置报错", "如何解决error")
    assert result == '技术问题'
    
    result = classify_question("API接口问题", "日志分析")
    assert result == '技术问题'
    
    result = classify_question("代码运行失败", "参数配置错误")
    assert result == '技术问题'


def test_classify_question_usage():
    result = classify_question("怎么安装", "如何部署")
    assert result == '使用问题'
    
    result = classify_question("教程文档", "下载安装")
    assert result == '使用问题'
    
    result = classify_question("如何使用", "安装指南")
    assert result == '使用问题'


def test_classify_question_community():
    result = classify_question("规范要求", "PR提交审核")
    assert result == '社区规则'
    
    result = classify_question("规则说明", "审核流程")
    assert result == '社区规则'
    
    result = classify_question("提交规范", "PR审核要求")
    assert result == '社区规则'


def test_classify_question_other():
    result = classify_question("普通问题", "一般内容")
    assert result == '其他'
    
    result = classify_question("测试内容", "示例文本")
    assert result == '其他'


def test_capture_retrieval_metrics_with_args():
    mock_func = Mock(return_value=(["doc"], {"key": "value"}))
    decorated_func = capture_retrieval_metrics(mock_func)
    
    result = decorated_func("arg1", "arg2", kwarg1="kw1")
    
    mock_func.assert_called_once_with("arg1", "arg2", kwarg1="kw1")
    assert result == (["doc"], {"key": "value"})


def test_capture_generation_metrics_with_args():
    mock_func = Mock(return_value="Output")
    decorated_func = capture_generation_metrics(mock_func)
    
    result = decorated_func("input", param="value")
    
    mock_func.assert_called_once_with("input", param="value")
    assert result == "Output"


def test_thread_isolation():
    results = {}
    
    def thread_func(thread_id):
        mock_func = Mock(return_value=(["doc{}".format(thread_id)], {"id": thread_id}))
        decorated_func = capture_retrieval_metrics(mock_func)
        decorated_func()
        ctx = get_evaluation_context()
        results[thread_id] = {
            'retrieval_context': getattr(ctx, 'retrieval_context', None),
            'retrieval_data': getattr(ctx, 'retrieval_data', None)
        }
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=thread_func, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    for thread_id, data in results.items():
        assert data['retrieval_context'] == ["doc{}".format(thread_id)]
        assert data['retrieval_data']['id'] == thread_id