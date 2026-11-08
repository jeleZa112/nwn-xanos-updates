@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0..\.venv_qwen\Scripts\python.exe"
if not exist "%PY%" (
 echo ERROR: Qwen Python not found. Nothing changed.
 pause
 exit /b 1
)
"%PY%" -X utf8 "%~dp0MAKE_LAUGH_35.py" --check
if errorlevel 1 (
 echo Preflight failed. Nothing modified.
 pause
 exit /b 1
)
"%PY%" -X utf8 "%~dp0MAKE_LAUGH_35.py"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" if exist "%~dp0LISTEN_LAUGH_35.html" start "" "%~dp0LISTEN_LAUGH_35.html"
pause
exit /b %RC%