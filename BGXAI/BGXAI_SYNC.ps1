# BGXAI GitHub package updater. Versioned, SHA256 verified, own mod files only.
param([string]$GameRoot=".")
$ErrorActionPreference="Stop"
$ProgressPreference="SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$GameRoot=(Resolve-Path -LiteralPath $GameRoot).Path
$cache=Join-Path $env:LOCALAPPDATA "BGXAI_UPDATER"
New-Item -ItemType Directory -Path $cache -Force | Out-Null
$log=Join-Path $GameRoot "BGXAI_UPDATE.log"
function Log([string]$msg) {
    $s="[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Write-Host $s
    Add-Content -LiteralPath $log -Value $s -Encoding UTF8
}
function Get-Bytes([string]$path) {
    $uri="https://api.github.com/repos/jeleZa112/nwn-xanos-updates/contents/$($path)?ref=$sha"
    $h=@{"User-Agent"="BGXAI-EET-Updater";"Accept"="application/vnd.github+json";"Cache-Control"="no-cache"}
    $obj=Invoke-RestMethod -Uri $uri -Headers $h -TimeoutSec 40 -UseBasicParsing
    if($obj.encoding -ne "base64" -or -not $obj.content){ throw "Invalid GitHub response: $path" }
    return ,([Convert]::FromBase64String(([string]$obj.content -replace '\s','')))
}
function Sha256([byte[]]$bytes) {
    $algo=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algo.ComputeHash($bytes))).Replace("-","").ToLowerInvariant() }
    finally { $algo.Dispose() }
}
try {
    if(!(Test-Path (Join-Path $GameRoot "chitin.key"))){throw "Put BGXAI_UPDATE.cmd next to chitin.key"}
    if(!(Test-Path (Join-Path $GameRoot "override"))){throw "override folder missing"}
    if(Get-Process -Name Baldur,BaldursGate,baldur -ErrorAction SilentlyContinue){throw "Close Baldur's Gate before updating"}
    $sha=[IO.File]::ReadAllText((Join-Path $cache "head.txt")).Trim()
    if($sha -notmatch "^[a-fA-F0-9]{40}$"){throw "Bad GitHub commit marker"}
    $manifest=[Text.Encoding]::UTF8.GetString((Get-Bytes "BGXAI/latest.json")) | ConvertFrom-Json
    if($manifest.channel -ne "pilot" -or $manifest.package_path -notmatch '^BGXAI/releases/[A-Za-z0-9._-]+\.zip\.b64$'){throw "Unsupported manifest"}
    $version=[string]$manifest.version
    if($version -notmatch '^[A-Za-z0-9._-]+$'){throw "Invalid release version"}
    Log "GitHub release: $version; status: $($manifest.status)"
    $marker=Join-Path $GameRoot "BGXAI\bgxai-updater-version.txt"
    if((Test-Path $marker) -and ([IO.File]::ReadAllText($marker).Trim() -eq $version)) {
       Log "Already installed; no changes."
       exit 0
    }
    $raw=[Text.Encoding]::UTF8.GetString((Get-Bytes ([string]$manifest.package_path))).Trim()
    if($raw -notmatch '^[A-Za-z0-9+/=]+$'){throw "Package is not valid base64"}
    $bytes=[Convert]::FromBase64String($raw)
    if($bytes.Length -ne [int]$manifest.package_size){throw "Package size mismatch"}
    if((Sha256 $bytes) -ne [string]$manifest.package_sha256){throw "SHA256 mismatch; refusing update"}
    $stamp=Get-Date -Format "yyyyMMdd_HHmmss"
    $stage=Join-Path $cache "stage_$stamp"
    New-Item -ItemType Directory -Path $stage -Force | Out-Null
    Add-Type -AssemblyName System.IO.Compression
    $zip=New-Object IO.MemoryStream(,$bytes)
    $archive=New-Object IO.Compression.ZipArchive($zip,[IO.Compression.ZipArchiveMode]::Read)
    $allowed=@("BGXAI/BGXAI.TP2","BGXAI/AI_BAF/BGXATK.BAF","BGXAI/AI_BAF/BGXSCUT.BAF","BGXAI/AI_BAF/BGXHEAL.BAF","BGXAI/AI_BAF/BGXWARD.BAF","BGXAI/AI_BAF/BGXHYBR.BAF","BGXAI/AI_BAF/BGXMANU.BAF","BGXAI/AI_BAF/BGXSAFE.BAF","BGXAI/AI_BAF/BGXDBG.BAF","BGXAI/AI_BAF/BGXGRP.BAF","BGXAI/AI_BAF/BGXTANK.BAF")
    $found=@()
    try {
      foreach($entry in $archive.Entries) {
        $rel=$entry.FullName.Replace('\','/')
        if($rel -eq "README_RU.txt"){continue}
        if($allowed -notcontains $rel -or $found -contains $rel){throw "Unexpected or duplicate package entry: $rel"}
        $found+= $rel
        $dest=Join-Path $stage ($rel.Replace('/',[IO.Path]::DirectorySeparatorChar))
        New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
        $inputStream=$entry.Open()
        $outputStream=[IO.File]::Create($dest)
        try { $inputStream.CopyTo($outputStream) } finally { $outputStream.Dispose(); $inputStream.Dispose() }
      }
    } finally { $archive.Dispose(); $zip.Dispose() }
    if($found.Count -ne $allowed.Count){throw "Incomplete package"}
    $setup=Join-Path $GameRoot "setup-BGXAI.exe"
    if(!(Test-Path $setup)){
       $weidu=Join-Path $GameRoot "setup-stratagems.exe"
       if(!(Test-Path $weidu)){throw "No setup-BGXAI.exe or setup-stratagems.exe (WeiDU). Not installed."}
       Copy-Item $weidu $setup
    }
    $moddir=Join-Path $GameRoot "BGXAI"
    $backup=Join-Path $cache "backup_$stamp"
    $hadOld=Test-Path $moddir
    if($hadOld){Copy-Item $moddir $backup -Recurse -Force}
    $weiduLog=Join-Path $GameRoot "WeiDU.log"
    $installed=$false
    if(Test-Path $weiduLog){
       $installed=Select-String -LiteralPath $weiduLog -Pattern 'BGXAI[\\/]BGXAI\.TP2' -Quiet
       Copy-Item $weiduLog (Join-Path $cache "WeiDU_$stamp.log") -Force
    }
    foreach($rel in $allowed) {
       $src=Join-Path $stage ($rel.Replace('/',[IO.Path]::DirectorySeparatorChar))
       $dst=Join-Path $GameRoot ($rel.Replace('/',[IO.Path]::DirectorySeparatorChar))
       New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
       Copy-Item $src $dst -Force
    }
    Log "SHA256 verified; source backed up: $backup; starting WeiDU."
    $arguments=@("--noautoupdate","--no-exit-pause")
    if($installed){$arguments+=@("--reinstall","0")}
    else{$arguments+=@("--language","0","--force-install","0")}
    Push-Location $GameRoot
    try { & $setup @arguments; $code=$LASTEXITCODE }
    finally { Pop-Location }
    if($code -ne 0) {
       Log "WeiDU failed, exit=$code; see setup-BGXAI.DEBUG"
       if($hadOld) {
          Remove-Item $moddir -Recurse -Force -ErrorAction SilentlyContinue
          Copy-Item $backup $moddir -Recurse -Force
          Log "Restored previous source folder (game-level WeiDU rollback NOT guaranteed)."
       }
       exit 1
    }
    [IO.File]::WriteAllText($marker,$version,[Text.Encoding]::ASCII)
    Log "SUCCESS: BGXAI $version; BGXTANK for Khalid, BGXGRP for Jaheira."
    Log "IMPORTANT: Experimental. Detailed combat telemetry is NOT active yet."
    exit 0
} catch {
    Log ("FAILED: "+ $_.Exception.Message)
    exit 1
}