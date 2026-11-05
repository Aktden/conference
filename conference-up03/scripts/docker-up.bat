@echo off
chcp 65001 > nul
cd /d "%~dp0\.."
docker compose up --build -d
exit /b %errorlevel%
