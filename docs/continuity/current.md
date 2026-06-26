## 현재 진행 중인 계획:
docs/exec-plans/active/2026-06-26-admin-dashboard.md

## 마지막 완료 상태:
단골팅 관리자 대시보드 초기 구축 완료
- app.py (메인 Streamlit 앱: 카드 UI, 필터, 추천 알고리즘, 매칭/거절 처리)
- utils/sheets.py (gspread 연동 + 데모 데이터)
- utils/matching.py (점수 기반 TOP3 추천)
- .streamlit/config.toml (다크 테마)
- credentials_template.json, secrets.toml.template, README.md

## 다음 행동:
1. pip install -r requirements.txt 실행
2. 데모 모드로 streamlit run app.py 동작 확인
3. 실제 구글 시트 연동 시: credentials.json 배치 + 시트 URL 입력
4. 실제 시트 컬럼명 확인 후 utils/sheets.py COL 딕셔너리 조정

## 하지 않을 것:
- credentials.json git 커밋 금지
- DB 마이그레이션 없음 (구글 시트가 유일한 데이터 소스)

_업데이트: 2026-06-26_
