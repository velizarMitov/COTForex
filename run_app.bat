@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title COTForex

rem ---- ANSI colours (Windows 10+) -------------------------------------------
for /f %%E in ('echo prompt $E ^| cmd') do set "ESC=%%E"
set "DIM=%ESC%[90m"
set "CYAN=%ESC%[96m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "RED=%ESC%[91m"
set "BOLD=%ESC%[1m"
set "OFF=%ESC%[0m"

echo.
echo   %CYAN%%BOLD%COTForex%OFF%  %DIM%COT positioning vs MT5 price%OFF%
echo   %DIM%------------------------------------------------%OFF%
echo.

rem ---- 1. Environment: .venv by default, "run_app.bat ml" for .venv-ml -------
set "ENV=.venv"
if /i "%~1"=="ml" set "ENV=.venv-ml"
if not exist "%ENV%\Scripts\python.exe" (
    if "%ENV%"==".venv" if exist ".venv-ml\Scripts\python.exe" set "ENV=.venv-ml"
)
if not exist "%ENV%\Scripts\python.exe" (
    echo   %RED%[ERR]%OFF%  No virtual environment found.
    echo         Create one with:  python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    goto :fail
)
set "PY=%~dp0%ENV%\Scripts\python.exe"
for /f "tokens=2" %%V in ('%ENV%\Scripts\python.exe --version') do set "PYV=%%V"
echo   %GREEN%[ OK ]%OFF%  Environment   %DIM%%ENV%  (Python %PYV%)%OFF%

rem ---- 2. Dependencies: install only when something is missing --------------
"%PY%" -c "import streamlit, pandas, plotly, MetaTrader5" >nul 2>&1
if errorlevel 1 (
    echo   %YELLOW%[ .. ]%OFF%  Installing dependencies ...
    "%PY%" -m pip install -q -r requirements.txt
    if errorlevel 1 (
        echo   %RED%[ERR]%OFF%  Dependency install failed.
        goto :fail
    )
)
echo   %GREEN%[ OK ]%OFF%  Dependencies  %DIM%streamlit, pandas, plotly, MetaTrader5%OFF%

rem ---- 3. MetaTrader 5 (prices need it; COT data does not) ------------------
tasklist /FI "IMAGENAME eq terminal64.exe" 2>nul | find /i "terminal64.exe" >nul
if errorlevel 1 (
    echo   %YELLOW%[WARN]%OFF%  MetaTrader 5   %DIM%not running - start it and log in for price data%OFF%
) else (
    echo   %GREEN%[ OK ]%OFF%  MetaTrader 5   %DIM%running%OFF%
)

rem ---- 4. Launch ------------------------------------------------------------
echo.
echo   %CYAN%Starting dashboard ...%OFF%  %DIM%the browser opens automatically%OFF%
echo   %DIM%Press Ctrl+C or close this window to stop.%OFF%
echo.

set "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"
"%PY%" -m streamlit run app.py --server.address localhost
if errorlevel 1 goto :fail
exit /b 0

:fail
echo.
echo   %RED%COTForex did not start.%OFF% Scroll up for the reason.
echo.
pause
exit /b 1
