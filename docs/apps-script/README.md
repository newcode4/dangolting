# Apps Script — 3단계만

| # | 함수 | 하는 일 |
|---|------|---------|
| 1 | `setupTelegram` | token · chat_id 저장 |
| 2 | **`installTriggers`** | ★ **알림 켜기** (폼·입금) |
| 3 | `testTelegramPing` | 텔레그램 테스트 |

**`installTriggers`를 안 하면 폼 제출해도 알림 없음.**

`onFormSubmit`은 직접 누르는 버튼이 아닙니다. `installTriggers()`가 백그라운드 트리거로 등록합니다.

## 실행 방법

1. 스프레드시트 → **확장 프로그램 → Apps Script**
2. `Code.gs` 붙여넣기 → 저장
3. 상단 함수 드롭다운에서 함수 선택 → **실행**
4. 시트 **새로고침** → 메뉴 **단골팅 알림** (2번부터 여기서도 가능)

## 폼 테스트

- 구글 **폼**으로 제출 (시트에 연결된 그 폼)
- 또는 `testLastRowNotify` — 마지막 행 내용으로 알림

## 주의

- Apps Script는 **응답이 쌓이는 그 스프레드시트**에 붙여야 함
- Streamlit Reboot **불필요**
