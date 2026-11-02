@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 goto BADROOT
if not exist "chitin.key" goto BADROOT
where powershell.exe >nul 2>nul
if errorlevel 1 goto BADPOWERSHELL
set "BGXAI_GAME_ROOT=%CD%"
set "BGXAI_SELF=%~f0"
title BGXAI LIVE 1.0 - ONE FILE
color 07
echo ===================================================
echo BGXAI LIVE 1.0 - ONE FILE - LOCAL - NO SOUND
echo [BGXAI 01] Game: %BGXAI_GAME_ROOT%
echo [BGXAI 02] Checking signed-source manifest and cache...
echo ===================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$raw=[IO.File]::ReadAllText($env:BGXAI_SELF,[Text.Encoding]::ASCII);$tag='##PS_BEGIN##';$i=$raw.LastIndexOf($tag);if($i -lt 0){Write-Host '[BGXAI FATAL 90] Embedded bootstrap missing';exit 90};$code=$raw.Substring($i+$tag.Length);& ([scriptblock]::Create($code))"
set "BGXAI_EXIT=%ERRORLEVEL%"
echo.
echo ===================================================
echo BGXAI LIVE exit code: %BGXAI_EXIT%
echo If a problem occurred, send a screenshot of this window.
echo ===================================================
pause
exit /b %BGXAI_EXIT%
:BADROOT
echo [BGXAI ERROR 10] Put this CMD next to chitin.key in EET game root.
pause
exit /b 10
:BADPOWERSHELL
echo [BGXAI ERROR 11] Windows PowerShell missing.
pause
exit /b 11
##PS_BEGIN##
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$root = $env:BGXAI_GAME_ROOT
$cache = Join-Path $env:LOCALAPPDATA 'BGXAI_LIVE'
$versions = Join-Path $cache 'versions'
$activePath = Join-Path $cache 'active.json'
$previousPath = Join-Path $cache 'previous.json'
[void][IO.Directory]::CreateDirectory($versions)
$manifestUrl = 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/bg-eet-ai/BGXAI/live/latest.json'
$scriptUrl = 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/bg-eet-ai/BGXAI/live/BGXAI_LIVE_MONITOR.ps1'
function Read-State([string]$path) {
  if (!(Test-Path -LiteralPath $path)) { return $null }
  try {
    $st = [IO.File]::ReadAllText($path,[Text.Encoding]::UTF8) | ConvertFrom-Json
    if ($st.version -notmatch '^[0-9a-zA-Z._-]{1,60}$') { return $null }
    if ($st.sha256 -notmatch '^[a-fA-F0-9]{64}$') { return $null }
    if ($st.size -lt 1000 -or $st.size -gt 200000) { return $null }
    return $st
  } catch { return $null }
}
function Verified-File($st) {
  if (!$st) { return $null }
  $p = Join-Path (Join-Path $versions $st.version) 'BGXAI_LIVE_MONITOR.ps1'
  if (!(Test-Path -LiteralPath $p -PathType Leaf)) { return $null }
  if ((Get-Item -LiteralPath $p).Length -ne [long]$st.size) { return $null }
  if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ine [string]$st.sha256) { return $null }
  return $p
}
function Save-State([string]$path,$st) {
  $json = @{version=[string]$st.version;size=[long]$st.size;sha256=[string]$st.sha256} | ConvertTo-Json -Compress
  [IO.File]::WriteAllText($path,$json,[Text.Encoding]::UTF8)
}
$old = Read-State $activePath
$oldFile = Verified-File $old
$updated = $false
try {
  $m = Invoke-RestMethod -Uri $manifestUrl -UseBasicParsing -TimeoutSec 15
  if ($m.channel -ne 'local-readonly' -or $m.version -notmatch '^[0-9a-zA-Z._-]{1,60}$') { throw 'manifest invalid: channel/version' }
  if (@($m.files).Count -ne 1) { throw 'manifest invalid: expected one file' }
  $entry = @($m.files)[0]
  if ($entry.path -ne 'BGXAI/live/BGXAI_LIVE_MONITOR.ps1' -or $entry.name -ne 'BGXAI_LIVE_MONITOR.ps1') { throw 'manifest invalid: file path' }
  if ($entry.sha256 -notmatch '^[a-fA-F0-9]{64}$' -or $entry.size -lt 1000 -or $entry.size -gt 200000) { throw 'manifest invalid: hash/size' }
  $target = @{version=[string]$m.version;sha256=[string]$entry.sha256;size=[long]$entry.size}
  if ($oldFile -and $old.version -eq $target.version -and $old.sha256 -ne $target.sha256) { throw 'release version reused with a different SHA256: refusing overwrite' }
  $targetFile = Verified-File $target
  if (!$targetFile) {
    $newDir = Join-Path $versions $target.version
    [void][IO.Directory]::CreateDirectory($newDir)
    $tmp = Join-Path $newDir 'incoming.tmp'
    Invoke-WebRequest -Uri $scriptUrl -UseBasicParsing -TimeoutSec 25 -OutFile $tmp
    if ((Get-Item -LiteralPath $tmp).Length -ne [long]$target.size) { throw 'download size mismatch' }
    if ((Get-FileHash -LiteralPath $tmp -Algorithm SHA256).Hash -ine $target.sha256) { throw 'download SHA256 mismatch' }
    $tok = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($tmp,[ref]$tok,[ref]$parseErrors)
    if (@($parseErrors).Count -gt 0) { throw ('PowerShell parse error: ' + $parseErrors[0].Message) }
    Move-Item -LiteralPath $tmp -Destination (Join-Path $newDir 'BGXAI_LIVE_MONITOR.ps1') -Force
    $targetFile = Verified-File $target
    if (!$targetFile) { throw 'stage verification failed' }
  }
  if (!$oldFile -or $old.version -ne $target.version -or $old.sha256 -ne $target.sha256) {
    if ($oldFile) { Save-State $previousPath $old }
    Save-State $activePath $target
    $updated = $true
  }
  Write-Host ('[BGXAI 03] VERIFIED SHA256: ' + $target.version) -ForegroundColor Green
} catch {
  Write-Host ('[BGXAI WARNING 20] GitHub update: ' + $_.Exception.Message) -ForegroundColor Yellow
  if (!$oldFile) { Write-Host '[BGXAI FATAL 21] No verified cached version. Internet required for first run.' -ForegroundColor Red; exit 21 }
  Write-Host ('[BGXAI 03] Offline verified cache: ' + $old.version) -ForegroundColor Yellow
}
$active = Read-State $activePath
$scriptPath = Verified-File $active
if (!$scriptPath) { Write-Host '[BGXAI FATAL 22] Cached monitor failed integrity verification.' -ForegroundColor Red; exit 22 }
Write-Host ('[BGXAI READY] Validated local monitor ' + $active.version) -ForegroundColor Green
Write-Host ('[BGXAI] Launch: ' + $scriptPath)
try {
  & $scriptPath -GameRoot $root
  exit 0
} catch {
  Write-Host ('[BGXAI ERROR 30] Monitor failed: ' + $_.Exception.Message) -ForegroundColor Red
  if ($updated -and $oldFile) {
    Save-State $activePath $old
    Write-Host '[BGXAI ROLLBACK] Previous verified version restored for next run.' -ForegroundColor Yellow
  }
  exit 30
}
