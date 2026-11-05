@echo off
chcp 65001 > nul
cd /d "%~dp0\.."
where py >nul 2>nul
if errorlevel 1 (
  python -m venv .venv
) else (
  py -3.12 -m venv .venv
)
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1
if not exist .env copy .env.example .env >nul
echo Setup completed. Run scripts\run.bat
exit /b 0
