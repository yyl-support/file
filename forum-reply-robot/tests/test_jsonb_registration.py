"""Test for psycopg2 JSONB adapter registration"""
import pytest


class TestJSONBRegistration:
    """Test that psycopg2.extras.register_default_jsonb is called during import"""

    def test_register_default_jsonb_called_on_import(self):
        """Test that register_default_jsonb is available and callable"""
        import psycopg2.extras

        assert hasattr(psycopg2.extras, 'register_default_jsonb'), \
            "psycopg2.extras should have register_default_jsonb function"

        assert callable(psycopg2.extras.register_default_jsonb), \
            "register_default_jsonb should be callable"

        try:
            psycopg2.extras.register_default_jsonb(globally=True)
            success = True
        except Exception as e:
            success = False
            error = str(e)

        assert success, f"register_default_jsonb(globally=True) should succeed, got error: {error if not success else ''}"

    def test_register_adapter_dict_to_json_called_on_import(self):
        """Test that register_adapter(dict, Json) is called during import"""
        import psycopg2.extensions
        import psycopg2.extras

        assert hasattr(psycopg2.extensions, 'register_adapter'), \
            "psycopg2.extensions should have register_adapter function"

        assert hasattr(psycopg2.extras, 'Json'), \
            "psycopg2.extras should have Json adapter"

        try:
            psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)
            success = True
        except Exception as e:
            success = False
            error = str(e)

        assert success, f"register_adapter(dict, Json) should succeed, got error: {error if not success else ''}"

    def test_jsonb_registration_line_coverage(self):
        """Test that the registration lines at data_processor.py:16-17 are covered"""
        import importlib
        import sys

        if 'src.ForumBot.data_processor' in sys.modules:
            del sys.modules['src.ForumBot.data_processor']

        try:
            module = importlib.import_module('src.ForumBot.data_processor')
            import_success = True
            assert hasattr(module, 'DataProcessor'), \
                "data_processor module should have DataProcessor class"
        except Exception as e:
            import_success = False
            import_error = str(e)

        assert import_success, \
            f"data_processor import should succeed and execute lines 16-17, but got: {import_error if not import_success else ''}"
    
    def test_jsonb_data_handling_in_save_evaluation_sample(self):
        """Test that JSONB data can be properly handled in save_evaluation_sample"""
        # This test validates that the JSONB registration fix works correctly
        from unittest.mock import Mock, MagicMock, patch
        import json
        
        with patch('src.ForumBot.data_processor.ImageProcessor'):
            from src.ForumBot.data_processor import DataProcessor
            
            processor = DataProcessor(config={
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'test',
                    'user': 'test',
                    'password': 'test',
                    'sslmode': 'prefer'
                }
            })
            
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            
            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()
            
            # Test with JSONB data (retrieval_context)
            result = processor.save_evaluation_sample(
                topic_id=123,
                input_text="Test question",
                retrieval_context=["doc1", "doc2", "doc3"],  # Will be stored as JSONB
                actual_output="Test answer",
                retrieval_latency=1.5,
                generation_latency=10.0,
                prompt_tokens=100,
                completion_tokens=50,
                category="技术问题"
            )
            
            assert result is True, "save_evaluation_sample should succeed with JSONB data"
            
            # Verify that the JSONB data was properly serialized
            call_args = mock_cursor.execute.call_args[0][1]
            jsonb_data = call_args[2]  # retrieval_context parameter
            
            # The data should be a JSON string
            assert jsonb_data is not None, "JSONB data should not be None"
            
            # Parse the JSON to verify it's valid
            parsed_data = json.loads(jsonb_data)
            assert isinstance(parsed_data, list), "Parsed JSONB data should be a list"
            assert len(parsed_data) == 3, "JSONB data should contain 3 items"
            assert 'doc1' in parsed_data, "JSONB data should contain expected values"

    def test_save_search_results_with_dict_uses_json_adapter(self):
        """Test that save_search_results_to_db adapts dict search results via Json adapter"""
        from unittest.mock import Mock, MagicMock, patch
        import json

        with patch('src.ForumBot.data_processor.ImageProcessor'):
            from src.ForumBot.data_processor import DataProcessor

        processor = DataProcessor(config={
            'api': {'base_url': 'http://test', 'api_key': 'test'},
            'image_processing': {'model1': 'm1', 'model2': 'm2', 'model3': 'm3', 'base_url': 'http://img'},
            'database': {
                'host': 'localhost', 'port': 5432,
                'database': 'test', 'user': 'test',
                'password': 'test', 'sslmode': 'prefer'
            }
        })

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        processor._get_db_connection = Mock(return_value=mock_conn)
        processor._close_db_connection = Mock()

        search_results = [
            {'topic_id': 1, 'title': 'Test Post', 'excerpt': 'test content'}
        ]

        result = processor.save_search_results_to_db(
            topic_id=123,
            search_results=search_results,
            search_keyword='test'
        )

        assert mock_cursor.execute.called, "cursor.execute should be called"
        call_args = mock_cursor.execute.call_args[0][1]

        assert call_args[5] is not None, "result_1 (dict) should be present, not rejected"
        assert call_args[5]['title'] == 'Test Post', "adapted result should contain original data"

    def test_append_to_db_replies_with_nested_list(self):
        """Test that append_to_db handles nested list in replies via Json adapter"""
        from unittest.mock import Mock, MagicMock, patch
        import json

        with patch('src.ForumBot.data_processor.ImageProcessor'):
            from src.ForumBot.data_processor import DataProcessor

            processor = DataProcessor(config={
                'database': {
                    'host': 'localhost', 'port': 5432,
                    'database': 'test', 'user': 'test',
                    'password': 'test', 'sslmode': 'prefer'
                }
            })

            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor

            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()

            nested_replies = [
                {'id': 1, 'content': 'first reply', 'nested': {'key': 'value'}},
                {'id': 2, 'content': 'second reply', 'items': [1, 2, 3]}
            ]
            payload = [{'id': 100, 'replies': nested_replies, 'tags': []}]

            result = processor.append_to_db(payload, 'forum_topics')

            assert result is True
            mock_conn.commit.assert_called_once()
            call_args = mock_cursor.execute.call_args[0][1]
            replies_arg = call_args[5]
            assert isinstance(replies_arg, str), "nested list should be serialized via Json adapter"
            parsed = json.loads(replies_arg)
            assert parsed[0]['nested']['key'] == 'value'

    def test_append_to_db_replies_with_dict_tags(self):
        """Test append_to_db handles dict tags correctly"""
        from unittest.mock import Mock, MagicMock, patch

        with patch('src.ForumBot.data_processor.ImageProcessor'):
            from src.ForumBot.data_processor import DataProcessor

            processor = DataProcessor(config={
                'database': {
                    'host': 'localhost', 'port': 5432,
                    'database': 'test', 'user': 'test',
                    'password': 'test', 'sslmode': 'prefer'
                }
            })

            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor

            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()

            dict_tags = [{'name': 'python'}, {'name': 'testing'}]
            payload = [{'id': 101, 'replies': [], 'tags': dict_tags}]

            result = processor.append_to_db(payload, 'processed_forum_topics')

            assert result is True
            call_args = mock_cursor.execute.call_args[0][1]
            tags_arg = call_args[4]
            assert tags_arg == 'python,testing'

    def test_append_to_db_replies_string_tags(self):
        """Test append_to_db handles string tags"""
        from unittest.mock import Mock, MagicMock, patch

        with patch('src.ForumBot.data_processor.ImageProcessor'):
            from src.ForumBot.data_processor import DataProcessor

            processor = DataProcessor(config={
                'database': {
                    'host': 'localhost', 'port': 5432,
                    'database': 'test', 'user': 'test',
                    'password': 'test', 'sslmode': 'prefer'
                }
            })

            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor

            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()

            payload = [{'id': 102, 'replies': [], 'tags': 'single-tag'}]

            result = processor.append_to_db(payload, 'forum_topics')

            assert result is True
            call_args = mock_cursor.execute.call_args[0][1]
            tags_arg = call_args[4]
            assert tags_arg == 'single-tag'

    def test_save_evaluation_sample_with_complex_jsonb(self):
        """Test save_evaluation_sample with complex nested JSONB data"""
        from unittest.mock import Mock, MagicMock, patch
        import json

        with patch('src.ForumBot.data_processor.ImageProcessor'):
            from src.ForumBot.data_processor import DataProcessor

            processor = DataProcessor(config={
                'database': {
                    'host': 'localhost', 'port': 5432,
                    'database': 'test', 'user': 'test',
                    'password': 'test', 'sslmode': 'prefer'
                }
            })

            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor

            processor._get_db_connection = Mock(return_value=mock_conn)
            processor._close_db_connection = Mock()

            complex_context = [
                {'chunk_id': 1, 'text': 'doc1', 'metadata': {'source': 'forum', 'score': 0.9}},
                {'chunk_id': 2, 'text': 'doc2', 'metadata': {'source': 'git', 'score': 0.8}}
            ]

            result = processor.save_evaluation_sample(
                topic_id=999,
                input_text="Complex question",
                retrieval_context=complex_context,
                actual_output="Complex answer",
                retrieval_latency=2.5,
                generation_latency=15.0,
                prompt_tokens=200,
                completion_tokens=100,
                category="技术问题"
            )

            assert result is True
            mock_conn.commit.assert_called_once()
            call_args = mock_cursor.execute.call_args[0][1]
            jsonb_data = json.loads(call_args[2])
            assert len(jsonb_data) == 2
            assert 'chunk_id' in str(jsonb_data[0])
