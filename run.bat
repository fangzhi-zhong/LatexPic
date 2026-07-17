@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" goto :notinstalled
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:notinstalled
echo LatexPic is not installed yet.
echo Please run install.bat first.
echo.
pause
exit /b 1
