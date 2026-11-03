@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0." 2>nul || (echo ERROR: Cannot enter game folder. & exit /b 1)
if not exist "chitin.key" (
  echo ERROR: chitin.key not found. Put this CMD and BGXUNI folder in game root.
  popd & exit /b 2
)
if not exist "BGXUNI\setup-BGXUNI.tp2" (
  echo ERROR: Missing BGXUNI\setup-BGXUNI.tp2.
  popd & exit /b 3
)
if not exist "BGXUNI\BGXUN1.BAF" (
  echo ERROR: Missing BGXUNI\BGXUN1.BAF.
  popd & exit /b 4
)
rem Stop before touching an existing non-BGXUNI script of the same name.
if not "%~1"=="/remove" if not "%~1"=="/uninstall" if not "%~1"=="/reinstall" (
 if exist "scripts\BGXUN1.BS" if not exist "BGXUNI\INSTALLED.TAG" (
  echo STOP: BGXUN1.BS exists but is not ours. No files changed.
  popd & exit /b 10
 )
)
if not exist "setup-BGXUNI.exe" (
  if exist "setup-stratagems.exe" (
    copy /b /y "setup-stratagems.exe" "setup-BGXUNI.exe" >nul
  ) else if exist "setup-BGXAI.exe" (
    copy /b /y "setup-BGXAI.exe" "setup-BGXUNI.exe" >nul
  ) else (
    echo ERROR: No existing WeiDU installer to copy. Nothing changed.
    popd & exit /b 5
  )
)
if not exist "setup-BGXUNI.exe" (
 echo ERROR: WeiDU copy failed.
 popd & exit /b 6
)
if /I "%~1"=="/remove" goto REMOVE
if /I "%~1"=="/uninstall" goto REMOVE
if /I "%~1"=="/reinstall" goto REINSTALL
if not "%~1"=="" if /I not "%~1"=="/install" (
 echo Usage: BGXUNI_SETUP.cmd [/install ^| /remove ^| /reinstall]
 popd & exit /b 7
)
echo BGXUN1 parallel script - existing Advanced AI will NOT be overwritten.
echo CLOSE GAME AND INFINITYLOADER BEFORE CONTINUING.
echo Press CTRL+C to cancel if the game is open.
pause
"setup-BGXUNI.exe" --tp2 "BGXUNI/setup-BGXUNI.tp2" --yes
if errorlevel 1 goto FAILED
if not exist "scripts\BGXUN1.BS" (
 echo ERROR: installer returned success but BGXUN1.BS was not found. See setup-BGXUNI.DEBUG.
 popd & exit /b 8
)
echo BGXUN1 v0.1 installed via WeiDU > "BGXUNI\INSTALLED.TAG"
echo OK: scripts\BGXUN1.BS exists. Select BGXUN1 on ONE test character.
popd & exit /b 0
:REINSTALL
echo CLOSE GAME BEFORE REINSTALLING.
pause
"setup-BGXUNI.exe" --tp2 "BGXUNI/setup-BGXUNI.tp2" --reinstall
if errorlevel 1 goto FAILED
popd & exit /b 0
:REMOVE
echo CLOSE GAME. Uninstalling only the BGXUNI component via WeiDU.
pause
"setup-BGXUNI.exe" --tp2 "BGXUNI/setup-BGXUNI.tp2" --uninstall --yes
if errorlevel 1 goto FAILED
if exist "BGXUNI\INSTALLED.TAG" del /q "BGXUNI\INSTALLED.TAG"
echo Uninstall command finished. Check WeiDU log and scripts folder.
popd & exit /b 0
:FAILED
echo ERROR: WeiDU reported a failure. DO NOT repeat blindly.
echo Inspect setup-BGXUNI.DEBUG and WeiDU.log. Prior scripts were not replaced by this mod.
popd & exit /b 9