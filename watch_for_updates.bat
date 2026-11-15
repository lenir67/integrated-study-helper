@echo off
setlocal
cd /d "%~dp0"

set "PY_EXE=..\cte-program-tracker-standalone\.venv\Scripts\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"

echo ===========================================================================
echo   Integrated Study Helper - Bidirectional Multi-Target Live Auto-Sync
echo ===========================================================================
echo Using Python: %PY_EXE%
echo.
echo Watching ^& syncing bidirectionally across:
echo   - Desktop Projects: Integrated Study Helper, Tracker, Electrical Board, Electrical Simulator, Cycle Lab
echo   - Study Guides Ch 01-52 + EPA 608 + Student Handouts (with embedded Vocabulary)
echo   - School Drive (G:\My Drive\HVAC Class Chapters)
echo   - Personal Drive (H:\ / My Drive HVAC Class Chapters ^& Projects\*)
echo   - GitHub Pages (integrated-study-helper ^& hvac-cycle-lab)
echo.
echo Press Ctrl+C to stop watching.
echo.

"%PY_EXE%" sync_and_publish.py --watch %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo.
  echo [WARN] Watcher exited with code %EXIT_CODE%.
  pause
)
exit /b %EXIT_CODE%
