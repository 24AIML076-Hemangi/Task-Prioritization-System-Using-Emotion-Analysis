@echo off
setlocal
cd /d "%~dp0"

start "Task Prioritization Backend" cmd /k "python Backend\app.py"
timeout /t 2 >nul
start "" "http://localhost:5000/"

endlocal

