# BGXAI safe diagnostic updater 2026-11-02
# Only updates diagnostic Lua and backed-up InfinityLoader.ini. Does not touch WeiDU / BGXAI combat files.
param([string]$GameRoot=".")
$ErrorActionPreference="Stop"
$ProgressPreference="SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$repo="https://api.github.com/repos/jeleZa112/nwn-xanos-updates"
$headers=@{"User-Agent"="BGXAI-EET-Updater";"Accept"="application/vnd.github+json";"Cache-Control"="no-cache"}
$GameRoot=(Resolve-Path -LiteralPath $GameRoot).Path
$cache=Join-Path $env:LOCALAPPDATA "BGXAI_UPDATER"
New-Item -Path $cache -ItemType Directory -Force | Out-Null
$log=Join-Path $GameRoot "BGXAI_UPDATE.log"
function Write-UpdateLog([string]$msg) {
    $line="[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content -LiteralPath $log -Value $line -Encoding UTF8
}
function Get-RepoText([string]$name,[string]$commitSha) {
    $uri=$repo + "/contents/" + $name + "?ref=" + $commitSha
    $response=Invoke-RestMethod -Uri $uri -Headers $headers -TimeoutSec 35 -UseBasicParsing
    if($response.encoding -ne "base64" -or -not $response.content) { throw "Invalid GitHub content for $name" }
    $bytes=[Convert]::FromBase64String(([string]$response.content -replace '\s',''))
    return [Text.Encoding]::UTF8.GetString($bytes)
}
try {
    if(!(Test-Path -LiteralPath (Join-Path $GameRoot "chitin.key"))) { throw "Place BGXAI_UPDATE.cmd beside chitin.key" }
    $commitFile=Join-Path $cache "head.txt"
    if(!(Test-Path -LiteralPath $commitFile)) { throw "Missing GitHub commit marker" }
    $sha=[IO.File]::ReadAllText($commitFile).Trim()
    if($sha -notmatch '^[a-fA-F0-9]{40}$') { throw "Invalid commit marker" }
    $stamp=Get-Date -Format "yyyyMMdd_HHmmss"
    Write-UpdateLog "Safe diagnostic update; GitHub commit $($sha.Substring(0,12))"
    $luaPath=Join-Path $GameRoot "override\M_BGXAI.lua"
    $probe=Get-RepoText "BGXAI/M_BGXAI.lua" $sha
    if(!$probe.Contains("FILTERED ACTION PROBE v4") -or $probe.Contains("Infinity_DisplayString")) {
        throw "Unexpected Lua diagnostic module refused"
    }
    if(Test-Path -LiteralPath $luaPath) {
        $oldProbe=Join-Path $cache ("M_BGXAI_$stamp.lua.bak")
        Copy-Item -LiteralPath $luaPath -Destination $oldProbe -Force
    }
    [IO.File]::WriteAllText($luaPath,$probe,(New-Object System.Text.UTF8Encoding($false)))
    Write-UpdateLog "Filtered action probe v4 installed: Khalid, Jaheira, Wolf; 2000 events; no AI edits."
    $iniPath=Join-Path $GameRoot "InfinityLoader.ini"
    if(Test-Path -LiteralPath $iniPath) {
        $iniContents=[IO.File]::ReadAllText($iniPath)
        if([Text.RegularExpressions.Regex]::IsMatch($iniContents,'(?m)^LogFile[ ]*=')) {
            $iniBackup=Join-Path $cache ("InfinityLoader_$stamp.ini.bak")
            Copy-Item -LiteralPath $iniPath -Destination $iniBackup -Force
            $newContents=[Text.RegularExpressions.Regex]::Replace($iniContents,'(?m)^LogFile[ ]*=.*$','LogFile=BGXAI_COMBAT.log')
            [IO.File]::WriteAllText($iniPath,$newContents)
            Write-UpdateLog "InfinityLoader native LogFile enabled; ini backup in updater cache."
        } else { Write-UpdateLog "WARNING: no LogFile key in InfinityLoader.ini; ini left unchanged." }
    } else { Write-UpdateLog "WARNING: InfinityLoader.ini not found; loader logging not configured." }
    $collector=Get-RepoText "BGXAI/BGXAI_DIAGNOSTICS.cmd" $sha
    if(!$collector.Contains("BGXAI_DIAGNOSTICS.txt")) { throw "Invalid diagnostics collector" }
    [IO.File]::WriteAllText((Join-Path $GameRoot "BGXAI_DIAGNOSTICS.cmd"),$collector,[Text.Encoding]::ASCII)
    Write-UpdateLog "SUCCESS: diagnostic update finished; combat scripts untouched."
    Write-UpdateLog "Start via InfinityLoader.exe; check BGXAI_COMBAT.log for FILTERED ACTION HOOK REGISTERED."
    exit 0
} catch {
    Write-UpdateLog ("ERROR: " + $_.Exception.Message)
    exit 1
}
# Padding: documentation for future maintainers
# The old v0.6.15 BAF scripts are still experimental. Updating the safe diagnostic layer
# neither compiles nor reinstalls them. All previously compiled .BS scripts remain unchanged.
# Do not add Unity or EEex action listeners without separate isolated testing.
# Do not call Infinity_DisplayString from a top-level M_*.lua during early load.
