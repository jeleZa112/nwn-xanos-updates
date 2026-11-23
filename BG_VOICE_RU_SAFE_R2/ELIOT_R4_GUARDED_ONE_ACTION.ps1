# ELIOT BG Voice RU R4 - one-time guarded patch + existing-CMD readonly probe.
# DO NOT execute automatically from ChatGPT. User runs this once in PowerShell.
$ErrorActionPreference = 'Stop'
$target = Join-Path $env:USERPROFILE 'Downloads\BG_VOICE_RU_TTS_READY\bg_voice_release_v2\BG_VOICE_UPDATE.cmd'
$oldSha = '48cb47020ff5c6d9fb9e8b847f443708be80521e479709b8d9be611007070e6b'
$newSha = '3f359c241774925175937ad8006419a06b9c20c3a96aea4a878333e8d9fc6dc4'
$sourceUrl = 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/aa8990d703427b2e16772be70194d8bab33b7a1f/BG_VOICE_RU_SAFE_R2/ELIOT_R4_PATCHED_SINGLEFILE_V68.cmd'
$pending = $target + '.eliot_r4_pending'
$backup = $target + '.before_eliot_r4.bak'
$changed = $false
try {
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw 'The existing BG_VOICE_UPDATE.cmd was not found. No files modified.'
    }
    $item = Get-Item -LiteralPath $target
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Updater is a symlink/reparse point: HOLD.'
    }
    $current = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($current -eq $oldSha) {
        if ((Test-Path -LiteralPath $pending) -or (Test-Path -LiteralPath $backup)) {
            throw 'Pending/backup file already exists. HOLD; do not overwrite it.'
        }
        Invoke-WebRequest -Uri $sourceUrl -OutFile $pending -UseBasicParsing -TimeoutSec 90 -ErrorAction Stop
        $downloaded = (Get-FileHash -LiteralPath $pending -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($downloaded -ne $newSha) { throw ('R4 downloaded SHA mismatch: ' + $downloaded) }
        [IO.File]::Replace($pending, $target, $backup)
        $changed = $true
        Write-Host 'ELIOT R4: existing CMD safely updated; original saved in one backup.' -ForegroundColor Green
    } elseif ($current -eq $newSha) {
        Write-Host 'ELIOT R4: exact patched CMD already installed; no replacement.'
    } else {
        throw ('UNKNOWN CMD SHA256='+$current+'. HOLD: nothing changed. Send this hash to ChatGPT.')
    }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $newSha) {
        throw 'Post-install SHA256 mismatch.'
    }
    & $target --eliot-r4-preflight
    if ($LASTEXITCODE -ne 0) { throw ('Read-only probe returned '+$LASTEXITCODE) }
    Write-Host 'ELIOT R4 PASS: attach existing C:\Users\...\Documents\BG_VOICE_RU\FULL_PRODUCTION\SEND_TO_CHATGPT_BG_VOICE_RU.zip' -ForegroundColor Green
} catch {
    if ($changed -and (Test-Path -LiteralPath $backup -PathType Leaf)) {
        try {
            $recover = $target + '.eliot_r4_rollback_pending'
            if (Test-Path -LiteralPath $recover) { throw 'Rollback pending already exists.' }
            Copy-Item -LiteralPath $backup -Destination $recover -ErrorAction Stop
            [IO.File]::Replace($recover, $target, $target + '.r4_failed_backup')
            Write-Host 'ELIOT R4: original updater restored after failure.' -ForegroundColor Yellow
        } catch {
            Write-Host ('ELIOT R4: restore failed, original is at '+$backup) -ForegroundColor Red
        }
    }
    Write-Host ('ELIOT R4 HOLD: '+$_.Exception.Message) -ForegroundColor Red
    exit 1
} finally {
    if (Test-Path -LiteralPath $pending) { Remove-Item -LiteralPath $pending -Force -ErrorAction SilentlyContinue }
}
