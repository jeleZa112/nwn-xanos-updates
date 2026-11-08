@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
set "MAIN=%~dp0VOXCPM2_PILOT_01.py"
set "BASE_PY=%~dp0..\.venv_qwen\Scripts\python.exe"
set "PILOT_PY=%~dp0.venv_voxcpm2\Scripts\python.exe"
if not exist "%BASE_PY%" (
 echo Existing Python next to Qwen not found. Nothing changed.
 pause
 exit /b 1
)
"%BASE_PY%" -X utf8 "%MAIN%" --check
if errorlevel 1 (
 echo CHECK FAILED. No new environment created.
 pause
 exit /b 1
)
if not exist "%PILOT_PY%" (
 echo.
 echo This test creates ONLY a separate .venv_voxcpm2 Python environment.
 echo It downloads large free packages and free VoxCPM2 model weights.
 echo Qwen, Rask WAVs and game scripts are NOT modified.
 set /p "OKAY=To proceed type YES: "
 if /I not "!OKAY!"=="YES" (
  echo Cancelled. All working files preserved.
  pause
  exit /b 0
 )
 "%BASE_PY%" -m venv "%~dp0.venv_voxcpm2"
 if errorlevel 1 (
  echo Cannot create isolated VoxCPM2 environment.
  pause
  exit /b 1
 )
)
"%PILOT_PY%" -c "import voxcpm, soundfile, scipy, torch; print('VoxCPM env:', torch.__version__, 'CUDA=',torch.cuda.is_available())" >nul 2>&1
if errorlevel 1 (
 echo Installing VoxCPM2 via official PyPI in ISOLATED environment.
 echo Using 120-second network timeout and retries. This may download multiple large packages.
 set "PIP_DEFAULT_TIMEOUT=120"
 set "PIP_RETRIES=5"
 "%PILOT_PY%" -m pip install --disable-pip-version-check --timeout 120 --retries 5 --index-url https://pypi.org/simple voxcpm soundfile scipy
 if errorlevel 1 (
  echo Install failed; Qwen untouched, see errors above.
  pause
  exit /b 1
 )
)
"%PILOT_PY%" -X utf8 "%MAIN%" --run
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
 if exist "%~dp0VOXCPM2_PILOT_01_OUTPUT\LISTEN_VOXCPM2_01.html" start "" "%~dp0VOXCPM2_PILOT_01_OUTPUT\LISTEN_VOXCPM2_01.html"
)
echo VoxCPM2 pilot exit code: %RC%
pause
exit /b %RC%