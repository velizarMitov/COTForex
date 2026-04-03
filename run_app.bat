@echo off
echo Starting COT vs MT5 Forex Analysis App...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
streamlit run app.py
pause
