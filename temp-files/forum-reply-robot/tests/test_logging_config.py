import logging
import os
import tempfile

from src.ForumBot.logging_config import setup_logger


class TestSetupLogger:
    @staticmethod
    def _close_handlers(logger):
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)

    def test_setup_logger_basic(self):
        logger = setup_logger("test_logger")
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1

    def test_setup_logger_with_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as file_obj:
            log_file = file_obj.name

        try:
            logger = setup_logger("test_file_logger", log_file=log_file)
            assert logger.name == "test_file_logger"
            assert len(logger.handlers) == 2

            logger.info("Test message")
            assert os.path.exists(log_file)

            with open(log_file, "r", encoding="utf-8") as file_obj:
                content = file_obj.read()
            assert "Test message" in content
        finally:
            if "logger" in locals():
                self._close_handlers(logger)
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_setup_logger_with_directory_creation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "subdir", "test.log")
            logger = setup_logger("test_dir_logger", log_file=log_file)

            assert os.path.exists(os.path.dirname(log_file))
            assert os.path.exists(log_file)
            self._close_handlers(logger)

    def test_setup_logger_custom_level(self):
        logger = setup_logger("test_level_logger", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_setup_logger_no_propagate(self):
        logger = setup_logger("test_no_propagate")
        assert logger.propagate is False

    def test_setup_logger_multiple_calls(self):
        logger1 = setup_logger("test_duplicate")
        initial_handlers = len(logger1.handlers)

        logger2 = setup_logger("test_duplicate")
        assert len(logger2.handlers) == initial_handlers * 2
        self._close_handlers(logger2)
