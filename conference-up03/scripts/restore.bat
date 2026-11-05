@echo off
chcp 65001 > nul
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (
  echo Run scripts\setup.bat first.
  exit /b 1
)
if "%~1"=="" (
  echo Usage: scripts\restore.bat backups\file.db data\restored.db
  exit /b 1
)
if "%~2"=="" (
  echo Specify a NEW target database path as second argument.
  exit /b 1
)
".venv\Scripts\python.exe" scripts\manage.py restore "%~1" --target "%~2" --confirm RESTORE
exit /b %errorlevel%
