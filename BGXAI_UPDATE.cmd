@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>nul
cd /d "%~dp0"
title BGXAI - ONE FILE UPDATE - RAW BOOTSTRAP
if not exist "chitin.key" (
  echo BGXAI STOP: Place BGXAI_UPDATE.cmd beside chitin.key in your Foxx EET game folder.
  pause
  exit /b 2
)
set "BGX_SELF=%~f0"
set "BGX_ROOT=%~dp0"
set "BGX_CACHE=%LOCALAPPDATA%\BGXAI_UPDATER"
set "BGX_SCRIPT=%BGX_CACHE%\BGXAI_SYNC.current.ps1"
echo BGXAI - one-file updater - RAW download without GitHub REST API ...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$raw=[IO.File]::ReadAllText($env:BGX_SELF); $tag='# BEGIN_BGXAI_RAW_BOOTSTRAP_PS'; $at=$raw.LastIndexOf($tag); if($at -lt 0){throw 'Missing embedded PowerShell'}; & ([ScriptBlock]::Create($raw.Substring($at)))"
set "BGX_RC=%ERRORLEVEL%"
if not "%BGX_RC%"=="0" (
  echo.
  echo BGXAI STOP: Bootstrap failed. Existing EET and EPS unchanged.
  echo Share this output with ChatGPT. No manual retry loop.
  pause
  exit /b %BGX_RC%
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%BGX_SCRIPT%" -GameRoot "%CD%"
set "BGX_RC=%ERRORLEVEL%"
echo.
if "%BGX_RC%"=="0" (
  echo BGXAI: update/status action completed.
) else (
  echo BGXAI STOP: Update action failed with code %BGX_RC%. Preserve this output.
)
pause
exit /b %BGX_RC%
# BEGIN_BGXAI_RAW_BOOTSTRAP_PS
# One-time permanent CMD bootstrap. HTTPS RAW + CDN, immutable ref + SHA256.
# No API calls, no tokens, no direct game/script/WeiDU changes in this phase.
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
try {
    [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
    $gameRoot=[IO.Path]::GetFullPath([string]$env:BGX_ROOT).TrimEnd('\')
    if($gameRoot -ine 'C:\Games\BG_EET_FOXX_NEW') {throw ('Unexpected game root: '+$gameRoot)}
    if(!(Test-Path -LiteralPath (Join-Path $gameRoot 'chitin.key') -PathType Leaf)) {throw 'Missing chitin.key'}
    $cacheDir=Join-Path $env:LOCALAPPDATA 'BGXAI_UPDATER'
    [IO.Directory]::CreateDirectory($cacheDir) | Out-Null
    $temporaryPin=Join-Path $cacheDir ('channel_'+[guid]::NewGuid().ToString('N')+'.json')
    $temporaryScript=Join-Path $cacheDir ('sync_'+[guid]::NewGuid().ToString('N')+'.ps1')
    function Download-Limited([string[]]$uris,[string]$target,[int]$limit) {
        $errorsSeen=@()
        foreach($uri in $uris) {
            try {
                if(Test-Path -LiteralPath $target){Remove-Item -LiteralPath $target -Force}
                Invoke-WebRequest -Uri $uri -Headers @{'User-Agent'='BGXAI-Foxx-Onefile-NoAPI'} -OutFile $target -UseBasicParsing -TimeoutSec 60 -ErrorAction Stop | Out-Null
                $size=(Get-Item -LiteralPath $target).Length
                if($size -lt 1 -or $size -gt $limit) {throw ('Unexpected response size: '+$size)}
                return
            } catch {
                $errorsSeen+=($_.Exception.Message)
            }
        }
        throw ('All download hosts failed: '+($errorsSeen -join ' | '))
    }
    try {
        $pinPath='BGXAI/fox_new/BOOTSTRAP_PIN.json'
        $pinSources=@(
          ('https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/bg-eet-ai/'+$pinPath),
          ('https://cdn.jsdelivr.net/gh/jeleZa112/nwn-xanos-updates@bg-eet-ai/'+$pinPath)
        )
        Download-Limited $pinSources $temporaryPin 4096
        $pin=[IO.File]::ReadAllText($temporaryPin,[Text.Encoding]::UTF8) | ConvertFrom-Json
        if($pin.schema -ne 1 -or $pin.channel -cne 'bgxai-fox-new-onefile' -or $pin.branch -cne 'bg-eet-ai' -or $pin.script_path -cne 'BGXAI/BGXAI_SYNC.ps1') {
            throw 'Unexpected updater channel descriptor'
        }
        $commitId=[string]$pin.commit
        $expectedHash=[string]$pin.script_sha256
        $expectedSize=[int]$pin.script_size
        if($commitId -cnotmatch '^[0-9a-f]{40}$' -or $expectedHash -cnotmatch '^[0-9a-f]{64}$' -or $expectedSize -lt 3000 -or $expectedSize -gt 80000) {
            throw 'Invalid pinned commit, SHA256 or size'
        }
        $scriptSources=@(
          ('https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'+$commitId+'/BGXAI/BGXAI_SYNC.ps1'),
          ('https://cdn.jsdelivr.net/gh/jeleZa112/nwn-xanos-updates@'+$commitId+'/BGXAI/BGXAI_SYNC.ps1')
        )
        Download-Limited $scriptSources $temporaryScript 80000
        if((Get-Item -LiteralPath $temporaryScript).Length -ne $expectedSize) {throw 'Downloaded updater size mismatch'}
        $actualHash=(Get-FileHash -LiteralPath $temporaryScript -Algorithm SHA256).Hash.ToLowerInvariant()
        if($actualHash -cne $expectedHash) {throw 'Downloaded updater SHA256 mismatch; refusing execution'}
        $targetScript=Join-Path $cacheDir 'BGXAI_SYNC.current.ps1'
        [IO.File]::Copy($temporaryScript,$targetScript,$true)
        if((Get-FileHash -LiteralPath $targetScript -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expectedHash) {
            throw 'Cached updater SHA256 mismatch; refusing execution'
        }
        [IO.File]::WriteAllText((Join-Path $cacheDir 'head.txt'),$commitId,[Text.Encoding]::ASCII)
        Write-Host ('BGXAI: verified pinned script '+$commitId.Substring(0,12)+' (SHA256 OK)')
        Write-Host 'GitHub REST API: not used.'
    } finally {
        foreach($item in @($temporaryPin,$temporaryScript)) {
            if(Test-Path -LiteralPath $item) {Remove-Item -LiteralPath $item -Force -ErrorAction SilentlyContinue}
        }
    }
    exit 0
} catch {
    Write-Host ('BGXAI BOOTSTRAP STOP: '+$_.Exception.Message) -ForegroundColor Red
    Write-Host 'No EET game or WeiDU resources were changed.'
    exit 1
}
