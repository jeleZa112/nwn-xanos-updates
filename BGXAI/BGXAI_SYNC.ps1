# BGXAI single-entry updater, Foxx + EPS + safe opt-in 038/039/040 addons.
# F mode feedback (040) ships as source with verified SHA256, no new CMD.
param([string]$GameRoot='.')
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$GameRoot=(Resolve-Path -LiteralPath $GameRoot).Path
$expectedRoot='C:\Games\BG_EET_FOXX_NEW'
if($GameRoot.TrimEnd('\') -ine $expectedRoot) {Write-Host 'STOP: wrong game folder';exit 2}
if(!(Test-Path -LiteralPath (Join-Path $GameRoot 'chitin.key') -PathType Leaf)) {Write-Host 'STOP: chitin.key missing';exit 2}
$cacheDir=Join-Path $env:LOCALAPPDATA 'BGXAI_UPDATER'
$pinnedFile=Join-Path $cacheDir 'head.txt'
if(!(Test-Path -LiteralPath $pinnedFile -PathType Leaf)){Write-Host 'STOP: pinned GitHub commit missing';exit 2}
$commitId=[IO.File]::ReadAllText($pinnedFile).Trim()
if($commitId -notmatch '^[a-fA-F0-9]{40}$'){Write-Host 'STOP: invalid pinned GitHub commit';exit 2}
$remoteRoot='BGXAI/fox_new/'
$release040=@{
    id='040';version='0.3.10';manifest=$remoteRoot+'release_040/manifest.json';prefix=$remoteRoot+'release_040/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_040';installer='BGXAI40_INSTALL.py';
    names=@('BGXAI40_INSTALL.py','setup-BGX40.tp2','BGX40/toggle_feedback.baf','BGX40/lang/ru_ru/feedback.tra','SOURCE_MANIFEST.json','README_RU.txt','tests/test_feedback_040.py')
}
$release039=@{
    id='039';version='0.3.9';manifest=$remoteRoot+'release_039/manifest.json';prefix=$remoteRoot+'release_039/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_039';installer='BGXAI39_INSTALL.py';
    names=@('BGXAI39_INSTALL.py','setup-BGX39.tp2','BGX39/team_guard_fallback.baf','SOURCE_MANIFEST.json','README_RU.txt','tests/test_team_guard_039.py')
}
function Get-PinnedBytes([string]$remotePath) {
    if($remotePath -notmatch '^BGXAI/fox_new/release_0(39|40)/[A-Za-z0-9_./-]+$' -or $remotePath.Contains('..')) {
        throw ('Remote source path blocked: '+$remotePath)
    }
    # All sources are publicly hosted; pin content by immutable commit and SHA256 manifest.
    # No requests to api.github.com: avoid unauthenticated per-IP rate limiting.
    $urls=@(
        ('https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'+$commitId+'/'+$remotePath),
        ('https://cdn.jsdelivr.net/gh/jeleZa112/nwn-xanos-updates@'+$commitId+'/'+$remotePath)
    )
    [IO.Directory]::CreateDirectory($cacheDir) | Out-Null
    $temporaryFile=Join-Path $cacheDir ('pinned_'+[guid]::NewGuid().ToString('N')+'.tmp')
    $failures=@()
    try {
        foreach($uri in $urls) {
            try {
                Invoke-WebRequest -Uri $uri -Headers @{'User-Agent'='BGXAI-Foxx-Onefile'} -TimeoutSec 60 -UseBasicParsing -OutFile $temporaryFile -ErrorAction Stop | Out-Null
                $rawBytes=[IO.File]::ReadAllBytes($temporaryFile)
                if($rawBytes.Length -lt 1 -or $rawBytes.Length -gt 500000) {throw ('Unexpected pinned source byte count: '+$remotePath)}
                return ,$rawBytes
            } catch {
                $failures+=($_.Exception.Message)
                if(Test-Path -LiteralPath $temporaryFile){Remove-Item -LiteralPath $temporaryFile -Force -ErrorAction SilentlyContinue}
            }
        }
        throw ('Both raw source hosts failed for '+$remotePath+': '+($failures -join '; '))
    } finally {
        if(Test-Path -LiteralPath $temporaryFile){Remove-Item -LiteralPath $temporaryFile -Force -ErrorAction SilentlyContinue}
    }
}
function HashBytes([byte[]]$payload) {
    $hasher=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($hasher.ComputeHash($payload))).Replace('-','').ToLowerInvariant()}
    finally {$hasher.Dispose()}
}
function HashFile([string]$filePath) {
    if(!(Test-Path -LiteralPath $filePath -PathType Leaf)){return ''}
    $hasher=[Security.Cryptography.SHA256]::Create()
    try {
        $stream=[IO.File]::OpenRead($filePath)
        try{return ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}
        finally {$stream.Dispose()}
    } finally {$hasher.Dispose()}
}
function AssertNotReparse([string]$item) {
    if(Test-Path -LiteralPath $item){
        $node=Get-Item -LiteralPath $item -Force
        if(($node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw ('Reparse path blocked: '+$item)}
    }
}
function VerifiedManifest($spec) {
    $bytes=Get-PinnedBytes $spec.manifest
    if($bytes.Length -gt 30000){throw 'Oversized manifest'}
    $m=[Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
    if($m.schema -ne 1 -or $m.channel -ne 'bgxai-fox-new-safe-source' -or $m.version -ne $spec.version){throw 'Unexpected release manifest'}
    $items=@($m.files)
    if($items.Count -ne $spec.names.Count){throw 'Unexpected release source count'}
    $seen=@{}
    foreach($entry in $items){
        $file=[string]$entry.dest;$remote=[string]$entry.source
        if(($spec.names -cnotcontains $file) -or $seen.ContainsKey($file) -or $remote -cne ($spec.prefix+$file)){throw 'Release path not in allowlist'}
        if($entry.size -le 0 -or $entry.size -gt 500000 -or [string]$entry.sha256 -cnotmatch '^[a-f0-9]{64}$'){throw 'Bad release size/hash'}
        $seen[$file]=@{sha=[string]$entry.sha256;size=[int]$entry.size;remote=$remote}
    }
    if($seen.Count -ne $spec.names.Count){throw 'Missing release files'}
    return $seen
}
function SyncRelease($spec){
    AssertNotReparse $GameRoot
    AssertNotReparse (Join-Path $GameRoot 'BGXAI_DEV')
    AssertNotReparse $spec.localPath
    Write-Host ('Downloading and verifying BGXAI '+$spec.id+' from pinned GitHub commit ...')
    $list=VerifiedManifest $spec
    $payload=@{}
    foreach($name in $spec.names){
        $bytes=Get-PinnedBytes $list[$name].remote
        if($bytes.Length -ne $list[$name].size -or (HashBytes $bytes) -cne $list[$name].sha){throw ('SHA256 mismatch: '+$name)}
        $payload[$name]=$bytes
        Write-Host (' VERIFIED '+$name)
    }
    $isCurrent=$true
    foreach($name in $spec.names){
        $dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
        if((HashFile $dest) -cne $list[$name].sha){$isCurrent=$false}
    }
    if($isCurrent){Write-Host ('BGXAI '+$spec.id+' sources already verified. Game unchanged.');return}
    $stamp=(Get-Date -Format 'yyyyMMdd_HHmmss_fff')
    $oldCopy=Join-Path $cacheDir ($spec.id+'_backup_'+$stamp)
    foreach($name in $spec.names){
        $dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
        AssertNotReparse (Split-Path -Parent $dest)
        AssertNotReparse $dest
        if(Test-Path -LiteralPath $dest){
            $oldFile=Join-Path $oldCopy ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
            [IO.Directory]::CreateDirectory((Split-Path -Parent $oldFile))|Out-Null
            [IO.File]::Copy($dest,$oldFile,$false)
        }
    }
    foreach($name in $spec.names){
        $dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
        [IO.Directory]::CreateDirectory((Split-Path -Parent $dest))|Out-Null
        $temp=$dest+'.bgxsync.tmp'
        if(Test-Path -LiteralPath $temp){throw ('Unresolved temp file, stop: '+$temp)}
        [IO.File]::WriteAllBytes($temp,[byte[]]$payload[$name])
        if((HashFile $temp) -cne $list[$name].sha){throw ('Staged file hash failure: '+$name)}
        if(Test-Path -LiteralPath $dest){[IO.File]::Delete($dest)}
        [IO.File]::Move($temp,$dest)
        if((HashFile $dest) -cne $list[$name].sha){throw ('Source file hash failure: '+$name)}
    }
    Write-Host ('BGXAI '+$spec.id+' SOURCE SYNC DONE. Live scripts and WeiDU unchanged.')
}
function RunRelease($spec,[string]$mode){
    # Before executing local Python, verify every local byte against pinned GitHub manifest.
    $list=VerifiedManifest $spec
    foreach($name in $spec.names){
        $dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
        AssertNotReparse $dest
        if((HashFile $dest) -cne $list[$name].sha){throw ('Unverified local source; select source sync first: '+$name)}
    }
    $installerPath=Join-Path $spec.localPath $spec.installer
    if($mode -eq '--install' -or $mode -eq '--uninstall'){
        Write-Host 'WARNING: experimental WeiDU change; requires explicit YES.'
        Write-Host 'Game/InfinityLoader/WeiDU must be closed. Preflight, backup and rollback gates active.'
    }
    & py -3 $installerPath $mode
    if($LASTEXITCODE -ne 0){throw ('BGXAI '+$spec.id+' installer returned code '+$LASTEXITCODE)}
}
Write-Host ''
Write-Host ' BGXAI ONE-FILE UPDATER / EET Foxx / EPS 18.4'
Write-Host ' Installed baseline: BGXAI 0381 + 039 (user-confirmed in-game).'
Write-Host ' 1 - Download/verify NEW BGXAI 040 (F key shows Guard ON/OFF; source only)'
Write-Host ' 2 - Status of BGXAI 040 (read-only)'
Write-Host ' 3 - EXPERIMENTAL install BGXAI 040 (YES + WeiDU backup)'
Write-Host ' 4 - Roll back ONLY BGXAI 040 (YES + WeiDU)'
Write-Host ' 5 - Status of BGXAI 039 (read-only)'
Write-Host ' 6 - Roll back BGXAI 039 ONLY (must first uninstall 040)'
Write-Host ' 0 - Exit [default]'
$choice=Read-Host 'Choice [0]'
if([string]::IsNullOrWhiteSpace($choice)){$choice='0'}
if($choice -eq '0'){Write-Host 'No changes.';exit 0}
try {
    switch($choice){
      '1' {SyncRelease $release040;break}
      '2' {RunRelease $release040 '--status';break}
      '3' {SyncRelease $release040;RunRelease $release040 '--install';break}
      '4' {RunRelease $release040 '--uninstall';break}
      '5' {RunRelease $release039 '--status';break}
      '6' {RunRelease $release039 '--uninstall';break}
      default {throw 'Unknown menu option, no game change.'}
    }
    exit 0
} catch {
    Write-Host ('BGXAI STOP: '+$_.Exception.Message) -ForegroundColor Red
    Write-Host 'Do not repeat failed installs automatically. Existing working AI left for review.'
    exit 1
}
