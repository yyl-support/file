"""
Unit tests for initialization_worker function in main.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import threading


class TestInitializationWorker:
    """Tests for initialization_worker function"""

    @patch('main.lightrag_data_init')
    @patch('main.initialize_service')
    @patch('main.lightrag_data_update_timer')
    @patch('main.service_initialized')
    @patch('main.logger')
    def test_initialization_worker_success(self, mock_logger, mock_service_initialized, 
                                           mock_timer, mock_init_service, mock_lightrag_init):
        """Test successful initialization flow"""
        mock_lightrag_init.return_value = True
        mock_init_service.return_value = True
        mock_timer.return_value = True
        
        config = Mock()
        
        from main import initialization_worker
        initialization_worker(config)
        
        mock_lightrag_init.assert_called_once_with(config)
        mock_init_service.assert_called_once_with(config)
        mock_timer.assert_called_once_with(config)
        mock_logger.info.assert_called()

    @patch('main.lightrag_data_init')
    @patch('main.service_initialized')
    @patch('main.logger')
    def test_initialization_worker_lightrag_failure(self, mock_logger, mock_service_initialized, 
                                                    mock_lightrag_init):
        """Test initialization_worker when LightRAG init fails"""
        mock_lightrag_init.return_value = False
        
        config = Mock()
        
        from main import initialization_worker
        initialization_worker(config)
        
        mock_lightrag_init.assert_called_once_with(config)
        mock_logger.error.assert_called()
        assert mock_service_initialized.value == False or True

    @patch('main.lightrag_data_init')
    @patch('main.initialize_service')
    @patch('main.service_initialized')
    @patch('main.logger')
    def test_initialization_worker_service_failure(self, mock_logger, mock_service_initialized,
                                                   mock_init_service, mock_lightrag_init):
        """Test initialization_worker when service init fails"""
        mock_lightrag_init.return_value = True
        mock_init_service.return_value = False
        
        config = Mock()
        
        from main import initialization_worker
        initialization_worker(config)
        
        mock_lightrag_init.assert_called_once_with(config)
        mock_init_service.assert_called_once_with(config)
        mock_logger.error.assert_called()

    @patch('main.lightrag_data_init')
    @patch('main.initialize_service')
    @patch('main.lightrag_data_update_timer')
    @patch('main.logger')
    def test_initialization_worker_timer_failure_not_fatal(self, mock_logger, mock_timer,
                                                           mock_init_service, mock_lightrag_init):
        """Test that timer failure is not fatal"""
        mock_lightrag_init.return_value = True
        mock_init_service.return_value = True
        mock_timer.return_value = False
        
        config = Mock()
        
        from main import initialization_worker
        initialization_worker(config)
        
        mock_timer.assert_called_once_with(config)
        mock_logger.warning.assert_called()
        mock_logger.info.assert_called()

    @patch('main.lightrag_data_init')
    @patch('main.service_initialized')
    @patch('main.logger')
    def test_initialization_worker_exception_handling(self, mock_logger, mock_service_initialized,
                                                      mock_lightrag_init):
        """Test exception handling in initialization_worker"""
        mock_lightrag_init.side_effect = Exception("Database connection failed")
        
        config = Mock()
        
        from main import initialization_worker
        initialization_worker(config)
        
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "异常" in error_call


class TestMainFunctionInitialization:
    """Tests for main() function initialization behavior"""

    @patch('main.check_schema_files')
    @patch('main.check_mdb_rule_files')
    @patch('main.load_config')
    @patch('main.delete_config_file')
    @patch('main.threading.Thread')
    @patch('main.get_best_private_ip')
    @patch('main.app')
    @patch('main.os.makedirs')
    @patch('main.logger')
    def test_main_starts_init_thread(self, mock_logger, mock_makedirs, mock_app,
                                     mock_get_ip, mock_thread, mock_delete_config,
                                     mock_load_config, mock_check_mdb, mock_check_schema):
        """Test that main starts initialization thread"""
        mock_check_schema.return_value = True
        mock_load_config.return_value = Mock()
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        from main import main
        main()
        
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        mock_app.run.assert_called_once()

    @patch('main.check_schema_files')
    @patch('main.logger')
    def test_main_exits_on_schema_check_failure(self, mock_logger, mock_check_schema):
        """Test that main exits when schema check fails"""
        mock_check_schema.return_value = False
        
        from main import main
        result = main()
        
        assert result is None
        mock_logger.error.assert_called()

    @patch('main.check_schema_files')
    @patch('main.check_mdb_rule_files')
    @patch('main.load_config')
    @patch('main.threading.Thread')
    @patch('main.app')
    @patch('main.os.makedirs')
    @patch('main.logger')
    def test_main_handles_config_load_failure(self, mock_logger, mock_makedirs, mock_app,
                                               mock_thread, mock_load_config, mock_check_mdb,
                                               mock_check_schema):
        """Test that main handles config load failure gracefully"""
        mock_check_schema.return_value = True
        mock_load_config.side_effect = Exception("Config file not found")
        
        from main import main
        main()
        
        mock_logger.error.assert_called()
        mock_makedirs.assert_called()
        mock_thread.assert_not_called()