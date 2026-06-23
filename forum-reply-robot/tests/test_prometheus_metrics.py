import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ForumBot.prometheus_metrics import update_prometheus_metrics


def test_update_prometheus_metrics_with_retrieval_latency():
    evaluation_data = {
        'retrieval_latency': 2.5,
        'generation_latency': 0.0,
        'actual_output': 'Test output',
        'retrieval_context': ['doc1', 'doc2']
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_called_once_with(2.5)
                            mock_generation.observe.assert_not_called()
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_called_once_with(2)
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(2.5)


def test_update_prometheus_metrics_with_generation_latency():
    evaluation_data = {
        'retrieval_latency': 0.0,
        'generation_latency': 30.5,
        'actual_output': 'Generated text',
        'retrieval_context': None
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_not_called()
                            mock_generation.observe.assert_called_once_with(30.5)
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_not_called()
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(30.5)


def test_update_prometheus_metrics_with_empty_output():
    evaluation_data = {
        'retrieval_latency': 1.0,
        'generation_latency': 5.0,
        'actual_output': '',
        'retrieval_context': ['doc']
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_called_once_with(1.0)
                            mock_generation.observe.assert_called_once_with(5.0)
                            mock_empty.set.assert_called_once_with(1.0)
                            mock_doc_count.inc.assert_called_once_with(1)
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(6.0)


def test_update_prometheus_metrics_with_string_context():
    evaluation_data = {
        'retrieval_latency': 1.5,
        'generation_latency': 10.0,
        'actual_output': 'Output',
        'retrieval_context': 'Single document'
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_called_once_with(1.5)
                            mock_generation.observe.assert_called_once_with(10.0)
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_called_once_with(1)
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(11.5)


def test_update_prometheus_metrics_with_no_latency():
    evaluation_data = {
        'retrieval_latency': 0.0,
        'generation_latency': 0.0,
        'actual_output': 'Output',
        'retrieval_context': None
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_not_called()
                            mock_generation.observe.assert_not_called()
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_not_called()
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_not_called()


def test_update_prometheus_metrics_with_exception():
    evaluation_data = {
        'retrieval_latency': 'invalid',
        'generation_latency': 5.0,
        'actual_output': 'Output',
        'retrieval_context': None
    }
    
    with patch('src.ForumBot.prometheus_metrics.logger') as mock_logger:
        update_prometheus_metrics(evaluation_data)
        mock_logger.warning.assert_called()


def test_update_prometheus_metrics_with_none_retrieval_context():
    evaluation_data = {
        'retrieval_latency': 1.0,
        'generation_latency': 2.0,
        'actual_output': 'Output',
        'retrieval_context': None
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_called_once_with(1.0)
                            mock_generation.observe.assert_called_once_with(2.0)
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_not_called()
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(3.0)


def test_update_prometheus_metrics_with_empty_retrieval_context():
    evaluation_data = {
        'retrieval_latency': 1.0,
        'generation_latency': 2.0,
        'actual_output': 'Output',
        'retrieval_context': []
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_called_once_with(1.0)
                            mock_generation.observe.assert_called_once_with(2.0)
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_not_called()
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(3.0)


def test_update_prometheus_metrics_with_none_latencies():
    evaluation_data = {
        'retrieval_latency': None,
        'generation_latency': None,
        'actual_output': 'Output',
        'retrieval_context': None
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_not_called()
                            mock_generation.observe.assert_not_called()
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_not_called()
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_not_called()


def test_update_prometheus_metrics_with_one_none_latency():
    evaluation_data = {
        'retrieval_latency': None,
        'generation_latency': 30.0,
        'actual_output': 'Output',
        'retrieval_context': None
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_not_called()
                            mock_generation.observe.assert_called_once_with(30.0)
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_not_called()
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(30.0)


def test_update_prometheus_metrics_with_dict_retrieval_context():
    evaluation_data = {
        'retrieval_latency': 2.0,
        'generation_latency': 10.0,
        'actual_output': 'Output',
        'retrieval_context': {'chunk1': 'doc1', 'chunk2': 'doc2', 'chunk3': 'doc3'}
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_called_once_with(2.0)
                            mock_generation.observe.assert_called_once_with(10.0)
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_called_once_with(3)
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(12.0)


def test_update_prometheus_metrics_with_nested_dict_retrieval_context():
    evaluation_data = {
        'retrieval_latency': 1.5,
        'generation_latency': 5.0,
        'actual_output': 'Output',
        'retrieval_context': {'key1': {'nested': 'value'}, 'key2': 'simple'}
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_called_once_with(1.5)
                            mock_generation.observe.assert_called_once_with(5.0)
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_called_once_with(2)
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(6.5)


def test_update_prometheus_metrics_with_empty_dict_retrieval_context():
    evaluation_data = {
        'retrieval_latency': 1.0,
        'generation_latency': 2.0,
        'actual_output': 'Output',
        'retrieval_context': {}
    }
    
    with patch('src.ForumBot.prometheus_metrics.forum_retrieval_latency_seconds') as mock_retrieval:
        with patch('src.ForumBot.prometheus_metrics.forum_generation_latency_seconds') as mock_generation:
            with patch('src.ForumBot.prometheus_metrics.forum_empty_reply_rate') as mock_empty:
                with patch('src.ForumBot.prometheus_metrics.forum_retrieval_doc_count') as mock_doc_count:
                    with patch('src.ForumBot.prometheus_metrics.forum_processed_topic_count') as mock_topic_count:
                        with patch('src.ForumBot.prometheus_metrics.forum_end_to_end_latency_seconds') as mock_end_to_end:
                            update_prometheus_metrics(evaluation_data)
                            
                            mock_retrieval.observe.assert_called_once_with(1.0)
                            mock_generation.observe.assert_called_once_with(2.0)
                            mock_empty.set.assert_called_once_with(0.0)
                            mock_doc_count.inc.assert_called_once_with(0)
                            mock_topic_count.inc.assert_called_once_with(1)
                            mock_end_to_end.observe.assert_called_once_with(3.0)