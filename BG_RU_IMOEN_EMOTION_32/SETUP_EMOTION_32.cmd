@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "VENV=%~dp0.venv_emotion"
if exist "%VENV%\Scripts\python.exe" goto install
py -3.11 -V >nul 2>&1
if not errorlevel 1 (
 py -3.11 -m venv "%VENV%"
) else (
 py -3.12 -V >nul 2>&1
 if not errorlevel 1 (
  py -3.12 -m venv "%VENV%"
 ) else (
  py -3.13 -V >nul 2>&1
  if not errorlevel 1 (
   py -3.13 -m venv "%VENV%"
  ) else (
   echo Python 3.11, 3.12 or 3.13 required. No Qwen files touched.
   pause
   exit /b 1
  )
 )
)
if errorlevel 1 (echo VENV FAILED & pause & exit /b 1)
:install
echo Installing model runner into separate .venv_emotion
"%VENV%\Scripts\python.exe" -m pip install -U pip
if errorlevel 1 goto fail
"%VENV%\Scripts\python.exe" -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto fail
"%VENV%\Scripts\python.exe" -m pip install "funasr" "modelscope" "numpy" "scipy" "soundfile"
if errorlevel 1 goto fail
"%VENV%\Scripts\python.exe" -X utf8 "%~dp0RUN_EMOTION_32.py" --self-test
if errorlevel 1 goto fail
echo SETUP SUCCESS. Qwen/Applio not modified.
pause
exit /b 0
:fail
echo SETUP FAILED. See lines above. Do not delete your Qwen environment.
pause
exit /b 1
