@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul

title XANOS - UPDATE AND RUN

set "XANOS_URL=https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/main/XANOS_CURRENT.cmd"
set "XANOS_DIR=%LOCALAPPDATA%\NWN_XANOS_UPDATER"
set "XANOS_NEW=%XANOS_DIR%\XANOS_CURRENT.new.cmd"
set "XANOS_CACHE=%XANOS_DIR%\XANOS_LAST_GOOD.cmd"

if not exist "%XANOS_DIR%" mkdir "%XANOS_DIR%" >nul 2>nul

echo ============================================================
echo   XANOS - UPDATE AND RUN
echo ============================================================
echo [1/3] Checking current build on GitHub...

set "XANOS_DL=%XANOS_NEW%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $u='%XANOS_URL%?ts='+[DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $env:XANOS_DL -Headers @{'Cache-Control'='no-cache'} -TimeoutSec 45"
if errorlevel 1 goto DOWNLOAD_FAILED
if not exist "%XANOS_NEW%" goto DOWNLOAD_FAILED

for %%A in ("%XANOS_NEW%") do set "XANOS_SIZE=%%~zA"
if not defined XANOS_SIZE goto DOWNLOAD_FAILED
if %XANOS_SIZE% LSS 1024 goto DOWNLOAD_FAILED

echo [2/3] Starting newest Xanos build...
call "%XANOS_NEW%"
set "XANOS_RC=%ERRORLEVEL%"
if not "%XANOS_RC%"=="0" goto BUILD_FAILED

copy /y "%XANOS_NEW%" "%XANOS_CACHE%" >nul 2>nul
echo [3/3] OK. Latest working build saved locally.
exit /b 0

:DOWNLOAD_FAILED
echo.
echo [XANOS] GitHub download failed. Trying last working local build...
goto RUN_CACHE

:BUILD_FAILED
echo.
echo [XANOS] New build returned error %XANOS_RC%.
echo [XANOS] Rolling back to last working local build...
goto RUN_CACHE

:RUN_CACHE
if not exist "%XANOS_CACHE%" goto NO_CACHE
call "%XANOS_CACHE%"
exit /b %ERRORLEVEL%

:NO_CACHE
echo.
echo [XANOS] No working cached build exists yet.
echo [XANOS] Send this window screenshot to ChatGPT.
pause
exit /b 1
