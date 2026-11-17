$ErrorActionPreference='Stop'
$target=Join-Path $env:USERPROFILE 'Downloads\BG_VOICE_RU_TTS_READY\bg_voice_release_v2\BG_VOICE_UPDATE.cmd'
$oldSha='3d9bea70e52e9c4b20b128be71625c76c9de7dd6b0063425c5f4412622e9fdb0'
$newSha='5ddb59927b0e4cd6bd823f4d632228e6b93a2bedcb80a4ceb4f9cf51c09a1868'
if (!(Test-Path -LiteralPath $target -PathType Leaf)) { throw ('Original updater missing: '+$target) }
$actual=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -eq $newSha) { Write-Host 'BG Voice RU 4.9 AUTO UPDATE: ALREADY INSTALLED'; exit 0 }
if ($actual -ne $oldSha) { throw ('Unknown updater version. No changes. SHA256='+$actual) }
$payload='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'
$memory=[IO.MemoryStream]::new([Convert]::FromBase64String($payload))
$gzip=[IO.Compression.GzipStream]::new($memory,[IO.Compression.CompressionMode]::Decompress)
$reader=[IO.StreamReader]::new($gzip,[Text.Encoding]::UTF8)
try { $insert=$reader.ReadToEnd() } finally { $reader.Dispose(); $gzip.Dispose(); $memory.Dispose() }
$old="if __name__=='__main__':`n    try:sys.exit(main())"
$replacement=$insert+"if __name__=='__main__':`n    try:`n        if not _boot_cached_or_fallback():sys.exit(main())"
$body=[IO.File]::ReadAllText($target,[Text.Encoding]::UTF8)
if (!$body.Contains($old)) { throw 'Expected embedded updater entrypoint not found' }
$updated=$body.Replace($old,$replacement)
$bytes=[Text.UTF8Encoding]::new($false).GetBytes($updated)
$crypto=[Security.Cryptography.SHA256]::Create()
try { $newActual=([BitConverter]::ToString($crypto.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $crypto.Dispose() }
if ($newActual -ne $newSha) { throw ('Refusing incorrect patch. New hash='+$newActual) }
$pending=$target+'.auto_pending'
try {
    [IO.File]::WriteAllBytes($pending,$bytes)
    Move-Item -LiteralPath $pending -Destination $target -Force
} finally { if (Test-Path -LiteralPath $pending) { Remove-Item -LiteralPath $pending -Force -ErrorAction SilentlyContinue } }
Write-Host 'BG Voice RU 4.9 AUTO UPDATE: INSTALLED AND VERIFIED'
Write-Host ('Permanent launcher: '+$target)
Write-Host 'Next runs will update the cached engine, without replacing the CMD again.'
