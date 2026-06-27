"""약식 회원가입 · 비밀번호 로그인 · 자동 로그인(쿠키)"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
from extra_streamlit_components import CookieManager

from utils.error_log import get_logger, log_exception

ROOT = Path(__file__).resolve().parent.parent
USERS_FILE = ROOT / "data" / "users.json"
COOKIE_NAME = "dgt_auth"
COOKIE_WIDGET_KEY = "dgt_cookie_mgr"
TOKEN_DAYS = 30

def _auth_cfg() -> dict:
    try:
        return dict(st.secrets.get("auth", {}))
    except Exception:
        return {}


def _session_key() -> bytes:
    key = _auth_cfg().get("session_key", "")
    if key:
        return str(key).encode()
    return b"dangolting-local-dev-change-in-secrets"


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return salt, digest.hex()


def verify_password(password: str, salt: str, pwd_hash: str) -> bool:
    _, digest = hash_password(password, salt)
    return hmac.compare_digest(digest, pwd_hash)


def _users_from_secrets() -> dict[str, dict]:
    out: dict[str, dict] = {}
    raw = _auth_cfg().get("users", {})
    if not raw:
        return out
    for name, cfg in raw.items():
        if not isinstance(cfg, dict):
            continue
        if cfg.get("hash") and cfg.get("salt"):
            out[str(name)] = {"salt": str(cfg["salt"]), "hash": str(cfg["hash"])}
        elif cfg.get("password"):
            salt, digest = hash_password(str(cfg["password"]))
            out[str(name)] = {"salt": salt, "hash": digest}
    return out


def load_user_store() -> dict[str, dict]:
    users = _users_from_secrets()
    if USERS_FILE.is_file():
        try:
            data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            for name, rec in data.get("users", {}).items():
                users[str(name)] = rec
        except (json.JSONDecodeError, OSError):
            pass
    if not users:
        boot_user = _auth_cfg().get("bootstrap_user", "")
        boot_pw = _auth_cfg().get("bootstrap_password", "")
        if boot_user and boot_pw:
            salt, digest = hash_password(str(boot_pw))
            users[str(boot_user)] = {"salt": salt, "hash": digest}
    return users


def save_user_store(users: dict[str, dict]) -> bool:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        USERS_FILE.write_text(
            json.dumps({"users": users}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def signup_allowed() -> bool:
    return bool(_auth_cfg().get("allow_signup", False))


def _signup_code_required() -> str:
    return str(_auth_cfg().get("signup_code", "")).strip()


def register(username: str, password: str, password2: str, invite_code: str = "") -> str | None:
    if not signup_allowed():
        return "회원가입이 비활성화되어 있습니다. 관리자에게 계정을 요청하세요."
    required = _signup_code_required()
    if required and not hmac.compare_digest(invite_code.strip(), required):
        return "초대 코드가 올바르지 않습니다."
    name = username.strip()
    if len(name) < 2:
        return "아이디는 2자 이상이어야 합니다."
    if len(password) < 4:
        return "비밀번호는 4자 이상이어야 합니다."
    if password != password2:
        return "비밀번호가 일치하지 않습니다."
    users = load_user_store()
    if name in users:
        return "이미 사용 중인 아이디입니다."
    salt, digest = hash_password(password)
    users[name] = {"salt": salt, "hash": digest}
    if not save_user_store(users):
        return "가입 정보를 저장할 수 없습니다. (클라우드 배포 시 secrets에 계정을 등록하세요.)"
    return None


def authenticate(username: str, password: str) -> bool:
    users = load_user_store()
    rec = users.get(username.strip())
    if not rec:
        return False
    return verify_password(password, rec["salt"], rec["hash"])


def make_token(username: str, days: int = TOKEN_DAYS) -> str:
    exp = int(time.time()) + days * 86400
    payload = f"{username}:{exp}"
    sig = hmac.new(_session_key(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}:{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def parse_token(token: str) -> str | None:
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        username, exp_s, sig = raw.rsplit(":", 2)
        payload = f"{username}:{exp_s}"
        expected = hmac.new(_session_key(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(exp_s) < time.time():
            return None
        users = load_user_store()
        if username not in users:
            return None
        return username
    except Exception:
        return None


def _get_cookie_manager() -> CookieManager:
    """CookieManager 1회 생성 — __init__에서 getAll 1번만 (key=COOKIE_WIDGET_KEY)."""
    return CookieManager(key=COOKIE_WIDGET_KEY)


def _read_cookies_safe(cm: CookieManager) -> dict | None:
    """None = 컴포넌트 아직 준비 안 됨. {} = 쿠키 없음.

    get_all() 재호출 금지 — Streamlit 1.58 duplicate key 오류.
    """
    try:
        if not hasattr(cm, "cookies"):
            return {}
        raw = getattr(cm, "cookies", None)
        if raw is None:
            return None
        if isinstance(raw, dict):
            return raw
        get_logger().warning("CookieManager.cookies 비정상 — type=%s", type(raw).__name__)
        return {}
    except Exception as exc:
        log_exception(exc, where="auth.read_cookies")
        return {}


def _token_from_cookies(cookies: dict) -> str | None:
    val = cookies.get(COOKIE_NAME)
    return str(val) if val else None


def _try_cookie_login(cm: CookieManager, *, cookies: dict | None = None) -> bool:
    if cookies is None:
        cookies = _read_cookies_safe(cm)
    if cookies is None:
        return False
    token = _token_from_cookies(cookies)
    if not token:
        return False
    user = parse_token(token)
    if user:
        st.session_state["auth_user"] = user
        st.session_state.pop("_admin_scroll_reset", None)
        return True
    _clear_auth_cookie_safe(cm)
    return False


def set_auth_cookie(username: str, remember: bool, *, cm: CookieManager | None = None) -> None:
    if not remember:
        if cm is not None:
            _clear_auth_cookie_safe(cm)
        return
    try:
        manager = cm or _get_cookie_manager()
        expires = datetime.now(timezone.utc) + timedelta(days=TOKEN_DAYS)
        manager.set(COOKIE_NAME, make_token(username), expires_at=expires, key="dgt_set")
    except Exception as exc:
        log_exception(exc, where="auth.set_cookie")


def _clear_auth_cookie_safe(cm: CookieManager | None = None) -> None:
    try:
        manager = cm or _get_cookie_manager()
        manager.delete(COOKIE_NAME, key="dgt_logout")
    except Exception as exc:
        log_exception(exc, where="auth.clear_cookie")


def clear_auth_cookie() -> None:
    _clear_auth_cookie_safe()


def logout() -> None:
    st.session_state.pop("auth_user", None)
    st.session_state.pop("_auth_cookie_tried", None)
    clear_auth_cookie()


def current_user() -> str | None:
    return st.session_state.get("auth_user")


def _render_login_form(*, cm: CookieManager) -> None:
    with st.form("login_form", clear_on_submit=False):
        uid = st.text_input("아이디", placeholder="아이디", autocomplete="username")
        pw = st.text_input(
            "비밀번호", type="password", placeholder="비밀번호", autocomplete="current-password"
        )
        remember = st.checkbox("자동 로그인", value=True)
        if st.form_submit_button("로그인", type="primary", use_container_width=True):
            if authenticate(uid, pw):
                st.session_state["auth_user"] = uid.strip()
                set_auth_cookie(uid.strip(), remember, cm=cm)
                st.session_state.pop("_admin_scroll_reset", None)
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")


def _render_signup_form() -> None:
    with st.form("signup_form", clear_on_submit=True):
        if _signup_code_required():
            invite = st.text_input("초대 코드", placeholder="관리자가 발급한 코드", type="password")
        else:
            invite = ""
        new_id = st.text_input("아이디", placeholder="2자 이상", autocomplete="username")
        new_pw = st.text_input(
            "비밀번호", type="password", placeholder="4자 이상", autocomplete="new-password"
        )
        new_pw2 = st.text_input("비밀번호 확인", type="password", autocomplete="new-password")
        if st.form_submit_button("가입하기", use_container_width=True):
            err = register(new_id, new_pw, new_pw2, invite)
            if err:
                st.error(err)
            else:
                st.success("가입 완료! 로그인 탭에서 로그인하세요.")


def render_auth_page(logo_uri: str) -> None:
    from utils.scroll_top import reset_page_scroll

    reset_page_scroll(force=True)
    st.markdown(
        """
        <style>
        section.main > div.block-container {
          max-width: 100% !important;
          padding: 4rem 1.5rem 2rem !important;
        }
        section.main [data-testid="stVerticalBlockBorderWrapper"]:has(.auth-brand) {
          padding: 28px 32px 22px !important;
          background: #161b22 !important;
          border-color: #30363d !important;
          border-radius: 14px !important;
          max-width: 400px;
          margin: 0 auto;
        }
        section.main [data-testid="stVerticalBlockBorderWrapper"]:has(.auth-brand)
          [data-testid="stForm"] [data-testid="stVerticalBlock"] > div {
          gap: 10px !important;
        }
        section.main [data-testid="stVerticalBlockBorderWrapper"]:has(.auth-brand)
          div[data-testid="stButton"] > button {
          min-height: 38px !important;
          font-size: 0.85rem !important;
        }
        section.main [data-testid="stVerticalBlockBorderWrapper"]:has(.auth-brand)
          [data-testid="stTextInput"] input {
          min-height: 36px !important;
          font-size: 0.85rem !important;
        }
        .auth-logo { width: 52px; height: 52px; margin-bottom: 12px; }
        .auth-brand { text-align: center; margin-bottom: 4px; }
        .auth-brand h1 { font-size: 1.3rem; font-weight: 700; color: #e6edf3; margin: 0 0 6px; }
        .auth-brand p  { font-size: 0.82rem; color: #8b949e; margin: 0; }
        @media (max-width: 768px) {
          section.main > div.block-container {
            padding: 2.5rem 1rem 1.5rem !important;
          }
          section.main [data-testid="stVerticalBlockBorderWrapper"]:has(.auth-brand) {
            max-width: 100%;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    cm = _get_cookie_manager()

    # 쿠키 자동로그인 — 준비됐을 때만 시도. None이면 폼을 먼저 보여줌 (st.stop 금지).
    if not st.session_state.get("_auth_cookie_tried"):
        cookies = _read_cookies_safe(cm)
        if cookies is not None:
            st.session_state["_auth_cookie_tried"] = True
            if _try_cookie_login(cm, cookies=cookies):
                st.rerun()

    _sp, main, _sp2 = st.columns([2.2, 1.6, 2.2], gap="small")

    with main:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="auth-brand">
                  <img src="{logo_uri}" alt="단골팅" class="auth-logo"/>
                  <h1>단골팅 관리자</h1>
                  <p>관리자 계정으로 로그인하세요</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if signup_allowed():
                tab_login, tab_signup = st.tabs(["로그인", "회원가입"])
                with tab_login:
                    _render_login_form(cm=cm)
                with tab_signup:
                    _render_signup_form()
            else:
                _render_login_form(cm=cm)
                st.markdown(
                    '<p class="auth-hint">접근 권한이 있는 관리자만 이용할 수 있습니다.<br>'
                    "계정은 운영자가 발급합니다.</p>",
                    unsafe_allow_html=True,
                )


def ensure_authenticated(logo_uri: str) -> None:
    """앱 시작 시 session_state만 확인 — CookieManager는 로그인 페이지에서만 사용."""
    if "auth_user" not in st.session_state:
        st.session_state["auth_user"] = None

    if st.session_state.get("auth_user"):
        return

    render_auth_page(logo_uri)
    st.stop()


def get_cookie_manager() -> CookieManager:
    return _get_cookie_manager()


def _safe_cookie_get_all() -> dict | None:
    cm = _get_cookie_manager()
    return _read_cookies_safe(cm)
