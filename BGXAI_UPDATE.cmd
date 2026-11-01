@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>nul
cd /d "%~dp0"
title BGXAI - GITHUB UPDATE
if not exist "chitin.key" (
  echo ERROR: Place this BGXAI_UPDATE.cmd in the BG EET game folder beside chitin.key.
  pause
  exit /b 1
)
set "BGX_CACHE=%LOCALAPPDATA%\BGXAI_UPDATER"
if not exist "%BGX_CACHE%" mkdir "%BGX_CACHE%"
set "BGX_SCRIPT=%BGX_CACHE%\BGXAI_SYNC.current.ps1"
set "BGX_COMMIT=%BGX_CACHE%\head.txt"
echo BGXAI - fetching latest pilot release from GitHub ...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$base='https://api.github.com/repos/jeleZa112/nwn-xanos-updates';" ^
  "$h=@{'User-Agent'='BGXAI-EET-Updater';'Accept'='application/vnd.github+json';'Cache-Control'='no-cache'};" ^
  "$c=Invoke-RestMethod -Uri ($base+'/commits/bg-eet-ai') -Headers $h -TimeoutSec 30 -UseBasicParsing;" ^
  "$sha=[string]$c.sha; if($sha -notmatch '^[0-9a-fA-F]{40}$'){throw 'Invalid commit sha'};" ^
  "$j=Invoke-RestMethod -Uri ($base+'/contents/BGXAI/BGXAI_SYNC.ps1?ref='+$sha) -Headers $h -TimeoutSec 30 -UseBasicParsing;" ^
  "$bytes=[Convert]::FromBase64String(([string]$j.content -replace '\s',''));" ^
  "if($bytes.Length -lt 3000){throw 'Invalid updater script'};" ^
  "[IO.File]::WriteAllBytes($env:BGX_SCRIPT,$bytes);" ^
  "[IO.File]::WriteAllText($env:BGX_COMMIT,$sha,[Text.Encoding]::ASCII);" ^
  "Write-Host ('GitHub commit '+$sha.Substring(0,12))"
if errorlevel 1 (
  echo ERROR: Cannot fetch updater. No game files were changed.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%BGX_SCRIPT%"
set "BGX_RC=%ERRORLEVEL%"
echo.
if "%BGX_RC%"=="0" (
  echo BGXAI: update/check completed.
) else (
  echo BGXAI ERROR: send this screenshot to ChatGPT. Code %BGX_RC%.
)
pause
exit /b %BGX_RC%
