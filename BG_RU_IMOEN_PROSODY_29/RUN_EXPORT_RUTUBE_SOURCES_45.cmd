@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0..\.venv_qwen\Scripts\python.exe"
if not exist "%PY%" goto :NO_PYTHON
"%PY%" -X utf8 "%~dp0EXPORT_RUTUBE_SOURCES_45.py" --root "%~dp0.."
if errorlevel 1 goto :FAILED
start "" "%~dp0..\BG_RU_RUTUBE_3_CHARACTERS_44\UPLOAD_SOURCES"
echo.
echo SUCCESS: Send BG_VOICE_RU_3_CHARACTERS_EN_WAV_FOR_MP4.zip to ChatGPT.
pause
exit /b 0
:NO_PYTHON
echo ERROR: Existing Qwen Python is not found. No files changed.
pause
exit /b 2
:FAILED
echo ERROR: ZIP export failed. See error above. No game WAV modified.
pause
exit /b 1