@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0..\.venv_qwen\Scripts\python.exe"
if not exist "%PY%" (
 echo Existing Qwen Python not found. Nothing changed.
 pause
 exit /b 1
)
"%PY%" -X utf8 "%~dp0GENERATE_PROSODY_29.py" --check
if errorlevel 1 (
 echo Preflight failed. See PROSODY_29_RUN.log.
 pause
 exit /b 1
)
"%PY%" -X utf8 "%~dp0GENERATE_PROSODY_29.py"
set "RC=%ERRORLEVEL%"
if exist "%~dp0LISTEN_PROSODY_29.html" start "" "%~dp0LISTEN_PROSODY_29.html"
echo Finished with code %RC%. No game files changed.
pause
exit /b %RC%
