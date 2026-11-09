@echo off
setlocal
cd /d "%~dp0"
echo BGXAI 044 READ-ONLY DIAGNOSTIC (EET+EEex)
echo.
echo 1 = Check prerequisites (NO CHANGES)
echo 2 = Install optional hotkey diagnostic (requires YES)
echo 3 = Status (NO CHANGES)
echo 4 = Uninstall ONLY 044 (requires YES, WeiDU rollback)
echo 0 = Exit
echo.
set "CH=0"
set /p "CH=Choose 0-4 [0]: "
if "%CH%"=="1" py -3 "BGXAI44_INSTALL.py" --status
if "%CH%"=="2" py -3 "BGXAI44_INSTALL.py" --install
if "%CH%"=="3" py -3 "BGXAI44_INSTALL.py" --status
if "%CH%"=="4" py -3 "BGXAI44_INSTALL.py" --uninstall
if "%CH%"=="0" goto end
:end
echo.
pause
endlocal
