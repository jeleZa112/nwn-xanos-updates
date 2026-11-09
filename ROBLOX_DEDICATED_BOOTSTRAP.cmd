@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>&1
title ROBLOX - DEDICATED HOST BOOTSTRAP
set "WORKDIR=%USERPROFILE%\Documents\ROBLOX_BG_AI"
set "UPDATER=%WORKDIR%\ROBLOX_UPDATE.cmd"
echo ==========================================
echo ROBLOX - DEDICATED HOST BOOTSTRAP
echo ==========================================
echo.
echo This launcher is for a SECOND PHYSICAL WINDOWS COMPUTER.
echo Foreground Roblox control will not free the same PC for other work.
echo It will NOT install drivers, edit game files, or bypass game security.
echo.
if /i not "%~1"=="--dedicated-host" (
  echo No action taken. To acknowledge the separate-host requirement:
  echo   ROBLOX_DEDICATED_BOOTSTRAP.cmd --dedicated-host
  echo.
  pause
  exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python launcher "py" not found.
  echo Install supported Python on this Windows gaming PC, then retry.
  pause
  exit /b 2
)
if not exist "%WORKDIR%" mkdir "%WORKDIR%"
if not exist "%WORKDIR%" (
  echo ERROR: Cannot create "%WORKDIR%".
  pause
  exit /b 2
)
set "RB_DEST=%UPDATER%"
echo Downloading the verified existing updater from the Roblox branch...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
 "$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue';$u='https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/roblox-bg-monitor/ROBLOX_UPDATE.cmd';$d=$env:RB_DEST;Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile ($d+'.download') -TimeoutSec 30; $s=[IO.File]::ReadAllText($d+'.download');if($s.Length -lt 1000 -or -not $s.Contains('roblox-bg-monitor/roblox_monitor.py') -or -not $s.Contains('CHECK_VERSION')){throw 'Unexpected updater content'};Move-Item -Force ($d+'.download') $d"
if errorlevel 1 (
  echo ERROR: Could not download/verify updater. No game launch attempted.
  pause
  exit /b 2
)
set "ROBLOX_BG_INPUT=0"
echo.
echo Starting the existing updater in foreground-only input mode.
echo After it opens: choose mode 15, enter YES, and leave Roblox active.
echo Press F10 inside Roblox to stop game control.
echo Your other PC remains independent.
echo.
pushd "%WORKDIR%"
call "%UPDATER%"
set "RC=%ERRORLEVEL%"
popd
echo.
echo Finished with exit code %RC%.
pause
exit /b %RC%
