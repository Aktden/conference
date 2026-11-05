@echo off
chcp 65001 > nul
cd /d "%~dp0\.."
call scripts\check.bat
if errorlevel 1 exit /b 1
call scripts\build.bat
exit /b %errorlevel%
