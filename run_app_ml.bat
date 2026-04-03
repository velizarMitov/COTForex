@echo off
echo Starting COT vs MT5 Forex Analysis App (.venv-ml / Python 3.12)...
cd /d "%~dp0"
call .venv-ml\Scripts\activate.bat
streamlit run app.py
pause

