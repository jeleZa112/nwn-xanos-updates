# BGXAI GitHub updater v0.6.16 pilot. Separate branch, never touches NWN main.
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
    [byte[]]$auditBytes=GetFile 'BGXAI/BGXAI_RESOURCE_AUDIT.ps1' $pinnedCommit
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
try {
    if(!(Test-Path -LiteralPath (Join-Path $GameRoot 'chitin.key'))) { throw 'Missing chitin.key. Run in game root.' }
    if(Get-Process -Name Baldur,BaldursGate,baldur -ErrorAction SilentlyContinue) { throw 'Close Baldurs Gate before updating.' }
    $commit=[IO.File]::ReadAllText((Join-Path $cache 'head.txt')).Trim()
    if($commit -notmatch '^[a-fA-F0-9]{40}$') {throw 'Invalid commit marker'}
    $manifest=[Text.Encoding]::UTF8.GetString((GetFile 'BGXAI/latest.json' $commit)) | ConvertFrom-Json
    if($manifest.channel -ne 'pilot') { throw 'Unknown channel' }
    $version=[string]$manifest.version
    if($version -notmatch '^[A-Za-z0-9._-]+$') {throw 'Invalid version'}
    $rel=[string]$manifest.package_path
    if($rel -notmatch '^BGXAI/releases/[A-Za-z0-9._-]+\.zip\.b64$') {throw 'Invalid package path'}
    $marker=Join-Path $GameRoot 'BGXAI\bgxai-updater-version.txt'
    Log ('Target BGXAI '+$version)
    if((Test-Path $marker) -and ([IO.File]::ReadAllText($marker).Trim() -eq $version)) {
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


    # v0.6.21: compile under unique resrefs to prevent old BCS reuse.
    $extraFiles=@()
    if($version -eq '0.6.21-verified-compile-pilot') {
        $extraPatches=@{
            'BGXAI/BGXAI.TP2'='BGXAI/hotfix/BGXAI_0.6.21.TP2'
            'BGXAI/AI_BAF/BGG621.BAF'='BGXAI/hotfix/BGG621.BAF'
            'BGXAI/AI_BAF/BGT621.BAF'='BGXAI/hotfix/BGT621.BAF'
        }
        foreach($targetName in $extraPatches.Keys) {
            [byte[]]$extraBytes=GetFile $extraPatches[$targetName] $commit
            $extraText=[Text.Encoding]::UTF8.GetString($extraBytes)
            if($extraBytes.Length -lt 500) {throw ('Too short: '+$targetName)}
            if($targetName.EndsWith('.BAF') -and !$extraText.Contains('BGXVER21')) {
                throw ('Source lacks version marker: '+$targetName)
            }
            if($targetName.EndsWith('.TP2') -and !$extraText.Contains('BGXAI v0.6.21 VERIFIED COMPILE')) {
                throw 'Wrong v0.6.21 TP2'
            }
            $extraDest=Join-Path $stage ($targetName.Replace('/',[IO.Path]::DirectorySeparatorChar))
            New-Item -ItemType Directory -Path (Split-Path -Parent $extraDest) -Force | Out-Null
            [IO.File]::WriteAllBytes($extraDest,$extraBytes)
            Log ('Staged unique compilation source '+$targetName)
        }
        $extraFiles=@('BGXAI/AI_BAF/BGG621.BAF','BGXAI/AI_BAF/BGT621.BAF')
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
    if($version -eq '0.6.21-verified-compile-pilot') {
        $liveBackupDir=Join-Path $cache ('active_pre_weidu_621_'+$stamp)
        New-Item -ItemType Directory -Path $liveBackupDir -Force | Out-Null
        foreach($scriptName in @('BGXGRP','BGXTANK')) {
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

        if($version -eq '0.6.21-verified-compile-pilot' -and $liveBackupDir) {
            foreach($entry in @(Get-ChildItem -LiteralPath $liveBackupDir -File -ErrorAction SilentlyContinue)) {
                if($entry.Name -match '^(override|scripts)_(BGXGRP|BGXTANK)\.(BCS|BS)$') {
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

    # New v0.6.21 activation requires proof from two NEW compiler outputs.
    # Never report SUCCESS for the old BGXGRP/BGXTANK aliases unless proven.
    if($version -eq '0.6.21-verified-compile-pilot') {
        [byte[]]$helper=GetFile 'BGXAI/BGXAI_VERIFY_ACTIVATE_621.ps1' $commit
        $helperText=[Text.Encoding]::UTF8.GetString($helper)
        if($helper.Length -lt 3000 -or !$helperText.Contains('BGXAI v0.6.21 VERIFIED ACTIVATION SUCCESS')) {
            throw 'Invalid compiler verification helper'
        }
        $helperPath=Join-Path $cache 'BGXAI_VERIFY_ACTIVATE_621.latest.ps1'
        [IO.File]::WriteAllBytes($helperPath,$helper)
        Log 'Proving freshly compiled BGXVER21 BCS resources before activation.'
        & $helperPath -GameRoot $GameRoot -CacheRoot $cache
        if(!$?) {throw 'Compiler verification/activation failed'}
        foreach($scriptName in @('BGXGRP','BGXTANK')) {
            $compiledBytes=[IO.File]::ReadAllBytes((Join-Path $GameRoot ('scripts\'+$scriptName+'.BS')))
            if(!([Text.Encoding]::ASCII.GetString($compiledBytes)).Contains('BGXVER21')) {
                throw ('ACTIVE VERSION MARKER MISSING '+$scriptName)
            }
            Log ('VERIFIED ACTIVE BGXVER21 '+$scriptName)
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
    Log ('SUCCESS: BGXAI '+$version+' installed; BGXTANK for Khalid, BGXGRP for Jaheira')
    Log 'v0.6.20: finite retreat and nonblocking fallback; EEex telemetry unchanged. Use disposable save.'
    exit 0
} catch {
    if(([string]$version) -eq '0.6.21-verified-compile-pilot' -and $liveBackupDir -and (Test-Path -LiteralPath $liveBackupDir)) {
        foreach($entry in @(Get-ChildItem -LiteralPath $liveBackupDir -File -ErrorAction SilentlyContinue)) {
            if($entry.Name -match '^(override|scripts)_(BGXGRP|BGXTANK)\.(BCS|BS)$') {
                $restoreDest=Join-Path $GameRoot ($Matches[1]+'\'+$Matches[2]+'.'+$Matches[3])
                Copy-Item -LiteralPath $entry.FullName -Destination $restoreDest -Force -ErrorAction Continue
            }
        }
        Log 'RESTORED pre-WeiDU active scripts following activation failure; WeiDU metadata rollback not guaranteed.'
    }
    Log ('FAILED: '+$_.Exception.Message)
    exit 1
}
