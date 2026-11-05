# BGXUNI_INTEGRATED_INSTALLER_V017
# Runs only when selected from the existing BGXAI_UPDATE.cmd -> BGXAI_SYNC.ps1.
# Installs one SEPARATE, optional BGXUN1 party script. NEVER patches BDDEFAI/BGXGRP/BGXTANK.
# Windows PowerShell 5.1; WeiDU 251; fail-closed with file backups and pinned GitHub assets.
param(
    [string]$GameRoot='.',
    [Parameter(Mandatory=$true)][string]$Commit
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$GameRoot=(Resolve-Path -LiteralPath $GameRoot).Path
$cache=Join-Path $env:LOCALAPPDATA 'BGXAI_UPDATER'
New-Item -ItemType Directory -Path $cache -Force | Out-Null
$log=Join-Path $GameRoot 'BGXUNI_UPDATE.log'
function Log([string]$message) {
    $line='['+(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')+'] [BGXUNI] '+$message
    Write-Host $line
    Add-Content -LiteralPath $log -Value $line -Encoding UTF8
}
function Sha256([byte[]]$bytes) {
    $hash=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}
    finally {$hash.Dispose()}
}
function FetchPinned([string]$path) {
    if($path -notmatch '^BGXAI/pilots/BGXUNI_010/(?:parallel/latest\.json|BGXUNI/BGXUN1\.BAF|BGXUNI/setup-BGXUNI\.tp2)$') {
        throw ('Disallowed remote source: '+$path)
    }
    $base='https://api.github.com/repos/jeleZa112/nwn-xanos-updates/contents/'
    $h=@{'User-Agent'='BGXAI-EET-Updater';'Accept'='application/vnd.github+json';'Cache-Control'='no-cache'}
    $reply=Invoke-RestMethod -Uri ($base+$path+'?ref='+$Commit) -Headers $h -TimeoutSec 50 -UseBasicParsing
    if($reply.encoding -ne 'base64' -or !$reply.content){throw ('Invalid GitHub response: '+$path)}
    [byte[]]$decoded=[Convert]::FromBase64String(([string]$reply.content -replace '\s',''))
    return ,$decoded
}
function ReadScript([string]$relativePath) {
    return ,([IO.File]::ReadAllBytes((Join-Path $GameRoot $relativePath)))
}
function ValidCompiledScript() {
    $compiled=Join-Path $GameRoot 'override\BGXUN1.BCS'
    $assigned=Join-Path $GameRoot 'scripts\BGXUN1.BS'
    if(!(Test-Path -LiteralPath $compiled -PathType Leaf) -or !(Test-Path -LiteralPath $assigned -PathType Leaf)) {return $false}
    [byte[]]$a=[IO.File]::ReadAllBytes($compiled)
    [byte[]]$b=[IO.File]::ReadAllBytes($assigned)
    if($a.Length -lt 120 -or (Sha256 $a) -ne (Sha256 $b)){return $false}
    if(!([Text.Encoding]::ASCII.GetString($a)).Contains('BGXU017')) {return $false}
    return $true
}
$backupRoot=$null
$backupTable=New-Object System.Collections.ArrayList
$changesStarted=$false
$weiduInvoked=$false
try {
    if($Commit -notmatch '^[a-fA-F0-9]{40}$'){throw 'Invalid pinned GitHub commit'}
    if(!(Test-Path -LiteralPath (Join-Path $GameRoot 'chitin.key') -PathType Leaf)){throw 'Missing chitin.key'}
    if(Get-Process -Name Baldur,BaldursGate,InfinityLoader -ErrorAction SilentlyContinue) {
        throw 'Close the game AND InfinityLoader before updating scripts'
    }
    Log 'BGXUNI 0.1.7 PARALLEL via existing BGXAI_UPDATE.cmd (no additional CMD needed)'
    $manifestPath='BGXAI/pilots/BGXUNI_010/parallel/latest.json'
    $manifestBytes=FetchPinned $manifestPath
    $manifest=[Text.Encoding]::UTF8.GetString($manifestBytes) | ConvertFrom-Json
    if($manifest.channel -ne 'BGXUNI-parallel' -or $manifest.version -ne '0.1.7-threat-gated-short-retreat') {
        throw 'Unknown BGXUNI manifest'
    }
    $expected=@(
      'BGXAI/pilots/BGXUNI_010/BGXUNI/BGXUN1.BAF',
      'BGXAI/pilots/BGXUNI_010/BGXUNI/setup-BGXUNI.tp2'
    )
    $downloaded=@{}
    $entries=@($manifest.files)
    if($entries.Count -ne $expected.Count){throw 'Unexpected number of BGXUNI source files'}
    foreach($entry in $entries) {
        $key=[string]$entry.path
        if($expected -notcontains $key -or $downloaded.ContainsKey($key)){throw ('Unexpected/duplicate source: '+$key)}
        [byte[]]$bytes=FetchPinned $key
        if($bytes.Length -ne [int]$entry.size -or (Sha256 $bytes) -ne [string]$entry.sha256) {
            throw ('Source hash/size mismatch: '+$key)
        }
        $downloaded[$key]=$bytes
        Log ('Verified source '+$key+' SHA256 '+(Sha256 $bytes))
    }
    foreach($key in $expected){if(!$downloaded.ContainsKey($key)){throw ('Missing source: '+$key)}}
    $bafBytes=[byte[]]$downloaded[$expected[0]]
    $tp2Bytes=[byte[]]$downloaded[$expected[1]]
    $bafText=[Text.Encoding]::UTF8.GetString($bafBytes)
    $tp2Text=[Text.Encoding]::UTF8.GetString($tp2Bytes)
    if(!$bafText.Contains('BGXU017') -or !$bafText.Contains('ActionListEmpty()')){throw 'Invalid BGXUN1 BAF marker'}
    if(!$tp2Text.Contains('COMPILE ~BGXUNI/BGXUN1.BAF~') -or
       !$tp2Text.Contains('~scripts/BGXUN1.BS~') -or
       $tp2Text -match '(?i)(BDDEFAI|BGXGRP|BGXTANK|BGXRANG|BGXCAST|BGXHEAL)') {
        throw 'TP2 violates parallel-install-only scope'
    }
    $installedTag=Join-Path $GameRoot 'BGXUNI\INSTALLED.TAG'
    $activeScript=Join-Path $GameRoot 'scripts\BGXUN1.BS'
    $compiledScript=Join-Path $GameRoot 'override\BGXUN1.BCS'
    if((Test-Path -LiteralPath $activeScript) -and !(Test-Path -LiteralPath $installedTag)) {
        throw 'Existing BGXUN1.BS without project marker. Stop to protect this script.'
    }
    if((Test-Path -LiteralPath $compiledScript) -and !(Test-Path -LiteralPath $installedTag)) {
        throw 'Existing BGXUN1.BCS without project marker. Stop to protect this script.'
    }
    if(Test-Path -LiteralPath $installedTag) {
        $tag=[IO.File]::ReadAllText($installedTag)
        if($tag -match '(?m)^version=0\.1\.7-threat-gated-short-retreat\s*$' -and
           (ValidCompiledScript)) {
            Log 'ALREADY CURRENT: compiled BGXUN1.BCS and BGXUN1.BS match; legacy scripts untouched.'
            exit 0
        }
        $weiduLog=Join-Path $GameRoot 'WeiDU.log'
        if(!(Test-Path -LiteralPath $weiduLog) -or
           !(Select-String -LiteralPath $weiduLog -Pattern 'BGXUNI[/\\]SETUP-BGXUNI\.TP2' -Quiet)) {
            throw 'Project marker exists but WeiDU.log has no BGXUNI component. Manual audit required.'
        }
    }
    # Detect a conflicting TP2 in game root. Match it against the existing project-owned TP2.
    $rootTp2=Join-Path $GameRoot 'setup-BGXUNI.tp2'
    $projectTp2=Join-Path $GameRoot 'BGXUNI\setup-BGXUNI.tp2'
    if((Test-Path -LiteralPath $rootTp2) -and !(Test-Path -LiteralPath $installedTag)) {
        if(!(Test-Path -LiteralPath $projectTp2)) {
            throw 'Existing root setup-BGXUNI.tp2 has no project source: refuse overwrite'
        }
        if((Sha256 ([IO.File]::ReadAllBytes($rootTp2))) -ne
           (Sha256 ([IO.File]::ReadAllBytes($projectTp2)))) {
            throw 'Root setup-BGXUNI.tp2 differs from project source: refuse overwrite'
        }
    }
    # Only these project-owned files can ever be updated by this branch.
    $filesToBackup=@('BGXUNI\BGXUN1.BAF','BGXUNI\setup-BGXUNI.tp2',
       'setup-BGXUNI.tp2','override\BGXUN1.BCS','scripts\BGXUN1.BS','BGXUNI\INSTALLED.TAG')
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
    $backupRoot=Join-Path $cache ('BGXUNI_parallel_preinstall_'+$stamp)
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    foreach($relativePath in $filesToBackup) {
        $dest=Join-Path $GameRoot $relativePath
        $record=@{relative=$relativePath;existed=(Test-Path -LiteralPath $dest);backup=$null}
        if($record.existed) {
            $backup=Join-Path $backupRoot ($relativePath -replace '[\\/]','__')
            Copy-Item -LiteralPath $dest -Destination $backup -Force
            $record.backup=$backup
        }
        $null=$backupTable.Add($record)
    }
    $mod=Join-Path $GameRoot 'BGXUNI'
    New-Item -ItemType Directory -Path $mod -Force | Out-Null
    $changesStarted=$true
    [IO.File]::WriteAllBytes((Join-Path $mod 'BGXUN1.BAF'),$bafBytes)
    [IO.File]::WriteAllBytes($projectTp2,$tp2Bytes)
    [IO.File]::WriteAllBytes($rootTp2,$tp2Bytes)
    foreach($p in @('BGXUNI\BGXUN1.BAF','BGXUNI\setup-BGXUNI.tp2','setup-BGXUNI.tp2')) {
        $actual=ReadScript $p
        $wanted=if($p -like '*.BAF'){$bafBytes}else{$tp2Bytes}
        if((Sha256 $actual) -ne (Sha256 $wanted)){throw ('Staging verification failure: '+$p)}
    }
    $setup=Join-Path $GameRoot 'setup-BGXUNI.exe'
    if(!(Test-Path -LiteralPath $setup -PathType Leaf)) {
        $source=Join-Path $GameRoot 'setup-stratagems.exe'
        if(!(Test-Path -LiteralPath $source -PathType Leaf)) {$source=Join-Path $GameRoot 'setup-BGXAI.exe'}
        if(!(Test-Path -LiteralPath $source -PathType Leaf)){throw 'Cannot find an existing WeiDU EXE'}
        Copy-Item -LiteralPath $source -Destination $setup
        Log ('Created independent WeiDU setup executable from '+(Split-Path $source -Leaf))
    }
    $installed=(Test-Path -LiteralPath $installedTag)
    $argsList=if($installed) {
       @('--noautoupdate','--no-exit-pause','--reinstall')
    }else{
       @('--noautoupdate','--no-exit-pause','--language','0','--force-install','0')
    }
    Log ('Calling WeiDU only for BGXUNI: '+($argsList -join ' '))
    Push-Location $GameRoot
    try {
        $weiduInvoked=$true
        & $setup @argsList
        $code=$LASTEXITCODE
    } finally {Pop-Location}
    if($code -ne 0){throw ('WeiDU BGXUNI install failed, exit code '+$code+'; see setup-BGXUNI.DEBUG')}
    if(!(ValidCompiledScript)){
        throw 'Compiled BGXUN1.BCS/BGXUN1.BS missing, wrong marker or unequal SHA256'
    }
    $finalHash=Sha256 (ReadScript 'scripts\BGXUN1.BS')
    [IO.File]::WriteAllText($installedTag,('version=0.1.7-threat-gated-short-retreat'+[Environment]::NewLine+
       'sha256='+$finalHash+[Environment]::NewLine),[Text.Encoding]::ASCII)
    Log ('SUCCESS BGXUNI 0.1.7: scripts\BGXUN1.BS SHA256='+$finalHash)
    Log 'SAFE: existing Advanced AI (BDDEFAI) and original BGXAI combat scripts unchanged.'
    Log ('Backup directory: '+$backupRoot)
    exit 0
} catch {
    $failure=$_.Exception.Message
    if($changesStarted -and $backupTable.Count -gt 0) {
        foreach($item in $backupTable) {
            $dest=Join-Path $GameRoot $item.relative
            try {
                if($item.existed -and $item.backup) {
                    Copy-Item -LiteralPath $item.backup -Destination $dest -Force
                } elseif(!$item.existed) {
                    Remove-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue
                }
            } catch { Write-Host ('WARNING: could not restore '+$item.relative) }
        }
    }
    Log ('FAILED: '+$failure)
    if($weiduInvoked) {
        Log 'WeiDU metadata/game TLK rollback was NOT proven. Do not rerun blindly.'
        Log 'Send only the LAST error lines of setup-BGXUNI.DEBUG or this output.'
    }
    exit 1
}
