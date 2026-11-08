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
 echo Official PyPI has repeatedly timed out. Checking HTTPS mirrors (maximum 12s each).
 echo External mirrors are optional package indexes; Qwen and original WAVs are untouched.
 set "VOX_PIP_INDEX="
 powershell.exe -NoProfile -Command "$ProgressPreference='SilentlyContinue'; try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 12 -Uri 'https://pypi.tuna.tsinghua.edu.cn/simple/voxcpm/'; if($r.StatusCode -eq 200){exit 0} } catch{}; exit 1" >nul 2>&1
 if not errorlevel 1 set "VOX_PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple"
 if not defined VOX_PIP_INDEX (
  powershell.exe -NoProfile -Command "$ProgressPreference='SilentlyContinue'; try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 12 -Uri 'https://mirrors.aliyun.com/pypi/simple/voxcpm/'; if($r.StatusCode -eq 200){exit 0} } catch{}; exit 1" >nul 2>&1
  if not errorlevel 1 set "VOX_PIP_INDEX=https://mirrors.aliyun.com/pypi/simple/"
 )
 if not defined VOX_PIP_INDEX (
  echo ERROR: Neither Tsinghua nor Aliyun PyPI mirror responded.
  echo This is a network/proxy problem; pip and Qwen were not modified.
  echo Check VPN proxy routing and try again; do not reinstall everything.
  pause
  exit /b 2
 )
 echo Installing through responsive mirror: !VOX_PIP_INDEX!
 set "PIP_DEFAULT_TIMEOUT=90"
 set "PIP_RETRIES=2"
 "%PILOT_PY%" -m pip install --disable-pip-version-check --timeout 90 --retries 2 --index-url "!VOX_PIP_INDEX!" voxcpm soundfile scipy
 if errorlevel 1 (
  echo Install failed; Qwen untouched, see errors above.
  pause
  exit /b 1
 )
)
rem The default PyPI torch on this Windows machine was CPU-only.
rem Repair ONLY the isolated VoxCPM venv with official matching CUDA wheels.
"%PILOT_PY%" -c "import torch,sys; print('PyTorch:',torch.__version__,'CUDA runtime:',torch.version.cuda,'CUDA available:',torch.cuda.is_available());sys.exit(0 if torch.cuda.is_available() else 2)"
if errorlevel 1 (
 echo.
 echo CPU-only PyTorch detected. Installing the OFFICIAL NVIDIA CUDA 12.8 build
 echo into .venv_voxcpm2 ONLY. This may download a large PyTorch wheel.
 echo Qwen CUDA, existing voice references and generated WAVs are untouched.
 set "PIP_DEFAULT_TIMEOUT=120"
 set "PIP_RETRIES=3"
 "%PILOT_PY%" -m pip install --disable-pip-version-check --timeout 120 --retries 3 --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0" "torchaudio==2.11.0"
 if errorlevel 1 (
  echo CUDA wheel install failed. Existing Qwen installation unchanged.
  echo Check connection to download.pytorch.org; do not delete the venv.
  pause
  exit /b 3
 )
 "%PILOT_PY%" -c "import torch,sys; print('PyTorch:',torch.__version__,'CUDA runtime:',torch.version.cuda,'CUDA available:',torch.cuda.is_available());sys.exit(0 if torch.cuda.is_available() else 2)"
 if errorlevel 1 (
  echo CUDA still unavailable. Check NVIDIA driver or library errors above.
  echo Do not install further packages blindly. Qwen is unchanged.
  pause
  exit /b 4
 )
)
echo CUDA CHECK OK. Starting the separate VoxCPM2 generator.
"%PILOT_PY%" -X utf8 "%MAIN%" --run
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" (
 if exist "%~dp0VOXCPM2_PILOT_01_OUTPUT\LISTEN_VOXCPM2_01.html" start "" "%~dp0VOXCPM2_PILOT_01_OUTPUT\LISTEN_VOXCPM2_01.html"
)
echo VoxCPM2 pilot exit code: %RC%
pause
exit /b %RC%