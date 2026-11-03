@echo off
rem BGXUNI v0.1.1: parallel pilot. Requires WeiDU 251. No unsupported --tp2 option.
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0." 2>nul || (echo ERROR: Cannot enter game folder. & exit /b 1)
if not exist "chitin.key" (
 echo ERROR: chitin.key not found. Put BGXUNI_SETUP.cmd next to chitin.key.
 popd & exit /b 2
)
if not exist "BGXUNI\setup-BGXUNI.tp2" (
 echo ERROR: BGXUNI\setup-BGXUNI.tp2 missing. Keep old BGXUNI folder.
 popd & exit /b 3
)
if not exist "BGXUNI\BGXUN1.BAF" (
 echo ERROR: BGXUNI\BGXUN1.BAF missing.
 popd & exit /b 4
)
rem WeiDU does NOT recognize --tp2. Its normal setup-name detection expects
rem setup-BGXUNI.tp2 next to setup-BGXUNI.exe in the GAME ROOT.
rem Do not overwrite a different TP2 file with the same name.
if exist "setup-BGXUNI.tp2" (
 fc /b "setup-BGXUNI.tp2" "BGXUNI\setup-BGXUNI.tp2" >nul 2>nul
 if errorlevel 1 (
  echo STOP: root setup-BGXUNI.tp2 differs from the packaged TP2. No mod files changed.
  popd & exit /b 11
 )
) else (
 copy /b "BGXUNI\setup-BGXUNI.tp2" "setup-BGXUNI.tp2" >nul
 if errorlevel 1 (
  echo ERROR: Could not stage setup-BGXUNI.tp2 in game root.
  popd & exit /b 12
 )
)
rem Never overwrite an existing non-BGXUNI script without a project install marker.
if /I not "%~1"=="/remove" if /I not "%~1"=="/uninstall" (
 if exist "scripts\BGXUN1.BS" if not exist "BGXUNI\INSTALLED.TAG" (
  echo STOP: BGXUN1.BS exists but no BGXUNI install marker. No game script changed.
  popd & exit /b 10
 )
)
if not exist "setup-BGXUNI.exe" (
 if exist "setup-stratagems.exe" (
  copy /b "setup-stratagems.exe" "setup-BGXUNI.exe" >nul
 ) else if exist "setup-BGXAI.exe" (
  copy /b "setup-BGXAI.exe" "setup-BGXUNI.exe" >nul
 ) else (
  echo ERROR: No existing WeiDU EXE to copy. Nothing installed.
  popd & exit /b 5
 )
)
if not exist "setup-BGXUNI.exe" (
 echo ERROR: setup-BGXUNI.exe missing.
 popd & exit /b 6
)
if /I "%~1"=="/remove" goto REMOVE
if /I "%~1"=="/uninstall" goto REMOVE
if /I "%~1"=="/reinstall" goto REINSTALL
if not "%~1"=="" if /I not "%~1"=="/install" (
 echo Usage: BGXUNI_SETUP.cmd [/install ^| /remove ^| /reinstall]
 popd & exit /b 7
)
echo BGXUNI v0.1.1 - parallel script BGXUN1. Existing Advanced AI is NOT replaced.
echo CLOSE BALDUR'S GATE AND INFINITYLOADER before continuing.
echo Press CTRL+C now if the game is open.
pause
rem WeiDU recognizes --yes; it auto-detects setup-BGXUNI.tp2 in game root.
"setup-BGXUNI.exe" --yes
if errorlevel 1 goto FAILED
if not exist "scripts\BGXUN1.BS" (
 echo ERROR: WeiDU finished but scripts\BGXUN1.BS was NOT found. Read setup-BGXUNI.DEBUG.
 popd & exit /b 8
)
echo BGXUN1 v0.1.1 installed with WeiDU > "BGXUNI\INSTALLED.TAG"
echo SUCCESS: scripts\BGXUN1.BS exists. Select BGXUN1 on ONE NPC to test.
popd & exit /b 0
:REINSTALL
echo CLOSE GAME and InfinityLoader before reinstall.
pause
"setup-BGXUNI.exe" --reinstall
if errorlevel 1 goto FAILED
if not exist "scripts\BGXUN1.BS" (
 echo ERROR: scripts\BGXUN1.BS missing after reinstall.
 popd & exit /b 8
)
echo BGXUN1 v0.1.1 reinstalled with WeiDU > "BGXUNI\INSTALLED.TAG"
echo SUCCESS: BGXUN1 script found.
popd & exit /b 0
:REMOVE
echo CLOSE GAME and InfinityLoader before removing ONLY BGXUNI.
pause
"setup-BGXUNI.exe" --uninstall
if errorlevel 1 goto FAILED
if exist "BGXUNI\INSTALLED.TAG" del /q "BGXUNI\INSTALLED.TAG"
echo WeiDU uninstall completed. Existing Advanced AI was not modified by BGXUNI.
popd & exit /b 0
:FAILED
echo ERROR: WeiDU returned failure. DO NOT rerun repeatedly.
echo Inspect setup-BGXUNI.DEBUG. Original Advanced AI remains separate.
popd & exit /b 9