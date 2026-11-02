@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 (
 echo [BGXAI ERROR 01] Cannot open folder containing this CMD.
 pause
 exit /b 1
)
title BGXAI LIVE START FIXED - DIAGNOSTIC
color 07
echo ===================================================
echo BGXAI LIVE - FIXED START 0.2.1 - DIAGNOSTIC
echo ===================================================
echo [01] Actual starting folder: "%CD%"
echo [02] Actual CMD file: "%~f0"
if not exist "chitin.key" (
 echo [ERROR 10] chitin.key NOT FOUND. This is not EET game root.
 goto FAILURE
)
echo [OK] chitin.key exists.
if not exist "BGXAI_LIVE_MONITOR.ps1" (
 echo [ERROR 11] BGXAI_LIVE_MONITOR.ps1 NOT FOUND in this folder.
 goto FAILURE
)
echo [OK] BGXAI_LIVE_MONITOR.ps1 exists.
where powershell.exe >nul 2>&1
if errorlevel 1 (
 echo [ERROR 12] Windows PowerShell not found.
 goto FAILURE
)
echo [03] Checking PowerShell syntax BEFORE starting monitor...
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$tok=$null; $err=$null; [void][System.Management.Automation.Language.Parser]::ParseFile((Join-Path (Get-Location).Path 'BGXAI_LIVE_MONITOR.ps1'),[ref]$tok,[ref]$err); if($err.Count) { $err | ForEach-Object { Write-Host ('[PS PARSE ERROR line ' + $_.Extent.StartLineNumber + '] ' + $_.Message) }; exit 8 }; Write-Host '[OK] PowerShell syntax check passed.'"
if errorlevel 1 (
 echo [ERROR 13] PowerShell script has parse error or syntax validation failed.
 goto FAILURE
)
echo [04] Starting monitor. Keep this window open.
echo [04] Using -GameRoot "%CD%" WITHOUT trailing backslash.
echo ===================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CD%\BGXAI_LIVE_MONITOR.ps1" -GameRoot "%CD%"
set "MONITOR_EXIT=%ERRORLEVEL%"
echo.
echo ===================================================
echo [BGXAI] Monitor exited with code %MONITOR_EXIT%.
if "%MONITOR_EXIT%"=="0" echo [BGXAI] Normal stop requested.
if not "%MONITOR_EXIT%"=="0" echo [BGXAI ERROR 20] PowerShell process ended unexpectedly; read the error above.
echo Leave this window open and photograph the COMPLETE output.
echo ===================================================
pause
exit /b %MONITOR_EXIT%
:FAILURE
echo ===================================================
echo [BGXAI START FAILED] Screenshot the error code above.
echo No game files, scripts, or saves were changed.
echo ===================================================
pause
exit /b 1
