# BGXAI SAFE ONE-FILE UPDATE channel 039. Public code ONLY, no telemetry.
# This file is fetched automatically by the EXISTING BGXAI_UPDATE.cmd in game root.
# Source sync is harmless to live scripts. WeiDU requires separate explicit menu + YES.
param([string]$GameRoot='.')
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$GameRoot=(Resolve-Path -LiteralPath $GameRoot).Path
$expectedRoot='C:\Games\BG_EET_FOXX_NEW'
if($GameRoot.TrimEnd('\') -ine $expectedRoot) {
    Write-Host 'STOP: this update channel is ONLY for C:\Games\BG_EET_FOXX_NEW.'
    exit 2
}
if(!(Test-Path -LiteralPath (Join-Path $GameRoot 'chitin.key') -PathType Leaf)) {
    Write-Host 'STOP: no chitin.key found.'
    exit 2
}
$cache=Join-Path $env:LOCALAPPDATA 'BGXAI_UPDATER'
$head=Join-Path $cache 'head.txt'
if(!(Test-Path -LiteralPath $head -PathType Leaf)){Write-Host 'STOP: pinned GitHub commit missing';exit 2}
$commit=[IO.File]::ReadAllText($head).Trim()
if($commit -notmatch '^[a-fA-F0-9]{40}$'){Write-Host 'STOP: invalid GitHub commit';exit 2}
$bgxSourceDir=Join-Path $GameRoot 'BGXAI_DEV\experimental_039'
$manifestName='BGXAI/fox_new/release_039/manifest.json'
$names=@('BGXAI39_INSTALL.py','setup-BGX39.tp2','BGX39/team_guard_fallback.baf','SOURCE_MANIFEST.json','README_RU.txt','tests/test_team_guard_039.py')
$remotePrefix='BGXAI/fox_new/release_039/'
function Get-VerifiedGitHubBytes([string]$path){
    $headers=@{'User-Agent'='BGXAI-039-Safe-Updater';'Accept'='application/vnd.github+json';'Cache-Control'='no-cache'}
    $uri='https://api.github.com/repos/jeleZa112/nwn-xanos-updates/contents/'+$path+'?ref='+$commit
    $record=Invoke-RestMethod -Method Get -Uri $uri -Headers $headers -TimeoutSec 60 -UseBasicParsing
    if([string]$record.encoding -ne 'base64' -or !$record.content){throw ('Invalid response: '+$path)}
    $bytes=[Convert]::FromBase64String(([string]$record.content -replace '\s',''))
    return ,$bytes
}
function HashBytes([byte[]]$bytes){
    $h=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($h.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}
    finally {$h.Dispose()}
}
function SameFile([string]$f,[string]$expected){
    if(!(Test-Path -LiteralPath $f -PathType Leaf)){return $false}
    $h=[Security.Cryptography.SHA256]::Create()
    try {
        $stream=[IO.File]::OpenRead($f)
        try{$sum=([BitConverter]::ToString($h.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}
        finally{$stream.Dispose()}
    } finally{$h.Dispose()}
    return $sum -eq $expected
}
function AssertNotReparse([string]$item){
    if(Test-Path -LiteralPath $item){
        $obj=Get-Item -LiteralPath $item -Force
        if(($obj.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
            throw ('Refusing redirected/reparse source path: '+$item)
        }
    }
}
function Sync039 {
    AssertNotReparse $GameRoot
    AssertNotReparse (Join-Path $GameRoot 'BGXAI_DEV')
    AssertNotReparse $bgxSourceDir
    Write-Host 'BGXAI: downloading original 039 source at pinned GitHub commit ...'
    $manifestBytes=Get-VerifiedGitHubBytes $manifestName
    $manifest=[Text.Encoding]::UTF8.GetString($manifestBytes) | ConvertFrom-Json
    if($manifest.schema -ne 1 -or $manifest.channel -ne 'bgxai-fox-new-safe-source' -or $manifest.version -ne '0.3.9'){
        throw 'Unrecognized 039 release manifest'
    }
    if($manifest.files.Count -ne $names.Count){throw 'Wrong 039 file count'}
    $pending=@{}
    foreach($file in @($manifest.files)) {
        $name=[string]$file.dest
        $source=[string]$file.source
        if(($names -cnotcontains $name) -or $pending.ContainsKey($name)) {throw 'Unknown/duplicate 039 file'}
        if($source -cne ($remotePrefix+$name)) {throw 'Unexpected source path'}
        $bytes=Get-VerifiedGitHubBytes $source
        if($bytes.Length -ne [int]$file.size -or (HashBytes $bytes) -ne [string]$file.sha256){
            throw ('SHA256/size mismatch: '+$name)
        }
        $pending[$name]=@{bytes=$bytes;hash=[string]$file.sha256}
        Write-Host (' VERIFIED '+$name)
    }
    if($pending.Count -ne $names.Count){throw 'Missing 039 source'}
    # All network/manifest validation is complete before modifying local source files.
    $currentVerified=$true
    foreach($n in $names){
        $file=Join-Path $bgxSourceDir ($n.Replace('/',[IO.Path]::DirectorySeparatorChar))
        if(!(SameFile $file $pending[$n].hash)){$currentVerified=$false}
    }
    if($currentVerified){Write-Host ' BGXAI 039 source ALREADY CURRENT. Live EET untouched.';return}
    if(!(Test-Path -LiteralPath $bgxSourceDir -PathType Container)) {New-Item -ItemType Directory -Path $bgxSourceDir -Force | Out-Null}
    $bakBase=Join-Path $cache ('039_backup_'+(Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
    foreach($n in $names){
        $target=Join-Path $bgxSourceDir ($n.Replace('/',[IO.Path]::DirectorySeparatorChar))
        AssertNotReparse (Split-Path -Parent $target)
        AssertNotReparse $target
        if(Test-Path -LiteralPath $target){
            $b=Join-Path $bakBase ($n.Replace('/',[IO.Path]::DirectorySeparatorChar))
            [IO.Directory]::CreateDirectory((Split-Path -Parent $b))|Out-Null
            [IO.File]::Copy($target,$b,$false)
        }
    }
    foreach($n in $names){
        $target=Join-Path $bgxSourceDir ($n.Replace('/',[IO.Path]::DirectorySeparatorChar))
        [IO.Directory]::CreateDirectory((Split-Path -Parent $target))|Out-Null
        $tmp=$target+'.bgx39.tmp'
        if(Test-Path -LiteralPath $tmp){throw ('Unresolved previous temporary update: '+$tmp)}
        [IO.File]::WriteAllBytes($tmp,[byte[]]$pending[$n].bytes)
        if(!(SameFile $tmp $pending[$n].hash)){throw ('Staged hash mismatch: '+$n)}
        if(Test-Path -LiteralPath $target){[IO.File]::Delete($target)}
        [IO.File]::Move($tmp,$target)
        if(!(SameFile $target $pending[$n].hash)){throw ('Installed source hash mismatch: '+$n)}
    }
    Write-Host ' BGXAI 039 source VERIFIED and SYNCED. Live BDDEFAI and WeiDU untouched.'
}
function Run039([string]$mode){
    $script=Join-Path $bgxSourceDir 'BGXAI39_INSTALL.py'
    if(!(Test-Path -LiteralPath $script)){throw '039 source not synced; choose option 1 first'}
    if($mode -eq '--install' -or $mode -eq '--uninstall'){
        # The Python installer re-verifies its own source manifest, processes,
        # last WeiDU mod, and original backup; asks for typed YES separately.
        Write-Host ' CAUTION: EXPERIMENTAL 039 NOT TESTED IN REAL EET.'
        Write-Host ' Installer is opt-in and will NOT modify files without YES.'
    }
    & py -3 $script $mode
    if($LASTEXITCODE -ne 0){throw ('BGXAI39 installer returned '+$LASTEXITCODE)}
}
Write-Host ''
Write-Host ' BGXAI ONE-FILE UPDATER / EET Foxx / EPS 18.4'
Write-Host ' Installed gameplay checkpoint: BGXAI 0381 (user-confirmed).'
Write-Host ' 1 - Download/verify source BGXAI 039 (no game script changes)'
Write-Host ' 2 - Read-only status of BGXAI 039'
Write-Host ' 3 - EXPERIMENTAL install 039 on top of 038 (requires YES)'
Write-Host ' 4 - WeiDU rollback of 039 ONLY (requires YES)'
Write-Host ' 0 - Exit [default]'
$choice=Read-Host 'Choice [0]'
if([string]::IsNullOrWhiteSpace($choice)){$choice='0'}
if($choice -eq '0'){Write-Host 'No changes.';exit 0}
try{
    if($choice -eq '1'){Sync039;exit 0}
    if($choice -eq '2'){Run039 '--status';exit 0}
    if($choice -eq '3'){Sync039;Run039 '--install';exit 0}
    if($choice -eq '4'){Run039 '--uninstall';exit 0}
    throw 'Unknown menu option: no changes.'
} catch {
    Write-Host ('BGXAI 039 STOP: '+$_.Exception.Message)
    Write-Host 'No automatic rollback or repeated WeiDU attempts. Preserve the reports.'
    exit 1
}
