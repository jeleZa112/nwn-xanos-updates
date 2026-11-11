@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>nul
cd /d "%~dp0"
title BGXAI 060 - READ ONLY COMPILE PRECHECK
if not exist "BGXAI60_INSTALL.py" (
 echo BGXAI 060 STOP: unpack this archive to a separate folder first.
 pause
 exit /b 2
)
if not exist "BGX60_RECEIVER.baf" (
 echo BGXAI 060 STOP: source BAF missing. Game unchanged.
 pause
 exit /b 2
)
echo BGXAI 060 - compiling guarded BCS candidate in TEMP only.
echo No install, no game override write, no WeiDU mod change.
py -3 "BGXAI60_INSTALL.py" preflight
set "R=%ERRORLEVEL%"
echo.
if not "%R%"=="0" (
 echo BGXAI 060 PRECHECK BLOCKED. Do not install or retry blindly.
 echo Copy this output to the BGXAI chat.
) else (
 echo BGXAI 060 PRECHECK PASSED. No files installed.
 echo Copy this output to the BGXAI chat.
)
pause
exit /b %R%
