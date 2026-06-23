import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.ForumBot.data_processor import DataProcessor


class TestNormalizeRetrievalContext:
    def test_normalize_dict_type_retrieval_context(self):
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            
            dict_context = {'chunk1': 'document one', 'chunk2': 'document two', 'chunk3': 'document three'}
            result = processor._normalize_retrieval_context(dict_context)
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert 'document one' in result
            assert 'document two' in result
            assert 'document three' in result
    
    def test_normalize_dict_with_nested_values(self):
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            
            dict_context = {'key1': {'nested': 'value'}, 'key2': 123, 'key3': 'simple'}
            result = processor._normalize_retrieval_context(dict_context)
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert any('nested' in str(r) for r in result)
            assert '123' in result
            assert 'simple' in result
    
    def test_normalize_list_type_retrieval_context(self):
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            
            list_context = ['doc1', 'doc2', 'doc3']
            result = processor._normalize_retrieval_context(list_context)
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert result == ['doc1', 'doc2', 'doc3']
    
    def test_normalize_string_type_retrieval_context(self):
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            
            string_context = "single document"
            result = processor._normalize_retrieval_context(string_context)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result == ['single document']
    
    def test_normalize_empty_string_retrieval_context(self):
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            
            result = processor._normalize_retrieval_context("")
            
            assert result is None
    
    def test_normalize_empty_list_retrieval_context(self):
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            
            result = processor._normalize_retrieval_context([])
            
            assert result is None
    
    def test_normalize_none_retrieval_context(self):
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            
            result = processor._normalize_retrieval_context(None)
            
            assert result is None


class TestSaveTokenUsageToDb:
    def test_save_token_usage_insert_new_record(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            token_usage = {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150,
                'model_calls': 2
            }
            
            processor.save_token_usage_to_db(123, token_usage)
            
            assert mock_cursor.execute.call_count == 1
            mock_conn.commit.assert_called_once()
            processor._close_db_connection.assert_called_once()
    
    def test_save_token_usage_update_existing_record(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            token_usage = {
                'prompt_tokens': 200,
                'completion_tokens': 100,
                'total_tokens': 300,
                'model_calls': 3
            }
            
            processor.save_token_usage_to_db(456, token_usage)
            
            assert mock_cursor.execute.call_count == 1
            mock_conn.commit.assert_called_once()
            processor._close_db_connection.assert_called_once()
    
    def test_save_token_usage_no_connection(self):
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=None)
            
            token_usage = {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150,
                'model_calls': 1
            }
            
            processor.save_token_usage_to_db(123, token_usage)
    
    def test_save_token_usage_with_missing_fields(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            token_usage = {}
            
            processor.save_token_usage_to_db(789, token_usage)
            
            assert mock_cursor.execute.call_count == 1
            mock_conn.commit.assert_called_once()
    
    def test_save_token_usage_with_none_token_usage(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            processor.save_token_usage_to_db(999, None)
            
            assert mock_cursor.execute.call_count == 1
            mock_conn.commit.assert_called_once()
            
            call_args = mock_cursor.execute.call_args[0][1]
            assert call_args[1] == 0
            assert call_args[2] == 0
            assert call_args[3] == 0
            assert call_args[4] == 0


class TestSaveEvaluationSample:
    def test_save_evaluation_sample_success(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test question",
                retrieval_context=["doc1", "doc2"],
                actual_output="Test answer",
                retrieval_latency=1.5,
                generation_latency=10.0,
                prompt_tokens=100,
                completion_tokens=50,
                category="技术问题"
            )
            
            assert result is True
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()
            mock_cursor.close.assert_called_once()
            processor._close_db_connection.assert_called_once()
    
    def test_save_evaluation_sample_with_dict_context(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            dict_context = {'chunk1': 'doc1', 'chunk2': 'doc2'}
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test question",
                retrieval_context=dict_context,
                actual_output="Test answer",
                retrieval_latency=1.5,
                generation_latency=10.0,
                prompt_tokens=100,
                completion_tokens=50,
                category="技术问题"
            )
            
            assert result is True
            mock_cursor.execute.assert_called_once()
            
            call_args = mock_cursor.execute.call_args[0][1]
            normalized_context = json.loads(call_args[2])
            assert isinstance(normalized_context, list)
            assert 'doc1' in normalized_context
            assert 'doc2' in normalized_context
    
    def test_save_evaluation_sample_with_nested_dict_context(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            nested_dict_context = {'key1': {'nested': 'value'}, 'key2': 'simple'}
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test question",
                retrieval_context=nested_dict_context,
                actual_output="Test answer",
                retrieval_latency=1.5,
                generation_latency=10.0,
                prompt_tokens=100,
                completion_tokens=50,
                category="技术问题"
            )
            
            assert result is True
            mock_cursor.execute.assert_called_once()
            
            call_args = mock_cursor.execute.call_args[0][1]
            normalized_context = json.loads(call_args[2])
            assert isinstance(normalized_context, list)
            assert len(normalized_context) == 2
    
    def test_save_evaluation_sample_no_connection(self):
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=None)
            
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test question",
                retrieval_context=["doc1"],
                actual_output="Test answer",
                retrieval_latency=1.0,
                generation_latency=5.0,
                prompt_tokens=50,
                completion_tokens=30,
                category="使用问题"
            )
            
            assert result is False
    
    def test_save_evaluation_sample_db_error(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test question",
                retrieval_context=None,
                actual_output="Test answer",
                retrieval_latency=0.0,
                generation_latency=0.0,
                prompt_tokens=0,
                completion_tokens=0,
                category="其他"
            )
            
            assert result is False
            mock_conn.rollback.assert_called_once()
            processor._close_db_connection.assert_called_once()
    
    def test_save_evaluation_sample_with_none_context(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test question",
                retrieval_context=None,
                actual_output="Test answer",
                retrieval_latency=0.0,
                generation_latency=0.0,
                prompt_tokens=0,
                completion_tokens=0,
                category="社区规则"
            )
            
            assert result is True
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()
    
    def test_save_evaluation_sample_with_string_context(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test question",
                retrieval_context="Single document",
                actual_output="Test answer",
                retrieval_latency=1.0,
                generation_latency=5.0,
                prompt_tokens=100,
                completion_tokens=50,
                category="技术问题"
            )
            
            assert result is True
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()

    def test_save_evaluation_sample_commit_error(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.commit.side_effect = Exception("Commit failed")
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test",
                retrieval_context=None,
                actual_output="Answer",
                retrieval_latency=0.0,
                generation_latency=0.0,
                prompt_tokens=0,
                completion_tokens=0,
                category="其他"
            )
            
            assert result is False
            mock_conn.rollback.assert_called_once()

    def test_save_evaluation_sample_with_empty_list_context(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test question",
                retrieval_context=[],
                actual_output="Test answer",
                retrieval_latency=0.0,
                generation_latency=0.0,
                prompt_tokens=0,
                completion_tokens=0,
                category="其他"
            )
            
            assert result is True
            call_args = mock_cursor.execute.call_args[0][1]
            assert call_args[2] is None

    def test_save_evaluation_sample_close_connection_error(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test",
                retrieval_context=["doc"],
                actual_output="Answer",
                retrieval_latency=1.0,
                generation_latency=1.0,
                prompt_tokens=10,
                completion_tokens=5,
                category="技术问题"
            )
            
            assert result is True
            processor._close_db_connection.assert_called_once()

    def test_save_evaluation_sample_with_all_categories(self):
        for category in ["技术问题", "使用问题", "社区规则", "其他"]:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            
            with patch('src.ForumBot.data_processor.ImageProcessor'):
                processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
                processor._get_db_connection = Mock(return_value=mock_conn)
                processor._close_db_connection = Mock()
                
                result = processor.save_evaluation_sample(
                    topic_id=123,
                    input_text=f"Test for {category}",
                    retrieval_context=["doc"],
                    actual_output="Answer",
                    retrieval_latency=1.0,
                    generation_latency=1.0,
                    prompt_tokens=10,
                    completion_tokens=5,
                    category=category
                )
                
                assert result is True
                call_args = mock_cursor.execute.call_args[0][1]
                assert call_args[8] == category


class TestCreateTablesMigration:
    def test_create_tables_adds_unique_constraint_when_missing(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = None
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            processor.create_tables()
            
            executed_sqls = [call[0][0] if call[0] else '' for call in mock_cursor.execute.call_args_list]
            
            assert any('SELECT conname FROM pg_constraint' in sql for sql in executed_sqls)
            assert any('ALTER TABLE consume_tokens_topic' in sql and 'UNIQUE (topic_id)' in sql for sql in executed_sqls)
    
    def test_create_tables_skips_constraint_when_exists(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = ('consume_tokens_topic_topic_id_key',)
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            processor = DataProcessor(config={'database': {'host': 'localhost', 'port': 5432, 'database': 'test', 'user': 'test', 'password': 'test', 'sslmode': 'prefer'}})
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            processor.create_tables()
            
            executed_sqls = [call[0][0] if call[0] else '' for call in mock_cursor.execute.call_args_list]
            
            assert any('SELECT conname FROM pg_constraint' in sql for sql in executed_sqls)
            assert not any('ALTER TABLE consume_tokens_topic' in sql and 'UNIQUE (topic_id)' in sql for sql in executed_sqls)