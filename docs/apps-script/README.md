# Google Sheets Apps Script — 텔레그램 알림

Streamlit 앱과 **함께** 쓰거나, 앱 없이 **시트만**으로 알림을 받을 수 있습니다.

| 이벤트 | Streamlit 앱 | Apps Script |
|--------|--------------|-------------|
| 구글 폼 **새 제출** | ✅ (앱 켜져 있을 때, ~2분) | ✅ 즉시 (`onFormSubmit`) |
| U열 **입금 체크** | ❌ | ✅ (`onEdit`) |

## 설치

1. 단골팅 스프레드시트 → **확장 프로그램 → Apps Script**
2. `Code.gs` 내용 붙여넣기 (또는 앱 **설정 · 알림** 탭에서 다운로드)
3. `setupTelegram` 선택 → **실행** → bot_token, chat_id 입력
4. **트리거**(시계 아이콘) → **트리거 추가**
   - `onFormSubmit` — 이벤트: **양식 제출 시**
   - `onEdit` — 이벤트: **편집 시**
5. `testTelegramPing` 실행으로 연동 확인

## 열 번호 수정

시트에 열이 추가·삭제됐으면 `Code.gs` 상단 `COL` 숫자만 맞추세요.  
앱의 `utils/columns.py` `COL`과 동일합니다.

## 보안

- token · chat_id는 **스크립트 속성**에 저장 (시트에 노출 안 됨)
- Streamlit `secrets.toml`과 **같은 봇**을 써도 됩니다
