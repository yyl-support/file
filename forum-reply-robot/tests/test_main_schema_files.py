import importlib, sys, types
from unittest.mock import Mock

import pytest


def import_main_module(monkeypatch):
    sys.modules.pop("main", None)
    specs = [("src.ForumBot.monitor", "ForumMonitor", "start"), ("src.update_lightrag.full_data_init", "FullDataUpdate", "update_full_data"), ("src.update_lightrag.increment_date_update_timer", "UpdateLightRAGTimer", "run_scheduler")]
    for module_name, class_name, method_name in specs:
        module = types.ModuleType(module_name)
        dummy_class = type(class_name, (), {"__init__": lambda self, config=None: setattr(self, "config", config), method_name: lambda self: None})
        setattr(module, class_name, dummy_class)
        monkeypatch.setitem(sys.modules, module_name, module)
    netifaces_module = types.ModuleType("netifaces")
    netifaces_module.AF_INET, netifaces_module.interfaces, netifaces_module.ifaddresses = 2, (lambda: []), (lambda interface: {})
    monkeypatch.setitem(sys.modules, "netifaces", netifaces_module)
    return importlib.import_module("main")


@pytest.mark.parametrize(("exists", "files", "expected"), [(False, [], False), (True, [".gitkeep"], False), (True, [".gitkeep", "schema.json"], True)])
def test_check_schema_files(monkeypatch, exists, files, expected):
    main_module = import_main_module(monkeypatch)
    monkeypatch.setattr(main_module.os.path, "exists", lambda path: exists)
    monkeypatch.setattr(main_module.os, "listdir", lambda path: files)
    assert main_module.check_schema_files() is expected


def test_main_returns_early_when_schema_files_check_fails(monkeypatch):
    main_module = import_main_module(monkeypatch)
    lightrag_init, initialize_service, update_timer = Mock(), Mock(), Mock()
    monkeypatch.setattr(main_module, "check_schema_files", lambda: False)
    monkeypatch.setattr(main_module, "lightrag_data_init", lightrag_init)
    monkeypatch.setattr(main_module, "initialize_service", initialize_service)
    monkeypatch.setattr(main_module, "lightrag_data_update_timer", update_timer)
    main_module.main()
    for mock in (lightrag_init, initialize_service, update_timer):
        mock.assert_not_called()
