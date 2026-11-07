@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "ENV=%~dp0.venv_emotion"
set "PY=%ENV%\Scripts\python.exe"
if not exist "%PY%" (
 echo Creating separate environment. Existing Qwen/Applio untouched.
 py -3.11 -m venv "%ENV%" 2>nul
 if not exist "%PY%" py -3.12 -m venv "%ENV%" 2>nul
 if not exist "%PY%" py -3.13 -m venv "%ENV%" 2>nul
 if not exist "%PY%" (
  echo ERROR: Python 3.11, 3.12 or 3.13 needed. Qwen not changed.
  pause
  exit /b 1
 )
)
"%PY%" -c "import funasr, numpy, scipy, soundfile" >nul 2>&1
if errorlevel 1 (
 echo Installing emotion analysis dependencies in separate environment ONLY.
 "%PY%" -m pip install --disable-pip-version-check funasr modelscope soundfile scipy numpy
 if errorlevel 1 (
  echo Dependency install failed. No existing tools were changed.
  pause
  exit /b 1
 )
)
"%PY%" -X utf8 "%~dp0EMOTION_ANALYZER_32.py" --check
if errorlevel 1 (
 echo Missing English originals. Place IMOEN.zip next to this CMD, then retry.
 pause
 exit /b 1
)
"%PY%" -X utf8 "%~dp0EMOTION_ANALYZER_32.py"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" start "" "%~dp0EMOTION_32_RESULTS\LISTEN_EMOTIONS.html"
echo Finished with exit code %RC%.
pause
exit /b %RC%