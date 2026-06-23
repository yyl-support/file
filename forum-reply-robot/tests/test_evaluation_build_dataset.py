import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock, create_autospec
from datetime import datetime, timedelta


class TestBuildDataset:
    def test_build_evaluation_dataset_success(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            (1, "Question 1", json.dumps(["doc1", "doc2"]), "Answer 1", "技术问题", datetime.now()),
            (2, "Question 2", json.dumps(["doc3"]), "Answer 2", "使用问题", datetime.now()),
            (3, "Question 3", None, "Answer 3", "其他", datetime.now()),
        ]
        
        mock_utils = MagicMock()
        mock_utils.load_config = MagicMock(return_value={
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test',
                'user': 'test',
                'password': 'test',
                'sslmode': 'prefer'
            }
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict('sys.modules', {'utils': mock_utils}):
                with patch('src.evaluation.build_dataset.psycopg2.connect', return_value=mock_conn):
                    from src.evaluation.build_dataset import build_evaluation_dataset
                    
                    result = build_evaluation_dataset(
                        days=30,
                        similarity_threshold=0.9,
                        min_samples_per_category=1,
                        max_samples_per_category=2,
                        output_dir=tmpdir,
                        config_path='config/config.yaml'
                    )
                    
                    assert result is not None
                    assert os.path.exists(result)
                    
                    with open(result, 'r', encoding='utf-8') as f:
                        dataset = json.load(f)
                        assert isinstance(dataset, list)
                        assert len(dataset) > 0
    
    def test_build_evaluation_dataset_with_deduplication(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            (1, "Question A", json.dumps(["doc1"]), "Answer 1", "技术问题", datetime.now()),
            (2, "Question A", json.dumps(["doc2"]), "Answer 2", "技术问题", datetime.now()),
            (3, "Question B", json.dumps(["doc3"]), "Answer 3", "使用问题", datetime.now()),
        ]
        
        mock_utils = MagicMock()
        mock_utils.load_config = MagicMock(return_value={
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test',
                'user': 'test',
                'password': 'test',
                'sslmode': 'prefer'
            }
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict('sys.modules', {'utils': mock_utils}):
                with patch('src.evaluation.build_dataset.psycopg2.connect', return_value=mock_conn):
                    from src.evaluation.build_dataset import build_evaluation_dataset
                    
                    result = build_evaluation_dataset(
                        days=30,
                        similarity_threshold=0.9,
                        min_samples_per_category=1,
                        max_samples_per_category=2,
                        output_dir=tmpdir,
                        config_path='config/config.yaml'
                    )
                    
                    assert result is not None
                    
                    with open(result, 'r', encoding='utf-8') as f:
                        dataset = json.load(f)
                        assert len(dataset) <= 2
    
    def test_build_evaluation_dataset_db_error(self):
        mock_utils = MagicMock()
        mock_utils.load_config = MagicMock(return_value={
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test',
                'user': 'test',
                'password': 'test',
                'sslmode': 'prefer'
            }
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict('sys.modules', {'utils': mock_utils}):
                with patch('src.evaluation.build_dataset.psycopg2.connect', side_effect=Exception("DB connection error")):
                    from src.evaluation.build_dataset import build_evaluation_dataset
                    
                    result = build_evaluation_dataset(
                        days=30,
                        output_dir=tmpdir,
                        config_path='config/config.yaml'
                    )
                    
                    assert result is None
    
    def test_similar_function(self):
        from src.evaluation.build_dataset import similar
        
        result = similar("Question A", "Question A")
        assert result == 1.0
        
        result = similar("Question A", "Question B")
        assert 0.8 < result < 1.0
        
        result = similar("Question A", "Different text")
        assert 0.2 < result < 0.5


class TestClassifyQuestion:
    def test_classify_question_technical(self):
        from src.ForumBot.evaluation_hooks import classify_question
        
        result = classify_question("配置报错", "参数设置问题")
        assert result == "技术问题"
        
        result = classify_question("API接口调用", "代码错误")
        assert result == "技术问题"
    
    def test_classify_question_usage(self):
        from src.ForumBot.evaluation_hooks import classify_question
        
        result = classify_question("如何安装", "怎么使用")
        assert result == "使用问题"
        
        result = classify_question("教程文档", "下载部署")
        assert result == "使用问题"
    
    def test_classify_question_community(self):
        from src.ForumBot.evaluation_hooks import classify_question
        
        result = classify_question("PR审核", "提交规范")
        assert result == "社区规则"
        
        result = classify_question("规则要求", "审核流程")
        assert result == "社区规则"
    
    def test_classify_question_other(self):
        from src.ForumBot.evaluation_hooks import classify_question
        
        result = classify_question("普通问题", "一般内容")
        assert result == "其他"