@echo off
setlocal
cd /d "%~dp0"

set "NO_PAUSE=0"
set "PASS_ARGS="
:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--no-pause" (
  set "NO_PAUSE=1"
) else (
  set "PASS_ARGS=%PASS_ARGS% %1"
)
shift
goto parse_args
:args_done

set "PY_EXE=..\cte-program-tracker-standalone\.venv\Scripts\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"

echo ============================================================
echo   Integrated Study Helper - Sync, Build Check ^& Publisher
echo ============================================================
echo Using Python: %PY_EXE%
echo.

"%PY_EXE%" sync_and_publish.py --push%PASS_ARGS%
if errorlevel 1 (
  echo.
  echo [ERROR] Sync or GitHub push did not complete.
  echo         If this is your first publish, create a Public repository on GitHub:
  echo           https://github.com/new
  echo           Repository name: integrated-study-helper
  echo         Then link and push from this folder:
  echo           git init -b main
  echo           git remote add origin https://github.com/lenir67/integrated-study-helper.git
  echo           git push -u origin main
  echo         See GOOGLE_SITES_SETUP.md for full instructions.
  if "%NO_PAUSE%"=="0" pause
  exit /b 1
)

echo.
echo [SUCCESS] Integrated Study Helper pushed to GitHub Pages!
echo           Live URL (refreshes in ~15-30 seconds):
echo           https://lenir67.github.io/integrated-study-helper/
if "%NO_PAUSE%"=="0" pause
exit /b 0
