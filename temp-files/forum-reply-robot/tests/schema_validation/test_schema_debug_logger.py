import logging

from src.ForumBot.SchemaValidation import schema_debug_logger as debug_logger


class FakeCursor:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        if self.should_fail:
            raise RuntimeError("insert failed")
        self.executed.append((query, params))

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor=None, fail_rollback=False, fail_close=False):
        self.cursor_obj = cursor or FakeCursor()
        self.fail_rollback = fail_rollback
        self.fail_close = fail_close
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True
        if self.fail_rollback:
            raise RuntimeError("rollback failed")

    def close(self):
        self.closed = True
        if self.fail_close:
            raise RuntimeError("close failed")


def reset_debug_logger(monkeypatch):
    monkeypatch.setattr(debug_logger, "_db_config", None)
    monkeypatch.setattr(debug_logger, "_initialized", False)
    monkeypatch.setattr(debug_logger, "_disabled", False)


def test_init_and_write_debug_record_success(monkeypatch):
    reset_debug_logger(monkeypatch)
    connections = [FakeConnection(), FakeConnection()]
    monkeypatch.setattr(debug_logger.psycopg2, "connect", lambda **_kwargs: connections.pop(0))

    debug_logger.init_debug_logger({"host": "localhost", "database": "db"})
    debug_logger.write_debug_record(
        {
            "topic_id": "1",
            "title": "title",
            "overall_pass": True,
            "total_processing_time_seconds": 0.1,
            "error": None,
        }
    )

    assert debug_logger._initialized is True
    assert debug_logger._disabled is False
    assert connections == []


def test_write_debug_record_logs_cleanup_failures(monkeypatch, caplog):
    reset_debug_logger(monkeypatch)
    monkeypatch.setattr(debug_logger, "_db_config", {"database": "db"})
    conn = FakeConnection(
        cursor=FakeCursor(should_fail=True),
        fail_rollback=True,
        fail_close=True,
    )
    monkeypatch.setattr(debug_logger.psycopg2, "connect", lambda **_kwargs: conn)
    caplog.set_level(logging.DEBUG, logger=debug_logger.__name__)

    debug_logger.write_debug_record({"topic_id": "1"})

    assert conn.rolled_back is True
    assert conn.closed is True
    assert "rollback failed" in caplog.text
    assert "close connection failed" in caplog.text


def test_debug_record_builder_records_and_swallows_debug_failures(monkeypatch, caplog):
    written = []
    monkeypatch.setattr(debug_logger, "write_debug_record", written.append)

    builder = debug_logger.DebugRecordBuilder("topic", "title")
    builder.set_relevance(True, "reason", 0.1)
    builder.set_review_points([{"title": "rp"}], 0.2)
    builder.set_filter_result([{"title": "redfish"}], [{"title": "other"}], 0.3)
    builder.add_review_point_check({"title": "check"})
    builder.finalize("final", True)

    assert written[0]["overall_pass"] is True
    assert written[0]["steps"]["check_review_points"][0]["title"] == "check"

    caplog.set_level(logging.DEBUG, logger=debug_logger.__name__)
    broken = debug_logger.DebugRecordBuilder("topic", "title")
    broken._record = object()
    broken.set_relevance(True, "reason", 0.1)
    broken.set_review_points([], 0.1)
    broken.set_filter_result([], [], 0.1)
    broken.add_review_point_check({})
    broken.finalize("final", False)

    exit_builder = debug_logger.DebugRecordBuilder("topic", "title")
    exit_builder.finalize = lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("finalize failed"))
    exit_builder.__exit__(None, None, None)

    assert "set relevance failed" in caplog.text
    assert "set review points failed" in caplog.text
    assert "set filter result failed" in caplog.text
    assert "add review point check failed" in caplog.text
    assert "write debug record failed" in caplog.text
    assert "finalize on exit failed" in caplog.text
