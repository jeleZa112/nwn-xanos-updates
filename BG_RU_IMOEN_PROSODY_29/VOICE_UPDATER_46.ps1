$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$work = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$base = 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/bg-voice-ru'
$report = Join-Path $work 'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
$tempFiles = New-Object System.Collections.ArrayList
$installed = New-Object System.Collections.ArrayList
$runTemp = $null
try {
  $manifestTmp = [IO.Path]::GetTempFileName(); [void]$tempFiles.Add($manifestTmp)
  Invoke-WebRequest -UseBasicParsing -Uri ($base+'/release_manifest.json') -OutFile $manifestTmp -TimeoutSec 90
  $manifest = Get-Content -Raw -Encoding UTF8 $manifestTmp | ConvertFrom-Json
  if ($manifest.project -ne 'BG_VOICE_RU' -or $manifest.version -notmatch '^4\.[6-9][0-9]*\.[0-9]+$') { throw 'Unexpected update manifest' }
  $files = @($manifest.files)
  if ($files.Count -lt 3) { throw 'Incomplete update manifest' }
  $staged = @()
  foreach ($entry in $files) {
    $relative = [string]$entry.path
    if ($relative -notmatch '^(BG_VOICE_UPDATE\.cmd|BG_RU_IMOEN_PROSODY_29/[A-Za-z0-9_.-]+)$' -or $relative.Contains('..')) {
      throw ('Unapproved updater path: ' + $relative)
    }
    $target = Join-Path $work ($relative -replace '/', [IO.Path]::DirectorySeparatorChar)
    if (!(Test-Path -LiteralPath (Split-Path -Parent $target) -PathType Container)) {
      throw ('Required existing folder is missing: '+(Split-Path -Parent $target))
    }
    $expected = ([string]$entry.sha256).ToLowerInvariant()
    if ($expected -notmatch '^[0-9a-f]{64}$') { throw 'Invalid SHA256 in manifest' }
    if (Test-Path -LiteralPath $target -PathType Leaf) {
      $current = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
      if ($current -eq $expected) { continue }
    }
    $temp = [IO.Path]::GetTempFileName(); [void]$tempFiles.Add($temp)
    Invoke-WebRequest -UseBasicParsing -Uri ($base+'/'+$relative) -OutFile $temp -TimeoutSec 90
    if ((Get-FileHash -LiteralPath $temp -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
      throw ('Download SHA256 mismatch: '+$relative)
    }
    $staged += [pscustomobject]@{Target=$target; Temp=$temp; Relative=$relative}
  }
  foreach ($item in $staged) {
    $had = Test-Path -LiteralPath $item.Target -PathType Leaf
    $old = if ($had) { [IO.File]::ReadAllBytes($item.Target) } else { $null }
    $pending = $item.Target+'.voice_pending'
    Copy-Item -LiteralPath $item.Temp -Destination $pending -Force
    try { Move-Item -LiteralPath $pending -Destination $item.Target -Force }
    finally { if (Test-Path -LiteralPath $pending) { Remove-Item -LiteralPath $pending -Force } }
    [void]$installed.Add([pscustomobject]@{Path=$item.Target; Previous=$old; Had=$had})
  }
  $payload = Join-Path $work 'BG_RU_IMOEN_PROSODY_29\VOICE_REVIEW_46.py.gz.b64'
  $engine = Join-Path $work 'BG_RU_IMOEN_PROSODY_29\VOICE_REVIEW_46.py'
  if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.11 -c "import sys; assert sys.version_info >= (3,9)" 2>$null
    if ($LASTEXITCODE -eq 0) { $python = 'py'; $prefix = @('-3.11') }
  }
  if (!$python) {
    if (!(Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python 3.9+ not found' }
    & python -c "import sys; assert sys.version_info >= (3,9)" 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.9+ not found' }
    $python = 'python'; $prefix = @()
  }
  $unpack = "import base64,gzip,hashlib,pathlib,sys;p=pathlib.Path(sys.argv[1]);d=pathlib.Path(sys.argv[2]);b=gzip.decompress(base64.b64decode(p.read_bytes()));assert hashlib.sha256(b).hexdigest()=='3a877228f6c32e76adb2267394ac741dd1b0369ef1e5bf2692a816b90b6b4d6f';d.write_bytes(b) if not d.exists() or d.read_bytes()!=b else None"
  & $python @prefix -c $unpack $payload $engine
  if ($LASTEXITCODE -ne 0) { throw 'Audit module verification failed' }
  & $python @prefix $engine --self-test
  if ($LASTEXITCODE -ne 0) { throw 'Audit self-test failed' }
  $source = if ($env:BG_VOICE_RU_ROOT) { $env:BG_VOICE_RU_ROOT } else { 'C:\BG_VOICE_RU_MASTER\08_VOXCPM2_ALL_CHARACTERS' }
  if (!(Test-Path -LiteralPath $source -PathType Container)) { throw ('WAV source folder not found: '+$source) }
  $runTemp = Join-Path ([IO.Path]::GetTempPath()) ('BG_VOICE_RU_AUDIT_'+[guid]::NewGuid().ToString('N'))
  [void](New-Item -ItemType Directory -Force -Path $runTemp)
  # Existing user selections are read from a temporary copy; they are never overwritten.
  $checker = Join-Path $env:USERPROFILE 'Downloads\BG_VOICE_RU_STRESS_CHECKER_V02\BG_VOICE_RU_STRESS_CHECKER_V02'
  if (Test-Path -LiteralPath $checker -PathType Container) {
    $choiceFile = Get-ChildItem -LiteralPath $checker -File -Recurse -Filter 'YOUR_DECISIONS_50.csv' -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($choiceFile) { Copy-Item -LiteralPath $choiceFile.FullName -Destination (Join-Path $runTemp 'USER_CHOICES.csv') }
  }
  $runner = @'
import importlib.util, sys
engine, source, out = sys.argv[1:4]
spec = importlib.util.spec_from_file_location("voice_review_46", engine)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot import verified voice audit engine")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
module.OUT = out
sys.argv = [engine, "--root", source]
raise SystemExit(module.main())
'@
  $runnerTmp = Join-Path ([IO.Path]::GetTempPath()) ('BG_VOICE_RU_RUN_'+[guid]::NewGuid().ToString('N')+'.py')
  [IO.File]::WriteAllText($runnerTmp, $runner, (New-Object Text.UTF8Encoding($false)))
  [void]$tempFiles.Add($runnerTmp)
  & $python @prefix $runnerTmp $engine $source $runTemp
  if ($LASTEXITCODE -ne 0) { throw 'WAV audit failed' }
  $generated = Join-Path $runTemp 'SEND_TO_CHATGPT_BG_VOICE_RU_ONECLICK.zip'
  if (!(Test-Path -LiteralPath $generated -PathType Leaf)) { throw 'Audit ZIP missing' }
  $pendingReport = $report+'.pending'
  Copy-Item -LiteralPath $generated -Destination $pendingReport -Force
  Move-Item -LiteralPath $pendingReport -Destination $report -Force
  Write-Host ('SUCCESS: BG Voice RU '+$manifest.version) -ForegroundColor Green
  Write-Host ('ONE REPORT: '+$report)
  Write-Host 'Original WAVs and approved voices unchanged.'
} catch {
  $msg = $_.Exception.Message
  Write-Host ('BG VOICE RU ERROR: '+$msg) -ForegroundColor Red
  # Failed installs are restored; originals and approved recordings are never touched.
  $restore = @($installed)
  [array]::Reverse($restore)
  foreach ($rec in $restore) {
    try {
      if ($rec.Had) { [IO.File]::WriteAllBytes($rec.Path,$rec.Previous) }
      elseif (Test-Path -LiteralPath $rec.Path) { Remove-Item -LiteralPath $rec.Path -Force }
    } catch { Write-Host ('Rollback failure: '+$rec.Path) -ForegroundColor Red }
  }
  try {
    $errorText = [IO.Path]::GetTempFileName()
    [void]$tempFiles.Add($errorText)
    [IO.File]::WriteAllText($errorText, ("BG Voice RU audit error" + [Environment]::NewLine + $msg), [Text.Encoding]::UTF8)
    $errorDir = Join-Path ([IO.Path]::GetTempPath()) ('BG_VOICE_RU_ERROR_' + [guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Path $errorDir -Force)
    try {
      Copy-Item -LiteralPath $errorText -Destination (Join-Path $errorDir 'ERROR.txt')
      $failedZip = Join-Path ([IO.Path]::GetTempPath()) ('BG_VOICE_RU_FAILURE_' + [guid]::NewGuid().ToString('N') + '.zip')
      [void]$tempFiles.Add($failedZip)
      Compress-Archive -LiteralPath (Join-Path $errorDir 'ERROR.txt') -DestinationPath $failedZip -CompressionLevel Optimal -Force
      if (!(Test-Path -LiteralPath $failedZip)) { throw 'ZIP was not created' }
      $pendingReport = $report+'.pending'
      Copy-Item -LiteralPath $failedZip -Destination $pendingReport -Force
      Move-Item -LiteralPath $pendingReport -Destination $report -Force
    } finally {
      Remove-Item -LiteralPath $errorDir -Recurse -Force -ErrorAction SilentlyContinue
    }
  } catch { Write-Host ('Could not create failure ZIP: '+$_.Exception.Message) }
  exit 1
} finally {
  foreach ($tmp in $tempFiles) { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue } }
  if ($runTemp -and (Test-Path -LiteralPath $runTemp)) { Remove-Item -LiteralPath $runTemp -Recurse -Force -ErrorAction SilentlyContinue }
}
