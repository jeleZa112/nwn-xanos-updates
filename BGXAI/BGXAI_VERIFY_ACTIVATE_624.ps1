# BGXAI v0.6.24 verified activation. Runs only after WeiDU successfully creates unique BCS.
# Keeps original BGXGRP/BGXTANK names chosen in existing saves.
param([string]$GameRoot=".", [string]$CacheRoot="")
$ErrorActionPreference="Stop"
$GameRoot=(Resolve-Path -LiteralPath $GameRoot).Path
if(!$CacheRoot) {$CacheRoot=Join-Path $env:LOCALAPPDATA "BGXAI_UPDATER"}
$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath=Join-Path $CacheRoot ("active_scripts_before_624_"+$stamp)
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
function Digest([byte[]]$bytes) {
  $sha=[Security.Cryptography.SHA256]::Create()
  try {return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-","").ToLowerInvariant()}
  finally {$sha.Dispose()}
}
$plan=@(
  @{newName="BGG624";oldName="BGXGRP"},
  @{newName="BGT624";oldName="BGXTANK"}
)
$operations=New-Object System.Collections.ArrayList
# FIRST verify BOTH new outputs, then and only then modify any live file.
foreach($pair in $plan) {
  $compiledFile=Join-Path $GameRoot ("override\"+$pair.newName+".BCS")
  if(!(Test-Path -LiteralPath $compiledFile -PathType Leaf)) {throw ("WeiDU did not compile "+$pair.newName+".BCS")}
  [byte[]]$newBytes=[IO.File]::ReadAllBytes($compiledFile)
  if($newBytes.Length -lt 100) {throw ("Invalid compiled output for "+$pair.newName)}
  $display=[Text.Encoding]::ASCII.GetString($newBytes)
  if(!$display.Contains("BGXVER24")) {throw ("Version marker BGXVER24 missing in compiled "+$pair.newName)}
  if($display.Contains("BGXMODE")) {throw ("Legacy BGXMODE found in compiled "+$pair.newName)}
  $hash=Digest $newBytes
  Write-Host ("PROVEN NEW COMPILED "+$pair.newName+" SHA256="+$hash)
  foreach($target in @(
      (Join-Path $GameRoot ("override\"+$pair.oldName+".BCS")),
      (Join-Path $GameRoot ("scripts\"+$pair.oldName+".BS"))
  )) {
    $null=$operations.Add(@{path=$target;bytes=$newBytes;hash=$hash;label=$pair.oldName})
  }
}
# Backup every affected live file before the first write.
$backups=New-Object System.Collections.ArrayList
foreach($operation in $operations) {
  $destination=$operation.path
  $entry=@{path=$destination;existed=(Test-Path -LiteralPath $destination);backup=""}
  if($entry.existed) {
    $backupFile=Join-Path $backupPath ((Split-Path -Leaf $destination)+"_"+$backups.Count+".bak")
    Copy-Item -LiteralPath $destination -Destination $backupFile -Force
    $entry.backup=$backupFile
  }
  $null=$backups.Add($entry)
}
try {
  foreach($operation in $operations) {
    $destination=$operation.path
    $tempFile=$destination+".bgxai_pending"
    [IO.File]::WriteAllBytes($tempFile,[byte[]]$operation.bytes)
    if((Digest ([IO.File]::ReadAllBytes($tempFile))) -ne $operation.hash) {throw ("Staging failed for "+$destination)}
    Move-Item -LiteralPath $tempFile -Destination $destination -Force
    if((Digest ([IO.File]::ReadAllBytes($destination))) -ne $operation.hash) {throw ("Activation failed for "+$destination)}
    Write-Host ("ACTIVE VERIFIED "+$operation.label+" "+$destination)
  }
} catch {
  foreach($entry in $backups) {
    if($entry.existed -and $entry.backup) {
      Copy-Item -LiteralPath $entry.backup -Destination $entry.path -Force -ErrorAction Continue
    } elseif(!$entry.existed) {
      Remove-Item -LiteralPath $entry.path -Force -ErrorAction SilentlyContinue
    }
  }
  throw
}
Write-Host "BGXAI v0.6.24 VERIFIED ACTIVATION SUCCESS"
