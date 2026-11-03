@echo off
rem BGXUNI RUN 0.1.2 - unique filename to prevent old --tp2 installer mix-up.
rem Game files BDDEFAI, BGXGRP, BGXTANK and legacy updaters stay unchanged.
setlocal EnableExtensions DisableDelayedExpansion
title BGXUNI RUN 012 - NEW INSTALLER - NO TP2 FLAG
echo.
echo ======================================================================
echo   BGXUNI RUN 012 - NEW LAUNCHER - WEIDU 251 - NO UNSUPPORTED --tp2
echo ======================================================================
echo Do NOT continue if Baldur's Gate or InfinityLoader is still running.
echo.
set "BGXROOT=%~dp0"
if exist "%BGXROOT%chitin.key" goto ROOT_FOUND
rem Your game folder from the prior BGXAI LIVE screenshot.
if exist "C:\Games\Baldur's Gate Trilogy (EE)\chitin.key" (
  set "BGXROOT=C:\Games\Baldur's Gate Trilogy (EE)\"
  goto ROOT_FOUND
)
echo [BGXUNI 012 ERROR] I cannot locate the game.
echo Put BGXUNI_RUN_012.cmd in the same folder as chitin.key and run it.
goto FINISH_FAIL
:ROOT_FOUND
pushd "%BGXROOT%" 2>nul
if errorlevel 1 (
 echo [BGXUNI 012 ERROR] Game directory cannot be accessed.
 goto FINISH_FAIL
)
echo [BGXUNI 012] Game folder: %CD%
if not exist "BGXUNI\setup-BGXUNI.tp2" (
 echo [BGXUNI 012 ERROR] Missing BGXUNI\setup-BGXUNI.tp2.
 echo Extract the ORIGINAL BGXUNI package into the game folder first.
 goto FAIL
)
if not exist "BGXUNI\BGXUN1.BAF" (
 echo [BGXUNI 012 ERROR] Missing BGXUNI\BGXUN1.BAF.
 goto FAIL
)
rem Stop on a running loader / game: it is unsafe to compile while playing.
tasklist /FI "IMAGENAME eq InfinityLoader.exe" 2>nul | find /I "InfinityLoader.exe" >nul
if not errorlevel 1 (
 echo [BGXUNI 012 ERROR] InfinityLoader.exe is running. Exit the game first.
 goto FAIL
)
tasklist /FI "IMAGENAME eq Baldur.exe" 2>nul | find /I "Baldur.exe" >nul
if not errorlevel 1 (
 echo [BGXUNI 012 ERROR] Baldur.exe is running. Exit the game first.
 goto FAIL
)
tasklist /FI "IMAGENAME eq BaldursGate.exe" 2>nul | find /I "BaldursGate.exe" >nul
if not errorlevel 1 (
 echo [BGXUNI 012 ERROR] BaldursGate.exe is running. Exit the game first.
 goto FAIL
)
rem Avoid overwriting an unrelated script with the same 8-character resref.
if exist "scripts\BGXUN1.BS" if not exist "BGXUNI\INSTALLED.TAG" (
 echo [BGXUNI 012 STOP] scripts\BGXUN1.BS already exists without our marker.
 echo Existing script is preserved; request an audit before proceeding.
 goto FAIL
)
rem WeiDU recognizes the setup executable/TP2 pair. Copy one verified TP2 to root.
if exist "setup-BGXUNI.tp2" (
 fc /b "setup-BGXUNI.tp2" "BGXUNI\setup-BGXUNI.tp2" >nul 2>nul
 if errorlevel 1 (
  echo [BGXUNI 012 STOP] Root setup-BGXUNI.tp2 is DIFFERENT.
  echo Nothing has been overwritten. Check both files before retrying.
  goto FAIL
 )
) else (
 copy /b "BGXUNI\setup-BGXUNI.tp2" "setup-BGXUNI.tp2" >nul
 if errorlevel 1 (
  echo [BGXUNI 012 ERROR] Could not copy TP2 to root.
  goto FAIL
 )
)
if not exist "setup-BGXUNI.exe" (
 if exist "setup-stratagems.exe" (
  copy /b "setup-stratagems.exe" "setup-BGXUNI.exe" >nul
 ) else if exist "setup-BGXAI.exe" (
  copy /b "setup-BGXAI.exe" "setup-BGXUNI.exe" >nul
 ) else (
  echo [BGXUNI 012 ERROR] WeiDU executable is missing.
  goto FAIL
 )
 if errorlevel 1 (
  echo [BGXUNI 012 ERROR] Could not create separate WeiDU executable.
  goto FAIL
 )
)
echo.
echo [BGXUNI 012] Safe preflight passed. This runs one NEW optional component.
echo [BGXUNI 012] Existing Advanced AI and BGXAI scripts are not touched.
echo Press CTRL+C to cancel. Any other key starts WeiDU 251.
pause
rem WeiDU 251 accepts --yes, auto-detects the root setup-BGXUNI.tp2.
echo [BGXUNI 012] Executing: setup-BGXUNI.exe --yes
echo [BGXUNI 012] The OLD --tp2 command is NOT used.
"setup-BGXUNI.exe" --yes
if errorlevel 1 (
 echo [BGXUNI 012 FAILED] WeiDU returned an error: review setup-BGXUNI.DEBUG.
 goto FAIL
)
if not exist "scripts\BGXUN1.BS" (
 echo [BGXUNI 012 FAILED] scripts\BGXUN1.BS was not created.
 echo [BGXUNI 012] Inspect setup-BGXUNI.DEBUG; do NOT assign this script.
 goto FAIL
)
>"BGXUNI\INSTALLED.TAG" echo BGXUN1 v0.1.2 installed with separate WeiDU component
echo.
echo ======================================================================
echo [BGXUNI 012 SUCCESS] scripts\BGXUN1.BS exists.
echo Select BGXUN1 for ONE NPC. Keep everyone else on the current AI.
echo ======================================================================
popd
pause
exit /b 0
:FAIL
popd
:FINISH_FAIL
echo.
echo [BGXUNI 012] Installation was NOT confirmed. Send a screenshot of this window.
pause
exit /b 1