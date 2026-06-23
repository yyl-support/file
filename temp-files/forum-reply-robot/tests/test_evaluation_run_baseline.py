import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock


class TestRunBaselineEvaluation:
    @patch('src.evaluation.run_baseline.load_config')
    @patch('src.evaluation.run_baseline.OpenAI')
    def test_run_baseline_evaluation_success(self, mock_openai, mock_load_config):
        mock_load_config.return_value = {
            'api': {
                'model_name': 'test-model',
                'base_url': 'https://test.api.com',
                'api_key': 'test-key'
            }
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "0.8"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = os.path.join(tmpdir, 'dataset.json')
            dataset = [
                {
                    'input': 'Question 1',
                    'retrieval_context': ['doc1', 'doc2'],
                    'actual_output': 'Answer 1',
                    'category': '技术问题',
                    'topic_id': 1
                },
                {
                    'input': 'Question 2',
                    'retrieval_context': ['doc3'],
                    'actual_output': 'Answer 2',
                    'category': '使用问题',
                    'topic_id': 2
                }
            ]
            
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f)
            
            from src.evaluation.run_baseline import run_baseline_evaluation
            
            result = run_baseline_evaluation(
                dataset_path=dataset_path,
                config_path='config/config.yaml',
                output_dir=tmpdir
            )
            
            assert result is not None
            assert os.path.exists(result)
            
            with open(result, 'r', encoding='utf-8') as f:
                report_content = f.read()
                assert '答案相关性指标' in report_content
                assert '忠实性指标' in report_content
                assert '上下文精确率指标' in report_content
                assert '分类别统计' in report_content
    
    @patch('src.evaluation.run_baseline.load_config')
    def test_run_baseline_evaluation_file_not_found(self, mock_load_config):
        mock_load_config.return_value = {
            'api': {
                'model_name': 'test-model',
                'base_url': 'https://test.api.com',
                'api_key': 'test-key'
            }
        }
        
        from src.evaluation.run_baseline import run_baseline_evaluation
        
        result = run_baseline_evaluation(
            dataset_path='/nonexistent/dataset.json',
            config_path='config/config.yaml',
            output_dir='/tmp'
        )
        
        assert result is None
    
    @patch('src.evaluation.run_baseline.load_config')
    @patch('src.evaluation.run_baseline.OpenAI')
    def test_run_baseline_evaluation_with_empty_dataset(self, mock_openai, mock_load_config):
        mock_load_config.return_value = {
            'api': {
                'model_name': 'test-model',
                'base_url': 'https://test.api.com',
                'api_key': 'test-key'
            }
        }
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = os.path.join(tmpdir, 'empty_dataset.json')
            
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            
            from src.evaluation.run_baseline import run_baseline_evaluation
            
            result = run_baseline_evaluation(
                dataset_path=dataset_path,
                config_path='config/config.yaml',
                output_dir=tmpdir
            )
            
            assert result is not None
    
    @patch('src.evaluation.run_baseline.load_config')
    @patch('src.evaluation.run_baseline.OpenAI')
    def test_run_baseline_evaluation_with_string_context(self, mock_openai, mock_load_config):
        mock_load_config.return_value = {
            'api': {
                'model_name': 'test-model',
                'base_url': 'https://test.api.com',
                'api_key': 'test-key'
            }
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "7"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = os.path.join(tmpdir, 'dataset_string_context.json')
            dataset = [
                {
                    'input': 'Question',
                    'retrieval_context': 'Single document string',
                    'actual_output': 'Answer',
                    'category': '使用问题',
                    'topic_id': 1
                }
            ]
            
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f)
            
            from src.evaluation.run_baseline import run_baseline_evaluation
            
            result = run_baseline_evaluation(
                dataset_path=dataset_path,
                config_path='config/config.yaml',
                output_dir=tmpdir
            )
            
            assert result is not None
    
    @patch('src.evaluation.run_baseline.load_config')
    @patch('src.evaluation.run_baseline.OpenAI')
    def test_run_baseline_evaluation_with_dict_context(self, mock_openai, mock_load_config):
        mock_load_config.return_value = {
            'api': {
                'model_name': 'test-model',
                'base_url': 'https://test.api.com',
                'api_key': 'test-key'
            }
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "0.9"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = os.path.join(tmpdir, 'dataset_dict_context.json')
            dataset = [
                {
                    'input': 'Question',
                    'retrieval_context': {'chunk1': 'doc1', 'chunk2': 'doc2'},
                    'actual_output': 'Answer',
                    'category': '技术问题',
                    'topic_id': 1
                }
            ]
            
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f)
            
            from src.evaluation.run_baseline import run_baseline_evaluation
            
            result = run_baseline_evaluation(
                dataset_path=dataset_path,
                config_path='config/config.yaml',
                output_dir=tmpdir
            )
            
            assert result is not None
    
    @patch('src.evaluation.run_baseline.load_config')
    @patch('src.evaluation.run_baseline.OpenAI')
    def test_run_baseline_evaluation_with_llm_failure(self, mock_openai, mock_load_config):
        mock_load_config.return_value = {
            'api': {
                'model_name': 'test-model',
                'base_url': 'https://test.api.com',
                'api_key': 'test-key'
            }
        }
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = os.path.join(tmpdir, 'dataset.json')
            dataset = [
                {
                    'input': 'Question',
                    'retrieval_context': ['doc'],
                    'actual_output': 'Answer',
                    'category': '技术问题',
                    'topic_id': 1
                }
            ]
            
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f)
            
            from src.evaluation.run_baseline import run_baseline_evaluation
            
            result = run_baseline_evaluation(
                dataset_path=dataset_path,
                config_path='config/config.yaml',
                output_dir=tmpdir
            )
            
            assert result is not None
            with open(result, 'r', encoding='utf-8') as f:
                report_content = f.read()
                assert '无有效评分' in report_content or '平均得分' in report_content


class TestExtractScore:
    def test_extract_score_with_decimal(self):
        from src.evaluation.run_baseline import extract_score
        
        result = extract_score("0.85")
        assert result == 0.85
    
    def test_extract_score_with_integer(self):
        from src.evaluation.run_baseline import extract_score
        
        result = extract_score("8")
        assert result == 0.8
    
    def test_extract_score_with_invalid_input(self):
        from src.evaluation.run_baseline import extract_score
        
        result = extract_score("invalid")
        assert result == 0.5
    
    def test_extract_score_with_text_wrapping(self):
        from src.evaluation.run_baseline import extract_score
        
        result = extract_score("评分是 0.9")
        assert result == 0.9
    
    def test_extract_score_out_of_range(self):
        from src.evaluation.run_baseline import extract_score
        
        result = extract_score("15")
        assert result == 1.0


class TestNormalizeRetrievalContext:
    def test_normalize_list_context(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        result = normalize_retrieval_context(['doc1', 'doc2'])
        assert result == ['doc1', 'doc2']
    
    def test_normalize_string_context(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        result = normalize_retrieval_context('single doc')
        assert result == ['single doc']
    
    def test_normalize_dict_context(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        result = normalize_retrieval_context({'k1': 'v1', 'k2': 'v2'})
        assert result == ['v1', 'v2']
    
    def test_normalize_nested_dict_context(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        nested_dict = {'key1': {'nested': 'value'}, 'key2': 123, 'key3': 'simple'}
        result = normalize_retrieval_context(nested_dict)
        assert isinstance(result, list)
        assert len(result) == 3
        assert any('nested' in str(r) for r in result)
        assert '123' in result
        assert 'simple' in result
    
    def test_normalize_dict_with_empty_values(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        result = normalize_retrieval_context({'k1': '', 'k2': 'v2'})
        assert '' in result
        assert 'v2' in result
    
    def test_normalize_empty_context(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        result = normalize_retrieval_context('')
        assert result == []
    
    def test_normalize_none_context(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        result = normalize_retrieval_context(None)
        assert result == []
    
    def test_normalize_empty_list_context(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        result = normalize_retrieval_context([])
        assert result == []
    
    def test_normalize_empty_dict_context(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        result = normalize_retrieval_context({})
        assert result == []
    
    def test_normalize_list_with_mixed_types(self):
        from src.evaluation.run_baseline import normalize_retrieval_context
        
        result = normalize_retrieval_context(['str', 123, {'nested': 'value'}])
        assert len(result) == 3
        assert 'str' in result
        assert '123' in result
        assert any('nested' in str(r) for r in result)


class TestTemplates:
    def test_templates_exist(self):
        from src.evaluation.templates import (
            ANSWER_RELEVANCY_TEMPLATE,
            FAITHFULNESS_TEMPLATE,
            CONTEXT_PRECISION_TEMPLATE
        )
        
        assert ANSWER_RELEVANCY_TEMPLATE is not None
        assert FAITHFULNESS_TEMPLATE is not None
        assert CONTEXT_PRECISION_TEMPLATE is not None
        assert isinstance(ANSWER_RELEVANCY_TEMPLATE, str)
        assert isinstance(FAITHFULNESS_TEMPLATE, str)
        assert isinstance(CONTEXT_PRECISION_TEMPLATE, str)
        assert len(ANSWER_RELEVANCY_TEMPLATE) > 0
        assert len(FAITHFULNESS_TEMPLATE) > 0
        assert len(CONTEXT_PRECISION_TEMPLATE) > 0
    
    def test_answer_relevancy_template_format(self):
        from src.evaluation.templates import ANSWER_RELEVANCY_TEMPLATE
        
        formatted = ANSWER_RELEVANCY_TEMPLATE.format(
            input="测试问题",
            actual_output="测试回答"
        )
        assert "测试问题" in formatted
        assert "测试回答" in formatted
    
    def test_faithfulness_template_format(self):
        from src.evaluation.templates import FAITHFULNESS_TEMPLATE
        
        formatted = FAITHFULNESS_TEMPLATE.format(
            actual_output="测试回答",
            retrieval_context="测试上下文"
        )
        assert "测试回答" in formatted
        assert "测试上下文" in formatted
    
    def test_context_precision_template_format(self):
        from src.evaluation.templates import CONTEXT_PRECISION_TEMPLATE
        
        formatted = CONTEXT_PRECISION_TEMPLATE.format(
            retrieval_context="测试上下文",
            input="测试问题"
        )
        assert "测试上下文" in formatted
        assert "测试问题" in formatted


class TestLLMJudge:
    @patch('src.evaluation.run_baseline.OpenAI')
    def test_llm_judge_success(self, mock_openai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "0.8"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        from src.evaluation.run_baseline import llm_judge
        
        result = llm_judge(mock_client, 'test-model', 'test prompt')
        assert result == 0.8
    
    @patch('src.evaluation.run_baseline.OpenAI')
    def test_llm_judge_failure(self, mock_openai):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai.return_value = mock_client
        
        from src.evaluation.run_baseline import llm_judge
        
        result = llm_judge(mock_client, 'test-model', 'test prompt')
        assert result is None