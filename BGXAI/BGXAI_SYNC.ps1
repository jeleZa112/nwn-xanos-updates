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
        Log 'Already current; no changes.'
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
    if($version -eq '0.6.17-tank-pursuit-recover-pilot') {
        $patches=@{
            'BGXAI/AI_BAF/BGXTANK.BAF'='BGXAI/hotfix/BGXTANK_0.6.17.BAF'
            'BGXAI/AI_BAF/BGXGRP.BAF'='BGXAI/hotfix/BGXGRP_0.6.17.BAF'
        }
        foreach($target in $patches.Keys) {
            [byte[]]$patch=GetFile $patches[$target] $commit
            $patchText=[Text.Encoding]::UTF8.GetString($patch)
            if($patch.Length -lt 1000 -or !$patchText.Contains('0.6.17')) {throw ('Invalid hotfix script: '+$target)}
            $dst=Join-Path $stage ($target.Replace('/',[IO.Path]::DirectorySeparatorChar))
            [IO.File]::WriteAllBytes($dst,$patch)
            Log ('Staged verified hotfix BAF: '+$target)
        }
    }

    $setup=Join-Path $GameRoot 'setup-BGXAI.exe'
    if(!(Test-Path $setup)) {
        $source=Join-Path $GameRoot 'setup-stratagems.exe'
        if(!(Test-Path $source)) {throw 'WeiDU exe missing'}
        Copy-Item -LiteralPath $source -Destination $setup -Force
    }
    $mod=Join-Path $GameRoot 'BGXAI'
    $backup=Join-Path $cache ('backup_'+$stamp)
    $hadOld=Test-Path $mod
    if($hadOld) {Copy-Item -LiteralPath $mod -Destination $backup -Recurse -Force}
    $weiduLog=Join-Path $GameRoot 'WeiDU.log'
    $installed=$false
    if(Test-Path $weiduLog) {
        $installed=Select-String -LiteralPath $weiduLog -Pattern 'BGXAI[\\/]BGXAI\.TP2' -Quiet
        Copy-Item -LiteralPath $weiduLog -Destination (Join-Path $cache ('WeiDU_'+$stamp+'.log')) -Force
    }
    foreach($p in $allowed) {
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
        if($hadOld) {
            Remove-Item -LiteralPath $mod -Recurse -Force -ErrorAction SilentlyContinue
            Copy-Item -LiteralPath $backup -Destination $mod -Recurse -Force
            Log 'Old BGXAI sources restored; game-level WeiDU rollback is NOT guaranteed.'
        }
        exit 1
    }
    [IO.File]::WriteAllText($marker,$version,[Text.Encoding]::ASCII)
    Log ('SUCCESS: BGXAI '+$version+' installed; BGXTANK for Khalid, BGXGRP for Jaheira')
    Log 'Experimental retreat logic. EEex v5 logging unchanged. Test on a disposable save.'
    exit 0
} catch {
    Log ('FAILED: '+$_.Exception.Message)
    exit 1
}
