@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0..\.venv_qwen\Scripts\python.exe"
if not exist "%PY%" (
 echo Existing Python for reports was not found. No changes made.
 pause
 exit /b 1
)
"%PY%" -X utf8 "%~dp0EMOTION_ANALYSIS_32.py" --report-only
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
 if exist "%~dp0ANALYSIS\REPORT_EMOTION_32.html" start "" "%~dp0ANALYSIS\REPORT_EMOTION_32.html"
)
echo Emotion report rebuild finished with exit code %RC%.
pause
exit /b %RC%
