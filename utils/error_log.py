"""앱 전역 오류 로깅 — data/logs/app.log"""
from __future__ import annotations

import logging
import sys
import traceback
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "data" / "logs"
LOG_FILE = LOG_DIR / "app.log"
_LOGGER_NAME = "dangolting"

F = TypeVar("F", bound=Callable[..., Any])


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    return logger


def get_logger() -> logging.Logger:
    return setup_logging()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def log_message(level: int, msg: str, *, where: str = "", exc: BaseException | None = None) -> None:
    logger = get_logger()
    prefix = f"[{where}] " if where else ""
    if exc is not None:
        logger.log(level, f"{prefix}{msg}: {exc}", exc_info=exc)
    else:
        logger.log(level, f"{prefix}{msg}")


def log_exception(exc: BaseException, *, where: str, extra: str = "") -> None:
    logger = get_logger()
    detail = f" ({extra})" if extra else ""
    logger.error(f"[{where}]{detail} {type(exc).__name__}: {exc}", exc_info=exc)


def install_excepthook() -> None:
    """처리되지 않은 예외 → 로그 파일."""

    def _hook(exc_type, exc, tb):
        if exc_type is KeyboardInterrupt:
            sys.__excepthook__(exc_type, exc, tb)
            return
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        get_logger().critical("uncaught exception\n%s", text)
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook


def tail_log(max_lines: int = 80) -> str:
    if not LOG_FILE.is_file():
        return "(로그 없음)"
    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "(로그 읽기 실패)"
    if not lines:
        return "(로그 비어 있음)"
    return "\n".join(lines[-max_lines:])


def guarded(where: str) -> Callable[[F], F]:
    """함수 예외 → 로그 기록 후 재발생."""

    def deco(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                log_exception(exc, where=where)
                raise

        return wrapper  # type: ignore[return-value]

    return deco


def ui_error(exc: BaseException, *, where: str, streamlit_module: Any) -> None:
    """Streamlit UI + 로그."""
    log_exception(exc, where=where)
    streamlit_module.error(f"{where}: {exc}")
    with streamlit_module.expander("오류 상세 (로그에도 기록됨)"):
        streamlit_module.code(traceback.format_exc())
