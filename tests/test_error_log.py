"""오류 로그 파일 기록."""
from __future__ import annotations

from pathlib import Path

from utils.error_log import LOG_FILE, log_exception, setup_logging, tail_log


def test_log_exception_writes_file(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_file = log_dir / "app.log"
    monkeypatch.setattr("utils.error_log.LOG_DIR", log_dir)
    monkeypatch.setattr("utils.error_log.LOG_FILE", log_file)

    # reset logger handlers
    import logging
    logger = logging.getLogger("dangolting")
    logger.handlers.clear()

    setup_logging()
    try:
        raise ValueError("test error")
    except ValueError as exc:
        log_exception(exc, where="test.unit")

    text = log_file.read_text(encoding="utf-8")
    assert "test.unit" in text
    assert "ValueError" in text
    assert "test error" in text


def test_tail_log_returns_recent_lines(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_file = log_dir / "app.log"
    log_dir.mkdir()
    log_file.write_text("line1\nline2\nline3\n", encoding="utf-8")
    monkeypatch.setattr("utils.error_log.LOG_FILE", log_file)

    tail = tail_log(2)
    assert "line2" in tail
    assert "line3" in tail
    assert "line1" not in tail
