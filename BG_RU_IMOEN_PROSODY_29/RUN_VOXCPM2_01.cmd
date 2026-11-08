@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
if errorlevel 1 goto :BAD_DIRECTORY

set "MAIN=%~dp0VOXCPM2_PILOT_01.py"
set "BASE_PY=%~dp0..\.venv_qwen\Scripts\python.exe"
set "PILOT_PY=%~dp0.venv_voxcpm2\Scripts\python.exe"

echo BG Voice RU VoxCPM2 - safe Windows launcher
if not exist "%BASE_PY%" goto :BASE_MISSING
"%BASE_PY%" -X utf8 "%MAIN%" --check
if errorlevel 1 goto :CHECK_FAILED

if exist "%PILOT_PY%" goto :CHECK_PACKAGES
echo VoxCPM2 requires a separate environment. Existing Qwen is unaffected.
set /p "OKAY=Type YES to create isolated VoxCPM2 environment: "
if /I not "!OKAY!"=="YES" goto :CANCELLED
"%BASE_PY%" -m venv "%~dp0.venv_voxcpm2"
if errorlevel 1 goto :VENV_FAILED

:CHECK_PACKAGES
"%PILOT_PY%" -c "import voxcpm, soundfile, scipy, torch; print('VoxCPM libraries present')" >nul 2>&1
if not errorlevel 1 goto :CHECK_CUDA

echo VoxCPM2 package missing or incomplete. Checking package mirrors.
set "VOX_PIP_INDEX="
powershell.exe -NoProfile -Command "$ProgressPreference='SilentlyContinue'; try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 12 -Uri 'https://pypi.tuna.tsinghua.edu.cn/simple/voxcpm/'; if($r.StatusCode -eq 200){exit 0} } catch{}; exit 1" >nul 2>&1
if not errorlevel 1 set "VOX_PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple"
if defined VOX_PIP_INDEX goto :INSTALL_PACKAGES
powershell.exe -NoProfile -Command "$ProgressPreference='SilentlyContinue'; try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 12 -Uri 'https://mirrors.aliyun.com/pypi/simple/voxcpm/'; if($r.StatusCode -eq 200){exit 0} } catch{}; exit 1" >nul 2>&1
if not errorlevel 1 set "VOX_PIP_INDEX=https://mirrors.aliyun.com/pypi/simple/"
if not defined VOX_PIP_INDEX goto :MIRROR_FAILED

:INSTALL_PACKAGES
echo Installing VoxCPM2 into isolated environment from !VOX_PIP_INDEX!
"%PILOT_PY%" -m pip install --disable-pip-version-check --timeout 90 --retries 2 --index-url "!VOX_PIP_INDEX!" voxcpm soundfile scipy
if errorlevel 1 goto :PACKAGE_FAILED

:CHECK_CUDA
echo Checking NVIDIA CUDA in isolated VoxCPM2 environment...
"%PILOT_PY%" -c "import torch,sys; print('PyTorch:',torch.__version__,'CUDA runtime:',torch.version.cuda,'CUDA available:',torch.cuda.is_available());sys.exit(0 if torch.cuda.is_available() else 2)"
if errorlevel 1 goto :INSTALL_CUDA
goto :GENERATE

:INSTALL_CUDA
echo CUDA unavailable in VoxCPM2 Python. Repairing only its PyTorch wheels.
echo This download can be large; do not modify Qwen or its Python environment.
"%PILOT_PY%" -m pip install --disable-pip-version-check --timeout 120 --retries 3 --index-url https://download.pytorch.org/whl/cu128 "torch==2.11.0" "torchaudio==2.11.0"
if errorlevel 1 goto :CUDA_INSTALL_FAILED
"%PILOT_PY%" -c "import torch,sys; print('PyTorch:',torch.__version__,'CUDA runtime:',torch.version.cuda,'CUDA available:',torch.cuda.is_available());sys.exit(0 if torch.cuda.is_available() else 2)"
if errorlevel 1 goto :CUDA_UNAVAILABLE

:GENERATE
echo CUDA CHECK OK. Starting the separate VoxCPM2 generator.
"%PILOT_PY%" -X utf8 "%MAIN%" --run
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto :GENERATION_FAILED
if exist "%~dp0VOXCPM2_PILOT_01_OUTPUT\LISTEN_VOXCPM2_01.html" start "" "%~dp0VOXCPM2_PILOT_01_OUTPUT\LISTEN_VOXCPM2_01.html"
echo VoxCPM2 pilot SUCCESS.
pause
exit /b 0

:GENERATION_FAILED
echo VoxCPM2 generator returned code %RC%. Source files are unchanged.
pause
exit /b %RC%

:BAD_DIRECTORY
echo ERROR: Cannot open the script directory.
pause
exit /b 1

:BASE_MISSING
echo ERROR: Existing Qwen Python was not found. No files changed.
pause
exit /b 1

:CHECK_FAILED
echo ERROR: VoxCPM2 pilot source preflight failed. No install performed.
pause
exit /b 1

:VENV_FAILED
echo ERROR: Separate VoxCPM2 environment could not be created.
pause
exit /b 1

:MIRROR_FAILED
echo ERROR: Both package mirrors are unavailable. Try fixing network routing first.
pause
exit /b 2

:PACKAGE_FAILED
echo ERROR: VoxCPM2 package installation failed; check pip output above.
pause
exit /b 2

:CUDA_INSTALL_FAILED
echo ERROR: Official CUDA PyTorch wheels could not be installed.
pause
exit /b 3

:CUDA_UNAVAILABLE
echo ERROR: CUDA still unavailable. Inspect PyTorch or NVIDIA driver errors above.
pause
exit /b 4

:CANCELLED
echo Cancelled. Existing game, voices, and models preserved.
pause
exit /b 0
