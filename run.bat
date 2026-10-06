@echo off
title AttendEasy - Attendance Application
cd /d "%~dp0"
echo ===================================================
echo   AttendEasy - Attendance Tracking Application
echo ===================================================
echo Starting web server and launching your browser...
echo Address: http://127.0.0.1:5000
echo.
python app.py
pause
