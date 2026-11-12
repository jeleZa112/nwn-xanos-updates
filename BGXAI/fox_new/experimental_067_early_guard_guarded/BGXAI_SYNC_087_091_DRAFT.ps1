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
$release061=@{
    id='061';version='0.3.27-061-RESCUE-APPROACH';
    manifest=$remoteRoot+'experimental_061_rescue_approach_source_only/manifest.json';
    prefix=$remoteRoot+'experimental_061_rescue_approach_source_only/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_061';installer='BGXAI61_INSTALL.py';
    names=@('BGX61_RECEIVER.baf','generate_baf.py','BGXAI61_BUILDER.py','BGXAI61_INSTALL.py','test_061.py','test_061_install.py','README_RU.md')
}
$release064=@{
    id='064';version='0.3.29-064-061-SAME-AREA-GUARD-SOURCE';
    manifest=$remoteRoot+'experimental_064_same_area_061_source_only/manifest.json';
    prefix=$remoteRoot+'experimental_064_same_area_061_source_only/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_064';installer='BGXAI64_PREFLIGHT_READONLY.py';
    names=@('M_BX43_064_CANDIDATE.lua','BGX64_BRIDGE_PREPARE_NATIVE.lua','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','README_RU.md','lua64_harness.py','test_064_native.py','test_064_patch.py','test_064_preflight.py','SOURCE_MANIFEST.json')
}
$release064g=@{
    id='064G';version='0.3.30-064-GUARDED-WEIDU-CANDIDATE';
    manifest=$remoteRoot+'experimental_064_guarded_weidu_source_only/manifest.json';
    prefix=$remoteRoot+'experimental_064_guarded_weidu_source_only/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_064_guarded';installer='BGXAI64_INSTALL_SOURCE_ONLY.py';
    names=@('M_BX43_064_CANDIDATE.lua','M_BX43_061_BASELINE_READONLY.lua','BGX64_BRIDGE_PREPARE_NATIVE.lua','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','BGXAI64_INSTALL_SOURCE_ONLY.py','test_064_install_mock.py','test_064_patch.py','test_064_preflight.py','README_RU.md')
}
$release066=@{
    id='066';version='0.3.32-066-MULTI-FRONTLINE-GUARDED';
    manifest=$remoteRoot+'experimental_066_multi_guard_guarded/manifest.json';
    prefix=$remoteRoot+'experimental_066_multi_guard_guarded/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_066_guarded';installer='BGXAI66_INSTALL.py';
    names=@('BGX66_TEAM_BRIDGE.lua','M_BX43_064_BASELINE_READONLY.lua','M_BX43_066_CANDIDATE.lua','build_066.py','BGXAI66_INSTALL.py','BGXAI64_INSTALL_SOURCE_ONLY.py','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','M_BX43_061_BASELINE_READONLY.lua','M_BX43_064_CANDIDATE.lua','test_066_native.py','test_066_install_mock.py','lua65_harness.py','README_RU.md')
}
$release066s=@{
    id='066S';version='0.3.34-066S-CASTER-GUARDED';
    manifest=$remoteRoot+'experimental_066s_guarded_install_candidate/manifest_updater.json';
    prefix=$remoteRoot+'experimental_066s_guarded_install_candidate/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_066s_guarded';installer='BGXAI66S_INSTALL.py';
    names=@('BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf','BGX66_CASTER_SUPPORT.lua','BGXAI64_INSTALL_SOURCE_ONLY.py','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','BGXAI66S_BCS_PATCH.py','BGXAI66S_INSTALL.py','M_BX43_061_BASELINE_READONLY.lua','M_BX43_064_CANDIDATE.lua','M_BX43_066S_CASTER_CANDIDATE.lua','M_BX43_066_BASELINE_READONLY.lua','M_BX43_066_CANDIDATE.lua','README_RELEASE_RU.md','README_RU.md','build_066.py','build_066s.py','ci_weidu_066s.py','generate_receiver.py','ids/action.ids','ids/modal.ids','ids/object.ids','ids/spell.ids','ids/trigger.ids','lua65_harness.py','native_066_fixture.py','test_066s_caster_native.py','test_066s_installer_mock.py','verify_066s.py','verify_release.py')
}
$release067=@{
    id='067';version='0.3.35-067-EARLY-GUARD-GUARDED';
    manifest=$remoteRoot+'experimental_067_early_guard_guarded/manifest_updater.json';
    prefix=$remoteRoot+'experimental_067_early_guard_guarded/';
    localPath=Join-Path $GameRoot 'BGXAI_DEV\experimental_067_early_guard';installer='BGXAI67_INSTALL.py';
    names=@('BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf','BGX66_CASTER_SUPPORT.lua','BGX67_EARLY_GUARD.baf','BGX67_PREHIT_GUARD.lua','BGXAI64_INSTALL_SOURCE_ONLY.py','BGXAI64_PATCH.py','BGXAI64_PREFLIGHT_READONLY.py','BGXAI66S_BCS_PATCH.py','BGXAI66S_INSTALL.py','BGXAI67_BCS_PATCH.py','BGXAI67_INSTALL.py','M_BX43_064_CANDIDATE.lua','M_BX43_066S_CASTER_CANDIDATE.lua','M_BX43_066_BASELINE_READONLY.lua','M_BX43_066_CANDIDATE.lua','M_BX43_067_EARLY_CANDIDATE.lua','README_RU.md','build_066.py','build_066s.py','build_067.py','ci_weidu_067.py','generate_067_baf.py','generate_receiver.py','ids/action.ids','ids/modal.ids','ids/object.ids','ids/spell.ids','ids/trigger.ids','lua65_harness.py','native_066_fixture.py','test_066s_installer_mock.py','test_067_bcs.py','test_067_install_mock.py','test_067_native.py')
}

function Get-PinnedBytes([string]$remotePath) {
    if($remotePath -notmatch '^BGXAI/fox_new/(?:release_0(39|40|41|42b|43p|44|45|45b|46|47|48|49|54)|experimental_056_active_guard|experimental_060_direct_response_source_only|experimental_061_rescue_approach_source_only|experimental_064_same_area_061_source_only|experimental_064_guarded_weidu_source_only|experimental_066_multi_guard_guarded|experimental_066s_guarded_install_candidate|experimental_067_early_guard_guarded)/[A-Za-z0-9_./-]+$' -or $remotePath.Contains('..')) {
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
function Test061ReadOnly {
    $spec=$release061
    $list=VerifiedManifest $spec
    foreach($name in $spec.names){
        $dest=Join-Path $spec.localPath $name
        AssertNotReparse $dest
        if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI061 unverified file: '+$name)}
    }
    Write-Host 'BGXAI 061 - REAL WeiDU BAF + Lua-TTL read-only preflight (NO INSTALL).'
    & py -3 (Join-Path $spec.localPath 'BGXAI61_INSTALL.py') preflight
    if($LASTEXITCODE -ne 0){throw ('BGXAI 061 preflight FAILED: exit '+$LASTEXITCODE+'. No changes to game.')}
    Write-Host 'BGXAI 061 - preflight PASS; installed 060 unchanged.'
}
function Run061Guarded([string]$mode) {
    if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI061 unknown mode blocked'}
    SyncRelease $release061
    $list=VerifiedManifest $release061
    foreach($name in $release061.names){
        $dest=Join-Path $release061.localPath $name
        AssertNotReparse $dest
        if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI061 source SHA mismatch: '+$name)}
    }
    $token=if($mode -ceq 'install'){'INSTALL_BGXAI_061'}else{'ROLLBACK_BGXAI_061'}
    Write-Host 'EXPERIMENTAL BGXAI 061: changes both guarded BCS receiver and Lua request TTL via WeiDU.'
    Write-Host 'Close Baldur / InfinityLoader first. Game hash gates and external verified backup are mandatory.'
    $confirmation=Read-Host ('Type '+$token+' exactly to authorize or ENTER to cancel')
    if($confirmation -cne $token){Write-Host 'BGXAI 061 CANCELLED. Game unchanged.';return}
    & py -3 (Join-Path $release061.localPath 'BGXAI61_INSTALL.py') $mode '--yes' '--confirm' 'BGXAI_061_EXPERIMENTAL'
    if($LASTEXITCODE -ne 0){throw ('BGXAI 061 '+$mode+' STOP code '+$LASTEXITCODE+'. Do not retry blindly.')}
    Write-Host ('BGXAI 061 '+$mode+' completed, inspect status 68.')
}
function Verify064GuardedSource {
    $spec=$release064g
    $list=VerifiedManifest $spec
    foreach($name in $spec.names){
        $dest=Join-Path $spec.localPath $name
        AssertNotReparse $dest
        if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI064G source SHA mismatch: '+$name)}
    }
}
function Test064GuardedReadOnly {
    SyncRelease $release064g
    Verify064GuardedSource
    Write-Host 'BGXAI 064 GUARDED INSTALL PRECHECK - READ ONLY (no game writes).'
    & py -3 (Join-Path $release064g.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') preflight
    if($LASTEXITCODE -ne 0){throw ('BGXAI064 guarded PRECHECK STOP '+$LASTEXITCODE)}
    Write-Host 'BGXAI064 guarded preflight PASS. Installed 061 remains unchanged.'
}
function Status064GuardedReadOnly {
    SyncRelease $release064g
    Verify064GuardedSource
    & py -3 (Join-Path $release064g.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') status
    if($LASTEXITCODE -ne 0){throw ('BGXAI064 guarded STATUS STOP '+$LASTEXITCODE)}
}
function Run064Guarded([string]$mode) {
    if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI064 illegal mode'}
    SyncRelease $release064g
    Verify064GuardedSource
    if($mode -ceq 'install'){
        & py -3 (Join-Path $release064g.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') preflight
    }else{
        & py -3 (Join-Path $release064g.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') status
    }
    if($LASTEXITCODE -ne 0){throw ('BGXAI064 pre-authorization CHECK FAILED '+$LASTEXITCODE)}
    $token=if($mode -ceq 'install'){'INSTALL_BGXAI_064'}else{'ROLLBACK_BGXAI_064'}
    Write-Host 'EXPERIMENTAL 064: this action modifies live Lua via WeiDU, with external SHA-verified backup.'
    Write-Host 'Baldur and InfinityLoader MUST be closed. BCS and EPS will not be modified by candidate.'
    $confirmation=Read-Host ('Type '+$token+' exactly to authorize or ENTER to cancel')
    if($confirmation -cne $token){Write-Host 'BGXAI 064 CANCELLED. Live game unchanged.';return}
    & py -3 (Join-Path $release064g.localPath 'BGXAI64_INSTALL_SOURCE_ONLY.py') $mode '--yes' '--confirm' $token
    if($LASTEXITCODE -ne 0){throw ('BGXAI064 '+$mode+' STOP code '+$LASTEXITCODE+'; do NOT retry blindly')}
    Write-Host ('BGXAI064 '+$mode+' completed; check guarded read-only STATUS menu 75.')
}
function Verify066Source {
    $spec=$release066
    $checked=VerifiedManifest $spec
    foreach($name in $spec.names){
        $dest=Join-Path $spec.localPath $name
        AssertNotReparse $dest
        if((HashFile $dest) -cne $checked[$name].sha){throw ('BGXAI066 source SHA mismatch: '+$name)}
    }
}
function Verify066SGuardedSource {
    $spec=$release066s
    $items=VerifiedManifest $spec
    foreach($name in $spec.names){
        $file=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
        AssertNotReparse $file
        if((HashFile $file) -cne $items[$name].sha){throw ('BGXAI066S source SHA mismatch: '+$name)}
    }
}
function Test066SReadOnly {
    SyncRelease $release066s
    Verify066SGuardedSource
    Write-Host 'BGXAI 066S real EET IDS + BCS preflight: READ ONLY, no WeiDU installation.'
    & py -3 (Join-Path $release066s.localPath 'BGXAI66S_INSTALL.py') preflight
    if($LASTEXITCODE -ne 0){throw ('BGXAI066S REAL EET IDS preflight STOP '+$LASTEXITCODE)}
    Write-Host 'BGXAI066S PRECHECK PASS. Existing 064 remains installed.'
}
function Status066SReadOnly {
    SyncRelease $release066s
    Verify066SGuardedSource
    & py -3 (Join-Path $release066s.localPath 'BGXAI66S_INSTALL.py') status
    if($LASTEXITCODE -ne 0){throw ('BGXAI066S status STOP '+$LASTEXITCODE)}
}
function Run066SGuarded([string]$mode) {
    if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI066S unsupported mode'}
    SyncRelease $release066s
    Verify066SGuardedSource
    $token=if($mode -ceq 'install'){'INSTALL_BGXAI_066S'}else{'ROLLBACK_BGXAI_066S'}
    Write-Host 'BGXAI066S EXPERIMENTAL: two exact SHA-pinned game scripts via WeiDU, external verified backup and strict 064 baseline.'
    Write-Host 'CLOSE BALDUR + INFINITYLOADER before continuing. No automatic retry on failure.'
    $confirmation=Read-Host ('Type '+$token+' exactly to authorize, or ENTER to cancel')
    if($confirmation -cne $token){Write-Host 'BGXAI066S CANCELLED. Game unchanged.';return}
    & py -3 (Join-Path $release066s.localPath 'BGXAI66S_INSTALL.py') $mode '--yes' '--confirm' $token
    if($LASTEXITCODE -ne 0){throw ('BGXAI066S '+$mode+' STOP '+$LASTEXITCODE+'. DO NOT AUTO-RETRY')}
    Write-Host 'BGXAI066S action completed. Verify via menu 85.'
}

function Verify067GuardedSource {
    $spec=$release067
    $items=VerifiedManifest $spec
    foreach($name in $spec.names){
        $file=Join-Path $spec.localPath ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))
        AssertNotReparse $file
        if((HashFile $file) -cne $items[$name].sha){throw ('BGXAI067 source SHA mismatch: '+$name)}
    }
}
function Test067ReadOnly {
    SyncRelease $release067
    Verify067GuardedSource
    Write-Host 'BGXAI 067 installed 066S baseline + real EET IDS prehit guard preflight: READ ONLY.'
    & py -3 (Join-Path $release067.localPath 'BGXAI67_INSTALL.py') preflight
    if($LASTEXITCODE -ne 0){throw ('BGXAI067 REAL EET preflight STOP '+$LASTEXITCODE)}
    Write-Host 'BGXAI067 PRECHECK PASS. Existing 066S remains installed.'
}
function Status067ReadOnly {
    SyncRelease $release067
    Verify067GuardedSource
    & py -3 (Join-Path $release067.localPath 'BGXAI67_INSTALL.py') status
    if($LASTEXITCODE -ne 0){throw ('BGXAI067 status STOP '+$LASTEXITCODE)}
}
function Run067Guarded([string]$mode) {
    if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI067 unsupported mode'}
    SyncRelease $release067
    Verify067GuardedSource
    $token=if($mode -ceq 'install'){'INSTALL_BGXAI_067'}else{'ROLLBACK_BGXAI_067'}
    Write-Host 'BGXAI067 EXPERIMENTAL: SHA-pinned Lua + BCS via WeiDU, external verified backup and exact 066S baseline.'
    Write-Host 'CLOSE BALDUR + INFINITYLOADER. No retry after a failure.'
    $confirmation=Read-Host ('Type '+$token+' exactly to authorize, or ENTER to cancel')
    if($confirmation -cne $token){Write-Host 'BGXAI067 CANCELLED. Game unchanged.';return}
    & py -3 (Join-Path $release067.localPath 'BGXAI67_INSTALL.py') $mode '--yes' '--confirm' $token
    if($LASTEXITCODE -ne 0){throw ('BGXAI067 '+$mode+' STOP '+$LASTEXITCODE+'. DO NOT AUTO-RETRY')}
    Write-Host 'BGXAI067 action completed. Read-only status via menu 90.'
}

function Test066GuardedReadOnly {
    $parsedTokens=$null
    $parseErrors=$null
    [System.Management.Automation.Language.Parser]::ParseFile($PSCommandPath,[ref]$parsedTokens,[ref]$parseErrors) | Out-Null
    if($parseErrors.Count -gt 0){throw ('BGXAI066 parser STOP: '+(($parseErrors | ForEach-Object {$_.Message}) -join '; '))}
    SyncRelease $release066
    Verify066Source
    Write-Host 'BGXAI 066 READ-ONLY preflight on installed 064. No game mutation.'
    & py -3 (Join-Path $release066.localPath 'BGXAI66_INSTALL.py') preflight
    if($LASTEXITCODE -ne 0){throw ('BGXAI066 preflight STOP '+$LASTEXITCODE)}
    Write-Host 'BGXAI066 preflight PASS. Game remains 064 until separately authorized installation.'
}
function Status066GuardedReadOnly {
    SyncRelease $release066
    Verify066Source
    & py -3 (Join-Path $release066.localPath 'BGXAI66_INSTALL.py') status
    if($LASTEXITCODE -ne 0){throw ('BGXAI066 status STOP '+$LASTEXITCODE)}
}
function Run066Guarded([string]$mode) {
    if($mode -cne 'install' -and $mode -cne 'rollback'){throw 'BGXAI066 illegal mode'}
    SyncRelease $release066
    Verify066Source
    if($mode -ceq 'install'){
        & py -3 (Join-Path $release066.localPath 'BGXAI66_INSTALL.py') preflight
    }else{
        & py -3 (Join-Path $release066.localPath 'BGXAI66_INSTALL.py') status
    }
    if($LASTEXITCODE -ne 0){throw ('BGXAI066 pre-authorization STOP '+$LASTEXITCODE)}
    $token=if($mode -ceq 'install'){'INSTALL_BGXAI_066'}else{'ROLLBACK_BGXAI_066'}
    Write-Host 'EXPERIMENTAL 066 changes only M_BX43.lua via WeiDU with SHA-verified external backup.'
    Write-Host 'Baldur, InfinityLoader and WeiDU must be closed. Exact 064 or 066 baseline is mandatory.'
    $confirmation=Read-Host ('Type '+$token+' exactly to authorize or ENTER to cancel')
    if($confirmation -cne $token){Write-Host 'BGXAI 066 CANCELLED. Game unchanged.';return}
    & py -3 (Join-Path $release066.localPath 'BGXAI66_INSTALL.py') $mode '--yes' '--confirm' $token
    if($LASTEXITCODE -ne 0){throw ('BGXAI066 '+$mode+' STOP '+$LASTEXITCODE+'; do NOT retry automatically')}
    Write-Host 'BGXAI066 action complete. Check status with option 80.'
}
function Test064ReadOnly {
    # Native PowerShell 5.1+ syntax check; this only reads its own file.
    $parsedTokens=$null
    $parseErrors=$null
    [System.Management.Automation.Language.Parser]::ParseFile($PSCommandPath,[ref]$parsedTokens,[ref]$parseErrors) | Out-Null
    if($parseErrors.Count -gt 0){throw ('BGXAI064 PowerShell parser STOP: '+(($parseErrors | ForEach-Object {$_.Message}) -join '; '))}
    $spec=$release064
    $list=VerifiedManifest $spec
    foreach($name in $spec.names){
        $dest=Join-Path $spec.localPath $name
        AssertNotReparse $dest
        if((HashFile $dest) -cne $list[$name].sha){throw ('BGXAI064 source SHA mismatch: '+$name)}
    }
    Write-Host 'BGXAI 064 - SHA-pinned read-only status of installed 061; no game files modified.'
    & py -3 (Join-Path $spec.localPath 'BGXAI64_PREFLIGHT_READONLY.py') '--game-root' $GameRoot
    if($LASTEXITCODE -ne 0){throw ('BGXAI064 read-only preflight STOP: '+$LASTEXITCODE)}
    Write-Host 'BGXAI 064 SOURCE ONLY: preflight PASSED. NOT INSTALLED. EEex runtime API NOT VERIFIED.'
}
function Status061ReadOnly {
    $log=Join-Path $GameRoot 'WeiDU.log'
    $bcs=Join-Path $GameRoot 'override\BDDEFAI.BCS'
    $lua=Join-Path $GameRoot 'override\M_BX43.lua'
    AssertNotReparse $log
    AssertNotReparse $bcs
    AssertNotReparse $lua
    if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'WeiDU.log missing'}
    $rows=@(Get-Content -LiteralPath $log -ErrorAction Stop | Where-Object {$_.TrimStart().StartsWith('~')})
    if($rows.Count -lt 1){throw 'WeiDU.log has no installed components'}
    $last=[string]$rows[-1]
    $is061=($last -match '(?i)BGX61[/\\]SETUP-BGX61[.]TP2~')
    $is060=($last -match '(?i)BGX60[/\\]SETUP-BGX60[.]TP2~')
    $bhash=HashFile $bcs
    $lhash=HashFile $lua
    Write-Host ('Last WeiDU: '+$last)
    Write-Host ('061 is LAST: '+$is061)
    Write-Host ('060 is LAST: '+$is060)
    if($is061){
        $sourceBCS=Join-Path $GameRoot 'BGX61\staged\BDDEFAI.BCS'
        $sourceLua=Join-Path $GameRoot 'BGX61\staged\M_BX43.lua'
        AssertNotReparse $sourceBCS
        AssertNotReparse $sourceLua
        Write-Host ('061 BCS staged SHA matches live: '+((HashFile $sourceBCS) -ceq $bhash -and $bhash.Length -eq 64))
        Write-Host ('061 Lua staged SHA matches live: '+((HashFile $sourceLua) -ceq $lhash -and $lhash.Length -eq 64))
    } elseif($is060) {
        Write-Host ('060 BCS SHA correct: '+($bhash -ceq '038b41c529fb45bb75528722577beef7b474e1ce55e280dc5fca4d6ed9e72841'))
        Write-Host ('060 Lua SHA correct: '+($lhash -ceq '35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab'))
    } else {Write-Host 'STOP: current last WeiDU is not BGX60/BGX61; no install or rollback until reviewed.'}
    Write-Host ('Live BCS SHA: '+$bhash)
    Write-Host ('Live Lua SHA: '+$lhash)
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
Write-Host ' 65 - Download/verify BGXAI 061 SOURCE ONLY (NO INSTALL)'
Write-Host ' 66 - BGXAI 061 REAL WeiDU preflight (READ ONLY, no game changes)'
Write-Host ' 67 - EXPERIMENTAL install BGXAI 061 (separate approval + backup)'
Write-Host ' 68 - BGXAI 061/060 install STATUS (READ ONLY)'
Write-Host ' 69 - Roll back BGXAI 061 to 060 (separate approval + backup)'
Write-Host ' 70 - Download/verify BGXAI 064 SOURCE ONLY (NO INSTALL)'
Write-Host ' 71 - BGXAI 064 SHA-pinned PRECHECK (READ ONLY, NO INSTALL)'
Write-Host ' 72 - Download/verify BGXAI 064 GUARDED WEIDU SOURCES (NO INSTALL)'
Write-Host ' 73 - BGXAI 064 guarded WeiDU PRECHECK (NO INSTALL)'
Write-Host ' 74 - EXPERIMENTAL install BGXAI 064 (explicit confirmation + backup)'
Write-Host ' 75 - BGXAI 064/061 guarded STATUS (READ ONLY)'
Write-Host ' 76 - Roll back BGXAI 064 to 061 (explicit confirmation + backup)'
Write-Host ' 77 - Download/verify BGXAI 066 guarded sources (NO INSTALL)'
Write-Host ' 78 - BGXAI 066 real 064-baseline preflight (READ ONLY)'
Write-Host ' 79 - BLOCKED legacy 066 install (caster regression); use 066S'
Write-Host ' 80 - BGXAI 066/064 status (READ ONLY)'
Write-Host ' 81 - Roll back BGXAI 066 to 064 (explicit confirmation + backup)'
Write-Host ' 82 - BGXAI 066S caster+frontline download/verify sources (NO INSTALL)'
Write-Host ' 83 - BGXAI 066S real EET IDS / BCS preflight (READ ONLY)'
Write-Host ' 84 - EXPERIMENTAL install BGXAI 066S (explicit opt-in + backup)'
Write-Host ' 85 - BGXAI 066S/064 verified status (READ ONLY)'
Write-Host ' 86 - Roll back BGXAI 066S to 064 (explicit opt-in)'
Write-Host ' 87 - BGXAI 067 early guard download/verify (NO INSTALL)'
Write-Host ' 88 - BGXAI 067 installed 066S and real EET IDS preflight (READ ONLY)'
Write-Host ' 89 - EXPERIMENTAL install BGXAI 067 (explicit opt-in + backup)'
Write-Host ' 90 - BGXAI 067/066S guarded status (READ ONLY)'
Write-Host ' 91 - Roll back BGXAI 067 to 066S (explicit opt-in)'
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
      '65' {SyncRelease $release061;break}
      '66' {SyncRelease $release061;Test061ReadOnly;break}
      '67' {Run061Guarded 'install';break}
      '68' {Status061ReadOnly;break}
      '69' {Run061Guarded 'rollback';break}
      '70' {SyncRelease $release064;break}
      '71' {SyncRelease $release064;Test064ReadOnly;break}
      '72' {SyncRelease $release064g;break}
      '73' {Test064GuardedReadOnly;break}
      '74' {Run064Guarded 'install';break}
      '75' {Status064GuardedReadOnly;break}
      '76' {Run064Guarded 'rollback';break}
      '77' {SyncRelease $release066;break}
      '78' {Test066GuardedReadOnly;break}
      '79' {throw 'BGXAI 066 deprecated: frontline-only regression; use tested BGXAI066S 83/84 instead.'}
      '80' {Status066GuardedReadOnly;break}
      '81' {Run066Guarded 'rollback';break}
      '82' {SyncRelease $release066s;break}
      '83' {Test066SReadOnly;break}
      '84' {Run066SGuarded 'install';break}
      '85' {Status066SReadOnly;break}
      '86' {Run066SGuarded 'rollback';break}
      '87' {SyncRelease $release067;break}
      '88' {Test067ReadOnly;break}
      '89' {Run067Guarded 'install';break}
      '90' {Status067ReadOnly;break}
      '91' {Run067Guarded 'rollback';break}
      default {throw 'Unknown menu option, no game change.'}
    }
    exit 0
} catch {
    Write-Host ('BGXAI STOP: '+$_.Exception.Message) -ForegroundColor Red
    Write-Host 'Do not repeat failed installs automatically. Existing working AI left for review.'
    exit 1
}
