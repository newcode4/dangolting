## 버그: PC에서 hook VS 섹션이 모바일처럼 깨짐
## 원인:
- 랜딩이 Streamlit `components.html` iframe 안에서 렌더됨
- `@media (max-width:520px)` 등이 **iframe 너비** 기준이라 PC 브라우저에서도 모바일 CSS 적용
- CSS 수정이 배포/캐시 없이는 반영 안 됨
## 영향 파일:
- `assets/landing-page.css`
- `utils/landing.py`
## 수정 내용:
- `@media` hook 분기 제거 → `html[data-hook-layout="desktop|mobile"]` + `syncHookLayout()` JS
- PC: 부모 창 너비 기준 desktop — 가로 VS 3열, 큰 밴드 pill
- 모바일: 세로 스택 (10배+ 우선)
- hook HTML 들여쓰기/닫는 태그 정리
## 재발 방지:
- `tests/test_landing.py`: syncHookLayout·data-hook-layout·CSS attribute 회귀 테스트
## 검증 명령:
- `pytest tests/test_landing.py -q`
