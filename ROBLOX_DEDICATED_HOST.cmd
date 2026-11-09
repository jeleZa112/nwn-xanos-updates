@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title ROBLOX - DEDICATED GAME HOST
echo ============================================
echo ROBLOX - DEDICATED GAME HOST
echo ============================================
echo This launcher is for a SEPARATE physical Windows gaming PC.
echo Roblox runs in foreground on that PC while you work on another PC.
echo.
echo No VM, no PostMessage background injection, no other app focus stealing.
echo Mode 15 is still EXPERIMENTAL; full cycle is not confirmed.
echo F10 stops the autopilot when Roblox is the focused window.
echo.
if /i not "%~1"=="--dedicated-host" (
    echo To avoid accidentally taking over your main workstation,
    echo this launcher requires an explicit dedicated-host argument.
    echo.
    echo Start via: ROBLOX_DEDICATED_HOST.cmd --dedicated-host
    echo.
    pause
    exit /b 2
)
if not exist "%~dp0ROBLOX_UPDATE.cmd" (
    echo ERROR: Keep ROBLOX_UPDATE.cmd in the same folder.
    pause
    exit /b 2
)
set "ROBLOX_BG_INPUT=0"
echo INPUT: verified foreground SendInput on this separate PC.
echo Start Roblox normally, use mode 15 and confirm YES when ready.
echo Leave Roblox focused on THIS PC. Do not close/lock its game session.
echo.
call "%~dp0ROBLOX_UPDATE.cmd"
exit /b %ERRORLEVEL%
