@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul

title XANOS - UPDATE AND RUN

set "XANOS_API=https://api.github.com/repos/jeleZa112/nwn-xanos-updates"
set "XANOS_RAW=https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/main/XANOS_CURRENT.cmd"
set "XANOS_DIR=%LOCALAPPDATA%\NWN_XANOS_UPDATER"
set "XANOS_NEW=%XANOS_DIR%\XANOS_CURRENT.new.cmd"
set "XANOS_CACHE=%XANOS_DIR%\XANOS_LAST_GOOD.cmd"

if not exist "%XANOS_DIR%" mkdir "%XANOS_DIR%" >nul 2>nul
del /q "%XANOS_NEW%" >nul 2>nul

echo ============================================================
echo   XANOS - UPDATE AND RUN
echo   UPDATER 2.1 - API FIRST / IMMUTABLE COMMIT
echo ============================================================
echo [1/3] Resolving newest GitHub main commit...

set "XANOS_DL=%XANOS_NEW%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$h=@{'User-Agent'='Xanos-NWN-Updater';'Accept'='application/vnd.github+json';'Cache-Control'='no-cache'};" ^
  "$c=Invoke-RestMethod -UseBasicParsing -Uri ($env:XANOS_API+'/commits/main') -Headers $h -TimeoutSec 15;" ^
  "$sha=[string]$c.sha; if([string]::IsNullOrWhiteSpace($sha)){throw 'No main commit SHA'};" ^
  "$j=Invoke-RestMethod -UseBasicParsing -Uri ($env:XANOS_API+'/contents/XANOS_CURRENT.cmd?ref='+$sha) -Headers $h -TimeoutSec 15;" ^
  "if(!$j.content){throw 'GitHub API returned no payload content'};" ^
  "$b=[Convert]::FromBase64String(([string]$j.content -replace '\s',''));" ^
  "[IO.File]::WriteAllBytes($env:XANOS_DL,$b);" ^
  "Write-Host ('      commit '+$sha.Substring(0,12)+' fetched via GitHub API') -ForegroundColor DarkCyan"
if errorlevel 1 goto RAW_FALLBACK
goto VALIDATE_DOWNLOAD

:RAW_FALLBACK
echo       GitHub API failed; trying raw fallback...
del /q "%XANOS_NEW%" >nul 2>nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$u='%XANOS_RAW%?ts='+[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();" ^
  "Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $env:XANOS_DL -Headers @{'Cache-Control'='no-cache'} -TimeoutSec 15"
if errorlevel 1 goto DOWNLOAD_FAILED

:VALIDATE_DOWNLOAD
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
echo [XANOS] GitHub download failed on API and raw paths.
echo [XANOS] Starting last working local build...
goto RUN_CACHE

:BUILD_FAILED
echo.
echo [XANOS] New build returned error %XANOS_RC%.
echo [XANOS] Rolling back to last working local build...
goto RUN_CACHE

:RUN_CACHE
if not exist "%XANOS_CACHE%" goto NO_CACHE
echo [XANOS] Starting cached build now...
call "%XANOS_CACHE%"
exit /b %ERRORLEVEL%

:NO_CACHE
echo.
echo [XANOS] No working cached build exists yet.
echo [XANOS] Send this window screenshot to ChatGPT.
pause
exit /b 1
