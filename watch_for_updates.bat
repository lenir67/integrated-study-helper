@echo off
setlocal
cd /d "%~dp0"

set "PY_EXE=..\cte-program-tracker-standalone\.venv\Scripts\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"

echo ============================================================
echo   Integrated Study Helper - Live Auto-Sync Watcher
echo ============================================================
echo Using Python: %PY_EXE%
echo Watching MRAC Ch 01-52, EPA 608, Electrical Board, Cycle Lab ^& Student Handouts...
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
