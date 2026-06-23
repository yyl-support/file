import os
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.update_lightrag.update_time import get_last_update_time, save_last_update_time


class TestUpdateTime:
    def test_save_last_update_time_success(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            save_last_update_time(temp_path)

            assert os.path.exists(temp_path)
            with open(temp_path, "r", encoding="utf-8") as file_obj:
                content = file_obj.read()
            assert len(content) > 0
            assert "T" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch("builtins.open")
    def test_save_last_update_time_exception(self, mock_open):
        mock_open.side_effect = Exception("File write error")
        save_last_update_time("/fake/path.txt")

    def test_get_last_update_time_file_exists(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            test_time = "2024-01-01T12:00:00.000000+00:00"
            with open(temp_path, "w", encoding="utf-8") as file_obj:
                file_obj.write(test_time)

            assert get_last_update_time(temp_path) == test_time
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_last_update_time_file_not_found(self):
        assert get_last_update_time("/nonexistent/file.txt") is None

    def test_get_last_update_time_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            with open(temp_path, "w", encoding="utf-8") as file_obj:
                file_obj.write("")

            assert get_last_update_time(temp_path) == ""
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_last_update_time_empty_file_with_default(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            with open(temp_path, "w", encoding="utf-8") as file_obj:
                file_obj.write("")

            default_time = "2024-01-01T00:00:00.000000+00:00"
            assert get_last_update_time(temp_path, default_time) == default_time
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_last_update_time_with_default(self):
        default_time = "2024-01-01T00:00:00.000000+00:00"
        assert get_last_update_time("/nonexistent/file.txt", default_time) == default_time

    @patch("builtins.open")
    def test_get_last_update_time_exception(self, mock_open):
        mock_open.side_effect = Exception("File read error")
        assert get_last_update_time("/fake/path.txt") is None

    @patch("builtins.open")
    def test_get_last_update_time_exception_with_default(self, mock_open):
        mock_open.side_effect = Exception("File read error")
        default_time = "2024-01-01T00:00:00.000000+00:00"
        assert get_last_update_time("/fake/path.txt", default_time) == default_time
