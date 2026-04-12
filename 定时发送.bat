@echo off
chcp 65001 >nul
title Alpha Signal - Daily Scheduler (08:00)
echo.
echo  ============================================
echo    ALPHA SIGNAL - Daily Scheduler
echo    Will send email every day at 08:00
echo    Keep this window open!
echo  ============================================
echo.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python scheduler.py
pause
