@echo off
chcp 65001 >nul
title Alpha Signal - Web Dashboard
echo.
echo  ============================================
echo    ALPHA SIGNAL - AI Financial Intelligence
echo    Starting Web Dashboard...
echo  ============================================
echo.
cd /d "%~dp0"
start http://localhost:5000
python web_app.py
pause
