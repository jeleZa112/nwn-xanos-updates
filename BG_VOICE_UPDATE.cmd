@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0BG_VOICE_UPDATE.ps1"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto :done
set "PAYLOAD=%~dp0BG_RU_IMOEN_PROSODY_29\VOICE_REVIEW_46.py.gz.b64"
set "ENGINE=%~dp0BG_RU_IMOEN_PROSODY_29\VOICE_REVIEW_46.py"
if not exist "%PAYLOAD%" goto :done
set "PYRUN=py -3.11"
py -3.11 -c "import sys" >nul 2>nul
if not errorlevel 1 goto :python_ok
set "PYRUN=python"
python -c "import sys;assert sys.version_info >= (3,9)" >nul 2>nul
if not errorlevel 1 goto :python_ok
echo Python 3.9+ not found; updater succeeded, voice audit skipped.
goto :done
:python_ok
%PYRUN% -c "import base64,gzip,hashlib,pathlib,sys;p=pathlib.Path(sys.argv[1]);d=pathlib.Path(sys.argv[2]);b=gzip.decompress(base64.b64decode(p.read_bytes()));assert hashlib.sha256(b).hexdigest()=='3a877228f6c32e76adb2267394ac741dd1b0369ef1e5bf2692a816b90b6b4d6f','VOICE_AUDIT_HASH_MISMATCH';d.write_bytes(b) if not d.exists() or d.read_bytes()!=b else None" "%PAYLOAD%" "%ENGINE%"
if errorlevel 1 goto :audit_failed
%PYRUN% "%ENGINE%" --self-test
if errorlevel 1 goto :audit_failed
if not defined BG_VOICE_RU_ROOT set "BG_VOICE_RU_ROOT=C:\BG_VOICE_RU_MASTER"
if not exist "%BG_VOICE_RU_ROOT%\" goto :missing_data
%PYRUN% "%ENGINE%" --root "%BG_VOICE_RU_ROOT%"
if errorlevel 1 goto :audit_failed
goto :done
:missing_data
echo BG Voice RU data folder not found: %BG_VOICE_RU_ROOT%
echo Updater succeeded; audit will run when the data folder is available.
goto :done
:audit_failed
echo BG Voice RU audit failed safely; source WAVs and game files unchanged.
set "RC=1"
:done
echo BG Voice RU updater exit code: %RC%
pause
exit /b %RC%
