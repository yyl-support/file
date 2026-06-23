"""
覆盖 main.main() 中 Flask SECRET_KEY 加载逻辑（main.py:342-356）的单元测试。

load_config / delete_config_file / init_db_connection_pool 在 main() 内通过
`from src.utils import ...` 局部导入，因此必须 patch `src.utils.*`（而非 main.*）。
通过 external_api.enabled=False 跳过 RAG 注册，并 patch 线程与 app.run，
使 main() 执行到 SECRET_KEY 分支后安全返回。
"""
import os
from contextlib import ExitStack
from unittest.mock import patch

import main


def _run_main(config, env):
    with ExitStack() as stack:
        stack.enter_context(patch("main.check_schema_files", return_value=True))
        stack.enter_context(patch("main.check_mdb_rule_files"))
        stack.enter_context(patch("src.utils.load_config", return_value=config))
        stack.enter_context(patch("src.utils.delete_config_file"))
        stack.enter_context(patch("src.utils.init_db_connection_pool", return_value=True))
        stack.enter_context(patch("main.os.makedirs"))
        stack.enter_context(patch("main.threading.Thread"))
        stack.enter_context(patch("main.get_best_private_ip", return_value="127.0.0.1"))
        stack.enter_context(patch.object(main.app, "run"))
        mock_logger = stack.enter_context(patch("main.logger"))
        stack.enter_context(patch.dict(os.environ, env, clear=True))
        main.app.config["SECRET_KEY"] = None
        main.main()
        return mock_logger


def test_secret_key_from_config():
    _run_main({"flask_secret_key": "cfg-key", "external_api": {"enabled": False}}, {})
    assert main.app.config["SECRET_KEY"] == "cfg-key"


def test_secret_key_from_env():
    _run_main({"external_api": {"enabled": False}}, {"FLASK_SECRET_KEY": "env-key"})
    assert main.app.config["SECRET_KEY"] == "env-key"


def test_secret_key_debug_default():
    _run_main({"external_api": {"enabled": False}}, {"FLASK_DEBUG": "1"})
    assert main.app.config["SECRET_KEY"] == "dev-secret-key-for-local-debug-only"


def test_secret_key_missing_logs_error():
    mock_logger = _run_main({"external_api": {"enabled": False}}, {})
    assert mock_logger.error.called
