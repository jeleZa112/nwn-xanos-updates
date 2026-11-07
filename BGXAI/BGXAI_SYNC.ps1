# BGXAI single-entry updater, Foxx + EPS + safe opt-in 038/039/040/041 addons.
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
$release041=@{
    id='041';version='0.3.11';manifest=$remoteRoot+'release_041/manifest.json';prefix=$remoteRoot+'release_041/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_041';installer='BGXAI41_INSTALL.py';
    names=@('BGXAI41_INSTALL.py','README_RU.md','SOURCE_MANIFEST.json','build_assets.py',
            'setup-BGX41.tp2','BGX41/icon.tra','BGX41/toggle_icon.baf',
            'combat_ru/GLOSSARY_RU.md','combat_ru/explain_attack.py','combat_ru/parse_attack_feedback.py',
            'tests/test_attack_parser_041.py','tests/test_attack_ru.py','tests/test_installer_041.py',
            'tests/test_runtime_semantics_041.py','tests/test_source_041.py')
}
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
    if($remotePath -notmatch '^BGXAI/fox_new/release_0(39|40|41)/[A-Za-z0-9_./-]+$' -or $remotePath.Contains('..')) {
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
function Generate041Assets($spec) {
    if($spec.id -ne '041'){return}
    $checked=VerifiedManifest $spec
    foreach($name in $spec.names) {
        $f=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
        AssertNotReparse $f
        if((HashFile $f) -cne $checked[$name].sha){throw ('Unverified BGX41 generator/source: '+$name)}
    }
    $manifest=[Text.Encoding]::UTF8.GetString((Get-PinnedBytes $spec.manifest)) | ConvertFrom-Json
    $expected=@('BGX41/BGX41IC.BAM','BGX41/BGX41ON.SPL','BGX41/BGX41OF.SPL')
    $generated=@($manifest.generated_files)
    if($generated.Count -ne 3){throw 'BGX41: incorrect generated asset count'}
    $seen=@{}
    foreach($x in $generated) {
        $name=[string]$x.dest
        if(($expected -cnotcontains $name) -or $seen.ContainsKey($name) -or $x.size -le 0 -or $x.size -gt 5000 -or [string]$x.sha256 -cnotmatch '^[a-f0-9]{64}$'){
            throw 'BGX41: invalid binary metadata'
        }
        $seen[$name]=$x
    }
    $isCurrent=$true
    foreach($name in $expected) {
        $dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
        AssertNotReparse (Split-Path -Parent $dest)
        AssertNotReparse $dest
        if((HashFile $dest) -cne [string]$seen[$name].sha256) {$isCurrent=$false}
    }
    if(!$isCurrent) {
        Write-Host 'BGX41: building OWN icon assets from SHA256-verified source (no game changes).'
        $builder=Join-Path $spec.localPath 'build_assets.py'
        & py -3 $builder
        if($LASTEXITCODE -ne 0){throw ('BGX41: asset generator exited '+$LASTEXITCODE)}
    }
    foreach($name in $expected) {
        $dest=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
        if(!(Test-Path -LiteralPath $dest -PathType Leaf)){throw ('BGX41: generated binary missing '+$name)}
        if((Get-Item -LiteralPath $dest).Length -ne [int]$seen[$name].size -or (HashFile $dest) -cne [string]$seen[$name].sha256){
            throw ('BGX41: generated checksum mismatch '+$name)
        }
        Write-Host (' VERIFIED generated '+$name)
    }
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
    if($isCurrent){Generate041Assets $spec;Write-Host ('BGXAI '+$spec.id+' sources already verified. Game unchanged.');return}
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
    Generate041Assets $spec
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
    Generate041Assets $spec
    $installerPath=Join-Path $spec.localPath $spec.installer
    if($mode -eq '--install' -or $mode -eq '--uninstall'){
        Write-Host 'WARNING: experimental WeiDU change; requires explicit YES.'
        Write-Host 'Game/InfinityLoader/WeiDU must be closed. Preflight, backup and rollback gates active.'
    }
    & py -3 $installerPath $mode
    if($LASTEXITCODE -ne 0){throw ('BGXAI '+$spec.id+' installer returned code '+$LASTEXITCODE)}
}
function Test041ReadOnly {
    # No Python, WeiDU, installation, file writes, or game processes are invoked.
    Write-Host ''
    Write-Host 'BGXAI 041 - GAME PRECHECK (READ ONLY; NO INSTALL)'
    $logPath=Join-Path $GameRoot 'WeiDU.log'
    if(!(Test-Path -LiteralPath $logPath -PathType Leaf)){throw 'WeiDU.log missing'}
    $lines=@(Get-Content -LiteralPath $logPath -ErrorAction Stop)
    $active=@($lines | Where-Object { $_.TrimStart().StartsWith('~') })
    $has039=@($active | Where-Object { $_ -match 'BGX39[^~]*[.]TP2~' }).Count -gt 0
    $has040=@($active | Where-Object { $_ -match 'BGX40[^~]*[.]TP2~' }).Count -gt 0
    $has041=@($active | Where-Object { $_ -match 'BGX41[^~]*[.]TP2~' }).Count -gt 0
    $is040Last=$active.Count -gt 0 -and $active[-1] -match 'BGX40[^~]*[.]TP2~'
    $eps=@($active | Where-Object { $_.ToUpperInvariant().Contains('ENHANCED-POWERGAMING-SCRIPTS') }).Count -gt 0
    Write-Host ('EPS in WeiDU.log: '+$eps)
    Write-Host ('BGX39 in WeiDU.log: '+$has039)
    Write-Host ('BGX40 in WeiDU.log: '+$has040)
    Write-Host ('BGX41 in WeiDU.log: '+$has041)
    Write-Host ('BGX40 is LAST installed WeiDU mod: '+$is040Last)
    $stat=Join-Path $GameRoot 'override\STATDESC.2DA'
    Write-Host ('STATDESC.2DA in override: '+(Test-Path -LiteralPath $stat -PathType Leaf))
    Write-Host 'NOTE: STATDESC may exist in game archives even when not in override.'
    $bcs=Join-Path $GameRoot 'override\BDDEFAI.BCS'
    Write-Host ('EPS script in override: '+(Test-Path -LiteralPath $bcs -PathType Leaf))
    $toolsOk=(Test-Path -LiteralPath (Join-Path $GameRoot 'setup-enhanced-powergaming-scripts.exe') -PathType Leaf)
    Write-Host ('WeiDU executable available: '+$toolsOk)
    if($eps -and $has039 -and $has040 -and !$has041 -and $is040Last -and $toolsOk -and (Test-Path -LiteralPath $bcs -PathType Leaf)) {
        Write-Host 'BGXAI 041 READ-ONLY PRECHECK: BASELINE OK; binary/icon compilation is NOT yet proven.'
    } else {
        Write-Host 'BGXAI 041 READ-ONLY PRECHECK: REVIEW REQUIRED; do NOT install 041.'
    }
    Write-Host 'NO GAME FILES CHANGED.'
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
Write-Host ' 7 - BGXAI 041 game precheck (READ-ONLY; NO INSTALL)' 
Write-Host ' 8 - Download/verify BGXAI 041 (own icon sources; no installation)'
Write-Host ' 9 - Status of BGXAI 041 (game read-only)'
Write-Host ' 10 - EXPERIMENTAL install BGXAI 041 (YES + WeiDU backup; only if 040 last)'
Write-Host ' 11 - Roll back BGXAI 041 (YES; only if 041 last)'
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
      '7' {Test041ReadOnly;break}
      '8' {SyncRelease $release041;break}
      '9' {RunRelease $release041 '--status';break}
      '10' {SyncRelease $release041;RunRelease $release041 '--install';break}
      '11' {RunRelease $release041 '--uninstall';break}
      default {throw 'Unknown menu option, no game change.'}
    }
    exit 0
} catch {
    Write-Host ('BGXAI STOP: '+$_.Exception.Message) -ForegroundColor Red
    Write-Host 'Do not repeat failed installs automatically. Existing working AI left for review.'
    exit 1
}
