@echo off
setlocal EnableExtensions DisableDelayedExpansion
title QVFilm 5D Mark III - SAFE PREFLIGHT / RECOVERY v0.2.1

rem All interactive paths are read in Python, never expanded in CMD.
rem This fixes spaces in folder names such as Z:\5D Mark III Upgrade\.
pushd "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open the extracted program folder.
  pause
  exit /b 2
)

py -3 -c "import sys; assert sys.version_info.major == 3" >nul 2>&1
if not errorlevel 1 goto PY_LAUNCH

python -c "import sys; assert sys.version_info.major == 3" >nul 2>&1
if not errorlevel 1 goto PY_FALLBACK

echo.
echo ERROR: Python 3 is not installed or not available in PATH.
echo Install Python 3 and restart this script.
echo Nothing was written to the camera or card.
popd
if not defined QVFILM_NO_PAUSE pause
exit /b 2

:PY_LAUNCH
py -3 "preflight.py" interactive
goto FINISH

:PY_FALLBACK
python "preflight.py" interactive
goto FINISH

:FINISH
set "RET=%ERRORLEVEL%"
popd
echo.
echo QVFilm v0.2.1 ended. No firmware was installed.
if not defined QVFILM_NO_PAUSE pause
exit /b %RET%
