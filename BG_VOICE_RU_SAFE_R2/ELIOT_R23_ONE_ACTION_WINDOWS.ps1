# BG Voice RU ELIOT R23 two-scene A/B preview — one-time guarded patch of the SAME existing CMD.
# User explicitly runs in ordinary PowerShell. No game, source WAV or approved voice writes.
$ErrorActionPreference = 'Stop'
$target = Join-Path $env:USERPROFILE 'Downloads\BG_VOICE_RU_TTS_READY\bg_voice_release_v2\BG_VOICE_UPDATE.cmd'
$knownOriginalV68 = '48cb47020ff5c6d9fb9e8b847f443708be80521e479709b8d9be611007070e6b'
$knownR4 = '3f359c241774925175937ad8006419a06b9c20c3a96aea4a878333e8d9fc6dc4'
$expectedR23 = 'c739bbbbc18cfb5cba1040828ef3287fc6fc4e28a5d49c5501582cdc2e5ecf9b'
$sourceUrl = 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/62ea8b43fac7670ad79b87b2f16e61c5418d687a/BG_VOICE_RU_SAFE_R2/ELIOT_R23_MOVIE_AB2_SINGLEFILE.cmd'
$pending = $target + '.eliot_r23_pending'
$backup = $null
$changed = $false
$preflightFinished = $false
try {
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw 'Existing one BG_VOICE_UPDATE.cmd missing. Nothing modified.'
    }
    if (((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'CMD symlink/reparse point refused.'
    }
    $current = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($current -eq $knownOriginalV68 -or $current -eq $knownR4) {
        $backup = $target + '.before_eliot_r23_' + $current.Substring(0,12) + '.bak'
        if ((Test-Path -LiteralPath $pending) -or (Test-Path -LiteralPath $backup)) {
            throw 'Existing pending/backup: HOLD without overwrite. Send message to ChatGPT.'
        }
        Invoke-WebRequest -UseBasicParsing -Uri $sourceUrl -OutFile $pending -TimeoutSec 90 -ErrorAction Stop
        $downloadSha = (Get-FileHash -LiteralPath $pending -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($downloadSha -ne $expectedR23) {
            throw ('Downloaded R23 failed SHA256: '+$downloadSha)
        }
        [IO.File]::Replace($pending,$target,$backup)
        $changed = $true
        Write-Host 'ELIOT R23: exact known CMD updated; original safely backed up.' -ForegroundColor Green
    } elseif ($current -eq $expectedR23) {
        Write-Host 'ELIOT R23: exact pilot CMD already installed; no replacement.' -ForegroundColor Green
    } else {
        throw ('UNKNOWN_CMD_SHA256='+$current+'; HOLD, no modification. Send SHA to ChatGPT.')
    }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedR23) {
        throw 'Post-install SHA check failed.'
    }
    & $target --eliot-movie-ab2-selftest
    if ($LASTEXITCODE -ne 0) { throw ('R23 internal selftest failed: '+$LASTEXITCODE) }
    & $target --eliot-movie-ab2-preflight
    if ($LASTEXITCODE -ne 0) { throw ('R23 exact source preflight failed: '+$LASTEXITCODE) }
    $preflightFinished = $true
    Write-Host 'ELIOT R23: 8 source WAVs verified. Starting 2-scenes x2 A/B PREVIEW ONLY.' -ForegroundColor Cyan
    & $target --eliot-movie-ab2
    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        # Preserve new candidate caches so the exact same one CMD can resume; no destructive rollback.
        Write-Host ('ELIOT R23 HOLD: generator RC='+$rc+'. Keep cache and this CMD; send console output to ChatGPT.') -ForegroundColor Yellow
        exit $rc
    }
    Write-Host 'ELIOT R23 PASS: 4 new candidates written into the existing ONE report; nothing installed in game.' -ForegroundColor Green
    Write-Host 'SEND: Documents\BG_VOICE_RU\FULL_PRODUCTION\SEND_TO_CHATGPT_BG_VOICE_RU.zip'
} catch {
    if (-not $preflightFinished -and $changed -and $backup -and (Test-Path -LiteralPath $backup -PathType Leaf)) {
        try {
            $restore = $target + '.r23_restore_pending'
            if (Test-Path -LiteralPath $restore) { throw 'Rollback pending exists; original remains at backup path.' }
            Copy-Item -LiteralPath $backup -Destination $restore -ErrorAction Stop
            [IO.File]::Replace($restore,$target,$target+'.r23_failed_attempt.bak')
            Write-Host 'ELIOT R23: original CMD restored; no model generation attempted.' -ForegroundColor Yellow
        } catch {
            Write-Host ('ELIOT R23: restore failed; manually locate the backed-up original at '+$backup) -ForegroundColor Red
        }
    }
    Write-Host ('ELIOT R23 HOLD: '+$_.Exception.Message) -ForegroundColor Red
    exit 1
} finally {
    if (Test-Path -LiteralPath $pending) {
        Remove-Item -LiteralPath $pending -Force -ErrorAction SilentlyContinue
    }
}
