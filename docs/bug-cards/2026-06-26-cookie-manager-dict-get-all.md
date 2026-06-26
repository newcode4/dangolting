## 버그: CookieManager dict — get_all AttributeError (Streamlit Cloud)
## 원인:
1. `ensure_authenticated()`가 앱 최상단(line 69)에서 `get_cookie_manager().get_all()` 호출
2. CookieManager 위젯이 DOM에 마운트되기 전에 get_all 호출
3. `session_state`에 CookieManager 대신 dict가 저장되어 AttributeError
## 영향 파일:
- `utils/auth.py`
## 수정 내용:
- **앱 시작(`ensure_authenticated`)**: `session_state.auth_user`만 확인 — CookieManager 미사용
- **로그인 페이지(`render_auth_page`)**: CookieManager 마운트 후 쿠키 자동로그인 시도
- CookieManager 인스턴스를 session_state에 저장하지 않음 (실행당 1회 생성)
- `_read_cookies_safe()` — AttributeError/비정상 타입 시 `{}` 반환, 앱 크래시 방지
## 재발 방지:
- `tests/test_auth_cookie.py` — ensure_authenticated에 get_all 없음 assert
## 검증 명령:
`python -m pytest tests/test_auth_cookie.py -q`

