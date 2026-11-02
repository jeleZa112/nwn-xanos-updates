# BGXAI_RESOURCE_AUDIT.ps1 - safe shadow-script inspection/synchronization.
# Only own BGXGRP / BGXTANK resource names. Preserve backups before replacing.
param([string]$GameRoot=".")
$ErrorActionPreference="Stop"
$GameRoot=(Resolve-Path -LiteralPath $GameRoot).Path
$cache=Join-Path $env:LOCALAPPDATA "BGXAI_UPDATER"
New-Item -ItemType Directory -Path $cache -Force | Out-Null
$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot=Join-Path $cache ("shadow_backup_"+$stamp)
$report=Join-Path $GameRoot "BGXAI_RESOURCE_AUDIT.txt"
function Digest([string]$file) {
    $h=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($h.ComputeHash([IO.File]::ReadAllBytes($file)))).Replace("-","").ToLowerInvariant()}
    finally {$h.Dispose()}
}
function Note([string]$message) {
    $line="[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] "+$message
    Write-Host $line
    Add-Content -LiteralPath $report -Value $line -Encoding UTF8
}
function SyncOwnedFile([string]$src,[string]$dst,[string]$identifier) {
    if(!(Test-Path -LiteralPath $src)) { throw "Source missing: $src" }
    $referenceHash=Digest $src
    if(Test-Path -LiteralPath $dst) {
        $oldHash=Digest $dst
        if($oldHash -eq $referenceHash) {
            Note ("MATCH "+$identifier+" sha256="+$oldHash.Substring(0,16)+" path="+$dst)
            return
        }
        $safeName=($identifier -replace '[^A-Za-z0-9.-]','_')
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
        $backup=Join-Path $backupRoot ($safeName+".bak")
        Copy-Item -LiteralPath $dst -Destination $backup -Force
        Note ("SHADOW OLD "+$identifier+" sha256="+$oldHash.Substring(0,16)+" saved="+$backup)
    } else { Note ("SHADOW NEW "+$identifier+" path="+$dst) }
    New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
    $newHash=Digest $dst
    if($newHash -ne $referenceHash) {throw "Failed hash verification for $dst"}
    Note ("SYNCED "+$identifier+" sha256="+$newHash.Substring(0,16)+" path="+$dst)
}
try {
    Note ("AUDIT BEGIN GameRoot="+$GameRoot)
    foreach($name in @("BGXGRP","BGXTANK")) {
        $mainBS=Join-Path $GameRoot ("scripts\\"+$name+".BS")
        $mainBCS=Join-Path $GameRoot ("override\\"+$name+".BCS")
        if(!(Test-Path -LiteralPath $mainBS) -or !(Test-Path -LiteralPath $mainBCS)) {
            throw "Missing installation resources for $name. Repair WeiDU before shadow sync."
        }
        if((Digest $mainBS) -ne (Digest $mainBCS)) {throw "Game BS/BCS mismatch for $name"}
        Note ("SOURCE "+$name+" sha256="+(Digest $mainBS).Substring(0,16))
    }
    $docRoots=New-Object System.Collections.Generic.List[string]
    $defaultDocs=[Environment]::GetFolderPath("MyDocuments")
    if($defaultDocs) {$docRoots.Add($defaultDocs)}
    if($env:USERPROFILE) {$docRoots.Add((Join-Path $env:USERPROFILE "Documents"))}
    if($env:OneDrive) {$docRoots.Add((Join-Path $env:OneDrive "Documents"))}
    $seen=@{}
    $found=0
    foreach($docs in $docRoots) {
        $home=Join-Path $docs "Baldur's Gate - Enhanced Edition Trilogy"
        $unique=$home.ToLowerInvariant()
        if($seen.ContainsKey($unique)) {continue}
        $seen[$unique]=$true
        if(!(Test-Path -LiteralPath $home)) {continue}
        $found++
        Note ("PROFILE FOUND "+$home)
        $userScripts=Join-Path $home "scripts"
        foreach($name in @("BGXGRP","BGXTANK")) {
            $srcBS=Join-Path $GameRoot ("scripts\\"+$name+".BS")
            $srcBCS=Join-Path $GameRoot ("override\\"+$name+".BCS")
            SyncOwnedFile $srcBS (Join-Path $userScripts ($name+".BS")) ("user_scripts_"+$name+"_BS")
            # Fix only already-existing shadow resources in higher-priority user folders.
            foreach($folderName in @("characters","portraits","sounds","override","scripts")) {
                $candidateDir=Join-Path $home $folderName
                foreach($ext in @(".BS",".BCS")) {
                    $candidate=Join-Path $candidateDir ($name+$ext)
                    if(!(Test-Path -LiteralPath $candidate)) {continue}
                    $src=$srcBCS
                    if($ext -eq ".BS") {$src=$srcBS}
                    SyncOwnedFile $src $candidate ("user_"+$folderName+"_"+$name+$ext)
                }
            }
        }
    }
    if($found -eq 0) {
        Note "WARNING: No user profile folder found; original InfinityLoader path may use a redirected Documents directory."
    }
    Note ("AUDIT SUCCESS profiles="+$found+"; same game script resources, home shadows synchronized.")
    return
} catch {
    Note ("AUDIT FAILED: "+$_.Exception.Message)
    throw
}
