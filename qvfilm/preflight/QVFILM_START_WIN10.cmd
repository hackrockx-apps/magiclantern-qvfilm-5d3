@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title QVFilm 5D Mark III - SAFE PREFLIGHT / RECOVERY
set "PYTHON=py -3"
py -3 --version >nul 2>&1
if errorlevel 1 (
  set "PYTHON=python"
  python --version >nul 2>&1
  if errorlevel 1 (
    echo ERROR: Python 3 is not available. Install Python 3 first.
    echo No changes have been made to the camera or card.
    pause
    exit /b 2
  )
)
:MAIN
echo.
echo ================================================
echo  QVFilm 5D3.123 - OFFLINE SAFETY CHECK (v0.2.0)
echo ================================================
echo  1. Read firmware metadata from original JPG/CR2
echo  2. Back up known-good Magic Lantern card to PC
echo  3. Verify backup checksums (SHA-256)
echo  4. Exit
echo.
set "CHOICE="
set /p "CHOICE=Select 1-4: "
if "%CHOICE%"=="1" goto SCAN
if "%CHOICE%"=="2" goto BACKUP
if "%CHOICE%"=="3" goto VERIFY
if "%CHOICE%"=="4" exit /b 0
goto MAIN

:SCAN
echo Please use the ORIGINAL image taken by Canon 5D Mark III.
set "PHOTO="
set /p "PHOTO=Full path to JPG or CR2: "
set "PHOTO=%PHOTO:"=%"
if not defined PHOTO goto MAIN
set "CARD="
set /p "CARD=Optional camera card drive/folder (e.g. E:\), ENTER to skip: "
set "CARD=%CARD:"=%"
if defined CARD (
  %PYTHON% "%~dp0preflight.py" scan --photo "%PHOTO%" --card "%CARD%\." --out "%~dp0reports"
) else (
  %PYTHON% "%~dp0preflight.py" scan --photo "%PHOTO%" --out "%~dp0reports"
)
echo.
echo Even PASS_METADATA is NOT permission to install new firmware.
pause
goto MAIN

:BACKUP
echo Backup reads the card only. It NEVER writes to the card.
set "CARD="
set /p "CARD=Source SD/CF card drive root (e.g. E:\): "
set "CARD=%CARD:"=%"
if not defined CARD goto MAIN
set "DEST="
set /p "DEST=NEW empty destination folder on PC (e.g. C:\QVFilm\backup_5D3): "
set "DEST=%DEST:"=%"
if not defined DEST goto MAIN
%PYTHON% "%~dp0preflight.py" backup --card "%CARD%\." --dest "%DEST%\."
echo.
pause
goto MAIN

:VERIFY
set "DEST="
set /p "DEST=Backup folder to verify: "
set "DEST=%DEST:"=%"
if not defined DEST goto MAIN
%PYTHON% "%~dp0preflight.py" verify-backup --dir "%DEST%\."
echo.
pause
goto MAIN
