@echo off
chcp 65001 >nul
title Alpha Signal - Daily Email
echo.
echo  ============================================
echo    ALPHA SIGNAL - Sending Daily Briefing
echo  ============================================
echo.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python run_daily.py
echo.
echo  Done! Press any key to close...
pause >nul
