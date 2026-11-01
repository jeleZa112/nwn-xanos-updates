# BGXAI GitHub update installer - beta. Only own mod content.
param([string]$GameRoot = ".")
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$repo = 'jeleZa112/nwn-xanos-updates'
$api = 'https://api.github.com/repos/' + $repo
$prefix = 'BGXAI'
$h = @{'User-Agent'='BGXAI-EET-Updater';'Accept'='application/vnd.github+json';'Cache-Control'='no-cache'}
$GameRoot = (Resolve-Path -LiteralPath $GameRoot).Path
if (-not (Test-Path -LiteralPath (Join-Path $GameRoot 'chitin.key'))) { throw 'chitin.key not found. Place BGXAI_UPDATE.cmd in the game root.' }
if (-not (Test-Path -LiteralPath (Join-Path $GameRoot 'override'))) { throw 'override directory not found.' }
if ((Get-Process -Name Baldur,BaldursGate,baldur -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0) {
    throw 'Close Baldur''s Gate before installing or updating BGXAI.'
}
$cache = Join-Path $env:LOCALAPPDATA 'BGXAI_UPDATER'
New-Item -Force -ItemType Directory -Path $cache | Out-Null
$headFile = Join-Path $cache 'head.txt'
if (-not (Test-Path -LiteralPath $headFile)) { throw 'Commit marker missing from bootstrap.' }
$sha = [IO.File]::ReadAllText($headFile).Trim()
if ($sha -notmatch '^[0-9a-fA-F]{40}$') { throw 'Invalid GitHub commit marker.' }
function Read-GithubFile([string]$path) {
    $u = $api + '/contents/' + $path + '?ref=' + $sha
    $doc = Invoke-RestMethod -Uri $u -Headers $h -TimeoutSec 30 -UseBasicParsing
    if ($doc.encoding -ne 'base64' -or !$doc.content) { throw ('GitHub API returned no base64 data for ' + $path) }
    return ,([Convert]::FromBase64String(([string]$doc.content -replace '\s','')))
}
$rawManifest = Read-GithubFile 'BGXAI/latest.json'
$manifest = [Text.Encoding]::UTF8.GetString($rawManifest) | ConvertFrom-Json
if ($manifest.channel -ne 'pilot' -or !$manifest.files -or !$manifest.version) { throw 'Invalid BGXAI release manifest.' }
Write-Host ('BGXAI GitHub version: ' + $manifest.version + ' (pilot)') -ForegroundColor Cyan
$marker = Join-Path $GameRoot 'BGXAI\bgxai-updater-version.txt'
if (Test-Path -LiteralPath $marker) {
    $previous = [IO.File]::ReadAllText($marker).Trim()
    if ($previous -eq $sha) { Write-Host 'Already up to date. No changes.' -ForegroundColor Green; exit 0 }
}
$stage = Join-Path $cache ('stage_' + $sha.Substring(0,12))
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$paths = @()
foreach ($asset in $manifest.files) {
    $rel = [string]$asset.path
    if ($rel -notmatch '^BGXAI/(AI_BAF/[A-Za-z0-9_]+\.BAF|BGXAI\.TP2)$') { throw ('Forbidden manifest file path: ' + $rel) }
    if ($paths -contains $rel) { throw ('Duplicate manifest file: ' + $rel) }
    $paths += $rel
    $bytes = Read-GithubFile ('BGXAI/releases/' + $manifest.version + '/' + $rel)
    $hash = [System.Security.Cryptography.SHA256]::Create()
    try { $actual = ([BitConverter]::ToString($hash.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $hash.Dispose() }
    if ($actual -ne [string]$asset.sha256) { throw ('SHA256 mismatch: ' + $rel) }
    $out = Join-Path $stage ($rel.Replace('/', [IO.Path]::DirectorySeparatorChar))
    $parent = Split-Path -Parent $out
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    [IO.File]::WriteAllBytes($out,$bytes)
}
if (($paths.Count -ne 7) -or !($paths -contains 'BGXAI/BGXAI.TP2')) { throw 'Unexpected number of mod files.' }
$setup = Join-Path $GameRoot 'setup-BGXAI.exe'
if (-not (Test-Path -LiteralPath $setup)) {
    $sourceExe = Join-Path $GameRoot 'setup-stratagems.exe'
    if (-not (Test-Path -LiteralPath $sourceExe)) { throw 'Missing local setup-stratagems.exe (WeiDU). Nothing changed.' }
    Copy-Item -LiteralPath $sourceExe -Destination $setup -ErrorAction Stop
}
$modDir = Join-Path $GameRoot 'BGXAI'
$time = (Get-Date).ToString('yyyyMMdd-HHmmss')
$backup = Join-Path $cache ('backup_' + $time)
$hadOld = Test-Path -LiteralPath $modDir
if ($hadOld) { Copy-Item -LiteralPath $modDir -Destination $backup -Recurse -Force }
$weiduLog = Join-Path $GameRoot 'WeiDU.log'
$installed = $false
if (Test-Path -LiteralPath $weiduLog) {
    $installed = (Select-String -Path $weiduLog -Pattern 'BGXAI[\\/]BGXAI\.TP2' -Quiet)
    Copy-Item -LiteralPath $weiduLog -Destination (Join-Path $cache ('WeiDU_' + $time + '.log')) -Force
}
foreach ($rel in $paths) {
    $src = Join-Path $stage ($rel.Replace('/', [IO.Path]::DirectorySeparatorChar))
    $dst = Join-Path $GameRoot ($rel.Replace('/', [IO.Path]::DirectorySeparatorChar))
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
}
Write-Host 'Files verified and backed up. Installing via WeiDU ...' -ForegroundColor Yellow
if ($installed) {
    $args = @('--noautoupdate','--no-exit-pause','--reinstall')
} else {
    $args = @('--noautoupdate','--no-exit-pause','--language','0','--force-install','0')
}
Push-Location $GameRoot
try {
    & $setup @args
    $exitCode = $LASTEXITCODE
} finally { Pop-Location }
if ($exitCode -ne 0) {
    Write-Warning ('WeiDU failed (exit code ' + $exitCode + '). See setup-BGXAI.DEBUG and WeiDU.log.')
    if ($hadOld) {
        Remove-Item -LiteralPath $modDir -Recurse -Force -ErrorAction SilentlyContinue
        Copy-Item -LiteralPath $backup -Destination $modDir -Recurse -Force
        Write-Warning 'Previous BGXAI source folder restored. Do NOT ignore WeiDU installation errors.'
    }
    exit 1
}
[IO.File]::WriteAllText($marker,$sha,[Text.Encoding]::ASCII)
Write-Host ('SUCCESS: BGXAI ' + $manifest.version + ' installed. Script files should be in scripts\BGX*.BS') -ForegroundColor Green
Write-Host 'TEST ONLY: assign BGXATK to one character in a backup save.' -ForegroundColor Yellow
exit 0