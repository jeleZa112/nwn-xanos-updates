@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0BG_RU_IMOEN_PROSODY_29\VOICE_UPDATER_46.ps1"
set "RC=%ERRORLEVEL%"
echo BG Voice RU updater exit code: %RC%
pause
exit /b %RC%
