import logging
import threading
from pathlib import Path

import pytest

import database.connection as dbconn
import services.report_service as reports
from auth.rate_limit import RateLimiter
from tests.fakes import ScriptedDB


# ----------------------------------------------------- medical file access

@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    root = (tmp_path / "uploads").resolve()
    root.mkdir()
    monkeypatch.setattr(reports, "UPLOAD_DIR", root)
    return root


def _image(path):
    return {"id": 1, "patient_id": 7, "chat_session_id": None, "file_path": str(path), "uploaded_at": None}


def test_path_inside_uploads_is_allowed(upload_dir, monkeypatch):
    f = upload_dir / "7" / "scan.png"
    f.parent.mkdir()
    f.write_bytes(b"x")
    monkeypatch.setattr(reports, "get_db", ScriptedDB([_image(f)]))
    assert reports.get_secure_image_path(7, 1) == f.resolve()


def test_relative_path_resolves_against_uploads(upload_dir, monkeypatch):
    (upload_dir / "a.png").write_bytes(b"x")
    monkeypatch.setattr(reports, "get_db", ScriptedDB([_image("a.png")]))
    assert reports.get_secure_image_path(7, 1) == (upload_dir / "a.png").resolve()


@pytest.mark.parametrize("evil", ["../../etc/passwd", "/etc/passwd", "../outside.png"])
def test_path_traversal_blocked(upload_dir, monkeypatch, evil):
    monkeypatch.setattr(reports, "get_db", ScriptedDB([_image(evil)]))
    assert reports.get_secure_image_path(7, 1) is None


def test_missing_file_returns_none(upload_dir, monkeypatch):
    monkeypatch.setattr(reports, "get_db", ScriptedDB([_image("ghost.png")]))
    assert reports.get_secure_image_path(7, 1) is None


def test_report_lookup_is_scoped_to_patient(monkeypatch):
    db = ScriptedDB([None])
    monkeypatch.setattr(reports, "get_db", db)
    assert reports.get_medical_image(patient_id=8, image_id=1) is None
    sql, params = db.queries[0]
    assert "patient_id = %s" in sql and params == (1, 8)


def test_history_lookup_is_scoped_to_patient(monkeypatch):
    db = ScriptedDB([None])
    monkeypatch.setattr(reports, "get_db", db)
    reports.get_medical_history_by_id(patient_id=8, history_id=3)
    sql, params = db.queries[0]
    assert "mh.patient_id = %s" in sql and params == (3, 8)


def test_upload_dir_is_not_cwd_dependent():
    assert reports.UPLOAD_DIR.is_absolute()
    assert reports.UPLOAD_DIR.name == "uploads" or "UPLOAD_DIR" in __import__("os").environ


def test_report_tool_never_returns_file_path(monkeypatch):
    import mcp_app.user.mcp_user_05.tool as tool
    monkeypatch.setattr(tool, "get_medical_image",
                        lambda **kw: {"id": 1, "chat_session_id": 2, "file_path": "/secret/x.png", "uploaded_at": "t"})
    res = tool.get_my_medical_report(patient_id=7, image_id=1)
    assert "file_path" not in str(res)


# ---------------------------------------------------------------- limiter

def test_rate_limiter_blocks_and_expires(monkeypatch):
    import auth.rate_limit as rl
    now = [1000.0]
    monkeypatch.setattr(rl.time, "monotonic", lambda: now[0])
    lim = RateLimiter(max_events=3, window_seconds=10)
    assert [lim.check_and_hit("k") for _ in range(4)] == [True, True, True, False]
    assert lim.retry_after("k") >= 1
    assert lim.check_and_hit("other") is True                 # separate keys
    now[0] += 11
    assert lim.check_and_hit("k") is True                     # window passed
    lim.reset("k")
    assert lim.is_blocked("k") is False


def test_rate_limiter_is_thread_safe():
    lim = RateLimiter(max_events=50, window_seconds=60)
    results = []
    threads = [threading.Thread(target=lambda: results.append(lim.check_and_hit("k"))) for _ in range(200)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert results.count(True) == 50


# --------------------------------------------------------------------- db

class _FakeConn:
    def __init__(self):
        self.log = []

    def commit(self):
        self.log.append("commit")

    def rollback(self):
        self.log.append("rollback")

    def close(self):
        self.log.append("close")


def test_get_db_commits_on_success(monkeypatch):
    conn = _FakeConn()
    monkeypatch.setattr(dbconn, "get_connection", lambda: conn)
    with dbconn.get_db():
        pass
    assert conn.log == ["commit", "close"]


def test_get_db_rolls_back_on_error(monkeypatch):
    conn = _FakeConn()
    monkeypatch.setattr(dbconn, "get_connection", lambda: conn)
    with pytest.raises(ValueError):
        with dbconn.get_db():
            raise ValueError("x")
    assert conn.log == ["rollback", "close"]


def test_db_connection_has_timeouts(monkeypatch):
    captured = {}
    monkeypatch.setattr(dbconn.pymysql, "connect", lambda **kw: captured.update(kw))
    dbconn.get_connection()
    assert captured["connect_timeout"] > 0 and captured["read_timeout"] > 0


def test_db_env_is_read_at_call_time(monkeypatch):
    captured = {}
    monkeypatch.setattr(dbconn.pymysql, "connect", lambda **kw: captured.update(kw))
    monkeypatch.setenv("DB_NAME", "other_db")
    monkeypatch.setenv("DB_PORT", "not-a-number")
    dbconn.get_connection()
    assert captured["database"] == "other_db" and captured["port"] == 3306


# ----------------------------------------------------------------- logger

def test_logger_is_idempotent_and_writes_one_file():
    from src.logger import get_logger, LOG_FILE_PATH
    a = get_logger("x.one")
    b = get_logger("x.two")
    from logging.handlers import RotatingFileHandler
    root = logging.getLogger()
    rotating = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
    assert len(rotating) <= 1                      # never one file per call/start
    assert a is not b and Path(LOG_FILE_PATH).parent.name == "logs"
