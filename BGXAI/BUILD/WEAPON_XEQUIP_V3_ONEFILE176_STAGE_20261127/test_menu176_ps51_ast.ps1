$ErrorActionPreference='Stop'
$path='BGXAI/BUILD/WEAPON_XEQUIP_V3_ONEFILE176_STAGE_20261127/STAGED_BGXAI_SYNC_MENU176.ps1'
$full=(Resolve-Path -LiteralPath $path).Path
$tokens=$null
$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($full,[ref]$tokens,[ref]$errors)
if($null -eq $ast -or $errors.Count -ne 0) {
  $errors | ForEach-Object { Write-Host $_.ToString() }
  throw 'STAGED_176_PS51_AST_PARSE_FAIL'
}
$cases=@{'175'=$true;'176'=$true;'174'=$false;'177'=$false;'0'=$false}
foreach($entry in $cases.GetEnumerator()){
  $hit=$false
  switch($entry.Key){
    {$_ -match '^17[56]$'} { $hit=$true;break }
    default {break}
  }
  if($hit -ne $entry.Value){throw ('SWITCH_DISPATCH_BAD '+$entry.Key)}
}
function TestSplat {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
  return ($Arguments -join '|')
}
foreach($choice in @('175','176')) {
  $extra=@()
  if($choice -eq '176'){$extra=@('--v3')}
  $actual=TestSplat '--native-readonly' @extra
  $expected=if($choice -eq '176'){'--native-readonly|--v3'}else{'--native-readonly'}
  if($actual -ne $expected){throw ('SPLAT_ARGS_BAD '+$choice+': '+$actual)}
}
Write-Host 'BGXAI_MENU176_PS51_AST_AND_DISPATCH_PASS'
