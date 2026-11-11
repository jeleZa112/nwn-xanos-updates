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
$release042b=@{
    id='042B';version='0.3.12-042B';manifest=$remoteRoot+'release_042b/manifest.json';prefix=$remoteRoot+'release_042b/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_042b';installer='BGXAI42_INSTALL.py';
    names=@('BGXAI42_INSTALL.py','build_042b_preview.py','guard_source_042a.py',
            'setup-BGX42.tp2','SOURCE_MANIFEST.json','README_RU.md',
            'BGX42/tests/test_installer_042b.py','BGX42/tests/test_recovery_gate.py')
}
$release043p=@{
    id='043P';version='0.3.14-043-PROBE';manifest=$remoteRoot+'release_043p/manifest.json';prefix=$remoteRoot+'release_043p/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_043p';installer='BGXAI43_PROBE_INSTALL.py';
    names=@('BGXAI43_PROBE_INSTALL.py','BGX43/setup-BGX43.tp2','BGX43/M_BGX43Probe.lua',
            'BGX43/tests/test_installer_043.py','README_RU.md','eeex_bridge_043.py',
            'intercept_policy.py','test_eeex_bridge_043.py','SOURCE_MANIFEST.json')
}
$release044=@{
    id='044';version='0.3.15-044-DIAG';manifest=$remoteRoot+'release_044/manifest.json';prefix=$remoteRoot+'release_044/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_044';installer='BGXAI44_INSTALL.py';
    names=@('BGXAI44_INSTALL.py','BGX44/setup-BGX44.tp2','BGX44/M_BGX44Diag.lua',
            'README_RU.md','BGX44/tests/test_installer_044.py',
            'BGX44/tests/test_lua_044.py','SOURCE_MANIFEST.json')
}
$release045=@{
    id='045';version='0.3.16b-045-RESREF-FIX';manifest=$remoteRoot+'release_045b/manifest.json';prefix=$remoteRoot+'release_045b/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_045';installer='BGXAI45_INSTALL.py';
    names=@('BGXAI45_INSTALL.py','BGX45/setup-BGX45.tp2','BGX45/M_BX43.lua',
            'BGX45/M_BX44.lua','README_RU.md','BGX45/tests/test_installer_045.py',
            'BGX45/tests/test_lua_045.py','SOURCE_MANIFEST.json')
}
$release046=@{
    id='046';version='0.3.17-046-ATTACK-FILTER';manifest=$remoteRoot+'release_046/manifest.json';prefix=$remoteRoot+'release_046/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_046';installer='BGXAI46_INSTALL.py';
    names=@('BGXAI46_INSTALL.py','BGX46/setup-BGX46.tp2','BGX46/M_BX43.lua',
            'BGX46/tests/test_installer_046.py','BGX46/tests/test_lua_046.py',
            'README_RU.md','SOURCE_MANIFEST.json')
}
$release047=@{
    id='047';version='0.3.18-047-RESOLVED-TARGET';manifest=$remoteRoot+'release_047/manifest.json';prefix=$remoteRoot+'release_047/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_047';installer='BGXAI47_INSTALL.py';
    names=@('BGXAI47_INSTALL.py','BGX47/setup-BGX47.tp2','BGX47/M_BX43.lua',
            'BGX47/tests/test_installer_047.py','BGX47/tests/test_lua_047.py',
            'README_RU.md','SOURCE_MANIFEST.json')
}
$release048=@{
    id='048';version='0.3.19-048-CONFIRMED-HIT';manifest=$remoteRoot+'release_048/manifest.json';prefix=$remoteRoot+'release_048/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_048';installer='BGXAI48_INSTALL.py';
    names=@('BGXAI48_INSTALL.py','BGX48/setup-BGX48.tp2','BGX48/M_BX43.lua',
            'BGX48/tests/test_installer_048.py','BGX48/tests/test_lua_048.py',
            'README_RU.md','SOURCE_MANIFEST.json')
}
$release049=@{
    id='049';version='0.3.20-049-GUARD-ADVISORY';manifest=$remoteRoot+'release_049/manifest.json';prefix=$remoteRoot+'release_049/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_049';installer='BGXAI49_INSTALL.py';
    names=@('BGXAI49_INSTALL.py','BGX49/setup-BGX49.tp2','BGX49/M_BX43.lua',
            'BGX49/tests/test_installer_049.py','BGX49/tests/test_lua_049.py',
            'README_RU.md','SOURCE_MANIFEST.json')
}
$release054=@{
    id='054';version='0.3.21-054-WEIDU-READONLY';manifest=$remoteRoot+'release_054/manifest.json';prefix=$remoteRoot+'release_054/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_054';installer='compile_guard_054.py';
    names=@('compile_guard_054.py','verify_053_baseline.py','BGX52_guard_receiver_PREVIEW.baf',
            'test_compile_054.py','README_RU.md','SOURCE_MANIFEST.json')
}
$release056=@{
    id='056';version='0.3.22-056-ACTIVE-GUARD-OPTIN';
    manifest=$remoteRoot+'experimental_056_active_guard/manifest.json';prefix=$remoteRoot+'experimental_056_active_guard/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_056';installer='BGXAI56_INSTALL.py';
    names=@('BGX56/M_BX43.lua','BGX56/BGX56_RECEIVER.baf','BGX56/setup-BGX56.tp2','BGXAI56_BUILDER.py','BGXAI56_INSTALL.py','README_RU.md','tests/test_056.py','tests/test_lua_056.py','ci_weidu_056.py','ids/trigger.ids','ids/action.ids','ids/object.ids','ids/modal.ids','SOURCE_MANIFEST.json')
}
$release060=@{
    id='060';version='0.3.26-060-READONLY-COMPILE';
    manifest=$remoteRoot+'experimental_060_direct_response_source_only/manifest.json';
    prefix=$remoteRoot+'experimental_060_direct_response_source_only/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_060';installer='BGXAI60_INSTALL.py';
    names=@('BGX60_RECEIVER.baf','generate_baf.py','BGXAI60_BUILDER.py','BGXAI60_INSTALL.py','test_060.py','test_060_install.py','README_RU.md')
}
function Get-PinnedBytes([string]$remotePath) {
    if($remotePath -notmatch '^BGXAI/fox_new/(?:release_0(39|40|41|42b|43p|44|45|45b|46|47|48|49|54)|experimental_056_active_guard|experimental_060_direct_response_source_only)/[A-Za-z0-9_./-]+$' -or $remotePath.Contains('..')) {
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
    # BGXAI42_INSTALL.py uses NO CLI flag for read-only status.
    # Keep legacy 039/040/041 --status semantics unchanged.
    if($spec.id -eq '042B' -and $mode -eq '--status'){
        & py -3 $installerPath
    } else {
        & py -3 $installerPath $mode
    }
    if($LASTEXITCODE -ne 0){throw ('BGXAI '+$spec.id+' installer returned code '+$LASTEXITCODE)}
}
function Run060Guarded([string]$mode) {
    if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI060 unsafe operation blocked'}
    # Download/verify release before any game-changing action; SyncRelease writes only BGXAI_DEV.
    SyncRelease $release060
    $files=VerifiedManifest $release060
    foreach($name in $release060.names){
        $dest=Join-Path $release060.localPath $name
        AssertNotReparse $dest
        if((HashFile $dest) -cne $files[$name].sha){throw ('BGXAI060 source SHA mismatch: '+$name)}
    }
    $token=if($mode -ceq 'install'){'INSTALL_BGXAI_060'}else{'ROLLBACK_BGXAI_060'}
    Write-Host 'EXPERIMENTAL BGXAI 060: this step modifies the game through WeiDU.'
    Write-Host 'Close Baldur / InfinityLoader first; installer checks 056/060 hashes and creates external verified backup.'
    $confirmation=Read-Host ('Type '+$token+' exactly to authorize or press ENTER to cancel')
    if($confirmation -cne $token){Write-Host 'BGXAI 060 CANCELLED; no game/WeiDU change.';return}
    & py -3 (Join-Path $release060.localPath 'BGXAI60_INSTALL.py') $mode '--yes' '--confirm' 'BGXAI_060_EXPERIMENTAL'
    if($LASTEXITCODE -ne 0){throw ('BGXAI060 '+$mode+' STOP code '+$LASTEXITCODE+'. No automatic retry. Save output for review.')}
    Write-Host ('BGXAI060 '+$mode+' completed; inspect WeiDU status and game behavior.')
}
function Status060ReadOnly {
    $log=Join-Path $GameRoot 'WeiDU.log'
    $bcs=Join-Path $GameRoot 'override\BDDEFAI.BCS'
    $lua=Join-Path $GameRoot 'override\M_BX43.lua'
    AssertNotReparse $log
    AssertNotReparse $bcs
    AssertNotReparse $lua
    if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
    $rows=@(Get-Content -LiteralPath $log -ErrorAction Stop | Where-Object {$_.TrimStart().StartsWith('~')})
    if($rows.Count -lt 1){throw 'WeiDU.log has no active components'}
    $last=[string]$rows[-1]
    $is060=($last -match '(?i)BGX60[/\\]SETUP-BGX60[.]TP2~')
    $is056=($last -match '(?i)BGX56[/\\]SETUP-BGX56[.]TP2~')
    $actualBCS=HashFile $bcs
    $actualLua=HashFile $lua
    Write-Host ('Last WeiDU component: '+$last)
    Write-Host ('BGXAI060 is LAST: '+$is060)
    Write-Host ('BGXAI056 is LAST: '+$is056)
    Write-Host ('056 Lua SHA unchanged: '+($actualLua -ceq '35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab'))
    if($is056){
        Write-Host ('056 BCS SHA correct: '+($actualBCS -ceq '054c1c8e99b4d8ef8fb541287844d46cb81faa4c320f59c3f39f82f8bf0ab87c'))
    } elseif($is060) {
        $stage=Join-Path $GameRoot 'BGX60\staged\BDDEFAI.BCS'
        AssertNotReparse $stage
        Write-Host ('060 staged BCS SHA matches installed: '+((HashFile $stage) -ceq $actualBCS -and $actualBCS.Length -eq 64))
    } else {Write-Host 'BGXAI060/056 is not last; do not install/rollback blindly.'}
    Write-Host ('Installed BCS SHA256: '+$actualBCS)
}
function Test060ReadOnly {
    $spec=$release060
    $list=VerifiedManifest $spec
    foreach($name in $spec.names){
        $dest=Join-Path $spec.localPath $name
        AssertNotReparse $dest
        if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI060 unverified file: '+$name)}
    }
    Write-Host 'BGXAI 060 - READ-ONLY Windows WeiDU compile (NO INSTALL).'
    & py -3 (Join-Path $spec.localPath 'BGXAI60_INSTALL.py') preflight
    if($LASTEXITCODE -ne 0){throw ('BGXAI 060 preflight failed: exit '+$LASTEXITCODE)}
    Write-Host 'BGXAI 060 - preflight PASSED; installed 056 unchanged.'
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
function Test042EPSReadOnly {
    # BGXAI 042 read-only BCS inspection: no WeiDU, Python, process calls, or game writes.
    Write-Host ''
    Write-Host 'BGXAI 042 - EPS GUARD / AUTOATTACK AUDIT (READ ONLY)'
    $fileName=Join-Path $GameRoot 'override\BDDEFAI.BCS'
    if(!(Test-Path -LiteralPath $fileName -PathType Leaf)){throw 'Current BDDEFAI.BCS missing'}
    $bytes=[IO.File]::ReadAllBytes($fileName)
    if($bytes.Length -gt 8000000 -or $bytes.Length -lt 50){throw 'Unexpected compiled BCS size'}
    $bcs=[Text.Encoding]::GetEncoding(28591).GetString($bytes)
    if(!$bcs.StartsWith(('SC'+[char]10))){throw 'Unexpected compiled BCS signature'}
    $blockPattern=[regex]'(?s)CR\nCO\n(.*?)\nRS\n(.*?)\nRS\nCR(?=\n(?:CR|SC))'
    $blocks=$blockPattern.Matches($bcs)
    if($blocks.Count -lt 1){throw 'Unable to recognize complete BCS blocks'}
    $modeCount=0;$guardCount=0;$modeActionList=0;$protectCount=0
    $attackReeval=0;$attackOneRound=0
    $interesting=@()
    for($i=0;$i -lt $blocks.Count;$i++){
        $condition=$blocks[$i].Groups[1].Value
        $actions=$blocks[$i].Groups[2].Value
        $isMode=$condition.Contains('BDAI_ATTACK_MODE')
        $isGuard=$condition.Contains('BGX38_GUARD')
        if($isMode){$modeCount++}
        if($isGuard){$guardCount++}
        if($isMode -and $condition.Contains('16427 ')){$modeActionList++}
        $actionIds=@([regex]::Matches($actions,'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n') | ForEach-Object {$_.Groups[1].Value})
        $protectCount+=@($actionIds | Where-Object {$_ -eq '87'}).Count
        $attackReeval+=@($actionIds | Where-Object {$_ -eq '134'}).Count
        $attackOneRound+=@($actionIds | Where-Object {$_ -eq '105'}).Count
        if(($isMode -or $isGuard) -and $interesting.Count -lt 12){
            $interesting+=('  Block '+($i+1)+': mode='+$isMode+' guard='+$isGuard+
                ' idle='+$condition.Contains('16427 ')+' actions='+($actionIds -join ','))
        }
    }
    Write-Host ('Live BDDEFAI.BCS SHA256: '+(HashBytes $bytes))
    Write-Host ('Bytes: '+$bytes.Length+'; complete blocks: '+$blocks.Count)
    Write-Host ('EPS attack-mode blocks: '+$modeCount+' (ActionListEmpty: '+$modeActionList+')')
    Write-Host ('BGXAI guard-mode blocks: '+$guardCount)
    Write-Host ('Actions: ProtectObject='+$protectCount+' AttackReevaluate='+$attackReeval+' AttackOneRound='+$attackOneRound)
    foreach($item in $interesting){Write-Host $item}
    Write-Host 'Historical copies are NOT used for this audit; game resources READ ONLY.'
    Write-Host '042 audit only; no game files changed by this option.'
}
function Test042BReadOnly {
    # Current game state only: no Python, WeiDU, download or write.
    Write-Host ''
    Write-Host 'BGXAI 042B - LIVE EET READ-ONLY PREFLIGHT'
    $log=Join-Path $GameRoot 'WeiDU.log'
    if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
    $active=@(Get-Content -LiteralPath $log | Where-Object { $_.TrimStart().StartsWith('~') })
    $has41=@($active | Where-Object { $_ -match 'BGX41[^~]*[.]TP2~' }).Count -gt 0
    $has42=@($active | Where-Object { $_ -match 'BGX42[^~]*[.]TP2~' }).Count -gt 0
    $last41=$active.Count -gt 0 -and $active[-1] -match 'BGX41[^~]*[.]TP2~'
    $last42=$active.Count -gt 0 -and $active[-1] -match 'BGX42[^~]*[.]TP2~'
    $eps=@($active | Where-Object { $_.ToUpperInvariant().Contains('ENHANCED-POWERGAMING-SCRIPTS') }).Count -gt 0
    $bcs=Join-Path $GameRoot 'override\BDDEFAI.BCS'
    if(!(Test-Path -LiteralPath $bcs -PathType Leaf)){throw 'BDDEFAI.BCS missing'}
    $hash=HashFile $bcs
    $orig='86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5'
    $patched='8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
    $weidu=Test-Path -LiteralPath (Join-Path $GameRoot 'setup-enhanced-powergaming-scripts.exe') -PathType Leaf
    Write-Host ('EPS installed: '+$eps+'; WeiDU available: '+$weidu)
    Write-Host ('BGX41 present: '+$has41+'; 041 last: '+$last41)
    Write-Host ('BGX42 present: '+$has42+'; 042 last: '+$last42)
    Write-Host ('Live BCS SHA256: '+$hash)
    if($eps -and $weidu -and $has41 -and !$has42 -and $last41 -and $hash -ceq $orig) {
       Write-Host 'BGXAI 042B PRECHECK: BASELINE OK. NOT INSTALLED.'
    } elseif($eps -and $has42 -and $last42 -and $hash -ceq $patched) {
       Write-Host 'BGXAI 042B PRECHECK: PATCH PRESENT. For backup status choose 16.'
    } else {
       Write-Host 'BGXAI 042B PRECHECK: REVIEW REQUIRED. DO NOT INSTALL.'
    }
    Write-Host 'NO GAME FILES CHANGED.'
}
function Test043PReadOnly {
    # Completely read-only live game and EEex preflight; no package download or writes.
    Write-Host ''
    Write-Host 'BGXAI 043P / EEex OBSERVER - PRECHECK (READ ONLY)'
    $logPath=Join-Path $GameRoot 'WeiDU.log'
    if(!(Test-Path -LiteralPath $logPath -PathType Leaf)){throw 'WeiDU.log missing'}
    $active=@(Get-Content -LiteralPath $logPath | Where-Object { $_.TrimStart().StartsWith('~') })
    $has42=@($active | Where-Object { $_ -match 'BGX42[^~]*[.]TP2~' }).Count -gt 0
    $has43=@($active | Where-Object { $_ -match 'BGX43[^~]*[.]TP2~' }).Count -gt 0
    $last42=$active.Count -gt 0 -and $active[-1] -match 'BGX42[^~]*[.]TP2~'
    $last43=$active.Count -gt 0 -and $active[-1] -match 'BGX43[^~]*[.]TP2~'
    $bcs=Join-Path $GameRoot 'override\BDDEFAI.BCS'
    if(!(Test-Path -LiteralPath $bcs -PathType Leaf)){throw 'BDDEFAI.BCS missing'}
    $bcsSha=HashFile $bcs
    $expect='8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
    $eeex=Test-Path -LiteralPath (Join-Path $GameRoot 'override\M___EEex.lua') -PathType Leaf
    $loader=Test-Path -LiteralPath (Join-Path $GameRoot 'InfinityLoader.exe') -PathType Leaf
    $lua=Test-Path -LiteralPath (Join-Path $GameRoot 'override\M_BGX43Probe.lua') -PathType Leaf
    Write-Host ('BGX42 installed: '+$has42+'; 042 last: '+$last42)
    Write-Host ('BGX43 installed: '+$has43+'; 043 last: '+$last43)
    Write-Host ('EEex M___EEex.lua present: '+$eeex+'; InfinityLoader present: '+$loader)
    Write-Host ('Probe Lua in override: '+$lua)
    Write-Host ('BGX42 BCS SHA256: '+$bcsSha)
    if($has42 -and !$has43 -and $last42 -and !$lua -and $eeex -and $loader -and $bcsSha -ceq $expect){
        Write-Host 'BGXAI 043P PRECHECK: BASELINE OK. NOT INSTALLED.'
    } elseif($has43 -and $last43 -and $lua -and $bcsSha -ceq $expect){
        Write-Host 'BGXAI 043P PRECHECK: PROBE PRESENT. Use option 21 for checksum/backup status.'
    } else {
        Write-Host 'BGXAI 043P PRECHECK: REVIEW REQUIRED. DO NOT INSTALL.'
    }
    Write-Host 'NO GAME FILES CHANGED.'
}
function Test044ReadOnly {
    # Live EET preflight ONLY. No network, Python, WeiDU, writes or installs.
    Write-Host ''
    Write-Host 'BGXAI 044 / EEex hotkey diagnosis - READ-ONLY PREFLIGHT'
    $log=Join-Path $GameRoot 'WeiDU.log'
    if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
    $lines=@(Get-Content -LiteralPath $log | Where-Object { $_.TrimStart().StartsWith('~') })
    $has42=@($lines | Where-Object { $_ -match 'BGX42[^~]*[.]TP2~' }).Count -gt 0
    $has43=@($lines | Where-Object { $_ -match 'BGX43[^~]*[.]TP2~' }).Count -gt 0
    $has44=@($lines | Where-Object { $_ -match 'BGX44[^~]*[.]TP2~' }).Count -gt 0
    $last43=$lines.Count -gt 0 -and $lines[-1] -match 'BGX43[^~]*[.]TP2~'
    $last44=$lines.Count -gt 0 -and $lines[-1] -match 'BGX44[^~]*[.]TP2~'
    $bcs=HashFile (Join-Path $GameRoot 'override\BDDEFAI.BCS')
    $obs=HashFile (Join-Path $GameRoot 'override\M_BGX43Probe.lua')
    $goodBCS=$bcs -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
    $goodObs=$obs -ceq 'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f'
    $loader=Test-Path -LiteralPath (Join-Path $GameRoot 'InfinityLoader.exe') -PathType Leaf
    $eeex=Test-Path -LiteralPath (Join-Path $GameRoot 'override\M___EEex.lua') -PathType Leaf
    $diag=Test-Path -LiteralPath (Join-Path $GameRoot 'override\M_BGX44Diag.lua') -PathType Leaf
    Write-Host ('042B installed='+$has42+'; 043P installed='+$has43+'; 043P last='+$last43)
    Write-Host ('044 installed='+$has44+'; 044 last='+$last44+'; 044 lua exists='+$diag)
    Write-Host ('042B exact BCS hash='+$goodBCS+'; 043P exact Lua hash='+$goodObs)
    Write-Host ('EEex boot='+$eeex+'; InfinityLoader='+$loader)
    if($has42 -and $has43 -and $last43 -and !$has44 -and !$diag -and
       $goodBCS -and $goodObs -and $eeex -and $loader) {
        Write-Host 'BGXAI 044 PREFLIGHT: BASELINE OK. NOT INSTALLED.'
    } elseif($has44 -and $last44 -and $diag -and $goodBCS -and $goodObs) {
        Write-Host 'BGXAI 044 PREFLIGHT: ALREADY INSTALLED. Choose 26 for status.'
    } else {
        Write-Host 'BGXAI 044 PREFLIGHT: REVIEW REQUIRED. DO NOT INSTALL.'
    }
    Write-Host 'NO GAME FILES CHANGED.'
}
function Test045ReadOnly {
    # 045 only observes files and WeiDU order: no download / Python / writes / install.
    Write-Host ''
    Write-Host 'BGXAI 045 / EEex 8-char Lua RESREF FIX - READ ONLY PREFLIGHT'
    $log=Join-Path $GameRoot 'WeiDU.log'
    if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
    $lines=@(Get-Content -LiteralPath $log | Where-Object { $_.TrimStart().StartsWith('~') })
    $has42=@($lines | Where-Object { $_ -match 'BGX42[^~]*[.]TP2~' }).Count -gt 0
    $has43=@($lines | Where-Object { $_ -match 'BGX43[^~]*[.]TP2~' }).Count -gt 0
    $has44=@($lines | Where-Object { $_ -match 'BGX44[^~]*[.]TP2~' }).Count -gt 0
    $has45=@($lines | Where-Object { $_ -match 'BGX45[^~]*[.]TP2~' }).Count -gt 0
    $last44=$lines.Count -gt 0 -and $lines[-1] -match 'BGX44[^~]*[.]TP2~'
    $last45=$lines.Count -gt 0 -and $lines[-1] -match 'BGX45[^~]*[.]TP2~'
    $base42=(HashFile (Join-Path $GameRoot 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
    $base43=(HashFile (Join-Path $GameRoot 'override\M_BGX43Probe.lua')) -ceq 'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f'
    $base44=(HashFile (Join-Path $GameRoot 'override\M_BGX44Diag.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
    $short43=Test-Path -LiteralPath (Join-Path $GameRoot 'override\M_BX43.lua') -PathType Leaf
    $short44=Test-Path -LiteralPath (Join-Path $GameRoot 'override\M_BX44.lua') -PathType Leaf
    $boot=Test-Path -LiteralPath (Join-Path $GameRoot 'override\M___EEex.lua') -PathType Leaf
    $loader=Test-Path -LiteralPath (Join-Path $GameRoot 'InfinityLoader.exe') -PathType Leaf
    Write-Host ('042B/043P/044 installed: '+$has42+'/'+$has43+'/'+$has44)
    Write-Host ('044 last: '+$last44+'; 045 installed: '+$has45+'; 045 last: '+$last45)
    Write-Host ('Original 042B/043P/044 SHA256 match: '+$base42+'/'+$base43+'/'+$base44)
    Write-Host ('Short Lua files exist: '+$short43+'/'+$short44)
    Write-Host ('EEex boot='+$boot+'; InfinityLoader='+$loader)
    if($has42 -and $has43 -and $has44 -and $last44 -and !$has45 -and
       !$short43 -and !$short44 -and $base42 -and $base43 -and $base44 -and $boot -and $loader){
        Write-Host 'BGXAI 045 PRECHECK: BASELINE OK. NOT INSTALLED.'
    } elseif($has45 -and $last45 -and $short43 -and $short44 -and $base42 -and $base43 -and $base44) {
        Write-Host 'BGXAI 045 PRECHECK: PRESENT. Choose 31 for detailed hash and rollback status.'
    } else {
        Write-Host 'BGXAI 045 PRECHECK: REVIEW REQUIRED. DO NOT INSTALL.'
    }
    Write-Host 'NO GAME FILES CHANGED.'
}
function Test046ReadOnly {
    # Pure read-only precheck. No network, Python, WeiDU, or file writes.
    Write-Host ''
    Write-Host 'BGXAI 046 ATTACK FILTER - PRECHECK (READ ONLY)'
    $p=Join-Path $GameRoot 'WeiDU.log'
    if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw 'WeiDU.log missing'}
    $e=@(Get-Content -LiteralPath $p | Where-Object { $_.TrimStart().StartsWith('~') })
    $last45=$e.Count -gt 0 -and $e[-1] -match 'BGX45[^~]*[.]TP2~'
    $last46=$e.Count -gt 0 -and $e[-1] -match 'BGX46[^~]*[.]TP2~'
    $present46=@($e | Where-Object { $_ -match 'BGX46[^~]*[.]TP2~' }).Count -gt 0
    $old='f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f'
    $old45=(HashFile (Join-Path $GameRoot 'override\M_BX43.lua')) -ceq $old
    $bcs=(HashFile (Join-Path $GameRoot 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
    $other=(HashFile (Join-Path $GameRoot 'override\M_BX44.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
    Write-Host ('045 last='+$last45+'; 046 present='+$present46+'; 046 last='+$last46)
    Write-Host ('045 observer original='+$old45+'; 042B BCS='+$bcs+'; 044 short Lua='+$other)
    if($last45 -and !$present46 -and $old45 -and $bcs -and $other){
        Write-Host 'BGXAI 046 PRECHECK: BASELINE OK. NOT INSTALLED.'
    } elseif($last46 -and $bcs -and $other) {
        Write-Host 'BGXAI 046 PRECHECK: PRESENT. Use option 36 for exact hash status.'
    } else {
        Write-Host 'BGXAI 046 PRECHECK: REVIEW. DO NOT INSTALL.'
    }
    Write-Host 'NO GAME FILES CHANGED.'
}
function Test047ReadOnly {
    # Pure read-only precheck, no Python/WeiDU/network/changes.
    Write-Host ''
    Write-Host 'BGXAI 047 EEex TARGET RESOLUTION - PRECHECK (READ ONLY)'
    $p=Join-Path $GameRoot 'WeiDU.log'
    if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw 'WeiDU.log missing'}
    $e=@(Get-Content -LiteralPath $p | Where-Object { $_.TrimStart().StartsWith('~') })
    $last46=$e.Count -gt 0 -and $e[-1] -match 'BGX46[^~]*[.]TP2~'
    $last47=$e.Count -gt 0 -and $e[-1] -match 'BGX47[^~]*[.]TP2~'
    $present47=@($e | Where-Object { $_ -match 'BGX47[^~]*[.]TP2~' }).Count -gt 0
    $old46=(HashFile (Join-Path $GameRoot 'override\M_BX43.lua')) -ceq '1c1e314e1f14a693fa0b10d7450e737447a992e9d7900fb7112437f75c26a6a3'
    $bcs=(HashFile (Join-Path $GameRoot 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
    $diag=(HashFile (Join-Path $GameRoot 'override\M_BX44.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
    Write-Host ('046 last='+$last46+'; 047 installed='+$present47+'; 047 last='+$last47)
    Write-Host ('046 Lua verified='+$old46+'; 042B BCS unchanged='+$bcs+'; 044 Lua unchanged='+$diag)
    if($last46 -and !$present47 -and $old46 -and $bcs -and $diag){
        Write-Host 'BGXAI 047 PRECHECK: BASELINE OK. NOT INSTALLED.'
    } elseif($last47 -and $bcs -and $diag) {
        Write-Host 'BGXAI 047 PRECHECK: PRESENT. Use 41 for checksum status.'
    } else {Write-Host 'BGXAI 047 PRECHECK: REVIEW. DO NOT INSTALL.'}
    Write-Host 'NO GAME FILES CHANGED.'
}
function Test048ReadOnly {
    # No download/Python/WeiDU/game writes.
    Write-Host ''
    Write-Host 'BGXAI 048 CONFIRMED HIT OBSERVER - PRECHECK (READ ONLY)'
    $p=Join-Path $GameRoot 'WeiDU.log'
    if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw 'WeiDU.log missing'}
    $e=@(Get-Content -LiteralPath $p | Where-Object { $_.TrimStart().StartsWith('~') })
    $last47=$e.Count -gt 0 -and $e[-1] -match 'BGX47[^~]*[.]TP2~'
    $last48=$e.Count -gt 0 -and $e[-1] -match 'BGX48[^~]*[.]TP2~'
    $present48=@($e | Where-Object { $_ -match 'BGX48[^~]*[.]TP2~' }).Count -gt 0
    $old47=(HashFile (Join-Path $GameRoot 'override\M_BX43.lua')) -ceq 'c5b72a9bd22e120b38aa0d4f82fc9ce3532c31c8676e52cfdc855ee39521ddfd'
    $bcs=(HashFile (Join-Path $GameRoot 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
    $diag=(HashFile (Join-Path $GameRoot 'override\M_BX44.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
    Write-Host ('047 last='+$last47+'; 048 installed='+$present48+'; 048 last='+$last48)
    Write-Host ('047 Lua verified='+$old47+'; 042B BCS unchanged='+$bcs+'; 044 Lua unchanged='+$diag)
    if($last47 -and !$present48 -and $old47 -and $bcs -and $diag) {
        Write-Host 'BGXAI 048 PRECHECK: BASELINE OK. NOT INSTALLED.'
    } elseif($last48 -and $bcs -and $diag) {
        Write-Host 'BGXAI 048 PRECHECK: PRESENT. Use option 46 for checksum status.'
    } else { Write-Host 'BGXAI 048 PRECHECK: REVIEW. DO NOT INSTALL.' }
    Write-Host 'NO GAME FILES CHANGED.'
}
function Test049ReadOnly {
    # Passive baseline verification only; no script execution/download/write.
    Write-Host ''
    Write-Host 'BGXAI 049 GUARD ADVISORY PRECHECK (READ ONLY)'
    $p=Join-Path $GameRoot 'WeiDU.log'
    if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw 'WeiDU.log missing'}
    $e=@(Get-Content -LiteralPath $p | Where-Object { $_.TrimStart().StartsWith('~') })
    $last48=$e.Count -gt 0 -and $e[-1] -match 'BGX48[^~]*[.]TP2~'
    $last49=$e.Count -gt 0 -and $e[-1] -match 'BGX49[^~]*[.]TP2~'
    $present49=@($e | Where-Object { $_ -match 'BGX49[^~]*[.]TP2~' }).Count -gt 0
    $old48=(HashFile (Join-Path $GameRoot 'override\M_BX43.lua')) -ceq '7b7b613c736df4d7d8a360e9879486bfe26ca52b7f29242c64ab6b2a27c694ea'
    $bcs=(HashFile (Join-Path $GameRoot 'override\BDDEFAI.BCS')) -ceq '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
    $diag=(HashFile (Join-Path $GameRoot 'override\M_BX44.lua')) -ceq 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'
    Write-Host ('048 last='+$last48+'; 049 present='+$present49+'; 049 last='+$last49)
    Write-Host ('048 Lua verified='+$old48+'; 042B BCS unchanged='+$bcs+'; 044 Lua unchanged='+$diag)
    if($last48 -and !$present49 -and $old48 -and $bcs -and $diag) {
        Write-Host 'BGXAI 049 PRECHECK: BASELINE OK. NOT INSTALLED.'
    } elseif($last49 -and $bcs -and $diag) {
        Write-Host 'BGXAI 049 PRECHECK: PRESENT. Use option 51 for checksum status.'
    } else {Write-Host 'BGXAI 049 PRECHECK: REVIEW. DO NOT INSTALL.'}
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
Write-Host ' 12 - BGXAI 042 EPS guard/autoattack audit (READ-ONLY)'
Write-Host ' 13 - BGXAI 042B LIVE preflight (READ-ONLY; NO INSTALL)'
Write-Host ' 14 - Download/verify BGXAI 042B SOURCE ONLY'
Write-Host ' 15 - EXPERIMENTAL install BGXAI 042B (YES + WeiDU backups)'
Write-Host ' 16 - BGXAI 042B status (READ-ONLY; first download via 14)'
Write-Host ' 17 - Roll back BGXAI 042B (YES; only if last + verified backups)'
Write-Host ' 18 - BGXAI 043P EEex passive observer PRECHECK (READ ONLY)'
Write-Host ' 19 - Download/verify BGXAI 043P source ONLY'
Write-Host ' 20 - EXPERIMENTAL install PASSIVE BGXAI 043P (YES + WeiDU backup)'
Write-Host ' 21 - BGXAI 043P status (READ ONLY; needs 19 first)'
Write-Host ' 22 - Roll back BGXAI 043P (YES; only if last + verified backup)'
Write-Host ' 23 - BGXAI 044 hotkey diagnostic PRECHECK (READ ONLY)'
Write-Host ' 24 - Download/verify BGXAI 044 source ONLY'
Write-Host ' 25 - EXPERIMENTAL install PASSIVE BGXAI 044 (YES + WeiDU backup)'
Write-Host ' 26 - BGXAI 044 status (READ ONLY; after 24/25)'
Write-Host ' 27 - Roll back BGXAI 044 (YES; only if last + verified backup)'
Write-Host ' 28 - BGXAI 045 short-Lua-resref PRECHECK (READ ONLY)'
Write-Host ' 29 - Download/verify BGXAI 045 source ONLY'
Write-Host ' 30 - EXPERIMENTAL install PASSIVE BGXAI 045 resref FIX (YES + WeiDU backup)'
Write-Host ' 31 - BGXAI 045 status (READ ONLY; after 29/30)'
Write-Host ' 32 - Roll back BGXAI 045 (YES; only if last + verified backup)'
Write-Host ' 33 - BGXAI 046 attack observer PRECHECK (READ ONLY)'
Write-Host ' 34 - Download/verify BGXAI 046 SOURCE ONLY'
Write-Host ' 35 - EXPERIMENTAL install PASSIVE BGXAI 046 (YES + WeiDU backup)'
Write-Host ' 36 - BGXAI 046 status (READ ONLY; after 34/35)'
Write-Host ' 37 - Roll back BGXAI 046 (YES; if last + verified backup)'
Write-Host ' 38 - BGXAI 047 target resolver PRECHECK (READ ONLY)'
Write-Host ' 39 - Download/verify BGXAI 047 SOURCE ONLY'
Write-Host ' 40 - EXPERIMENTAL install PASSIVE BGXAI 047 (YES + WeiDU backup)'
Write-Host ' 41 - BGXAI 047 status (READ ONLY; after 39/40)'
Write-Host ' 42 - Roll back BGXAI 047 (YES; only if last + verified backup)'
Write-Host ' 43 - BGXAI 048 weapon-hit PRECHECK (READ ONLY)'
Write-Host ' 44 - Download/verify BGXAI 048 SOURCE ONLY'
Write-Host ' 45 - EXPERIMENTAL install PASSIVE BGXAI 048 (YES + WeiDU backup)'
Write-Host ' 46 - BGXAI 048 status (READ ONLY; after 44/45)'
Write-Host ' 47 - Roll back BGXAI 048 (YES; only if last + verified backup)'
Write-Host ' 48 - BGXAI 049 guard signal PRECHECK (READ ONLY)'
Write-Host ' 49 - Download/verify BGXAI 049 SOURCE ONLY'
Write-Host ' 50 - EXPERIMENTAL install PASSIVE BGXAI 049 (YES + WeiDU backup)'
Write-Host ' 51 - BGXAI 049 status (READ ONLY; after 49/50)'
Write-Host ' 52 - Roll back BGXAI 049 (YES; only if last + verified backup)'
Write-Host ' 53 - BGXAI 054 download/verify read-only compiler SOURCES'
Write-Host ' 54 - BGXAI 054 compile BAF READ ONLY (NO INSTALL / no TP2)'
Write-Host ' 55 - BGXAI 056 active guard PRECHECK (READ ONLY, sources verified)'
Write-Host ' 56 - Download/verify BGXAI 056 ACTIVE GUARD SOURCE ONLY'
Write-Host ' 57 - EXPERIMENTAL install BGXAI 056 ACTIVE F GUARD (YES + WeiDU backups)'
Write-Host ' 58 - BGXAI 056 active guard STATUS (READ ONLY)'
Write-Host ' 59 - Roll back BGXAI 056 (YES + verified last WeiDU backup)'
Write-Host ' 60 - Download/verify BGXAI 060 SOURCE ONLY (NO INSTALL)'
Write-Host ' 61 - BGXAI 060 read-only compiler PRECHECK (NO INSTALL)'
Write-Host ' 62 - EXPERIMENTAL install BGXAI 060 (explicit phrase + verified WeiDU backup)'
Write-Host ' 63 - BGXAI 060/056 install STATUS (READ ONLY)'
Write-Host ' 64 - Roll back BGXAI 060 to 056 (explicit phrase + verified WeiDU backup)'
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
      '12' {Test042EPSReadOnly;break}
      '13' {Test042BReadOnly;break}
      '14' {SyncRelease $release042b;break}
      '15' {SyncRelease $release042b;RunRelease $release042b '--install';break}
      '16' {RunRelease $release042b '--status';break}
      '17' {SyncRelease $release042b;RunRelease $release042b '--uninstall';break}
      '18' {Test043PReadOnly;break}
      '19' {SyncRelease $release043p;break}
      '20' {SyncRelease $release043p;RunRelease $release043p '--install';break}
      '21' {RunRelease $release043p '--status';break}
      '22' {SyncRelease $release043p;RunRelease $release043p '--uninstall';break}
      '23' {Test044ReadOnly;break}
      '24' {SyncRelease $release044;break}
      '25' {SyncRelease $release044;RunRelease $release044 '--install';break}
      '26' {RunRelease $release044 '--status';break}
      '27' {SyncRelease $release044;RunRelease $release044 '--uninstall';break}
      '28' {Test045ReadOnly;break}
      '29' {SyncRelease $release045;break}
      '30' {SyncRelease $release045;RunRelease $release045 '--install';break}
      '31' {RunRelease $release045 '--status';break}
      '32' {SyncRelease $release045;RunRelease $release045 '--uninstall';break}
      '33' {Test046ReadOnly;break}
      '34' {SyncRelease $release046;break}
      '35' {SyncRelease $release046;RunRelease $release046 '--install';break}
      '36' {RunRelease $release046 '--status';break}
      '37' {SyncRelease $release046;RunRelease $release046 '--uninstall';break}
      '38' {Test047ReadOnly;break}
      '39' {SyncRelease $release047;break}
      '40' {SyncRelease $release047;RunRelease $release047 '--install';break}
      '41' {RunRelease $release047 '--status';break}
      '42' {SyncRelease $release047;RunRelease $release047 '--uninstall';break}
      '43' {Test048ReadOnly;break}
      '44' {SyncRelease $release048;break}
      '45' {SyncRelease $release048;RunRelease $release048 '--install';break}
      '46' {RunRelease $release048 '--status';break}
      '47' {SyncRelease $release048;RunRelease $release048 '--uninstall';break}
      '48' {Test049ReadOnly;break}
      '49' {SyncRelease $release049;break}
      '50' {SyncRelease $release049;RunRelease $release049 '--install';break}
      '51' {RunRelease $release049 '--status';break}
      '52' {SyncRelease $release049;RunRelease $release049 '--uninstall';break}
      '53' {SyncRelease $release054;break}
      '54' {SyncRelease $release054;RunRelease $release054 '--compile-readonly';break}
      '55' {SyncRelease $release056;RunRelease $release056 '--precheck';break}
      '56' {SyncRelease $release056;break}
      '57' {SyncRelease $release056;RunRelease $release056 '--install';break}
      '58' {RunRelease $release056 '--status';break}
      '59' {SyncRelease $release056;RunRelease $release056 '--uninstall';break}
      '60' {SyncRelease $release060;break}
      '61' {SyncRelease $release060;Test060ReadOnly;break}
      '62' {Run060Guarded 'install';break}
      '63' {Status060ReadOnly;break}
      '64' {Run060Guarded 'rollback';break}
      default {throw 'Unknown menu option, no game change.'}
    }
    exit 0
} catch {
    Write-Host ('BGXAI STOP: '+$_.Exception.Message) -ForegroundColor Red
    Write-Host 'Do not repeat failed installs automatically. Existing working AI left for review.'
    exit 1
}
