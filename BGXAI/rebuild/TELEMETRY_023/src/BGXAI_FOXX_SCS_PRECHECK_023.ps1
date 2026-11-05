# BGXAI 0.2.3 — READ-ONLY validation after Foxx + SCS installation in a NEW directory.
# Does not install, change, delete, copy or patch any game file.
param([Parameter(Mandatory=$true)][string]$GameRoot)
$ErrorActionPreference='Stop'
try {
  $root=(Resolve-Path -LiteralPath $GameRoot).Path
  if(!(Test-Path -LiteralPath (Join-Path $root 'chitin.key') -PathType Leaf)) {throw 'missing_chitin_key'}
  $log=Join-Path $root 'WeiDU.log'
  if(!(Test-Path -LiteralPath $log -PathType Leaf)){throw 'missing_weidu_log'}
  $lines=@(Get-Content -LiteralPath $log)
  # Use installed component markers; comments are informational only.
  $scs=@($lines | Where-Object {$_ -match '^~STRATAGEMS[\\/]SETUP-STRATAGEMS\.TP2~\s+#\d+\s+#\d+\b'})
  $scsAIMatches=@($scs | Where-Object {$_ -match '^~STRATAGEMS[\\/]SETUP-STRATAGEMS\.TP2~\s+#\d+\s+#5000\b'})
  $scsCore=@($scs | Where-Object {$_ -match '^~STRATAGEMS[\\/]SETUP-STRATAGEMS\.TP2~\s+#\d+\s+#5900\b'})
  $eeex=@($lines | Where-Object {$_ -match '^~EEEX[\\/]EEEX\.TP2~\s+#\d+\s+#1\b'})
  $eet=@($lines | Where-Object {$_ -match '^~EET_END[\\/]EET_END\.TP2~\s+#\d+\s+#0\b'})
  $ver='UNKNOWN'
  foreach($line in $scs){if($line -match ':\s*(\d+\.\d+)\s*$'){$ver=$Matches[1];break}}
  $status='READY_FOR_SOURCE_AUDIT'
  if($scs.Count -eq 0 -or $eeex.Count -eq 0){$status='MISSING_SCS_OR_EEEX'}
  if($scsAIMatches.Count -gt 0){$status='BARD_BEHAVIOR_RISK_SCS_PARTY_AI_5000'}
  if($eet.Count -eq 0){$status='EET_END_NOT_RECORDED'}
  Write-Output ('BGXAI_PRECHECK023 status='+$status)
  Write-Output ('SCS_components='+$scs.Count+' SCS_version='+$ver+' SCS_core5900='+($scsCore.Count -gt 0))
  Write-Output ('SCS_party_AI_5000='+($scsAIMatches.Count -gt 0)+' EEex_installed='+($eeex.Count -gt 0)+' EET_end_logged='+($eet.Count -gt 0))
  Write-Output 'INFO: no verification of script slots, current resource hashes, save compatibility or runtime bard song; source audit still required.'
  if($status -ne 'READY_FOR_SOURCE_AUDIT'){exit 2}
  exit 0
} catch {
  Write-Output 'BGXAI_PRECHECK023 status=ERROR verify new installation path and WeiDU.log (no changes made)'
  exit 3
}
