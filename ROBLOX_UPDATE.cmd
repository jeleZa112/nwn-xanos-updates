@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title ROBLOX - VERIFIED ONE FILE UPDATER

echo ============================================
echo   ROBLOX - VERIFIED ONE FILE UPDATER
echo ============================================
echo.
where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python launcher py.exe is missing.
  echo Install Python and check py -3 -V.
  goto STOP
)
py -3 -V
if errorlevel 1 goto STOP

set "MODULE=%~dp0roblox_monitor.py"
set "DOWNLOAD=%~dp0roblox_monitor.py.download"
set "RB_DL_PATH=%DOWNLOAD%"
set "MIN_VERSION=2.2.2"

if exist "%DOWNLOAD%" del /q "%DOWNLOAD%" >nul 2>&1
echo.
echo [1] Downloading fresh Roblox monitor from GitHub...
echo     Trying GitHub raw, website raw and GitHub API.
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
 "$ProgressPreference='SilentlyContinue'; $ErrorActionPreference='Stop'; $t=$env:RB_DL_PATH; $sources=@('https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/roblox-bg-monitor/roblox_monitor.py','https://github.com/jeleZa112/nwn-xanos-updates/raw/refs/heads/roblox-bg-monitor/roblox_monitor.py'); foreach($u in $sources){try{Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 22 -OutFile $t; if((Get-Item $t).Length -gt 50000){Write-Host ('Download OK: '+$u);exit 0}}catch{Write-Host ('Source unavailable: '+$u)}}; try{$uri='https://api.github.com/repos/jeleZa112/nwn-xanos-updates/contents/roblox_monitor.py?ref=roblox-bg-monitor'; $data=Invoke-RestMethod -Uri $uri -TimeoutSec 22 -Headers @{'User-Agent'='ROBLOX-GAME-UPDATER';'Accept'='application/vnd.github+json'}; if($data.content){[IO.File]::WriteAllBytes($t,[Convert]::FromBase64String(($data.content -replace '\s',''))); if((Get-Item $t).Length -gt 50000){Write-Host 'Download OK: GitHub API';exit 0}}}catch{Write-Host ('GitHub API unavailable: '+$_.Exception.Message)};exit 1"
if errorlevel 1 (
  echo WARNING: None of the GitHub servers are reachable from this PC.
  echo Check VPN route for raw.githubusercontent.com, github.com, api.github.com.
  goto LOCAL_CHECK
)

echo.
echo [2] Checking downloaded code and release version...
call :CHECK_VERSION "%DOWNLOAD%"
if errorlevel 1 (
  echo ERROR: Downloaded file is not valid V2.2.2 or newer.
  if exist "%DOWNLOAD%" del /q "%DOWNLOAD%" >nul 2>&1
  goto LOCAL_CHECK
)
py -3 -m py_compile "%DOWNLOAD%" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Downloaded Python code has a syntax problem.
  if exist "%DOWNLOAD%" del /q "%DOWNLOAD%" >nul 2>&1
  goto LOCAL_CHECK
)
move /y "%DOWNLOAD%" "%MODULE%" >nul
if errorlevel 1 (
  echo ERROR: Cannot replace roblox_monitor.py. Close other Python windows.
  goto STOP
)
echo Updated module OK.
goto RUN_CHECK

:LOCAL_CHECK
if exist "%DOWNLOAD%" del /q "%DOWNLOAD%" >nul 2>&1
if not exist "%MODULE%" (
  echo ERROR: No local module found.
  echo Download roblox_monitor.py with Chrome and put it beside this CMD.
  echo https://github.com/jeleZa112/nwn-xanos-updates/blob/roblox-bg-monitor/roblox_monitor.py
  goto STOP
)
echo.
echo [2] Checking existing local module for offline use...
call :CHECK_VERSION "%MODULE%"
if errorlevel 1 (
  echo STOP: local file is older than V2.2.2, or invalid.
  echo DO NOT choose mode 4 in an older release - it does not exist.
  echo Download roblox_monitor.py through Chrome and save beside this CMD.
  echo https://github.com/jeleZa112/nwn-xanos-updates/blob/roblox-bg-monitor/roblox_monitor.py
  goto STOP
)
py -3 -m py_compile "%MODULE%" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Local Python source is invalid.
  goto STOP
)
echo OFFLINE MODE: valid local V2.2.2+ module found.

:RUN_CHECK
echo.
echo [3] Checking Python libraries...
py -3 -c "import numpy, cv2, windows_capture" >nul 2>&1
if errorlevel 1 (
  echo Missing Python libraries. Trying to install...
  py -3 -m pip install --user numpy opencv-python windows-capture
  if errorlevel 1 (
    echo ERROR: Python dependencies could not be installed.
    goto STOP
  )
)
echo.
echo [4] Launching Roblox monitor from this exact file:
echo %MODULE%
echo For movement pilot in an existing match: mode 4, YES, then F8 in Roblox.
echo F9 cancels the pilot. Keep clear of platform edges.
echo.
py -3 "%MODULE%"
echo.
echo Program exited with code %ERRORLEVEL%.
goto STOP

:CHECK_VERSION
py -3 -c "import ast,sys; t=ast.parse(open(sys.argv[1],encoding='utf-8').read()); a=[n.value.value for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='VERSION' for x in n.targets) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str)]; v=a[0] if a else '0.0.0'; print('Found version:',v); sys.exit(0 if tuple(map(int,v.split('.'))) >= (2,2,2) else 2)" "%~1"
exit /b %ERRORLEVEL%

:STOP
echo.
pause
exit /b
