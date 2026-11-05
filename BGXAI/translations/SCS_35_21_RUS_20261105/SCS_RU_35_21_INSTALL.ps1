# SCS 35.21 Russian translation patch. Powershell 5.1, ASCII script; UTF-8 .TRA payload.
param([string]$GameRoot = '', [switch]$Restore)
$ErrorActionPreference='Stop'
$scriptDir=Split-Path -Parent $MyInvocation.MyCommand.Path
if([string]::IsNullOrWhiteSpace($GameRoot)){$GameRoot=$scriptDir}
$root=[IO.Path]::GetFullPath($GameRoot)
if(!(Test-Path -LiteralPath (Join-Path $root 'chitin.key') -PathType Leaf)) {
  $parent=Split-Path -Parent $root
  if(Test-Path -LiteralPath (Join-Path $parent 'chitin.key') -PathType Leaf){$root=$parent}
  else{throw 'chitin.key missing. Extract this patch into your NEW EET game root.'}
}
$src=Join-Path $root 'stratagems\lang\russian'
$tp2=Join-Path $root 'stratagems\setup-stratagems.tp2'
$somSrc=Join-Path $root 'stratagems\lang_som\russian'
$backupRoot=Join-Path $root 'SCS_RU35_21_BACKUPS'
$sourcePaths=@{
  'setup.tra'=(Join-Path $src 'setup.tra');
  'gameplay.tra'=(Join-Path $src 'gameplay.tra');
  'initial.tra'=(Join-Path $src 'initial.tra');
  'leveller.tra'=(Join-Path $src 'leveller.tra');
  'spell_som.tra'=(Join-Path $somSrc 'spell.tra')
}
$utf8=[System.Text.UTF8Encoding]::new($false)
function ReadUtf8([string]$file){return [IO.File]::ReadAllText($file,[Text.Encoding]::UTF8)}
function Make-IdSet([string]$txt){
  $set=@{}
  foreach($match in [regex]::Matches($txt,'(?m)^\s*@(\d+)\s*=')) {
    $id=$match.Groups[1].Value
    if($set.ContainsKey($id)){throw ('Duplicate translation id @'+$id)}
    $set[$id]=$true
  }
  return $set
}
function Is-SameIds($left,$right){
  if($left.Count -ne $right.Count){return $false}
  foreach($key in $left.Keys){if(!$right.ContainsKey($key)){return $false}}
  return $true
}
function Check-Payload([string]$file,[string]$sha){
  if(!(Test-Path -LiteralPath $file -PathType Leaf)){throw ('Payload not found: '+$file)}
  $calculated=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
  if($calculated -ne $sha){throw ('Payload integrity failure: '+$file)}
}
if($Restore){
  if(!(Test-Path -LiteralPath $backupRoot -PathType Container)){throw 'No translation backup found.'}
  $list=@(Get-ChildItem -LiteralPath $backupRoot -Directory | Sort-Object Name -Descending)
  if($list.Count -lt 1){throw 'No translation backup found.'}
  $backup=$list[0].FullName
  foreach($name in @('setup.tra','gameplay.tra','initial.tra','leveller.tra','spell_som.tra')){
    $from=Join-Path $backup $name
    $dest=$sourcePaths[$name]
    if(!(Test-Path -LiteralPath $from -PathType Leaf)){throw ('Backup incomplete: '+$from)}
    if(!(Test-Path -LiteralPath $dest -PathType Leaf)){throw ('Game .tra missing: '+$dest)}
  }
  foreach($name in @('setup.tra','gameplay.tra','initial.tra','leveller.tra','spell_som.tra')){
    Copy-Item -LiteralPath (Join-Path $backup $name) -Destination $sourcePaths[$name] -Force
  }
  Write-Host ('RESTORED original translation files from '+$backup) -ForegroundColor Green
  Write-Host 'NOTE: This restores only source .tra, NOT previously installed game translations.'
  exit 0
}
if(!(Test-Path -LiteralPath $tp2 -PathType Leaf)){throw 'SCS installer files missing: stratagems/setup-stratagems.tp2'}
if((ReadUtf8 $tp2) -notmatch '(?m)^\s*VERSION\s+~35\.21~'){throw 'Wrong SCS version. This patch is ONLY for original v35.21.'}
$manifestPath=Join-Path $scriptDir 'PAYLOAD_MANIFEST.json'
if(!(Test-Path -LiteralPath $manifestPath)){throw 'PAYLOAD_MANIFEST.json not found.'}
$manifest=ReadUtf8 $manifestPath | ConvertFrom-Json
if($manifest.tag -ne 'v35.21' -or [int]$manifest.installer_translation_entries -ne 263 -or [int]$manifest.new_game_translation_entries -ne 18){throw 'Wrong translation manifest.'}
foreach($it in $manifest.files.PSObject.Properties){
  $f=Join-Path (Join-Path $scriptDir 'translated') ([string]$it.Name)
  Check-Payload $f ([string]$it.Value.sha256)
}
$translationSetup=Join-Path $scriptDir 'translated\setup.tra'
$setupTarget=Join-Path $src 'setup.tra'
if(!(Test-Path -LiteralPath $setupTarget)){throw 'Russian SCS language folder not found.'}
$newSetupBytes=[IO.File]::ReadAllBytes($translationSetup)
$newSetup=ReadUtf8 $translationSetup
$allIds=Make-IdSet $newSetup
if($allIds.Count -ne 263 -or !$allIds.ContainsKey('50016')){throw 'Invalid translated setup.tra key set.'}
$oldSetup=ReadUtf8 $setupTarget
$oldSetupIds=Make-IdSet $oldSetup
$changes=@{}
$files=@('setup.tra','gameplay.tra','initial.tra','leveller.tra','spell_som.tra')
foreach($name in $files){
  if(!(Test-Path -LiteralPath $sourcePaths[$name] -PathType Leaf)){throw ('SCS Russian file missing: '+$name)}
}
$oldSetupBytes=[IO.File]::ReadAllBytes($setupTarget)
$setupIdentical=([Convert]::ToBase64String($oldSetupBytes) -eq [Convert]::ToBase64String($newSetupBytes))
if(!$setupIdentical){
  # Official v35.21 Russian setup has 262 untranslated keys and lacks @50016.
  $check=@{}
  foreach($id in $allIds.Keys){if($id -ne '50016'){$check[$id]=$true}}
  if(!(Is-SameIds $oldSetupIds $check) -or
     $oldSetup -notmatch '(?m)^\s*@3\s*=\s*~Spell system tweaks~' -or
     $oldSetup -notmatch '(?m)^\s*@7\s*=\s*~Ease-of-use party AI~'){
    throw 'setup.tra is not the unmodified official SCS 35.21 Russian version. Refusing to overwrite existing custom translation.'
  }
  $changes['setup.tra']=$newSetupBytes
}
$counts=@{'gameplay.tra'=90;'initial.tra'=11;'leveller.tra'=53;'spell_som.tra'=217}
foreach($name in @('gameplay.tra','initial.tra','leveller.tra','spell_som.tra')){
  $f=$sourcePaths[$name]
  $existing=ReadUtf8 $f
  $known=Make-IdSet $existing
  $addition=ReadUtf8 (Join-Path (Join-Path $scriptDir 'translated') ($name+'.add'))
  $added=Make-IdSet $addition
  if($added.Count -eq 0){throw ('Empty .tra.add: '+$name)}
  $present=0
  foreach($id in $added.Keys){if($known.ContainsKey($id)){$present++}}
  if($present -eq $added.Count){
    # Already applied; do not overwrite any existing translation.
    continue
  }
  if($present -ne 0){throw ('Partially localized '+$name+'; no files changed. Reconcile this file manually.')}
  if($known.Count -ne [int]$counts[$name]){
    throw ('Unexpected v35.21 Russian translation layout: '+$name+' has '+$known.Count+' entries. No files changed.')
  }
  $joined=$existing.TrimEnd([char[]]@("`r","`n"))+"`r`n`r`n"+$addition
  $changes[$name]=$utf8.GetBytes($joined)
}
if($changes.Count -eq 0){Write-Host 'ALREADY PATCHED. No changes were made.' -ForegroundColor Green;exit 0}
# Fully validate all inputs before touching anything.
[void][IO.Directory]::CreateDirectory($backupRoot)
$stamp=(Get-Date -Format 'yyyyMMdd_HHmmss_fff')
$backup=Join-Path $backupRoot $stamp
[void][IO.Directory]::CreateDirectory($backup)
$sourceBytes=@{}
foreach($name in $files){
  $original=$sourcePaths[$name]
  $sourceBytes[$name]=[IO.File]::ReadAllBytes($original)
  [IO.File]::WriteAllBytes((Join-Path $backup $name),$sourceBytes[$name])
}
try {
  foreach($name in $files){
    if(!$changes.ContainsKey($name)){continue}
    $dest=$sourcePaths[$name]
    $temp=$dest+'.BGXAI_RU_PATCH.tmp'
    [IO.File]::WriteAllBytes($temp,[byte[]]($changes[$name]))
    Move-Item -LiteralPath $temp -Destination $dest -Force
    Write-Host ('UPDATED '+$name) -ForegroundColor Green
  }
  $newKeys=Make-IdSet (ReadUtf8 $setupTarget)
  if($newKeys.Count -ne 263){throw 'Post-write setup count mismatch.'}
  foreach($name in @('gameplay.tra','initial.tra','leveller.tra','spell_som.tra')){
    $ids=Make-IdSet (ReadUtf8 $sourcePaths[$name])
    $added=Make-IdSet (ReadUtf8 (Join-Path (Join-Path $scriptDir 'translated') ($name+'.add')))
    foreach($id in $added.Keys){if(!$ids.ContainsKey($id)){throw ('Missing post-write @'+$id+' in '+$name)}}
  }
  [IO.File]::WriteAllText((Join-Path $backup 'README_BACKUP.txt'),'Unmodified Russian SCS 35.21 .tra source files. Run SCS_RU_35_21_RESTORE.cmd to restore them.',$utf8)
  Write-Host 'SUCCESS: SCS 35.21 Russian setup (263 entries) + 18 missing game entries.' -ForegroundColor Green
  Write-Host ('BACKUP: '+$backup)
  Write-Host 'Next: run setup-stratagems.exe and choose Russian. Skip SCS party AI component #5000.'
}catch{
  foreach($name in $files){
    try{[IO.File]::WriteAllBytes($sourcePaths[$name],[byte[]]($sourceBytes[$name]))}catch{}
    try{Remove-Item -LiteralPath ($sourcePaths[$name]+'.BGXAI_RU_PATCH.tmp') -Force -ErrorAction SilentlyContinue}catch{}
  }
  throw ('Installation failed and rollback was attempted: '+$_.Exception.Message)
}
