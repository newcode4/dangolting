@echo off
cd /d "%~dp0"
echo 단골팅 Streamlit 앱 시작 중...
echo 브라우저: http://localhost:8501
python -m streamlit run app.py
if errorlevel 1 (
  echo.
  echo 실행 실패. 아래 명령으로 의존성을 먼저 설치하세요:
  echo   python -m pip install -r requirements.txt
  pause
)
