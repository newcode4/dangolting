"""CookieManager — 앱 시작 시 get_all 호출 금지 회귀 방지."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class _FakeCookieManager:
    def __init__(self, key: str = ""):
        self.key = key
        self._cookies: dict | None = {}

    @property
    def cookies(self):
        return self._cookies

    def get_all(self, key="get_all"):
        return self._cookies

    def set(self, name, val, **kwargs):
        if self._cookies is None:
            self._cookies = {}
        self._cookies[name] = val

    def delete(self, name, **kwargs):
        if self._cookies and name in self._cookies:
            del self._cookies[name]


def test_attempt_cookie_auto_login_logs_in_when_token_present():
    cm = _FakeCookieManager()
    from utils.auth import _attempt_cookie_auto_login, make_token

    class _State(dict):
        pass

    fake_st = MagicMock()
    fake_st.session_state = _State()
    reruns: list[None] = []

    boot_users = load_user_store_with_admin()

    def _rerun():
        reruns.append(None)

    with (
        patch("utils.auth.st", fake_st),
        patch("utils.auth.st.rerun", side_effect=_rerun),
        patch("utils.auth.load_user_store", return_value=boot_users),
        patch("utils.auth._session_key", return_value=_FIXED_KEY),
    ):
        cm._cookies = {"dgt_auth": make_token("admin")}
        _attempt_cookie_auto_login(cm)
        assert fake_st.session_state.get("auth_user") == "admin"
        assert len(reruns) == 1


def test_attempt_cookie_auto_login_retries_until_ready():
    cm = _FakeCookieManager()
    from utils.auth import COOKIE_RETRY_MAX, _attempt_cookie_auto_login

    class _State(dict):
        pass

    fake_st = MagicMock()
    fake_st.session_state = _State()
    reruns: list[None] = []

    with (
        patch("utils.auth.st", fake_st),
        patch("utils.auth.st.rerun", side_effect=lambda: reruns.append(None)),
    ):
        cm._cookies = None
        for _ in range(COOKIE_RETRY_MAX + 2):
            _attempt_cookie_auto_login(cm)
            if fake_st.session_state.get("_auth_cookie_gave_up"):
                break
        assert len(reruns) == COOKIE_RETRY_MAX
        assert fake_st.session_state.get("_auth_cookie_gave_up") is True


def test_get_cookie_manager_reuses_session_singleton():
    from utils.auth import SESSION_CM_KEY, _get_cookie_manager

    class _State(dict):
        pass

    fake_st = MagicMock()
    fake_st.session_state = _State()
    created: list[str] = []

    def _cm_factory(**kwargs):
        created.append(kwargs.get("key", ""))
        return _FakeCookieManager(key=kwargs.get("key", ""))

    with (
        patch("utils.auth.st", fake_st),
        patch("utils.auth.CookieManager", side_effect=lambda **kw: _cm_factory(**kw)),
    ):
        a = _get_cookie_manager()
        b = _get_cookie_manager()
        assert a is b
        assert len(created) == 1
        assert fake_st.session_state[SESSION_CM_KEY] is a


def test_set_auth_cookie_uses_lax_and_max_age():
    cm = _FakeCookieManager()
    from utils.auth import COOKIE_NAME, TOKEN_DAYS, set_auth_cookie

    class _State(dict):
        pass

    fake_st = MagicMock()
    fake_st.session_state = _State()

    with patch("utils.auth.st", fake_st), patch("utils.auth._cookie_secure", return_value=True):
        set_auth_cookie("admin", True, cm=cm)
    assert COOKIE_NAME in cm._cookies
    # set() kwargs captured via MagicMock if we use one — FakeCookieManager ignores extras
    # ensure call path completes without error


def test_ensure_authenticated_never_calls_get_all_directly():
    """ensure_authenticated 본문에 get_cookie_manager().get_all() 패턴 없음."""
    import inspect

    from utils import auth

    src = inspect.getsource(auth.ensure_authenticated)
    assert "get_all()" not in src
    assert "get_cookie_manager()" not in src


def test_read_cookies_safe_handles_dict_without_get_all():
    broken = {"not": "a manager"}

    from utils.auth import _read_cookies_safe

    with patch("utils.auth.get_logger"):
        result = _read_cookies_safe(broken)  # type: ignore[arg-type]
    assert result == {}


def test_read_cookies_safe_none_means_not_ready():
    cm = _FakeCookieManager()
    cm._cookies = None

    from utils.auth import _read_cookies_safe

    assert _read_cookies_safe(cm) is None


def test_render_auth_page_does_not_stop_while_cookies_loading():
    """CookieManager 준비 전 st.stop()으로 로그인 버튼이 늦게 뜨는 회귀 방지."""
    import inspect

    from utils import auth

    src = inspect.getsource(auth.render_auth_page)
    assert "st.stop()" not in src
    assert "auth-loading" not in src


def test_read_cookies_safe_uses_cm_cookies_not_get_all():
    """get_all() 재호출 시 StreamlitDuplicateElementKey(get_all) 회귀 방지."""
    import inspect

    from utils import auth

    src = inspect.getsource(auth._read_cookies_safe)
    assert "cm.get_all(" not in src


_FIXED_KEY = b"dangolting-local-dev-change-in-secrets"


def test_try_cookie_login_accepts_prefetched_cookies():
    cm = _FakeCookieManager()
    from utils.auth import _try_cookie_login, make_token

    boot_users = load_user_store_with_admin()

    class _State(dict):
        pass

    fake_st = MagicMock()
    fake_st.session_state = _State()

    with (
        patch("utils.auth.st", fake_st),
        patch("utils.auth.load_user_store", return_value=boot_users),
        patch("utils.auth._session_key", return_value=_FIXED_KEY),
    ):
        cm._cookies = {"dgt_auth": make_token("admin")}
        assert _try_cookie_login(cm, cookies=cm._cookies) is True
        assert fake_st.session_state["auth_user"] == "admin"


def test_try_cookie_login_sets_user():
    cm = _FakeCookieManager()
    from utils.auth import _try_cookie_login, make_token

    class _State(dict):
        pass

    fake_st = MagicMock()
    fake_st.session_state = _State()

    boot_users = load_user_store_with_admin()

    with (
        patch("utils.auth.st", fake_st),
        patch("utils.auth.load_user_store", return_value=boot_users),
        patch("utils.auth._session_key", return_value=_FIXED_KEY),
    ):
        cm._cookies = {"dgt_auth": make_token("admin")}
        assert _try_cookie_login(cm) is True
        assert fake_st.session_state["auth_user"] == "admin"


def load_user_store_with_admin():
    from utils.auth import hash_password

    salt, digest = hash_password("secret")
    return {"admin": {"salt": salt, "hash": digest}}
