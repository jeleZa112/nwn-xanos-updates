param([string]$GameRoot='.',[switch]$SelfTest)
# BGXAI onefile V2: one old CMD, one small permanent dispatch, immutable modules.
# Windows PowerShell 5.1; no game writes, orders, hook installs or implicit retries.
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$Repo='jeleZa112/nwn-xanos-updates'
$Branch='bg-eet-ai'
$IndexPath='BGXAI/UPDATER_V2/MODULES_V1.json'
$LegacyCommit='8fb1296926925b1298085665255bb9ef95ebddd7'
$LegacyPath='BGXAI/UPDATER_V2/BGXAI_SYNC_LEGACY_F282.ps1'
$LegacySize=80027
$LegacyHash='edd1a67be9c5ea9d5ec7c52fb7eb1135cd3ae6f4d248f709459e11667053df75'
$Root=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$Cache=Join-Path $env:LOCALAPPDATA 'BGXAI_UPDATER\VERIFIED_MODULES_V2'

function Stop-IfReparse([string]$Path) {
 if(Test-Path -LiteralPath $Path) {
  $item=Get-Item -LiteralPath $Path -Force
  if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
   throw 'HOLD_UPDATER_V2_REPARSE_POINT'
  }
 }
}
function Digest([byte[]]$Payload) {
 $sha=[Security.Cryptography.SHA256]::Create()
 try {return ([BitConverter]::ToString($sha.ComputeHash($Payload))).Replace('-','').ToLowerInvariant()}
 finally {$sha.Dispose()}
}
function Check-Path([string]$Remote) {
 if($Remote -cnotmatch '^BGXAI/(?:UPDATER_V2|BUILD|patchsets)/[A-Za-z0-9_./-]{1,210}$' -or
    $Remote.Contains('..') -or $Remote.Contains('//') -or
    $Remote.EndsWith('/') -or $Remote.Contains('\')) {
  throw 'HOLD_UPDATER_V2_PATH_NOT_ALLOWLISTED'
 }
}
function Check-Pin([string]$Commit,[string]$Remote,[long]$Size,[string]$Sha) {
 if($Commit -cnotmatch '^[a-f0-9]{40}$' -or
    $Sha -cnotmatch '^[a-f0-9]{64}$' -or
    $Size -lt 1 -or $Size -gt 1000000) {
  throw 'HOLD_UPDATER_V2_PIN_INVALID'
 }
 Check-Path $Remote
}
function Download-Bounded([string]$Url,[int]$Limit) {
 $scratch=Join-Path $Cache ('fetch_'+[guid]::NewGuid().ToString('N')+'.tmp')
 try {
  Invoke-WebRequest -Uri $Url -Headers @{'User-Agent'='BGXAI-Onefile-V2-NoREST'} -OutFile $scratch -UseBasicParsing -TimeoutSec 35 -ErrorAction Stop | Out-Null
  Stop-IfReparse $scratch
  $bytes=[IO.File]::ReadAllBytes($scratch)
  if($bytes.Length -lt 1 -or $bytes.Length -gt $Limit){
   throw 'HOLD_UPDATER_V2_DOWNLOAD_SIZE'
  }
  return ,$bytes
 } finally {
  if(Test-Path -LiteralPath $scratch){Remove-Item -LiteralPath $scratch -Force -ErrorAction SilentlyContinue}
 }
}
function Get-PinnedAsset([string]$Commit,[string]$Remote,[long]$Size,[string]$Sha) {
 Check-Pin $Commit $Remote $Size $Sha
 $ext=[IO.Path]::GetExtension($Remote)
 if($ext -notin @('.py','.ps1','.lua','.json','.baf','.tp2','.2da','.md','.txt')){
  throw 'HOLD_UPDATER_V2_EXTENSION_NOT_ALLOWLISTED'
 }
 $cached=Join-Path $Cache ($Sha+$ext)
 Stop-IfReparse $cached
 if(Test-Path -LiteralPath $cached -PathType Leaf){
  $old=[IO.File]::ReadAllBytes($cached)
  if($old.Length -eq $Size -and (Digest $old) -ceq $Sha){return ,$old}
  throw 'HOLD_UPDATER_V2_CACHED_ASSET_CHANGED'
 }
 $hosts=@(
  ('https://raw.githubusercontent.com/'+$Repo+'/'+$Commit+'/'+$Remote),
  ('https://cdn.jsdelivr.net/gh/'+$Repo+'@'+$Commit+'/'+$Remote)
 )
 $last=''
 foreach($url in $hosts){
  try{
   $bytes=Download-Bounded $url 1000000
   if($bytes.Length -ne $Size -or (Digest $bytes) -cne $Sha){
    throw 'HOLD_UPDATER_V2_DOWNLOADED_PIN_MISMATCH'
   }
   $tmp=Join-Path $Cache ('verified_'+[guid]::NewGuid().ToString('N')+$ext)
   try{
    [IO.File]::WriteAllBytes($tmp,$bytes)
    if((Digest ([IO.File]::ReadAllBytes($tmp))) -cne $Sha){
     throw 'HOLD_UPDATER_V2_STAGE_SHA_CHANGED'
    }
    if(Test-Path -LiteralPath $cached){throw 'HOLD_UPDATER_V2_CACHE_COLLISION'}
    [IO.File]::Move($tmp,$cached)
   } finally {
    if(Test-Path -LiteralPath $tmp){Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue}
   }
   return ,$bytes
  } catch {
   $last=$_.Exception.Message
  }
 }
 throw ('HOLD_UPDATER_V2_ALL_IMMUTABLE_DOWNLOADS_FAILED: '+$last)
}
function Check-Index($Index){
 if($null -eq $Index -or $Index.schema -ne 1 -or
    $Index.channel -cne 'BGXAI_ONEFILE_MODULES_V2' -or
    $Index.branch -cne $Branch) {
  throw 'HOLD_UPDATER_V2_MANIFEST_HEADER'
 }
 $mods=@($Index.modules)
 if($mods.Count -gt 100){throw 'HOLD_UPDATER_V2_TOO_MANY_MODULES'}
 $seen=@{}
 foreach($m in $mods){
  $id=[int]$m.code
  if($m.code -isnot [int] -or $id -lt 180 -or $id -gt 899 -or
     $seen.ContainsKey($id) -or
     [string]$m.label -cnotmatch '^[A-Za-z0-9 .:_()/+-]{3,90}$' -or
     [string]$m.language -cnotin @('python','powershell') -or
     [string]$m.mode -cnotin @('readonly','guarded') -or
     [string]$m.commit -cnotmatch '^[a-f0-9]{40}$') {
   throw 'HOLD_UPDATER_V2_INVALID_MODULE_ENTRY'
  }
  $seen[$id]=$true
  $assets=@($m.files)
  if($assets.Count -lt 1 -or $assets.Count -gt 30){
   throw 'HOLD_UPDATER_V2_ASSET_COUNT'
  }
  $names=@{}
  foreach($file in $assets){
   $remote=[string]$file.path
   Check-Pin ([string]$m.commit) $remote ([long]$file.size) ([string]$file.sha256)
   if($names.ContainsKey($remote)){
    throw 'HOLD_UPDATER_V2_DUPLICATED_ASSET'
   }
   $names[$remote]=$true
  }
  if(-not $names.ContainsKey([string]$m.entry)){
   throw 'HOLD_UPDATER_V2_ENTRY_NOT_IN_PINNED_ASSETS'
  }
  $expectedExt=if($m.language -ceq 'python'){'.py'}else{'.ps1'}
  if(-not ([string]$m.entry).EndsWith($expectedExt)){
   throw 'HOLD_UPDATER_V2_ENTRY_EXTENSION'
  }
  if($m.mode -ceq 'guarded' -and
     ([string]$m.approval -cnotmatch '^(?:INSTALL|ROLLBACK)_BGXAI_[A-Z0-9_]{8,100}$')){
   throw 'HOLD_UPDATER_V2_GUARDED_TOKEN'
  }
 }
 return $mods
}
function Get-ModuleIndex {
 $filename=Join-Path $Cache 'last_verified_index.json'
 $lock=Join-Path $Cache 'last_verified_index.sha256'
 Stop-IfReparse $filename;Stop-IfReparse $lock
 $hosts=@(
  ('https://raw.githubusercontent.com/'+$Repo+'/'+$Branch+'/'+$IndexPath+'?bgxnonce='+[DateTime]::UtcNow.Ticks),
  ('https://cdn.jsdelivr.net/gh/'+$Repo+'@'+$Branch+'/'+$IndexPath+'?bgxnonce='+[DateTime]::UtcNow.Ticks)
 )
 foreach($url in $hosts){
  try{
   $bytes=Download-Bounded $url 32768
   $m=[Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
   $null=Check-Index $m
   $hash=Digest $bytes
   [IO.File]::WriteAllBytes($filename,$bytes)
   [IO.File]::WriteAllText($lock,$hash,[Text.Encoding]::ASCII)
   return $m
  }catch{Write-Host ('V2 manifest host unavailable: '+$_.Exception.GetType().Name)}
 }
 if((Test-Path -LiteralPath $filename -PathType Leaf) -and
    (Test-Path -LiteralPath $lock -PathType Leaf)){
  $bytes=[IO.File]::ReadAllBytes($filename)
  if($bytes.Length -le 32768 -and
     (Digest $bytes) -ceq [IO.File]::ReadAllText($lock).Trim()){
   $m=[Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
   $null=Check-Index $m
   Write-Host 'BGXAI V2: offline last verified module index.'
   return $m
  }
 }
 Write-Host 'BGXAI V2: no verified module index. Legacy 1-179 still available.'
 return $null
}
function Execute-Legacy([int]$Choice) {
 $bytes=Get-PinnedAsset $LegacyCommit $LegacyPath $LegacySize $LegacyHash
 $path=Join-Path $Cache ($LegacyHash+'.ps1')
 if((Digest ([IO.File]::ReadAllBytes($path))) -cne $LegacyHash){
  throw 'HOLD_UPDATER_V2_LEGACY_SOURCE_MISMATCH'
 }
 Write-Host 'BGXAI V2 -> original exact f282 legacy menu; no new behavior.'
 & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $path -GameRoot $Root -HubChoice ([string]$Choice)
 if($LASTEXITCODE -ne 0){throw ('HOLD_UPDATER_V2_LEGACY_EXIT_'+$LASTEXITCODE)}
}
function Execute-Module($Module) {
 if($Module.mode -ceq 'guarded'){
  $approval=[string]$Module.approval
  Write-Host 'GUARDED MODULE: a separate exact confirmation is required.'
  $typed=Read-Host ('Type '+$approval+' exactly (ENTER cancels)')
  if($typed -cne $approval){throw 'HOLD_UPDATER_V2_TYPED_CONSENT_MISSING'}
 }
 $work=Join-Path $Cache ('run_'+[guid]::NewGuid().ToString('N'))
 [IO.Directory]::CreateDirectory($work) | Out-Null
 try{
  if($work -eq $Root -or $work.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase)){
   throw 'HOLD_UPDATER_V2_STAGE_OVERLAPS_GAME'
  }
  foreach($f in @($Module.files)){
   $remote=[string]$f.path
   $bytes=Get-PinnedAsset ([string]$Module.commit) $remote ([long]$f.size) ([string]$f.sha256)
   $local=Join-Path $work ($remote.Replace('/',[IO.Path]::DirectorySeparatorChar))
   $parent=Split-Path -Parent $local
   [IO.Directory]::CreateDirectory($parent) | Out-Null
   [IO.File]::WriteAllBytes($local,$bytes)
   if((Digest ([IO.File]::ReadAllBytes($local))) -cne [string]$f.sha256){
    throw 'HOLD_UPDATER_V2_MODULE_SOURCE_CHANGED'
   }
  }
  $entry=Join-Path $work (([string]$Module.entry).Replace('/',[IO.Path]::DirectorySeparatorChar))
  Write-Host ('BGXAI V2 module '+$Module.code+': '+$Module.label)
  if($Module.language -ceq 'python'){
   if($Module.mode -ceq 'readonly'){
    & py -3 $entry --game $Root --onefile-hub-source-only
   }else{
    & py -3 $entry --game $Root --onefile-hub-guarded --approved-token ([string]$Module.approval)
   }
  }else{
   if($Module.mode -ceq 'readonly'){
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $entry -GameRoot $Root -OnefileHubSourceOnly
   }else{
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $entry -GameRoot $Root -OnefileHubGuarded -ApprovedToken ([string]$Module.approval)
   }
  }
  if($LASTEXITCODE -ne 0){throw ('HOLD_UPDATER_V2_MODULE_EXIT_'+$LASTEXITCODE)}
 }finally{
  if(Test-Path -LiteralPath $work){Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue}
 }
}
function Run-SelfTest {
 $fixture='{"schema":1,"channel":"BGXAI_ONEFILE_MODULES_V2","branch":"bg-eet-ai","modules":[{"code":180,"label":"Test read only","language":"python","mode":"readonly","commit":"0123456789abcdef0123456789abcdef01234567","entry":"BGXAI/UPDATER_V2/TEST.py","files":[{"path":"BGXAI/UPDATER_V2/TEST.py","size":14,"sha256":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]}]}'
 $obj=ConvertFrom-Json $fixture
 if((@(Check-Index $obj)).Count -ne 1){throw 'SELFTEST_MANIFEST_FAIL'}
 $obj.modules[0].files[0].path='BGXAI/../../../evil.py'
 try{$null=Check-Index $obj;throw 'SELFTEST_BAD_PATH_ACCEPTED'}
 catch{if($_.Exception.Message -ceq 'SELFTEST_BAD_PATH_ACCEPTED'){throw}}
 $obj=ConvertFrom-Json $fixture
 $obj.modules[0].mode='guarded'
 try{$null=Check-Index $obj;throw 'SELFTEST_GUARDED_WITHOUT_TOKEN_ACCEPTED'}
 catch{if($_.Exception.Message -ceq 'SELFTEST_GUARDED_WITHOUT_TOKEN_ACCEPTED'){throw}}
 Write-Host 'BGXAI_UPDATER_V2_SELFTEST_PASS'
}
try{
 if($SelfTest){Run-SelfTest;exit 0}
 if($Root -ine 'C:\Games\BG_EET_FOXX_NEW' -or
    !(Test-Path -LiteralPath (Join-Path $Root 'chitin.key') -PathType Leaf)){
  throw 'HOLD_UPDATER_V2_GAME_ROOT'
 }
 foreach($folder in @($Cache,(Join-Path $Cache '..'))){
  Stop-IfReparse $folder
 }
 [IO.Directory]::CreateDirectory($Cache) | Out-Null
 $index=Get-ModuleIndex
 $mods=if($null -eq $index){@()}else{@(Check-Index $index)}
 Write-Host 'BGXAI V2: SAME original BGXAI_UPDATE.cmd. SHA-pinned isolated modules.'
 Write-Host 'Legacy: 1-174 unchanged | 175 inert | 176 R38 | 179 R42/R47 guarded | 0 exit'
 foreach($m in $mods){Write-Host ('Module '+$m.code+': '+$m.label+' ['+$m.mode+']')}
 $choice=(Read-Host 'Choice [0]').Trim()
 if(!$choice -or $choice -eq '0'){Write-Host 'No game changes.';exit 0}
 if($choice -notmatch '^[1-9][0-9]{0,2}$'){throw 'HOLD_UPDATER_V2_BAD_MENU_CHOICE'}
 $n=[int]$choice
 if($n -le 179){Execute-Legacy $n}
 else{
  $chosen=@($mods | Where-Object {$_.code -eq $n})
  if($chosen.Count -ne 1){throw 'HOLD_UPDATER_V2_UNKNOWN_MODULE'}
  Execute-Module $chosen[0]
 }
 exit 0
}catch{
 Write-Host ('BGXAI V2 STOP: '+$_.Exception.Message)
 Write-Host 'No auto retry. Do not overwrite existing R47/EPS.'
 exit 3
}
