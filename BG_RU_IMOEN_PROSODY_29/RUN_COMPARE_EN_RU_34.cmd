@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "BASE_PY=%~dp0..\.venv_qwen\Scripts\python.exe"
set "EMO_PY=%~dp0.venv_emotion32\Scripts\python.exe"
if not exist "%BASE_PY%" (
 echo Existing Python not found: %BASE_PY%
 pause
 exit /b 1
)
"%BASE_PY%" -X utf8 "%~dp0COMPARE_EN_RU_34.py" --check
if errorlevel 1 (
 echo Missing input files. Do not reinstall any models.
 pause
 exit /b 1
)
if not exist "%EMO_PY%" (
 echo Previous separate emotion environment not found. Run the original analysis first.
 pause
 exit /b 1
)
"%EMO_PY%" -X utf8 "%~dp0COMPARE_EN_RU_34.py"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" start "" "%~dp0ANALYSIS\COMPARE_EN_RU_34\LISTEN_EN_RU_34.html"
echo EN/RU comparison finished with exit code %RC%.
pause
exit /b %RC%
