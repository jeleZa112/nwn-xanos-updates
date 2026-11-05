# BGXAI GitHub updater v0.6.26 verified squad compilation pilot. Separate branch; never touches NWN main.
param([string]$GameRoot=".")
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$GameRoot=(Resolve-Path -LiteralPath $GameRoot).Path
$cache=Join-Path $env:LOCALAPPDATA 'BGXAI_UPDATER'
New-Item -ItemType Directory -Path $cache -Force | Out-Null
$log=Join-Path $GameRoot 'BGXAI_UPDATE.log'
function Log([string]$message) {
    $line='['+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+'] '+$message
    Write-Host $line
    Add-Content -LiteralPath $log -Value $line -Encoding UTF8
}
function GetFile([string]$name,[string]$commit) {
    $h=@{'User-Agent'='BGXAI-EET-Updater';'Accept'='application/vnd.github+json';'Cache-Control'='no-cache'}
    $api='https://api.github.com/repos/jeleZa112/nwn-xanos-updates/contents/'
    $v=Invoke-RestMethod -Uri ($api+$name+'?ref='+$commit) -Headers $h -TimeoutSec 50 -UseBasicParsing
    if($v.encoding -ne 'base64' -or !$v.content) { throw ('Bad GitHub response: '+$name) }
    return ,([Convert]::FromBase64String(([string]$v.content -replace '\s','')))
}
function Hash([byte[]]$bytes) {
    $h=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($h.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}
    finally {$h.Dispose()}
}
function RepairUserScriptShadow([string]$pinnedCommit) {
    $auditFile='BGXAI/BGXAI_RESOURCE_AUDIT.ps1'
    if($script:ActiveVersion -eq '0.6.27-role-profile-install-pilot') {$auditFile='BGXAI/BGXAI_RESOURCE_AUDIT_627.ps1'}
    [byte[]]$auditBytes=GetFile $auditFile $pinnedCommit
    $auditText=[Text.Encoding]::UTF8.GetString($auditBytes)
    if($auditBytes.Length -lt 3000 -or !$auditText.Contains("AUDIT SUCCESS") -or !$auditText.Contains("SyncOwnedFile")) {
        throw 'Unexpected resource audit script; refusing to execute'
    }
    $auditPath=Join-Path $cache 'BGXAI_RESOURCE_AUDIT.latest.ps1'
    [IO.File]::WriteAllBytes($auditPath,$auditBytes)
    Log 'Checking user Documents script shadows (backup before any update).'
    & $auditPath -GameRoot $GameRoot
    if(!$?) {throw 'BGXAI shadow resource audit failed'}
    Log 'User script shadow audit completed. See BGXAI_RESOURCE_AUDIT.txt'
}
# BGXAI_ONE_FILE_SELECTOR_018
# This is REMOTE code inside the existing BGXAI_SYNC.ps1. The user still runs ONLY
# the original game-root BGXAI_UPDATE.cmd; no new launcher or manually installed ZIP.
Write-Host ''
Write-Host '============================================================='
Write-Host ' BGXAI ONE UPDATE FILE - EET / WeiDU 251'
Write-Host '============================================================='
Write-Host ' 1 = Install/update NEW parallel BGXUN1 script (recommended)'
Write-Host '     Existing Advanced AI / BGXGRP / BGXTANK remain unchanged.'
Write-Host ' 2 = Update EXISTING BGXAI 0.6.x role pilots (legacy behavior)'
Write-Host ' 3 = Exit without changing game files'
Write-Host ''
$bgxChoice=Read-Host 'Choose [1]'
if([string]::IsNullOrWhiteSpace($bgxChoice)) {$bgxChoice='1'}
if($bgxChoice -eq '3') {Write-Host 'No game files changed.'; exit 0}
if($bgxChoice -ne '1' -and $bgxChoice -ne '2') {
    Log ('ERROR: Invalid menu selection: '+$bgxChoice)
    exit 1
}
if($bgxChoice -eq '1') {
    try {
        if(!(Test-Path -LiteralPath (Join-Path $GameRoot 'chitin.key'))) {throw 'chitin.key not found'}
        if(Get-Process -Name Baldur,BaldursGate,InfinityLoader -ErrorAction SilentlyContinue) {
            throw 'Game / InfinityLoader is running: close both before changing game scripts'
        }
        $bgxCommit=[IO.File]::ReadAllText((Join-Path $cache 'head.txt')).Trim()
        if($bgxCommit -notmatch '^[a-fA-F0-9]{40}$') {throw 'Updater GitHub commit marker missing'}
        [byte[]]$bgxManifestBytes=GetFile 'BGXAI/pilots/BGXUNI_010/parallel/latest.json' $bgxCommit
        $bgxManifest=[Text.Encoding]::UTF8.GetString($bgxManifestBytes) | ConvertFrom-Json
        if($bgxManifest.channel -ne 'BGXUNI-parallel' -or
           $bgxManifest.version -ne '0.1.8-safe-resume-fire') {throw 'Invalid parallel channel manifest'}
        $bgxHelperRemote='BGXAI/pilots/BGXUNI_010/parallel/BGXUNI_AUTOINSTALL.ps1'
        if([string]$bgxManifest.installer.path -ne $bgxHelperRemote) {throw 'Unexpected helper path'}
        [byte[]]$bgxHelper=GetFile $bgxHelperRemote $bgxCommit
        $bgxHelperText=[Text.Encoding]::UTF8.GetString($bgxHelper)
        if($bgxHelper.Length -ne [int]$bgxManifest.installer.size -or
           (Hash $bgxHelper) -ne [string]$bgxManifest.installer.sha256 -or
           !$bgxHelperText.Contains('BGXUNI_INTEGRATED_INSTALLER_V018')) {
            throw 'BGXUNI helper content verification failed'
        }
        $bgxHelperPath=Join-Path $cache 'BGXUNI_AUTOINSTALL.current.ps1'
        [IO.File]::WriteAllBytes($bgxHelperPath,$bgxHelper)
        Log ('BGXUNI: pinned helper SHA256 checked; commit '+$bgxCommit.Substring(0,12))
        & $bgxHelperPath -GameRoot $GameRoot -Commit $bgxCommit
        if(!$? -or $LASTEXITCODE -ne 0) {throw 'BGXUNI parallel installer failed; see BGXUNI_UPDATE.log'}
        Log 'SUCCESS: parallel BGXUN1 installation verified. Other AI scripts unchanged.'
        exit 0
    } catch {
        Log ('FAILED BGXUNI: '+$_.Exception.Message)
        exit 1
    }
}
# Choice 2 falls through unchanged to the historic BGXAI 0.6.x try/catch below.

try {
    if(!(Test-Path -LiteralPath (Join-Path $GameRoot 'chitin.key'))) { throw 'Missing chitin.key. Run in game root.' }
    if(Get-Process -Name Baldur,BaldursGate,baldur -ErrorAction SilentlyContinue) { throw 'Close Baldurs Gate before updating.' }
    $commit=[IO.File]::ReadAllText((Join-Path $cache 'head.txt')).Trim()
    if($commit -notmatch '^[a-fA-F0-9]{40}$') {throw 'Invalid commit marker'}
    $manifest=[Text.Encoding]::UTF8.GetString((GetFile 'BGXAI/latest.json' $commit)) | ConvertFrom-Json
    if($manifest.channel -ne 'pilot') { throw 'Unknown channel' }
    $version=[string]$manifest.version
    $verifiedTag=''
    if($version -eq '0.6.21-verified-compile-pilot') {$verifiedTag='621'}
    if($version -eq '0.6.22-intercept-melee-pilot') {$verifiedTag='622'}
    if($version -eq '0.6.23-formation-rescue-pilot') {$verifiedTag='623'}
    if($version -eq '0.6.24-support-survival-pilot') {$verifiedTag='624'}
    if($version -eq '0.6.25-healthy-engage-pilot') {$verifiedTag='625'}
    if($version -eq '0.6.25-no-premature-formation-pilot') {$verifiedTag='625'}
    if($version -eq '0.6.26-squad-two-tank-pilot') {$verifiedTag='626'}
    if($version -eq '0.6.27-role-profile-install-pilot') {$verifiedTag='626'}
    $script:ActiveVersion=$version
    $ownedNames=@('BGXGRP','BGXTANK')
    if($version -eq '0.6.27-role-profile-install-pilot') {$ownedNames+=@('BGXRANG','BGXSCOUT','BGXCAST','BGXHEAL')}
    $ownedMarkers=@{BGXGRP='BGXVER26';BGXTANK='BGXVER26';BGXRANG='BGXRV02';BGXSCOUT='BGXSV02';BGXCAST='BGXCV02';BGXHEAL='BGXHV02'}
    if($version -eq '0.6.23-formation-rescue-pilot') {$verifiedTag='623'}
    $expectedCompiledMarker=''
    if($verifiedTag) {$expectedCompiledMarker='BGXVER'+$verifiedTag.Substring(1)}

    if($version -notmatch '^[A-Za-z0-9._-]+$') {throw 'Invalid version'}
    $rel=[string]$manifest.package_path
    if($rel -notmatch '^BGXAI/releases/[A-Za-z0-9._-]+\.zip\.b64$') {throw 'Invalid package path'}
    $marker=Join-Path $GameRoot 'BGXAI\bgxai-updater-version.txt'
    Log ('Target BGXAI '+$version)
    $alreadyCurrent=(Test-Path $marker) -and ([IO.File]::ReadAllText($marker).Trim() -eq $version)
    if($alreadyCurrent -and $verifiedTag) {
        foreach($name in $ownedNames) {
            $activeFile=Join-Path $GameRoot ('scripts\'+$name+'.BS')
            if(!(Test-Path -LiteralPath $activeFile)) {
                $alreadyCurrent=$false
                break
            }
            $activeBytes=[IO.File]::ReadAllBytes($activeFile)
            if(!([Text.Encoding]::ASCII.GetString($activeBytes)).Contains([string]$ownedMarkers[$name])) {
                $alreadyCurrent=$false
                break
            }
        }
        if(!$alreadyCurrent) {Log ('Version marker says current, but an active script version marker is missing; rebuilding.')}
    }
    if($alreadyCurrent) {
        Log 'Already current; combat scripts untouched. Auditing higher-priority user script folders.'
        RepairUserScriptShadow $commit
        exit 0
    }
    $b64=[Text.Encoding]::ASCII.GetString((GetFile $rel $commit)).Trim()
    if($b64 -notmatch '^[A-Za-z0-9+/=]+$') {throw 'Invalid base64 package'}
    [byte[]]$bytes=[Convert]::FromBase64String($b64)
    if($bytes.Length -ne [int]$manifest.package_size) {throw 'Size mismatch'}
    if((Hash $bytes) -ne [string]$manifest.package_sha256) {throw 'SHA256 mismatch'}
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
    $stage=Join-Path $cache ('stage_'+$stamp)
    New-Item -ItemType Directory -Path $stage -Force | Out-Null
    $allowed=@('BGXAI/BGXAI.TP2','BGXAI/AI_BAF/BGXATK.BAF','BGXAI/AI_BAF/BGXSCUT.BAF','BGXAI/AI_BAF/BGXHEAL.BAF','BGXAI/AI_BAF/BGXWARD.BAF','BGXAI/AI_BAF/BGXHYBR.BAF','BGXAI/AI_BAF/BGXMANU.BAF','BGXAI/AI_BAF/BGXSAFE.BAF','BGXAI/AI_BAF/BGXDBG.BAF','BGXAI/AI_BAF/BGXGRP.BAF','BGXAI/AI_BAF/BGXTANK.BAF')
    Add-Type -AssemblyName System.IO.Compression
    $mem=New-Object System.IO.MemoryStream
    $mem.Write($bytes,0,$bytes.Length)
    $mem.Position=0
    $zip=[System.IO.Compression.ZipArchive]::new($mem,[System.IO.Compression.ZipArchiveMode]::Read)
    $seen=@()
    try {
        foreach($e in $zip.Entries) {
            $p=$e.FullName.Replace('\','/')
            if($p -eq 'README_RU.txt') {continue}
            if(($allowed -notcontains $p) -or ($seen -contains $p)) {throw ('Unexpected archive file: '+$p)}
            $seen+= $p
            $out=Join-Path $stage ($p.Replace('/',[IO.Path]::DirectorySeparatorChar))
            New-Item -ItemType Directory -Path (Split-Path -Parent $out) -Force | Out-Null
            $stream=$e.Open()
            $w=[IO.File]::Create($out)
            try {$stream.CopyTo($w)} finally {$stream.Dispose();$w.Dispose()}
        }
    } finally {$zip.Dispose();$mem.Dispose()}
    if($seen.Count -ne $allowed.Count) {throw 'Incomplete package'}
    # v0.6.17 hotfix overlay: retrieve individual BAF source files at the pinned GitHub commit.
    if($version -eq '0.6.17-tank-pursuit-recover-pilot' -or $version -eq '0.6.18-formation-cohesion-pilot' -or $version -eq '0.6.19-emergency-guard-pilot' -or $version -eq '0.6.20-liveness-first-pilot') {
        $hotfix='0.6.17'
        if($version -eq '0.6.18-formation-cohesion-pilot') {$hotfix='0.6.18'}
        if($version -eq '0.6.19-emergency-guard-pilot') {$hotfix='0.6.19'}
        if($version -eq '0.6.20-liveness-first-pilot') {$hotfix='0.6.20'}
        $patches=@{
            'BGXAI/AI_BAF/BGXTANK.BAF'=('BGXAI/hotfix/BGXTANK_'+$hotfix+'.BAF')
            'BGXAI/AI_BAF/BGXGRP.BAF'=('BGXAI/hotfix/BGXGRP_'+$hotfix+'.BAF')
        }
        if($version -eq '0.6.20-liveness-first-pilot') {
            $patches['BGXAI/BGXAI.TP2']='BGXAI/hotfix/BGXAI_0.6.20.TP2'
        }
        foreach($target in $patches.Keys) {
            [byte[]]$patch=GetFile $patches[$target] $commit
            $patchText=[Text.Encoding]::UTF8.GetString($patch)
            if($patch.Length -lt 300 -or !$patchText.Contains($hotfix)) {throw ('Invalid hotfix script: '+$target)}
            $dst=Join-Path $stage ($target.Replace('/',[IO.Path]::DirectorySeparatorChar))
            [IO.File]::WriteAllBytes($dst,$patch)
            Log ('Staged verified hotfix BAF: '+$target)
        }
    }


    # Compile under fresh resource names; select exact source for each pilot.
    $extraFiles=@()
    if($verifiedTag) {
        $extraPatches=@{'BGXAI/BGXAI.TP2'=('BGXAI/hotfix/BGXAI_0.6.'+$verifiedTag.Substring(1)+'.TP2')}
        $extraPatches[('BGXAI/AI_BAF/BGG'+$verifiedTag+'.BAF')]=('BGXAI/hotfix/BGG'+$verifiedTag+'.BAF')
        $extraPatches[('BGXAI/AI_BAF/BGT'+$verifiedTag+'.BAF')]=('BGXAI/hotfix/BGT'+$verifiedTag+'.BAF')
        if($version -eq '0.6.27-role-profile-install-pilot') {
            $extraPatches['BGXAI/BGXAI.TP2']='BGXAI/hotfix/BGXAI_0.6.27.TP2'
            $extraPatches['BGXAI/AI_BAF/BGR002.BAF']='BGXAI/prototypes/BGR002.BAF'
            $extraPatches['BGXAI/AI_BAF/BGS002.BAF']='BGXAI/prototypes/BGS002.BAF'
            $extraPatches['BGXAI/AI_BAF/BGC002.BAF']='BGXAI/prototypes/BGC002.BAF'
            $extraPatches['BGXAI/AI_BAF/BGH002.BAF']='BGXAI/prototypes/BGH002.BAF'
        }
        foreach($sourceTarget in $extraPatches.Keys) {
            [byte[]]$extraBytes=GetFile $extraPatches[$sourceTarget] $commit
            $extraText=[Text.Encoding]::UTF8.GetString($extraBytes)
            if($extraBytes.Length -lt 500) {throw ('Too short: '+$sourceTarget)}
            if($sourceTarget.EndsWith('.BAF')) {
                $expected=$expectedCompiledMarker
                if($version -eq '0.6.27-role-profile-install-pilot') {
                    switch -Exact ($sourceTarget) {
                        'BGXAI/AI_BAF/BGR002.BAF' {$expected='BGXRV02'}
                        'BGXAI/AI_BAF/BGS002.BAF' {$expected='BGXSV02'}
                        'BGXAI/AI_BAF/BGC002.BAF' {$expected='BGXCV02'}
                        'BGXAI/AI_BAF/BGH002.BAF' {$expected='BGXHV02'}
                    }
                }
                if(!$extraText.Contains($expected)){throw ('Source lacks version marker '+$expected+': '+$sourceTarget)}
            }
            if($sourceTarget.EndsWith('.TP2')) {
                $tp2Marker='BGXAI v0.6.'+$verifiedTag.Substring(1)+' VERIFIED COMPILE'
                if($version -eq '0.6.27-role-profile-install-pilot'){$tp2Marker='BGXAI v0.6.27 ROLE PROFILES'}
                if(!$extraText.Contains($tp2Marker)){throw 'Wrong TP2 version'}
            }
            $extraDest=Join-Path $stage ($sourceTarget.Replace('/',[IO.Path]::DirectorySeparatorChar))
            New-Item -ItemType Directory -Path (Split-Path -Parent $extraDest) -Force | Out-Null
            [IO.File]::WriteAllBytes($extraDest,$extraBytes)
            Log ('Staged unique compilation source '+$sourceTarget)
        }
        $extraFiles=@(('BGXAI/AI_BAF/BGG'+$verifiedTag+'.BAF'),('BGXAI/AI_BAF/BGT'+$verifiedTag+'.BAF'))
        if($version -eq '0.6.27-role-profile-install-pilot') {$extraFiles+=@('BGXAI/AI_BAF/BGR002.BAF','BGXAI/AI_BAF/BGS002.BAF','BGXAI/AI_BAF/BGC002.BAF','BGXAI/AI_BAF/BGH002.BAF')}
    }

    $setup=Join-Path $GameRoot 'setup-BGXAI.exe'
    if(!(Test-Path $setup)) {
        $source=Join-Path $GameRoot 'setup-stratagems.exe'
        if(!(Test-Path $source)) {throw 'WeiDU exe missing'}
        Copy-Item -LiteralPath $source -Destination $setup -Force
    }
    $mod=Join-Path $GameRoot 'BGXAI'
    $backup=Join-Path $cache ('backup_'+$stamp)

    $liveBackupDir=$null
    if($verifiedTag) {
        $liveBackupDir=Join-Path $cache ('active_pre_weidu_'+$verifiedTag+'_'+$stamp)
        New-Item -ItemType Directory -Path $liveBackupDir -Force | Out-Null
        foreach($scriptName in $ownedNames) {
            foreach($pair in @(
                @{folder='override';ext='BCS'},
                @{folder='scripts';ext='BS'}
            )) {
                $original=Join-Path $GameRoot ($pair.folder+'\'+$scriptName+'.'+$pair.ext)
                if(Test-Path -LiteralPath $original) {
                    $safeCopy=Join-Path $liveBackupDir ($pair.folder+'_'+$scriptName+'.'+$pair.ext)
                    Copy-Item -LiteralPath $original -Destination $safeCopy -Force
                }
            }
        }
        Log ('BACKUP active game scripts before WeiDU: '+$liveBackupDir)
    }
    $hadOld=Test-Path $mod
    if($hadOld) {Copy-Item -LiteralPath $mod -Destination $backup -Recurse -Force}
    $weiduLog=Join-Path $GameRoot 'WeiDU.log'
    $installed=$false
    if(Test-Path $weiduLog) {
        $installed=Select-String -LiteralPath $weiduLog -Pattern 'BGXAI[\\/]BGXAI\.TP2' -Quiet
        Copy-Item -LiteralPath $weiduLog -Destination (Join-Path $cache ('WeiDU_'+$stamp+'.log')) -Force
    }
    foreach($p in ($allowed + $extraFiles)) {
        $src=Join-Path $stage ($p.Replace('/',[IO.Path]::DirectorySeparatorChar))
        $dst=Join-Path $GameRoot ($p.Replace('/',[IO.Path]::DirectorySeparatorChar))
        New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
    Log ('Package SHA256 verified; backup='+$backup)
    Push-Location $GameRoot
    try {
        if($installed) {& $setup '--noautoupdate' '--no-exit-pause' '--reinstall' '0'}
        else {& $setup '--noautoupdate' '--no-exit-pause' '--language' '0' '--force-install' '0'}
        $code=$LASTEXITCODE
    } finally {Pop-Location}
    if($code -ne 0) {
        Log ('WeiDU FAILED code='+$code+'; see setup-BGXAI.DEBUG')

        if($verifiedTag -and $liveBackupDir) {
            foreach($entry in @(Get-ChildItem -LiteralPath $liveBackupDir -File -ErrorAction SilentlyContinue)) {
                if($entry.Name -match '^(override|scripts)_(BGXGRP|BGXTANK|BGXRANG|BGXSCOUT|BGXCAST|BGXHEAL)\.(BCS|BS)$') {
                    $restoreDest=Join-Path $GameRoot ($Matches[1]+'\'+$Matches[2]+'.'+$Matches[3])
                    Copy-Item -LiteralPath $entry.FullName -Destination $restoreDest -Force -ErrorAction Continue
                }
            }
            Log 'RESTORED pre-WeiDU active scripts following compile failure.'
        }

        if($hadOld) {
            Remove-Item -LiteralPath $mod -Recurse -Force -ErrorAction SilentlyContinue
            Copy-Item -LiteralPath $backup -Destination $mod -Recurse -Force
            Log 'Old BGXAI sources restored; game-level WeiDU rollback is NOT guaranteed.'
        }
        exit 1
    }

    # Verify new compiled script provenance before activating old alias names.
    if($verifiedTag) {
        $verifyHelperRemote='BGXAI/BGXAI_VERIFY_ACTIVATE_'+$verifiedTag+'.ps1'
        $helperSuccess='BGXAI v0.6.'+$verifiedTag.Substring(1)+' VERIFIED ACTIVATION SUCCESS'
        if($version -eq '0.6.27-role-profile-install-pilot') {
            $verifyHelperRemote='BGXAI/BGXAI_VERIFY_ACTIVATE_627.ps1'
            $helperSuccess='BGXAI v0.6.27 VERIFIED ACTIVATION SUCCESS'
        }
        [byte[]]$helper=GetFile $verifyHelperRemote $commit
        $helperText=[Text.Encoding]::UTF8.GetString($helper)
        if($helper.Length -lt 3000 -or !$helperText.Contains($helperSuccess)) {
            throw 'Invalid compiler verification helper'
        }
        $helperPath=Join-Path $cache ('BGXAI_VERIFY_ACTIVATE_'+$verifiedTag+'.latest.ps1')
        [IO.File]::WriteAllBytes($helperPath,$helper)
        Log ('Proving freshly compiled '+$expectedCompiledMarker+' BCS resources before activation.')
        & $helperPath -GameRoot $GameRoot -CacheRoot $cache
        if(!$?) {throw 'Compiler verification/activation failed'}
        foreach($scriptName in $ownedNames) {
            $compiledBytes=[IO.File]::ReadAllBytes((Join-Path $GameRoot ('scripts\'+$scriptName+'.BS')))
            if(!([Text.Encoding]::ASCII.GetString($compiledBytes)).Contains([string]$ownedMarkers[$scriptName])) {
                throw ('ACTIVE VERSION MARKER MISSING '+$scriptName+' '+$ownedMarkers[$scriptName])
            }
            Log ('VERIFIED ACTIVE '+$ownedMarkers[$scriptName]+' '+$scriptName)
        }
    }
    # Verify *installed* compiled scripts. The BAF source alone is not proof of game installation.
    if($version -eq '0.6.20-liveness-first-pilot') {
        foreach($name in @('BGXGRP','BGXTANK')) {
            $bcs=Join-Path $GameRoot ('override\' + $name + '.BCS')
            $bs=Join-Path $GameRoot ('scripts\' + $name + '.BS')
            if(!(Test-Path -LiteralPath $bcs) -or !(Test-Path -LiteralPath $bs)) {
                throw ('Missing compiled script: '+$name)
            }
            [byte[]]$compiled=[IO.File]::ReadAllBytes($bcs)
            [byte[]]$assigned=[IO.File]::ReadAllBytes($bs)
            if($compiled.Length -lt 100 -or $assigned.Length -lt 100 -or (Hash $compiled) -ne (Hash $assigned)) {
                throw ('Compiled script mismatch: '+$name)
            }
            Log ('VERIFY compiled '+$name+': override BCS == scripts BS')
        }
    }
    RepairUserScriptShadow $commit
    [IO.File]::WriteAllText($marker,$version,[Text.Encoding]::ASCII)
    Log ('SUCCESS: BGXAI '+$version+' installed; selectable role scripts: '+($ownedNames -join ', '))
    Log ('Diagnostic: '+$version+'; EEex telemetry unchanged. Test only after verified binary/version markers.')
    exit 0
} catch {
    if($verifiedTag -and $liveBackupDir -and (Test-Path -LiteralPath $liveBackupDir)) {
        foreach($entry in @(Get-ChildItem -LiteralPath $liveBackupDir -File -ErrorAction SilentlyContinue)) {
            if($entry.Name -match '^(override|scripts)_(BGXGRP|BGXTANK|BGXRANG|BGXSCOUT|BGXCAST|BGXHEAL)\.(BCS|BS)$') {
                $restoreDest=Join-Path $GameRoot ($Matches[1]+'\'+$Matches[2]+'.'+$Matches[3])
                Copy-Item -LiteralPath $entry.FullName -Destination $restoreDest -Force -ErrorAction Continue
            }
        }
        Log 'RESTORED pre-WeiDU active scripts following activation failure; WeiDU metadata rollback not guaranteed.'
    }
    Log ('FAILED: '+$_.Exception.Message)
    exit 1
}
