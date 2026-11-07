@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0.venv_emotion\Scripts\python.exe"
if not exist "%PY%" (
 echo First run SETUP_EMOTION_32.cmd; isolated installation.
 pause
 exit /b 1
)
"%PY%" -X utf8 "%~dp0RUN_EMOTION_32.py" %*
set "RC=%ERRORLEVEL%"
if exist "%~dp0REPORTS\LISTEN_EMOTIONS_PILOT4.html" start "" "%~dp0REPORTS\LISTEN_EMOTIONS_PILOT4.html"
echo FINISHED code %RC%. Reports: REPORTS
pause
exit /b %RC%
