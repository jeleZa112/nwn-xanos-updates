# BG Voice RU safe updater. Code-only. Run from bg_voice_release_v2.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path -LiteralPath (Join-Path $root 'VOICE_MANIFEST.csv'))) {
 throw 'Place BG_VOICE_UPDATE.ps1 inside bg_voice_release_v2 next to VOICE_MANIFEST.csv.'
}
$base = 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/bg-voice-ru'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$stage = Join-Path $root ('.bgvoice_stage_' + $stamp)
$backup = Join-Path $root ('BG_VOICE_BACKUP_' + $stamp)
New-Item -ItemType Directory -Path $stage -Force | Out-Null
try {
 Write-Host 'BG Voice RU: downloading manifest...'
 $manifestPath = Join-Path $stage 'manifest.json'
 Invoke-WebRequest -UseBasicParsing -Uri ($base + '/release_manifest.json') -OutFile $manifestPath -TimeoutSec 90
 $manifest = Get-Content -Raw -Encoding UTF8 $manifestPath | ConvertFrom-Json
 if ($manifest.project -ne 'BG_VOICE_RU' -or $manifest.version -notmatch '^\\d+\\.\\d+(\\.\\d+)?) { throw 'Unexpected release manifest' }
 $entries = @($manifest.files)
 if ($entries.Count -lt 3) {throw 'Incomplete manifest'}
 # Download + validate *every* file before installing anything.
 foreach ($item in $entries) {
  $name = [string]$item.path
  if ($name -notmatch '^(BG_RU_IMOEN_PROSODY_29/[A-Za-z0-9_.-]+|BG_VOICE_UPDATE.cmd)$') {throw ('Disallowed filename: ' + $name)}
  $local = Join-Path $stage ($name -replace '/', [IO.Path]::DirectorySeparatorChar)
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $local) | Out-Null
  Invoke-WebRequest -UseBasicParsing -Uri ($base + '/' + $name) -OutFile $local -TimeoutSec 90
  $actual = (Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -ne ([string]$item.sha256).ToLowerInvariant()) {throw ('SHA256 mismatch: ' + $name)}
  Write-Host ('Verified ' + $name)
 }
 # Never touch local voice references, models, game files, or existing generated WAVs.
 New-Item -ItemType Directory -Path $backup -Force | Out-Null
 $changed = @()
 foreach ($item in $entries) {
  $name = [string]$item.path
  $relative = $name -replace '/', [IO.Path]::DirectorySeparatorChar
  $source = Join-Path $stage $relative
  $target = Join-Path $root $relative
  $previous = Join-Path $backup $relative
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
  if (Test-Path -LiteralPath $target) {
   New-Item -ItemType Directory -Force -Path (Split-Path -Parent $previous) | Out-Null
   Copy-Item -LiteralPath $target -Destination $previous -Force
  }
  $pending = $target + '.bgvoice_new'
  Copy-Item -LiteralPath $source -Destination $pending -Force
  Move-Item -LiteralPath $pending -Destination $target -Force
  $changed += $name
 }
 Write-Host ('SUCCESS: BG Voice RU ' + $manifest.version)
 Write-Host ('Backup folder: ' + $backup)
 Write-Host 'Next: BG_RU_IMOEN_PROSODY_29\\RUN_PROSODY_29.cmd'
} catch {
 Write-Host ('UPDATE FAILED: ' + $_.Exception.Message) -ForegroundColor Red
 Write-Host ('No generated WAV/model/game files were changed. Stage: ' + $stage)
 exit 1
} finally {
 if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
}
) { throw 'Unexpected release manifest' }
 $entries = @($manifest.files)
 if ($entries.Count -lt 3) {throw 'Incomplete manifest'}
 # Download + validate *every* file before installing anything.
 foreach ($item in $entries) {
  $name = [string]$item.path
  if ($name -notmatch '^(BG_RU_IMOEN_PROSODY_29/[A-Za-z0-9_.-]+|BG_VOICE_UPDATE.cmd)$') {throw ('Disallowed filename: ' + $name)}
  $local = Join-Path $stage ($name -replace '/', [IO.Path]::DirectorySeparatorChar)
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $local) | Out-Null
  Invoke-WebRequest -UseBasicParsing -Uri ($base + '/' + $name) -OutFile $local -TimeoutSec 90
  $actual = (Get-FileHash -LiteralPath $local -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -ne ([string]$item.sha256).ToLowerInvariant()) {throw ('SHA256 mismatch: ' + $name)}
  Write-Host ('Verified ' + $name)
 }
 # Never touch local voice references, models, game files, or existing generated WAVs.
 New-Item -ItemType Directory -Path $backup -Force | Out-Null
 $changed = @()
 foreach ($item in $entries) {
  $name = [string]$item.path
  $relative = $name -replace '/', [IO.Path]::DirectorySeparatorChar
  $source = Join-Path $stage $relative
  $target = Join-Path $root $relative
  $previous = Join-Path $backup $relative
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
  if (Test-Path -LiteralPath $target) {
   New-Item -ItemType Directory -Force -Path (Split-Path -Parent $previous) | Out-Null
   Copy-Item -LiteralPath $target -Destination $previous -Force
  }
  $pending = $target + '.bgvoice_new'
  Copy-Item -LiteralPath $source -Destination $pending -Force
  Move-Item -LiteralPath $pending -Destination $target -Force
  $changed += $name
 }
 Write-Host ('SUCCESS: BG Voice RU ' + $manifest.version)
 Write-Host ('Backup folder: ' + $backup)
 Write-Host 'Next: BG_RU_IMOEN_PROSODY_29\\RUN_PROSODY_29.cmd'
} catch {
 Write-Host ('UPDATE FAILED: ' + $_.Exception.Message) -ForegroundColor Red
 Write-Host ('No generated WAV/model/game files were changed. Stage: ' + $stage)
 exit 1
} finally {
 if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
}
