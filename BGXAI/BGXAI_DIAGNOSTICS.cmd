@echo off
setlocal
cd /d "%~dp0"
if not exist "chitin.key" (
 echo Put this file next to chitin.key
 pause
 exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
 "$ErrorActionPreference='Stop'; $root=(Get-Location).Path; $out=Join-Path $root 'BGXAI_DIAGNOSTICS.txt'; $names=@('BGXAI_UPDATE.log','WeiDU.log','setup-BGXAI.DEBUG','InfinityLoader.log','EEex.log','BGXAI_COMBAT.log'); Set-Content $out ('BGXAI diagnostic bundle '+(Get-Date -Format o)) -Encoding UTF8; foreach($name in $names){$p=Join-Path $root $name; Add-Content $out ('==== '+$name+' ====') -Encoding UTF8; if(Test-Path $p){Get-Content $p -Tail 250 -ErrorAction SilentlyContinue | Add-Content $out -Encoding UTF8}else{Add-Content $out 'not found' -Encoding UTF8}}; $crash=Join-Path $root 'InfinityLoader_Crash'; if(Test-Path $crash){Get-ChildItem $crash -Filter '*.log' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | ForEach-Object {Add-Content $out ('==== CRASH '+$_.Name+' ====') -Encoding UTF8; Get-Content $_.FullName -Tail 200 -ErrorAction SilentlyContinue | Add-Content $out -Encoding UTF8}}; Write-Host ('Saved: '+$out)"
echo Send BGXAI_DIAGNOSTICS.txt to ChatGPT
pause
