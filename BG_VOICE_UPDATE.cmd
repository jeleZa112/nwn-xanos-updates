@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0BG_VOICE_UPDATE.ps1"
set "RC=%ERRORLEVEL%"
echo Updater exit code: %RC%
pause
exit /b %RC%
