## 목표:
단골팅 비즈니스 매칭 서비스의 관리자 대시보드 구축
구글 시트 ↔ Streamlit 양방향 실시간 연동

## 문맥:
- 구글 폼으로 신청자 데이터가 시트에 적재됨
- 관리자가 매칭 추천/확정/거절을 대시보드에서 처리
- 변경사항이 즉시 구글 시트에 반영

## 제약:
- gspread + service_account 인증
- Streamlit 단일 파일 구조 (app.py + utils/)
- 거절 2회 → 매칭 종료 잠금

## 완료조건:

## M1: 프로젝트 구조 및 의존성 — 검증: pip install -r requirements.txt — 상태: [ ]
## M2: gspread 연동 모듈 (utils/sheets.py) — 검증: python -c "from utils.sheets import load_data" — 상태: [ ]
## M3: 매칭 알고리즘 (utils/matching.py) — 검증: python -c "from utils.matching import recommend_top3" — 상태: [ ]
## M4: Streamlit 메인 앱 (app.py) — 검증: streamlit run app.py — 상태: [ ]
## M5: 테마 + credentials 템플릿 + README — 검증: 파일 존재 확인 — 상태: [ ]

## stop rule:
- 단일 파일 300줄 초과 시 모듈 분리
- gspread 인증 오류 시 README 안내로 대체 처리

## rollback:
- kill switch: 시트 연동 없이 샘플 데이터(DEMO_MODE=True)로 실행 가능
- revert scope: utils/ 폴더 삭제 후 app.py 단독 실행
