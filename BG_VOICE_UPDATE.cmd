@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "AUDIT_SCRIPT=%~dp0BG_RU_IMOEN_PROSODY_29\VOICE_UPDATER_46.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $p=$env:AUDIT_SCRIPT; $sha='9e70866641389c34b850f5ba0e445d1a2c5fd8020d9980a2b936e35901a09ab8'; if (!(Test-Path -LiteralPath $p -PathType Leaf) -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha) { if (!(Test-Path -LiteralPath (Split-Path -Parent $p) -PathType Container)) { throw 'Expected existing BG_RU_IMOEN_PROSODY_29 folder missing' }; $tmp=$p+'.voice_tmp'; try { Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/bg-voice-ru/BG_RU_IMOEN_PROSODY_29/VOICE_UPDATER_46.ps1' -OutFile $tmp -TimeoutSec 90; if ((Get-FileHash -LiteralPath $tmp -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha) { throw 'Downloaded updater SHA256 mismatch' }; Move-Item -LiteralPath $tmp -Destination $p -Force } finally { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force } } }"
if errorlevel 1 goto :failed
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%AUDIT_SCRIPT%"
set "RC=%ERRORLEVEL%"
goto :done
:failed
set "RC=1"
:done
echo BG Voice RU updater exit code: %RC%
pause
exit /b %RC%
