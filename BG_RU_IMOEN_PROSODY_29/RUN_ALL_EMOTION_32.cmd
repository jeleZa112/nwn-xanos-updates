@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist "%~dp0.venv_emotion\Scripts\python.exe" (
 echo First run RUN_EMOTION_32.cmd (four-file pilot).
 pause
 exit /b 1
)
"%~dp0.venv_emotion\Scripts\python.exe" -X utf8 "%~dp0EMOTION_ANALYZER_32.py" --all
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" start "" "%~dp0EMOTION_32_RESULTS\LISTEN_EMOTIONS.html"
echo Finished with exit code %RC%.
pause
exit /b %RC%