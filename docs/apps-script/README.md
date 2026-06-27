# Apps Script — 알림 전용 (Streamlit enabled=false)

| 알림 | 시점 |
|------|------|
| 🆕 새 신청 | 폼 제출 즉시 |
| 💰 입금 확인 | U열 체크 |
| 📋 입금 대기 묶음 | **매일 12:00** (신청 3시간+ & 미입금) |

## 설치

1. `setupTelegram`
2. **`installTriggers`** ★ (위 3가지 트리거 한 번에)
3. `testTelegramPing` · `testUnpaidDigest`

## 설정 변경 (Code.gs 상단)

```javascript
const UNPAID_MIN_HOURS = 3;  // N시간 지난 사람만 점심 알림
const DIGEST_HOUR = 12;      // 점심 몇 시 (한국)
```

코드 수정 후 **`installTriggers` 다시 실행**.

## Streamlit

`data/telegram.toml` → `enabled = false` (중복·2분 지연 방지)
