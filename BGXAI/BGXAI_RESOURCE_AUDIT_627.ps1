# BGXAI_RESOURCE_AUDIT_627.ps1 - safe shadow-script inspection/synchronization.
# Only owned BGXGRP / BGXTANK / BGXRANG / BGXSCOUT / BGXCAST / BGXHEAL names. Preserve backups before replacing.
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
    foreach($name in @("BGXGRP","BGXTANK","BGXRANG","BGXSCOUT","BGXCAST","BGXHEAL")) {
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
        $profileDir=Join-Path $docs "Baldur's Gate - Enhanced Edition Trilogy"
        $unique=$profileDir.ToLowerInvariant()
        if($seen.ContainsKey($unique)) {continue}
        $seen[$unique]=$true
        if(!(Test-Path -LiteralPath $profileDir)) {continue}
        $found++
        Note ("PROFILE FOUND "+$profileDir)
        $userScripts=Join-Path $profileDir "scripts"
        foreach($name in @("BGXGRP","BGXTANK","BGXRANG","BGXSCOUT","BGXCAST","BGXHEAL")) {
            $srcBS=Join-Path $GameRoot ("scripts\\"+$name+".BS")
            $srcBCS=Join-Path $GameRoot ("override\\"+$name+".BCS")
            SyncOwnedFile $srcBS (Join-Path $userScripts ($name+".BS")) ("user_scripts_"+$name+"_BS")
            # Fix only already-existing shadow resources in higher-priority user folders.
            foreach($folderName in @("characters","portraits","sounds","override","scripts")) {
                $candidateDir=Join-Path $profileDir $folderName
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

    # Read-only provenance: check the active binary for the expected version marker.
    $markerPath=Join-Path $GameRoot 'BGXAI\bgxai-updater-version.txt'
    $expectedMarker='BGXVER20'
    if(Test-Path -LiteralPath $markerPath) {
        $installedMarker=[IO.File]::ReadAllText($markerPath).Trim()
        if($installedMarker -eq '0.6.21-verified-compile-pilot') {$expectedMarker='BGXVER21'}
        if($installedMarker -eq '0.6.22-intercept-melee-pilot') {$expectedMarker='BGXVER22'}
        if($installedMarker -eq '0.6.23-formation-rescue-pilot') {$expectedMarker='BGXVER23'}
        if($installedMarker -eq '0.6.24-support-survival-pilot') {$expectedMarker='BGXVER24'}
        if($installedMarker -eq '0.6.25-healthy-engage-pilot') {$expectedMarker='BGXVER25'}
        if($installedMarker -eq '0.6.26-squad-two-tank-pilot') {$expectedMarker='BGXVER26'}
        if($installedMarker -eq '0.6.25-no-premature-formation-pilot') {$expectedMarker='BGXVER25'}
        if($installedMarker -eq '0.6.23-formation-rescue-pilot') {$expectedMarker='BGXVER23'}
    }
    foreach($scriptName in @("BGXGRP","BGXTANK","BGXRANG","BGXSCOUT","BGXCAST","BGXHEAL")) {
        $compiledFile=Join-Path $GameRoot ("scripts\"+$scriptName+".BS")
        $compiledText=[Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($compiledFile))
        $requiredMarker=$expectedMarker
        if($compiledText.Contains("BGXVER21")) {$requiredMarker='BGXVER21'}
        if($compiledText.Contains("BGXVER22")) {$requiredMarker='BGXVER22'}
        if($compiledText.Contains("BGXVER23")) {$requiredMarker='BGXVER23'}
        if($compiledText.Contains("BGXVER24")) {$requiredMarker='BGXVER24'}
        if($compiledText.Contains("BGXVER25")) {$requiredMarker='BGXVER25'}
        if($compiledText.Contains("BGXVER26")) {$requiredMarker='BGXVER26'}
        if($compiledText.Contains("BGXVER25")) {$requiredMarker='BGXVER25'}
        if($compiledText.Contains("BGXVER23")) {$requiredMarker='BGXVER23'}
        if($compiledText.Contains($requiredMarker)) {
            Note ("COMPILED VERSION MARKER PRESENT "+$scriptName+" "+$requiredMarker)
        } else {
            Note ("WARNING COMPILED VERSION MARKER MISSING "+$scriptName+" expected="+$requiredMarker)
        }
        if($compiledText.Contains("BGXMODE")) {
            Note ("WARNING LEGACY MODE DETECTED "+$scriptName)
        }
    }
    # Scan known game and user resource folders for colliding scripts, without modifying them.
    $scanDirs=New-Object System.Collections.Generic.List[string]
    foreach($folderLabel in @("characters","portraits","sounds","scripts","override","lang\ru_RU\override","lang\en_US\override")) {
        $scanDirs.Add((Join-Path $GameRoot $folderLabel))
    }
    foreach($docs in $docRoots) {
        $userDir=Join-Path $docs "Baldur's Gate - Enhanced Edition Trilogy"
        foreach($folderLabel in @("characters","portraits","sounds","scripts","override")) {
            $scanDirs.Add((Join-Path $userDir $folderLabel))
        }
    }
    $seenDirs=@{}
    foreach($folderPath in $scanDirs) {
        $folderKey=$folderPath.ToLowerInvariant()
        if($seenDirs.ContainsKey($folderKey)) {continue}
        $seenDirs[$folderKey]=$true
        if(!(Test-Path -LiteralPath $folderPath -PathType Container)) {continue}
        foreach($scriptName in @("BGXGRP","BGXTANK","BGXRANG","BGXSCOUT","BGXCAST","BGXHEAL")) {
            $baselineHash=Digest (Join-Path $GameRoot ("scripts\"+$scriptName+".BS"))
            foreach($extension in @(".BS",".BCS")) {
                $candidateFile=Join-Path $folderPath ($scriptName+$extension)
                if(!(Test-Path -LiteralPath $candidateFile -PathType Leaf)) {continue}
                $candidateHash=Digest $candidateFile
                if($candidateHash -eq $baselineHash) {
                    Note ("RESOURCE MATCH "+$scriptName+$extension+" path="+$candidateFile)
                } else {
                    Note ("WARNING RESOURCE CONFLICT "+$scriptName+$extension+" sha256="+$candidateHash.Substring(0,16)+" path="+$candidateFile)
                }
            }
        }
    }
    Note ("AUDIT SUCCESS profiles="+$found+"; same game script resources, home shadows synchronized.")
    return
} catch {
    Note ("AUDIT FAILED: "+$_.Exception.Message)
    throw
}
