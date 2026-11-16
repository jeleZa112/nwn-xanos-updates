@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>nul
cd /d "%~dp0"
title BGXAI Priest Modes - EPS-first guarded trial
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher 'py' was not found. No game changes made.
  pause
  exit /b 2
)
:menu
echo.
echo BGXAI PRIEST - HEALER / SUPPORT / BATTLE / AUTO
 echo [1] Read-only status
 echo [2] Read-only LIVE EET IDS+BCS compile preflight
 echo [3] Install BGXPR via WeiDU (separate typed approval)
 echo [4] Rollback BGXPR via WeiDU (separate typed approval)
 echo [0] Exit
set /p BGXPR_CHOICE=Choose: 
if "%BGXPR_CHOICE%"=="0" exit /b 0
if "%BGXPR_CHOICE%"=="1" goto status
if "%BGXPR_CHOICE%"=="2" goto preflight
if "%BGXPR_CHOICE%"=="3" goto install
if "%BGXPR_CHOICE%"=="4" goto rollback
echo Invalid choice. No changes made.
goto menu
:status
py -3 BGXPR_INSTALL.py status
goto finish
:preflight
py -3 BGXPR_INSTALL.py preflight
goto finish
:install
py -3 BGXPR_INSTALL.py preflight
if errorlevel 1 goto finish
echo Close Baldur, InfinityLoader, and WeiDU. Backup outside game required.
set /p BGXPR_CONFIRM=Type INSTALL_BGXPRIEST_MODES exactly: 
if not "%BGXPR_CONFIRM%"=="INSTALL_BGXPRIEST_MODES" goto cancel
py -3 BGXPR_INSTALL.py install --yes --confirm INSTALL_BGXPRIEST_MODES
goto finish
:rollback
py -3 BGXPR_INSTALL.py status
if errorlevel 1 goto finish
echo Close Baldur, InfinityLoader, and WeiDU. Backup outside game required.
set /p BGXPR_CONFIRM=Type ROLLBACK_BGXPRIEST_MODES exactly: 
if not "%BGXPR_CONFIRM%"=="ROLLBACK_BGXPRIEST_MODES" goto cancel
py -3 BGXPR_INSTALL.py rollback --yes --confirm ROLLBACK_BGXPRIEST_MODES
goto finish
:cancel
echo Not approved. No changes made.
goto finish
:finish
if errorlevel 1 echo STOP: DO NOT RETRY AUTOMATICALLY. Send the error text.
pause
goto menu
