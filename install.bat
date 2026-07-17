@echo off
setlocal
cd /d "%~dp0"
title LatexPic Installer

echo ========================================
echo          LatexPic Installer
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 goto :nopython

echo Python found:
python --version
echo.
echo Installation output is saved to install.log.
echo Creating virtual environment...

>install.log echo LatexPic installation log
python -m venv .venv >>install.log 2>&1
if errorlevel 1 goto :error

echo Installing dependencies. This can take several minutes...
".venv\Scripts\python.exe" -m pip install --upgrade pip >>install.log 2>&1
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install -r requirements.txt >>install.log 2>&1
if errorlevel 1 goto :error

echo.
echo Installation completed successfully.
echo Double-click run.bat to start LatexPic.
echo.
pause
exit /b 0

:nopython
echo ERROR: Python was not found.
echo Install 64-bit Python 3.11 or 3.12 and enable "Add Python to PATH".
echo.
pause
exit /b 1

:error
echo.
echo ERROR: Installation failed.
echo See this file for details:
echo %~dp0install.log
echo.
type install.log
echo.
pause
exit /b 1

