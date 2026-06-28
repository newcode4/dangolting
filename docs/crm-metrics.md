# CRM 지표 정의서

> Single Source: `utils/crm_truth.py` · Snapshot: `utils/crm.build_crm_snapshot()`

## 퍼널 (랜딩 → 신청)

| key | 라벨 | 계산 |
|-----|------|------|
| `visit_u` | 랜딩 방문 (순) | events `page_view` unique visitor |
| `visit_t` | 랜딩 방문 (총) | events `page_view` total |
| `apply_u` | 참여 신청 클릭 (순) | events `apply_click` unique |
| `apply_t` | 참여 신청 클릭 (총) | events `apply_click` total |
| `form` | 폼 제출 | 시트 성함 있는 행 수 |
| `unpaid` | 입금 대기 | `stage_key == unpaid` |
| `paid` | 입금 확인 | `paid_applicant_count()` — 입금 O · 환불 X |
| `matching_pool` | 매칭 풀 | matching + reject_1 |
| `matched` | 매칭 완료 | `stage_key == matched` |
| `refunded` | 환불 | `stage_key == refunded` |

## 매출

- **입금액** = `paid_applicant_count × PARTICIPATION_FEE`
- **환불액** = `refunded_count × PARTICIPATION_FEE`
- **순수익** = 입금액 − 환불액

## 오늘 할 일 큐

우선순위 (`utils/crm_queue.build_today_queue`):

1. SLA 초과 입금 대기 (기본 48h)
2. 입금 대기
3. 1차 거절 · 재매칭
4. 매칭 진행

## 시트 불일치

`detect_sheet_anomalies()`:

- 입금 + 환불 동시
- 매칭 TRUE + 거절 2회
- 매칭 TRUE + 매칭일 없음

## 기간 필터

CRM 상단 4 preset: 이번 주 · 이번 달 · 3개월 · 전체  
기간별 KPI는 `snapshot.applicants` 신청일 + events ts 기준 재집계.
