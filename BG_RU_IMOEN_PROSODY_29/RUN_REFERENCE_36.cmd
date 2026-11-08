@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0..\.venv_qwen\Scripts\python.exe"
if not exist "%PY%" (
 echo Existing Qwen environment not found; nothing installed or modified.
 pause
 exit /b 1
)
"%PY%" -X utf8 "%~dp0REFERENCE_PILOT_36.py" --check
if errorlevel 1 (
 echo Preflight failed. See REFERENCE_36_RUN.log; do not install anything.
 pause
 exit /b 1
)
"%PY%" -X utf8 "%~dp0REFERENCE_PILOT_36.py"
set "RC=%ERRORLEVEL%"
if exist "%~dp0LISTEN_REFERENCE_36.html" start "" "%~dp0LISTEN_REFERENCE_36.html"
echo Finished code %RC%. Original voice and game files not changed.
pause
exit /b %RC%