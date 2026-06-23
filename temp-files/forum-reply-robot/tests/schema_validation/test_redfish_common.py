import json

from src.ForumBot.SchemaValidation import redfish_common


def test_configure_from_dict_and_init_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(redfish_common.Config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(redfish_common.Config, "LOG_DIR", tmp_path / "log")
    monkeypatch.setattr(redfish_common.Config, "OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(redfish_common.Config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(redfish_common.Config, "URI_SAMPLES_DIR", tmp_path / "samples")

    redfish_common.Config.configure_from_dict(
        {
            "api_key": "k",
            "base_url": "https://api.example.com",
            "model": "m",
            "schema_dir": "schemas",
            "output_dir": "result-dir",
            "disable_file_output": False,
            "max_retry": 2,
            "retry_delay": 1,
        }
    )
    redfish_common.Config.init_directories()

    assert redfish_common.Config.MODELSCOPE_API_KEY == "k"
    assert redfish_common.Config.MODELSCOPE_BASE_URL == "https://api.example.com"
    assert redfish_common.Config.MODELSCOPE_MODEL == "m"
    assert str(redfish_common.Config.SCHEMA_DIR).endswith("schemas")
    assert redfish_common.Config.OUTPUT_DIR.exists()
    assert redfish_common.Config.LOG_DIR.exists()


def test_json_and_csv_helpers_round_trip(tmp_path):
    json_file = tmp_path / "data.json"
    csv_file = tmp_path / "rows.csv"
    redfish_common.save_json({"ok": True}, json_file)
    csv_file.write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")

    assert redfish_common.load_json(json_file) == {"ok": True}
    assert redfish_common.load_csv(csv_file)[0]["name"] == "Alice"
    assert redfish_common.load_csv_row(csv_file, "2")["name"] == "Bob"


def test_formatting_and_filename_helpers():
    formatted = redfish_common.format_time(65)
    assert "1" in formatted and "5" in formatted
    assert redfish_common.sanitize_filename("a/b:c*?") == "a_b_c__"
    assert redfish_common.safe_title("Title/With:Chars") == "Title_With_Chars"


def test_validation_result():
    result = redfish_common.ValidationResult()
    result.add_error("Type", "bad")
    result.add_warning("Warn", "careful")

    assert result.errors[0]["type"] == "Type"
    assert result.warnings[0]["type"] == "Warn"
    assert result.is_fail is False
    assert result.is_error is False


def test_setup_logger(tmp_path):
    log_file = tmp_path / "test.log"
    logger = redfish_common.setup_logger("schema-test", str(log_file), console_output=False)
    logger.info("hello")

    contents = log_file.read_text(encoding="utf-8")
    assert "hello" in contents
