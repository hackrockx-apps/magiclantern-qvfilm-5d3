@echo off
setlocal EnableExtensions DisableDelayedExpansion
title QVFilm - First Install Baseline ZIP Check v0.3.0
pushd "%~dp0"
if errorlevel 1 (
    echo Cannot access program directory.
    pause
    exit /b 2
)
py -3 --version >nul 2>&1
if not errorlevel 1 goto PY
python --version >nul 2>&1
if not errorlevel 1 goto PY_ALT
echo Python 3 is required. No card or camera was modified.
goto FINISH
:PY
py -3 "baseline_stager.py"
goto FINISH
:PY_ALT
python "baseline_stager.py"
goto FINISH
:FINISH
set "RC=%ERRORLEVEL%"
echo.
echo Result is a PC-only archive inspection, NOT permission to install firmware.
popd
if not defined QVFILM_NO_PAUSE pause
exit /b %RC%
