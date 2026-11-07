@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "BASE_PY=%~dp0..\.venv_qwen\Scripts\python.exe"
set "EMO_PY=%~dp0.venv_emotion32\Scripts\python.exe"
if not exist "%BASE_PY%" (
 echo ERROR: Existing Qwen Python not found. Nothing changed.
 pause
 exit /b 1
)
"%BASE_PY%" -X utf8 "%~dp0EMOTION_ANALYSIS_32.py" --check
if errorlevel 1 (
 echo Source preflight failed. Copy your existing IMOEN.zip into bg_voice_release_v2.
 pause
 exit /b 1
)
if not exist "%EMO_PY%" (
 echo Creating a SEPARATE emotion2vec environment. Qwen remains unchanged.
 "%BASE_PY%" -m venv "%~dp0.venv_emotion32"
 if errorlevel 1 (
  echo Could not create separate virtual environment.
  pause
  exit /b 1
 )
)
if not exist "%~dp0.venv_emotion32\INSTALLED_32.flag" (
 echo Installing official emotion2vec+ dependencies once. This may download large packages.
 "%EMO_PY%" -m pip install --disable-pip-version-check "funasr>=1.2,<2" "modelscope>=1.20,<3" "soundfile>=0.12,<1" "scipy>=1.11,<2" "numpy>=1.26,<2.3" "torch>=2.4,<3"
 if errorlevel 1 (
  echo Dependency installation failed. See console; do not delete Qwen or retry blindly.
  pause
  exit /b 1
 )
 "%EMO_PY%" -c "import funasr, modelscope, torch, numpy, soundfile, scipy; print('EMOTION ENV VERIFIED')"
 if errorlevel 1 (
  echo Environment import check failed. Qwen not affected.
  pause
  exit /b 1
 )
 echo verified>"%~dp0.venv_emotion32\INSTALLED_32.flag"
)
set "RUN_MODE=--pilot"
if /i "%~1"=="--all" set "RUN_MODE=--all"
"%EMO_PY%" -X utf8 "%~dp0EMOTION_ANALYSIS_32.py" %RUN_MODE%
set "RC=%ERRORLEVEL%"
if exist "%~dp0ANALYSIS\REPORT_EMOTION_32.html" start "" "%~dp0ANALYSIS\REPORT_EMOTION_32.html"
echo Emotion analysis finished with code %RC%.
pause
exit /b %RC%